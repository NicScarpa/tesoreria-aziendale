import api from "@/lib/api";
import type {
  DashboardData,
  DashboardWidget,
  DashboardSnapshot,
  DashboardTrendResponse,
  QuickActionItem,
} from "@/types/dashboard";

// --- Dashboard main ---

export async function getDashboard(params?: Record<string, string>) {
  const query = params
    ? "?" + new URLSearchParams(params).toString()
    : "";
  const resp = await api.get<DashboardData>(`/dashboard${query}`);
  return resp.data;
}

export async function getDashboardSection(section: string, params?: Record<string, string>) {
  const query = params
    ? "?" + new URLSearchParams(params).toString()
    : "";
  const resp = await api.get<Record<string, unknown>>(`/dashboard/section/${section}${query}`);
  return resp.data;
}

// --- Widgets ---

export async function getWidgets() {
  const resp = await api.get<DashboardWidget[]>("/dashboard/widgets");
  return resp.data;
}

export async function updateWidgets(widgets: Omit<DashboardWidget, "id">[]) {
  const resp = await api.put<DashboardWidget[]>("/dashboard/widgets", { widgets });
  return resp.data;
}

export async function resetWidgets() {
  const resp = await api.post<DashboardWidget[]>("/dashboard/widgets/reset");
  return resp.data;
}

// --- Trend ---

export async function getTrend(kpi: string, periodo: string = "30g") {
  const resp = await api.get<DashboardTrendResponse>("/dashboard/trend", {
    params: { kpi, periodo },
  });
  return resp.data;
}

// --- Snapshot ---

export async function generateSnapshot() {
  const resp = await api.post<DashboardSnapshot>("/dashboard/snapshot");
  return resp.data;
}

export async function getSnapshots(params?: Record<string, string>) {
  const query = params
    ? "?" + new URLSearchParams(params).toString()
    : "";
  const resp = await api.get<DashboardSnapshot[]>(`/dashboard/snapshots${query}`);
  return resp.data;
}

// --- Quick Actions ---

export async function getQuickActions() {
  const resp = await api.get<QuickActionItem[]>("/dashboard/quick-actions");
  return resp.data;
}
