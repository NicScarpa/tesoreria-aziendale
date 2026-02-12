import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import ALGORITHM
from app.models import Company, User, UserCompany, UserCompanyStatus
from app.models.enums import UserRole

DB = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DB,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token mancante")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token non valido")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token non valido")

    user = db.query(User).filter(User.id == uuid.UUID(user_id), User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utente non trovato")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_company(
    db: DB,
    current_user: CurrentUser,
    x_company_id: Annotated[str | None, Header()] = None,
) -> tuple[Company, UserCompany]:
    if not x_company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header X-Company-ID mancante")
    try:
        company_id = uuid.UUID(x_company_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Company-ID non valido")

    uc = (
        db.query(UserCompany)
        .filter(
            UserCompany.user_id == current_user.id,
            UserCompany.company_id == company_id,
            UserCompany.status == UserCompanyStatus.ACTIVE,
        )
        .first()
    )
    if not uc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso alla company negato")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company non trovata")

    return company, uc


CurrentCompany = Annotated[tuple[Company, UserCompany], Depends(get_current_company)]


def require_role(min_role: UserRole):
    def _check(company_data: CurrentCompany) -> tuple[Company, UserCompany]:
        _company, uc = company_data
        if not uc.role >= min_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Ruolo minimo richiesto: {min_role.value}",
            )
        return company_data
    return _check
