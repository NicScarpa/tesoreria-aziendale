import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm.attributes import flag_modified

from app.core.deps import DB, CurrentUser
from app.models import Company, UserCompany, UserCompanyStatus
from app.models.enums import AuditAction, UserRole
from app.schemas.company import CompanyResponse, UpdateCompanyRequest
from app.schemas.settings import CompanySettingsResponse, UpdateCompanySettingsRequest
from app.schemas.modules import ModulesResponse, UpdateModulesRequest
from app.services import audit_service, user_service, settings_service

router = APIRouter(prefix="/companies", tags=["companies"])


def _get_user_company(db, user_id: uuid.UUID, company_id: uuid.UUID, min_role: UserRole) -> tuple[Company, UserCompany]:
    uc = (
        db.query(UserCompany)
        .filter(
            UserCompany.user_id == user_id,
            UserCompany.company_id == company_id,
            UserCompany.status == UserCompanyStatus.ACTIVE,
        )
        .first()
    )
    if not uc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso alla company negato")
    if not uc.role >= min_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Ruolo minimo richiesto: {min_role.value}")
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company non trovata")
    return company, uc


@router.get("", response_model=list[CompanyResponse])
def list_companies(current_user: CurrentUser, db: DB):
    user_companies = user_service.get_user_companies(db, current_user.id)
    return [CompanyResponse.model_validate(uc.company) for uc in user_companies]


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: uuid.UUID, current_user: CurrentUser, db: DB):
    company, _uc = _get_user_company(db, current_user.id, company_id, UserRole.VIEWER)
    return CompanyResponse.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: uuid.UUID, body: UpdateCompanyRequest, current_user: CurrentUser, db: DB):
    company, _uc = _get_user_company(db, current_user.id, company_id, UserRole.ADMIN)
    data = body.model_dump(exclude_unset=True)
    if data:
        for key, value in data.items():
            if value is not None:
                setattr(company, key, value)
        db.commit()
        db.refresh(company)
        audit_service.log_action(
            db, AuditAction.COMPANY_UPDATE, user_id=current_user.id, company_id=company.id
        )
    return CompanyResponse.model_validate(company)


# --- Company Settings ---


@router.get("/{company_id}/settings", response_model=CompanySettingsResponse)
def get_company_settings(company_id: uuid.UUID, current_user: CurrentUser, db: DB):
    company, _uc = _get_user_company(db, current_user.id, company_id, UserRole.VIEWER)
    data = settings_service.get_company_settings(company)
    return CompanySettingsResponse(**data)


@router.patch("/{company_id}/settings", response_model=CompanySettingsResponse)
def update_company_settings(
    company_id: uuid.UUID, body: UpdateCompanySettingsRequest, current_user: CurrentUser, db: DB
):
    company, _uc = _get_user_company(db, current_user.id, company_id, UserRole.ADMIN)
    data = settings_service.update_company_settings(
        db, company,
        treasury_settings=body.treasury_settings,
        display_settings=body.display_settings,
    )
    return CompanySettingsResponse(**data)


# --- Company Modules ---


@router.get("/{company_id}/modules", response_model=ModulesResponse)
def get_company_modules(company_id: uuid.UUID, current_user: CurrentUser, db: DB):
    company, _uc = _get_user_company(db, current_user.id, company_id, UserRole.VIEWER)
    features = company.features or {}
    modules = features.get("active_modules", [])
    return ModulesResponse(features=modules)


@router.patch("/{company_id}/modules", response_model=ModulesResponse)
def update_company_modules(
    company_id: uuid.UUID, body: UpdateModulesRequest, current_user: CurrentUser, db: DB
):
    company, _uc = _get_user_company(db, current_user.id, company_id, UserRole.OWNER)
    features = dict(company.features or {})
    features["active_modules"] = body.features
    company.features = features
    flag_modified(company, "features")
    db.commit()
    db.refresh(company)
    return ModulesResponse(features=body.features)
