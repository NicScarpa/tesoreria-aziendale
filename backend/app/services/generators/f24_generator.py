"""
Generatore F24 telematico.

Produce un file di testo in formato record per l'invio telematico del modello F24
(pagamento imposte, contributi, tributi locali).
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.models.company import Company
from app.models.payment_order import PaymentOrder
from app.models.payment_order_line import PaymentOrderLine


def generate_f24(order: PaymentOrder, company: Company) -> str:
    """
    Genera un file F24 telematico in formato record.

    Args:
        order: Ordine di pagamento con righe F24.
        company: Azienda contribuente.

    Returns:
        Stringa di testo in formato F24 telematico.

    Raises:
        ValueError: Se non ci sono righe con stato 'inclusa'.
    """
    included_lines = _get_included_lines(order)
    if not included_lines:
        raise ValueError("Nessuna riga con stato 'inclusa' nell'ordine di pagamento")

    now = datetime.now(timezone.utc)
    cf_contribuente = _get_codice_fiscale(company)

    records: list[str] = []

    # --- Record A (header) ---
    records.append(_build_record_a(
        cf_contribuente=cf_contribuente,
        progressivo_invio=1,
        anno=now.year,
        mese=now.month,
    ))

    # Raggruppa righe per sezione F24
    sezioni = _group_by_sezione(included_lines)

    totale_debiti_cents = 0
    totale_crediti_cents = 0
    num_record_detail = 0

    # --- Record B (Erario) ---
    for line in sezioni.get("erario", []):
        debito_cents = _to_centesimi(line.f24_importo_debito)
        credito_cents = _to_centesimi(line.f24_importo_credito)
        totale_debiti_cents += debito_cents
        totale_crediti_cents += credito_cents
        num_record_detail += 1
        records.append(_build_record_b(
            cf_contribuente=cf_contribuente,
            codice_tributo=line.f24_codice_tributo or "0000",
            rateazione=line.f24_rateazione or "0101",
            anno_riferimento=line.f24_anno_riferimento or now.year,
            importo_debito_cents=debito_cents,
            importo_credito_cents=credito_cents,
        ))

    # --- Record C (INPS) ---
    for line in sezioni.get("inps", []):
        debito_cents = _to_centesimi(line.f24_importo_debito)
        credito_cents = _to_centesimi(line.f24_importo_credito)
        totale_debiti_cents += debito_cents
        totale_crediti_cents += credito_cents
        num_record_detail += 1
        records.append(_build_record_c(
            cf_contribuente=cf_contribuente,
            codice_sede=line.f24_codice_sede or "",
            codice_ente=line.f24_codice_ente or "",
            periodo_da=line.f24_mese_riferimento or 1,
            periodo_a=line.f24_mese_riferimento or 12,
            anno_riferimento=line.f24_anno_riferimento or now.year,
            importo_debito_cents=debito_cents,
            importo_credito_cents=credito_cents,
        ))

    # --- Record D (Regioni) ---
    for line in sezioni.get("regioni", []):
        debito_cents = _to_centesimi(line.f24_importo_debito)
        credito_cents = _to_centesimi(line.f24_importo_credito)
        totale_debiti_cents += debito_cents
        totale_crediti_cents += credito_cents
        num_record_detail += 1
        records.append(_build_record_d(
            cf_contribuente=cf_contribuente,
            codice_regione=line.f24_codice_ente or "00",
            codice_tributo=line.f24_codice_tributo or "0000",
            anno_riferimento=line.f24_anno_riferimento or now.year,
            importo_debito_cents=debito_cents,
            importo_credito_cents=credito_cents,
        ))

    # --- Record E (IMU e altri enti locali) ---
    for line in sezioni.get("imu_altri_enti", []):
        debito_cents = _to_centesimi(line.f24_importo_debito)
        credito_cents = _to_centesimi(line.f24_importo_credito)
        totale_debiti_cents += debito_cents
        totale_crediti_cents += credito_cents
        num_record_detail += 1
        records.append(_build_record_e(
            cf_contribuente=cf_contribuente,
            codice_ente=line.f24_codice_ente or "",
            codice_tributo=line.f24_codice_tributo or "0000",
            anno_riferimento=line.f24_anno_riferimento or now.year,
            importo_debito_cents=debito_cents,
            importo_credito_cents=credito_cents,
        ))

    # --- Record Z (footer) ---
    saldo_cents = totale_debiti_cents - totale_crediti_cents
    # Numero record totali: header (A) + dettaglio + footer (Z)
    num_record_totali = 1 + num_record_detail + 1
    records.append(_build_record_z(
        totale_debiti_cents=totale_debiti_cents,
        totale_crediti_cents=totale_crediti_cents,
        saldo_cents=saldo_cents,
        num_record=num_record_totali,
    ))

    return "\n".join(records) + "\n"


# ---------------------------------------------------------------------------
# Costruzione record
# ---------------------------------------------------------------------------

def _build_record_a(
    cf_contribuente: str,
    progressivo_invio: int,
    anno: int,
    mese: int,
) -> str:
    """Record A (header): tipo, CF contribuente, progressivo, anno/mese."""
    return (
        f"A"
        f"|{cf_contribuente.ljust(16)}"
        f"|{str(progressivo_invio).rjust(5, '0')}"
        f"|{str(anno).rjust(4, '0')}"
        f"|{str(mese).rjust(2, '0')}"
    )


def _build_record_b(
    cf_contribuente: str,
    codice_tributo: str,
    rateazione: str,
    anno_riferimento: int,
    importo_debito_cents: int,
    importo_credito_cents: int,
) -> str:
    """Record B (Erario): codice tributo, rateazione, anno, importi."""
    return (
        f"B"
        f"|{cf_contribuente.ljust(16)}"
        f"|{codice_tributo.ljust(4)}"
        f"|{rateazione.ljust(4)}"
        f"|{str(anno_riferimento).rjust(4, '0')}"
        f"|{str(importo_debito_cents).rjust(15, '0')}"
        f"|{str(importo_credito_cents).rjust(15, '0')}"
    )


def _build_record_c(
    cf_contribuente: str,
    codice_sede: str,
    codice_ente: str,
    periodo_da: int,
    periodo_a: int,
    anno_riferimento: int,
    importo_debito_cents: int,
    importo_credito_cents: int,
) -> str:
    """Record C (INPS): sede, ente, periodo, anno, importi."""
    return (
        f"C"
        f"|{cf_contribuente.ljust(16)}"
        f"|{codice_sede.ljust(4)}"
        f"|{codice_ente.ljust(10)}"
        f"|{str(periodo_da).rjust(2, '0')}"
        f"|{str(periodo_a).rjust(2, '0')}"
        f"|{str(anno_riferimento).rjust(4, '0')}"
        f"|{str(importo_debito_cents).rjust(15, '0')}"
        f"|{str(importo_credito_cents).rjust(15, '0')}"
    )


def _build_record_d(
    cf_contribuente: str,
    codice_regione: str,
    codice_tributo: str,
    anno_riferimento: int,
    importo_debito_cents: int,
    importo_credito_cents: int,
) -> str:
    """Record D (Regioni): codice regione, tributo, anno, importi."""
    return (
        f"D"
        f"|{cf_contribuente.ljust(16)}"
        f"|{codice_regione.ljust(2)}"
        f"|{codice_tributo.ljust(4)}"
        f"|{str(anno_riferimento).rjust(4, '0')}"
        f"|{str(importo_debito_cents).rjust(15, '0')}"
        f"|{str(importo_credito_cents).rjust(15, '0')}"
    )


def _build_record_e(
    cf_contribuente: str,
    codice_ente: str,
    codice_tributo: str,
    anno_riferimento: int,
    importo_debito_cents: int,
    importo_credito_cents: int,
) -> str:
    """Record E (IMU/altri enti): codice ente, tributo, anno, importi."""
    return (
        f"E"
        f"|{cf_contribuente.ljust(16)}"
        f"|{codice_ente.ljust(10)}"
        f"|{codice_tributo.ljust(4)}"
        f"|{str(anno_riferimento).rjust(4, '0')}"
        f"|{str(importo_debito_cents).rjust(15, '0')}"
        f"|{str(importo_credito_cents).rjust(15, '0')}"
    )


def _build_record_z(
    totale_debiti_cents: int,
    totale_crediti_cents: int,
    saldo_cents: int,
    num_record: int,
) -> str:
    """Record Z (footer): totali debiti, crediti, saldo, numero record."""
    return (
        f"Z"
        f"|{str(totale_debiti_cents).rjust(15, '0')}"
        f"|{str(totale_crediti_cents).rjust(15, '0')}"
        f"|{str(abs(saldo_cents)).rjust(15, '0')}"
        f"|{'+' if saldo_cents >= 0 else '-'}"
        f"|{str(num_record).rjust(5, '0')}"
    )


# ---------------------------------------------------------------------------
# Funzioni helper
# ---------------------------------------------------------------------------

def _get_included_lines(order: PaymentOrder) -> list[PaymentOrderLine]:
    """Filtra le righe con stato 'inclusa'."""
    result = []
    for line in order.lines:
        stato_value = line.stato
        if hasattr(stato_value, "value"):
            stato_value = stato_value.value
        if str(stato_value) == "inclusa":
            result.append(line)
    return result


def _get_codice_fiscale(company: Company) -> str:
    """Recupera il codice fiscale del contribuente (tax_number o vat_number)."""
    cf = company.tax_number or company.vat_number or ""
    # Rimuovi prefisso paese se presente (es. "IT01234567890" -> "01234567890")
    if len(cf) > 2 and cf[:2].isalpha():
        cf = cf[2:]
    return cf[:16]


def _group_by_sezione(lines: list[PaymentOrderLine]) -> dict[str, list[PaymentOrderLine]]:
    """Raggruppa le righe per sezione F24."""
    result: dict[str, list[PaymentOrderLine]] = {}
    for line in lines:
        sezione = line.f24_sezione
        if sezione is None:
            # Righe senza sezione F24: default a erario
            sezione_key = "erario"
        else:
            sezione_value = sezione
            if hasattr(sezione_value, "value"):
                sezione_value = sezione_value.value
            sezione_key = str(sezione_value)

        if sezione_key not in result:
            result[sezione_key] = []
        result[sezione_key].append(line)
    return result


def _to_centesimi(amount: Decimal | None) -> int:
    """Converte un importo Decimal in centesimi. None -> 0."""
    if amount is None:
        return 0
    return int(amount * 100)
