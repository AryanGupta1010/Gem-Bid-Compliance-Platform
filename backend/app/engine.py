"""
Deterministic Rule Engine for ProcureGuard.

Principle:
  - AI finds and explains evidence (ColPali visual retrieval, Surya OCR, NLI contextual understanding).
  - Trusted sources verify facts (GSTN, CPPP).
  - Deterministic code verifies numbers, dates, thresholds, and statuses.
  - Human Procurement Officer makes the final decision.
"""
import re
import math
import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app import models
from app.adapters import get_adapter
from app.services.retriever import get_retriever
from app.services.ocr import get_ocr
from app.services.extractor import get_extractor
from app.services.nli import get_nli_service
from app.services.exceptions import AIModelUnavailableError

logger = logging.getLogger(__name__)

# ── Value Parsers ─────────────────────────────────────────────────────

def parse_turnover_crore(raw: str) -> Optional[float]:
    """Return crore units; ambiguous, negative and non-finite input is unavailable."""
    if not raw:
        return None
    cleaned = raw.strip().replace(",", "")
    match = re.search(r"(?:₹|INR|Rs\.?)?\s*(-?\d+(?:\.\d+)?)\s*(crores?|cr|lakhs?|lacs?)?", cleaned, re.I)
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    unit = (match.group(2) or "").lower()
    if not math.isfinite(value) or value < 0:
        return None
    if unit.startswith(("lakh", "lac")):
        value /= 100.0
    elif not unit and re.match(r"^(?:₹|INR|Rs\.?)", raw.strip(), re.I):
        value /= 10000000.0
    elif not unit and "," in raw:
        return None
    return value

def parse_percentage(raw: str) -> Optional[float]:
    if not raw:
        return None
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", raw)
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return value if math.isfinite(value) and 0 <= value <= 100 else None

# ── Engine ────────────────────────────────────────────────────────────

class DeterministicEngine:
    def __init__(self, db_session):
        self.db = db_session

    def evaluate_document_evidence(self, document_id: str):
        """
        Run the full rule evaluation pipeline for a document.
        Calls ColPali retrieval → Surya targeted OCR → NLI reasoning → Gov verification → Deterministic rules.
        """
        doc = self.db.query(models.Document).filter(models.Document.id == document_id).first()
        if not doc:
            return None

        bid = doc.bid
        if not bid:
            return None

        tender = bid.tender
        if not tender:
            return None

        retriever = get_retriever()
        ocr_service = get_ocr()
        extractor = get_extractor()
        nli_service = get_nli_service()
        page_count = doc.page_count or 7

        rules_run = []
        
        tender_requirements = self.db.query(models.TenderRequirement).filter(
            models.TenderRequirement.tender_id == tender.id,
            models.TenderRequirement.status != "rejected"
        ).all()
        
        if not tender_requirements:
            logger.warning(f"No tender requirements found for tender {tender.id}. Cannot evaluate bid.")

        for req in tender_requirements:
            rule_id = req.rule_id
            
            # Common retrieval & extraction logic
            ret_data = retriever.retrieve(doc.id, doc.hash_sha3_512, req.description, page_count=page_count)
            ocr_data = ocr_service.extract_field(
                doc.id, doc.hash_sha3_512,
                bounding_box=ret_data["bounding_box"],
                field_type=req.field or "GENERAL",
                page_number=ret_data["page_number"],
                gstin=bid.gstin,
                rule_id=rule_id,
                bidder_hint=bid.bidder_name
            )
            
            extracted_val = ocr_data.get("extracted_value") or ""
            expected_str = str(req.expected_value)
            
            result = "REVIEW"
            evidence_extra = ""
            confidence = ocr_data.get("confidence", 0.90)
            source = f"Surya OCR ({ocr_data.get('model', 'vikp/surya_rec')})"

            # Custom handling for standard well-known rules (if they were extracted and kept their IDs)
            if rule_id == "RULE-TURNOVER" or req.field == "turnover":
                ext_turnover = extractor.extract_field(extracted_val, "RULE-TURNOVER")
                turnover_val = parse_turnover_crore(ext_turnover.get("extracted_value") or "")
                
                try:
                    expected_float = float(expected_str)
                except ValueError:
                    expected_float = 10.0
                
                if turnover_val is not None and turnover_val >= expected_float:
                    result = "PASS"
                elif turnover_val is not None and turnover_val < expected_float:
                    result = "FAIL"
                
                extracted_val = ext_turnover["extracted_value"] or extracted_val
                evidence_extra = f"Numeric evaluation: {turnover_val} Cr >= {expected_float} Cr -> {result}"
                
            elif rule_id == "RULE-GST" or req.field == "gstin":
                ext_gst = extractor.extract_field(extracted_val, "RULE-GST")
                actual_gstin = ext_gst.get("extracted_value", "")
                gst_adapter = get_adapter("GST")
                gst_res = gst_adapter.verify({"gstin": actual_gstin})
                
                gst_status = gst_res.get("status", "UNKNOWN")
                if gst_status in {"SUSPENDED", "NOT_FOUND"} and gst_res.get("response_code") in {200, 404}:
                    result = "FAIL"
                elif gst_status != "ACTIVE" or gst_res.get("response_code") != 200:
                    result = "REVIEW"
                elif ocr_data.get("confidence", 1.0) < 0.6:
                    result = "REVIEW"
                else:
                    result = "PASS"
                    
                extracted_val = f"{actual_gstin} (Status: {gst_status})"
                source = f"{gst_res.get('source', 'GSTN API')} [{gst_res.get('source_type', 'CONTROLLED_SOURCE')}]"
                evidence_extra = f"GSTN registry check: status={gst_status}, HTTP={gst_res.get('response_code')}"
                
            elif rule_id == "RULE-CPPP" or req.field == "debarred":
                ext_cppp = extractor.extract_field(extracted_val, "RULE-CPPP")
                cppp_adapter = get_adapter("CPPP")
                cppp_res = cppp_adapter.verify({"company_name": bid.bidder_name})
                
                if ext_cppp.get("extracted_value") == "True (debarred)":
                    result = "FAIL"
                elif cppp_res.get("debarred") is True and cppp_res.get("response_code") == 200:
                    result = "FAIL"
                elif cppp_res.get("status") == "UNAVAILABLE" or cppp_res.get("response_code") != 200:
                    result = "REVIEW"
                elif ocr_data.get("confidence", 1.0) < 0.5:
                    result = "REVIEW"
                else:
                    result = "PASS"
                    
                extracted_val = "Debarred" if cppp_res.get("debarred") or "debarred" in str(ext_cppp.get("extracted_value", "")).lower() else "Not Debarred"
                source = f"{cppp_res.get('source', 'CPPP Portal')} [{cppp_res.get('source_type', 'CONTROLLED_SOURCE')}]"
                evidence_extra = cppp_res.get("reason", "No debarment record found on CPPP list.")
                
            else:
                # Generic fallback using NLI
                nli_res = nli_service.evaluate(
                    premise=extracted_val,
                    hypothesis=f"The document confirms that {req.name} meets the condition: {req.operator} {expected_str}."
                )
                
                if nli_res.get("label") == "CONTRADICTION":
                    result = "FAIL"
                elif nli_res.get("label") == "ENTAILMENT":
                    result = "PASS"
                else:
                    result = "REVIEW"
                    
                confidence = round((confidence + nli_res.get("confidence", 0.90)) / 2.0, 3)
                source = f"Surya OCR + NLI Reasoning ({nli_res.get('model', 'deberta-v3')})"
                evidence_extra = f"NLI label={nli_res.get('label')} (conf={nli_res.get('confidence')})"
            
            rules_run.append(self._make_rule(
                bid=bid, doc=doc, rule_id=rule_id,
                rule_name=req.name,
                description=req.description,
                extracted=extracted_val,
                expected=f"{req.operator} {expected_str}",
                result=result,
                confidence=confidence,
                page=ret_data["page_number"],
                bbox=ret_data["bounding_box"],
                source=source,
                model=ret_data.get("model", "vidore/colpali-v1.2"),
                evidence_extra=evidence_extra
            ))

        # Atomic commit of rule results
        self.db.query(models.RuleResult).filter(models.RuleResult.bid_id == bid.id).delete(synchronize_session=False)
        for r in rules_run:
            self.db.add(r)
            self.db.add(models.AuditEvent(
                time=datetime.now(timezone.utc).isoformat(),
                actor="System (Deterministic Rule Engine)",
                action=f"Rule Evaluated: {r.rule_name}",
                document=doc.filename,
                hash=doc.hash_sha3_512,
                rule=r.rule_name,
                result=r.result,
                source=f"bid:{bid.id}"
            ))

        # ── Aggregate Compliance & Risk Calculation ──────────────────
        failed = sum(1 for r in rules_run if r.result == "FAIL")
        review = sum(1 for r in rules_run if r.result == "REVIEW")

        score = max(0, 100 - (failed * 20) - (review * 10))

        if failed > 0:
            bid.risk = "CRITICAL" if failed >= 2 else "HIGH"
            bid.status = "FAIL"
            bid.summary = f"{failed} rule(s) failed deterministic evaluation. Officer review required before any procurement decision."
        elif review > 0:
            bid.risk = "MEDIUM"
            bid.status = "REVIEW"
            bid.summary = f"{review} rule(s) require officer attention due to unclear, conflicting, or unavailable evidence."
        else:
            bid.risk = "LOW"
            bid.status = "PASS"
            bid.summary = "Complete and internally consistent evidence package. All mandatory requirements met."

        bid.score = score
        bid.failed_rules = failed
        bid.review_rules = review
        bid.reviewer_decision = bid.reviewer_note = bid.reviewed_at = None

        self.db.commit()
        return bid

    def _make_rule(self, *, bid, doc, rule_id, rule_name, description,
                   extracted, expected, result, confidence, page, bbox,
                   source, model, evidence_extra=None):
        evidence_text = f"Retrieved from Page {page}."
        if bbox:
            evidence_text += f" Bounding Box: {bbox}."
        if evidence_extra:
            evidence_text += f" {evidence_extra}"

        return models.RuleResult(
            id=str(uuid.uuid4()),
            bid_id=bid.id,
            document_id=doc.id,
            rule_id=rule_id,
            rule_name=rule_name,
            description=description,
            extracted_value=str(extracted),
            expected_value=expected,
            result=result,
            confidence=confidence,
            evidence=evidence_text,
            document_name=doc.filename,
            page=page,
            bounding_box=bbox,
            source=source,
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_version=model,
            rule_version="GeM-Ruleset 2.0.0"
        )
