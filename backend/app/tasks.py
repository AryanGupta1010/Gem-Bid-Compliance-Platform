"""
RQ Background Worker Processing Pipeline.

Stages:
  1. HASH: Validate SHA3-512 integrity
  2. RENDER: Render PDF pages to images via PyMuPDF and store in MinIO
  3. INDEX: Generate and persist ColPali visual embeddings
  4. EVALUATE: Targeted OCR, field extraction, NLI reasoning, rule verification
  5. HUMAN_REVIEW: Evaluation complete; awaiting Procurement Officer decision
"""
import hashlib
import logging
from datetime import datetime, timezone

from app import models
from app.database import SessionLocal
from app.storage import minio_client
from app.services.renderer import PDFRenderer
from app.services.retriever import get_retriever
from app.services.exceptions import AIModelUnavailableError

logger = logging.getLogger(__name__)

def _update_stage(db, doc, stage, action, result="IN_PROGRESS", source=None):
    doc.processing_stage = stage
    db.add(models.AuditEvent(
        time=datetime.now(timezone.utc).isoformat(),
        actor="System (AI Pipeline)",
        action=action,
        document=doc.filename,
        hash=doc.hash_sha3_512,
        result=result,
        source=source or (f"bid:{doc.bid_id}" if getattr(doc, "bid_id", None) else f"tender:{getattr(doc, 'tender_id', '')}")
    ))
    db.commit()

def process_document_pipeline(document_id: str):
    db = SessionLocal()
    try:
        doc = db.get(models.Document, document_id)
        if not doc or doc.status == "completed":
            return
        doc.status = "processing"
        
        # 1. HASH Verification
        _update_stage(db, doc, "HASH", "Verifying SHA3-512 document cryptographic seal")
        pdf_bytes = minio_client.download_file_bytes(doc.minio_path)
        actual_hash = hashlib.sha3_512(pdf_bytes).hexdigest()
        if actual_hash != doc.hash_sha3_512:
            raise ValueError(f"Document tamper detected: hash mismatch {actual_hash} != {doc.hash_sha3_512}")

        # 2. RENDER PDF Pages
        _update_stage(db, doc, "RENDER", "Rendering PDF pages to visual images (PyMuPDF)")
        records = PDFRenderer().render_document_with_metadata(document_id, pdf_bytes)
        if not records:
            raise ValueError("PDF has no renderable pages")
        
        db.query(models.PageImage).filter(models.PageImage.document_id == document_id).delete(synchronize_session=False)
        for record in records:
            db.add(models.PageImage(document_id=document_id, **record))
        doc.page_count = len(records)
        db.commit()

        # 3. INDEX with ColPali
        _update_stage(db, doc, "INDEX", "Generating ColPali late-interaction visual embeddings")
        retriever = get_retriever()
        try:
            retriever.index_document(document_id)
        except AIModelUnavailableError as ai_err:
            logger.error("ColPali indexing failed: %s", ai_err)
            raise

        # 4. EVALUATE Deterministic Rules & Evidence
        _update_stage(db, doc, "EVALUATE", "Targeted OCR (Surya), NLI reasoning and deterministic rule evaluation")
        from app.engine import DeterministicEngine
        engine = DeterministicEngine(db)
        if not engine.evaluate_document_evidence(document_id):
            raise ValueError("Evaluation produced no rule results")

        # 5. HUMAN_REVIEW
        doc.status = "completed"
        _update_stage(db, doc, "HUMAN_REVIEW", "Evaluation complete; awaiting Procurement Officer decision", result="COMPLETED")

    except AIModelUnavailableError as ai_exc:
        logger.exception("AI Model Service Unavailable for document %s: %s", document_id, ai_exc)
        db.rollback()
        doc = db.get(models.Document, document_id)
        if doc:
            doc.status = "error"
            doc.processing_stage = "FAILED"
            if doc.bid and doc.bid.status != "FAIL":
                doc.bid.status = "REVIEW"
                doc.bid.risk = "HIGH"
            doc.bid.summary = f"AI Evaluation Failed: {ai_exc.message}. No mock fallback was applied in production mode."
            db.add(models.AuditEvent(
                time=datetime.now(timezone.utc).isoformat(),
                actor="System (AI Service Failure)",
                action=f"Processing halted: {ai_exc.service_name.upper()} model service unavailable",
                document=doc.filename,
                hash=doc.hash_sha3_512,
                result="AI_SERVICE_UNAVAILABLE",
                source=f"bid:{doc.bid_id}"
            ))
            db.commit()
        raise
    except Exception as exc:
        logger.exception("Document processing failed: %s", document_id)
        db.rollback()
        doc = db.get(models.Document, document_id)
        if doc:
            doc.status = "error"
            doc.processing_stage = "FAILED"
            if doc.bid and doc.bid.status != "FAIL":
                doc.bid.status = "REVIEW"
                doc.bid.risk = "MEDIUM"
            doc.bid.summary = f"Processing error: {str(exc)}"
            db.add(models.AuditEvent(
                time=datetime.now(timezone.utc).isoformat(),
                actor="System (Pipeline Error)",
                action=f"Processing error: {str(exc)}",
                document=doc.filename,
                hash=doc.hash_sha3_512,
                result="FAILED",
                source=f"bid:{doc.bid_id}"
            ))
            db.commit()
        raise
    finally:
        db.close()

def process_tender_pipeline(document_id: str):
    db = SessionLocal()
    try:
        doc = db.get(models.Document, document_id)
        if not doc or doc.status == "completed":
            return
        doc.status = "processing"
        
        # 1. HASH Verification
        _update_stage(db, doc, "HASH", "Verifying SHA3-512 document cryptographic seal", source=f"tender:{doc.tender_id}")
        pdf_bytes = minio_client.download_file_bytes(doc.minio_path)
        actual_hash = hashlib.sha3_512(pdf_bytes).hexdigest()
        if actual_hash != doc.hash_sha3_512:
            raise ValueError(f"Document tamper detected: hash mismatch {actual_hash} != {doc.hash_sha3_512}")

        # 2. Extract Text & RENDER
        import pymupdf
        tender_pages = []
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
            for i, page in enumerate(pdf):
                tender_pages.append({
                    "page_number": i + 1,
                    "text": page.get_text()
                })
        
        _update_stage(db, doc, "RENDER", "Rendering PDF pages to visual images (PyMuPDF)", source=f"tender:{doc.tender_id}")
        records = PDFRenderer().render_document_with_metadata(document_id, pdf_bytes)
        db.query(models.PageImage).filter(models.PageImage.document_id == document_id).delete(synchronize_session=False)
        for record in records:
            db.add(models.PageImage(document_id=document_id, **record))
        doc.page_count = len(records)
        db.commit()

        # 3. Saul Rule Extraction
        _update_stage(db, doc, "EXTRACT_RULES", "Extracting requirements via SaulLM", source=f"tender:{doc.tender_id}")
        from app.services.saul import get_saul_service
        saul_service = get_saul_service()
        extraction_result = saul_service.extract_requirements(doc.tender_id, tender_pages)
        requirements = extraction_result.get("requirements", [])
        details = extraction_result.get("tender_details", {})
        
        # Update Tender Details
        tender = db.get(models.Tender, doc.tender_id)
        if tender:
            if details.get("tender_number"): tender.tender_number = details["tender_number"]
            if details.get("quantity"): tender.quantity = details["quantity"]
            if details.get("delivery_period"): tender.delivery_period = details["delivery_period"]
            if details.get("warranty"): tender.warranty = details["warranty"]
            if details.get("emd"): tender.emd = details["emd"]
        
        db.query(models.TenderRequirement).filter(models.TenderRequirement.tender_id == doc.tender_id).delete(synchronize_session=False)
        for req in requirements:
            req_model = models.TenderRequirement(
                tender_id=doc.tender_id,
                rule_id=req["rule_id"],
                name=req["name"],
                rule_type=req.get("rule_type"),
                field=req.get("field"),
                operator=req.get("operator"),
                expected_value=req.get("expected_value"),
                unit=req.get("unit"),
                period=req.get("period"),
                evidence_type=req.get("evidence_type"),
                mandatory=req.get("mandatory", True),
                severity=req.get("severity", "HIGH"),
                description=req.get("description"),
                source_page=req.get("source_page"),
                source_text=req.get("source_text"),
                status="pending"
            )
            db.add(req_model)
        
        doc.status = "completed"
        _update_stage(db, doc, "HUMAN_REVIEW", "Rule extraction complete; awaiting Procurement Officer approval", result="COMPLETED", source=f"tender:{doc.tender_id}")

    except Exception as exc:
        logger.exception("Tender document processing failed: %s", document_id)
        db.rollback()
        doc = db.get(models.Document, document_id)
        if doc:
            doc.status = "error"
            doc.processing_stage = "FAILED"
            db.add(models.AuditEvent(
                time=datetime.now(timezone.utc).isoformat(),
                actor="System (Pipeline Error)",
                action=f"Processing error: {str(exc)}",
                document=doc.filename,
                hash=doc.hash_sha3_512,
                result="FAILED",
                source=f"tender:{doc.tender_id}"
            ))
            db.commit()
        raise
    finally:
        db.close()
