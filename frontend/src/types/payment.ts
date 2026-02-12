// --- Enum types ---

export type PaymentOrderType =
  | "sepa_credit_transfer"
  | "riba"
  | "sdd"
  | "f24"
  | "bonifico_estero";

export type PaymentOrderStatus =
  | "bozza"
  | "da_approvare"
  | "approvata"
  | "file_generato"
  | "inviata_banca"
  | "eseguita"
  | "rifiutata"
  | "annullata";

export type PaymentPriority = "normale" | "alta" | "urgente";

export type PaymentLineStatus = "inclusa" | "eseguita" | "rifiutata" | "esclusa";

export type ApprovalAction = "approvata" | "rifiutata" | "richiesta_modifica";

export type SDDMandateType = "core" | "b2b";

export type SDDSequenceType = "frst" | "rcur" | "fnal" | "ooff";

export type F24SectionType = "erario" | "inps" | "regioni" | "imu_altri_enti";

// --- Label maps ---

export const PAYMENT_ORDER_TYPE_LABELS: Record<PaymentOrderType, string> = {
  sepa_credit_transfer: "Bonifico SEPA",
  riba: "RiBa",
  sdd: "SDD",
  f24: "F24",
  bonifico_estero: "Bonifico Estero",
};

export const PAYMENT_ORDER_STATUS_LABELS: Record<PaymentOrderStatus, string> = {
  bozza: "Bozza",
  da_approvare: "Da Approvare",
  approvata: "Approvata",
  file_generato: "File Generato",
  inviata_banca: "Inviata alla Banca",
  eseguita: "Eseguita",
  rifiutata: "Rifiutata",
  annullata: "Annullata",
};

export const PAYMENT_PRIORITY_LABELS: Record<PaymentPriority, string> = {
  normale: "Normale",
  alta: "Alta",
  urgente: "Urgente",
};

export const PAYMENT_LINE_STATUS_LABELS: Record<PaymentLineStatus, string> = {
  inclusa: "Inclusa",
  eseguita: "Eseguita",
  rifiutata: "Rifiutata",
  esclusa: "Esclusa",
};

export const F24_SECTION_LABELS: Record<F24SectionType, string> = {
  erario: "Erario",
  inps: "INPS",
  regioni: "Regioni",
  imu_altri_enti: "IMU / Altri enti",
};

// --- Status colors ---

export const PAYMENT_STATUS_COLORS: Record<PaymentOrderStatus, string> = {
  bozza: "bg-[#f2f2f2] text-[#817f7d]",
  da_approvare: "bg-[#ffd98c] text-[#1a1a1a]",
  approvata: "bg-[#c0c8ff] text-[#1a1a1a]",
  file_generato: "bg-[#d9deff] text-[#1a1a1a]",
  inviata_banca: "bg-[#c8b9df] text-[#1a1a1a]",
  eseguita: "bg-[#8cddba] text-[#1a1a1a]",
  rifiutata: "bg-[#fddcdc] text-[#ea0b0b]",
  annullata: "bg-[#e5e4e3] text-[#817f7d]",
};

// --- Interfaces ---

export interface PaymentOrderLine {
  id: string;
  payment_order_id: string;
  beneficiario_nome: string;
  beneficiario_iban: string | null;
  beneficiario_bic: string | null;
  beneficiario_cf: string | null;
  beneficiario_indirizzo: string | null;
  importo: number;
  valuta: string;
  causale: string | null;
  end_to_end_id: string | null;
  stato: PaymentLineStatus;
  counterparty_id: string | null;
  schedule_id: string | null;
  // RiBa
  riba_numero_ricevuta: string | null;
  riba_data_scadenza: string | null;
  riba_piazza: string | null;
  riba_abi_banca_domiciliataria: string | null;
  riba_cab_banca_domiciliataria: string | null;
  // SDD
  sdd_mandate_id: string | null;
  sdd_mandate_date: string | null;
  sdd_mandate_type: SDDMandateType | null;
  sdd_sequence_type: SDDSequenceType | null;
  // F24
  f24_sezione: F24SectionType | null;
  f24_codice_tributo: string | null;
  f24_rateazione: string | null;
  f24_anno_riferimento: number | null;
  f24_mese_riferimento: number | null;
  f24_importo_debito: number | null;
  f24_importo_credito: number | null;
  f24_codice_ente: string | null;
  f24_codice_sede: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentApproval {
  id: string;
  payment_order_id: string;
  user_id: string;
  user_name: string | null;
  azione: ApprovalAction;
  commento: string | null;
  data_azione: string;
}

export interface PaymentOrder {
  id: string;
  company_id: string;
  bank_account_id: string | null;
  bank_account_nickname: string | null;
  tipo: PaymentOrderType;
  stato: PaymentOrderStatus;
  riferimento_interno: string;
  data_esecuzione_richiesta: string;
  importo_totale: number;
  numero_disposizioni: number;
  valuta: string;
  priorita: PaymentPriority;
  metadata_sepa: Record<string, unknown> | null;
  metadata_extra: Record<string, unknown> | null;
  file_generato_nome: string | null;
  file_generato_at: string | null;
  approvato_da_user_id: string | null;
  data_approvazione: string | null;
  creato_da_user_id: string | null;
  creato_da_user_name: string | null;
  note: string | null;
  lines: PaymentOrderLine[];
  created_at: string;
  updated_at: string;
}

export interface PaymentOrderSummary {
  totale_bozze: number;
  totale_da_approvare: number;
  totale_approvate: number;
  totale_eseguite: number;
  importo_bozze: number;
  importo_da_approvare: number;
  importo_approvate: number;
  importo_eseguite: number;
}

export interface PaymentOrderListResponse {
  items: PaymentOrder[];
  total: number;
  page: number;
  page_size: number;
  summary: PaymentOrderSummary;
}

export interface PaymentTemplate {
  id: string;
  company_id: string;
  nome: string;
  tipo: PaymentOrderType;
  bank_account_id: string | null;
  dati_template: Record<string, unknown> | null;
  ultimo_utilizzo: string | null;
  volte_utilizzato: number;
  created_at: string;
  updated_at: string;
}

export interface IbanValidationResponse {
  valid: boolean;
  iban_formatted: string | null;
  error: string | null;
}

// --- Workflow steps ---

export const WORKFLOW_STEPS: PaymentOrderStatus[] = [
  "bozza",
  "da_approvare",
  "approvata",
  "file_generato",
  "inviata_banca",
  "eseguita",
];

export const TERMINAL_STATUSES: PaymentOrderStatus[] = [
  "eseguita",
  "rifiutata",
  "annullata",
];
