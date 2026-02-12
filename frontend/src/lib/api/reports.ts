import api from "@/lib/api";
import type {
  ReportDefinition,
  ReportDefinitionListResponse,
  ReportExecution,
  ReportExecutionListResponse,
  ReportSchedule,
  ReportScheduleListResponse,
} from "@/types/report";

// --- Report Definitions ---

export async function listReportDefinitions(params?: Record<string, string>) {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  const resp = await api.get<ReportDefinitionListResponse>(`/reports${query}`);
  return resp.data;
}

export async function getReportDefinition(id: string) {
  const resp = await api.get<ReportDefinition>(`/reports/${id}`);
  return resp.data;
}

export async function createReportDefinition(data: Record<string, unknown>) {
  const resp = await api.post<ReportDefinition>("/reports", data);
  return resp.data;
}

export async function updateReportDefinition(id: string, data: Record<string, unknown>) {
  const resp = await api.put<ReportDefinition>(`/reports/${id}`, data);
  return resp.data;
}

export async function deleteReportDefinition(id: string) {
  await api.delete(`/reports/${id}`);
}

export async function togglePreferito(id: string) {
  const resp = await api.put<ReportDefinition>(`/reports/${id}/toggle-preferito`);
  return resp.data;
}

// --- Report Generation ---

export async function generateReport(
  definitionId: string,
  data: { formato?: string; parametri?: Record<string, unknown> }
) {
  const resp = await api.post<ReportExecution>(`/reports/${definitionId}/generate`, data);
  return resp.data;
}

export async function generateQuickReport(data: {
  tipo: string;
  formato?: string;
  parametri?: Record<string, unknown>;
  nome?: string;
}) {
  const resp = await api.post<ReportExecution>("/reports/generate-quick", data);
  return resp.data;
}

// --- Report Executions ---

export async function listExecutions(params?: Record<string, string | number>) {
  const query = params
    ? "?" + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()
    : "";
  const resp = await api.get<ReportExecutionListResponse>(`/reports/executions${query}`);
  return resp.data;
}

export async function getExecution(id: string) {
  const resp = await api.get<ReportExecution>(`/reports/executions/${id}`);
  return resp.data;
}

export async function downloadExecution(id: string) {
  const resp = await api.get(`/reports/executions/${id}/download`, {
    responseType: "blob",
  });
  return resp.data;
}

export async function deleteExecution(id: string) {
  await api.delete(`/reports/executions/${id}`);
}

// --- Report Schedules ---

export async function listSchedules() {
  const resp = await api.get<ReportScheduleListResponse>("/reports/schedules");
  return resp.data;
}

export async function createSchedule(data: Record<string, unknown>) {
  const resp = await api.post<ReportSchedule>("/reports/schedules", data);
  return resp.data;
}

export async function updateSchedule(id: string, data: Record<string, unknown>) {
  const resp = await api.put<ReportSchedule>(`/reports/schedules/${id}`, data);
  return resp.data;
}

export async function deleteSchedule(id: string) {
  await api.delete(`/reports/schedules/${id}`);
}

export async function runScheduleNow(id: string) {
  const resp = await api.post<ReportExecution>(`/reports/schedules/${id}/run-now`);
  return resp.data;
}

// --- Download helper ---

export function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
