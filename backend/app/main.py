import hashlib
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from redis import Redis
from rq import Queue

from app import models, schemas
from app.database import engine, Base, get_db
from app.storage import minio_client
from app.config import settings

Base.metadata.create_all(bind=engine)

redis_conn = Redis.from_url(settings.REDIS_URL)
task_queue = Queue(connection=redis_conn)

app = FastAPI(title="ProcureGuard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health ────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"status": "ok", "message": "ProcureGuard API is running."}

# ── Upload ────────────────────────────────────────────────────────────

@app.post("/upload/{bid_id}", response_model=schemas.DocumentResponse)
def upload_document(bid_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    contents = file.file.read()
    size_bytes = len(contents)
    mime_type = file.content_type or "application/pdf"

    # Real SHA-3-512 from actual bytes
    hash_sha3_512 = hashlib.sha3_512(contents).hexdigest()

    # Store in MinIO
    file.file.seek(0)
    object_name = f"{bid_id}/{hash_sha3_512}_{file.filename}"
    minio_path = minio_client.upload_fileobj(file.file, object_name)

    # Create Document record with full metadata
    doc = models.Document(
        bid_id=bid_id,
        filename=file.filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        hash_sha3_512=hash_sha3_512,
        minio_path=minio_path,
        status="uploaded",
        processing_stage="UPLOAD"
    )
    db.add(doc)

    # Audit event
    db.add(models.AuditEvent(
        time=datetime.now(timezone.utc).isoformat(),
        actor="System (Ingestion)",
        action="Document Uploaded & SHA-3-512 Sealed",
        document=file.filename,
        hash=hash_sha3_512,
        result="SUCCESS",
        source="Upload API"
    ))
    db.commit()
    db.refresh(doc)

    # Enqueue background processing job
    task_queue.enqueue('app.tasks.process_document_pipeline', doc.id)

    return doc

# ── Tenders ───────────────────────────────────────────────────────────

@app.post("/tenders", response_model=schemas.TenderResponse)
def create_tender(tender_data: schemas.TenderCreate, db: Session = Depends(get_db)):
    import datetime
    import uuid
    tender = models.Tender(
        id=f"tnd-{uuid.uuid4().hex[:8]}",
        title=tender_data.title,
        department=tender_data.department,
        published=datetime.datetime.now().strftime("%Y-%m-%d"),
        deadline=tender_data.deadline,
        budget=tender_data.budget,
        status="active"
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)
    return tender

@app.get("/tenders", response_model=List[schemas.TenderResponse])
def get_tenders(db: Session = Depends(get_db)):
    tenders = db.query(models.Tender).all()
    return tenders

@app.get("/tenders/{tender_id}", response_model=schemas.TenderResponse)
def get_tender(tender_id: str, db: Session = Depends(get_db)):
    tender = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return tender

# ── Bids ──────────────────────────────────────────────────────────────

@app.get("/bids", response_model=List[schemas.BidResponse])
def get_bids(db: Session = Depends(get_db)):
    bids = db.query(models.Bid).all()
    return bids

@app.get("/bids/{bid_id}", response_model=schemas.BidResponse)
def get_bid(bid_id: str, db: Session = Depends(get_db)):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    return bid

@app.get("/bids/{bid_id}/status")
def get_bid_status(bid_id: str, db: Session = Depends(get_db)):
    """Polling endpoint for frontend to check processing progress."""
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    # Get latest document processing state
    docs = db.query(models.Document).filter(models.Document.bid_id == bid_id).all()
    doc_statuses = []
    for d in docs:
        doc_statuses.append({
            "document_id": d.id,
            "filename": d.filename,
            "status": d.status,
            "processing_stage": d.processing_stage,
            "page_count": d.page_count
        })

    return {
        "bid_id": bid.id,
        "bid_status": bid.status,
        "bid_risk": bid.risk,
        "bid_score": bid.score,
        "documents": doc_statuses,
        "rules_count": len(bid.rules),
        "reviewer_decision": bid.reviewer_decision
    }

# ── Verify (trigger engine on existing documents) ────────────────────

@app.post("/verify/{bid_id}")
def verify_bid(bid_id: str, db: Session = Depends(get_db)):
    from app.engine import DeterministicEngine

    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    # Find the latest document for this bid
    doc = db.query(models.Document).filter(
        models.Document.bid_id == bid_id
    ).order_by(models.Document.uploaded_at.desc()).first()

    engine = DeterministicEngine(db)
    if doc:
        updated_bid = engine.evaluate_document_evidence(doc.id)
    else:
        # No documents uploaded yet — run with no evidence
        updated_bid = engine.process_bid(bid_id)

    if not updated_bid:
        raise HTTPException(status_code=500, detail="Engine returned no result")

    return {"status": "verification_completed", "bid_status": updated_bid.status, "bid_score": updated_bid.score}

# ── Officer Decision ──────────────────────────────────────────────────

@app.post("/bids/{bid_id}/decision")
def record_decision(bid_id: str, req: schemas.DecisionRequest, db: Session = Depends(get_db)):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    bid.reviewer_decision = req.decision
    bid.reviewer_note = req.note
    bid.reviewed_at = datetime.now(timezone.utc).isoformat()

    db.add(models.AuditEvent(
        time=datetime.now(timezone.utc).isoformat(),
        actor="Procurement Officer",
        action=f"Decision Recorded: {req.decision}",
        document=None,
        rule=None,
        result=req.decision,
        source="Officer Workspace"
    ))
    db.commit()
    return {"status": "decision_recorded", "decision": req.decision}

# ── Document Pages ────────────────────────────────────────────────────

@app.get("/documents/{doc_id}/pages", response_model=List[schemas.PageImageResponse])
def get_document_pages(doc_id: str, db: Session = Depends(get_db)):
    pages = db.query(models.PageImage).filter(
        models.PageImage.document_id == doc_id
    ).order_by(models.PageImage.page_number).all()
    return pages

# ── Audit ─────────────────────────────────────────────────────────────

@app.get("/audit", response_model=List[schemas.AuditEventResponse])
def get_audit_trail(db: Session = Depends(get_db)):
    events = db.query(models.AuditEvent).order_by(models.AuditEvent.time.desc()).limit(50).all()
    return events
