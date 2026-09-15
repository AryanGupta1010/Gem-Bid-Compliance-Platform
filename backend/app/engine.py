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

        retriever = get_retriever()
        ocr_service = get_ocr()
        extractor = get_extractor()
        nli_service = get_nli_service()
        page_count = doc.page_count or 7

        rules_run = []

        # ── Rule 1: Minimum Turnover (≥ 10 Crore) ────────────────────
        ret_turnover = retriever.retrieve(doc.id, doc.hash_sha3_512, "RULE-TURNOVER", page_count=page_count)
        ocr_turnover = ocr_service.extract_field(
            doc.id, doc.hash_sha3_512,
            bounding_box=ret_turnover["bounding_box"],
            field_type="TURNOVER",
            page_number=ret_turnover["page_number"],
            gstin=bid.gstin,
            rule_id="RULE-TURNOVER",
            bidder_hint=bid.bidder_name
        )
        ext_turnover = extractor.extract_field(ocr_turnover["extracted_value"], "RULE-TURNOVER")
        turnover_val = parse_turnover_crore(ext_turnover.get("extracted_value") or "")

        if turnover_val is not None and turnover_val >= 10.0:
            turnover_result = "PASS"
        elif turnover_val is not None and turnover_val < 10.0:
            turnover_result = "FAIL"
        else:
            turnover_result = "REVIEW"

        rules_run.append(self._make_rule(
            bid=bid, doc=doc, rule_id="RULE-TURNOVER",
            rule_name="Minimum Turnover",
            description="Average annual turnover must be at least ₹10 Crore.",
            extracted=ext_turnover["extracted_value"] or ocr_turnover["extracted_value"],
            expected="≥ ₹10 Crore",
            result=turnover_result,
            confidence=ocr_turnover.get("confidence", 0.95),
            page=ret_turnover["page_number"],
            bbox=ret_turnover["bounding_box"],
            source=f"Surya OCR ({ocr_turnover.get('model', 'vikp/surya_rec')})",
            model=ret_turnover.get("model", "vidore/colpali-v1.2"),
            evidence_extra=f"Numeric evaluation: {turnover_val} Cr >= 10.0 Cr -> {turnover_result}"
        ))

        # ── Rule 2: Active GST Registration ──────────────────────────
        ret_gst = retriever.retrieve(doc.id, doc.hash_sha3_512, "RULE-GST", page_count=page_count)
        ocr_gst = ocr_service.extract_field(
            doc.id, doc.hash_sha3_512,
            bounding_box=ret_gst["bounding_box"],
            field_type="GST",
            page_number=ret_gst["page_number"],
            gstin=bid.gstin,
            rule_id="RULE-GST",
            bidder_hint=bid.bidder_name
        )
        ext_gst = extractor.extract_field(ocr_gst["extracted_value"], "RULE-GST")
        actual_gstin = ext_gst.get("extracted_value", "")

        gst_adapter = get_adapter("GST")
        gst_res = gst_adapter.verify({"gstin": actual_gstin})

        gst_result = "PASS"
        gst_status = gst_res.get("status", "UNKNOWN")
        if gst_status in {"SUSPENDED", "NOT_FOUND"} and gst_res.get("response_code") in {200, 404}:
            gst_result = "FAIL"
        elif gst_status != "ACTIVE" or gst_res.get("response_code") != 200:
            gst_result = "REVIEW"
        elif ocr_gst.get("confidence", 1.0) < 0.6:
            gst_result = "REVIEW"

        rules_run.append(self._make_rule(
            bid=bid, doc=doc, rule_id="RULE-GST",
            rule_name="Active GST Registration",
            description="GST registration must be active and match the bidder identity.",
            extracted=f"{actual_gstin} (Status: {gst_status})",
            expected="ACTIVE",
            result=gst_result,
            confidence=ocr_gst.get("confidence", 0.96),
            page=ret_gst["page_number"],
            bbox=ret_gst["bounding_box"],
            source=f"{gst_res.get('source', 'GSTN API')} [{gst_res.get('source_type', 'CONTROLLED_SOURCE')}]",
            model=ret_gst.get("model", "vidore/colpali-v1.2"),
            evidence_extra=f"GSTN registry check: status={gst_status}, HTTP={gst_res.get('response_code')}"
        ))

        # ── Rule 3: CPPP Debarment Check ─────────────────────────────
        ret_cppp = retriever.retrieve(doc.id, doc.hash_sha3_512, "RULE-CPPP", page_count=page_count)
        ocr_cppp = ocr_service.extract_field(
            doc.id, doc.hash_sha3_512,
            bounding_box=ret_cppp["bounding_box"],
            field_type="CPPP",
            page_number=ret_cppp["page_number"],
            gstin=bid.gstin,
            rule_id="RULE-CPPP",
            bidder_hint=bid.bidder_name
        )
        ext_cppp = extractor.extract_field(ocr_cppp["extracted_value"], "RULE-CPPP")

        cppp_adapter = get_adapter("CPPP")
        cppp_res = cppp_adapter.verify({"company_name": bid.bidder_name})

        cppp_result = "PASS"
        if ext_cppp.get("extracted_value") == "True (debarred)":
            cppp_result = "FAIL"
        elif cppp_res.get("debarred") is True and cppp_res.get("response_code") == 200:
            cppp_result = "FAIL"
        elif cppp_res.get("status") == "UNAVAILABLE" or cppp_res.get("response_code") != 200:
            cppp_result = "REVIEW"
        elif ocr_cppp.get("confidence", 1.0) < 0.5:
            cppp_result = "REVIEW"

        rules_run.append(self._make_rule(
            bid=bid, doc=doc, rule_id="RULE-CPPP",
            rule_name="CPPP Debarment Check",
            description="Bidder must not appear on applicable government debarment records.",
            extracted="Debarred" if cppp_res.get("debarred") or "debarred" in str(ext_cppp.get("extracted_value", "")).lower() else "Not Debarred",
            expected="False (not debarred)",
            result=cppp_result,
            confidence=ocr_cppp.get("confidence", 0.98),
            page=ret_cppp["page_number"],
            bbox=ret_cppp["bounding_box"],
            source=f"{cppp_res.get('source', 'CPPP Portal')} [{cppp_res.get('source_type', 'CONTROLLED_SOURCE')}]",
            model=ret_cppp.get("model", "vidore/colpali-v1.2"),
            evidence_extra=cppp_res.get("reason", "No debarment record found on CPPP list.")
        ))

        # ── Rule 4: Local Content (≥ 50%) with NLI Contextual Check ──
        ret_lc = retriever.retrieve(doc.id, doc.hash_sha3_512, "RULE-LOCAL-CONTENT", page_count=page_count)
        ocr_lc = ocr_service.extract_field(
            doc.id, doc.hash_sha3_512,
            bounding_box=ret_lc["bounding_box"],
            field_type="LOCAL_CONTENT",
            page_number=ret_lc["page_number"],
            gstin=bid.gstin,
            rule_id="RULE-LOCAL-CONTENT",
            bidder_hint=bid.bidder_name
        )
        ext_lc = extractor.extract_field(ocr_lc["extracted_value"], "RULE-LOCAL-CONTENT")
        lc_val = parse_percentage(ext_lc.get("extracted_value") or "")

        # NLI contextual reasoning to detect conflicting or ambiguous declarations
        nli_res = nli_service.evaluate(
            premise=ocr_lc["extracted_value"],
            hypothesis="Bidder certifies compliance with minimum 50 percent local content threshold without contradictions."
        )

        if "conflict" in (ext_lc.get("extracted_value") or "").lower() or nli_res.get("label") == "NEUTRAL":
            lc_result = "REVIEW"
        elif nli_res.get("label") == "CONTRADICTION" or (lc_val is not None and lc_val < 50.0):
            lc_result = "FAIL"
        elif lc_val is not None and lc_val >= 50.0:
            lc_result = "PASS"
        else:
            lc_result = "REVIEW"

        rules_run.append(self._make_rule(
            bid=bid, doc=doc, rule_id="RULE-LOCAL-CONTENT",
            rule_name="Local Content Threshold",
            description="Bidder must meet the minimum Make in India local-content threshold (≥50%).",
            extracted=f"{ext_lc['extracted_value'] or ocr_lc['extracted_value']} (NLI: {nli_res.get('label')})",
            expected="≥ 50%",
            result=lc_result,
            confidence=round((ocr_lc.get("confidence", 0.92) + nli_res.get("confidence", 0.90)) / 2.0, 3),
            page=ret_lc["page_number"],
            bbox=ret_lc["bounding_box"],
            source=f"Surya OCR + NLI Reasoning ({nli_res.get('model', 'deberta-v3')})",
            model=ret_lc.get("model", "vidore/colpali-v1.2"),
            evidence_extra=f"NLI label={nli_res.get('label')} (conf={nli_res.get('confidence')})"
        ))

        # ── Rule 5: OEM Authorization with NLI Check ─────────────────
        ret_oem = retriever.retrieve(doc.id, doc.hash_sha3_512, "RULE-OEM", page_count=page_count)
        ocr_oem = ocr_service.extract_field(
            doc.id, doc.hash_sha3_512,
            bounding_box=ret_oem["bounding_box"],
            field_type="OEM",
            page_number=ret_oem["page_number"],
            gstin=bid.gstin,
            rule_id="RULE-OEM",
            bidder_hint=bid.bidder_name
        )
        ext_oem = extractor.extract_field(ocr_oem["extracted_value"], "RULE-OEM")
        oem_raw = ocr_oem["extracted_value"]

        nli_oem = nli_service.evaluate(
            premise=oem_raw,
            hypothesis=f"Manufacturer explicitly authorizes {bid.bidder_name} to supply and support products."
        )

        oem_val = ext_oem.get("extracted_value") or ""
        if nli_oem.get("label") == "CONTRADICTION" or "mismatch" in oem_raw.lower() or "missing" in oem_raw.lower():
            oem_result = "FAIL"
            oem_val = f"OEM recipient mismatch: {oem_raw}"
        elif nli_oem.get("label") == "NEUTRAL" or ocr_oem.get("confidence", 1.0) < 0.7:
            oem_result = "REVIEW"
            oem_val = "Authorization recipient could not be conclusively verified"
        else:
            oem_result = "PASS"
            oem_val = f"Verified OEM Authorization: {bid.bidder_name}"

        rules_run.append(self._make_rule(
            bid=bid, doc=doc, rule_id="RULE-OEM",
            rule_name="OEM Authorization",
            description="Authorization from the original equipment manufacturer is required.",
            extracted=oem_val,
            expected="Valid authorization matching bidder identity",
            result=oem_result,
            confidence=round((ocr_oem.get("confidence", 0.94) + nli_oem.get("confidence", 0.92)) / 2.0, 3),
            page=ret_oem["page_number"],
            bbox=ret_oem["bounding_box"],
            source=f"Surya OCR + NLI Reasoning ({nli_oem.get('model', 'deberta-v3')})",
            model=ret_oem.get("model", "vidore/colpali-v1.2"),
            evidence_extra=f"NLI label={nli_oem.get('label')} (conf={nli_oem.get('confidence')})"
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
