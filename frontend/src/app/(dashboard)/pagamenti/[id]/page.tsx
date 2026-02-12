"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Send,
  CheckCircle2,
  XCircle,
  FileOutput,
  Download,
  Truck,
  CircleCheck,
  Pencil,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import {
  getPaymentOrder,
  getApprovals,
  submitOrder,
  approveOrder,
  rejectOrder,
  generateFile,
  downloadFile,
  markSent,
  markExecuted,
  deletePaymentOrder,
} from "@/lib/api/payments";
import type {
  PaymentOrder,
  PaymentApproval,
  PaymentOrderStatus,
} from "@/types/payment";
import {
  PAYMENT_ORDER_TYPE_LABELS,
  PAYMENT_ORDER_STATUS_LABELS,
  PAYMENT_PRIORITY_LABELS,
} from "@/types/payment";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { PaymentStatusBadge } from "@/components/payments/PaymentStatusBadge";
import { PaymentWorkflowBar } from "@/components/payments/PaymentWorkflowBar";
import { PaymentLineTable } from "@/components/payments/PaymentLineTable";
import { PaymentApprovalHistory } from "@/components/payments/PaymentApprovalHistory";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "\u2014";
  return new Date(dateStr).toLocaleDateString("it-IT");
}

export default function DettaglioPagamentoPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.id as string;

  // Data
  const [order, setOrder] = useState<PaymentOrder | null>(null);
  const [approvals, setApprovals] = useState<PaymentApproval[]>([]);
  const [loading, setLoading] = useState(true);

  // Reject dialog
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectComment, setRejectComment] = useState("");
  const [rejectSubmitting, setRejectSubmitting] = useState(false);

  // Action loading
  const [actionLoading, setActionLoading] = useState(false);

  const loadOrder = useCallback(async () => {
    try {
      const [orderData, approvalsData] = await Promise.all([
        getPaymentOrder(orderId),
        getApprovals(orderId),
      ]);
      setOrder(orderData);
      setApprovals(approvalsData);
    } catch {
      toast.error("Ordine di pagamento non trovato");
      router.push("/pagamenti");
    } finally {
      setLoading(false);
    }
  }, [orderId, router]);

  useEffect(() => {
    loadOrder();
  }, [loadOrder]);

  // --- Action handlers ---

  const handleSubmit = async () => {
    setActionLoading(true);
    try {
      const updated = await submitOrder(orderId);
      setOrder(updated);
      toast.success("Ordine inviato per approvazione");
      loadOrder();
    } catch {
      toast.error("Errore nell'invio per approvazione");
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprove = async () => {
    setActionLoading(true);
    try {
      const updated = await approveOrder(orderId);
      setOrder(updated);
      toast.success("Ordine approvato");
      loadOrder();
    } catch {
      toast.error("Errore nell'approvazione");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!rejectComment.trim()) {
      toast.error("Il commento e' obbligatorio per il rifiuto");
      return;
    }
    setRejectSubmitting(true);
    try {
      const updated = await rejectOrder(orderId, rejectComment.trim());
      setOrder(updated);
      setRejectOpen(false);
      setRejectComment("");
      toast.success("Ordine rifiutato");
      loadOrder();
    } catch {
      toast.error("Errore nel rifiuto");
    } finally {
      setRejectSubmitting(false);
    }
  };

  const handleGenerateFile = async () => {
    setActionLoading(true);
    try {
      const updated = await generateFile(orderId);
      setOrder(updated);
      toast.success("File generato con successo");
    } catch {
      toast.error("Errore nella generazione del file");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownloadFile = async () => {
    try {
      const blob = await downloadFile(orderId);
      const url = URL.createObjectURL(blob as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = order?.file_generato_nome || "pagamento.xml";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Errore nel download del file");
    }
  };

  const handleMarkSent = async () => {
    setActionLoading(true);
    try {
      const updated = await markSent(orderId);
      setOrder(updated);
      toast.success("Ordine segnato come inviato alla banca");
    } catch {
      toast.error("Errore nell'aggiornamento dello stato");
    } finally {
      setActionLoading(false);
    }
  };

  const handleMarkExecuted = async () => {
    setActionLoading(true);
    try {
      const updated = await markExecuted(orderId);
      setOrder(updated);
      toast.success("Ordine segnato come eseguito");
    } catch {
      toast.error("Errore nell'aggiornamento dello stato");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Sei sicuro di voler eliminare questo ordine di pagamento?")) return;
    setActionLoading(true);
    try {
      await deletePaymentOrder(orderId);
      toast.success("Ordine di pagamento eliminato");
      router.push("/pagamenti");
    } catch {
      toast.error("Errore nell'eliminazione");
    } finally {
      setActionLoading(false);
    }
  };

  // --- Render actions based on status ---

  function renderActions(status: PaymentOrderStatus) {
    const disabled = actionLoading;

    switch (status) {
      case "bozza":
        return (
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleSubmit} disabled={disabled}>
              <Send className="h-4 w-4 mr-2" />
              Invia per Approvazione
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push(`/pagamenti/${orderId}`)}
              disabled={disabled}
            >
              <Pencil className="h-4 w-4 mr-2" />
              Modifica
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={disabled}>
              <Trash2 className="h-4 w-4 mr-2" />
              Elimina
            </Button>
          </div>
        );

      case "da_approvare":
        return (
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleApprove} disabled={disabled}>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Approva
            </Button>
            <Button
              variant="destructive"
              onClick={() => setRejectOpen(true)}
              disabled={disabled}
            >
              <XCircle className="h-4 w-4 mr-2" />
              Rifiuta
            </Button>
          </div>
        );

      case "approvata":
        return (
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleGenerateFile} disabled={disabled}>
              <FileOutput className="h-4 w-4 mr-2" />
              Genera File
            </Button>
          </div>
        );

      case "file_generato":
        return (
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={handleDownloadFile}>
              <Download className="h-4 w-4 mr-2" />
              Scarica File
            </Button>
            <Button onClick={handleMarkSent} disabled={disabled}>
              <Truck className="h-4 w-4 mr-2" />
              Segna Inviato
            </Button>
          </div>
        );

      case "inviata_banca":
        return (
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleMarkExecuted} disabled={disabled}>
              <CircleCheck className="h-4 w-4 mr-2" />
              Segna Eseguito
            </Button>
          </div>
        );

      default:
        return null;
    }
  }

  if (loading) return <LoadingState />;
  if (!order) return null;

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/pagamenti")}>
          <ArrowLeft className="h-4 w-4 mr-1" />
          Pagamenti
        </Button>
      </div>

      {/* Page header */}
      <PageHeader
        title={
          <span className="flex items-center gap-3">
            {order.riferimento_interno}
            <PaymentStatusBadge stato={order.stato} />
          </span>
        }
        description={`${PAYMENT_ORDER_TYPE_LABELS[order.tipo]} \u2014 ${formatDate(order.data_esecuzione_richiesta)}`}
      />

      {/* Workflow bar */}
      <PaymentWorkflowBar stato={order.stato} />

      {/* Info cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Tipo</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">{PAYMENT_ORDER_TYPE_LABELS[order.tipo]}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Importo Totale</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-bold font-mono">{formatCurrency(order.importo_totale)}</p>
            <p className="text-xs text-muted-foreground">
              {order.numero_disposizioni} disposizion{order.numero_disposizioni === 1 ? "e" : "i"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Data Esecuzione</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">{formatDate(order.data_esecuzione_richiesta)}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Priorita</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">{PAYMENT_PRIORITY_LABELS[order.priorita]}</p>
          </CardContent>
        </Card>
      </div>

      {/* Additional info */}
      <Card>
        <CardHeader>
          <CardTitle>Informazioni aggiuntive</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-muted-foreground">Conto bancario</dt>
              <dd>{order.bank_account_nickname || "\u2014"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Valuta</dt>
              <dd>{order.valuta}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Creato da</dt>
              <dd>{order.creato_da_user_name || "\u2014"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Data creazione</dt>
              <dd>{formatDate(order.created_at)}</dd>
            </div>
            {order.data_approvazione && (
              <div>
                <dt className="text-muted-foreground">Data approvazione</dt>
                <dd>{formatDate(order.data_approvazione)}</dd>
              </div>
            )}
            {order.file_generato_nome && (
              <div>
                <dt className="text-muted-foreground">File generato</dt>
                <dd className="font-mono text-xs">{order.file_generato_nome}</dd>
              </div>
            )}
            {order.file_generato_at && (
              <div>
                <dt className="text-muted-foreground">Data generazione file</dt>
                <dd>{formatDate(order.file_generato_at)}</dd>
              </div>
            )}
            {order.note && (
              <div className="col-span-2">
                <dt className="text-muted-foreground">Note</dt>
                <dd className="whitespace-pre-wrap">{order.note}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* Payment lines */}
      <Card>
        <CardHeader>
          <CardTitle>Disposizioni ({order.lines.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <PaymentLineTable lines={order.lines} />
        </CardContent>
      </Card>

      {/* Approval history */}
      {approvals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Storico approvazioni</CardTitle>
          </CardHeader>
          <CardContent>
            <PaymentApprovalHistory approvals={approvals} />
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex justify-end">
        {renderActions(order.stato)}
      </div>

      {/* Reject dialog */}
      <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rifiuta ordine di pagamento</DialogTitle>
            <DialogDescription>
              Inserisci un commento obbligatorio per motivare il rifiuto.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="reject-comment">Commento</Label>
              <Textarea
                id="reject-comment"
                placeholder="Motivazione del rifiuto..."
                value={rejectComment}
                onChange={(e) => setRejectComment(e.target.value)}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectOpen(false)}>
              Annulla
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={rejectSubmitting || !rejectComment.trim()}
            >
              {rejectSubmitting ? "Invio..." : "Conferma Rifiuto"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
