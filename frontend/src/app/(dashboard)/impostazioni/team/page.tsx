"use client";

import { useEffect, useState, useCallback } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { MoreHorizontal, UserPlus, ShieldAlert } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { TeamMember } from "@/types/settings";
import {
  inviteMemberSchema,
  transferOwnershipSchema,
  type InviteMemberInput,
  type TransferOwnershipInput,
} from "@/lib/validations/settings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const ROLE_LABELS: Record<string, string> = {
  owner: "Owner",
  admin: "Admin",
  editor: "Editor",
  viewer: "Viewer",
};

const ROLE_VARIANTS: Record<
  string,
  "default" | "secondary" | "outline" | "destructive"
> = {
  owner: "default",
  admin: "secondary",
  editor: "outline",
  viewer: "outline",
};

const STATUS_LABELS: Record<string, string> = {
  active: "Attivo",
  invited: "Invitato",
  suspended: "Sospeso",
  removed: "Rimosso",
};

const STATUS_VARIANTS: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  active: "default",
  invited: "secondary",
  suspended: "destructive",
  removed: "outline",
};

export default function TeamSettingsPage() {
  const { currentCompany } = useAuthStore();
  const companyId = currentCompany?.company_id;
  const userRole = currentCompany?.role;
  const isOwner = userRole === "owner";
  const canManage = isOwner || userRole === "admin";

  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [transferOpen, setTransferOpen] = useState(false);
  const [inviting, setInviting] = useState(false);
  const [transferring, setTransferring] = useState(false);

  const inviteForm = useForm<InviteMemberInput>({
    resolver: zodResolver(inviteMemberSchema),
    defaultValues: {
      email: "",
      role: "viewer",
    },
  });

  const transferForm = useForm<TransferOwnershipInput>({
    resolver: zodResolver(transferOwnershipSchema),
    defaultValues: {
      target_user_id: "",
      password: "",
    },
  });

  const loadMembers = useCallback(async () => {
    if (!companyId) return;
    try {
      const res = await api.get<TeamMember[]>("/company-users");
      setMembers(res.data);
    } catch {
      toast.error("Errore nel caricamento del team");
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  const onInvite = async (data: InviteMemberInput) => {
    setInviting(true);
    try {
      await api.post("/company-users/invite", data);
      toast.success(`Invito inviato a ${data.email}`);
      setInviteOpen(false);
      inviteForm.reset();
      await loadMembers();
    } catch {
      toast.error("Errore nell'invio dell'invito");
    } finally {
      setInviting(false);
    }
  };

  const onTransfer = async (data: TransferOwnershipInput) => {
    setTransferring(true);
    try {
      await api.post("/company-users/transfer-ownership", data);
      toast.success("Ownership trasferita con successo");
      setTransferOpen(false);
      transferForm.reset();
      await loadMembers();
    } catch {
      toast.error("Errore nel trasferimento ownership");
    } finally {
      setTransferring(false);
    }
  };

  const updateMemberRole = async (
    memberId: string,
    role: string
  ) => {
    try {
      await api.patch(`/company-users/${memberId}`, { role });
      toast.success("Ruolo aggiornato");
      await loadMembers();
    } catch {
      toast.error("Errore nell'aggiornamento del ruolo");
    }
  };

  const toggleMemberStatus = async (member: TeamMember) => {
    const newStatus = member.status === "suspended" ? "active" : "suspended";
    try {
      await api.patch(`/company-users/${member.id}`, {
        status: newStatus,
      });
      toast.success(
        newStatus === "suspended" ? "Utente sospeso" : "Utente riattivato"
      );
      await loadMembers();
    } catch {
      toast.error("Errore nell'aggiornamento dello stato");
    }
  };

  const removeMember = async (memberId: string) => {
    try {
      await api.delete(`/company-users/${memberId}`);
      toast.success("Membro rimosso");
      await loadMembers();
    } catch {
      toast.error("Errore nella rimozione del membro");
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  // Filtra i membri eleggibili per il trasferimento ownership (attivi, non owner)
  const transferCandidates = members.filter(
    (m) => m.role !== "owner" && m.status === "active"
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Team</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Gestisci i membri del team e i permessi
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Team</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Gestisci i membri del team e i permessi
          </p>
        </div>
        <div className="flex gap-2">
          {isOwner && (
            <Dialog open={transferOpen} onOpenChange={setTransferOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                  <ShieldAlert className="h-4 w-4 mr-2" />
                  Trasferisci ownership
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Trasferisci ownership</DialogTitle>
                  <DialogDescription>
                    Trasferisci il ruolo di owner a un altro membro del team.
                    Questa azione e irreversibile.
                  </DialogDescription>
                </DialogHeader>
                <Form {...transferForm}>
                  <form
                    onSubmit={transferForm.handleSubmit(onTransfer)}
                    className="space-y-4"
                  >
                    <FormField
                      control={transferForm.control}
                      name="target_user_id"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Nuovo owner</FormLabel>
                          <Select
                            onValueChange={field.onChange}
                            value={field.value}
                          >
                            <FormControl>
                              <SelectTrigger className="w-full">
                                <SelectValue placeholder="Seleziona membro" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {transferCandidates.map((m) => (
                                <SelectItem key={m.user.id} value={m.user.id}>
                                  {m.user.first_name} {m.user.last_name} (
                                  {m.user.email})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={transferForm.control}
                      name="password"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>La tua password</FormLabel>
                          <FormControl>
                            <Input
                              {...field}
                              type="password"
                              placeholder="Inserisci la tua password per confermare"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <DialogFooter>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setTransferOpen(false)}
                      >
                        Annulla
                      </Button>
                      <Button
                        type="submit"
                        variant="destructive"
                        disabled={transferring}
                      >
                        {transferring ? "Trasferimento..." : "Trasferisci"}
                      </Button>
                    </DialogFooter>
                  </form>
                </Form>
              </DialogContent>
            </Dialog>
          )}
          {canManage && (
            <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <UserPlus className="h-4 w-4 mr-2" />
                  Invita membro
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Invita nuovo membro</DialogTitle>
                  <DialogDescription>
                    Invia un invito via email per aggiungere un nuovo membro al
                    team.
                  </DialogDescription>
                </DialogHeader>
                <Form {...inviteForm}>
                  <form
                    onSubmit={inviteForm.handleSubmit(onInvite)}
                    className="space-y-4"
                  >
                    <FormField
                      control={inviteForm.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email</FormLabel>
                          <FormControl>
                            <Input
                              {...field}
                              type="email"
                              placeholder="email@esempio.it"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={inviteForm.control}
                      name="role"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Ruolo</FormLabel>
                          <Select
                            onValueChange={field.onChange}
                            value={field.value}
                          >
                            <FormControl>
                              <SelectTrigger className="w-full">
                                <SelectValue placeholder="Seleziona ruolo" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="admin">Admin</SelectItem>
                              <SelectItem value="editor">Editor</SelectItem>
                              <SelectItem value="viewer">Viewer</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <DialogFooter>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setInviteOpen(false)}
                      >
                        Annulla
                      </Button>
                      <Button type="submit" disabled={inviting}>
                        {inviting ? "Invio..." : "Invia invito"}
                      </Button>
                    </DialogFooter>
                  </form>
                </Form>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Membri del team</CardTitle>
          <CardDescription>
            {members.length}{" "}
            {members.length === 1 ? "membro" : "membri"} nel team
          </CardDescription>
        </CardHeader>
        <CardContent>
          {members.length === 0 ? (
            <p className="text-muted-foreground text-sm text-center py-8">
              Nessun membro nel team
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Utente</TableHead>
                  <TableHead>Ruolo</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead>Data</TableHead>
                  {canManage && <TableHead className="w-10" />}
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">
                          {member.user.first_name} {member.user.last_name}
                        </p>
                        <p className="text-muted-foreground text-sm">
                          {member.user.email}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={ROLE_VARIANTS[member.role] ?? "outline"}>
                        {ROLE_LABELS[member.role] ?? member.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={STATUS_VARIANTS[member.status] ?? "outline"}
                      >
                        {STATUS_LABELS[member.status] ?? member.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {member.joined_at
                        ? formatDate(member.joined_at)
                        : member.invited_at
                          ? `Invitato il ${formatDate(member.invited_at)}`
                          : formatDate(member.created_at)}
                    </TableCell>
                    {canManage && (
                      <TableCell>
                        {member.role !== "owner" && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() =>
                                  updateMemberRole(member.id, "admin")
                                }
                                disabled={member.role === "admin"}
                              >
                                Imposta Admin
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() =>
                                  updateMemberRole(member.id, "editor")
                                }
                                disabled={member.role === "editor"}
                              >
                                Imposta Editor
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() =>
                                  updateMemberRole(member.id, "viewer")
                                }
                                disabled={member.role === "viewer"}
                              >
                                Imposta Viewer
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => toggleMemberStatus(member)}
                              >
                                {member.status === "suspended"
                                  ? "Riattiva"
                                  : "Sospendi"}
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                variant="destructive"
                                onClick={() => removeMember(member.id)}
                              >
                                Rimuovi
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </TableCell>
                    )}
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
