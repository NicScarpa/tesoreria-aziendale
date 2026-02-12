import uuid

from sqlalchemy.orm import Session

from app.models.notification_preference import NotificationPreference
from app.models.enums import NotificationType


def get_preferences(db: Session, user_id: uuid.UUID, company_id: uuid.UUID) -> list[NotificationPreference]:
    existing = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.company_id == company_id,
        )
        .all()
    )

    # Build a map of existing prefs
    existing_map = {p.notification_type: p for p in existing}

    # Return all types, using defaults where no pref exists
    result = []
    for nt in NotificationType:
        if nt in existing_map:
            result.append(existing_map[nt])
        else:
            # Return a default object (not persisted)
            result.append(NotificationPreference(
                user_id=user_id,
                company_id=company_id,
                notification_type=nt,
                in_app=True,
                email=False,
            ))
    return result


def update_preferences(
    db: Session,
    user_id: uuid.UUID,
    company_id: uuid.UUID,
    prefs: list[dict],
) -> list[NotificationPreference]:
    for pref_data in prefs:
        nt = pref_data["notification_type"]
        existing = (
            db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.company_id == company_id,
                NotificationPreference.notification_type == nt,
            )
            .first()
        )
        if existing:
            existing.in_app = pref_data.get("in_app", existing.in_app)
            existing.email = pref_data.get("email", existing.email)
        else:
            new_pref = NotificationPreference(
                user_id=user_id,
                company_id=company_id,
                notification_type=nt,
                in_app=pref_data.get("in_app", True),
                email=pref_data.get("email", False),
            )
            db.add(new_pref)
    db.commit()
    return get_preferences(db, user_id, company_id)
