import hashlib
import logging
from datetime import datetime, timezone
from app import models
from app.database import SessionLocal
from app.storage import minio_client
from app.services.renderer import PDFRenderer

logger = logging.getLogger(__name__)

def _update_stage(db, doc, stage, action):
    doc.processing_stage = stage
    db.add(models.AuditEvent(time=datetime.now(timezone.utc).isoformat(),
        actor="System (Pipeline)", action=action, document=doc.filename,
        hash=doc.hash_sha3_512, result="IN_PROGRESS", source=f"bid:{doc.bid_id}"))
    db.commit()

def process_document_pipeline(document_id: str):
    db = SessionLocal()
    try:
        doc = db.get(models.Document, document_id)
        if not doc or doc.status == "completed":
            return
        doc.status = "processing"
        _update_stage(db, doc, "HASH", "Checking stored document hash")
        pdf_bytes = minio_client.download_file_bytes(doc.minio_path)
        if hashlib.sha3_512(pdf_bytes).hexdigest() != doc.hash_sha3_512:
            raise ValueError("Stored document does not match upload hash")
        _update_stage(db, doc, "RENDER", "Rendering PDF pages")
        records = PDFRenderer().render_document_with_metadata(document_id, pdf_bytes)
        if not records:
            raise ValueError("PDF has no renderable pages")
        db.query(models.PageImage).filter(models.PageImage.document_id == document_id).delete(synchronize_session=False)
        for record in records:
            db.add(models.PageImage(document_id=document_id, **record))
        doc.page_count = len(records)
        _update_stage(db, doc, "EVALUATE", "Retrieving text, extracting fields and evaluating rules")
        from app.engine import DeterministicEngine
        if not DeterministicEngine(db).evaluate_document_evidence(document_id):
            raise ValueError("No evaluation produced")
        doc.status = "completed"
        _update_stage(db, doc, "HUMAN_REVIEW", "Evaluation complete; awaiting officer decision")
    except Exception:
        logger.exception("Document processing failed: %s", document_id)
        db.rollback()
        doc = db.get(models.Document, document_id)
        if doc:
            doc.status, doc.processing_stage = "error", "FAILED"
            if doc.bid.status != "FAIL":
                doc.bid.status, doc.bid.risk = "REVIEW", "MEDIUM"
            doc.bid.summary = "Package processing failed. Prior rules may be historical; no final decision is available."
            db.add(models.AuditEvent(time=datetime.now(timezone.utc).isoformat(),
                actor="System (Pipeline Error)", action="Processing failed; check worker logs and re-upload",
                document=doc.filename, hash=doc.hash_sha3_512, result="UNAVAILABLE", source=f"bid:{doc.bid_id}"))
            db.commit()
        raise
    finally:
        db.close()

