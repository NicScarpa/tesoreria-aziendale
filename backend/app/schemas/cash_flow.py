import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# --- Response schemas ---

class CashFlowForecastLineResponse(BaseModel):
    id: uuid.UUID
    forecast_id: uuid.UUID
    data: date
    tipo: str
    importo: Decimal
    categoria: str | None = None
    descrizione: str | None = None
    fonte: str
    fonte_id: str | None = None
    confidenza: str
    saldo_progressivo: Decimal
    is_realizzata: bool
    varianza: Decimal | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CashFlowScenarioResponse(BaseModel):
    id: uuid.UUID
    forecast_id: uuid.UUID
    nome: str
    descrizione: str | None = None
    tipo_aggiustamento: str
    data_originale: date | None = None
    data_modificata: date | None = None
    importo_originale: Decimal | None = None
    importo_modificato: Decimal | None = None
    tipo_movimento: str | None = None
    categoria: str | None = None
    attivo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CashFlowAlertResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    forecast_id: uuid.UUID | None = None
    tipo: str
    data_prevista: date
    saldo_previsto: Decimal
    soglia: Decimal
    messaggio: str
    stato: str
    notificato: bool
    notificato_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CashFlowForecastResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    creato_da_user_id: uuid.UUID | None = None
    nome: str
    descrizione: str | None = None
    data_inizio: date
    data_fine: date
    saldo_iniziale: Decimal
    saldo_finale_previsto: Decimal
    totale_entrate_previste: Decimal
    totale_uscite_previste: Decimal
    stato: str
    tipo: str
    parametri: dict | None = None
    is_auto: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CashFlowForecastDetailResponse(CashFlowForecastResponse):
    lines: list[CashFlowForecastLineResponse] = []
    scenarios: list[CashFlowScenarioResponse] = []


class CashFlowForecastListResponse(BaseModel):
    items: list[CashFlowForecastResponse]
    total: int
    page: int
    page_size: int


# --- Real-time projection response ---

class CashFlowProjectionLine(BaseModel):
    data: date
    tipo: str
    importo: Decimal
    categoria: str | None = None
    descrizione: str | None = None
    fonte: str
    fonte_id: str | None = None
    confidenza: str
    saldo_progressivo: Decimal
    is_realizzata: bool = False


class CashFlowProjectionResponse(BaseModel):
    saldo_iniziale: Decimal
    saldo_finale: Decimal
    totale_entrate: Decimal
    totale_uscite: Decimal
    data_inizio: date
    data_fine: date
    lines: list[CashFlowProjectionLine]


class CashFlowSummaryResponse(BaseModel):
    saldo_attuale: Decimal
    previsione_7gg: Decimal
    previsione_30gg: Decimal
    previsione_90gg: Decimal
    trend_7gg: Decimal
    trend_30gg: Decimal
    prossimo_alert: CashFlowAlertResponse | None = None
    runway_mesi: Decimal | None = None
    burn_rate_mensile: Decimal | None = None


# --- Variance ---

class VarianceLineResponse(BaseModel):
    data: date
    categoria: str | None = None
    importo_previsto: Decimal
    importo_reale: Decimal
    varianza: Decimal
    varianza_percentuale: Decimal | None = None


class VarianceResponse(BaseModel):
    forecast_id: uuid.UUID
    accuracy: Decimal
    totale_previsto: Decimal
    totale_reale: Decimal
    varianza_totale: Decimal
    lines: list[VarianceLineResponse]


# --- Scenario compare ---

class ScenarioCompareResponse(BaseModel):
    base: CashFlowProjectionResponse
    con_scenari: CashFlowProjectionResponse
    delta_saldo_finale: Decimal


# --- Analysis ---

class SeasonalityMonthResponse(BaseModel):
    mese: int
    entrate_medie: Decimal
    uscite_medie: Decimal
    saldo_netto_medio: Decimal


class SeasonalityResponse(BaseModel):
    mesi: list[SeasonalityMonthResponse]
    periodo_analisi_mesi: int


class TrendPointResponse(BaseModel):
    periodo: str
    entrate: Decimal
    uscite: Decimal
    saldo_netto: Decimal


class TrendResponse(BaseModel):
    punti: list[TrendPointResponse]
    trend_entrate: str  # crescente, decrescente, stabile
    trend_uscite: str
    raggruppamento: str


class RunwayResponse(BaseModel):
    saldo_attuale: Decimal
    burn_rate_mensile: Decimal
    runway_mesi: Decimal
    data_esaurimento: date | None = None
    mesi_analisi: int


# --- Chart/Table (PRD-08) ---

class CashFlowChartPoint(BaseModel):
    periodo: str
    saldo: Decimal
    entrate: Decimal
    uscite: Decimal


class CashFlowChartResponse(BaseModel):
    punti: list[CashFlowChartPoint]
    raggruppamento: str


class CashFlowTableRow(BaseModel):
    categoria: str
    tipo: str  # entrata / uscita
    periodi: dict[str, Decimal]
    totale: Decimal


class CashFlowTableResponse(BaseModel):
    righe: list[CashFlowTableRow]
    periodi: list[str]
    totali_entrate: dict[str, Decimal]
    totali_uscite: dict[str, Decimal]
    saldi_netti: dict[str, Decimal]


class CashFlowCellDetailItem(BaseModel):
    data: date
    descrizione: str | None = None
    importo: Decimal
    fonte: str
    controparte: str | None = None


class CashFlowCellDetailResponse(BaseModel):
    categoria: str
    periodo: str
    tipo: str
    items: list[CashFlowCellDetailItem]
    totale: Decimal


# --- Request schemas ---

class CashFlowForecastCreateRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    descrizione: str | None = None
    data_inizio: date
    data_fine: date
    tipo: str = "base"
    bank_account_ids: list[uuid.UUID] | None = None
    includi_scadenze: bool = True
    includi_pagamenti: bool = True
    includi_ricorrenze: bool = True
    includi_stime_storiche: bool = False


class CashFlowForecastUpdateRequest(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=255)
    descrizione: str | None = None
    stato: str | None = None


class CashFlowScenarioCreateRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    descrizione: str | None = None
    tipo_aggiustamento: str
    data_originale: date | None = None
    data_modificata: date | None = None
    importo_originale: Decimal | None = None
    importo_modificato: Decimal | None = None
    tipo_movimento: str | None = None
    categoria: str | None = None


class CashFlowScenarioUpdateRequest(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=255)
    descrizione: str | None = None
    tipo_aggiustamento: str | None = None
    data_originale: date | None = None
    data_modificata: date | None = None
    importo_originale: Decimal | None = None
    importo_modificato: Decimal | None = None
    tipo_movimento: str | None = None
    categoria: str | None = None
    attivo: bool | None = None


# --- Budget (PRD-08) ---

class BudgetCreateRequest(BaseModel):
    categoria: str
    tipo: str  # entrata / uscita
    importi_mensili: dict[str, Decimal]  # {"2026-01": 5000, "2026-02": 4500}


class BudgetSuggestionResponse(BaseModel):
    categoria: str
    tipo: str
    importo_suggerito: Decimal
    base_calcolo: str  # media_3_mesi, media_6_mesi, etc.


# --- Alert list response ---

class CashFlowAlertListResponse(BaseModel):
    items: list[CashFlowAlertResponse]
    total: int
