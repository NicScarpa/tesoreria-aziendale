from pydantic import BaseModel, EmailStr, field_validator
import re


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    company_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La password deve essere di almeno 8 caratteri")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La password deve contenere almeno una lettera maiuscola")
        if not re.search(r"[a-z]", v):
            raise ValueError("La password deve contenere almeno una lettera minuscola")
        if not re.search(r"[0-9]", v):
            raise ValueError("La password deve contenere almeno un numero")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La password deve essere di almeno 8 caratteri")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La password deve contenere almeno una lettera maiuscola")
        if not re.search(r"[a-z]", v):
            raise ValueError("La password deve contenere almeno una lettera minuscola")
        if not re.search(r"[0-9]", v):
            raise ValueError("La password deve contenere almeno un numero")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La password deve essere di almeno 8 caratteri")
        return v
