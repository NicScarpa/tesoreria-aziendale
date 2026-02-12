"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth-store";
import api from "@/lib/api";
import { changePasswordSchema, type ChangePasswordInput } from "@/lib/validations/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function ProfiloPage() {
  const { user, companies, checkSession } = useAuthStore();
  const [editLoading, setEditLoading] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);

  const [firstName, setFirstName] = useState(user?.first_name ?? "");
  const [lastName, setLastName] = useState(user?.last_name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");

  const {
    register: registerPw,
    handleSubmit: handlePwSubmit,
    formState: { errors: pwErrors },
    reset: resetPw,
  } = useForm<ChangePasswordInput>({
    resolver: zodResolver(changePasswordSchema),
  });

  async function handleProfileUpdate(e: React.FormEvent) {
    e.preventDefault();
    setEditLoading(true);
    try {
      await api.patch("/users/me", {
        first_name: firstName,
        last_name: lastName,
        phone: phone || null,
      });
      await checkSession();
      toast.success("Profilo aggiornato");
    } catch {
      toast.error("Errore durante l'aggiornamento");
    } finally {
      setEditLoading(false);
    }
  }

  async function onChangePassword(data: ChangePasswordInput) {
    setPwLoading(true);
    try {
      await api.post("/auth/change-password", data);
      toast.success("Password cambiata con successo");
      resetPw();
    } catch {
      toast.error("Password attuale non corretta");
    } finally {
      setPwLoading(false);
    }
  }

  if (!user) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Profilo</h1>

      <Card>
        <CardHeader>
          <CardTitle>Informazioni personali</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProfileUpdate} className="space-y-4">
            <div className="space-y-2">
              <Label>Email</Label>
              <Input value={user.email} disabled />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name">Nome</Label>
                <Input
                  id="first_name"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name">Cognome</Label>
                <Input
                  id="last_name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Telefono</Label>
              <Input
                id="phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+39 ..."
              />
            </div>
            <Button type="submit" disabled={editLoading}>
              {editLoading ? "Salvataggio..." : "Salva modifiche"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Cambia password</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePwSubmit(onChangePassword)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current_password">Password attuale</Label>
              <Input
                id="current_password"
                type="password"
                {...registerPw("current_password")}
              />
              {pwErrors.current_password && (
                <p className="text-sm text-destructive">{pwErrors.current_password.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="new_password">Nuova password</Label>
              <Input
                id="new_password"
                type="password"
                {...registerPw("new_password")}
              />
              {pwErrors.new_password && (
                <p className="text-sm text-destructive">{pwErrors.new_password.message}</p>
              )}
            </div>
            <Button type="submit" disabled={pwLoading}>
              {pwLoading ? "Cambio in corso..." : "Cambia password"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Aziende</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {companies.map((c) => (
              <div key={c.company_id} className="flex items-center justify-between">
                <span className="font-medium">{c.company_name}</span>
                <Badge variant="secondary" className="capitalize">
                  {c.role}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
