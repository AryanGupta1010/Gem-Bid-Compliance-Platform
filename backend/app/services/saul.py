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

    def extract_requirements(self, tender_id: str, tender_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract and strictly validate tender requirements and details from tender pages."""
        if settings.AI_MODE != 'live':
            # Deterministic standard requirements for test mode
            # But the user asked to NOT hardcode even in test mode if possible,
            # actually we can just call the Saul endpoint anyway since it's local.
            pass

        try:
            resp = requests.post(
                f"{self.endpoint}/extract-requirements",
                json={"tender_id": tender_id, "tender_pages": tender_pages},
                timeout=settings.MODEL_TIMEOUT
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_reqs = data.get("requirements", [])
                validated_reqs = []
                for r in raw_reqs:
                    # Ignore extra fields like source_page if they aren't in schema, or add them to schema
                    # Wait, TenderRequirementSchema doesn't have source_page! We should add it.
                    validated_item = TenderRequirementSchema(**{k: v for k, v in r.items() if k in TenderRequirementSchema.model_fields})
                    validated_item_dict = validated_item.model_dump()
                    if "source_page" in r: validated_item_dict["source_page"] = r["source_page"]
                    if "source_text" in r: validated_item_dict["source_text"] = r["source_text"]
                    validated_reqs.append(validated_item_dict)
                return {
                    "requirements": validated_reqs,
                    "tender_details": data.get("tender_details", {})
                }
            else:
                raise AIModelUnavailableError("SAUL", f"Saul service returned HTTP {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as exc:
            logger.error("Saul requirement extraction service unreachable: %s", exc)
            raise AIModelUnavailableError("SAUL", f"Saul requirement extraction service unreachable at {self.endpoint}: {exc}")

def get_saul_service() -> SaulRequirementExtractionService:
    return SaulRequirementExtractionService()
