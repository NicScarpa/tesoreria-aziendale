import re
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.models.enums import AccountStatus, AccountType, BalanceSource, AccessLevel


# --- IBAN validation helper ---

def validate_iban(iban: str) -> str:
    """Validate IBAN using modulo 97 check."""
    cleaned = iban.replace(" ", "").upper()
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$", cleaned):
        raise ValueError("Formato IBAN non valido")
    # Italian IBAN: 27 characters
    if cleaned[:2] == "IT" and len(cleaned) != 27:
        raise ValueError("IBAN italiano deve avere 27 caratteri")
    # Modulo 97 check
    rearranged = cleaned[4:] + cleaned[:4]
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        else:
            numeric += str(ord(ch) - ord("A") + 10)
    if int(numeric) % 97 != 1:
        raise ValueError("IBAN non valido (check digit errato)")
    return cleaned


# --- Response schemas ---

class BankAccountResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    bank_connection_id: uuid.UUID | None = None
    nickname: str | None = None
    iban: str | None = None
    bic: str | None = None
    account_number: str | None = None
    currency: str
    current_balance: Decimal | None = None
    available_balance: Decimal | None = None
    balance_date: datetime | None = None
    credit_limit: Decimal | None = None
    status: AccountStatus
    ignore_balance: bool
    hidden_at: datetime | None = None
    allow_balance_change: bool
    provider_account_id: str | None = None
    identifiers: list | dict | None = None
    last_synced_at: datetime | None = None
    account_type: AccountType | None = None
    color: str | None = None
    notes: str | None = None
    is_default: bool
    bank_name: str | None = None
    bank_abi: str | None = None
    bank_cab: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BankAccountSummaryResponse(BaseModel):
    count: int
    total_current_balance: Decimal
    total_available_balance: Decimal
    difference: Decimal
    total_credit_limit: Decimal


class BankAccountBalanceResponse(BaseModel):
    id: uuid.UUID
    bank_account_id: uuid.UUID
    balance_date: date
    current_balance: Decimal | None = None
    available_balance: Decimal | None = None
    source: BalanceSource
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BalanceChartPointResponse(BaseModel):
    date: date
    current_balance: Decimal | None = None
    available_balance: Decimal | None = None


class BankAccountAccessResponse(BaseModel):
    id: uuid.UUID
    bank_account_id: uuid.UUID
    user_id: uuid.UUID
    user_email: str | None = None
    user_name: str | None = None
    access_level: AccessLevel
    granted_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Request schemas ---

class CreateBankAccountRequest(BaseModel):
    nickname: str
    iban: str | None = None
    bic: str | None = None
    account_number: str | None = None
    currency: str = "EUR"
    current_balance: Decimal | None = None
    available_balance: Decimal | None = None
    credit_limit: Decimal | None = None
    account_type: AccountType | None = None
    color: str | None = "#6b7280"
    notes: str | None = None
    is_default: bool = False
    bank_name: str | None = None

    @field_validator("iban")
    @classmethod
    def check_iban(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_iban(v)
        return v

    @field_validator("color")
    @classmethod
    def check_color(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Colore deve essere in formato #RRGGBB")
        return v

    @field_validator("currency")
    @classmethod
    def check_currency(cls, v: str) -> str:
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Valuta deve essere codice ISO 4217 (3 lettere)")
        return v.upper()


class UpdateBankAccountRequest(BaseModel):
    nickname: str | None = None
    iban: str | None = None
    bic: str | None = None
    account_number: str | None = None
    currency: str | None = None
    credit_limit: Decimal | None = None
    account_type: AccountType | None = None
    color: str | None = None
    notes: str | None = None
    is_default: bool | None = None
    bank_name: str | None = None
    ignore_balance: bool | None = None

    @field_validator("iban")
    @classmethod
    def check_iban(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_iban(v)
        return v

    @field_validator("color")
    @classmethod
    def check_color(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Colore deve essere in formato #RRGGBB")
        return v

    @field_validator("currency")
    @classmethod
    def check_currency(cls, v: str | None) -> str | None:
        if v is not None:
            if len(v) != 3 or not v.isalpha():
                raise ValueError("Valuta deve essere codice ISO 4217 (3 lettere)")
            return v.upper()
        return v


class UpdateBalanceRequest(BaseModel):
    current_balance: Decimal | None = None
    available_balance: Decimal | None = None
    notes: str | None = None


class CreateBalanceEntryRequest(BaseModel):
    balance_date: date
    current_balance: Decimal | None = None
    available_balance: Decimal | None = None
    source: BalanceSource = BalanceSource.MANUAL
    notes: str | None = None


class CreateBankAccountAccessRequest(BaseModel):
    user_id: uuid.UUID
    access_level: AccessLevel = AccessLevel.READ


class UpdateBankAccountAccessRequest(BaseModel):
    access_level: AccessLevel
