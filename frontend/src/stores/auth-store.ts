"use client";

import { create } from "zustand";
import api from "@/lib/api";
import {
  clearAuth,
  getToken,
  setToken,
  setRefreshToken,
  getCurrentCompanyId,
  setCurrentCompanyId,
} from "@/lib/auth";
import type { User, UserCompany, LoginResponse, UserMeResponse } from "@/types/auth";

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  currentCompany: UserCompany | null;
  companies: UserCompany[];

  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    company_name: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  checkSession: () => Promise<void>;
  setCurrentCompany: (company: UserCompany) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: typeof window !== "undefined" ? getToken() : null,
  isAuthenticated:
    typeof window !== "undefined" ? !!getToken() : false,
  isLoading: true,
  currentCompany: null,
  companies: [],

  login: async (email, password) => {
    const resp = await api.post<LoginResponse>("/auth/login", { email, password });
    const { access_token, refresh_token } = resp.data;
    setToken(access_token);
    setRefreshToken(refresh_token);
    set({ token: access_token, isAuthenticated: true });
    await get().checkSession();
  },

  register: async (data) => {
    const resp = await api.post<LoginResponse>("/auth/register", data);
    const { access_token, refresh_token } = resp.data;
    setToken(access_token);
    setRefreshToken(refresh_token);
    set({ token: access_token, isAuthenticated: true });
    await get().checkSession();
  },

  logout: async () => {
    try {
      const refreshToken =
        typeof window !== "undefined"
          ? localStorage.getItem("refresh_token")
          : null;
      if (refreshToken) {
        await api.post("/auth/logout", { refresh_token: refreshToken });
      }
    } catch {
      // Ignora errori di logout
    }
    clearAuth();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      currentCompany: null,
      companies: [],
    });
  },

  checkSession: async () => {
    const token = getToken();
    if (!token) {
      set({ isLoading: false, isAuthenticated: false });
      return;
    }
    try {
      const resp = await api.get<UserMeResponse>("/users/me");
      const data = resp.data;
      const user: User = {
        id: data.id,
        email: data.email,
        first_name: data.first_name,
        last_name: data.last_name,
        phone: data.phone,
        email_verified: data.email_verified,
        created_at: data.created_at,
      };
      const companies = data.companies;

      // Restore company da localStorage se valida
      const savedCompanyId = getCurrentCompanyId();
      let currentCompany = companies.find((c) => c.company_id === savedCompanyId) || null;
      if (!currentCompany && companies.length === 1) {
        currentCompany = companies[0];
        setCurrentCompanyId(currentCompany.company_id);
      }

      set({
        user,
        companies,
        currentCompany,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      clearAuth();
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        currentCompany: null,
        companies: [],
      });
    }
  },

  setCurrentCompany: (company) => {
    setCurrentCompanyId(company.company_id);
    set({ currentCompany: company });
  },
}));
