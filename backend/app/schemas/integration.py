import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field
from app.models.enums import (
    IntegrationType, IntegrationConnectionStatus,
    OpenBankingProvider, OpenBankingConnectionStatus, SyncFrequency, SyncLogStatus,
    InvoiceSource, InvoiceDocumentType, InvoiceStatus,
    InvoiceBatchSource, InvoiceBatchStatus,
    WebhookType,
)


# --- Integration Config ---

class IntegrationStatusItem(BaseModel):
    integration_type: IntegrationType
    status: IntegrationConnectionStatus
    is_enabled: bool
    label: str
    description: str

class IntegrationOverviewResponse(BaseModel):
    integrations: list[IntegrationStatusItem]

class IntegrationConfigResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    company_id: uuid.UUID
    integration_type: IntegrationType
    status: IntegrationConnectionStatus
    is_enabled: bool
    config: dict | None = None
    last_test_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

class IntegrationConfigUpdate(BaseModel):
    credentials: dict | None = None
    config: dict | None = None

class IntegrationToggle(BaseModel):
    is_enabled: bool


# --- Open Banking ---

class InstitutionResponse(BaseModel):
    id: str
    name: str
    full_name: str | None = None
    logo_url: str | None = None
    country: str = "IT"
    bic: str | None = None

class OpenBankingConnectRequest(BaseModel):
    institution_id: str
    redirect_url: str

class OpenBankingLinkRequest(BaseModel):
    bank_account_id: str

class OpenBankingConnectionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    company_id: uuid.UUID
    bank_account_id: uuid.UUID | None = None
    provider: OpenBankingProvider
    institution_id: str | None = None
    institution_nome: str | None = None
    institution_logo_url: str | None = None
    stato: OpenBankingConnectionStatus
    consenso_scadenza: datetime | None = None
    consenso_creato_at: datetime | None = None
    ultimo_sync: datetime | None = None
    prossimo_sync: datetime | None = None
    frequenza_sync: SyncFrequency
    sync_attivo: bool
    errore_ultimo: str | None = None
    errore_conteggio: int
    created_at: datetime
    updated_at: datetime

class OpenBankingConnectionListResponse(BaseModel):
    items: list[OpenBankingConnectionResponse]
    total: int

class OpenBankingSyncLogResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    connection_id: uuid.UUID
    data_sync: datetime
    stato: SyncLogStatus
    movimenti_scaricati: int
    movimenti_nuovi: int
    movimenti_duplicati: int
    saldo_aggiornato: bool
    periodo_da: datetime | None = None
    periodo_a: datetime | None = None
    durata_ms: int | None = None
    errore_dettaglio: str | None = None
    request_id: str | None = None

class SyncLogListResponse(BaseModel):
    items: list[OpenBankingSyncLogResponse]
    total: int


# --- Invoice ---

class InvoiceImportResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    company_id: uuid.UUID
    batch_id: uuid.UUID | None = None
    fonte: InvoiceSource
    tipo_documento: InvoiceDocumentType
    stato: InvoiceStatus
    numero_fattura: str | None = None
    data_fattura: date | None = None
    cedente_denominazione: str | None = None
    cedente_piva: str | None = None
    cedente_cf: str | None = None
    cessionario_denominazione: str | None = None
    cessionario_piva: str | None = None
    importo_totale: Decimal | None = None
    imponibile_totale: Decimal | None = None
    iva_totale: Decimal | None = None
    valuta: str
    condizioni_pagamento: str | None = None
    modalita_pagamento: str | None = None
    data_scadenza_pagamento: date | None = None
    iban_pagamento: str | None = None
    xml_file_nome: str | None = None
    identificativo_sdi: str | None = None
    schedule_id: uuid.UUID | None = None
    expected_transaction_id: uuid.UUID | None = None
    errore_dettaglio: str | None = None
    data_importazione: datetime
    data_elaborazione: datetime | None = None

class InvoiceImportListResponse(BaseModel):
    items: list[InvoiceImportResponse]
    total: int

class InvoiceElaborateResponse(BaseModel):
    invoice_id: str
    schedule_id: str
    expected_transaction_id: str | None = None
    message: str

class InvoiceBatchElaborateRequest(BaseModel):
    invoice_ids: list[str] | None = None
    filter_stato: InvoiceStatus | None = None

class InvoiceImportBatchResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    company_id: uuid.UUID
    fonte: InvoiceBatchSource
    data_import: datetime
    totale_fatture: int
    fatture_importate: int
    fatture_errore: int
    fatture_duplicate: int
    stato: InvoiceBatchStatus

class InvoiceBatchListResponse(BaseModel):
    items: list[InvoiceImportBatchResponse]
    total: int


# --- CBI/SEPA ---

class SEPAValidationResponse(BaseModel):
    valid: bool
    errors: list[str] = []
    file_type: str | None = None
    message_id: str | None = None

class CBIParseResponse(BaseModel):
    records_parsed: int
    records: list[dict]
    errors: list[str] = []

class CAMT053ImportResponse(BaseModel):
    transactions_imported: int
    transactions_duplicated: int
    balance_updated: bool
    account_iban: str | None = None


# --- Webhook ---

class WebhookEndpointResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    company_id: uuid.UUID
    tipo: WebhookType
    url_path: str
    is_active: bool
    last_triggered_at: datetime | None = None
    trigger_count: int
    failure_count: int
    created_at: datetime

class WebhookEndpointCreate(BaseModel):
    tipo: WebhookType

class WebhookListResponse(BaseModel):
    items: list[WebhookEndpointResponse]
    total: int


# --- Alerts count for sidebar ---

class IntegrationAlertsCount(BaseModel):
    consents_expiring: int = 0
    invoices_pending: int = 0
    sync_errors: int = 0
    total: int = 0


# --- Agenzia Entrate (Entratel/Fisconline) ---

class AdECredentials(BaseModel):
    cf: str = Field(min_length=11, max_length=16)
    password: str = Field(min_length=1)
    pin: str = Field(min_length=1)


class AdETestResponse(BaseModel):
    success: bool
    message: str


class AdESyncInvoicesRequest(BaseModel):
    date_from: date
    date_to: date
    direction: Literal["issued", "received"]
    debug: bool = False


class AdESyncCorrispettiviRequest(BaseModel):
    date_from: date
    date_to: date
    debug: bool = False


class AdESyncResultResponse(BaseModel):
    success: bool
    scope: str
    imported_new: int = 0
    updated: int = 0
    failed: int = 0
    pending: bool = False
    external_request_id: str | None = None
    message: str | None = None


# --- Invoice Stats ---

class MonthlyBreakdown(BaseModel):
    mese: str
    emesse: float
    ricevute: float

class TopCounterpart(BaseModel):
    nome: str
    totale: float
    documenti: int
    percentuale: float

class InvoiceStatsResponse(BaseModel):
    emesse_count: int
    emesse_totale: float
    ricevute_count: int
    ricevute_totale: float
    da_elaborare: int
    per_mese: list[MonthlyBreakdown]
    top_clienti: list[TopCounterpart]
    top_fornitori: list[TopCounterpart]


class ReceiptImportResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    business_date: date
    external_id: str | None = None
    device_id: str | None = None
    time_rilevazione: datetime | None = None
    gross_total: Decimal | None = None
    net_total: Decimal | None = None
    vat_total: Decimal | None = None
    currency: str
    source: str
    status: str
    raw_available: bool = False
    errore_dettaglio: str | None = None
    created_at: datetime
    updated_at: datetime


class ReceiptImportListResponse(BaseModel):
    items: list[ReceiptImportResponse]
    total: int
