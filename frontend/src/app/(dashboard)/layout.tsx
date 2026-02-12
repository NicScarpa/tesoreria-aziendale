"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, currentCompany, companies } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (!currentCompany && companies.length > 1) {
      router.replace("/select-company");
    }
  }, [isAuthenticated, isLoading, currentCompany, companies, router]);

  if (isLoading || !isAuthenticated) return null;

  return (
    <div className="flex h-screen bg-white">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto px-6 pb-6">{children}</main>
      </div>
    </div>
  );
}
