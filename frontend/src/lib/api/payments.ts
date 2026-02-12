import api from "@/lib/api";
import type {
  PaymentOrder,
  PaymentOrderListResponse,
  PaymentOrderSummary,
  PaymentApproval,
  PaymentTemplate,
  IbanValidationResponse,
} from "@/types/payment";

// --- Payment Orders ---

export async function listPaymentOrders(params?: Record<string, string | number>) {
  const query = params ? "?" + new URLSearchParams(
    Object.entries(params).map(([k, v]) => [k, String(v)])
  ).toString() : "";
  const resp = await api.get<PaymentOrderListResponse>(`/payments${query}`);
  return resp.data;
}

export async function getPaymentOrder(id: string) {
  const resp = await api.get<PaymentOrder>(`/payments/${id}`);
  return resp.data;
}

export async function createPaymentOrder(data: Record<string, unknown>) {
  const resp = await api.post<PaymentOrder>("/payments", data);
  return resp.data;
}

export async function updatePaymentOrder(id: string, data: Record<string, unknown>) {
  const resp = await api.put<PaymentOrder>(`/payments/${id}`, data);
  return resp.data;
}

export async function deletePaymentOrder(id: string) {
  await api.delete(`/payments/${id}`);
}

export async function getPaymentSummary() {
  const resp = await api.get<PaymentOrderSummary>("/payments/summary");
  return resp.data;
}

// --- Lines ---

export async function addLine(orderId: string, data: Record<string, unknown>) {
  const resp = await api.post(`/payments/${orderId}/lines`, data);
  return resp.data;
}

export async function updateLine(orderId: string, lineId: string, data: Record<string, unknown>) {
  const resp = await api.put(`/payments/${orderId}/lines/${lineId}`, data);
  return resp.data;
}

export async function deleteLine(orderId: string, lineId: string) {
  await api.delete(`/payments/${orderId}/lines/${lineId}`);
}

// --- Workflow ---

export async function submitOrder(id: string) {
  const resp = await api.post<PaymentOrder>(`/payments/${id}/submit`);
  return resp.data;
}

export async function approveOrder(id: string, commento?: string) {
  const resp = await api.post<PaymentOrder>(`/payments/${id}/approve`, { commento });
  return resp.data;
}

export async function rejectOrder(id: string, commento: string) {
  const resp = await api.post<PaymentOrder>(`/payments/${id}/reject`, { commento });
  return resp.data;
}

export async function getApprovals(id: string) {
  const resp = await api.get<PaymentApproval[]>(`/payments/${id}/approvals`);
  return resp.data;
}

// --- File & Execution ---

export async function generateFile(id: string) {
  const resp = await api.post<PaymentOrder>(`/payments/${id}/generate-file`);
  return resp.data;
}

export async function downloadFile(id: string) {
  const resp = await api.get(`/payments/${id}/download-file`, { responseType: "blob" });
  return resp.data;
}

export async function markSent(id: string) {
  const resp = await api.post<PaymentOrder>(`/payments/${id}/mark-sent`);
  return resp.data;
}

export async function markExecuted(id: string, data_esecuzione?: string) {
  const resp = await api.post<PaymentOrder>(`/payments/${id}/mark-executed`, { data_esecuzione });
  return resp.data;
}

// --- From Schedules ---

export async function createFromSchedules(data: {
  schedule_ids: string[];
  bank_account_id?: string;
  data_esecuzione_richiesta: string;
  priorita?: string;
  note?: string;
}) {
  const resp = await api.post<PaymentOrder>("/payments/from-schedules", data);
  return resp.data;
}

// --- IBAN Validation ---

export async function validateIban(iban: string) {
  const resp = await api.post<IbanValidationResponse>("/payments/validate-iban", { iban });
  return resp.data;
}

// --- Templates ---

export async function listTemplates(tipo?: string) {
  const query = tipo ? `?tipo=${tipo}` : "";
  const resp = await api.get<PaymentTemplate[]>(`/payments/templates${query}`);
  return resp.data;
}

export async function createTemplate(data: Record<string, unknown>) {
  const resp = await api.post<PaymentTemplate>("/payments/templates", data);
  return resp.data;
}

export async function applyTemplate(templateId: string, data: Record<string, unknown>) {
  const resp = await api.post<PaymentOrder>(`/payments/templates/${templateId}/apply`, data);
  return resp.data;
}

export async function deleteTemplate(templateId: string) {
  await api.delete(`/payments/templates/${templateId}`);
}
