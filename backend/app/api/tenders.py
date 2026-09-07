from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Tender, TenderVersion, Requirement, TenderStatus, generate_uuid, utc_now
from app.schemas import (
    TenderOut, TenderDetailOut, TenderCreate, TenderUpdate, 
    RequirementCreate, RequirementOut, TenderVersionOut
)
from app.api.deps import get_current_user
from app.audit.service import audit_service

router = APIRouter(prefix="/tenders", tags=["Tenders"])

@router.get("", response_model=List[TenderOut])
def list_tenders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TenderStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Tender)
    if status:
        query = query.filter(Tender.status == status)
    tenders = query.order_by(Tender.created_at.desc()).offset(skip).limit(limit).all()
    
    # Populate counts
    result = []
    for t in tenders:
        req_count = db.query(Requirement).filter(Requirement.tender_id == t.id).count()
        from app.models import Bid
        bid_count = db.query(Bid).filter(Bid.tender_id == t.id).count()
        t_dict = TenderOut.model_validate(t)
        t_dict.requirements_count = req_count
        t_dict.bids_count = bid_count
        result.append(t_dict)
    return result

@router.post("", response_model=TenderDetailOut, status_code=status.HTTP_201_CREATED)
def create_tender(
    tender_in: TenderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    existing = db.query(Tender).filter(Tender.tender_number == tender_in.tender_number).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Tender with number '{tender_in.tender_number}' already exists."
        )

    tender = Tender(
        id=generate_uuid(),
        tender_number=tender_in.tender_number,
        title=tender_in.title,
        description=tender_in.description,
        procuring_organization=tender_in.procuring_organization,
        estimated_value=tender_in.estimated_value,
        currency=tender_in.currency,
        status=TenderStatus.ACTIVE
    )
    db.add(tender)
    db.commit()

    # Create initial version
    version = TenderVersion(
        id=generate_uuid(),
        tender_id=tender.id,
        version_number=1,
        change_summary="Initial publication on GeM platform"
    )
    db.add(version)
    db.commit()

    # Create requirements if provided
    for idx, req_in in enumerate(tender_in.requirements or []):
        req = Requirement(
            id=generate_uuid(),
            tender_id=tender.id,
            tender_version_id=version.id,
            name=req_in.name,
            description=req_in.description,
            rule_type=req_in.rule_type,
            operator=req_in.operator,
            expected_value=req_in.expected_value,
            unit=req_in.unit,
            evidence_type=req_in.evidence_type,
            severity=req_in.severity,
            mandatory=req_in.mandatory,
            enabled=req_in.enabled,
            weight=req_in.weight,
            exception_logic=req_in.exception_logic,
            display_order=req_in.display_order or idx
        )
        db.add(req)
    db.commit()
    db.refresh(tender)

    audit_service.record_event(
        db=db,
        action="TENDER_CREATED",
        entity_type="Tender",
        entity_id=tender.id,
        user_id=current_user.id if current_user else None,
        metadata_json={"tender_number": tender.tender_number, "title": tender.title}
    )

    return tender

@router.get("/{id}", response_model=TenderDetailOut)
def get_tender(id: str, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return tender

@router.post("/{id}/versions", response_model=TenderVersionOut)
def create_tender_version(
    id: str,
    change_summary: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    tender = db.query(Tender).filter(Tender.id == id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    last_version = db.query(TenderVersion).filter(TenderVersion.tender_id == id).order_by(TenderVersion.version_number.desc()).first()
    next_ver_num = (last_version.version_number + 1) if last_version else 1

    version = TenderVersion(
        id=generate_uuid(),
        tender_id=tender.id,
        version_number=next_ver_num,
        change_summary=change_summary
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    audit_service.record_event(
        db=db,
        action="TENDER_VERSION_CREATED",
        entity_type="TenderVersion",
        entity_id=version.id,
        user_id=current_user.id if current_user else None,
        metadata_json={"version_number": next_ver_num, "change_summary": change_summary}
    )

    return version

@router.get("/{id}/requirements", response_model=List[RequirementOut])
def get_tender_requirements(id: str, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    reqs = db.query(Requirement).filter(Requirement.tender_id == id).order_by(Requirement.display_order).all()
    return reqs

@router.post("/{id}/requirements", response_model=RequirementOut, status_code=status.HTTP_201_CREATED)
def create_tender_requirement(
    id: str,
    req_in: RequirementCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    tender = db.query(Tender).filter(Tender.id == id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    req = Requirement(
        id=generate_uuid(),
        tender_id=tender.id,
        name=req_in.name,
        description=req_in.description,
        rule_type=req_in.rule_type,
        operator=req_in.operator,
        expected_value=req_in.expected_value,
        unit=req_in.unit,
        evidence_type=req_in.evidence_type,
        severity=req_in.severity,
        mandatory=req_in.mandatory,
        enabled=req_in.enabled,
        weight=req_in.weight,
        exception_logic=req_in.exception_logic,
        display_order=req_in.display_order
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    audit_service.record_event(
        db=db,
        action="REQUIREMENT_CREATED",
        entity_type="Requirement",
        entity_id=req.id,
        user_id=current_user.id if current_user else None,
        metadata_json={"name": req.name, "rule_type": req.rule_type.value, "operator": req.operator.value}
    )

    return req
