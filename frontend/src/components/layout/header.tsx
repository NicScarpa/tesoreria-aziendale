"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut, User, Building2 } from "lucide-react";

export function Header() {
  const router = useRouter();
  const { user, currentCompany, companies, logout } = useAuthStore();

  const initials = user
    ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
    : "U";

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <header className="flex h-[96px] items-center justify-between border-b border-[#f2f2f2] bg-white px-6">
      <div className="flex min-w-0 flex-col">
        <h1 className="text-[20px] font-semibold leading-[28px] text-[#1a1a1a]">Tesoreria</h1>
        {currentCompany && (
          <span className="truncate text-[13px] font-medium leading-[19.5px] text-[#817f7d]">
            {currentCompany.company_name}
          </span>
        )}
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="flex items-center gap-2 rounded-[8px] border border-transparent px-2 py-1 transition-colors hover:bg-[#f9f9f9]">
            <span className="hidden text-[13px] font-medium leading-[19.5px] text-[#1a1a1a] sm:inline">
              {user ? `${user.first_name} ${user.last_name}` : ""}
            </span>
            <Avatar className="h-10 w-10">
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuItem onClick={() => router.push("/profilo")}>
            <User className="mr-2 h-4 w-4" />
            Profilo
          </DropdownMenuItem>
          {companies.length > 1 && (
            <DropdownMenuItem onClick={() => router.push("/select-company")}>
              <Building2 className="mr-2 h-4 w-4" />
              Cambia azienda
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleLogout}>
            <LogOut className="mr-2 h-4 w-4" />
            Esci
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
