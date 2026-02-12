// --- Enum types ---

export type ForecastStatus = "bozza" | "attiva" | "archiviata";
export type ForecastType = "base" | "ottimistico" | "pessimistico" | "personalizzato";
export type CashFlowLineType = "entrata" | "uscita";
export type CashFlowSource =
  | "movimento_reale"
  | "scadenza"
  | "pagamento_pianificato"
  | "ricorrenza"
  | "manuale"
  | "stima_storica";
export type ConfidenceLevel = "certa" | "alta" | "media" | "bassa";
export type ScenarioAdjustmentType = "aggiunta" | "rimozione" | "modifica_importo" | "spostamento_data";
export type CashFlowAlertType = "sotto_soglia_minima" | "sopra_soglia_massima" | "saldo_negativo" | "varianza_alta";
export type AlertStatus = "attivo" | "risolto" | "ignorato";

// --- Label maps ---

export const FORECAST_STATUS_LABELS: Record<ForecastStatus, string> = {
  bozza: "Bozza",
  attiva: "Attiva",
  archiviata: "Archiviata",
};

export const FORECAST_TYPE_LABELS: Record<ForecastType, string> = {
  base: "Base",
  ottimistico: "Ottimistico",
  pessimistico: "Pessimistico",
  personalizzato: "Personalizzato",
};

export const CASH_FLOW_SOURCE_LABELS: Record<CashFlowSource, string> = {
  movimento_reale: "Movimento Reale",
  scadenza: "Scadenza",
  pagamento_pianificato: "Pagamento Pianificato",
  ricorrenza: "Ricorrenza",
  manuale: "Manuale",
  stima_storica: "Stima Storica",
};

export const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  certa: "Certa",
  alta: "Alta",
  media: "Media",
  bassa: "Bassa",
};

export const ALERT_TYPE_LABELS: Record<CashFlowAlertType, string> = {
  sotto_soglia_minima: "Sotto Soglia Minima",
  sopra_soglia_massima: "Sopra Soglia Massima",
  saldo_negativo: "Saldo Negativo",
  varianza_alta: "Varianza Alta",
};

export const ALERT_STATUS_LABELS: Record<AlertStatus, string> = {
  attivo: "Attivo",
  risolto: "Risolto",
  ignorato: "Ignorato",
};

export const SCENARIO_TYPE_LABELS: Record<ScenarioAdjustmentType, string> = {
  aggiunta: "Aggiunta",
  rimozione: "Rimozione",
  modifica_importo: "Modifica Importo",
  spostamento_data: "Spostamento Data",
};

// --- Status colors ---

export const FORECAST_STATUS_COLORS: Record<ForecastStatus, string> = {
  bozza: "bg-[#f2f2f2] text-[#817f7d]",
  attiva: "bg-[#8cddba] text-[#1a1a1a]",
  archiviata: "bg-[#c0c8ff] text-[#1a1a1a]",
};

export const CONFIDENCE_COLORS: Record<ConfidenceLevel, string> = {
  certa: "bg-[#8cddba] text-[#1a1a1a]",
  alta: "bg-[#c0c8ff] text-[#1a1a1a]",
  media: "bg-[#ffd98c] text-[#1a1a1a]",
  bassa: "bg-[#e5e4e3] text-[#817f7d]",
};

export const ALERT_STATUS_COLORS: Record<AlertStatus, string> = {
  attivo: "bg-[#fddcdc] text-[#ea0b0b]",
  risolto: "bg-[#8cddba] text-[#1a1a1a]",
  ignorato: "bg-[#e5e4e3] text-[#817f7d]",
};

export const ALERT_TYPE_COLORS: Record<CashFlowAlertType, string> = {
  sotto_soglia_minima: "bg-[#ffd98c] text-[#1a1a1a]",
  sopra_soglia_massima: "bg-[#c0c8ff] text-[#1a1a1a]",
  saldo_negativo: "bg-[#fddcdc] text-[#ea0b0b]",
  varianza_alta: "bg-[#c8b9df] text-[#1a1a1a]",
};

// --- Interfaces ---

export interface CashFlowProjectionLine {
  data: string;
  tipo: CashFlowLineType;
  importo: number;
  categoria: string | null;
  descrizione: string | null;
  fonte: CashFlowSource;
  fonte_id: string | null;
  confidenza: ConfidenceLevel;
  saldo_progressivo: number;
  is_realizzata: boolean;
}

export interface CashFlowProjection {
  saldo_iniziale: number;
  saldo_finale: number;
  totale_entrate: number;
  totale_uscite: number;
  data_inizio: string;
  data_fine: string;
  lines: CashFlowProjectionLine[];
}

export interface CashFlowSummary {
  saldo_attuale: number;
  previsione_7gg: number;
  previsione_30gg: number;
  previsione_90gg: number;
  trend_7gg: number;
  trend_30gg: number;
  prossimo_alert: CashFlowAlert | null;
  runway_mesi: number | null;
  burn_rate_mensile: number | null;
}

export interface CashFlowForecastLine {
  id: string;
  forecast_id: string;
  data: string;
  tipo: CashFlowLineType;
  importo: number;
  categoria: string | null;
  descrizione: string | null;
  fonte: CashFlowSource;
  fonte_id: string | null;
  confidenza: ConfidenceLevel;
  saldo_progressivo: number;
  is_realizzata: boolean;
  varianza: number | null;
  created_at: string;
  updated_at: string;
}

export interface CashFlowScenario {
  id: string;
  forecast_id: string;
  nome: string;
  descrizione: string | null;
  tipo_aggiustamento: ScenarioAdjustmentType;
  data_originale: string | null;
  data_modificata: string | null;
  importo_originale: number | null;
  importo_modificato: number | null;
  tipo_movimento: CashFlowLineType | null;
  categoria: string | null;
  attivo: boolean;
  created_at: string;
  updated_at: string;
}

export interface CashFlowAlert {
  id: string;
  company_id: string;
  forecast_id: string | null;
  tipo: CashFlowAlertType;
  data_prevista: string;
  saldo_previsto: number;
  soglia: number;
  messaggio: string;
  stato: AlertStatus;
  notificato: boolean;
  notificato_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CashFlowForecast {
  id: string;
  company_id: string;
  creato_da_user_id: string | null;
  nome: string;
  descrizione: string | null;
  data_inizio: string;
  data_fine: string;
  saldo_iniziale: number;
  saldo_finale_previsto: number;
  totale_entrate_previste: number;
  totale_uscite_previste: number;
  stato: ForecastStatus;
  tipo: ForecastType;
  parametri: Record<string, unknown> | null;
  is_auto: boolean;
  created_at: string;
  updated_at: string;
}

export interface CashFlowForecastDetail extends CashFlowForecast {
  lines: CashFlowForecastLine[];
  scenarios: CashFlowScenario[];
}

export interface CashFlowForecastListResponse {
  items: CashFlowForecast[];
  total: number;
  page: number;
  page_size: number;
}

export interface CashFlowAlertListResponse {
  items: CashFlowAlert[];
  total: number;
}

export interface VarianceLine {
  data: string;
  categoria: string | null;
  importo_previsto: number;
  importo_reale: number;
  varianza: number;
  varianza_percentuale: number | null;
}

export interface VarianceResponse {
  forecast_id: string;
  accuracy: number;
  totale_previsto: number;
  totale_reale: number;
  varianza_totale: number;
  lines: VarianceLine[];
}

export interface ScenarioCompare {
  base: CashFlowProjection;
  con_scenari: CashFlowProjection;
  delta_saldo_finale: number;
}

export interface SeasonalityMonth {
  mese: number;
  entrate_medie: number;
  uscite_medie: number;
  saldo_netto_medio: number;
}

export interface SeasonalityResponse {
  mesi: SeasonalityMonth[];
  periodo_analisi_mesi: number;
}

export interface TrendPoint {
  periodo: string;
  entrate: number;
  uscite: number;
  saldo_netto: number;
}

export interface TrendResponse {
  punti: TrendPoint[];
  trend_entrate: string;
  trend_uscite: string;
  raggruppamento: string;
}

export interface RunwayResponse {
  saldo_attuale: number;
  burn_rate_mensile: number;
  runway_mesi: number;
  data_esaurimento: string | null;
  mesi_analisi: number;
}

export interface CashFlowChartPoint {
  periodo: string;
  saldo: number;
  entrate: number;
  uscite: number;
}

export interface CashFlowChartResponse {
  punti: CashFlowChartPoint[];
  raggruppamento: string;
}

export interface CashFlowTableRow {
  categoria: string;
  tipo: CashFlowLineType;
  periodi: Record<string, number>;
  totale: number;
}

export interface CashFlowTableResponse {
  righe: CashFlowTableRow[];
  periodi: string[];
  totali_entrate: Record<string, number>;
  totali_uscite: Record<string, number>;
  saldi_netti: Record<string, number>;
}
