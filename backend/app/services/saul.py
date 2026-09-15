"""
Tender Requirement Extraction Service (SaulLM).

CRITICAL RULE: NO SILENT AI FALLBACKS IN LIVE MODE.
Calls dedicated Saul requirement extraction microservice.
"""
import logging
import requests
from typing import List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.config import settings
from app.services.exceptions import AIModelUnavailableError, RequirementExtractionFailedError

logger = logging.getLogger(__name__)

class TenderRequirementSchema(BaseModel):
    rule_id: str
    name: str
    rule_type: str
    field: str
    operator: str
    expected_value: str
    unit: str | None = None
    period: str | None = None
    evidence_type: str
    mandatory: bool = True
    severity: str = "HIGH"
    description: str

class SaulRequirementExtractionService:
    def __init__(self):
        self.endpoint = settings.SAUL_URL

    def extract_requirements(self, tender_id: str, tender_text: str) -> List[Dict[str, Any]]:
        """Extract and strictly validate tender requirements from tender text."""
        if settings.AI_MODE != 'live':
            # Deterministic standard requirements for test mode
            return [
                {
                    "rule_id": "RULE-TURNOVER", "name": "Minimum Average Annual Turnover", "rule_type": "NUMERIC",
                    "field": "turnover", "operator": "GTE", "expected_value": "10.0", "unit": "CRORE_INR",
                    "evidence_type": "AUDITED_FINANCIAL_STATEMENT", "mandatory": True, "severity": "HIGH",
                    "description": "Average annual turnover must be at least ₹10 Crore."
                },
                {
                    "rule_id": "RULE-GST", "name": "Active GST Registration", "rule_type": "STATUS",
                    "field": "gstin", "operator": "VALID", "expected_value": "ACTIVE",
                    "evidence_type": "GST_CERTIFICATE", "mandatory": True, "severity": "CRITICAL",
                    "description": "GST registration must be active."
                },
                {
                    "rule_id": "RULE-CPPP", "name": "CPPP Debarment Verification", "rule_type": "STATUS",
                    "field": "debarred", "operator": "EQ", "expected_value": "False",
                    "evidence_type": "CPPP_RECORD", "mandatory": True, "severity": "CRITICAL",
                    "description": "Bidder must not be debarred."
                },
                {
                    "rule_id": "RULE-LOCAL-CONTENT", "name": "Local Content Threshold", "rule_type": "PERCENTAGE",
                    "field": "local_content", "operator": "GTE", "expected_value": "50%",
                    "evidence_type": "LOCAL_CONTENT_DECLARATION", "mandatory": True, "severity": "HIGH",
                    "description": "Local content must be at least 50%."
                },
                {
                    "rule_id": "RULE-OEM", "name": "OEM Authorization", "rule_type": "DOCUMENT_PRESENCE",
                    "field": "oem_authorization", "operator": "VALID", "expected_value": "VALID",
                    "evidence_type": "OEM_AUTHORIZATION_LETTER", "mandatory": True, "severity": "HIGH",
                    "description": "Valid OEM authorization letter."
                }
            ]

        try:
            resp = requests.post(
                f"{self.endpoint}/extract-requirements",
                json={"tender_id": tender_id, "tender_text": tender_text},
                timeout=settings.MODEL_TIMEOUT
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_reqs = data.get("requirements", [])
                validated = []
                for r in raw_reqs:
                    validated_item = TenderRequirementSchema(**r)
                    validated.append(validated_item.model_dump())
                return validated
            else:
                raise AIModelUnavailableError("SAUL", f"Saul service returned HTTP {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as exc:
            logger.error("Saul requirement extraction service unreachable: %s", exc)
            raise AIModelUnavailableError("SAUL", f"Saul requirement extraction service unreachable at {self.endpoint}: {exc}")

def get_saul_service() -> SaulRequirementExtractionService:
    return SaulRequirementExtractionService()
