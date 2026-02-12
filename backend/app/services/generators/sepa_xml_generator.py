"""
Generatore SEPA Credit Transfer pain.001.001.03.

Produce XML conforme allo standard ISO 20022 per bonifici SEPA,
compatibile con i sistemi bancari CBI italiani.
"""

import re
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from decimal import Decimal

from app.models.company import Company
from app.models.payment_order import PaymentOrder
from app.models.payment_order_line import PaymentOrderLine

# Namespace SEPA Credit Transfer pain.001.001.03
NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"

# Charset SEPA consentito (EPC raccomandazione)
SEPA_CHARSET_RE = re.compile(r"[^a-zA-Z0-9/\-?:().,'+\s]")

# Lunghezza massima causale SEPA
MAX_CAUSALE_LENGTH = 140

# Lunghezza massima MsgId
MAX_MSG_ID_LENGTH = 35


def generate_sepa_ct(order: PaymentOrder, company: Company) -> str:
    """
    Genera un file XML SEPA Credit Transfer pain.001.001.03.

    Args:
        order: Ordine di pagamento con le relative righe (lines).
        company: Azienda ordinante (debitore).

    Returns:
        Stringa XML conforme pain.001.001.03.

    Raises:
        ValueError: Se non ci sono righe con stato 'inclusa' o dati mancanti.
    """
    # Filtra solo le righe incluse
    included_lines = _get_included_lines(order)
    if not included_lines:
        raise ValueError("Nessuna riga con stato 'inclusa' nell'ordine di pagamento")

    # Calcola totali
    nb_of_txs = len(included_lines)
    ctrl_sum = sum(line.importo for line in included_lines)

    # Genera ID unici
    msg_id = _generate_msg_id(order)
    pmt_inf_id = f"PMT-{msg_id}"

    # Registra namespace
    ET.register_namespace("", NAMESPACE)

    # Root: Document
    document = ET.Element("Document", xmlns=NAMESPACE)

    # CstmrCdtTrfInitn
    cstmr = ET.SubElement(document, "CstmrCdtTrfInitn")

    # --- GrpHdr ---
    grp_hdr = ET.SubElement(cstmr, "GrpHdr")
    _add_text_element(grp_hdr, "MsgId", msg_id)
    _add_text_element(grp_hdr, "CreDtTm", _format_datetime_iso())
    _add_text_element(grp_hdr, "NbOfTxs", str(nb_of_txs))
    _add_text_element(grp_hdr, "CtrlSum", _format_amount(ctrl_sum))

    initg_pty = ET.SubElement(grp_hdr, "InitgPty")
    _add_text_element(initg_pty, "Nm", _truncate(company.name, 70))

    # --- PmtInf ---
    pmt_inf = ET.SubElement(cstmr, "PmtInf")
    _add_text_element(pmt_inf, "PmtInfId", _truncate(pmt_inf_id, 35))
    _add_text_element(pmt_inf, "PmtMtd", "TRF")
    _add_text_element(pmt_inf, "NbOfTxs", str(nb_of_txs))
    _add_text_element(pmt_inf, "CtrlSum", _format_amount(ctrl_sum))

    # ReqdExctnDt
    exec_date = order.data_esecuzione_richiesta
    _add_text_element(pmt_inf, "ReqdExctnDt", exec_date.isoformat())

    # Dbtr (debitore = azienda)
    dbtr = ET.SubElement(pmt_inf, "Dbtr")
    _add_text_element(dbtr, "Nm", _truncate(company.name, 70))
    if company.address:
        pstl_adr = ET.SubElement(dbtr, "PstlAdr")
        _add_text_element(pstl_adr, "Ctry", company.country or "IT")
        _add_text_element(pstl_adr, "AdrLine", _truncate(company.address, 70))

    # DbtrAcct (conto debitore)
    dbtr_acct = ET.SubElement(pmt_inf, "DbtrAcct")
    dbtr_acct_id = ET.SubElement(dbtr_acct, "Id")
    debtor_iban = _get_debtor_iban(order)
    _add_text_element(dbtr_acct_id, "IBAN", debtor_iban.replace(" ", "").upper())

    # DbtrAgt (banca debitore - BIC opzionale)
    dbtr_agt = ET.SubElement(pmt_inf, "DbtrAgt")
    fin_instn_id = ET.SubElement(dbtr_agt, "FinInstnId")
    debtor_bic = _get_debtor_bic(order)
    if debtor_bic:
        _add_text_element(fin_instn_id, "BIC", debtor_bic.upper())
    else:
        # Quando BIC non disponibile, usa "NOTPROVIDED"
        other = ET.SubElement(fin_instn_id, "Othr")
        _add_text_element(other, "Id", "NOTPROVIDED")

    # --- CdtTrfTxInf (una per riga inclusa) ---
    for line in included_lines:
        _add_credit_transfer_tx(pmt_inf, line)

    # Genera XML string
    tree = ET.ElementTree(document)
    ET.indent(tree, space="  ")

    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_body = ET.tostring(document, encoding="unicode", xml_declaration=False)

    return xml_declaration + xml_body


def _get_included_lines(order: PaymentOrder) -> list[PaymentOrderLine]:
    """Filtra le righe con stato 'inclusa'."""
    result = []
    for line in order.lines:
        stato_value = line.stato
        # Gestisci sia enum che stringa
        if hasattr(stato_value, "value"):
            stato_value = stato_value.value
        if str(stato_value) == "inclusa":
            result.append(line)
    return result


def _add_credit_transfer_tx(pmt_inf: ET.Element, line: PaymentOrderLine) -> None:
    """Aggiunge un elemento CdtTrfTxInf per una riga di pagamento."""
    cdt_trf = ET.SubElement(pmt_inf, "CdtTrfTxInf")

    # PmtId
    pmt_id = ET.SubElement(cdt_trf, "PmtId")
    end_to_end_id = line.end_to_end_id or _generate_end_to_end_id()
    _add_text_element(pmt_id, "EndToEndId", _truncate(end_to_end_id, 35))

    # Amt
    amt = ET.SubElement(cdt_trf, "Amt")
    instd_amt = ET.SubElement(amt, "InstdAmt", Ccy=line.valuta or "EUR")
    instd_amt.text = _format_amount(line.importo)

    # CdtrAgt (BIC creditore, opzionale)
    if line.beneficiario_bic:
        cdtr_agt = ET.SubElement(cdt_trf, "CdtrAgt")
        fin_instn = ET.SubElement(cdtr_agt, "FinInstnId")
        _add_text_element(fin_instn, "BIC", line.beneficiario_bic.upper())

    # Cdtr (creditore = beneficiario)
    cdtr = ET.SubElement(cdt_trf, "Cdtr")
    _add_text_element(cdtr, "Nm", _truncate(line.beneficiario_nome, 70))
    if line.beneficiario_indirizzo:
        pstl_adr = ET.SubElement(cdtr, "PstlAdr")
        _add_text_element(pstl_adr, "AdrLine", _truncate(line.beneficiario_indirizzo, 70))

    # CdtrAcct (IBAN creditore)
    if line.beneficiario_iban:
        cdtr_acct = ET.SubElement(cdt_trf, "CdtrAcct")
        cdtr_acct_id = ET.SubElement(cdtr_acct, "Id")
        _add_text_element(cdtr_acct_id, "IBAN", line.beneficiario_iban.replace(" ", "").upper())

    # RmtInf (causale)
    if line.causale:
        rmt_inf = ET.SubElement(cdt_trf, "RmtInf")
        sanitized = _sanitize_sepa_text(line.causale)
        _add_text_element(rmt_inf, "Ustrd", _truncate(sanitized, MAX_CAUSALE_LENGTH))


# ---------------------------------------------------------------------------
# Funzioni helper
# ---------------------------------------------------------------------------

def _generate_msg_id(order: PaymentOrder) -> str:
    """Genera un MsgId unico (max 35 caratteri)."""
    short_uuid = uuid.uuid4().hex[:12]
    ref = str(order.riferimento_interno or "ORD")[:15]
    msg_id = f"{ref}-{short_uuid}"
    return msg_id[:MAX_MSG_ID_LENGTH]


def _generate_end_to_end_id() -> str:
    """Genera un EndToEndId unico (max 35 caratteri)."""
    return f"E2E-{uuid.uuid4().hex[:28]}"


def _format_datetime_iso() -> str:
    """Restituisce datetime corrente in formato ISO 8601 per SEPA."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _format_amount(amount: Decimal) -> str:
    """Formatta un importo Decimal con 2 decimali e punto come separatore."""
    return f"{amount:.2f}"


def _sanitize_sepa_text(text: str) -> str:
    """
    Rimuove caratteri non consentiti dal charset SEPA.

    Charset consentito: a-zA-Z0-9 / - ? : ( ) . , ' + spazio
    """
    return SEPA_CHARSET_RE.sub("", text)


def _truncate(text: str, max_length: int) -> str:
    """Tronca una stringa alla lunghezza massima."""
    if not text:
        return ""
    return text[:max_length]


def _add_text_element(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """Aggiunge un sotto-elemento con testo."""
    elem = ET.SubElement(parent, tag)
    elem.text = text
    return elem


def _get_debtor_iban(order: PaymentOrder) -> str:
    """Recupera l'IBAN del debitore dal conto bancario dell'ordine."""
    if order.bank_account and order.bank_account.iban:
        return order.bank_account.iban
    raise ValueError(
        "IBAN debitore non disponibile: associare un conto bancario con IBAN all'ordine"
    )


def _get_debtor_bic(order: PaymentOrder) -> str | None:
    """Recupera il BIC del debitore dal conto bancario dell'ordine (opzionale)."""
    if order.bank_account and order.bank_account.bic:
        return order.bank_account.bic
    return None
