"""Invoice import and elaboration service."""
import logging
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.enums import (
    DocumentType, InvoiceBatchSource, InvoiceBatchStatus,
    InvoiceDocumentType, InvoiceSource, InvoiceStatus,
    ScheduleSource, ScheduleStatus, ScheduleType,
)
from app.models.invoice_import import InvoiceImport
from app.models.invoice_import_batch import InvoiceImportBatch
from app.models.schedule import Schedule
from app.services.parsers.fatturapa_parser import parse as parse_fatturapa
from app.services.schedule_expected_service import create_expected_from_schedule

logger = logging.getLogger(__name__)

UPLOAD_BASE = Path("uploads/invoices")

# Mapping InvoiceDocumentType -> (ScheduleType, DocumentType)
_INVOICE_TO_SCHEDULE_MAP = {
    InvoiceDocumentType.FATTURA_ACQUISTO: (ScheduleType.PASSIVA, DocumentType.FATTURA_ACQUISTO),
    InvoiceDocumentType.FATTURA_VENDITA: (ScheduleType.ATTIVA, DocumentType.FATTURA_VENDITA),
    InvoiceDocumentType.NOTA_CREDITO_VENDITA: (ScheduleType.PASSIVA, DocumentType.NOTA_CREDITO),
    InvoiceDocumentType.NOTA_CREDITO_ACQUISTO: (ScheduleType.ATTIVA, DocumentType.NOTA_CREDITO),
    InvoiceDocumentType.AUTOFATTURA: (ScheduleType.PASSIVA, DocumentType.ALTRO),
}


def _determine_invoice_type(parsed, company_piva: str = "") -> InvoiceDocumentType:
    """Determine if invoice is purchase or sale based on cedente/cessionario vs company."""
    tipo = parsed.tipo_documento_tipo
    codice = parsed.tipo_documento_codice

    if tipo == "autofattura":
        return InvoiceDocumentType.AUTOFATTURA

    is_company_cedente = company_piva and parsed.cedente_piva == company_piva

    if tipo == "nota_credito":
        return InvoiceDocumentType.NOTA_CREDITO_VENDITA if is_company_cedente else InvoiceDocumentType.NOTA_CREDITO_ACQUISTO

    # fattura
    return InvoiceDocumentType.FATTURA_VENDITA if is_company_cedente else InvoiceDocumentType.FATTURA_ACQUISTO


def _save_file(company_id: uuid.UUID, filename: str, content: bytes) -> str:
    """Save file and return relative path."""
    now = datetime.now(timezone.utc)
    dir_path = UPLOAD_BASE / str(company_id) / str(now.year) / f"{now.month:02d}"
    dir_path.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    file_path = dir_path / unique_name
    file_path.write_bytes(content)
    return str(file_path)


def import_single_with_source(
    db: Session, company_id: uuid.UUID, user_id: uuid.UUID,
    file_bytes: bytes, filename: str,
    fonte: InvoiceSource,
    batch_id: uuid.UUID | None = None,
    company_piva: str = "",
) -> tuple[InvoiceImport, bool]:
    """
    Import a single FatturaPA XML/P7M file with a specific source (e.g. AdE/Cassetto).

    This mirrors `upload_single` but lets callers set `fonte`.
    """
    parsed_list = parse_fatturapa(file_bytes, filename)

    if not parsed_list:
        inv = InvoiceImport(
            company_id=company_id,
            batch_id=batch_id,
            fonte=fonte,
            tipo_documento=InvoiceDocumentType.FATTURA_ACQUISTO,
            stato=InvoiceStatus.ERRORE,
            xml_file_nome=filename,
            errore_dettaglio="Nessuna fattura trovata nel file XML",
        )
        db.add(inv)
        db.flush()
        return inv, True

    # Process first body (most common case)
    parsed = parsed_list[0]
    tipo_doc = _determine_invoice_type(parsed, company_piva)

    # Dedup check
    existing = None
    if parsed.identificativo_sdi:
        existing = db.query(InvoiceImport).filter(
            InvoiceImport.identificativo_sdi == parsed.identificativo_sdi,
        ).first()

    if not existing and parsed.numero_fattura and parsed.cedente_piva:
        existing = db.query(InvoiceImport).filter(
            InvoiceImport.numero_fattura == parsed.numero_fattura,
            InvoiceImport.cedente_piva == parsed.cedente_piva,
            InvoiceImport.company_id == company_id,
        ).first()

    if existing:
        return existing, False

    # Save XML (only if new)
    xml_path = _save_file(company_id, filename, file_bytes)

    # Save PDF if present
    pdf_path = None
    if parsed.pdf_allegato_base64:
        import base64
        try:
            pdf_bytes = base64.b64decode(parsed.pdf_allegato_base64)
            pdf_name = parsed.pdf_allegato_nome or f"{filename}.pdf"
            pdf_path = _save_file(company_id, pdf_name, pdf_bytes)
        except Exception as e:
            logger.warning(f"Failed to save PDF attachment: {e}")

    inv = InvoiceImport(
        company_id=company_id,
        batch_id=batch_id,
        fonte=fonte,
        tipo_documento=tipo_doc,
        stato=InvoiceStatus.IMPORTATA,
        numero_fattura=parsed.numero_fattura,
        data_fattura=parsed.data_fattura,
        cedente_denominazione=parsed.cedente_denominazione,
        cedente_piva=parsed.cedente_piva,
        cedente_cf=parsed.cedente_cf,
        cessionario_denominazione=parsed.cessionario_denominazione,
        cessionario_piva=parsed.cessionario_piva,
        importo_totale=parsed.importo_totale,
        imponibile_totale=parsed.imponibile_totale,
        iva_totale=parsed.iva_totale,
        valuta=parsed.valuta,
        condizioni_pagamento=parsed.condizioni_pagamento,
        modalita_pagamento=parsed.modalita_pagamento,
        data_scadenza_pagamento=parsed.data_scadenza_pagamento,
        iban_pagamento=parsed.iban_pagamento,
        xml_file_path=xml_path,
        xml_file_nome=filename,
        pdf_allegato_path=pdf_path,
        identificativo_sdi=parsed.identificativo_sdi or None,
        metadata_extra={
            "tipo_documento_codice": parsed.tipo_documento_codice,
            "linee_dettaglio": parsed.linee_dettaglio,
            "riepilogo_iva": parsed.riepilogo_iva,
        },
    )
    db.add(inv)
    db.flush()
    return inv, True


def upload_single(
    db: Session, company_id: uuid.UUID, user_id: uuid.UUID,
    file_bytes: bytes, filename: str,
    batch_id: uuid.UUID | None = None,
    company_piva: str = "",
) -> InvoiceImport:
    """Parse and import a single FatturaPA XML/P7M file."""
    parsed_list = parse_fatturapa(file_bytes, filename)

    if not parsed_list:
        inv = InvoiceImport(
            company_id=company_id,
            batch_id=batch_id,
            fonte=InvoiceSource.UPLOAD_XML,
            tipo_documento=InvoiceDocumentType.FATTURA_ACQUISTO,
            stato=InvoiceStatus.ERRORE,
            xml_file_nome=filename,
            errore_dettaglio="Nessuna fattura trovata nel file XML",
        )
        db.add(inv)
        db.flush()
        return inv

    # Save XML
    xml_path = _save_file(company_id, filename, file_bytes)

    # Process first body (most common case)
    parsed = parsed_list[0]
    tipo_doc = _determine_invoice_type(parsed, company_piva)

    # Dedup check
    existing = None
    if parsed.identificativo_sdi:
        existing = db.query(InvoiceImport).filter(
            InvoiceImport.identificativo_sdi == parsed.identificativo_sdi,
        ).first()

    if not existing and parsed.numero_fattura and parsed.cedente_piva:
        existing = db.query(InvoiceImport).filter(
            InvoiceImport.numero_fattura == parsed.numero_fattura,
            InvoiceImport.cedente_piva == parsed.cedente_piva,
            InvoiceImport.company_id == company_id,
        ).first()

    if existing:
        return existing  # Return existing, caller handles duplicate tracking

    # Save PDF if present
    pdf_path = None
    if parsed.pdf_allegato_base64:
        import base64
        try:
            pdf_bytes = base64.b64decode(parsed.pdf_allegato_base64)
            pdf_name = parsed.pdf_allegato_nome or f"{filename}.pdf"
            pdf_path = _save_file(company_id, pdf_name, pdf_bytes)
        except Exception as e:
            logger.warning(f"Failed to save PDF attachment: {e}")

    inv = InvoiceImport(
        company_id=company_id,
        batch_id=batch_id,
        fonte=InvoiceSource.UPLOAD_XML,
        tipo_documento=tipo_doc,
        stato=InvoiceStatus.IMPORTATA,
        numero_fattura=parsed.numero_fattura,
        data_fattura=parsed.data_fattura,
        cedente_denominazione=parsed.cedente_denominazione,
        cedente_piva=parsed.cedente_piva,
        cedente_cf=parsed.cedente_cf,
        cessionario_denominazione=parsed.cessionario_denominazione,
        cessionario_piva=parsed.cessionario_piva,
        importo_totale=parsed.importo_totale,
        imponibile_totale=parsed.imponibile_totale,
        iva_totale=parsed.iva_totale,
        valuta=parsed.valuta,
        condizioni_pagamento=parsed.condizioni_pagamento,
        modalita_pagamento=parsed.modalita_pagamento,
        data_scadenza_pagamento=parsed.data_scadenza_pagamento,
        iban_pagamento=parsed.iban_pagamento,
        xml_file_path=xml_path,
        xml_file_nome=filename,
        pdf_allegato_path=pdf_path,
        identificativo_sdi=parsed.identificativo_sdi or None,
        metadata_extra={
            "tipo_documento_codice": parsed.tipo_documento_codice,
            "linee_dettaglio": parsed.linee_dettaglio,
            "riepilogo_iva": parsed.riepilogo_iva,
        },
    )
    db.add(inv)
    db.flush()
    return inv


def upload_batch(
    db: Session, company_id: uuid.UUID, user_id: uuid.UUID,
    files: list[tuple[bytes, str]],
    company_piva: str = "",
) -> InvoiceImportBatch:
    """Import multiple invoice files."""
    batch = InvoiceImportBatch(
        company_id=company_id,
        fonte=InvoiceBatchSource.UPLOAD_MULTIPLO,
        totale_fatture=len(files),
        importato_da_user_id=user_id,
    )
    db.add(batch)
    db.flush()

    imported = 0
    errors = 0
    duplicates = 0

    for file_bytes, filename in files:
        try:
            result = upload_single(db, company_id, user_id, file_bytes, filename, batch.id, company_piva)
            if result.stato == InvoiceStatus.ERRORE:
                errors += 1
            elif result.batch_id != batch.id:
                # Was existing (duplicate)
                duplicates += 1
            else:
                imported += 1
        except Exception as e:
            logger.error(f"Error importing {filename}: {e}")
            errors += 1

    batch.fatture_importate = imported
    batch.fatture_errore = errors
    batch.fatture_duplicate = duplicates

    if errors == 0:
        batch.stato = InvoiceBatchStatus.COMPLETATO
    elif imported > 0:
        batch.stato = InvoiceBatchStatus.COMPLETATO_CON_ERRORI
    else:
        batch.stato = InvoiceBatchStatus.FALLITO

    db.flush()
    db.commit()
    db.refresh(batch)
    return batch


EMESSE_TYPES = [
    InvoiceDocumentType.FATTURA_VENDITA,
    InvoiceDocumentType.NOTA_CREDITO_VENDITA,
]
RICEVUTE_TYPES = [
    InvoiceDocumentType.FATTURA_ACQUISTO,
    InvoiceDocumentType.NOTA_CREDITO_ACQUISTO,
    InvoiceDocumentType.AUTOFATTURA,
]


def list_invoices(
    db: Session, company_id: uuid.UUID,
    tipo_documento: str | None = None,
    stato: str | None = None,
    data_da: date | None = None,
    data_a: date | None = None,
    cedente_piva: str | None = None,
    search: str | None = None,
    importo_min: float | None = None,
    importo_max: float | None = None,
    direction: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[InvoiceImport], int]:
    q = db.query(InvoiceImport).filter(InvoiceImport.company_id == company_id)

    if direction == "emesse":
        q = q.filter(InvoiceImport.tipo_documento.in_(EMESSE_TYPES))
    elif direction == "ricevute":
        q = q.filter(InvoiceImport.tipo_documento.in_(RICEVUTE_TYPES))

    if tipo_documento:
        q = q.filter(InvoiceImport.tipo_documento == tipo_documento)
    if stato:
        q = q.filter(InvoiceImport.stato == stato)
    if data_da:
        q = q.filter(InvoiceImport.data_fattura >= data_da)
    if data_a:
        q = q.filter(InvoiceImport.data_fattura <= data_a)
    if cedente_piva:
        q = q.filter(InvoiceImport.cedente_piva == cedente_piva)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            (InvoiceImport.cedente_denominazione.ilike(pattern))
            | (InvoiceImport.numero_fattura.ilike(pattern))
            | (InvoiceImport.cessionario_denominazione.ilike(pattern))
        )
    if importo_min is not None:
        q = q.filter(InvoiceImport.importo_totale >= Decimal(str(importo_min)))
    if importo_max is not None:
        q = q.filter(InvoiceImport.importo_totale <= Decimal(str(importo_max)))

    q = q.order_by(InvoiceImport.data_fattura.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_invoice(db: Session, invoice_id: uuid.UUID, company_id: uuid.UUID) -> InvoiceImport | None:
    return db.query(InvoiceImport).filter(
        InvoiceImport.id == invoice_id,
        InvoiceImport.company_id == company_id,
    ).first()


def elaborate(
    db: Session, invoice_id: uuid.UUID, company_id: uuid.UUID, user_id: uuid.UUID,
) -> dict:
    """Elaborate an invoice: create a Schedule + ExpectedTransaction."""
    inv = get_invoice(db, invoice_id, company_id)
    if not inv:
        raise ValueError("Fattura non trovata")

    if inv.stato not in (InvoiceStatus.IMPORTATA, InvoiceStatus.ELABORATA):
        raise ValueError(f"Fattura non elaborabile (stato: {inv.stato.value})")

    mapping = _INVOICE_TO_SCHEDULE_MAP.get(inv.tipo_documento)
    if not mapping:
        raise ValueError(f"Tipo documento non mappabile: {inv.tipo_documento.value}")

    schedule_type, doc_type = mapping

    data_scadenza = inv.data_scadenza_pagamento or (
        (inv.data_fattura + timedelta(days=30)) if inv.data_fattura else date.today() + timedelta(days=30)
    )

    importo = abs(inv.importo_totale) if inv.importo_totale else Decimal("0")

    schedule = Schedule(
        company_id=company_id,
        tipo=schedule_type,
        stato=ScheduleStatus.APERTA,
        descrizione=f"Fattura {inv.numero_fattura or ''} - {inv.cedente_denominazione or inv.cessionario_denominazione or ''}".strip(" -"),
        importo_totale=importo,
        valuta=inv.valuta,
        data_scadenza=data_scadenza,
        data_emissione=inv.data_fattura,
        tipo_documento=doc_type,
        numero_documento=inv.numero_fattura,
        controparte_nome=inv.cedente_denominazione if schedule_type == ScheduleType.PASSIVA else inv.cessionario_denominazione,
        controparte_iban=inv.iban_pagamento,
        source=ScheduleSource.IMPORT_FATTURE_SDI,
        created_by_user_id=user_id,
    )
    db.add(schedule)
    db.flush()

    # Create ExpectedTransaction
    et = create_expected_from_schedule(db, schedule)

    # Update invoice
    inv.stato = InvoiceStatus.SCADENZA_CREATA
    inv.schedule_id = schedule.id
    inv.expected_transaction_id = et.id
    inv.elaborato_da_user_id = user_id
    inv.data_elaborazione = datetime.now(timezone.utc)

    db.flush()
    db.commit()

    return {
        "invoice_id": str(inv.id),
        "schedule_id": str(schedule.id),
        "expected_transaction_id": str(et.id),
        "message": f"Scadenza creata per fattura {inv.numero_fattura}",
    }


def elaborate_batch(
    db: Session, company_id: uuid.UUID, user_id: uuid.UUID,
    invoice_ids: list[str] | None = None,
    filter_stato: str | None = None,
) -> list[dict]:
    """Elaborate multiple invoices."""
    if invoice_ids:
        invoices = db.query(InvoiceImport).filter(
            InvoiceImport.id.in_([uuid.UUID(i) for i in invoice_ids]),
            InvoiceImport.company_id == company_id,
        ).all()
    elif filter_stato:
        invoices = db.query(InvoiceImport).filter(
            InvoiceImport.company_id == company_id,
            InvoiceImport.stato == filter_stato,
        ).all()
    else:
        invoices = db.query(InvoiceImport).filter(
            InvoiceImport.company_id == company_id,
            InvoiceImport.stato == InvoiceStatus.IMPORTATA,
        ).all()

    results = []
    for inv in invoices:
        try:
            result = elaborate(db, inv.id, company_id, user_id)
            results.append(result)
        except Exception as e:
            results.append({
                "invoice_id": str(inv.id),
                "error": str(e),
            })

    return results


def ignore(db: Session, invoice_id: uuid.UUID, company_id: uuid.UUID) -> InvoiceImport | None:
    inv = get_invoice(db, invoice_id, company_id)
    if not inv:
        return None
    inv.stato = InvoiceStatus.IGNORATA
    db.flush()
    db.commit()
    db.refresh(inv)
    return inv


def list_batches(
    db: Session, company_id: uuid.UUID, page: int = 1, page_size: int = 20,
) -> tuple[list[InvoiceImportBatch], int]:
    q = db.query(InvoiceImportBatch).filter(
        InvoiceImportBatch.company_id == company_id,
    ).order_by(InvoiceImportBatch.data_import.desc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_batch(db: Session, batch_id: uuid.UUID, company_id: uuid.UUID) -> InvoiceImportBatch | None:
    return db.query(InvoiceImportBatch).filter(
        InvoiceImportBatch.id == batch_id,
        InvoiceImportBatch.company_id == company_id,
    ).first()


def get_invoice_stats(
    db: Session, company_id: uuid.UUID,
    anno: int | None = None,
    mese: int | None = None,
) -> dict:
    """Return aggregated invoice statistics for the company."""
    base = db.query(InvoiceImport).filter(InvoiceImport.company_id == company_id)

    if anno:
        base = base.filter(extract("year", InvoiceImport.data_fattura) == anno)
    if mese:
        base = base.filter(extract("month", InvoiceImport.data_fattura) == mese)

    # --- Emesse ---
    emesse_q = base.filter(InvoiceImport.tipo_documento.in_(EMESSE_TYPES))
    emesse_count = emesse_q.count()

    emesse_agg = db.query(
        func.coalesce(func.sum(InvoiceImport.importo_totale), 0).label("totale"),
        func.coalesce(func.sum(InvoiceImport.imponibile_totale), 0).label("imponibile"),
        func.coalesce(func.sum(InvoiceImport.iva_totale), 0).label("iva"),
    ).filter(
        InvoiceImport.company_id == company_id,
        InvoiceImport.tipo_documento.in_(EMESSE_TYPES),
    )
    if anno:
        emesse_agg = emesse_agg.filter(extract("year", InvoiceImport.data_fattura) == anno)
    if mese:
        emesse_agg = emesse_agg.filter(extract("month", InvoiceImport.data_fattura) == mese)
    emesse_row = emesse_agg.one()
    emesse_totale = float(emesse_row.totale or 0)
    emesse_imponibile = float(emesse_row.imponibile or 0)
    emesse_iva = float(emesse_row.iva or 0)

    # --- Ricevute ---
    ricevute_q = base.filter(InvoiceImport.tipo_documento.in_(RICEVUTE_TYPES))
    ricevute_count = ricevute_q.count()

    ricevute_agg = db.query(
        func.coalesce(func.sum(InvoiceImport.importo_totale), 0).label("totale"),
        func.coalesce(func.sum(InvoiceImport.imponibile_totale), 0).label("imponibile"),
        func.coalesce(func.sum(InvoiceImport.iva_totale), 0).label("iva"),
    ).filter(
        InvoiceImport.company_id == company_id,
        InvoiceImport.tipo_documento.in_(RICEVUTE_TYPES),
    )
    if anno:
        ricevute_agg = ricevute_agg.filter(extract("year", InvoiceImport.data_fattura) == anno)
    if mese:
        ricevute_agg = ricevute_agg.filter(extract("month", InvoiceImport.data_fattura) == mese)
    ricevute_row = ricevute_agg.one()
    ricevute_totale = float(ricevute_row.totale or 0)
    ricevute_imponibile = float(ricevute_row.imponibile or 0)
    ricevute_iva = float(ricevute_row.iva or 0)

    # --- Da elaborare ---
    da_elaborare = base.filter(InvoiceImport.stato == InvoiceStatus.IMPORTATA).count()

    # --- Per mese (monthly breakdown) ---
    per_mese_raw = (
        db.query(
            extract("year", InvoiceImport.data_fattura).label("anno"),
            extract("month", InvoiceImport.data_fattura).label("mese"),
            InvoiceImport.tipo_documento,
            func.coalesce(func.sum(InvoiceImport.importo_totale), 0).label("totale"),
            func.coalesce(func.sum(InvoiceImport.imponibile_totale), 0).label("imponibile"),
            func.coalesce(func.sum(InvoiceImport.iva_totale), 0).label("iva"),
        )
        .filter(InvoiceImport.company_id == company_id)
    )
    if anno:
        per_mese_raw = per_mese_raw.filter(extract("year", InvoiceImport.data_fattura) == anno)
    if mese:
        per_mese_raw = per_mese_raw.filter(extract("month", InvoiceImport.data_fattura) == mese)

    per_mese_raw = (
        per_mese_raw
        .group_by("anno", "mese", InvoiceImport.tipo_documento)
        .order_by("anno", "mese")
        .all()
    )

    mesi_map: dict[str, dict] = {}
    for row in per_mese_raw:
        key = f"{int(row.anno)}-{int(row.mese):02d}"
        if key not in mesi_map:
            mesi_map[key] = {
                "mese": key, "emesse": 0.0, "ricevute": 0.0,
                "emesse_imponibile": 0.0, "ricevute_imponibile": 0.0,
                "emesse_iva": 0.0, "ricevute_iva": 0.0,
            }
        tipo = InvoiceDocumentType(row.tipo_documento) if isinstance(row.tipo_documento, str) else row.tipo_documento
        if tipo in EMESSE_TYPES:
            mesi_map[key]["emesse"] += float(row.totale or 0)
            mesi_map[key]["emesse_imponibile"] += float(row.imponibile or 0)
            mesi_map[key]["emesse_iva"] += float(row.iva or 0)
        elif tipo in RICEVUTE_TYPES:
            mesi_map[key]["ricevute"] += float(row.totale or 0)
            mesi_map[key]["ricevute_imponibile"] += float(row.imponibile or 0)
            mesi_map[key]["ricevute_iva"] += float(row.iva or 0)

    per_mese = list(mesi_map.values())

    # --- Top clienti (from emesse, group by cessionario) ---
    top_clienti_raw = (
        db.query(
            InvoiceImport.cessionario_denominazione.label("nome"),
            func.coalesce(func.sum(InvoiceImport.importo_totale), 0).label("totale"),
            func.coalesce(func.sum(InvoiceImport.imponibile_totale), 0).label("imponibile"),
            func.count(InvoiceImport.id).label("documenti"),
        )
        .filter(
            InvoiceImport.company_id == company_id,
            InvoiceImport.tipo_documento.in_(EMESSE_TYPES),
            InvoiceImport.cessionario_denominazione.isnot(None),
        )
    )
    if anno:
        top_clienti_raw = top_clienti_raw.filter(extract("year", InvoiceImport.data_fattura) == anno)
    if mese:
        top_clienti_raw = top_clienti_raw.filter(extract("month", InvoiceImport.data_fattura) == mese)

    top_clienti_raw = (
        top_clienti_raw
        .group_by(InvoiceImport.cessionario_denominazione)
        .order_by(func.sum(InvoiceImport.imponibile_totale).desc())
        .limit(10)
        .all()
    )

    top_clienti = []
    for row in top_clienti_raw:
        imp = float(row.imponibile or 0)
        top_clienti.append({
            "nome": row.nome or "N/D",
            "totale": float(row.totale or 0),
            "imponibile": imp,
            "documenti": row.documenti,
            "percentuale": round((imp / emesse_imponibile * 100) if emesse_imponibile > 0 else 0, 2),
        })

    # --- Top fornitori (from ricevute, group by cedente) ---
    top_fornitori_raw = (
        db.query(
            InvoiceImport.cedente_denominazione.label("nome"),
            func.coalesce(func.sum(InvoiceImport.importo_totale), 0).label("totale"),
            func.coalesce(func.sum(InvoiceImport.imponibile_totale), 0).label("imponibile"),
            func.count(InvoiceImport.id).label("documenti"),
        )
        .filter(
            InvoiceImport.company_id == company_id,
            InvoiceImport.tipo_documento.in_(RICEVUTE_TYPES),
            InvoiceImport.cedente_denominazione.isnot(None),
        )
    )
    if anno:
        top_fornitori_raw = top_fornitori_raw.filter(extract("year", InvoiceImport.data_fattura) == anno)
    if mese:
        top_fornitori_raw = top_fornitori_raw.filter(extract("month", InvoiceImport.data_fattura) == mese)

    top_fornitori_raw = (
        top_fornitori_raw
        .group_by(InvoiceImport.cedente_denominazione)
        .order_by(func.sum(InvoiceImport.imponibile_totale).desc())
        .limit(10)
        .all()
    )

    top_fornitori = []
    for row in top_fornitori_raw:
        imp = float(row.imponibile or 0)
        top_fornitori.append({
            "nome": row.nome or "N/D",
            "totale": float(row.totale or 0),
            "imponibile": imp,
            "documenti": row.documenti,
            "percentuale": round((imp / ricevute_imponibile * 100) if ricevute_imponibile > 0 else 0, 2),
        })

    return {
        "emesse_count": emesse_count,
        "emesse_totale": emesse_totale,
        "ricevute_count": ricevute_count,
        "ricevute_totale": ricevute_totale,
        "emesse_imponibile": emesse_imponibile,
        "ricevute_imponibile": ricevute_imponibile,
        "emesse_iva": emesse_iva,
        "ricevute_iva": ricevute_iva,
        "da_elaborare": da_elaborare,
        "per_mese": per_mese,
        "top_clienti": top_clienti,
        "top_fornitori": top_fornitori,
    }
