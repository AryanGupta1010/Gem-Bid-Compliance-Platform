from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import AuditEvent
from app.schemas import AuditEventOut
from app.audit.service import audit_service

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("", response_model=List[AuditEventOut])
def get_audit_trail(
    limit: int = Query(100, ge=1, le=500),
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AuditEvent)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)

    events = query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    for ev in events:
        if ev.user:
            ev.user_name = ev.user.full_name
        else:
            ev.user_name = "System Automated Engine"
    return events
