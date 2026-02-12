from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models import Company
from app.schemas.settings import TreasurySettings, DisplaySettings


def get_company_settings(company: Company) -> dict:
    features = company.features or {}
    treasury_raw = features.get("treasury_settings", {})
    display_raw = features.get("display_settings", {})
    return {
        "treasury_settings": TreasurySettings(**treasury_raw),
        "display_settings": DisplaySettings(**display_raw),
    }


def update_company_settings(
    db: Session,
    company: Company,
    treasury_settings: TreasurySettings | None = None,
    display_settings: DisplaySettings | None = None,
) -> dict:
    features = dict(company.features or {})
    if treasury_settings is not None:
        features["treasury_settings"] = treasury_settings.model_dump()
    if display_settings is not None:
        features["display_settings"] = display_settings.model_dump()
    company.features = features
    flag_modified(company, "features")
    db.commit()
    db.refresh(company)
    return get_company_settings(company)
