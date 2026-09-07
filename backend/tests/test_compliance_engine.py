import pytest
from datetime import date, timedelta
from app.models import RuleType, Operator, Severity, RuleStatus, RiskLevel, VerificationStatus, OfficerDecisionType
from app.rules.engine import RuleEngine, RuleResultDTO
from app.verification.adapters import MockGSTAdapter, MockDebarmentAdapter, MockUdyamAdapter
from app.services.scoring_service import ScoringService
from app.services.risk_service import RiskService

class MockRequirement:
    def __init__(self, id="req-1", name="Turnover", rule_type=RuleType.NUMERIC, operator=Operator.GTE, expected_value="10", unit="Cr", evidence_type="turnover", severity=Severity.HIGH, mandatory=True, weight=20.0):
        self.id = id
        self.name = name
        self.rule_type = rule_type
        self.operator = operator
        self.expected_value = expected_value
        self.unit = unit
        self.evidence_type = evidence_type
        self.severity = severity
        self.mandatory = mandatory
        self.weight = weight

# 1. Numeric rule PASS
def test_numeric_rule_pass():
    engine = RuleEngine()
    req = MockRequirement(expected_value="10", operator=Operator.GTE, evidence_type="turnover")
    context = {
        "extracted_fields": {
            "turnover": {"value": 12.5, "confidence": 1.0}
        }
    }
    res = engine.evaluate(req, context)
    assert res.status == RuleStatus.PASS
    assert "TRUE" in res.explanation
    assert "12.5" in res.actual_value

# 2. Numeric rule FAIL
def test_numeric_rule_fail():
    engine = RuleEngine()
    req = MockRequirement(expected_value="10", operator=Operator.GTE, evidence_type="turnover")
    context = {
        "extracted_fields": {
            "turnover": {"value": 7.0, "confidence": 1.0}
        }
    }
    res = engine.evaluate(req, context)
    assert res.status == RuleStatus.FAIL
    assert "FALSE" in res.explanation

# 3. Date rule PASS (Future validity date)
def test_date_rule_pass():
    engine = RuleEngine()
    future_date = (date.today() + timedelta(days=365)).isoformat()
    req = MockRequirement(rule_type=RuleType.DATE, operator=Operator.AFTER, expected_value="TODAY", evidence_type="expiry_date")
    context = {
        "extracted_fields": {
            "expiry_date": {"value": future_date, "confidence": 1.0}
        }
    }
    res = engine.evaluate(req, context)
    assert res.status == RuleStatus.PASS
    assert "VALID" in res.explanation

# 4. Date rule FAIL (Expired date)
def test_date_rule_fail():
    engine = RuleEngine()
    past_date = (date.today() - timedelta(days=365)).isoformat()
    req = MockRequirement(rule_type=RuleType.DATE, operator=Operator.AFTER, expected_value="TODAY", evidence_type="expiry_date")
    context = {
        "extracted_fields": {
            "expiry_date": {"value": past_date, "confidence": 1.0}
        }
    }
    res = engine.evaluate(req, context)
    assert res.status == RuleStatus.FAIL
    assert "EXPIRED" in res.explanation

# 5. Verification VALID
def test_verification_valid():
    adapter = MockGSTAdapter()
    res = adapter.verify("07AAAAA0000A1Z5")
    assert res.status == VerificationStatus.VALID
    assert res.success is True
    assert res.response_data["status"] == "Active"

# 6. Verification INVALID
def test_verification_invalid():
    adapter = MockGSTAdapter()
    res = adapter.verify("GST123INVALID")
    assert res.status == VerificationStatus.INVALID
    assert res.response_data["status"] == "Cancelled"

# 7. Verification UNAVAILABLE (Does not fail silently, preserves UNAVAILABLE state)
def test_verification_unavailable():
    adapter = MockGSTAdapter()
    res = adapter.verify("GST123DOWN")
    assert res.status == VerificationStatus.UNAVAILABLE
    assert res.success is False
    assert res.error_code == "GST_PORTAL_TIMEOUT"

# 8. Missing mandatory document
def test_missing_mandatory_document():
    engine = RuleEngine()
    req = MockRequirement(rule_type=RuleType.DOCUMENT_PRESENT, evidence_type="OEM_AUTH", expected_value="OEM_AUTH", mandatory=True)
    context = {
        "documents": [
            {"filename": "Financial_Statement.pdf", "document_type": "FINANCIAL"}
        ]
    }
    res = engine.evaluate(req, context)
    assert res.status == RuleStatus.FAIL
    assert res.actual_value == "Missing"

# 9. Score calculation
def test_score_calculation():
    scoring = ScoringService()
    results = [
        RuleResultDTO(requirement_id="r1", status=RuleStatus.PASS, actual_value="12", expected_value="10", explanation="ok", severity=Severity.HIGH, weight=20.0),
        RuleResultDTO(requirement_id="r2", status=RuleStatus.PASS, actual_value="VALID", expected_value="VALID", explanation="ok", severity=Severity.HIGH, weight=20.0),
        RuleResultDTO(requirement_id="r3", status=RuleStatus.FAIL, actual_value="7", expected_value="10", explanation="fail", severity=Severity.HIGH, weight=20.0),
    ]
    score, total_w, passed_w, failed_w, review_w, breakdown = scoring.calculate_score(results)
    assert total_w == 60.0
    assert passed_w == 40.0
    assert failed_w == 20.0
    assert score == 66.67

# 10. Risk calculation
def test_risk_calculation():
    risk = RiskService()
    # High failure case
    res_fail = [
        RuleResultDTO(requirement_id="r1", status=RuleStatus.FAIL, actual_value="7", expected_value="10", explanation="turnover below threshold", severity=Severity.HIGH, weight=20.0)
    ]
    risk_level, rec, reasons = risk.evaluate_risk(res_fail)
    assert risk_level == RiskLevel.HIGH
    assert rec == RuleStatus.FAIL

    # Unavailable case
    res_unavail = [
        RuleResultDTO(requirement_id="r1", status=RuleStatus.PASS, actual_value="12", expected_value="10", explanation="ok", severity=Severity.HIGH, weight=20.0),
        RuleResultDTO(requirement_id="r2", status=RuleStatus.UNAVAILABLE, actual_value="DOWN", expected_value="VALID", explanation="timeout", severity=Severity.HIGH, weight=20.0),
    ]
    risk_level2, rec2, reasons2 = risk.evaluate_risk(res_unavail)
    assert risk_level2 == RiskLevel.HIGH
    assert rec2 == RuleStatus.REVIEW

    # All pass case
    res_pass = [
        RuleResultDTO(requirement_id="r1", status=RuleStatus.PASS, actual_value="12", expected_value="10", explanation="ok", severity=Severity.HIGH, weight=20.0),
    ]
    risk_level3, rec3, reasons3 = risk.evaluate_risk(res_pass)
    assert risk_level3 == RiskLevel.LOW
    assert rec3 == RuleStatus.PASS

# 11. Review decision separation
def test_review_decision_creation():
    from app.models import ReviewDecision, OfficerDecisionType
    review = ReviewDecision(
        id="rev-1",
        bid_id="bid-1",
        officer_id="user-1",
        decision=OfficerDecisionType.APPROVED,
        officer_notes="All documents verified against original tender requirements. Recommended for financial bid opening."
    )
    assert review.decision == OfficerDecisionType.APPROVED
    assert "verified" in review.officer_notes

# 12. Audit event generation
def test_audit_event_generation():
    from app.models import AuditEvent
    event = AuditEvent(
        id="aud-1",
        action="RULE_EVALUATED",
        entity_type="Requirement",
        entity_id="req-1",
        user_id="user-1",
        metadata_json={"status": "PASS", "rule": "Turnover"}
    )
    assert event.action == "RULE_EVALUATED"
    assert event.metadata_json["status"] == "PASS"

