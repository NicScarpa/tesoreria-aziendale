// --- Enum types ---

export type ReportType =
  | "saldi_conti"
  | "movimenti"
  | "entrate_uscite"
  | "riconciliazione"
  | "scadenzario"
  | "aging"
  | "cash_flow"
  | "pagamenti"
  | "controparte"
  | "personalizzato";

export type ReportFormat = "pdf" | "xlsx" | "csv";

export type ReportExecutionStatus = "in_coda" | "in_generazione" | "completato" | "errore";

export type ReportFrequency = "giornaliero" | "settimanale" | "mensile" | "trimestrale";

// --- Label maps ---

export const REPORT_TYPE_LABELS: Record<ReportType, string> = {
  saldi_conti: "Situazione Saldi",
  movimenti: "Estratto Conto",
  entrate_uscite: "Entrate e Uscite",
  riconciliazione: "Riconciliazione",
  scadenzario: "Scadenzario",
  aging: "Aging Crediti/Debiti",
  cash_flow: "Cash Flow",
  pagamenti: "Pagamenti",
  controparte: "Scheda Controparte",
  personalizzato: "Personalizzato",
};

export const REPORT_FORMAT_LABELS: Record<ReportFormat, string> = {
  pdf: "PDF",
  xlsx: "Excel",
  csv: "CSV",
};

export const REPORT_EXECUTION_STATUS_LABELS: Record<ReportExecutionStatus, string> = {
  in_coda: "In coda",
  in_generazione: "In generazione",
  completato: "Completato",
  errore: "Errore",
};

export const REPORT_FREQUENCY_LABELS: Record<ReportFrequency, string> = {
  giornaliero: "Giornaliero",
  settimanale: "Settimanale",
  mensile: "Mensile",
  trimestrale: "Trimestrale",
};

// --- Status colors ---

export const REPORT_STATUS_COLORS: Record<ReportExecutionStatus, string> = {
  in_coda: "bg-[#f2f2f2] text-[#817f7d]",
  in_generazione: "bg-[#c0c8ff] text-[#1a1a1a]",
  completato: "bg-[#8cddba] text-[#1a1a1a]",
  errore: "bg-[#fddcdc] text-[#ea0b0b]",
};

// --- Icons per tipo ---

export const REPORT_TYPE_ICONS: Record<ReportType, string> = {
  saldi_conti: "Wallet",
  movimenti: "List",
  entrate_uscite: "ArrowUpDown",
  riconciliazione: "CheckCircle",
  scadenzario: "Calendar",
  aging: "Clock",
  cash_flow: "TrendingUp",
  pagamenti: "CreditCard",
  controparte: "Users",
  personalizzato: "FileText",
};

// --- Interfaces ---

export interface ReportDefinition {
  id: string;
  company_id: string | null;
  nome: string;
  descrizione: string | null;
  tipo: ReportType;
  formato_default: ReportFormat;
  parametri_default: Record<string, unknown> | null;
  layout: Record<string, unknown> | null;
  is_system: boolean;
  is_preferito: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface ReportExecution {
  id: string;
  company_id: string;
  report_definition_id: string | null;
  generato_da_user_id: string | null;
  nome: string;
  tipo: string;
  formato: ReportFormat;
  stato: ReportExecutionStatus;
  parametri: Record<string, unknown> | null;
  risultato: Record<string, unknown> | null;
  file_path: string | null;
  file_size: number | null;
  errore: string | null;
  righe_totali: number | null;
  data_generazione: string;
  data_completamento: string | null;
  data_scadenza_file: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReportSchedule {
  id: string;
  company_id: string;
  report_definition_id: string;
  creato_da_user_id: string | null;
  nome: string;
  frequenza: ReportFrequency;
  formato: ReportFormat;
  parametri: Record<string, unknown> | null;
  attivo: boolean;
  prossima_esecuzione: string | null;
  ultima_esecuzione: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReportDefinitionListResponse {
  items: ReportDefinition[];
  total: number;
}

export interface ReportExecutionListResponse {
  items: ReportExecution[];
  total: number;
  page: number;
  page_size: number;
}

export interface ReportScheduleListResponse {
  items: ReportSchedule[];
  total: number;
}
