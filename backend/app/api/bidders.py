from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Bidder, generate_uuid
from app.schemas import BidderOut, BidderCreate, BidderUpdate
from app.api.deps import get_current_user
from app.audit.service import audit_service

router = APIRouter(prefix="/bidders", tags=["Bidders"])

@router.get("", response_model=List[BidderOut])
def list_bidders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Bidder).order_by(Bidder.created_at.desc()).offset(skip).limit(limit).all()

@router.post("", response_model=BidderOut, status_code=status.HTTP_201_CREATED)
def create_bidder(
    bidder_in: BidderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    existing = db.query(Bidder).filter(Bidder.registration_number == bidder_in.registration_number).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Bidder with registration number '{bidder_in.registration_number}' already exists."
        )

    bidder = Bidder(
        id=generate_uuid(),
        name=bidder_in.name,
        registration_number=bidder_in.registration_number,
        gstin=bidder_in.gstin,
        pan=bidder_in.pan,
        udyam_number=bidder_in.udyam_number,
        contact_email=bidder_in.contact_email,
        contact_phone=bidder_in.contact_phone,
        is_msme=bidder_in.is_msme
    )
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    audit_service.record_event(
        db=db,
        action="BIDDER_CREATED",
        entity_type="Bidder",
        entity_id=bidder.id,
        user_id=current_user.id if current_user else None,
        metadata_json={"name": bidder.name, "reg_number": bidder.registration_number}
    )

    return bidder

@router.get("/{id}", response_model=BidderOut)
def get_bidder(id: str, db: Session = Depends(get_db)):
    bidder = db.query(Bidder).filter(Bidder.id == id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")
    return bidder
