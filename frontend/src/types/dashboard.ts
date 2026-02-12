// --- Dashboard Types ---

export interface ContoSaldoItem {
  id: string;
  nome: string;
  banca: string | null;
  saldo: number;
  variazione_giorno: number;
  colore: string;
}

export interface SaldiSection {
  totale: number;
  disponibile: number;
  variazione_giorno: number;
  variazione_percentuale: number;
  conti: ContoSaldoItem[];
}

export interface CashFlowMiniDataPoint {
  data: string;
  entrate: number;
  uscite: number;
  saldo: number;
}

export interface CashFlowPreviewSection {
  previsione_7gg: number;
  previsione_30gg: number;
  trend: "crescente" | "decrescente" | "stabile";
  prossimo_alert: string | null;
  mini_chart_data: CashFlowMiniDataPoint[];
}

export interface TopCategoriaItem {
  nome: string;
  importo: number;
  percentuale: number;
}

export interface EntrateUsciteSection {
  entrate: number;
  uscite: number;
  saldo_netto: number;
  confronto_mese_precedente: number;
  top_categorie: TopCategoriaItem[];
}

export interface ScadenzaProssimaItem {
  id: string;
  descrizione: string | null;
  importo: number;
  data_scadenza: string;
  stato: string;
}

export interface ScadenzeSection {
  in_scadenza_oggi: number;
  in_scadenza_7gg: number;
  scadute_conteggio: number;
  scadute_importo: number;
  prossime: ScadenzaProssimaItem[];
}

export interface RiconciliazioneSection {
  percentuale: number;
  movimenti_non_riconciliati: number;
  importo_non_riconciliato: number;
  suggerimenti_pendenti: number;
}

export interface PagamentiSection {
  da_approvare_conteggio: number;
  da_approvare_importo: number;
  in_attesa_esecuzione: number;
  eseguiti_mese: number;
}

export interface AlertItem {
  id: string;
  tipo: string;
  messaggio: string;
  gravita: "info" | "warning" | "critical";
  data_prevista: string | null;
}

export interface AlertSection {
  items: AlertItem[];
  totale: number;
}

export interface AttivitaRecenteItem {
  tipo: "import" | "schedule" | "payment" | "alert";
  descrizione: string;
  data: string;
  link: string | null;
}

export interface QuickActionItem {
  azione: string;
  titolo: string;
  descrizione: string;
  link: string;
  priorita: number;
  icona: string;
}

export interface DashboardData {
  saldi: SaldiSection;
  cash_flow: CashFlowPreviewSection;
  entrate_uscite: EntrateUsciteSection;
  scadenze: ScadenzeSection;
  riconciliazione: RiconciliazioneSection;
  pagamenti: PagamentiSection;
  alert: AlertSection;
  attivita_recenti: AttivitaRecenteItem[];
  quick_actions: QuickActionItem[];
  aggiornato_a: string;
}

export interface DashboardWidget {
  id: string;
  widget_type: WidgetType;
  posizione: number;
  colonna: number;
  dimensione: "small" | "medium" | "large";
  configurazione: Record<string, unknown> | null;
  visibile: boolean;
}

export type WidgetType =
  | "saldo_totale"
  | "cash_flow_mini"
  | "entrate_uscite"
  | "scadenze"
  | "riconciliazione"
  | "pagamenti_pendenti"
  | "alert"
  | "attivita_recenti"
  | "azioni_rapide"
  | "saldi_per_conto";

export interface DashboardSnapshot {
  id: string;
  data: string;
  saldo_totale: number;
  entrate_giorno: number;
  uscite_giorno: number;
  movimenti_non_riconciliati: number;
  scadenze_scadute_importo: number;
  scadenze_scadute_conteggio: number;
  pagamenti_da_approvare: number;
  previsione_30gg: number;
  alert_attivi: number;
  created_at: string;
}

export interface DashboardTrendPoint {
  data: string;
  valore: number;
}

export interface DashboardTrendResponse {
  kpi: string;
  punti: DashboardTrendPoint[];
  variazione: number;
  trend: "crescente" | "decrescente" | "stabile";
}

// --- Label & color maps ---

export const WIDGET_TYPE_LABELS: Record<WidgetType, string> = {
  saldo_totale: "Saldo Totale",
  cash_flow_mini: "Cash Flow",
  entrate_uscite: "Entrate/Uscite",
  scadenze: "Scadenze",
  riconciliazione: "Riconciliazione",
  pagamenti_pendenti: "Pagamenti",
  alert: "Alert",
  attivita_recenti: "Attivita Recenti",
  azioni_rapide: "Azioni Rapide",
  saldi_per_conto: "Saldi per Conto",
};

export const ACTIVITY_TYPE_LABELS: Record<string, string> = {
  import: "Importazione",
  schedule: "Scadenza",
  payment: "Pagamento",
  alert: "Alert",
};

export const GRAVITA_COLORS: Record<string, string> = {
  info: "bg-[#c0c8ff] text-[#1a1a1a]",
  warning: "bg-[#ffd98c] text-[#1a1a1a]",
  critical: "bg-[#fddcdc] text-[#ea0b0b]",
};
