"""Dashboard schemas — Pydantic v2 models for dashboard API."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


# --- Sub-sections ---

class ContoSaldoItem(BaseModel):
    id: uuid.UUID
    nome: str
    banca: str | None = None
    saldo: Decimal
    variazione_giorno: Decimal = Decimal("0")
    colore: str = "#6b7280"

    model_config = {"from_attributes": True}


class SaldiSection(BaseModel):
    totale: Decimal = Decimal("0")
    disponibile: Decimal = Decimal("0")
    variazione_giorno: Decimal = Decimal("0")
    variazione_percentuale: Decimal = Decimal("0")
    conti: list[ContoSaldoItem] = []


class CashFlowMiniDataPoint(BaseModel):
    data: date
    entrate: Decimal = Decimal("0")
    uscite: Decimal = Decimal("0")
    saldo: Decimal = Decimal("0")


class CashFlowPreviewSection(BaseModel):
    previsione_7gg: Decimal = Decimal("0")
    previsione_30gg: Decimal = Decimal("0")
    trend: str = "stabile"  # crescente, decrescente, stabile
    prossimo_alert: str | None = None
    mini_chart_data: list[CashFlowMiniDataPoint] = []


class TopCategoriaItem(BaseModel):
    nome: str
    importo: Decimal
    percentuale: Decimal = Decimal("0")


class EntrateUsciteSection(BaseModel):
    entrate: Decimal = Decimal("0")
    uscite: Decimal = Decimal("0")
    saldo_netto: Decimal = Decimal("0")
    confronto_mese_precedente: Decimal = Decimal("0")  # variazione %
    top_categorie: list[TopCategoriaItem] = []


class ScadenzaProssimaItem(BaseModel):
    id: uuid.UUID
    descrizione: str | None = None
    importo: Decimal
    data_scadenza: date
    stato: str

    model_config = {"from_attributes": True}


class ScadenzeSection(BaseModel):
    in_scadenza_oggi: int = 0
    in_scadenza_7gg: int = 0
    scadute_conteggio: int = 0
    scadute_importo: Decimal = Decimal("0")
    prossime: list[ScadenzaProssimaItem] = []


class RiconciliazioneSection(BaseModel):
    percentuale: Decimal = Decimal("0")
    movimenti_non_riconciliati: int = 0
    importo_non_riconciliato: Decimal = Decimal("0")
    suggerimenti_pendenti: int = 0


class PagamentiSection(BaseModel):
    da_approvare_conteggio: int = 0
    da_approvare_importo: Decimal = Decimal("0")
    in_attesa_esecuzione: int = 0
    eseguiti_mese: int = 0


class AlertItem(BaseModel):
    id: uuid.UUID
    tipo: str
    messaggio: str
    gravita: str = "warning"  # info, warning, critical
    data_prevista: date | None = None

    model_config = {"from_attributes": True}


class AlertSection(BaseModel):
    items: list[AlertItem] = []
    totale: int = 0


class AttivitaRecenteItem(BaseModel):
    tipo: str  # import, schedule, payment, alert
    descrizione: str
    data: datetime
    link: str | None = None


class QuickActionItem(BaseModel):
    azione: str
    titolo: str
    descrizione: str
    link: str
    priorita: int = 0
    icona: str = "zap"


# --- Main response ---

class DashboardResponse(BaseModel):
    saldi: SaldiSection = SaldiSection()
    cash_flow: CashFlowPreviewSection = CashFlowPreviewSection()
    entrate_uscite: EntrateUsciteSection = EntrateUsciteSection()
    scadenze: ScadenzeSection = ScadenzeSection()
    riconciliazione: RiconciliazioneSection = RiconciliazioneSection()
    pagamenti: PagamentiSection = PagamentiSection()
    alert: AlertSection = AlertSection()
    attivita_recenti: list[AttivitaRecenteItem] = []
    quick_actions: list[QuickActionItem] = []
    aggiornato_a: datetime | None = None


# --- Widget CRUD ---

class DashboardWidgetResponse(BaseModel):
    id: uuid.UUID
    widget_type: str
    posizione: int
    colonna: int
    dimensione: str
    configurazione: dict | None = None
    visibile: bool

    model_config = {"from_attributes": True}


class DashboardWidgetUpdateItem(BaseModel):
    widget_type: str
    posizione: int
    colonna: int = 0
    dimensione: str = "medium"
    visibile: bool = True
    configurazione: dict | None = None


class DashboardWidgetUpdateRequest(BaseModel):
    widgets: list[DashboardWidgetUpdateItem]


# --- Snapshot ---

class DashboardSnapshotResponse(BaseModel):
    id: uuid.UUID
    data: date
    saldo_totale: Decimal
    entrate_giorno: Decimal
    uscite_giorno: Decimal
    movimenti_non_riconciliati: int
    scadenze_scadute_importo: Decimal
    scadenze_scadute_conteggio: int
    pagamenti_da_approvare: int
    previsione_30gg: Decimal
    alert_attivi: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Trend ---

class DashboardTrendPoint(BaseModel):
    data: date
    valore: Decimal


class DashboardTrendResponse(BaseModel):
    kpi: str
    punti: list[DashboardTrendPoint] = []
    variazione: Decimal = Decimal("0")
    trend: str = "stabile"
