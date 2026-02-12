import uuid

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models import User, UserCompany, UserCompanyStatus


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()


def update_user(db: Session, user: User, data: dict) -> User:
    for key, value in data.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
    if not verify_password(current_password, user.password_hash):
        return False
    user.password_hash = get_password_hash(new_password)
    db.commit()
    return True


def get_user_companies(db: Session, user_id: uuid.UUID) -> list[UserCompany]:
    return (
        db.query(UserCompany)
        .filter(UserCompany.user_id == user_id, UserCompany.status == UserCompanyStatus.ACTIVE)
        .all()
    )
