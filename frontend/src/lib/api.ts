import axios from "axios";
import {
  clearAuth,
  getCurrentCompanyId,
  getRefreshToken,
  getToken,
  setRefreshToken,
  setToken,
} from "@/lib/auth";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: aggiunge Authorization + X-Company-ID
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    const companyId = getCurrentCompanyId();
    if (companyId) {
      config.headers["X-Company-ID"] = companyId;
    }
  }
  return config;
});

// Lock per evitare race condition su refresh paralleli
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((p) => {
    if (error) {
      p.reject(error);
    } else {
      p.resolve(token!);
    }
  });
  failedQueue = [];
}

// Response interceptor: tentativo di refresh token su 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      typeof window !== "undefined" &&
      !originalRequest.url?.includes("/auth/login") &&
      !originalRequest.url?.includes("/auth/refresh")
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(api(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearAuth();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        const resp = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`,
          { refresh_token: refreshToken }
        );
        const { access_token, refresh_token: newRefresh } = resp.data;
        setToken(access_token);
        setRefreshToken(newRefresh);
        processQueue(null, access_token);
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearAuth();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
