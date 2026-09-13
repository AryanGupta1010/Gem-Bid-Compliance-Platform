"""
Deterministic Rule Engine for ProcureGuard.

Principle: AI finds and explains evidence.
           Deterministic code verifies facts.
           The Procurement Officer makes the final decision.
"""
import re
import uuid
from typing import Optional
from datetime import datetime, timezone

from app import models
from app.adapters import get_adapter
from app.services.retriever import get_retriever
from app.services.extractor import get_extractor


# ── Value Parsers ─────────────────────────────────────────────────────

def parse_turnover_crore(raw: str) -> Optional[float]:
    """Parse '₹14.2 Crore' → 14.2. Returns None on failure."""
    if not raw:
        return None
    cleaned = raw.replace("₹", "").replace(",", "").strip()
    match = re.search(r"([\d.]+)\s*[Cc]r(?:ore|ores)?", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    # Try plain number
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_percentage(raw: str) -> Optional[float]:
    """Parse '62%' → 62.0. Returns None on failure."""
    if not raw:
        return None
    match = re.search(r"([\d.]+)\s*%", raw)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


# ── Engine ────────────────────────────────────────────────────────────

class DeterministicEngine:
    def __init__(self, db_session):
        self.db = db_session

    def evaluate_document_evidence(self, document_id: str):
        """
        Run the full rule evaluation pipeline for a document.
        Calls retriever → OCR → adapters → deterministic logic.
        """
        doc = self.db.query(models.Document).filter(models.Document.id == document_id).first()
        if not doc:
            return None

        bid = doc.bid
        if not bid:
            return None

        retriever = get_retriever()
        extractor = get_extractor()
        page_count = doc.page_count or 7

        rules_run = []

        # ── Rule 1: Minimum Turnover (≥ 10 Crore) ────────────────────
        ret = retriever.retrieve(doc.id, doc.hash_sha3_512, "RULE-TURNOVER", page_count=page_count)
        ext_res = extractor.extract_field(ret["retrieved_text"], "RULE-TURNOVER")
        
        turnover_val = parse_turnover_crore(ext_res.get("extracted_value") or "")

        # Default requirement if not set could be from tender, here we assume 10 Cr
        if turnover_val is not None and turnover_val >= 10:
            turnover_result = "PASS"
        elif turnover_val is not None and turnover_val < 10:
            turnover_result = "FAIL"
        else:
            turnover_result = "REVIEW"  # Unclear / unparseable → REVIEW

        rules_run.append(self._make_rule(
            bid=bid, doc=doc, rule_id="RULE-TURNOVER",
            rule_name="Minimum Turnover",
            description="Average annual turnover must be at least ₹10 Crore.",
            extracted=ext_res["extracted_value"] or "Not found",
            expected="≥ ₹10 Crore",
            result=turnover_result,
            confidence=ext_res["confidence"],
            page=ret["page_number"],
            bbox=ret["bounding_box"],
            source=ext_res["method"],
            model=ret["model"]
        ))

        # ── Rule 2: Active GST Registration ──────────────────────────
        ret_gst = retriever.retrieve(doc.id, doc.hash_sha3_512, "RULE-GST", page_count=page_count)
        ext_gst = extractor.extract_field(ret_gst["retrieved_text"], "RULE-GST")
        
        gst_adapter = get_adapter("GST")
        actual_gstin = ext_gst.get("extracted_value", "")
        gst_res = gst_adapter.verify({"gstin": actual_gstin})

        gst_result = "PASS"
        gst_extracted = gst_res.get("status", "UNKNOWN")
        if gst_res.get("status") == "SUSPENDED" or gst_res.get("status") == "NOT_FOUND":
            gst_result = "FAIL"
        elif gst_res.get("status") == "UNAVAILABLE" or gst_res.get("response_code") != 200:
            gst_result = "REVIEW"  # UNAVAILABLE → REVIEW
        elif ext_gst["confidence"] < 0.6:
            gst_result = "REVIEW"  # Extraction low confidence

        rules_run.append(self._make_rule(
            bid=bid, doc=doc, rule_id="RULE-GST",
            rule_name="Active GST Registration",
            description="GST registration must be active and match the bidder identity.",
            extracted=gst_extracted,
            expected="ACTIVE",
            result=gst_result,
            confidence=ext_gst["confidence"],
            page=ret_gst["page_number"],
            bbox=ret_gst["bounding_box"],
            source=gst_res.get("source", "GSTN Verification Adapter"),
            model=ret_gst["model"],
            evidence_extra=f"API status={gst_res.get('status')}, code={gst_res.get('response_code')}, GSTIN={actual_gstin}"
        ))

        # ── Rule 3: CPPP Debarment ───────────────────────────────────
        ret_cppp = retriever.retrieve(doc.id, doc.hash_sha3_512, "RULE-CPPP", page_count=page_count)
        ext_cppp = extractor.extract_field(ret_cppp["retrieved_text"], "RULE-CPPP")
        
        # Determine company name dynamically from bid (or extracted text if available). 
        # CPPP Adapter takes company_name. 
        cppp_adapter = get_adapter("CPPP")
        cppp_res = cppp_adapter.verify({"company_name": bid.bidder_name})
        
        cppp_result = "PASS"
        if ext_cppp.get("extracted_value") == "True (debarred)":
            cppp_result = "FAIL"
        elif cppp_res.get("debarred"):
            cppp_result = "FAIL"
        elif ext_cppp["confidence"] < 0.5:
            cppp_result = "REVIEW"

        rules_run.append(self._make_rule(
            bid=bid, doc=doc, rule_id="RULE-CPPP",
            rule_name="CPPP Debarment Check",
            description="Bidder must not appear on applicable debarment records.",
            extracted=ext_cppp["extracted_value"] or str(cppp_res.get("debarred", False)),
            expected="False (not debarred)",
            result=cppp_result,
            confidence=ext_cppp["confidence"],
            page=ret_cppp["page_number"],
            bbox=ret_cppp["bounding_box"],
            source=cppp_res.get("source", "CPPP Debarment Adapter"),
            model=ret_cppp["model"],
            evidence_extra=cppp_res.get("reason", "No record found on debarment list.")
        ))

        # ── Rule 4: Local Content (≥ 50%) ────────────────────────────
        ret_lc = retriever.retrieve(doc.id, doc.hash_sha3_512, "RULE-LOCAL-CONTENT", page_count=page_count)
        ext_lc = extractor.extract_field(ret_lc["retrieved_text"], "RULE-LOCAL-CONTENT")

        lc_val = parse_percentage(ext_lc.get("extracted_value") or "")

        if "conflict" in (ext_lc.get("extracted_value") or "").lower():
            lc_result = "REVIEW"
        elif lc_val is not None and lc_val >= 50:
            lc_result = "PASS"
        elif lc_val is not None and lc_val < 50:
            lc_result = "FAIL"
        else:
            lc_result = "REVIEW"  # Conflicting or unparseable

        rules_run.append(self._make_rule(
            bid=bid, doc=doc, rule_id="RULE-LOCAL-CONTENT",
            rule_name="Local Content Threshold",
            description="Bidder must meet the minimum Make in India local-content threshold (≥50%).",
            extracted=ext_lc["extracted_value"] or "Not found",
            expected="≥ 50%",
            result=lc_result,
            confidence=ext_lc["confidence"],
            page=ret_lc["page_number"],
            bbox=ret_lc["bounding_box"],
            source=ext_lc["method"],
            model=ret_lc["model"]
        ))

        # ── Rule 5: OEM Authorization ────────────────────────────────
        ret_oem = retriever.retrieve(doc.id, doc.hash_sha3_512, "RULE-OEM", page_count=page_count)
        ext_oem = extractor.extract_field(ret_oem["retrieved_text"], "RULE-OEM")

        oem_result = "PASS"
        oem_val = ext_oem.get("extracted_value") or ""
        if "mismatch" in oem_val.lower() or "missing" in oem_val.lower():
            oem_result = "FAIL"
        elif ext_oem["confidence"] < 0.7:
            oem_result = "REVIEW"

        rules_run.append(self._make_rule(
            bid=bid, doc=doc, rule_id="RULE-OEM",
            rule_name="OEM Authorization",
            description="Authorization from the original equipment manufacturer is required.",
            extracted=oem_val or "Not found",
            expected="Valid authorization matching bidder identity",
            result=oem_result,
            confidence=ext_oem["confidence"],
            page=ret_oem["page_number"],
            bbox=ret_oem["bounding_box"],
            source=ext_oem["method"],
            model=ret_oem["model"]
        ))

        # ── Commit rules (upsert) ────────────────────────────────────
        for r in rules_run:
            old_r = self.db.query(models.RuleResult).filter(
                models.RuleResult.bid_id == bid.id,
                models.RuleResult.rule_id == r.rule_id
            ).first()
            if old_r:
                self.db.delete(old_r)
            self.db.add(r)

            self.db.add(models.AuditEvent(
                time=datetime.now(timezone.utc).isoformat(),
                actor="System (Rule Engine)",
                action=f"Rule Evaluated: {r.rule_name}",
                document=doc.filename,
                hash=doc.hash_sha3_512,
                rule=r.rule_name,
                result=r.result,
                source=r.source
            ))

        # ── Aggregate ────────────────────────────────────────────────
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
            bid.summary = f"{review} rule(s) require officer attention due to unclear or unavailable evidence."
        else:
            bid.risk = "LOW"
            bid.status = "PASS"
            bid.summary = "Complete and internally consistent evidence package. All mandatory requirements met."

        bid.score = score
        bid.failed_rules = failed
        bid.review_rules = review

        self.db.commit()
        return bid

    def process_bid(self, bid_id: str):
        """Evaluate all uploaded documents for a bid."""
        bid = self.db.query(models.Bid).filter(models.Bid.id == bid_id).first()
        if not bid:
            return None

        # Find latest document
        doc = self.db.query(models.Document).filter(
            models.Document.bid_id == bid_id
        ).order_by(models.Document.uploaded_at.desc()).first()

        if doc:
            return self.evaluate_document_evidence(doc.id)

        # No documents — everything is REVIEW
        bid.status = "REVIEW"
        bid.risk = "MEDIUM"
        bid.score = 0
        bid.summary = "No documents uploaded yet."
        self.db.commit()
        return bid

    def _make_rule(self, *, bid, doc, rule_id, rule_name, description,
                   extracted, expected, result, confidence, page, bbox,
                   source, model, evidence_extra=None):
        evidence_text = f"Retrieved from Page {page}."
        if bbox:
            evidence_text += f" Region: {bbox}."
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
            rule_version="GeM-Ruleset 1.4.0"
        )
