const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const COMPANY_ID_KEY = "current_company_id";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token: string): void {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

export function removeRefreshToken(): void {
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getCurrentCompanyId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(COMPANY_ID_KEY);
}

export function setCurrentCompanyId(id: string): void {
  localStorage.setItem(COMPANY_ID_KEY, id);
}

export function removeCurrentCompanyId(): void {
  localStorage.removeItem(COMPANY_ID_KEY);
}

export function clearAuth(): void {
  removeToken();
  removeRefreshToken();
  removeCurrentCompanyId();
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
