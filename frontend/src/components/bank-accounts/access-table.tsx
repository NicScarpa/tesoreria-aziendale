"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Trash2, UserPlus } from "lucide-react";
import api from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { BankAccountAccess, AccessLevel } from "@/types/bank-account";

const LEVEL_LABELS: Record<string, string> = {
  read: "Lettura",
  write: "Scrittura",
  admin: "Admin",
};

const LEVEL_VARIANTS: Record<string, "default" | "secondary" | "outline"> = {
  read: "outline",
  write: "secondary",
  admin: "default",
};

interface Props {
  accountId: string;
  accesses: BankAccountAccess[];
  onRefresh: () => void;
  loading?: boolean;
}

export function AccessTable({ accountId, accesses, onRefresh, loading }: Props) {
  const [addOpen, setAddOpen] = useState(false);
  const [userId, setUserId] = useState("");
  const [level, setLevel] = useState<AccessLevel>("read");
  const [submitting, setSubmitting] = useState(false);

  const onAdd = async () => {
    setSubmitting(true);
    try {
      await api.post(`/bank-accounts/${accountId}/accesses`, {
        user_id: userId,
        access_level: level,
      });
      toast.success("Accesso aggiunto");
      setAddOpen(false);
      setUserId("");
      setLevel("read");
      onRefresh();
    } catch {
      toast.error("Errore nell'aggiunta dell'accesso");
    } finally {
      setSubmitting(false);
    }
  };

  const onUpdateLevel = async (accessId: string, newLevel: AccessLevel) => {
    try {
      await api.patch(`/bank-accounts/${accountId}/accesses/${accessId}`, {
        access_level: newLevel,
      });
      toast.success("Livello aggiornato");
      onRefresh();
    } catch {
      toast.error("Errore nell'aggiornamento");
    }
  };

  const onDelete = async (accessId: string) => {
    try {
      await api.delete(`/bank-accounts/${accountId}/accesses/${accessId}`);
      toast.success("Accesso rimosso");
      onRefresh();
    } catch {
      toast.error("Errore nella rimozione");
    }
  };

  if (loading) {
    return <div className="h-32 animate-pulse rounded bg-muted" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <UserPlus className="h-4 w-4 mr-2" />
          Aggiungi accesso
        </Button>
      </div>

      {accesses.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground text-sm">
          Nessun accesso specifico configurato
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Utente</TableHead>
              <TableHead>Livello</TableHead>
              <TableHead>Data</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {accesses.map((a) => (
              <TableRow key={a.id}>
                <TableCell>
                  <div>
                    <p className="font-medium">{a.user_name || "—"}</p>
                    <p className="text-sm text-muted-foreground">{a.user_email}</p>
                  </div>
                </TableCell>
                <TableCell>
                  <Select
                    value={a.access_level}
                    onValueChange={(v) => onUpdateLevel(a.id, v as AccessLevel)}
                  >
                    <SelectTrigger className="w-28">
                      <Badge variant={LEVEL_VARIANTS[a.access_level] || "outline"}>
                        {LEVEL_LABELS[a.access_level] || a.access_level}
                      </Badge>
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="read">Lettura</SelectItem>
                      <SelectItem value="write">Scrittura</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(a.created_at).toLocaleDateString("it-IT")}
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(a.id)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Aggiungi accesso</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">ID Utente</label>
              <Input
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="UUID dell'utente"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Livello accesso</label>
              <Select value={level} onValueChange={(v) => setLevel(v as AccessLevel)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="read">Lettura</SelectItem>
                  <SelectItem value="write">Scrittura</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddOpen(false)}>Annulla</Button>
            <Button onClick={onAdd} disabled={!userId || submitting}>
              {submitting ? "Aggiunta..." : "Aggiungi"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
