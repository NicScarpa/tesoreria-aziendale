"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

const PUBLIC_ROUTES = ["/login", "/register", "/forgot-password", "/reset-password"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, checkSession, currentCompany, companies } =
    useAuthStore();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  useEffect(() => {
    if (isLoading) return;

    const isPublicRoute = PUBLIC_ROUTES.some((r) => pathname.startsWith(r));

    if (!isAuthenticated && !isPublicRoute) {
      router.replace(`/login?rd=${encodeURIComponent(pathname)}`);
      return;
    }

    if (isAuthenticated && isPublicRoute) {
      router.replace("/dashboard");
      return;
    }

    // Se autenticato ma nessuna company selezionata e più di una company
    if (
      isAuthenticated &&
      !isPublicRoute &&
      !currentCompany &&
      companies.length > 1 &&
      pathname !== "/select-company"
    ) {
      router.replace("/select-company");
    }
  }, [isAuthenticated, isLoading, pathname, router, currentCompany, companies]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}
