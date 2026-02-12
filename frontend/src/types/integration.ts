// --- Enum types ---

export type IntegrationType = "open_banking" | "fatture_elettroniche" | "cbi_corporate_banking";

export type IntegrationConnectionStatus = "non_configurata" | "configurata" | "connessa" | "errore";

export type OpenBankingProvider = "nordigen_gocardless" | "tink" | "salt_edge" | "cbi_globe" | "fabrick" | "generico";

export type OpenBankingConnectionStatus = "in_attesa_consenso" | "attiva" | "scaduta" | "revocata" | "errore";

export type SyncFrequency = "ogni_ora" | "ogni_6_ore" | "giornaliero" | "manuale";

export type SyncLogStatus = "successo" | "parziale" | "errore";

export type InvoiceSource = "cassetto_fiscale" | "upload_xml" | "sdi_api" | "altro";

export type InvoiceDocumentType = "fattura_vendita" | "fattura_acquisto" | "nota_credito_vendita" | "nota_credito_acquisto" | "autofattura";

export type InvoiceStatus = "importata" | "elaborata" | "scadenza_creata" | "errore" | "ignorata";

export type InvoiceBatchSource = "cassetto_fiscale" | "upload_multiplo" | "sdi_api";

export type InvoiceBatchStatus = "in_corso" | "completato" | "completato_con_errori" | "fallito";

export type WebhookType = "open_banking_sync" | "sdi_notifica" | "pagamento_esito" | "generico";

// --- Label maps ---

export const INTEGRATION_TYPE_LABELS: Record<IntegrationType, string> = {
  open_banking: "Open Banking",
  fatture_elettroniche: "Fatture Elettroniche",
  cbi_corporate_banking: "CBI Corporate Banking",
};

export const INTEGRATION_STATUS_LABELS: Record<IntegrationConnectionStatus, string> = {
  non_configurata: "Non Configurata",
  configurata: "Configurata",
  connessa: "Connessa",
  errore: "Errore",
};

export const OB_CONNECTION_STATUS_LABELS: Record<OpenBankingConnectionStatus, string> = {
  in_attesa_consenso: "In Attesa Consenso",
  attiva: "Attiva",
  scaduta: "Scaduta",
  revocata: "Revocata",
  errore: "Errore",
};

export const SYNC_FREQUENCY_LABELS: Record<SyncFrequency, string> = {
  ogni_ora: "Ogni Ora",
  ogni_6_ore: "Ogni 6 Ore",
  giornaliero: "Giornaliero",
  manuale: "Manuale",
};

export const SYNC_LOG_STATUS_LABELS: Record<SyncLogStatus, string> = {
  successo: "Successo",
  parziale: "Parziale",
  errore: "Errore",
};

export const INVOICE_DOC_TYPE_LABELS: Record<InvoiceDocumentType, string> = {
  fattura_vendita: "Fattura Vendita",
  fattura_acquisto: "Fattura Acquisto",
  nota_credito_vendita: "NC Vendita",
  nota_credito_acquisto: "NC Acquisto",
  autofattura: "Autofattura",
};

export const INVOICE_STATUS_LABELS: Record<InvoiceStatus, string> = {
  importata: "Importata",
  elaborata: "Elaborata",
  scadenza_creata: "Scadenza Creata",
  errore: "Errore",
  ignorata: "Ignorata",
};

export const INVOICE_BATCH_STATUS_LABELS: Record<InvoiceBatchStatus, string> = {
  in_corso: "In Corso",
  completato: "Completato",
  completato_con_errori: "Completato con Errori",
  fallito: "Fallito",
};

export const WEBHOOK_TYPE_LABELS: Record<WebhookType, string> = {
  open_banking_sync: "Open Banking Sync",
  sdi_notifica: "SDI Notifica",
  pagamento_esito: "Pagamento Esito",
  generico: "Generico",
};

// --- Status colors ---

export const INTEGRATION_STATUS_COLORS: Record<IntegrationConnectionStatus, string> = {
  non_configurata: "bg-[#f2f2f2] text-[#817f7d]",
  configurata: "bg-[#c0c8ff] text-[#1a1a1a]",
  connessa: "bg-[#8cddba] text-[#1a1a1a]",
  errore: "bg-[#fddcdc] text-[#ea0b0b]",
};

export const OB_CONNECTION_STATUS_COLORS: Record<OpenBankingConnectionStatus, string> = {
  in_attesa_consenso: "bg-[#ffd98c] text-[#1a1a1a]",
  attiva: "bg-[#8cddba] text-[#1a1a1a]",
  scaduta: "bg-[#ffe6b2] text-[#1a1a1a]",
  revocata: "bg-[#e5e4e3] text-[#817f7d]",
  errore: "bg-[#fddcdc] text-[#ea0b0b]",
};

export const SYNC_LOG_STATUS_COLORS: Record<SyncLogStatus, string> = {
  successo: "bg-[#8cddba] text-[#1a1a1a]",
  parziale: "bg-[#ffd98c] text-[#1a1a1a]",
  errore: "bg-[#fddcdc] text-[#ea0b0b]",
};

export const INVOICE_STATUS_COLORS: Record<InvoiceStatus, string> = {
  importata: "bg-[#c0c8ff] text-[#1a1a1a]",
  elaborata: "bg-[#d9deff] text-[#1a1a1a]",
  scadenza_creata: "bg-[#8cddba] text-[#1a1a1a]",
  errore: "bg-[#fddcdc] text-[#ea0b0b]",
  ignorata: "bg-[#e5e4e3] text-[#817f7d]",
};

export const INVOICE_DOC_TYPE_COLORS: Record<InvoiceDocumentType, string> = {
  fattura_vendita: "bg-[#8cddba] text-[#1a1a1a]",
  fattura_acquisto: "bg-[#c0c8ff] text-[#1a1a1a]",
  nota_credito_vendita: "bg-[#ffd98c] text-[#1a1a1a]",
  nota_credito_acquisto: "bg-[#ffe6b2] text-[#1a1a1a]",
  autofattura: "bg-[#c8b9df] text-[#1a1a1a]",
};

// --- Interfaces ---

export interface IntegrationStatusItem {
  integration_type: IntegrationType;
  status: IntegrationConnectionStatus;
  is_enabled: boolean;
  label: string;
  description: string;
}

export interface IntegrationOverview {
  integrations: IntegrationStatusItem[];
}

export interface IntegrationConfig {
  id: string;
  company_id: string;
  integration_type: IntegrationType;
  status: IntegrationConnectionStatus;
  is_enabled: boolean;
  config: Record<string, unknown> | null;
  last_test_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface InstitutionInfo {
  id: string;
  name: string;
  full_name: string | null;
  logo_url: string | null;
  country: string;
  bic: string | null;
}

export interface OpenBankingConnection {
  id: string;
  company_id: string;
  bank_account_id: string | null;
  provider: OpenBankingProvider;
  institution_id: string | null;
  institution_nome: string | null;
  institution_logo_url: string | null;
  stato: OpenBankingConnectionStatus;
  consenso_scadenza: string | null;
  consenso_creato_at: string | null;
  ultimo_sync: string | null;
  prossimo_sync: string | null;
  frequenza_sync: SyncFrequency;
  sync_attivo: boolean;
  errore_ultimo: string | null;
  errore_conteggio: number;
  created_at: string;
  updated_at: string;
}

export interface OpenBankingConnectionListResponse {
  items: OpenBankingConnection[];
  total: number;
}

export interface OpenBankingSyncLog {
  id: string;
  connection_id: string;
  data_sync: string;
  stato: SyncLogStatus;
  movimenti_scaricati: number;
  movimenti_nuovi: number;
  movimenti_duplicati: number;
  saldo_aggiornato: boolean;
  periodo_da: string | null;
  periodo_a: string | null;
  durata_ms: number | null;
  errore_dettaglio: string | null;
  request_id: string | null;
}

export interface SyncLogListResponse {
  items: OpenBankingSyncLog[];
  total: number;
}

export interface InvoiceImport {
  id: string;
  company_id: string;
  batch_id: string | null;
  fonte: InvoiceSource;
  tipo_documento: InvoiceDocumentType;
  stato: InvoiceStatus;
  numero_fattura: string | null;
  data_fattura: string | null;
  cedente_denominazione: string | null;
  cedente_piva: string | null;
  cedente_cf: string | null;
  cessionario_denominazione: string | null;
  cessionario_piva: string | null;
  importo_totale: number | null;
  imponibile_totale: number | null;
  iva_totale: number | null;
  valuta: string;
  condizioni_pagamento: string | null;
  modalita_pagamento: string | null;
  data_scadenza_pagamento: string | null;
  iban_pagamento: string | null;
  xml_file_nome: string | null;
  identificativo_sdi: string | null;
  schedule_id: string | null;
  expected_transaction_id: string | null;
  errore_dettaglio: string | null;
  data_importazione: string;
  data_elaborazione: string | null;
}

export interface InvoiceImportListResponse {
  items: InvoiceImport[];
  total: number;
}

export interface InvoiceElaborateResult {
  invoice_id: string;
  schedule_id: string;
  expected_transaction_id: string | null;
  message: string;
}

export interface InvoiceImportBatch {
  id: string;
  company_id: string;
  fonte: InvoiceBatchSource;
  data_import: string;
  totale_fatture: number;
  fatture_importate: number;
  fatture_errore: number;
  fatture_duplicate: number;
  stato: InvoiceBatchStatus;
}

export interface InvoiceBatchListResponse {
  items: InvoiceImportBatch[];
  total: number;
}

export interface SEPAValidationResult {
  valid: boolean;
  errors: string[];
  file_type: string | null;
  message_id: string | null;
}

export interface CBIParseResult {
  records_parsed: number;
  records: Record<string, unknown>[];
  errors: string[];
}

export interface CAMT053ImportResult {
  transactions_imported: number;
  transactions_duplicated: number;
  balance_updated: boolean;
  account_iban: string | null;
}

export interface WebhookEndpoint {
  id: string;
  company_id: string;
  tipo: WebhookType;
  url_path: string;
  is_active: boolean;
  last_triggered_at: string | null;
  trigger_count: number;
  failure_count: number;
  created_at: string;
}

export interface WebhookListResponse {
  items: WebhookEndpoint[];
  total: number;
}

export interface IntegrationAlertsCount {
  consents_expiring: number;
  invoices_pending: number;
  sync_errors: number;
  total: number;
}
