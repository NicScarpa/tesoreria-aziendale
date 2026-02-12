from pydantic import BaseModel

from app.models.enums import NotificationType


class NotificationPreferenceResponse(BaseModel):
    notification_type: NotificationType
    in_app: bool
    email: bool

    model_config = {"from_attributes": True}


class NotificationPreferenceItem(BaseModel):
    notification_type: NotificationType
    in_app: bool = True
    email: bool = False


class UpdateNotificationPreferencesRequest(BaseModel):
    preferences: list[NotificationPreferenceItem]
