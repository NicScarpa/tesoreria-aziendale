"use client";

import { InvoiceListPage } from "@/components/fatture/invoice-list-page";

export default function FattureEmessePage() {
  return (
    <InvoiceListPage
      direction="emesse"
      title="Fatture Emesse"
      description="Fatture elettroniche emesse ai clienti"
    />
  );
}
