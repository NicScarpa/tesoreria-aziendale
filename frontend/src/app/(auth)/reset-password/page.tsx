"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import api from "@/lib/api";
import { resetPasswordSchema, type ResetPasswordInput } from "@/lib/validations/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordInput>({
    resolver: zodResolver(resetPasswordSchema),
  });

  async function onSubmit(data: ResetPasswordInput) {
    if (!token) {
      toast.error("Token mancante");
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/reset-password", {
        token,
        new_password: data.new_password,
      });
      toast.success("Password reimpostata con successo");
      router.replace("/login");
    } catch {
      toast.error("Token non valido o scaduto");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">Link non valido</CardTitle>
          <CardDescription>
            Il link di reset non è valido. Richiedi un nuovo link.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/forgot-password">
            <Button className="w-full">Richiedi nuovo link</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-2xl">Nuova password</CardTitle>
        <CardDescription>Inserisci la tua nuova password.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="new_password">Nuova password</Label>
            <Input id="new_password" type="password" {...register("new_password")} />
            {errors.new_password && (
              <p className="text-sm text-destructive">{errors.new_password.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm_password">Conferma password</Label>
            <Input id="confirm_password" type="password" {...register("confirm_password")} />
            {errors.confirm_password && (
              <p className="text-sm text-destructive">{errors.confirm_password.message}</p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Reset in corso..." : "Reimposta password"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
