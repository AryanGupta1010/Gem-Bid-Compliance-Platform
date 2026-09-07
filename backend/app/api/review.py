from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Bid, ReviewDecision, User, BidStatus, generate_uuid, utc_now
from app.schemas import ReviewDecisionCreate, ReviewDecisionOut
from app.api.deps import get_current_user
from app.audit.service import audit_service

router = APIRouter(prefix="/bids/{id}/review", tags=["Human Review"])

@router.post("", response_model=ReviewDecisionOut, status_code=status.HTTP_201_CREATED)
def submit_officer_review(
    id: str,
    review_in: ReviewDecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bid = db.query(Bid).filter(Bid.id == id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")

    officer_id = current_user.id if current_user else None
    if not officer_id:
        # Fallback to demo officer
        first_user = db.query(User).first()
        officer_id = first_user.id if first_user else generate_uuid()

    review = ReviewDecision(
        id=generate_uuid(),
        bid_id=bid.id,
        officer_id=officer_id,
        decision=review_in.decision,
        officer_notes=review_in.officer_notes,
        reviewed_at=utc_now()
    )
    db.add(review)

    # Update bid status to REVIEWED
    bid.status = BidStatus.REVIEWED
    db.commit()
    db.refresh(review)

    # Populate officer name
    if current_user:
        review.officer_name = current_user.full_name

    audit_service.record_event(
        db=db,
        action="OFFICER_REVIEW_SUBMITTED",
        entity_type="Bid",
        entity_id=bid.id,
        user_id=officer_id,
        metadata_json={
            "decision": review.decision.value,
            "notes": review.officer_notes,
            "automated_recommendation": bid.compliance_assessment.recommendation.value if bid.compliance_assessment else "N/A"
        }
    )

    return review

@router.get("", response_model=List[ReviewDecisionOut])
def get_bid_reviews(id: str, db: Session = Depends(get_db)):
    bid = db.query(Bid).filter(Bid.id == id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    reviews = db.query(ReviewDecision).filter(ReviewDecision.bid_id == id).order_by(ReviewDecision.reviewed_at.desc()).all()
    for r in reviews:
        if r.officer:
            r.officer_name = r.officer.full_name
    return reviews
