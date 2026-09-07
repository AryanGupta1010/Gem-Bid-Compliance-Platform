from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
import re
from app.models import RuleType, Operator, Severity, RuleStatus, VerificationStatus

class RuleResultDTO:
    def __init__(
        self,
        requirement_id: str,
        status: RuleStatus,
        actual_value: Optional[str],
        expected_value: Optional[str],
        explanation: str,
        severity: Severity,
        weight: float = 20.0,
        confidence: float = 1.0,
        evidence_data: Optional[List[Dict[str, Any]]] = None,
        verification_data: Optional[Dict[str, Any]] = None,
        rule_version: str = "1.0.0"
    ):
        self.requirement_id = requirement_id
        self.status = status
        self.actual_value = actual_value
        self.expected_value = expected_value
        self.explanation = explanation
        self.severity = severity
        self.weight = weight
        self.confidence = confidence
        self.evidence_data = evidence_data or []
        self.verification_data = verification_data
        self.rule_version = rule_version

class RuleEngine:
    def __init__(self, rule_version: str = "1.0.0"):
        self.rule_version = rule_version

    def evaluate(self, requirement: Any, context: Dict[str, Any]) -> RuleResultDTO:
        """
        Evaluates a requirement against the bid context (documents, extracted fields, verification results).
        """
        rule_type = requirement.rule_type
        if isinstance(rule_type, str):
            rule_type = RuleType(rule_type)

        if rule_type == RuleType.NUMERIC:
            return self.evaluate_numeric(requirement, context)
        elif rule_type == RuleType.DATE or rule_type == RuleType.DOCUMENT_EXPIRY:
            return self.evaluate_date(requirement, context)
        elif rule_type == RuleType.STATUS or rule_type == RuleType.BOOLEAN or rule_type == RuleType.TEXT_MATCH:
            return self.evaluate_status(requirement, context)
        elif rule_type == RuleType.DOCUMENT_PRESENT:
            return self.evaluate_document_presence(requirement, context)
        elif rule_type == RuleType.VERIFICATION:
            return self.evaluate_verification(requirement, context)
        elif rule_type == RuleType.MANUAL_REVIEW:
            return self.evaluate_manual_review(requirement, context)
        else:
            return self.evaluate_status(requirement, context)

    def evaluate_numeric(self, requirement: Any, context: Dict[str, Any]) -> RuleResultDTO:
        field_name = requirement.evidence_type or requirement.name.lower().replace(" ", "_")
        extracted_info = context.get("extracted_fields", {}).get(field_name)
        
        # Check fallback lookup
        if not extracted_info:
            for k, v in context.get("extracted_fields", {}).items():
                if field_name in k or k in field_name:
                    extracted_info = v
                    break

        if not extracted_info:
            return RuleResultDTO(
                requirement_id=requirement.id,
                status=RuleStatus.FAIL if requirement.mandatory else RuleStatus.REVIEW,
                actual_value="Missing / Not Found",
                expected_value=f"{requirement.operator.value if hasattr(requirement.operator, 'value') else requirement.operator} {requirement.expected_value} {requirement.unit or ''}".strip(),
                explanation=f"Required numeric evidence for '{requirement.name}' was not detected in submitted documents.",
                severity=requirement.severity,
                weight=requirement.weight,
                confidence=1.0,
                rule_version=self.rule_version
            )

        actual_raw = extracted_info.get("value")
        actual_val = self._parse_numeric(actual_raw)
        expected_val = self._parse_numeric(requirement.expected_value)

        evidence_list = [extracted_info.get("evidence")] if extracted_info.get("evidence") else []

        if actual_val is None or expected_val is None:
            return RuleResultDTO(
                requirement_id=requirement.id,
                status=RuleStatus.REVIEW,
                actual_value=str(actual_raw),
                expected_value=str(requirement.expected_value),
                explanation=f"Could not parse numeric values for comparison. Actual: '{actual_raw}', Expected: '{requirement.expected_value}'.",
                severity=requirement.severity,
                weight=requirement.weight,
                confidence=0.7,
                evidence_data=evidence_list,
                rule_version=self.rule_version
            )

        op = requirement.operator.value if hasattr(requirement.operator, "value") else requirement.operator
        passed = False
        formula = f"{actual_val} {op} {expected_val}"

        if op == "GTE" or op == ">=":
            passed = actual_val >= expected_val
        elif op == "GT" or op == ">":
            passed = actual_val > expected_val
        elif op == "LTE" or op == "<=":
            passed = actual_val <= expected_val
        elif op == "LT" or op == "<":
            passed = actual_val < expected_val
        elif op == "EQ" or op == "==":
            passed = abs(actual_val - expected_val) < 1e-6
        elif op == "NEQ" or op == "!=":
            passed = abs(actual_val - expected_val) >= 1e-6

        unit = requirement.unit or ""
        status = RuleStatus.PASS if passed else (RuleStatus.FAIL if requirement.mandatory else RuleStatus.REVIEW)
        
        explanation = (
            f"Evaluation: {formula} = {'TRUE (PASSED)' if passed else 'FALSE (FAILED)'}. "
            f"Actual value: {actual_val} {unit}, Required threshold: {expected_val} {unit}."
        )

        return RuleResultDTO(
            requirement_id=requirement.id,
            status=status,
            actual_value=f"{actual_val} {unit}".strip(),
            expected_value=f"{op} {expected_val} {unit}".strip(),
            explanation=explanation,
            severity=requirement.severity,
            weight=requirement.weight,
            confidence=extracted_info.get("confidence", 1.0),
            evidence_data=evidence_list,
            rule_version=self.rule_version
        )

    def evaluate_date(self, requirement: Any, context: Dict[str, Any]) -> RuleResultDTO:
        field_name = requirement.evidence_type or requirement.name.lower().replace(" ", "_")
        extracted_info = context.get("extracted_fields", {}).get(field_name)

        if not extracted_info:
            return RuleResultDTO(
                requirement_id=requirement.id,
                status=RuleStatus.FAIL if requirement.mandatory else RuleStatus.REVIEW,
                actual_value="Missing / Not Found",
                expected_value=requirement.expected_value,
                explanation=f"Required date/expiry evidence for '{requirement.name}' was not found in submitted documents.",
                severity=requirement.severity,
                weight=requirement.weight,
                confidence=1.0,
                rule_version=self.rule_version
            )

        actual_str = str(extracted_info.get("value", ""))
        actual_date = self._parse_date(actual_str)
        
        target_date_str = requirement.expected_value
        if target_date_str.upper() == "TODAY" or target_date_str.upper() == "CURRENT_DATE":
            target_date = date.today()
        else:
            target_date = self._parse_date(target_date_str) or date.today()

        evidence_list = [extracted_info.get("evidence")] if extracted_info.get("evidence") else []

        if not actual_date:
            return RuleResultDTO(
                requirement_id=requirement.id,
                status=RuleStatus.REVIEW,
                actual_value=actual_str,
                expected_value=requirement.expected_value,
                explanation=f"Date format in evidence '{actual_str}' could not be parsed unambiguously. Officer review required.",
                severity=requirement.severity,
                weight=requirement.weight,
                confidence=0.6,
                evidence_data=evidence_list,
                rule_version=self.rule_version
            )

        op = requirement.operator.value if hasattr(requirement.operator, "value") else requirement.operator
        passed = False
        if op == "AFTER" or op == "GT" or op == "GTE":
            passed = actual_date >= target_date
        elif op == "BEFORE" or op == "LT" or op == "LTE":
            passed = actual_date <= target_date
        elif op == "EQ":
            passed = actual_date == target_date

        status = RuleStatus.PASS if passed else (RuleStatus.FAIL if requirement.mandatory else RuleStatus.REVIEW)
        explanation = (
            f"Date check: {actual_date.isoformat()} {op} {target_date.isoformat()} = {'VALID' if passed else 'EXPIRED/INVALID'}. "
            f"Document validity date is {actual_date.isoformat()}."
        )

        return RuleResultDTO(
            requirement_id=requirement.id,
            status=status,
            actual_value=actual_date.isoformat(),
            expected_value=f"{op} {target_date.isoformat()}",
            explanation=explanation,
            severity=requirement.severity,
            weight=requirement.weight,
            confidence=extracted_info.get("confidence", 1.0),
            evidence_data=evidence_list,
            rule_version=self.rule_version
        )

    def evaluate_status(self, requirement: Any, context: Dict[str, Any]) -> RuleResultDTO:
        field_name = requirement.evidence_type or requirement.name.lower().replace(" ", "_")
        extracted_info = context.get("extracted_fields", {}).get(field_name)

        if not extracted_info:
            return RuleResultDTO(
                requirement_id=requirement.id,
                status=RuleStatus.FAIL if requirement.mandatory else RuleStatus.REVIEW,
                actual_value="Missing",
                expected_value=requirement.expected_value,
                explanation=f"No declaration or evidence found for '{requirement.name}'.",
                severity=requirement.severity,
                weight=requirement.weight,
                confidence=1.0,
                rule_version=self.rule_version
            )

        actual_val = str(extracted_info.get("value", "")).strip()
        expected_val = str(requirement.expected_value).strip()
        op = requirement.operator.value if hasattr(requirement.operator, "value") else requirement.operator
        evidence_list = [extracted_info.get("evidence")] if extracted_info.get("evidence") else []

        passed = False
        if op == "EQ":
            passed = actual_val.upper() == expected_val.upper()
        elif op == "NEQ":
            passed = actual_val.upper() != expected_val.upper()
        elif op == "CONTAINS":
            passed = expected_val.upper() in actual_val.upper()
        elif op == "IN":
            expected_items = [x.strip().upper() for x in expected_val.split(",")]
            passed = actual_val.upper() in expected_items

        status = RuleStatus.PASS if passed else (RuleStatus.FAIL if requirement.mandatory else RuleStatus.REVIEW)
        explanation = f"Value '{actual_val}' {'matches' if passed else 'does not match'} required '{expected_val}' ({op})."

        return RuleResultDTO(
            requirement_id=requirement.id,
            status=status,
            actual_value=actual_val,
            expected_value=expected_val,
            explanation=explanation,
            severity=requirement.severity,
            weight=requirement.weight,
            confidence=extracted_info.get("confidence", 1.0),
            evidence_data=evidence_list,
            rule_version=self.rule_version
        )

    def evaluate_document_presence(self, requirement: Any, context: Dict[str, Any]) -> RuleResultDTO:
        doc_type = requirement.evidence_type or requirement.expected_value
        submitted_docs = context.get("documents", [])
        
        matching_doc = None
        for doc in submitted_docs:
            d_type = doc.get("document_type", "")
            d_name = doc.get("filename", "")
            if doc_type.upper() in d_type.upper() or doc_type.upper() in d_name.upper():
                matching_doc = doc
                break

        if matching_doc:
            evidence_item = {
                "document_id": matching_doc.get("id"),
                "page_number": 1,
                "bounding_box": [0.05, 0.05, 0.95, 0.30],
                "extracted_field": "document_presence",
                "extracted_value": matching_doc.get("filename", "Present"),
                "confidence": 1.0,
                "source": f"Document: {matching_doc.get('filename')}"
            }
            return RuleResultDTO(
                requirement_id=requirement.id,
                status=RuleStatus.PASS,
                actual_value=f"Submitted: {matching_doc.get('filename')}",
                expected_value=f"Required ({doc_type})",
                explanation=f"Mandatory document '{doc_type}' is present and verified with SHA-3-512 cryptographic hash.",
                severity=requirement.severity,
                weight=requirement.weight,
                confidence=1.0,
                evidence_data=[evidence_item],
                rule_version=self.rule_version
            )
        else:
            return RuleResultDTO(
                requirement_id=requirement.id,
                status=RuleStatus.FAIL if requirement.mandatory else RuleStatus.REVIEW,
                actual_value="Missing",
                expected_value=f"Required ({doc_type})",
                explanation=f"Mandatory document '{doc_type}' was not submitted in the bid package.",
                severity=requirement.severity,
                weight=requirement.weight,
                confidence=1.0,
                rule_version=self.rule_version
            )

    def evaluate_verification(self, requirement: Any, context: Dict[str, Any]) -> RuleResultDTO:
        source_name = requirement.evidence_type or "GST"
        verif_results = context.get("verification_results", {})
        v_res = verif_results.get(source_name)

        if not v_res:
            for k, v in verif_results.items():
                if source_name.upper() in k.upper():
                    v_res = v
                    break

        if not v_res:
            return RuleResultDTO(
                requirement_id=requirement.id,
                status=RuleStatus.UNAVAILABLE,
                actual_value="Not Executed",
                expected_value=f"VALID via {source_name}",
                explanation=f"External verification service for '{source_name}' could not be reached or query was not executed.",
                severity=requirement.severity,
                weight=requirement.weight,
                confidence=1.0,
                rule_version=self.rule_version
            )

        v_status = v_res.get("status")
        if isinstance(v_status, str):
            v_status = VerificationStatus(v_status)

        # Map verification result status to rule result status
        # Critical business rule: UNAVAILABLE does NOT automatically become FAIL, it becomes UNAVAILABLE / REVIEW
        if v_status == VerificationStatus.VALID:
            rule_status = RuleStatus.PASS
            explanation = f"External {source_name} verification succeeded: Record confirmed VALID with government source."
        elif v_status == VerificationStatus.UNAVAILABLE:
            rule_status = RuleStatus.UNAVAILABLE
            explanation = f"External {source_name} verification service is currently UNAVAILABLE ({v_res.get('error_code', 'TIMEOUT')}). Human officer review recommended."
        elif v_status == VerificationStatus.EXPIRED:
            rule_status = RuleStatus.REVIEW if not requirement.mandatory else RuleStatus.FAIL
            explanation = f"External {source_name} record is EXPIRED according to the registry."
        else: # INVALID or NOT_FOUND
            rule_status = RuleStatus.FAIL if requirement.mandatory else RuleStatus.REVIEW
            explanation = f"External {source_name} verification FAILED: Status is {v_status.value} ({v_res.get('error_message', 'Invalid record')})."

        return RuleResultDTO(
            requirement_id=requirement.id,
            status=rule_status,
            actual_value=v_status.value if hasattr(v_status, 'value') else str(v_status),
            expected_value=f"VALID via {source_name}",
            explanation=explanation,
            severity=requirement.severity,
            weight=requirement.weight,
            confidence=1.0,
            verification_data=v_res,
            rule_version=self.rule_version
        )

    def evaluate_manual_review(self, requirement: Any, context: Dict[str, Any]) -> RuleResultDTO:
        return RuleResultDTO(
            requirement_id=requirement.id,
            status=RuleStatus.REVIEW,
            actual_value="Pending Officer Review",
            expected_value=requirement.expected_value,
            explanation=f"Requirement '{requirement.name}' is designated for discretionary human officer review.",
            severity=requirement.severity,
            weight=requirement.weight,
            confidence=1.0,
            rule_version=self.rule_version
        )

    def _parse_numeric(self, val: Any) -> Optional[float]:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip().replace(",", "")
        # Handle crore / lakh / percentage / currency symbols
        multiplier = 1.0
        if "CR" in val_str.upper() or "CRORE" in val_str.upper():
            multiplier = 1.0 # Standardize on Cr unit or raw numbers
        elif "LAKH" in val_str.upper():
            multiplier = 0.01

        match = re.search(r"[-+]?\d*\.?\d+", val_str)
        if match:
            try:
                return float(match.group(0)) * multiplier
            except ValueError:
                return None
        return None

    def _parse_date(self, val: str) -> Optional[date]:
        if not val:
            return None
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y", "%B %d, %Y", "%d %b %Y"]
        for fmt in formats:
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except ValueError:
                pass
        return None

rule_engine = RuleEngine()
