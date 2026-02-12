import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# --- Response schemas ---

class PaymentOrderLineResponse(BaseModel):
    id: uuid.UUID
    payment_order_id: uuid.UUID
    beneficiario_nome: str
    beneficiario_iban: str | None = None
    beneficiario_bic: str | None = None
    beneficiario_cf: str | None = None
    beneficiario_indirizzo: str | None = None
    importo: Decimal
    valuta: str
    causale: str | None = None
    end_to_end_id: str | None = None
    stato: str
    counterparty_id: uuid.UUID | None = None
    schedule_id: uuid.UUID | None = None
    # RiBa
    riba_numero_ricevuta: str | None = None
    riba_data_scadenza: date | None = None
    riba_piazza: str | None = None
    riba_abi_banca_domiciliataria: str | None = None
    riba_cab_banca_domiciliataria: str | None = None
    # SDD
    sdd_mandate_id: str | None = None
    sdd_mandate_date: date | None = None
    sdd_mandate_type: str | None = None
    sdd_sequence_type: str | None = None
    # F24
    f24_sezione: str | None = None
    f24_codice_tributo: str | None = None
    f24_rateazione: str | None = None
    f24_anno_riferimento: int | None = None
    f24_mese_riferimento: int | None = None
    f24_importo_debito: Decimal | None = None
    f24_importo_credito: Decimal | None = None
    f24_codice_ente: str | None = None
    f24_codice_sede: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentApprovalResponse(BaseModel):
    id: uuid.UUID
    payment_order_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str | None = None
    azione: str
    commento: str | None = None
    data_azione: datetime

    model_config = {"from_attributes": True}


class PaymentOrderResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    bank_account_id: uuid.UUID | None = None
    bank_account_nickname: str | None = None
    tipo: str
    stato: str
    riferimento_interno: str
    data_esecuzione_richiesta: date
    importo_totale: Decimal
    numero_disposizioni: int
    valuta: str
    priorita: str
    metadata_sepa: dict | None = None
    metadata_extra: dict | None = None
    file_generato_nome: str | None = None
    file_generato_at: datetime | None = None
    approvato_da_user_id: uuid.UUID | None = None
    data_approvazione: datetime | None = None
    creato_da_user_id: uuid.UUID | None = None
    creato_da_user_name: str | None = None
    note: str | None = None
    lines: list[PaymentOrderLineResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentOrderSummaryResponse(BaseModel):
    totale_bozze: int = 0
    totale_da_approvare: int = 0
    totale_approvate: int = 0
    totale_eseguite: int = 0
    importo_bozze: Decimal = Decimal("0")
    importo_da_approvare: Decimal = Decimal("0")
    importo_approvate: Decimal = Decimal("0")
    importo_eseguite: Decimal = Decimal("0")


class PaymentOrderListResponse(BaseModel):
    items: list[PaymentOrderResponse]
    total: int
    page: int
    page_size: int
    summary: PaymentOrderSummaryResponse


class PaymentTemplateResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    nome: str
    tipo: str
    bank_account_id: uuid.UUID | None = None
    dati_template: dict | None = None
    ultimo_utilizzo: datetime | None = None
    volte_utilizzato: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Request schemas ---

class PaymentOrderCreateRequest(BaseModel):
    tipo: str
    bank_account_id: uuid.UUID | None = None
    data_esecuzione_richiesta: date
    valuta: str = "EUR"
    priorita: str = "normale"
    metadata_sepa: dict | None = None
    metadata_extra: dict | None = None
    note: str | None = None


class PaymentOrderUpdateRequest(BaseModel):
    bank_account_id: uuid.UUID | None = None
    data_esecuzione_richiesta: date | None = None
    valuta: str | None = None
    priorita: str | None = None
    metadata_sepa: dict | None = None
    metadata_extra: dict | None = None
    note: str | None = None


class PaymentOrderLineCreateRequest(BaseModel):
    beneficiario_nome: str = Field(min_length=1, max_length=255)
    beneficiario_iban: str | None = None
    beneficiario_bic: str | None = None
    beneficiario_cf: str | None = None
    beneficiario_indirizzo: str | None = None
    importo: Decimal = Field(gt=0)
    valuta: str = "EUR"
    causale: str | None = Field(None, max_length=140)
    end_to_end_id: str | None = Field(None, max_length=35)
    counterparty_id: uuid.UUID | None = None
    schedule_id: uuid.UUID | None = None
    # RiBa
    riba_numero_ricevuta: str | None = None
    riba_data_scadenza: date | None = None
    riba_piazza: str | None = None
    riba_abi_banca_domiciliataria: str | None = None
    riba_cab_banca_domiciliataria: str | None = None
    # SDD
    sdd_mandate_id: str | None = None
    sdd_mandate_date: date | None = None
    sdd_mandate_type: str | None = None
    sdd_sequence_type: str | None = None
    # F24
    f24_sezione: str | None = None
    f24_codice_tributo: str | None = None
    f24_rateazione: str | None = None
    f24_anno_riferimento: int | None = None
    f24_mese_riferimento: int | None = None
    f24_importo_debito: Decimal | None = None
    f24_importo_credito: Decimal | None = None
    f24_codice_ente: str | None = None
    f24_codice_sede: str | None = None


class PaymentOrderLineUpdateRequest(BaseModel):
    beneficiario_nome: str | None = Field(None, min_length=1, max_length=255)
    beneficiario_iban: str | None = None
    beneficiario_bic: str | None = None
    beneficiario_cf: str | None = None
    beneficiario_indirizzo: str | None = None
    importo: Decimal | None = Field(None, gt=0)
    valuta: str | None = None
    causale: str | None = Field(None, max_length=140)
    end_to_end_id: str | None = Field(None, max_length=35)
    counterparty_id: uuid.UUID | None = None
    schedule_id: uuid.UUID | None = None
    # RiBa
    riba_numero_ricevuta: str | None = None
    riba_data_scadenza: date | None = None
    riba_piazza: str | None = None
    riba_abi_banca_domiciliataria: str | None = None
    riba_cab_banca_domiciliataria: str | None = None
    # SDD
    sdd_mandate_id: str | None = None
    sdd_mandate_date: date | None = None
    sdd_mandate_type: str | None = None
    sdd_sequence_type: str | None = None
    # F24
    f24_sezione: str | None = None
    f24_codice_tributo: str | None = None
    f24_rateazione: str | None = None
    f24_anno_riferimento: int | None = None
    f24_mese_riferimento: int | None = None
    f24_importo_debito: Decimal | None = None
    f24_importo_credito: Decimal | None = None
    f24_codice_ente: str | None = None
    f24_codice_sede: str | None = None


class PaymentApprovalRequest(BaseModel):
    commento: str | None = None


class PaymentRejectRequest(BaseModel):
    commento: str = Field(min_length=1, max_length=1000)


class PaymentFromSchedulesRequest(BaseModel):
    schedule_ids: list[uuid.UUID] = Field(min_length=1)
    bank_account_id: uuid.UUID | None = None
    data_esecuzione_richiesta: date
    priorita: str = "normale"
    note: str | None = None


class IbanValidationRequest(BaseModel):
    iban: str = Field(min_length=1, max_length=34)


class IbanValidationResponse(BaseModel):
    valid: bool
    iban_formatted: str | None = None
    error: str | None = None


class PaymentTemplateCreateRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    tipo: str
    bank_account_id: uuid.UUID | None = None
    dati_template: dict | None = None


class PaymentTemplateApplyRequest(BaseModel):
    data_esecuzione_richiesta: date
    override_bank_account_id: uuid.UUID | None = None
    override_priorita: str | None = None
    override_note: str | None = None


class MarkExecutedRequest(BaseModel):
    data_esecuzione: date | None = None
