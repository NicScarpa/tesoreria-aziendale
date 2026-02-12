import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# --- Response schemas ---

class ReportDefinitionResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID | None = None
    nome: str
    descrizione: str | None = None
    tipo: str
    formato_default: str
    parametri_default: dict | None = None
    layout: dict | None = None
    is_system: bool
    is_preferito: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportDefinitionListResponse(BaseModel):
    items: list[ReportDefinitionResponse]
    total: int


class ReportExecutionResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    report_definition_id: uuid.UUID | None = None
    generato_da_user_id: uuid.UUID | None = None
    nome: str
    tipo: str
    formato: str
    stato: str
    parametri: dict | None = None
    risultato: dict | None = None
    file_path: str | None = None
    file_size: int | None = None
    errore: str | None = None
    righe_totali: int | None = None
    data_generazione: datetime
    data_completamento: datetime | None = None
    data_scadenza_file: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportExecutionListResponse(BaseModel):
    items: list[ReportExecutionResponse]
    total: int
    page: int
    page_size: int


class ReportScheduleResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    report_definition_id: uuid.UUID
    creato_da_user_id: uuid.UUID | None = None
    nome: str
    frequenza: str
    formato: str
    parametri: dict | None = None
    attivo: bool
    prossima_esecuzione: datetime | None = None
    ultima_esecuzione: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportScheduleListResponse(BaseModel):
    items: list[ReportScheduleResponse]
    total: int


# --- Request schemas ---

class ReportDefinitionCreateRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    descrizione: str | None = None
    tipo: str = "personalizzato"
    formato_default: str = "pdf"
    parametri_default: dict | None = None
    layout: dict | None = None


class ReportDefinitionUpdateRequest(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=255)
    descrizione: str | None = None
    formato_default: str | None = None
    parametri_default: dict | None = None
    layout: dict | None = None


class ReportGenerateRequest(BaseModel):
    formato: str = "pdf"
    parametri: dict | None = None


class ReportGenerateQuickRequest(BaseModel):
    tipo: str
    formato: str = "pdf"
    parametri: dict | None = None
    nome: str | None = None


class ReportScheduleCreateRequest(BaseModel):
    report_definition_id: uuid.UUID
    nome: str = Field(min_length=1, max_length=255)
    frequenza: str
    formato: str = "pdf"
    parametri: dict | None = None


class ReportScheduleUpdateRequest(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=255)
    frequenza: str | None = None
    formato: str | None = None
    parametri: dict | None = None
    attivo: bool | None = None
