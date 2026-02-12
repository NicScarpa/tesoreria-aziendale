import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.models import (
    Company,
    PasswordResetToken,
    RefreshToken,
    User,
    UserCompany,
    UserCompanyStatus,
    UserRole,
)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_tokens(db: Session, user: User) -> dict:
    access_token = create_access_token(data={"sub": str(user.id)})
    raw_refresh = create_refresh_token()
    refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh)
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
    }


def refresh_access_token(db: Session, raw_refresh: str) -> dict | None:
    token_hash = hash_token(raw_refresh)
    rt = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not rt:
        return None
    user = db.query(User).filter(User.id == rt.user_id, User.deleted_at.is_(None)).first()
    if not user:
        return None
    # Rotate: revoke old, create new
    rt.revoked_at = datetime.now(timezone.utc)
    access_token = create_access_token(data={"sub": str(user.id)})
    new_raw = create_refresh_token()
    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_raw),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_rt)
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": new_raw,
        "token_type": "bearer",
    }


def revoke_refresh_token(db: Session, raw_refresh: str) -> bool:
    token_hash = hash_token(raw_refresh)
    rt = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
        .first()
    )
    if not rt:
        return False
    rt.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def register_user(
    db: Session, email: str, password: str, first_name: str, last_name: str, company_name: str
) -> tuple[User, Company]:
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        email_verified=False,
        is_active=True,
    )
    db.add(user)
    db.flush()

    company = Company(name=company_name, country="IT")
    db.add(company)
    db.flush()

    uc = UserCompany(
        user_id=user.id,
        company_id=company.id,
        role=UserRole.OWNER,
        status=UserCompanyStatus.ACTIVE,
    )
    db.add(uc)
    db.commit()
    db.refresh(user)
    return user, company


def request_password_reset(db: Session, email: str) -> str | None:
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    if not user:
        return None
    raw_token = secrets.token_urlsafe(64)
    prt = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(prt)
    db.commit()
    return raw_token


def reset_password(db: Session, raw_token: str, new_password: str) -> bool:
    token_hash = hash_token(raw_token)
    prt = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not prt:
        return False
    user = db.query(User).filter(User.id == prt.user_id).first()
    if not user:
        return False
    user.password_hash = get_password_hash(new_password)
    prt.used_at = datetime.now(timezone.utc)
    db.commit()
    return True
