from typing import List, Tuple, Dict, Any
from app.models import RuleStatus, Severity, RiskLevel
from app.rules.engine import RuleResultDTO

class RiskService:
    def evaluate_risk(self, rule_results: List[RuleResultDTO]) -> Tuple[RiskLevel, RuleStatus, List[str]]:
        """
        Determines deterministic risk level, overall recommendation, and risk rationale flags.
        Returns: (risk_level, recommendation, risk_reasons)
        """
        has_critical_failure = False
        has_high_failure = False
        has_medium_failure = False
        has_unavailable = False
        has_review = False
        risk_reasons = []

        for res in rule_results:
            if res.status == RuleStatus.FAIL:
                if res.severity == Severity.CRITICAL:
                    has_critical_failure = True
                    risk_reasons.append(f"Critical rule failure: {res.explanation}")
                elif res.severity == Severity.HIGH:
                    has_high_failure = True
                    risk_reasons.append(f"Mandatory high-severity rule failure: {res.explanation}")
                else:
                    has_medium_failure = True
                    risk_reasons.append(f"Standard rule failure: {res.explanation}")

            elif res.status == RuleStatus.UNAVAILABLE:
                has_unavailable = True
                risk_reasons.append(f"External verification service unavailable: {res.explanation}")

            elif res.status == RuleStatus.REVIEW:
                has_review = True
                risk_reasons.append(f"Ambiguity requiring manual review: {res.explanation}")

        # Deterministic Risk Hierarchy
        if has_critical_failure:
            risk_level = RiskLevel.CRITICAL
            recommendation = RuleStatus.FAIL
        elif has_high_failure:
            risk_level = RiskLevel.HIGH
            recommendation = RuleStatus.FAIL
        elif has_unavailable:
            risk_level = RiskLevel.HIGH if any(r.severity in (Severity.CRITICAL, Severity.HIGH) for r in rule_results if r.status == RuleStatus.UNAVAILABLE) else RiskLevel.MEDIUM
            recommendation = RuleStatus.REVIEW
        elif has_review or has_medium_failure:
            risk_level = RiskLevel.MEDIUM
            recommendation = RuleStatus.REVIEW
        else:
            risk_level = RiskLevel.LOW
            recommendation = RuleStatus.PASS
            risk_reasons.append("All mandatory technical, financial, and regulatory checks satisfied.")

        return risk_level, recommendation, risk_reasons

risk_service = RiskService()
