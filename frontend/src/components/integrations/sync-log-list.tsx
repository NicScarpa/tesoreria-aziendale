"use client";

import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { OpenBankingSyncLog } from "@/types/integration";
import { SYNC_LOG_STATUS_LABELS, SYNC_LOG_STATUS_COLORS } from "@/types/integration";

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

interface Props {
  logs: OpenBankingSyncLog[];
}

export function SyncLogList({ logs }: Props) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Data</TableHead>
          <TableHead>Stato</TableHead>
          <TableHead>Nuovi</TableHead>
          <TableHead>Duplicati</TableHead>
          <TableHead>Durata</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {logs.map((log) => (
          <TableRow key={log.id}>
            <TableCell className="text-xs">{formatDate(log.data_sync)}</TableCell>
            <TableCell>
              <Badge className={SYNC_LOG_STATUS_COLORS[log.stato]}>
                {SYNC_LOG_STATUS_LABELS[log.stato]}
              </Badge>
            </TableCell>
            <TableCell className="text-sm">{log.movimenti_nuovi}</TableCell>
            <TableCell className="text-sm">{log.movimenti_duplicati}</TableCell>
            <TableCell className="text-sm">{log.durata_ms ? `${log.durata_ms}ms` : "\u2014"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
