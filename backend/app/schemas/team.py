import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole, UserCompanyStatus


class TeamMemberUser(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str

    model_config = {"from_attributes": True}


class TeamMemberResponse(BaseModel):
    id: uuid.UUID
    user: TeamMemberUser
    role: UserRole
    status: UserCompanyStatus
    invited_at: datetime | None = None
    joined_at: datetime | None = None
    invited_by_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.VIEWER


class UpdateMemberRequest(BaseModel):
    role: UserRole | None = None
    status: UserCompanyStatus | None = None


class TransferOwnershipRequest(BaseModel):
    target_user_id: uuid.UUID
    password: str
