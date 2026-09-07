from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import AuditEvent, generate_uuid, utc_now
from app.core.logging import logger

class AuditService:
    @staticmethod
    def record_event(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Creates an immutable audit log record for traceability.
        """
        event = AuditEvent(
            id=generate_uuid(),
            timestamp=utc_now(),
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            request_id=request_id,
            metadata_json=metadata_json or {}
        )
        db.add(event)
        try:
            db.commit()
            db.refresh(event)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record audit event {action}: {e}")
            raise e

        logger.info(
            f"[AUDIT] action={action} entity={entity_type}:{entity_id} user={user_id or 'SYSTEM'}",
            extra={"action": action, "entity_type": entity_type, "entity_id": str(entity_id)}
        )
        return event

    @staticmethod
    def get_events_for_entity(db: Session, entity_type: str, entity_id: str) -> List[AuditEvent]:
        return db.query(AuditEvent).filter(
            AuditEvent.entity_type == entity_type,
            AuditEvent.entity_id == str(entity_id)
        ).order_by(AuditEvent.timestamp.desc()).all()

    @staticmethod
    def get_recent_events(db: Session, limit: int = 50) -> List[AuditEvent]:
        return db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit).all()

audit_service = AuditService()
