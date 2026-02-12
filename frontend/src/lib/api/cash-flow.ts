import api from "@/lib/api";
import type {
  CashFlowProjection,
  CashFlowSummary,
  CashFlowForecast,
  CashFlowForecastDetail,
  CashFlowForecastListResponse,
  CashFlowScenario,
  CashFlowAlert,
  CashFlowAlertListResponse,
  VarianceResponse,
  ScenarioCompare,
  SeasonalityResponse,
  TrendResponse,
  RunwayResponse,
  CashFlowChartResponse,
  CashFlowTableResponse,
} from "@/types/cash-flow";

// --- Real-time Projection ---

export async function getCashFlowProjection(params?: Record<string, string | number | boolean>) {
  const query = params
    ? "?" + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()
    : "";
  const resp = await api.get<CashFlowProjection>(`/cashflow${query}`);
  return resp.data;
}

export async function getCashFlowSummary() {
  const resp = await api.get<CashFlowSummary>("/cashflow/summary");
  return resp.data;
}

// --- Chart/Table (PRD-08) ---

export async function getChartData(params?: Record<string, string>) {
  const query = params
    ? "?" + new URLSearchParams(params).toString()
    : "";
  const resp = await api.get<CashFlowChartResponse>(`/cashflow/chart${query}`);
  return resp.data;
}

export async function getTableData(params?: Record<string, string>) {
  const query = params
    ? "?" + new URLSearchParams(params).toString()
    : "";
  const resp = await api.get<CashFlowTableResponse>(`/cashflow/table${query}`);
  return resp.data;
}

// --- Forecasts ---

export async function listForecasts(params?: Record<string, string | number>) {
  const query = params
    ? "?" + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()
    : "";
  const resp = await api.get<CashFlowForecastListResponse>(`/cashflow/forecasts${query}`);
  return resp.data;
}

export async function getForecast(id: string) {
  const resp = await api.get<CashFlowForecastDetail>(`/cashflow/forecasts/${id}`);
  return resp.data;
}

export async function createForecast(data: Record<string, unknown>) {
  const resp = await api.post<CashFlowForecast>("/cashflow/forecasts", data);
  return resp.data;
}

export async function updateForecast(id: string, data: Record<string, unknown>) {
  const resp = await api.put<CashFlowForecast>(`/cashflow/forecasts/${id}`, data);
  return resp.data;
}

export async function deleteForecast(id: string) {
  await api.delete(`/cashflow/forecasts/${id}`);
}

export async function refreshForecast(id: string) {
  const resp = await api.post<CashFlowForecast>(`/cashflow/forecasts/${id}/refresh`);
  return resp.data;
}

export async function getVariance(id: string) {
  const resp = await api.get<VarianceResponse>(`/cashflow/forecasts/${id}/variance`);
  return resp.data;
}

// --- Scenarios ---

export async function listScenarios(forecastId: string) {
  const resp = await api.get<CashFlowScenario[]>(`/cashflow/forecasts/${forecastId}/scenarios`);
  return resp.data;
}

export async function createScenario(forecastId: string, data: Record<string, unknown>) {
  const resp = await api.post<CashFlowScenario>(`/cashflow/forecasts/${forecastId}/scenarios`, data);
  return resp.data;
}

export async function updateScenario(forecastId: string, scenarioId: string, data: Record<string, unknown>) {
  const resp = await api.put<CashFlowScenario>(
    `/cashflow/forecasts/${forecastId}/scenarios/${scenarioId}`,
    data
  );
  return resp.data;
}

export async function deleteScenario(forecastId: string, scenarioId: string) {
  await api.delete(`/cashflow/forecasts/${forecastId}/scenarios/${scenarioId}`);
}

export async function applyScenarios(forecastId: string) {
  const resp = await api.post<CashFlowProjection>(`/cashflow/forecasts/${forecastId}/scenarios/apply`);
  return resp.data;
}

export async function compareScenarios(forecastId: string) {
  const resp = await api.get<ScenarioCompare>(`/cashflow/forecasts/${forecastId}/compare`);
  return resp.data;
}

// --- Alerts ---

export async function listAlerts(params?: Record<string, string>) {
  const query = params
    ? "?" + new URLSearchParams(params).toString()
    : "";
  const resp = await api.get<CashFlowAlertListResponse>(`/cashflow/alerts${query}`);
  return resp.data;
}

export async function getAlertCount() {
  const resp = await api.get<{ count: number }>("/cashflow/alerts/count");
  return resp.data.count;
}

export async function resolveAlert(id: string) {
  const resp = await api.put<CashFlowAlert>(`/cashflow/alerts/${id}/resolve`);
  return resp.data;
}

export async function ignoreAlert(id: string) {
  const resp = await api.put<CashFlowAlert>(`/cashflow/alerts/${id}/ignore`);
  return resp.data;
}

export async function checkAlerts() {
  const resp = await api.post<CashFlowAlert[]>("/cashflow/check-alerts");
  return resp.data;
}

// --- Analysis ---

export async function getSeasonality() {
  const resp = await api.get<SeasonalityResponse>("/cashflow/analysis/seasonality");
  return resp.data;
}

export async function getTrends(params?: Record<string, string | number>) {
  const query = params
    ? "?" + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()
    : "";
  const resp = await api.get<TrendResponse>(`/cashflow/analysis/trends${query}`);
  return resp.data;
}

export async function getRunway() {
  const resp = await api.get<RunwayResponse>("/cashflow/analysis/runway");
  return resp.data;
}
