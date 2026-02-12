"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { NotificationPreference } from "@/types/settings";
import { Switch } from "@/components/ui/switch";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const NOTIFICATION_LABELS: Record<string, string> = {
  low_balance: "Saldo basso",
  critical_balance: "Saldo critico",
  sync_complete: "Sincronizzazione completata",
  sync_error: "Errore sincronizzazione",
  reconciliation_complete: "Riconciliazione completata",
  payment_due: "Scadenza pagamento",
  user_invited: "Nuovo membro invitato",
  role_changed: "Cambio ruolo",
};

export default function NotificationSettingsPage() {
  const { currentCompany } = useAuthStore();
  const companyId = currentCompany?.company_id;

  const [preferences, setPreferences] = useState<NotificationPreference[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);
    api
      .get<NotificationPreference[]>("/notification-preferences")
      .then((res) => {
        setPreferences(res.data);
      })
      .catch(() => {
        toast.error("Errore nel caricamento delle preferenze di notifica");
      })
      .finally(() => setLoading(false));
  }, [companyId]);

  const updatePreference = async (
    notificationType: string,
    channel: "in_app" | "email",
    value: boolean
  ) => {
    const updated = preferences.map((p) =>
      p.notification_type === notificationType
        ? { ...p, [channel]: value }
        : p
    );
    setPreferences(updated);
    setSaving(true);

    try {
      await api.patch("/notification-preferences", {
        preferences: updated.map((p) => ({
          notification_type: p.notification_type,
          in_app: p.in_app,
          email: p.email,
        })),
      });
      toast.success("Preferenze di notifica aggiornate");
    } catch {
      // Rollback
      const rollback = preferences.map((p) =>
        p.notification_type === notificationType
          ? { ...p, [channel]: !value }
          : p
      );
      setPreferences(rollback);
      toast.error("Errore nell'aggiornamento delle preferenze");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Notifiche</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Configura come e quando ricevere le notifiche
          </p>
        </div>
        <Card>
          <CardContent>
            <div className="h-48 animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Notifiche</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Configura come e quando ricevere le notifiche
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Preferenze di notifica</CardTitle>
          <CardDescription>
            Scegli quali notifiche ricevere e attraverso quale canale
          </CardDescription>
        </CardHeader>
        <CardContent>
          {preferences.length === 0 ? (
            <p className="text-muted-foreground text-sm text-center py-8">
              Nessuna preferenza di notifica disponibile
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tipo notifica</TableHead>
                  <TableHead className="text-center w-24">In-app</TableHead>
                  <TableHead className="text-center w-24">Email</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {preferences.map((pref) => (
                  <TableRow key={pref.notification_type}>
                    <TableCell className="font-medium">
                      {NOTIFICATION_LABELS[pref.notification_type] ??
                        pref.notification_type}
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex justify-center">
                        <Switch
                          checked={pref.in_app}
                          onCheckedChange={(checked) =>
                            updatePreference(
                              pref.notification_type,
                              "in_app",
                              checked
                            )
                          }
                          disabled={saving}
                        />
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex justify-center">
                        <Switch
                          checked={pref.email}
                          onCheckedChange={(checked) =>
                            updatePreference(
                              pref.notification_type,
                              "email",
                              checked
                            )
                          }
                          disabled={saving}
                        />
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
