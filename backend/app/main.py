import hashlib
import io
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List

import pymupdf
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload
from redis import Redis
from rq import Queue

from app import models, schemas
from app.database import engine, Base, get_db
from app.storage import minio_client
from app.config import settings

logger = logging.getLogger(__name__)
redis_conn = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=3, socket_timeout=3)
task_queue = Queue(connection=redis_conn)
BID_LOAD = (selectinload(models.Bid.documents), selectinload(models.Bid.rules))
TENDER_LOAD = (selectinload(models.Tender.bids).selectinload(models.Bid.documents),
               selectinload(models.Tender.bids).selectinload(models.Bid.rules))

@asynccontextmanager
async def lifespan(app):
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError:
        logger.exception("Database initialization failed")
    yield

app = FastAPI(title="ProcureGuard API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

@app.exception_handler(SQLAlchemyError)
async def database_unavailable(request, exc):
    logger.error("Database request failed", exc_info=exc)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable. Retry when the service is restored."})

@app.get("/")
def read_root():
    return {"status": "ok", "message": "ProcureGuard API is running."}

@app.get("/capabilities")
def capabilities():
    return {
        "ai_mode": settings.AI_MODE,
        "retrieval": "UNAVAILABLE: ColPali integration is not implemented" if settings.AI_MODE == "real" else "REAL: PyMuPDF text retrieval; Tesseract fallback when installed",
        "extraction": "REAL: deterministic regex extraction (heuristic confidence, not model probability)",
        "connectors": [{"name": name, "mode": mode} for name, mode in
                       [("GST", "DEMO/OFFLINE fixtures"), ("CPPP", "DEMO/OFFLINE fixtures"),
                        ("Udyam", "MOCK; not evaluated"), ("UDIN", "UNAVAILABLE stub"), ("BIS", "UNAVAILABLE stub")]],
    }

@app.post("/upload/{bid_id}", response_model=schemas.DocumentResponse)
def upload_document(bid_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).with_for_update().first()
    if not bid:
        raise HTTPException(404, "Bid not found")
    if db.query(models.Document).filter(models.Document.bid_id == bid_id,
            models.Document.status.in_(["uploaded", "processing"])).first():
        raise HTTPException(409, "A package is already processing for this bidder.")
    contents = file.file.read(50 * 1024 * 1024 + 1)
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(413, "PDF exceeds the 50 MB limit")
    filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    if not filename.lower().endswith(".pdf") or not contents.startswith(b"%PDF-"):
        raise HTTPException(422, "Select a valid PDF document")
    try:
        with pymupdf.open(stream=contents, filetype="pdf") as pdf:
            if pdf.needs_pass or pdf.page_count == 0 or pdf.page_count > 200 or pdf.is_repaired:
                raise ValueError("Encrypted, damaged, empty or oversized PDF")
            for page in pdf:
                if page.rect.width <= 0 or page.rect.height <= 0 or max(page.rect.width, page.rect.height) > 14400:
                    raise ValueError("Unsupported page dimensions")
                page.get_text()
    except Exception as exc:
        raise HTTPException(422, "PDF is corrupt, encrypted, empty, or exceeds 200 pages. Supply a readable PDF.") from exc
    digest = hashlib.sha3_512(contents).hexdigest()
    try:
        redis_conn.ping()
        path = minio_client.upload_fileobj(io.BytesIO(contents), f"{bid_id}/{uuid.uuid4().hex}.pdf")
    except Exception as exc:
        logger.exception("Upload dependency unavailable")
        raise HTTPException(503, "Storage or queue unavailable. No processing job was accepted; retry later.") from exc
    doc = models.Document(bid_id=bid_id, filename=filename, mime_type="application/pdf",
                          size_bytes=len(contents), hash_sha3_512=digest, minio_path=path,
                          status="uploaded", processing_stage="UPLOAD")
    db.add(doc)
    # Previous rules remain visible as historical results until this package completes.
    if bid.status != "FAIL":
        bid.status, bid.risk = "REVIEW", "MEDIUM"
    bid.reviewer_decision = bid.reviewer_note = bid.reviewed_at = None
    bid.summary = "New package queued. Previous rule results are not an evaluation of this upload."
    db.add(models.AuditEvent(time=datetime.now(timezone.utc).isoformat(), actor="System (Ingestion)",
           action="Document Uploaded & SHA-3-512 Sealed", document=filename, hash=digest,
           result="SUCCESS", source=f"bid:{bid_id}"))
    db.commit()
    db.refresh(doc)
    try:
        task_queue.enqueue("app.tasks.process_document_pipeline", doc.id, job_timeout=900)
    except Exception as exc:
        doc.status, doc.processing_stage = "error", "FAILED"
        db.add(models.AuditEvent(time=datetime.now(timezone.utc).isoformat(), actor="System (Queue)",
               action="Processing queue unavailable", document=filename, hash=digest,
               result="UNAVAILABLE", source=f"bid:{bid_id}"))
        db.commit()
        raise HTTPException(503, "PDF stored, but queue submission failed. Upload again after Redis recovers.") from exc
    return doc

@app.post("/tenders", response_model=schemas.TenderResponse)
def create_tender(tender_data: schemas.TenderCreate, db: Session = Depends(get_db)):
    tender = models.Tender(id=f"tnd-{uuid.uuid4().hex}", **tender_data.model_dump(),
                           published=datetime.now(timezone.utc).date().isoformat(), status="active")
    db.add(tender)
    db.commit()
    db.refresh(tender)
    return tender

@app.get("/tenders", response_model=List[schemas.TenderResponse])
def get_tenders(db: Session = Depends(get_db)):
    return db.query(models.Tender).options(*TENDER_LOAD).order_by(models.Tender.published.desc(), models.Tender.id).all()

@app.get("/tenders/{tender_id:path}", response_model=schemas.TenderResponse)
def get_tender(tender_id: str, db: Session = Depends(get_db)):
    tender = db.query(models.Tender).options(*TENDER_LOAD).filter(models.Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "Tender not found")
    return tender

@app.post("/bids", response_model=schemas.BidResponse)
def create_bid(data: schemas.BidCreate, db: Session = Depends(get_db)):
    if not db.query(models.Tender).filter(models.Tender.id == data.tender_id).first():
        raise HTTPException(404, "Tender not found")
    bid = models.Bid(id=f"bid-{uuid.uuid4().hex}", **data.model_dump(), status="REVIEW", risk="MEDIUM",
                     score=0, failed_rules=0, review_rules=0, summary="No package uploaded. Evaluation unavailable; officer review required.")
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid

@app.get("/bids", response_model=List[schemas.BidResponse])
def get_bids(db: Session = Depends(get_db)):
    return db.query(models.Bid).options(*BID_LOAD).order_by(models.Bid.id).all()

@app.get("/bids/{bid_id}", response_model=schemas.BidResponse)
def get_bid(bid_id: str, db: Session = Depends(get_db)):
    bid = db.query(models.Bid).options(*BID_LOAD).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(404, "Bid not found")
    return bid

@app.get("/bids/{bid_id}/status")
def get_bid_status(bid_id: str, db: Session = Depends(get_db)):
    bid = get_bid(bid_id, db)
    return {"bid_id": bid.id, "bid_status": bid.status, "bid_risk": bid.risk, "bid_score": bid.score,
            "documents": [{"document_id": d.id, "filename": d.filename, "status": d.status,
                           "processing_stage": d.processing_stage, "page_count": d.page_count} for d in bid.documents],
            "rules_count": len(bid.rules), "reviewer_decision": bid.reviewer_decision}

@app.post("/verify/{bid_id}")
def verify_bid(bid_id: str, db: Session = Depends(get_db)):
    from app.engine import DeterministicEngine
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).with_for_update().first()
    if not bid:
        raise HTTPException(404, "Bid not found")
    doc = db.query(models.Document).filter(models.Document.bid_id == bid_id).order_by(models.Document.uploaded_at.desc()).first()
    if not doc or doc.status != "completed":
        raise HTTPException(409, "A successfully processed package is required before verification")
    updated = DeterministicEngine(db).evaluate_document_evidence(doc.id)
    return {"status": "verification_completed", "bid_status": updated.status, "bid_score": updated.score}

@app.post("/bids/{bid_id}/decision")
def record_decision(bid_id: str, req: schemas.DecisionRequest, db: Session = Depends(get_db)):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).with_for_update().first()
    if not bid:
        raise HTTPException(404, "Bid not found")
    doc = db.query(models.Document).filter(models.Document.bid_id == bid_id).order_by(models.Document.uploaded_at.desc()).first()
    if not doc or doc.status != "completed" or not bid.rules:
        raise HTTPException(409, "Complete package processing before recording a final decision")
    bid.reviewer_decision, bid.reviewer_note = req.decision, req.note
    bid.reviewed_at = datetime.now(timezone.utc).isoformat()
    db.add(models.AuditEvent(time=bid.reviewed_at, actor="Procurement Officer",
           action=f"Decision Recorded: {req.decision}; rationale: {req.note}",
           result=req.decision, source=f"bid:{bid_id}", document=doc.filename, hash=doc.hash_sha3_512))
    db.commit()
    return {"status": "decision_recorded", "decision": req.decision}

@app.get("/documents/{doc_id}/pages", response_model=List[schemas.PageImageResponse])
def get_document_pages(doc_id: str, db: Session = Depends(get_db)):
    if not db.get(models.Document, doc_id):
        raise HTTPException(404, "Document not found")
    return db.query(models.PageImage).filter(models.PageImage.document_id == doc_id).order_by(models.PageImage.page_number).all()

@app.get("/documents/{doc_id}/content")
def document_content(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(models.Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    try:
        contents = minio_client.download_file_bytes(doc.minio_path)
    except Exception as exc:
        raise HTTPException(503, "Document storage unavailable") from exc
    return Response(contents, media_type="application/pdf", headers={"Content-Disposition": "inline", "Cache-Control": "no-store"})

@app.get("/audit", response_model=List[schemas.AuditEventResponse])
def get_audit_trail(bid_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.AuditEvent)
    if bid_id:
        if not db.get(models.Bid, bid_id):
            raise HTTPException(404, "Bid not found")
        # Identical uploaded bytes may belong to different bidders. A hash is not an attribution key.
        query = query.filter(models.AuditEvent.source == f"bid:{bid_id}")
    return query.order_by(models.AuditEvent.time.desc(), models.AuditEvent.id).all()
