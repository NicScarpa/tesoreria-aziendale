"""
Generatore SEPA Direct Debit pain.008.001.02.

Produce XML conforme allo standard ISO 20022 per addebiti diretti SEPA,
compatibile con i sistemi bancari CBI italiani.

Struttura invertita rispetto al SEPA CT:
- Cdtr (creditore) = azienda che incassa
- Dbtr (debitore) = controparte addebitata
"""

import re
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from decimal import Decimal

from app.models.company import Company
from app.models.payment_order import PaymentOrder
from app.models.payment_order_line import PaymentOrderLine

# Namespace SEPA Direct Debit pain.008.001.02
NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:pain.008.001.02"

# Charset SEPA consentito
SEPA_CHARSET_RE = re.compile(r"[^a-zA-Z0-9/\-?:().,'+\s]")

MAX_CAUSALE_LENGTH = 140
MAX_MSG_ID_LENGTH = 35


def generate_sdd(order: PaymentOrder, company: Company) -> str:
    """
    Genera un file XML SEPA Direct Debit pain.008.001.02.

    Args:
        order: Ordine di pagamento con le relative righe.
        company: Azienda creditrice che incassa tramite SDD.

    Returns:
        Stringa XML conforme pain.008.001.02.

    Raises:
        ValueError: Se non ci sono righe con stato 'inclusa' o dati mancanti.
    """
    included_lines = _get_included_lines(order)
    if not included_lines:
        raise ValueError("Nessuna riga con stato 'inclusa' nell'ordine di pagamento")

    nb_of_txs = len(included_lines)
    ctrl_sum = sum(line.importo for line in included_lines)

    msg_id = _generate_msg_id(order)
    pmt_inf_id = f"SDD-{msg_id}"

    # Determina tipo mandato (CORE o B2B) dalla prima riga con mandato
    sdd_local_instrument = _determine_local_instrument(included_lines)

    ET.register_namespace("", NAMESPACE)

    # Root: Document
    document = ET.Element("Document", xmlns=NAMESPACE)

    # CstmrDrctDbtInitn
    cstmr = ET.SubElement(document, "CstmrDrctDbtInitn")

    # --- GrpHdr ---
    grp_hdr = ET.SubElement(cstmr, "GrpHdr")
    _add_text(grp_hdr, "MsgId", msg_id)
    _add_text(grp_hdr, "CreDtTm", _format_datetime_iso())
    _add_text(grp_hdr, "NbOfTxs", str(nb_of_txs))
    _add_text(grp_hdr, "CtrlSum", _format_amount(ctrl_sum))

    initg_pty = ET.SubElement(grp_hdr, "InitgPty")
    _add_text(initg_pty, "Nm", _truncate(company.name, 70))

    # --- PmtInf ---
    pmt_inf = ET.SubElement(cstmr, "PmtInf")
    _add_text(pmt_inf, "PmtInfId", _truncate(pmt_inf_id, 35))
    _add_text(pmt_inf, "PmtMtd", "DD")
    _add_text(pmt_inf, "NbOfTxs", str(nb_of_txs))
    _add_text(pmt_inf, "CtrlSum", _format_amount(ctrl_sum))

    # PmtTpInf
    pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
    svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
    _add_text(svc_lvl, "Cd", "SEPA")
    lcl_instrm = ET.SubElement(pmt_tp_inf, "LclInstrm")
    _add_text(lcl_instrm, "Cd", sdd_local_instrument)

    # Determine sequence type from first line (for PmtInf level)
    seq_tp = _determine_sequence_type(included_lines)
    _add_text(pmt_tp_inf, "SeqTp", seq_tp)

    # ReqdColltnDt (data incasso richiesta)
    collection_date = order.data_esecuzione_richiesta
    _add_text(pmt_inf, "ReqdColltnDt", collection_date.isoformat())

    # Cdtr (creditore = azienda che incassa)
    cdtr = ET.SubElement(pmt_inf, "Cdtr")
    _add_text(cdtr, "Nm", _truncate(company.name, 70))
    if company.address:
        pstl_adr = ET.SubElement(cdtr, "PstlAdr")
        _add_text(pstl_adr, "Ctry", company.country or "IT")
        _add_text(pstl_adr, "AdrLine", _truncate(company.address, 70))

    # CdtrAcct (conto creditore)
    cdtr_acct = ET.SubElement(pmt_inf, "CdtrAcct")
    cdtr_acct_id = ET.SubElement(cdtr_acct, "Id")
    creditor_iban = _get_creditor_iban(order)
    _add_text(cdtr_acct_id, "IBAN", creditor_iban.replace(" ", "").upper())

    # CdtrAgt (banca creditore)
    cdtr_agt = ET.SubElement(pmt_inf, "CdtrAgt")
    fin_instn_id = ET.SubElement(cdtr_agt, "FinInstnId")
    creditor_bic = _get_creditor_bic(order)
    if creditor_bic:
        _add_text(fin_instn_id, "BIC", creditor_bic.upper())
    else:
        other = ET.SubElement(fin_instn_id, "Othr")
        _add_text(other, "Id", "NOTPROVIDED")

    # CdtrSchmeId (identificativo schema creditore - obbligatorio per SDD)
    cdtr_schme_id = ET.SubElement(pmt_inf, "CdtrSchmeId")
    schme_id = ET.SubElement(cdtr_schme_id, "Id")
    prvt_id = ET.SubElement(schme_id, "PrvtId")
    othr = ET.SubElement(prvt_id, "Othr")
    # Creditor Identifier: usa VAT number prefissato da IT + check digits
    creditor_id = _build_creditor_identifier(company)
    _add_text(othr, "Id", creditor_id)
    schme_nm = ET.SubElement(othr, "SchmeNm")
    _add_text(schme_nm, "Prtry", "SEPA")

    # --- DrctDbtTxInf (una per riga inclusa) ---
    for line in included_lines:
        _add_direct_debit_tx(pmt_inf, line)

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
        if hasattr(stato_value, "value"):
            stato_value = stato_value.value
        if str(stato_value) == "inclusa":
            result.append(line)
    return result


def _add_direct_debit_tx(pmt_inf: ET.Element, line: PaymentOrderLine) -> None:
    """Aggiunge un elemento DrctDbtTxInf per una riga di addebito."""
    drct_dbt = ET.SubElement(pmt_inf, "DrctDbtTxInf")

    # PmtId
    pmt_id = ET.SubElement(drct_dbt, "PmtId")
    end_to_end_id = line.end_to_end_id or _generate_end_to_end_id()
    _add_text(pmt_id, "EndToEndId", _truncate(end_to_end_id, 35))

    # InstdAmt
    instd_amt = ET.SubElement(drct_dbt, "InstdAmt", Ccy=line.valuta or "EUR")
    instd_amt.text = _format_amount(line.importo)

    # DrctDbtTx / MndtRltdInf (informazioni mandato - obbligatorie)
    drct_dbt_tx = ET.SubElement(drct_dbt, "DrctDbtTx")
    mndt_rltd_inf = ET.SubElement(drct_dbt_tx, "MndtRltdInf")

    mandate_id = line.sdd_mandate_id or f"MNDT-{uuid.uuid4().hex[:16]}"
    _add_text(mndt_rltd_inf, "MndtId", _truncate(mandate_id, 35))

    mandate_date = line.sdd_mandate_date
    if mandate_date:
        _add_text(mndt_rltd_inf, "DtOfSgntr", mandate_date.isoformat())
    else:
        # Data firma mandato obbligatoria: usa data odierna come fallback
        _add_text(mndt_rltd_inf, "DtOfSgntr", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    _add_text(mndt_rltd_inf, "AmdmntInd", "false")

    # DbtrAgt (banca debitore)
    if line.beneficiario_bic:
        dbtr_agt = ET.SubElement(drct_dbt, "DbtrAgt")
        fin_instn = ET.SubElement(dbtr_agt, "FinInstnId")
        _add_text(fin_instn, "BIC", line.beneficiario_bic.upper())

    # Dbtr (debitore = controparte addebitata)
    dbtr = ET.SubElement(drct_dbt, "Dbtr")
    _add_text(dbtr, "Nm", _truncate(line.beneficiario_nome, 70))
    if line.beneficiario_indirizzo:
        pstl_adr = ET.SubElement(dbtr, "PstlAdr")
        _add_text(pstl_adr, "AdrLine", _truncate(line.beneficiario_indirizzo, 70))

    # DbtrAcct (IBAN debitore)
    if line.beneficiario_iban:
        dbtr_acct = ET.SubElement(drct_dbt, "DbtrAcct")
        dbtr_acct_id = ET.SubElement(dbtr_acct, "Id")
        _add_text(dbtr_acct_id, "IBAN", line.beneficiario_iban.replace(" ", "").upper())

    # RmtInf (causale)
    if line.causale:
        rmt_inf = ET.SubElement(drct_dbt, "RmtInf")
        sanitized = _sanitize_sepa_text(line.causale)
        _add_text(rmt_inf, "Ustrd", _truncate(sanitized, MAX_CAUSALE_LENGTH))


# ---------------------------------------------------------------------------
# Funzioni helper
# ---------------------------------------------------------------------------

def _generate_msg_id(order: PaymentOrder) -> str:
    """Genera un MsgId unico (max 35 caratteri)."""
    short_uuid = uuid.uuid4().hex[:12]
    ref = str(order.riferimento_interno or "SDD")[:15]
    msg_id = f"{ref}-{short_uuid}"
    return msg_id[:MAX_MSG_ID_LENGTH]


def _generate_end_to_end_id() -> str:
    """Genera un EndToEndId unico (max 35 caratteri)."""
    return f"E2E-{uuid.uuid4().hex[:28]}"


def _format_datetime_iso() -> str:
    """Restituisce datetime corrente in formato ISO 8601."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _format_amount(amount: Decimal) -> str:
    """Formatta un importo Decimal con 2 decimali e punto come separatore."""
    return f"{amount:.2f}"


def _sanitize_sepa_text(text: str) -> str:
    """Rimuove caratteri non consentiti dal charset SEPA."""
    return SEPA_CHARSET_RE.sub("", text)


def _truncate(text: str, max_length: int) -> str:
    """Tronca una stringa alla lunghezza massima."""
    if not text:
        return ""
    return text[:max_length]


def _add_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """Aggiunge un sotto-elemento con testo."""
    elem = ET.SubElement(parent, tag)
    elem.text = text
    return elem


def _get_creditor_iban(order: PaymentOrder) -> str:
    """Recupera l'IBAN del creditore dal conto bancario dell'ordine."""
    if order.bank_account and order.bank_account.iban:
        return order.bank_account.iban
    raise ValueError(
        "IBAN creditore non disponibile: associare un conto bancario con IBAN all'ordine"
    )


def _get_creditor_bic(order: PaymentOrder) -> str | None:
    """Recupera il BIC del creditore dal conto bancario dell'ordine (opzionale)."""
    if order.bank_account and order.bank_account.bic:
        return order.bank_account.bic
    return None


def _build_creditor_identifier(company: Company) -> str:
    """
    Costruisce il Creditor Identifier per SDD.

    Formato: IT + 2 check digits + 3 char codice business + creditor ref (max 28 char)
    Semplificato: usa IT00ZZZ + VAT number come identificativo.
    """
    vat = (company.vat_number or company.tax_number or "00000000000")
    # Rimuovi prefisso paese se presente
    if vat.upper().startswith("IT"):
        vat = vat[2:]
    return f"IT00ZZZ{vat[:28]}"


def _determine_local_instrument(lines: list[PaymentOrderLine]) -> str:
    """
    Determina il tipo di strumento locale (CORE o B2B) dalle righe.

    Default: CORE se non specificato.
    """
    for line in lines:
        mandate_type = line.sdd_mandate_type
        if mandate_type:
            type_value = mandate_type
            if hasattr(type_value, "value"):
                type_value = type_value.value
            if str(type_value).upper() == "B2B":
                return "B2B"
    return "CORE"


def _determine_sequence_type(lines: list[PaymentOrderLine]) -> str:
    """
    Determina il SeqTp (tipo sequenza) dalle righe.

    Valori possibili: FRST, RCUR, FNAL, OOFF.
    Default: RCUR se non specificato.
    """
    for line in lines:
        seq_type = line.sdd_sequence_type
        if seq_type:
            seq_value = seq_type
            if hasattr(seq_value, "value"):
                seq_value = seq_value.value
            return str(seq_value).upper()
    return "RCUR"
