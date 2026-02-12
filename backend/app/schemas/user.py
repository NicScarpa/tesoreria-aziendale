import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole, UserCompanyStatus


class UserCompanyResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    role: UserRole
    status: UserCompanyStatus

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None
    email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserMeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None
    email_verified: bool
    created_at: datetime
    companies: list[UserCompanyResponse]

    model_config = {"from_attributes": True}


class UpdateUserRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
