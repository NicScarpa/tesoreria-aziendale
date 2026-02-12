"""
Generatore RiBa (Ricevuta Bancaria) in formato CBI.

Produce file a record fissi (120 caratteri per riga) con codifica ISO-8859-1,
compatibile con il tracciato CBI per la presentazione di Ri.Ba.
"""

import unicodedata
from datetime import date, datetime, timezone
from decimal import Decimal

from app.models.company import Company
from app.models.payment_order import PaymentOrder
from app.models.payment_order_line import PaymentOrderLine

# Lunghezza fissa record CBI
RECORD_LENGTH = 120

# Line ending CBI
LINE_ENDING = "\r\n"

# Tabella translitterazione accenti italiani comuni
_TRANSLITERATION_TABLE = str.maketrans({
    "à": "a", "á": "a", "â": "a", "ã": "a", "ä": "a",
    "è": "e", "é": "e", "ê": "e", "ë": "e",
    "ì": "i", "í": "i", "î": "i", "ï": "i",
    "ò": "o", "ó": "o", "ô": "o", "õ": "o", "ö": "o",
    "ù": "u", "ú": "u", "û": "u", "ü": "u",
    "ñ": "n", "ç": "c",
    "À": "A", "Á": "A", "Â": "A", "Ã": "A", "Ä": "A",
    "È": "E", "É": "E", "Ê": "E", "Ë": "E",
    "Ì": "I", "Í": "I", "Î": "I", "Ï": "I",
    "Ò": "O", "Ó": "O", "Ô": "O", "Õ": "O", "Ö": "O",
    "Ù": "U", "Ú": "U", "Û": "U", "Ü": "U",
    "Ñ": "N", "Ç": "C",
})


def generate_riba(order: PaymentOrder, company: Company) -> bytes:
    """
    Genera un file RiBa CBI.

    Args:
        order: Ordine di pagamento con le relative righe.
        company: Azienda creditrice che emette le Ri.Ba.

    Returns:
        Contenuto del file in bytes (codifica ISO-8859-1, CRLF).

    Raises:
        ValueError: Se non ci sono righe con stato 'inclusa'.
    """
    included_lines = _get_included_lines(order)
    if not included_lines:
        raise ValueError("Nessuna riga con stato 'inclusa' nell'ordine di pagamento")

    records: list[str] = []
    now = datetime.now(timezone.utc)
    creation_date = now.strftime("%d%m%y")
    support_name = f"RIBA{now.strftime('%Y%m%d%H%M')}"[:20]

    # Codice SIA: primi 5 del VAT number o default
    sia_code = (company.vat_number or "00000")[:5].ljust(5)

    # Codice CUC (Codice Univoco CBI) - usa SIA code
    cuc = sia_code

    # ABI/CAB banca assuntrice dall'ordine
    abi_assuntrice = ""
    cab_assuntrice = ""
    if order.bank_account:
        abi_assuntrice = (order.bank_account.bank_abi or "")[:5]
        cab_assuntrice = (order.bank_account.bank_cab or "")[:5]
    abi_assuntrice = abi_assuntrice.ljust(5, "0") if abi_assuntrice else "00000"
    cab_assuntrice = cab_assuntrice.ljust(5, "0") if cab_assuntrice else "00000"

    # --- Record IB (header) ---
    records.append(_build_record_ib(
        sia_code=sia_code,
        abi_assuntrice=abi_assuntrice,
        creation_date=creation_date,
        support_name=support_name,
    ))

    # --- Record per ogni disposizione ---
    total_amount_cents = 0
    progressive = 0

    for line in included_lines:
        progressive += 1
        amount_cents = _to_centesimi(line.importo)
        total_amount_cents += amount_cents

        scadenza = line.riba_data_scadenza or order.data_esecuzione_richiesta
        scadenza_str = scadenza.strftime("%d%m%y")

        abi_domiciliataria = (line.riba_abi_banca_domiciliataria or "00000")[:5].ljust(5, "0")
        cab_domiciliataria = (line.riba_cab_banca_domiciliataria or "00000")[:5].ljust(5, "0")

        cf_debitore = _ascii(line.beneficiario_cf or "")[:16].ljust(16)
        nome_debitore = _ascii(line.beneficiario_nome or "")[:60]
        indirizzo_debitore = _ascii(line.beneficiario_indirizzo or "")[:30]
        causale = _ascii(line.causale or "")[:40]
        nome_creditore = _ascii(company.name or "")[:60]
        indirizzo_creditore = _ascii(company.address or "")[:30]
        numero_ricevuta = (line.riba_numero_ricevuta or str(progressive))[:10]
        piazza = _ascii(line.riba_piazza or "")[:50]

        # Record 14
        records.append(_build_record_14(
            progressive=progressive,
            scadenza=scadenza_str,
            amount_cents=amount_cents,
            abi_assuntrice=abi_assuntrice,
            cab_assuntrice=cab_assuntrice,
            cuc=cuc,
            abi_domiciliataria=abi_domiciliataria,
            cab_domiciliataria=cab_domiciliataria,
        ))

        # Record 20
        records.append(_build_record_20(
            progressive=progressive,
            causale=causale,
            cf_debitore=cf_debitore,
        ))

        # Record 30
        records.append(_build_record_30(
            progressive=progressive,
            nome_creditore=nome_creditore,
            indirizzo_creditore=indirizzo_creditore,
        ))

        # Record 40
        records.append(_build_record_40(
            progressive=progressive,
            abi_domiciliataria=abi_domiciliataria,
            cab_domiciliataria=cab_domiciliataria,
            piazza=piazza,
        ))

        # Record 50
        records.append(_build_record_50(
            progressive=progressive,
            causale=causale,
            nome_debitore=nome_debitore,
        ))

        # Record 51
        records.append(_build_record_51(
            progressive=progressive,
            numero_ricevuta=numero_ricevuta,
            nome_creditore=nome_creditore,
        ))

        # Record 70
        records.append(_build_record_70(progressive=progressive))

    # --- Record EF (footer) ---
    records.append(_build_record_ef(
        sia_code=sia_code,
        abi_assuntrice=abi_assuntrice,
        creation_date=creation_date,
        num_disposizioni=len(included_lines),
        total_amount_cents=total_amount_cents,
        num_records=len(records) + 1,  # +1 per EF stesso
    ))

    content = LINE_ENDING.join(records) + LINE_ENDING
    return content.encode("iso-8859-1", errors="replace")


# ---------------------------------------------------------------------------
# Costruzione record
# ---------------------------------------------------------------------------

def _build_record_ib(
    sia_code: str,
    abi_assuntrice: str,
    creation_date: str,
    support_name: str,
) -> str:
    """Record IB (testa del flusso)."""
    rec = " IB"                              # pos 1-3: spazio + tipo record
    rec += sia_code.ljust(5)                 # pos 4-8: codice SIA mittente
    rec += abi_assuntrice.ljust(5)           # pos 9-13: ABI banca assuntrice
    rec += creation_date.ljust(6)            # pos 14-19: data creazione DDMMYY
    rec += support_name.ljust(20)            # pos 20-39: nome supporto
    rec += " " * 6                           # pos 40-45: campo destinatario (vuoto)
    rec += " " * 59                          # pos 46-104: filler
    rec += "E"                               # pos 105: divisa (Euro)
    rec += " "                               # pos 106: filler
    rec += " " * 14                          # pos 107-120: filler
    return _pad(rec, RECORD_LENGTH)


def _build_record_14(
    progressive: int,
    scadenza: str,
    amount_cents: int,
    abi_assuntrice: str,
    cab_assuntrice: str,
    cuc: str,
    abi_domiciliataria: str,
    cab_domiciliataria: str,
) -> str:
    """Record 14 (dati della disposizione)."""
    rec = " 14"                              # pos 1-3: spazio + tipo record
    rec += str(progressive).rjust(7, "0")    # pos 4-10: progressivo
    rec += " " * 12                          # pos 11-22: filler
    rec += scadenza.ljust(6)                 # pos 23-28: data scadenza DDMMYY
    rec += str(amount_cents).rjust(13, "0")  # pos 29-41: importo in centesimi
    rec += "+"                               # pos 42: segno (+ = dare)
    rec += abi_assuntrice.ljust(5)           # pos 43-47: ABI banca assuntrice
    rec += cab_assuntrice.ljust(5)           # pos 48-52: CAB banca assuntrice
    rec += " " * 12                          # pos 53-64: filler
    rec += cuc.ljust(5)                      # pos 65-69: CUC
    rec += " " * 10                          # pos 70-79: filler
    rec += "E"                               # pos 80: codice valuta
    rec += abi_domiciliataria.ljust(5)       # pos 81-85: ABI banca domiciliataria
    rec += cab_domiciliataria.ljust(5)       # pos 86-90: CAB banca domiciliataria
    rec += " " * 30                          # pos 91-120: filler
    return _pad(rec, RECORD_LENGTH)


def _build_record_20(progressive: int, causale: str, cf_debitore: str) -> str:
    """Record 20 (descrizione e CF debitore)."""
    rec = " 20"                              # pos 1-3
    rec += str(progressive).rjust(7, "0")    # pos 4-10
    rec += causale.ljust(40)[:40]            # pos 11-50: descrizione causale
    rec += cf_debitore.ljust(16)[:16]        # pos 51-66: CF debitore
    rec += " " * 54                          # pos 67-120: filler
    return _pad(rec, RECORD_LENGTH)


def _build_record_30(progressive: int, nome_creditore: str, indirizzo_creditore: str) -> str:
    """Record 30 (dati creditore)."""
    rec = " 30"                              # pos 1-3
    rec += str(progressive).rjust(7, "0")    # pos 4-10
    rec += nome_creditore.ljust(60)[:60]     # pos 11-70: nome creditore
    rec += indirizzo_creditore.ljust(30)[:30]  # pos 71-100: indirizzo creditore
    rec += " " * 20                          # pos 101-120: filler
    return _pad(rec, RECORD_LENGTH)


def _build_record_40(
    progressive: int,
    abi_domiciliataria: str,
    cab_domiciliataria: str,
    piazza: str,
) -> str:
    """Record 40 (banca domiciliataria)."""
    rec = " 40"                              # pos 1-3
    rec += str(progressive).rjust(7, "0")    # pos 4-10
    rec += abi_domiciliataria.ljust(5)[:5]   # pos 11-15: ABI
    rec += cab_domiciliataria.ljust(5)[:5]   # pos 16-20: CAB
    rec += piazza.ljust(50)[:50]             # pos 21-70: denominazione/piazza
    rec += " " * 50                          # pos 71-120: filler
    return _pad(rec, RECORD_LENGTH)


def _build_record_50(progressive: int, causale: str, nome_debitore: str) -> str:
    """Record 50 (riferimento debito e nome debitore)."""
    rec = " 50"                              # pos 1-3
    rec += str(progressive).rjust(7, "0")    # pos 4-10
    rec += causale.ljust(40)[:40]            # pos 11-50: riferimento debito
    rec += nome_debitore.ljust(60)[:60]      # pos 51-110: nome debitore
    rec += " " * 10                          # pos 111-120: filler
    return _pad(rec, RECORD_LENGTH)


def _build_record_51(progressive: int, numero_ricevuta: str, nome_creditore: str) -> str:
    """Record 51 (numero ricevuta e denominazione creditore)."""
    rec = " 51"                              # pos 1-3
    rec += str(progressive).rjust(7, "0")    # pos 4-10
    rec += numero_ricevuta.ljust(10)[:10]    # pos 11-20: numero ricevuta
    rec += nome_creditore.ljust(60)[:60]     # pos 21-80: denominazione creditore
    rec += " " * 40                          # pos 81-120: filler
    return _pad(rec, RECORD_LENGTH)


def _build_record_70(progressive: int) -> str:
    """Record 70 (indicatori)."""
    rec = " 70"                              # pos 1-3
    rec += str(progressive).rjust(7, "0")    # pos 4-10
    rec += " " * 110                         # pos 11-120: filler/indicatori
    return _pad(rec, RECORD_LENGTH)


def _build_record_ef(
    sia_code: str,
    abi_assuntrice: str,
    creation_date: str,
    num_disposizioni: int,
    total_amount_cents: int,
    num_records: int,
) -> str:
    """Record EF (coda del flusso)."""
    rec = " EF"                              # pos 1-3
    rec += sia_code.ljust(5)                 # pos 4-8: codice SIA
    rec += abi_assuntrice.ljust(5)           # pos 9-13: ABI banca assuntrice
    rec += creation_date.ljust(6)            # pos 14-19: data creazione
    rec += " " * 20                          # pos 20-39: nome supporto (vuoto in EF)
    rec += " " * 6                           # pos 40-45: filler
    rec += str(num_disposizioni).rjust(7, "0")  # pos 46-52: numero disposizioni
    rec += str(total_amount_cents).rjust(15, "0")  # pos 53-67: importo totale centesimi
    rec += str(num_records).rjust(7, "0")    # pos 68-74: numero record totali
    rec += " " * 31                          # pos 75-105: filler
    rec += "E"                               # pos 106: divisa
    rec += " " * 14                          # pos 107-120: filler
    return _pad(rec, RECORD_LENGTH)


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


def _pad(s: str, length: int) -> str:
    """
    Assicura che la stringa sia esattamente 'length' caratteri.

    Right-pad con spazi se troppo corta, tronca se troppo lunga.
    """
    if len(s) > length:
        return s[:length]
    return s.ljust(length)


def _to_centesimi(amount: Decimal) -> int:
    """
    Converte un importo Decimal in centesimi (intero).

    Es: Decimal("1234.56") -> 123456
    """
    return int(amount * 100)


def _fmt_amount(amount_cents: int) -> str:
    """Formatta centesimi come stringa zero-padded di 13 caratteri."""
    return str(abs(amount_cents)).rjust(13, "0")


def _ascii(text: str) -> str:
    """
    Translittera caratteri accentati in ASCII e rimuove caratteri non gestibili.

    Usa prima la tabella esplicita, poi NFKD decomposition come fallback.
    """
    if not text:
        return ""
    # Applica tabella translitterazione esplicita
    result = text.translate(_TRANSLITERATION_TABLE)
    # Fallback NFKD per eventuali altri caratteri unicode
    result = unicodedata.normalize("NFKD", result)
    result = result.encode("ascii", errors="ignore").decode("ascii")
    return result
