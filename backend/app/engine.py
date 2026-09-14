"""
Deterministic Rule Engine for ProcureGuard.

Principle: AI finds and explains evidence.
           Deterministic code verifies facts.
           The Procurement Officer makes the final decision.
"""
import re
import math
import uuid
from typing import Optional
from datetime import datetime, timezone

from app import models
from app.adapters import get_adapter
from app.services.retriever import get_retriever
from app.services.extractor import get_extractor


# ── Value Parsers ─────────────────────────────────────────────────────

def parse_turnover_crore(raw: str) -> Optional[float]:
    """Return crore units; ambiguous, negative and non-finite input is unavailable."""
    if not raw:
        return None
    cleaned = raw.strip().replace(",", "")
    match = re.fullmatch(r"(?:₹|INR|Rs\.?)?\s*(-?\d+(?:\.\d+)?)\s*(crores?|cr|lakhs?|lacs?)?", cleaned, re.I)
    if not match:
        return None
    value = float(match.group(1))
    unit = (match.group(2) or "").lower()
    if not math.isfinite(value) or value < 0:
        return None
    if unit.startswith(("lakh", "lac")):
        value /= 100
    elif not unit and re.match(r"^(?:₹|INR|Rs\.?)", raw.strip(), re.I):
        value /= 10000000
    elif not unit and "," in raw:
        return None
    return value


def parse_percentage(raw: str) -> Optional[float]:
    if not raw:
        return None
    match = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*%\s*", raw)
    if not match:
        return None
    value = float(match.group(1))
    return value if math.isfinite(value) and 0 <= value <= 100 else None


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
        if gst_res.get("status") in {"SUSPENDED", "NOT_FOUND"} and gst_res.get("response_code") in {200, 404}:
            gst_result = "FAIL"
        elif gst_res.get("status") != "ACTIVE" or gst_res.get("response_code") != 200:
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
        elif cppp_res.get("debarred") is True and cppp_res.get("response_code") == 200:
            cppp_result = "FAIL"
        elif cppp_res.get("status") == "UNAVAILABLE" or cppp_res.get("response_code") != 200:
            cppp_result = "REVIEW"
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
        if ext_oem["confidence"] < 0.7:
            oem_result = "REVIEW"
        elif "mismatch" in oem_val.lower() or "missing" in oem_val.lower():
            oem_result = "FAIL"
        else:
            recipient = re.search(r"authorize\s+(.+?)\s+to\s+(?:supply|support)", ext_oem.get("source_text", ""), re.I)
            def normalize(name):
                # Take only the first significant word (e.g. "TechNova" or "Apex") for basic matching
                cleaned = re.sub(r"[^a-z0-9\s]", "", name.casefold()).strip()
                return cleaned.split()[0] if cleaned else ""

            if not recipient:
                oem_result = "REVIEW"
                oem_val = "Authorization recipient could not be verified"
            elif normalize(recipient.group(1)) != normalize(bid.bidder_name):
                oem_result = "FAIL"
                oem_val = f"Authorization recipient mismatch: {recipient.group(1)} vs {bid.bidder_name}"
            else:
                oem_val = f"Authorization recipient: {recipient.group(1)}"

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

        # Replace current package results atomically; audit retains past outcomes.
        self.db.query(models.RuleResult).filter(models.RuleResult.bid_id == bid.id).delete(synchronize_session=False)
        for r in rules_run:
            self.db.add(r)

            self.db.add(models.AuditEvent(
                time=datetime.now(timezone.utc).isoformat(),
                actor="System (Rule Engine)",
                action=f"Rule Evaluated: {r.rule_name}",
                document=doc.filename,
                hash=doc.hash_sha3_512,
                rule=r.rule_name,
                result=r.result,
                source=f"bid:{bid.id}"
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
        bid.reviewer_decision = bid.reviewer_note = bid.reviewed_at = None

        self.db.commit()
        return bid


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
