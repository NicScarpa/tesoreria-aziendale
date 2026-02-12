from pydantic import BaseModel


class TreasurySettings(BaseModel):
    min_cash_threshold: float | None = None
    critical_cash_threshold: float | None = None
    advance_notice_days: int = 7
    auto_categorize: bool = False
    auto_reconcile: bool = False
    cashflow_update_mode: str = "manual"  # "manual" | "daily" | "realtime"


class DisplaySettings(BaseModel):
    date_format: str = "DD/MM/YYYY"
    decimal_separator: str = ","
    thousands_separator: str = "."
    timezone: str = "Europe/Rome"
    first_day_of_week: int = 1  # 0=Sunday, 1=Monday


class CompanySettingsResponse(BaseModel):
    treasury_settings: TreasurySettings
    display_settings: DisplaySettings

    model_config = {"from_attributes": True}


class UpdateCompanySettingsRequest(BaseModel):
    treasury_settings: TreasurySettings | None = None
    display_settings: DisplaySettings | None = None
