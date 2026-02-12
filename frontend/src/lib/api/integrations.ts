import api from "@/lib/api";
import type {
  IntegrationOverview,
  IntegrationConfig,
  IntegrationAlertsCount,
  InstitutionInfo,
  OpenBankingConnection,
  OpenBankingConnectionListResponse,
  OpenBankingSyncLog,
  SyncLogListResponse,
  InvoiceImport,
  InvoiceImportListResponse,
  InvoiceElaborateResult,
  InvoiceImportBatch,
  InvoiceBatchListResponse,
  SEPAValidationResult,
  CBIParseResult,
  CAMT053ImportResult,
  WebhookEndpoint,
  WebhookListResponse,
} from "@/types/integration";

// --- Config Hub ---

export async function getOverview() {
  const resp = await api.get<IntegrationOverview>("/integrations");
  return resp.data;
}

export async function getAlertsCount() {
  const resp = await api.get<IntegrationAlertsCount>("/integrations/alerts-count");
  return resp.data;
}

export async function getConfig(tipo: string) {
  const resp = await api.get<IntegrationConfig>(`/integrations/${tipo}`);
  return resp.data;
}

export async function updateConfig(tipo: string, data: Record<string, unknown>) {
  const resp = await api.put<IntegrationConfig>(`/integrations/${tipo}`, data);
  return resp.data;
}

export async function testConnection(tipo: string) {
  const resp = await api.post(`/integrations/${tipo}/test`);
  return resp.data;
}

export async function toggleIntegration(tipo: string, is_enabled: boolean) {
  const resp = await api.put<IntegrationConfig>(`/integrations/${tipo}/toggle`, { is_enabled });
  return resp.data;
}

// --- Open Banking ---

export async function searchInstitutions(search?: string, country?: string) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (country) params.set("country", country);
  const query = params.toString() ? `?${params.toString()}` : "";
  const resp = await api.get<InstitutionInfo[]>(`/integrations/open-banking/institutions${query}`);
  return resp.data;
}

export async function connectBank(institution_id: string, redirect_url: string) {
  const resp = await api.post("/integrations/open-banking/connect", { institution_id, redirect_url });
  return resp.data;
}

export async function listConnections() {
  const resp = await api.get<OpenBankingConnectionListResponse>("/integrations/open-banking/connections");
  return resp.data;
}

export async function getConnection(id: string) {
  const resp = await api.get<OpenBankingConnection>(`/integrations/open-banking/connections/${id}`);
  return resp.data;
}

export async function deleteConnection(id: string) {
  await api.delete(`/integrations/open-banking/connections/${id}`);
}

export async function syncConnection(id: string) {
  const resp = await api.post<OpenBankingSyncLog>(`/integrations/open-banking/connections/${id}/sync`);
  return resp.data;
}

export async function linkConnection(connectionId: string, bankAccountId: string) {
  const resp = await api.post<OpenBankingConnection>(
    `/integrations/open-banking/connections/${connectionId}/link`,
    { bank_account_id: bankAccountId }
  );
  return resp.data;
}

export async function renewConsent(id: string) {
  const resp = await api.post(`/integrations/open-banking/connections/${id}/renew`);
  return resp.data;
}

export async function getConnectionLogs(connectionId: string, page?: number, pageSize?: number) {
  const params = new URLSearchParams();
  if (page) params.set("page", String(page));
  if (pageSize) params.set("page_size", String(pageSize));
  const query = params.toString() ? `?${params.toString()}` : "";
  const resp = await api.get<SyncLogListResponse>(
    `/integrations/open-banking/connections/${connectionId}/logs${query}`
  );
  return resp.data;
}

export async function syncAll() {
  const resp = await api.post("/integrations/open-banking/sync-all");
  return resp.data;
}

// --- Fatture Elettroniche ---

export async function uploadInvoice(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await api.post<InvoiceImport>("/integrations/invoices/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return resp.data;
}

export async function uploadBatch(files: File[]) {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));
  const resp = await api.post<InvoiceImportBatch>("/integrations/invoices/upload-batch", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return resp.data;
}

export async function listInvoices(params?: Record<string, string | number>) {
  const query = params ? "?" + new URLSearchParams(
    Object.entries(params).map(([k, v]) => [k, String(v)])
  ).toString() : "";
  const resp = await api.get<InvoiceImportListResponse>(`/integrations/invoices${query}`);
  return resp.data;
}

export async function getInvoice(id: string) {
  const resp = await api.get<InvoiceImport>(`/integrations/invoices/${id}`);
  return resp.data;
}

export async function downloadXml(id: string) {
  const resp = await api.get(`/integrations/invoices/${id}/xml`, { responseType: "blob" });
  return resp.data;
}

export async function downloadPdf(id: string) {
  const resp = await api.get(`/integrations/invoices/${id}/pdf`, { responseType: "blob" });
  return resp.data;
}

export async function elaborateInvoice(id: string) {
  const resp = await api.post<InvoiceElaborateResult>(`/integrations/invoices/${id}/elaborate`);
  return resp.data;
}

export async function elaborateBatch(data: { invoice_ids?: string[]; filter_stato?: string }) {
  const resp = await api.post("/integrations/invoices/elaborate-batch", data);
  return resp.data;
}

export async function ignoreInvoice(id: string) {
  const resp = await api.post<InvoiceImport>(`/integrations/invoices/${id}/ignore`);
  return resp.data;
}

export async function listBatches(page?: number, pageSize?: number) {
  const params = new URLSearchParams();
  if (page) params.set("page", String(page));
  if (pageSize) params.set("page_size", String(pageSize));
  const query = params.toString() ? `?${params.toString()}` : "";
  const resp = await api.get<InvoiceBatchListResponse>(`/integrations/invoices/batches${query}`);
  return resp.data;
}

export async function getBatch(id: string) {
  const resp = await api.get<InvoiceImportBatch>(`/integrations/invoices/batches/${id}`);
  return resp.data;
}

// --- CBI/SEPA ---

export async function parseCBI(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await api.post<CBIParseResult>("/integrations/cbi/parse", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return resp.data;
}

export async function validateSEPA(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await api.post<SEPAValidationResult>("/integrations/sepa/validate", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return resp.data;
}

export async function importRendicontazione(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await api.post("/integrations/cbi/import-rendicontazione", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return resp.data;
}

export async function importCAMT053(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await api.post<CAMT053ImportResult>("/integrations/sepa/import-camt053", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return resp.data;
}

// --- Webhook ---

export async function listWebhooks() {
  const resp = await api.get<WebhookListResponse>("/integrations/webhooks");
  return resp.data;
}

export async function createWebhook(tipo: string) {
  const resp = await api.post<WebhookEndpoint>("/integrations/webhooks", { tipo });
  return resp.data;
}

export async function deleteWebhook(id: string) {
  await api.delete(`/integrations/webhooks/${id}`);
}
