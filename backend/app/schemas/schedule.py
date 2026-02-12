import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# --- Response schemas ---

class SchedulePaymentResponse(BaseModel):
    id: uuid.UUID
    schedule_id: uuid.UUID
    importo: Decimal
    data_pagamento: date
    metodo: str | None = None
    riferimento: str | None = None
    note: str | None = None
    reconciliation_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleReminderResponse(BaseModel):
    id: uuid.UUID
    schedule_id: uuid.UUID
    giorni_prima: int
    tipo: str
    messaggio: str | None = None
    inviato: bool
    data_invio: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleAttachmentResponse(BaseModel):
    id: uuid.UUID
    schedule_id: uuid.UUID
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    uploaded_by_user_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    tipo: str
    stato: str
    descrizione: str
    importo_totale: Decimal
    importo_pagato: Decimal
    importo_residuo: Decimal
    valuta: str
    data_scadenza: date
    data_emissione: date | None = None
    data_pagamento: date | None = None
    tipo_documento: str
    numero_documento: str | None = None
    riferimento_documento: str | None = None
    controparte_nome: str | None = None
    controparte_iban: str | None = None
    counterparty_id: uuid.UUID | None = None
    bank_account_id: uuid.UUID | None = None
    bank_account_nickname: str | None = None
    priorita: str
    metodo_pagamento: str | None = None
    categoria_id: uuid.UUID | None = None
    source: str
    is_ricorrente: bool
    ricorrenza_tipo: str | None = None
    ricorrenza_fine: date | None = None
    ricorrenza_prossima_generazione: date | None = None
    ricorrenza_parent_id: uuid.UUID | None = None
    ricorrenza_attiva: bool
    expected_transaction_id: uuid.UUID | None = None
    note: str | None = None
    created_by_user_id: uuid.UUID | None = None
    payments: list[SchedulePaymentResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduleSummaryTotals(BaseModel):
    somma_attive_aperte: Decimal = Decimal("0")
    somma_passive_aperte: Decimal = Decimal("0")
    somma_scadute: Decimal = Decimal("0")
    conteggio_aperte: int = 0
    conteggio_parziali: int = 0
    conteggio_pagate: int = 0
    conteggio_scadute: int = 0
    conteggio_annullate: int = 0


class ScheduleListResponse(BaseModel):
    items: list[ScheduleResponse]
    total: int
    page: int
    page_size: int
    totals: ScheduleSummaryTotals


# --- Request schemas ---

class ScheduleCreateRequest(BaseModel):
    tipo: str
    descrizione: str = Field(min_length=1, max_length=500)
    importo_totale: Decimal = Field(gt=0)
    valuta: str = "EUR"
    data_scadenza: date
    data_emissione: date | None = None
    tipo_documento: str = "altro"
    numero_documento: str | None = None
    riferimento_documento: str | None = None
    controparte_nome: str | None = None
    controparte_iban: str | None = None
    counterparty_id: uuid.UUID | None = None
    bank_account_id: uuid.UUID | None = None
    priorita: str = "normale"
    metodo_pagamento: str | None = None
    categoria_id: uuid.UUID | None = None
    note: str | None = None
    is_ricorrente: bool = False
    ricorrenza_tipo: str | None = None
    ricorrenza_fine: date | None = None


class ScheduleUpdateRequest(BaseModel):
    descrizione: str | None = Field(None, min_length=1, max_length=500)
    importo_totale: Decimal | None = Field(None, gt=0)
    valuta: str | None = None
    data_scadenza: date | None = None
    data_emissione: date | None = None
    tipo_documento: str | None = None
    numero_documento: str | None = None
    riferimento_documento: str | None = None
    controparte_nome: str | None = None
    controparte_iban: str | None = None
    counterparty_id: uuid.UUID | None = None
    bank_account_id: uuid.UUID | None = None
    priorita: str | None = None
    metodo_pagamento: str | None = None
    categoria_id: uuid.UUID | None = None
    note: str | None = None


class ScheduleStatusUpdateRequest(BaseModel):
    stato: str


class SchedulePaymentCreateRequest(BaseModel):
    importo: Decimal = Field(gt=0)
    data_pagamento: date
    metodo: str | None = None
    riferimento: str | None = None
    note: str | None = None


class ScheduleReminderCreateRequest(BaseModel):
    giorni_prima: int = Field(ge=0, default=3)
    tipo: str = "in_app"
    messaggio: str | None = None


# --- Aggregate views ---

class ScheduleCalendarDay(BaseModel):
    data: date
    scadenze: list[ScheduleResponse]


class ScheduleAgingBand(BaseModel):
    fascia: str
    conteggio: int
    importo_totale: Decimal
    importo_residuo: Decimal


class ScheduleAgingResponse(BaseModel):
    attive: list[ScheduleAgingBand]
    passive: list[ScheduleAgingBand]


class ScheduleSummaryResponse(BaseModel):
    totale_attive: int
    totale_passive: int
    totale_aperte: int
    totale_scadute: int
    somma_attive_aperte: Decimal
    somma_passive_aperte: Decimal
    somma_scadute: Decimal
    prossime_7_giorni: int
    ricorrenti_attive: int


class GenerateRecurringResponse(BaseModel):
    generati: int
    errori: int
    dettaglio: list[str] = []
