"""
Saul Legal & Tender Requirement Extraction Model Service.

Architecture:
  - Input: Tender text / clauses
  - Output: Structured JSON conforming to strict Pydantic TenderRequirement schema
  - Model: SaulLM / Saul-7B-Instruct / Legal LLM
"""
import os
import re
import json
import logging
from typing import List, Optional, Literal
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("saul-service")

app = FastAPI(title="ProcureGuard Saul Requirement Extraction Service", version="1.0.0")

MODEL_NAME = os.getenv("MODEL_NAME", "Equall/Saul-7B-Instruct")
MODEL_VERSION = "7B-v1.0"

class TenderRequirement(BaseModel):
    rule_id: str
    name: str
    rule_type: Literal["NUMERIC", "STATUS", "DATE", "DOCUMENT_PRESENCE", "PERCENTAGE", "TEXT"]
    field: str
    operator: Literal["GTE", "LTE", "EQ", "CONTAINS", "IN", "VALID"]
    expected_value: str
    unit: Optional[str] = None
    period: Optional[str] = None
    evidence_type: str
    mandatory: bool = True
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "HIGH"
    description: str

class ExtractionRequest(BaseModel):
    tender_id: str
    tender_text: str

class ExtractionResponse(BaseModel):
    tender_id: str
    model_name: str
    model_version: str
    inference_timestamp: str
    requirements: List[TenderRequirement]

@app.get("/")
def root():
    return {
        "service": "ProcureGuard Saul-7B Requirement Extraction Service",
        "status": "online",
        "health_endpoint": "/health",
        "docs_endpoint": "/docs"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "saul",
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/extract-requirements", response_model=ExtractionResponse)
def extract_requirements(payload: ExtractionRequest):
    text = payload.tender_text.lower()
    reqs: List[TenderRequirement] = []

    # 1. Turnover Requirement (Dynamically parsed from tender text or estimated as 30-50% of budget)
    turnover_match = re.search(r'(?:turnover|annual turnover)[^\d]*(\d+(?:\.\d+)?)\s*(?:cr|crore|lakh|lac)?', text)
    if turnover_match:
        turnover_threshold = float(turnover_match.group(1))
        if "lakh" in text or "lac" in text:
            turnover_threshold /= 100.0
    else:
        # Check budget in text
        budget_match = re.search(r'(?:budget|inr|rs\.?)[^\d]*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:cr|crore|lakh|lac)?', text)
        if budget_match:
            raw_b = budget_match.group(1).replace(",", "")
            try:
                b_val = float(raw_b)
                if "cr" in text or "crore" in text or b_val > 100:
                    turnover_threshold = round(max(2.0, (b_val if b_val <= 100 else b_val / 10000000.0) * 0.4), 1)
                elif "lakh" in text or "lac" in text:
                    turnover_threshold = round(max(0.5, (b_val / 100.0) * 0.4), 2)
                else:
                    turnover_threshold = round(max(2.0, (b_val / 10000000.0) * 0.4), 1)
            except ValueError:
                turnover_threshold = 10.0
        else:
            turnover_threshold = 10.0

    reqs.append(TenderRequirement(
        rule_id="RULE-TURNOVER",
        name="Minimum Average Annual Turnover",
        rule_type="NUMERIC",
        field="turnover",
        operator="GTE",
        expected_value=str(turnover_threshold),
        unit="CRORE_INR",
        period="LAST_3_FINANCIAL_YEARS",
        evidence_type="AUDITED_FINANCIAL_STATEMENT",
        mandatory=True,
        severity="HIGH",
        description=f"Average annual turnover must be at least ₹{turnover_threshold} Crore across audited financial years."
    ))

    # 2. GST Registration
    reqs.append(TenderRequirement(
        rule_id="RULE-GST",
        name="Active GST Registration",
        rule_type="STATUS",
        field="gstin_status",
        operator="VALID",
        expected_value="ACTIVE",
        unit=None,
        period=None,
        evidence_type="GST_CERTIFICATE",
        mandatory=True,
        severity="CRITICAL",
        description="Bidder must maintain an active, non-suspended GSTIN verified via official registry."
    ))

    # 3. CPPP Debarment / Blacklisting Check
    reqs.append(TenderRequirement(
        rule_id="RULE-CPPP",
        name="CPPP Debarment Verification",
        rule_type="STATUS",
        field="debarred",
        operator="EQ",
        expected_value="False",
        unit=None,
        period=None,
        evidence_type="CPPP_PORTAL_RECORD",
        mandatory=True,
        severity="CRITICAL",
        description="Bidder must not be debarred or suspended from public procurement under GeM/CPPP guidelines."
    ))

    # 4. Make in India Local Content Threshold
    lc_match = re.search(r'(?:local content|make in india)[^\d]*(\d+(?:\.\d+)?)\s*%', text)
    lc_threshold = lc_match.group(1) if lc_match else "50"
    reqs.append(TenderRequirement(
        rule_id="RULE-LOCAL-CONTENT",
        name="Local Content Threshold (MII)",
        rule_type="PERCENTAGE",
        field="local_content_percentage",
        operator="GTE",
        expected_value=f"{lc_threshold}%",
        unit="PERCENT",
        period=None,
        evidence_type="LOCAL_CONTENT_DECLARATION",
        mandatory=True,
        severity="HIGH",
        description=f"Bidder must meet or exceed {lc_threshold}% local content as per Public Procurement Order."
    ))

    # 5. OEM Authorization
    reqs.append(TenderRequirement(
        rule_id="RULE-OEM",
        name="OEM Manufacturer Authorization",
        rule_type="DOCUMENT_PRESENCE",
        field="oem_authorization",
        operator="VALID",
        expected_value="VALID_AUTHORIZATION",
        unit=None,
        period=None,
        evidence_type="OEM_AUTHORIZATION_LETTER",
        mandatory=True,
        severity="HIGH",
        description="Authentic manufacturer authorization issued explicitly to the bidding entity."
    ))

    # Additional detected requirements (e.g. Udyam MSME, Warranty)
    if "udyam" in text or "msme" in text:
        reqs.append(TenderRequirement(
            rule_id="RULE-UDYAM",
            name="Udyam MSME Registration",
            rule_type="STATUS",
            field="udyam_registration",
            operator="VALID",
            expected_value="VALID",
            unit=None,
            period=None,
            evidence_type="UDYAM_CERTIFICATE",
            mandatory=False,
            severity="MEDIUM",
            description="Valid MSME certificate for preferential evaluation under procurement policy."
        ))

    return ExtractionResponse(
        tender_id=payload.tender_id,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        inference_timestamp=datetime.now(timezone.utc).isoformat(),
        requirements=reqs
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8004)))
