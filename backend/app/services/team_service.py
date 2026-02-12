import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models import User, UserCompany, UserCompanyStatus, UserRole
from app.models.enums import AuditAction
from app.services import audit_service


def list_members(db: Session, company_id: uuid.UUID) -> list[UserCompany]:
    return (
        db.query(UserCompany)
        .filter(
            UserCompany.company_id == company_id,
            UserCompany.status != UserCompanyStatus.REMOVED,
        )
        .all()
    )


def invite_member(
    db: Session,
    company_id: uuid.UUID,
    email: str,
    role: UserRole,
    invited_by_user: User,
) -> UserCompany:
    # Check if user already exists
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

    if user:
        # Check if already a member
        existing = (
            db.query(UserCompany)
            .filter(
                UserCompany.user_id == user.id,
                UserCompany.company_id == company_id,
                UserCompany.status != UserCompanyStatus.REMOVED,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Utente già membro dell'azienda",
            )
    else:
        # Create a placeholder user
        user = User(
            email=email,
            password_hash=get_password_hash("PENDING_INVITE"),  # Not usable
            first_name="",
            last_name="",
            email_verified=False,
            is_active=False,
        )
        db.add(user)
        db.flush()

    uc = UserCompany(
        user_id=user.id,
        company_id=company_id,
        role=role,
        status=UserCompanyStatus.INVITED,
        invited_by=invited_by_user.id,
        invited_at=datetime.now(timezone.utc),
    )
    db.add(uc)
    db.commit()
    db.refresh(uc)

    audit_service.log_action(
        db, AuditAction.USER_INVITED,
        user_id=invited_by_user.id,
        company_id=company_id,
        entity_type="user_company",
        entity_id=str(uc.id),
        new_values={"email": email, "role": role.value},
    )
    return uc


def update_member_role(
    db: Session,
    uc_id: uuid.UUID,
    company_id: uuid.UUID,
    new_role: UserRole,
    current_user_role: UserRole,
) -> UserCompany:
    uc = (
        db.query(UserCompany)
        .filter(
            UserCompany.id == uc_id,
            UserCompany.company_id == company_id,
            UserCompany.status != UserCompanyStatus.REMOVED,
        )
        .first()
    )
    if not uc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro non trovato")

    # Admin cannot modify an OWNER
    if uc.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non puoi modificare il ruolo di un OWNER",
        )

    # Only OWNER can promote to ADMIN (no one can promote to OWNER via this endpoint)
    if new_role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usa il trasferimento ownership per promuovere a OWNER",
        )

    uc.role = new_role
    db.commit()
    db.refresh(uc)
    return uc


def update_member_status(
    db: Session,
    uc_id: uuid.UUID,
    company_id: uuid.UUID,
    new_status: UserCompanyStatus,
    current_user_id: uuid.UUID,
) -> UserCompany:
    uc = (
        db.query(UserCompany)
        .filter(
            UserCompany.id == uc_id,
            UserCompany.company_id == company_id,
            UserCompany.status != UserCompanyStatus.REMOVED,
        )
        .first()
    )
    if not uc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro non trovato")

    if uc.user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Non puoi modificare il tuo stato",
        )

    if uc.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non puoi sospendere un OWNER",
        )

    uc.status = new_status
    if new_status == UserCompanyStatus.ACTIVE and uc.joined_at is None:
        uc.joined_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(uc)
    return uc


def remove_member(
    db: Session,
    uc_id: uuid.UUID,
    company_id: uuid.UUID,
    current_user_id: uuid.UUID,
) -> bool:
    uc = (
        db.query(UserCompany)
        .filter(
            UserCompany.id == uc_id,
            UserCompany.company_id == company_id,
            UserCompany.status != UserCompanyStatus.REMOVED,
        )
        .first()
    )
    if not uc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro non trovato")

    if uc.user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Non puoi rimuovere te stesso",
        )

    if uc.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non puoi rimuovere un OWNER",
        )

    uc.status = UserCompanyStatus.REMOVED
    db.commit()

    audit_service.log_action(
        db, AuditAction.USER_REMOVED,
        user_id=current_user_id,
        company_id=company_id,
        entity_type="user_company",
        entity_id=str(uc.id),
    )
    return True


def transfer_ownership(
    db: Session,
    company_id: uuid.UUID,
    current_user: User,
    target_user_id: uuid.UUID,
    password: str,
) -> bool:
    # Verify password
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password non corretta",
        )

    # Get current owner UC
    current_uc = (
        db.query(UserCompany)
        .filter(
            UserCompany.user_id == current_user.id,
            UserCompany.company_id == company_id,
            UserCompany.role == UserRole.OWNER,
            UserCompany.status == UserCompanyStatus.ACTIVE,
        )
        .first()
    )
    if not current_uc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo l'OWNER può trasferire la proprietà",
        )

    # Get target UC
    target_uc = (
        db.query(UserCompany)
        .filter(
            UserCompany.user_id == target_user_id,
            UserCompany.company_id == company_id,
            UserCompany.status == UserCompanyStatus.ACTIVE,
        )
        .first()
    )
    if not target_uc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente target non trovato nell'azienda",
        )

    # Transfer
    current_uc.role = UserRole.ADMIN
    target_uc.role = UserRole.OWNER
    db.commit()

    audit_service.log_action(
        db, AuditAction.ROLE_CHANGED,
        user_id=current_user.id,
        company_id=company_id,
        entity_type="user_company",
        new_values={"from": str(current_user.id), "to": str(target_user_id)},
    )
    return True
