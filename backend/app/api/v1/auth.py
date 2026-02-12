from fastapi import APIRouter, HTTPException, status

from app.core.deps import DB, CurrentUser
from app.models.enums import AuditAction
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.services import audit_service, auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DB):
    user = auth_service.authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenziali non valide")
    tokens = auth_service.create_tokens(db, user)
    audit_service.log_action(db, AuditAction.LOGIN, user_id=user.id)
    return tokens


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: DB):
    existing = user_service.get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email già registrata")
    user, _company = auth_service.register_user(
        db, body.email, body.password, body.first_name, body.last_name, body.company_name
    )
    tokens = auth_service.create_tokens(db, user)
    audit_service.log_action(db, AuditAction.USER_REGISTER, user_id=user.id)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: DB):
    result = auth_service.refresh_access_token(db, body.refresh_token)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token non valido o scaduto")
    return result


@router.post("/logout", response_model=MessageResponse)
def logout(body: LogoutRequest, db: DB, current_user: CurrentUser):
    auth_service.revoke_refresh_token(db, body.refresh_token)
    audit_service.log_action(db, AuditAction.LOGOUT, user_id=current_user.id)
    return {"message": "Logout effettuato"}


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(body: ForgotPasswordRequest, db: DB):
    token = auth_service.request_password_reset(db, body.email)
    if token:
        # In produzione qui si invierebbe l'email. Per ora stampa in console.
        print(f"[PASSWORD RESET] Token per {body.email}: {token}")
    # Rispondi sempre 200 per non rivelare se l'email esiste
    return {"message": "Se l'email esiste, riceverai un link per il reset della password"}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: DB):
    success = auth_service.reset_password(db, body.token, body.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token non valido o scaduto")
    return {"message": "Password reimpostata con successo"}


@router.post("/change-password", response_model=MessageResponse)
def change_password(body: ChangePasswordRequest, db: DB, current_user: CurrentUser):
    success = user_service.change_password(db, current_user, body.current_password, body.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password attuale non corretta")
    audit_service.log_action(db, AuditAction.PASSWORD_CHANGE, user_id=current_user.id)
    return {"message": "Password cambiata con successo"}
