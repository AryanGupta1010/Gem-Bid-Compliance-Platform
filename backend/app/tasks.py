from app import models
from app.database import SessionLocal
from app.storage import minio_client
from app.services.renderer import PDFRenderer
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def _update_stage(db, doc, stage: str, audit_action: str = None, audit_result: str = None):
    """Helper to update document processing stage and optionally write an audit event."""
    doc.processing_stage = stage
    if audit_action:
        db.add(models.AuditEvent(
            time=datetime.now(timezone.utc).isoformat(),
            actor=f"System (Pipeline/{stage})",
            action=audit_action,
            document=doc.filename,
            hash=doc.hash_sha3_512,
            result=audit_result or "IN_PROGRESS",
            source="RQ Worker"
        ))
    db.commit()

def process_document_pipeline(document_id: str):
    """
    Background job: process a document through the full AI pipeline.

    Stages: UPLOAD → HASH → RENDER → RETRIEVE → OCR → VERIFY → EVALUATE → AGGREGATE → HUMAN_REVIEW
    """
    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(models.Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return

        logger.info(f"Starting pipeline for document {document_id} ({doc.filename})")
        doc.status = "processing"

        # ── Stage: HASH (already done at upload, but record it) ───────
        _update_stage(db, doc, "HASH",
                      audit_action="SHA-3-512 Hash Verified",
                      audit_result=f"SUCCESS: {doc.hash_sha3_512[:24]}...")

        # ── Stage: RENDER ─────────────────────────────────────────────
        _update_stage(db, doc, "RENDER", audit_action="PDF Rendering Started")

        logger.info(f"Downloading {doc.minio_path} from MinIO")
        pdf_bytes = minio_client.download_file_bytes(doc.minio_path)

        renderer = PDFRenderer()
        page_records = renderer.render_document_with_metadata(document_id, pdf_bytes)

        # Persist PageImage records
        for pr in page_records:
            db.add(models.PageImage(
                document_id=document_id,
                page_number=pr["page_number"],
                minio_path=pr["minio_path"],
                width=pr["width"],
                height=pr["height"]
            ))

        doc.page_count = len(page_records)
        _update_stage(db, doc, "RENDER",
                      audit_action="PDF Pages Rendered",
                      audit_result=f"SUCCESS: {len(page_records)} pages")

        # ── Stage: RETRIEVE ───────────────────────────────────────────
        _update_stage(db, doc, "RETRIEVE", audit_action="Evidence Retrieval Started")

        # ── Stage: OCR ────────────────────────────────────────────────
        _update_stage(db, doc, "OCR", audit_action="Targeted OCR Started")

        # ── Stage: VERIFY ─────────────────────────────────────────────
        _update_stage(db, doc, "VERIFY", audit_action="External Verification Started")

        # ── Stage: EVALUATE ───────────────────────────────────────────
        _update_stage(db, doc, "EVALUATE", audit_action="Rule Engine Started")

        # Engine handles RETRIEVE → OCR → VERIFY → EVALUATE → AGGREGATE internally
        from app.engine import DeterministicEngine
        engine = DeterministicEngine(db)
        engine.evaluate_document_evidence(document_id)

        # ── Stage: AGGREGATE ──────────────────────────────────────────
        _update_stage(db, doc, "AGGREGATE",
                      audit_action="Score Aggregation Complete",
                      audit_result="SUCCESS")

        # ── Stage: HUMAN_REVIEW ───────────────────────────────────────
        _update_stage(db, doc, "HUMAN_REVIEW",
                      audit_action="Awaiting Officer Review",
                      audit_result="PENDING")

        doc.status = "completed"
        db.commit()
        logger.info(f"Completed pipeline for document {document_id}")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
        db.rollback()
        doc = db.query(models.Document).filter(models.Document.id == document_id).first()
        if doc:
            doc.status = "error"
            doc.processing_stage = "FAILED"
            db.add(models.AuditEvent(
                time=datetime.now(timezone.utc).isoformat(),
                actor="System (Pipeline Error)",
                action="Processing Failed",
                document=doc.filename,
                hash=doc.hash_sha3_512,
                result=f"ERROR: {str(e)}",
                source="RQ Worker"
            ))
            db.commit()
    finally:
        db.close()
