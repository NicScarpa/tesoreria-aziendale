"use client";

import { InvoiceListPage } from "@/components/fatture/invoice-list-page";

export default function FattureRicevutePage() {
  return (
    <InvoiceListPage
      direction="ricevute"
      title="Fatture Ricevute"
      description="Fatture elettroniche ricevute dai fornitori"
    />
  );
}
