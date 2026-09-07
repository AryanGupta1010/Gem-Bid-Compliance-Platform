from typing import List, Optional
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import (
    Bid, Bidder, Tender, Document, DocumentVersion, RuleResult, Evidence, 
    ComplianceAssessment, BidStatus, generate_uuid, utc_now
)
from app.schemas import (
    BidOut, BidDetailOut, BidCreate, DocumentOut, RuleResultOut, 
    ComplianceAssessmentOut, EvidenceOut, AuditEventOut
)
from app.api.deps import get_current_user
from app.storage import storage_service
from app.utils.hashing import compute_sha3_512
from app.utils.pdf_handler import extract_pdf_info
from app.audit.service import audit_service
from app.workers.pipeline import run_bid_evaluation_pipeline

router = APIRouter(prefix="/bids", tags=["Bids & Evaluation"])

@router.get("", response_model=List[BidOut])
def list_bids(
    tender_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Bid)
    if tender_id:
        query = query.filter(Bid.tender_id == tender_id)
    return query.order_by(Bid.submitted_at.desc()).offset(skip).limit(limit).all()

@router.post("", response_model=BidOut, status_code=status.HTTP_201_CREATED)
def create_bid(
    bid_in: BidCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    tender = db.query(Tender).filter(Tender.id == bid_in.tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    bidder = db.query(Bidder).filter(Bidder.id == bid_in.bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    existing = db.query(Bid).filter(Bid.bid_number == bid_in.bid_number).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Bid number '{bid_in.bid_number}' already exists.")

    bid = Bid(
        id=generate_uuid(),
        tender_id=bid_in.tender_id,
        bidder_id=bid_in.bidder_id,
        bid_number=bid_in.bid_number,
        bid_amount=bid_in.bid_amount,
        status=BidStatus.SUBMITTED
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)

    audit_service.record_event(
        db=db,
        action="BID_SUBMITTED",
        entity_type="Bid",
        entity_id=bid.id,
        user_id=current_user.id if current_user else None,
        metadata_json={"bid_number": bid.bid_number, "bidder": bidder.name, "tender": tender.tender_number}
    )

    return bid

@router.get("/{id}", response_model=BidDetailOut)
def get_bid(id: str, db: Session = Depends(get_db)):
    bid = db.query(Bid).filter(Bid.id == id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    return bid

@router.post("/{id}/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_bid_document(
    id: str,
    file: UploadFile = File(...),
    document_type: str = Form("OTHER"),
    metadata_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    bid = db.query(Bid).filter(Bid.id == id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    file_bytes = await file.read()
    file_size = len(file_bytes)
    
    if file_size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="File exceeds maximum size of 50MB")

    # Cryptographic SHA-3-512 Hash Generation
    doc_hash = compute_sha3_512(file_bytes)

    # PyMuPDF PDF Metadata Extraction
    pdf_info = extract_pdf_info(file_bytes)

    # Parse metadata if passed
    import json
    parsed_meta = {}
    if metadata_json:
        try:
            parsed_meta = json.loads(metadata_json)
        except Exception:
            pass

    # Save to storage
    ext = os.path.splitext(file.filename or "doc.pdf")[1]
    storage_path = f"bids/{bid.id}/{doc_hash[:16]}_{file.filename}"
    storage_service.save_file(file_bytes, storage_path)

    doc = Document(
        id=generate_uuid(),
        bid_id=bid.id,
        document_type=document_type,
        filename=file.filename or "document.pdf",
        file_path=storage_path,
        mime_type=file.content_type or "application/pdf",
        file_size=file_size,
        document_hash=doc_hash,
        page_count=pdf_info.get("page_count", 1),
        metadata_json=parsed_meta,
        uploaded_by_id=current_user.id if current_user else None
    )
    db.add(doc)
    db.commit()

    # Initial Document Version
    doc_ver = DocumentVersion(
        id=generate_uuid(),
        document_id=doc.id,
        version_number=1,
        document_hash=doc_hash,
        file_path=storage_path
    )
    db.add(doc_ver)
    db.commit()
    db.refresh(doc)

    audit_service.record_event(
        db=db,
        action="DOCUMENT_UPLOADED_AND_HASHED",
        entity_type="Document",
        entity_id=doc.id,
        user_id=current_user.id if current_user else None,
        metadata_json={
            "filename": doc.filename,
            "document_hash": doc.document_hash,
            "file_size": file_size,
            "page_count": doc.page_count,
            "document_type": document_type
        }
    )

    return doc

@router.post("/{id}/verify")
def trigger_bid_verification(
    id: str,
    background_tasks: BackgroundTasks,
    async_mode: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    bid = db.query(Bid).filter(Bid.id == id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    user_id = current_user.id if current_user else None

    if async_mode:
        job_id = generate_uuid()
        # Queue task
        background_tasks.add_task(run_bid_evaluation_pipeline, db, id, user_id, job_id)
        return {
            "job_id": job_id,
            "status": "QUEUED",
            "message": "Evaluation workflow initiated asynchronously."
        }
    else:
        # Synchronous execution
        result = run_bid_evaluation_pipeline(db, id, user_id)
        return result

@router.get("/{id}/assessment", response_model=ComplianceAssessmentOut)
def get_bid_assessment(id: str, db: Session = Depends(get_db)):
    assessment = db.query(ComplianceAssessment).filter(ComplianceAssessment.bid_id == id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found for this bid. Please trigger verification first.")
    return assessment

@router.get("/{id}/rules", response_model=List[RuleResultOut])
def get_bid_rule_results(id: str, db: Session = Depends(get_db)):
    results = db.query(RuleResult).filter(RuleResult.bid_id == id).all()
    # Populate requirement details
    for r in results:
        if r.requirement:
            r.requirement_name = r.requirement.name
            r.rule_type = r.requirement.rule_type
            r.operator = r.requirement.operator
            r.unit = r.requirement.unit
    return results

@router.get("/{id}/evidence", response_model=List[EvidenceOut])
def get_bid_evidences(id: str, db: Session = Depends(get_db)):
    rule_ids = [r.id for r in db.query(RuleResult.id).filter(RuleResult.bid_id == id).all()]
    evidences = db.query(Evidence).filter(Evidence.rule_result_id.in_(rule_ids)).all()
    return evidences

@router.get("/{id}/audit", response_model=List[AuditEventOut])
def get_bid_audit_trail(id: str, db: Session = Depends(get_db)):
    return audit_service.get_events_for_entity(db, "Bid", id)
