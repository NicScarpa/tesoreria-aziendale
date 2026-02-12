export type ScheduleType = "attiva" | "passiva";

export type ScheduleStatus =
  | "aperta"
  | "parzialmente_pagata"
  | "pagata"
  | "scaduta"
  | "annullata";

export type DocumentType =
  | "fattura_vendita"
  | "fattura_acquisto"
  | "nota_credito"
  | "nota_debito"
  | "stipendio"
  | "tassa_f24"
  | "contributo"
  | "affitto"
  | "utenza"
  | "rata_prestito"
  | "altro";

export type SchedulePriority = "bassa" | "normale" | "alta" | "urgente";

export type RecurrenceType =
  | "settimanale"
  | "mensile"
  | "bimestrale"
  | "trimestrale"
  | "semestrale"
  | "annuale";

export type ScheduleSource =
  | "manuale"
  | "import_csv"
  | "import_fatture_sdi"
  | "ricorrenza_auto";

export type PaymentMethodType =
  | "bonifico"
  | "ri_ba"
  | "sdd"
  | "carta"
  | "contanti"
  | "f24"
  | "altro";

export type ReminderType = "email" | "in_app" | "entrambi";

export interface SchedulePayment {
  id: string;
  schedule_id: string;
  importo: number;
  data_pagamento: string;
  metodo: PaymentMethodType | null;
  riferimento: string | null;
  note: string | null;
  reconciliation_id: string | null;
  created_at: string;
}

export interface ScheduleReminder {
  id: string;
  schedule_id: string;
  giorni_prima: number;
  tipo: ReminderType;
  messaggio: string | null;
  inviato: boolean;
  data_invio: string | null;
  created_at: string;
}

export interface ScheduleAttachment {
  id: string;
  schedule_id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  uploaded_by_user_id: string | null;
  created_at: string;
}

export interface Schedule {
  id: string;
  company_id: string;
  tipo: ScheduleType;
  stato: ScheduleStatus;
  descrizione: string;
  importo_totale: number;
  importo_pagato: number;
  importo_residuo: number;
  valuta: string;
  data_scadenza: string;
  data_emissione: string | null;
  data_pagamento: string | null;
  tipo_documento: DocumentType;
  numero_documento: string | null;
  riferimento_documento: string | null;
  controparte_nome: string | null;
  controparte_iban: string | null;
  counterparty_id: string | null;
  bank_account_id: string | null;
  bank_account_nickname: string | null;
  priorita: SchedulePriority;
  metodo_pagamento: PaymentMethodType | null;
  categoria_id: string | null;
  source: ScheduleSource;
  is_ricorrente: boolean;
  ricorrenza_tipo: RecurrenceType | null;
  ricorrenza_fine: string | null;
  ricorrenza_prossima_generazione: string | null;
  ricorrenza_parent_id: string | null;
  ricorrenza_attiva: boolean;
  expected_transaction_id: string | null;
  note: string | null;
  created_by_user_id: string | null;
  payments: SchedulePayment[];
  created_at: string;
  updated_at: string;
}

export interface ScheduleSummaryTotals {
  somma_attive_aperte: number;
  somma_passive_aperte: number;
  somma_scadute: number;
  conteggio_aperte: number;
  conteggio_parziali: number;
  conteggio_pagate: number;
  conteggio_scadute: number;
  conteggio_annullate: number;
}

export interface ScheduleListResponse {
  items: Schedule[];
  total: number;
  page: number;
  page_size: number;
  totals: ScheduleSummaryTotals;
}

export interface ScheduleCalendarDay {
  data: string;
  scadenze: Schedule[];
}

export interface ScheduleAgingBand {
  fascia: string;
  conteggio: number;
  importo_totale: number;
  importo_residuo: number;
}

export interface ScheduleAgingResponse {
  attive: ScheduleAgingBand[];
  passive: ScheduleAgingBand[];
}

export interface ScheduleSummary {
  totale_attive: number;
  totale_passive: number;
  totale_aperte: number;
  totale_scadute: number;
  somma_attive_aperte: number;
  somma_passive_aperte: number;
  somma_scadute: number;
  prossime_7_giorni: number;
  ricorrenti_attive: number;
}

// Label maps
export const SCHEDULE_STATUS_LABELS: Record<ScheduleStatus, string> = {
  aperta: "Aperta",
  parzialmente_pagata: "Parziale",
  pagata: "Pagata",
  scaduta: "Scaduta",
  annullata: "Annullata",
};

export const SCHEDULE_TYPE_LABELS: Record<ScheduleType, string> = {
  attiva: "Da incassare",
  passiva: "Da pagare",
};

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  fattura_vendita: "Fattura vendita",
  fattura_acquisto: "Fattura acquisto",
  nota_credito: "Nota credito",
  nota_debito: "Nota debito",
  stipendio: "Stipendio",
  tassa_f24: "Tassa F24",
  contributo: "Contributo",
  affitto: "Affitto",
  utenza: "Utenza",
  rata_prestito: "Rata prestito",
  altro: "Altro",
};

export const PRIORITY_LABELS: Record<SchedulePriority, string> = {
  bassa: "Bassa",
  normale: "Normale",
  alta: "Alta",
  urgente: "Urgente",
};

export const PAYMENT_METHOD_LABELS: Record<PaymentMethodType, string> = {
  bonifico: "Bonifico",
  ri_ba: "Ri.Ba.",
  sdd: "SDD",
  carta: "Carta",
  contanti: "Contanti",
  f24: "F24",
  altro: "Altro",
};

export const RECURRENCE_LABELS: Record<RecurrenceType, string> = {
  settimanale: "Settimanale",
  mensile: "Mensile",
  bimestrale: "Bimestrale",
  trimestrale: "Trimestrale",
  semestrale: "Semestrale",
  annuale: "Annuale",
};
