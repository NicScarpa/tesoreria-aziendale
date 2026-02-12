import uuid

from sqlalchemy.orm import Session

from app.models import AuditLog
from app.models.enums import AuditAction


def log_action(
    db: Session,
    action: AuditAction,
    user_id: uuid.UUID | None = None,
    company_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        company_id=company_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
    )
    db.add(entry)
    db.commit()
