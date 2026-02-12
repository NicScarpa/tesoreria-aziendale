import re
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    vat_number: str | None = None
    tax_number: str | None = None
    country: str
    address: str | None = None
    fiscal_regime: str | None = None
    group_vat_number: str | None = None
    city: str | None = None
    postal_code: str | None = None
    province_code: str | None = None
    certified_email: str | None = None
    destination_code: str | None = None
    default_currency: str = "EUR"
    logo_url: str | None = None
    features: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpdateCompanyRequest(BaseModel):
    name: str | None = None
    vat_number: str | None = None
    tax_number: str | None = None
    country: str | None = None
    address: str | None = None
    fiscal_regime: str | None = None
    group_vat_number: str | None = None
    city: str | None = None
    postal_code: str | None = None
    province_code: str | None = None
    certified_email: str | None = None
    destination_code: str | None = None
    default_currency: str | None = None
    logo_url: str | None = None

    @field_validator("vat_number")
    @classmethod
    def validate_vat_number(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^\d{11}$", v):
            raise ValueError("P.IVA deve essere di 11 cifre")
        # Luhn check
        total = 0
        for i, digit in enumerate(v):
            d = int(digit)
            if i % 2 == 0:
                total += d
            else:
                doubled = d * 2
                total += doubled if doubled < 10 else doubled - 9
        if total % 10 != 0:
            raise ValueError("P.IVA non valida (checksum)")
        return v

    @field_validator("tax_number")
    @classmethod
    def validate_tax_number(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^[A-Z0-9]{16}$", v.upper()):
            raise ValueError("Codice fiscale deve essere 16 caratteri alfanumerici")
        return v.upper()

    @field_validator("destination_code")
    @classmethod
    def validate_destination_code(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^[A-Z0-9]{7}$", v.upper()):
            raise ValueError("Codice SDI deve essere 7 caratteri alfanumerici")
        return v.upper()

    @field_validator("certified_email")
    @classmethod
    def validate_certified_email(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("PEC non valida")
        return v.lower()
