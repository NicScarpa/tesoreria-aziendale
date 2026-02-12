from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.notification_preference import (
    NotificationPreferenceResponse,
    UpdateNotificationPreferencesRequest,
)
from app.services import notification_service

router = APIRouter(prefix="/notification-preferences", tags=["notifications"])


@router.get("", response_model=list[NotificationPreferenceResponse])
def get_preferences(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    prefs = notification_service.get_preferences(db, current_user.id, company.id)
    return [NotificationPreferenceResponse.model_validate(p) for p in prefs]


@router.patch("", response_model=list[NotificationPreferenceResponse])
def update_preferences(
    body: UpdateNotificationPreferencesRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    prefs_data = [p.model_dump() for p in body.preferences]
    prefs = notification_service.update_preferences(db, current_user.id, company.id, prefs_data)
    return [NotificationPreferenceResponse.model_validate(p) for p in prefs]
