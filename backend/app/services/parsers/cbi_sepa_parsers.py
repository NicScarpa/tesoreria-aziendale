"""Parsers for CBI and SEPA banking formats.

Supports:
- camt.053 (Bank-to-Customer Statement)
- camt.054 (Bank-to-Customer Debit/Credit Notification)
- pain.002 (Payment Status Report)
- CBI Rendicontazione (fixed-width records)
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from lxml import etree

logger = logging.getLogger(__name__)

CAMT053_NS = "urn:iso:std:iso:20022:tech:xsd:camt.053.001.02"
CAMT054_NS = "urn:iso:std:iso:20022:tech:xsd:camt.054.001.02"
PAIN002_NS = "urn:iso:std:iso:20022:tech:xsd:pain.002.001.03"


def _text(element, xpath: str, ns: dict) -> str:
    results = element.xpath(xpath, namespaces=ns)
    if results:
        el = results[0]
        return el.text.strip() if el.text else ""
    return ""


def _parse_decimal(value: str) -> Decimal:
    if not value:
        return Decimal("0")
    try:
        return Decimal(value.strip())
    except InvalidOperation:
        return Decimal("0")


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


# --- camt.053 Parser ---

@dataclass
class CAMT053Statement:
    account_iban: str = ""
    account_currency: str = "EUR"
    statement_id: str = ""
    creation_datetime: datetime | None = None
    opening_balance: Decimal = Decimal("0")
    closing_balance: Decimal = Decimal("0")
    entries: list[dict] = field(default_factory=list)


class CAMT053Parser:
    """Parse camt.053.001.02 Bank-to-Customer Statement."""

    def parse(self, file_bytes: bytes) -> list[CAMT053Statement]:
        tree = etree.fromstring(file_bytes)
        ns = {"c": CAMT053_NS}

        # Try with namespace, fallback to local-name
        stmts = tree.xpath("//c:Stmt", namespaces=ns)
        if not stmts:
            stmts = tree.xpath("//*[local-name()='Stmt']")
            ns = {}

        results = []
        for stmt in stmts:
            statement = CAMT053Statement()
            statement.statement_id = _text(stmt, "c:Id", ns) if ns else _text(stmt, "*[local-name()='Id']", {})
            statement.creation_datetime = _parse_datetime(
                _text(stmt, "c:CreDtTm", ns) if ns else _text(stmt, "*[local-name()='CreDtTm']", {})
            )

            # Account
            statement.account_iban = (
                _text(stmt, ".//c:Acct/c:Id/c:IBAN", ns) if ns
                else _text(stmt, ".//*[local-name()='Acct']/*[local-name()='Id']/*[local-name()='IBAN']", {})
            )
            statement.account_currency = (
                _text(stmt, ".//c:Acct/c:Ccy", ns) if ns
                else _text(stmt, ".//*[local-name()='Acct']/*[local-name()='Ccy']", {})
            ) or "EUR"

            # Balances
            bals = stmt.xpath(".//c:Bal", namespaces=ns) if ns else stmt.xpath(".//*[local-name()='Bal']")
            for bal in bals:
                tp = _text(bal, ".//c:Cd", ns) if ns else _text(bal, ".//*[local-name()='Cd']", {})
                amt = _parse_decimal(
                    _text(bal, ".//c:Amt", ns) if ns else _text(bal, ".//*[local-name()='Amt']", {})
                )
                if tp == "OPBD":
                    statement.opening_balance = amt
                elif tp == "CLBD":
                    statement.closing_balance = amt

            # Entries
            entries = stmt.xpath(".//c:Ntry", namespaces=ns) if ns else stmt.xpath(".//*[local-name()='Ntry']")
            for entry in entries:
                amt = _parse_decimal(
                    _text(entry, "c:Amt", ns) if ns else _text(entry, "*[local-name()='Amt']", {})
                )
                cdt_dbt = (
                    _text(entry, "c:CdtDbtInd", ns) if ns
                    else _text(entry, "*[local-name()='CdtDbtInd']", {})
                )
                direction = "inflow" if cdt_dbt == "CRDT" else "outflow"

                booking_date = _parse_date(
                    _text(entry, ".//c:BookgDt/c:Dt", ns) if ns
                    else _text(entry, ".//*[local-name()='BookgDt']/*[local-name()='Dt']", {})
                )
                value_date = _parse_date(
                    _text(entry, ".//c:ValDt/c:Dt", ns) if ns
                    else _text(entry, ".//*[local-name()='ValDt']/*[local-name()='Dt']", {})
                )

                ref = (
                    _text(entry, ".//c:AcctSvcrRef", ns) if ns
                    else _text(entry, ".//*[local-name()='AcctSvcrRef']", {})
                )

                # Remittance info
                rmtinf = (
                    _text(entry, ".//c:RmtInf/c:Ustrd", ns) if ns
                    else _text(entry, ".//*[local-name()='RmtInf']/*[local-name()='Ustrd']", {})
                )

                # Counterpart
                counterpart = ""
                if direction == "inflow":
                    counterpart = (
                        _text(entry, ".//c:NtryDtls//c:RltdPties/c:Dbtr/c:Nm", ns) if ns
                        else _text(entry, ".//*[local-name()='Dbtr']/*[local-name()='Nm']", {})
                    )
                else:
                    counterpart = (
                        _text(entry, ".//c:NtryDtls//c:RltdPties/c:Cdtr/c:Nm", ns) if ns
                        else _text(entry, ".//*[local-name()='Cdtr']/*[local-name()='Nm']", {})
                    )

                statement.entries.append({
                    "amount": amt,
                    "direction": direction,
                    "booking_date": booking_date,
                    "value_date": value_date,
                    "reference": ref,
                    "description": rmtinf,
                    "counterpart_name": counterpart,
                    "currency": statement.account_currency,
                })

            results.append(statement)

        return results


# --- camt.054 Parser ---

class CAMT054Parser:
    """Parse camt.054.001.02 Debit/Credit Notification.
    Structure is nearly identical to camt.053."""

    def parse(self, file_bytes: bytes) -> list[CAMT053Statement]:
        tree = etree.fromstring(file_bytes)
        ns = {"c": CAMT054_NS}

        ntfctns = tree.xpath("//c:Ntfctn", namespaces=ns)
        if not ntfctns:
            ntfctns = tree.xpath("//*[local-name()='Ntfctn']")
            ns = {}

        results = []
        for ntfctn in ntfctns:
            statement = CAMT053Statement()
            statement.statement_id = _text(ntfctn, "c:Id", ns) if ns else _text(ntfctn, "*[local-name()='Id']", {})
            statement.account_iban = (
                _text(ntfctn, ".//c:Acct/c:Id/c:IBAN", ns) if ns
                else _text(ntfctn, ".//*[local-name()='Acct']/*[local-name()='Id']/*[local-name()='IBAN']", {})
            )

            entries = ntfctn.xpath(".//c:Ntry", namespaces=ns) if ns else ntfctn.xpath(".//*[local-name()='Ntry']")
            for entry in entries:
                amt = _parse_decimal(
                    _text(entry, "c:Amt", ns) if ns else _text(entry, "*[local-name()='Amt']", {})
                )
                cdt_dbt = _text(entry, "c:CdtDbtInd", ns) if ns else _text(entry, "*[local-name()='CdtDbtInd']", {})

                statement.entries.append({
                    "amount": amt,
                    "direction": "inflow" if cdt_dbt == "CRDT" else "outflow",
                    "booking_date": _parse_date(
                        _text(entry, ".//c:BookgDt/c:Dt", ns) if ns
                        else _text(entry, ".//*[local-name()='BookgDt']/*[local-name()='Dt']", {})
                    ),
                    "reference": _text(entry, ".//c:AcctSvcrRef", ns) if ns else _text(entry, ".//*[local-name()='AcctSvcrRef']", {}),
                    "description": _text(entry, ".//c:RmtInf/c:Ustrd", ns) if ns else _text(entry, ".//*[local-name()='RmtInf']/*[local-name()='Ustrd']", {}),
                })

            results.append(statement)

        return results


# --- pain.002 Parser ---

@dataclass
class PaymentStatusEntry:
    original_end_to_end_id: str = ""
    original_instruction_id: str = ""
    status: str = ""  # ACCP, RJCT, etc.
    reason_code: str = ""
    reason_text: str = ""


class PAIN002Parser:
    """Parse pain.002.001.03 Payment Status Report."""

    def parse(self, file_bytes: bytes) -> list[PaymentStatusEntry]:
        tree = etree.fromstring(file_bytes)
        ns = {"p": PAIN002_NS}

        tx_infos = tree.xpath("//p:TxInfAndSts", namespaces=ns)
        if not tx_infos:
            tx_infos = tree.xpath("//*[local-name()='TxInfAndSts']")
            ns = {}

        results = []
        for tx in tx_infos:
            entry = PaymentStatusEntry()
            entry.original_end_to_end_id = (
                _text(tx, "p:OrgnlEndToEndId", ns) if ns
                else _text(tx, "*[local-name()='OrgnlEndToEndId']", {})
            )
            entry.original_instruction_id = (
                _text(tx, "p:OrgnlInstrId", ns) if ns
                else _text(tx, "*[local-name()='OrgnlInstrId']", {})
            )
            entry.status = (
                _text(tx, "p:TxSts", ns) if ns
                else _text(tx, "*[local-name()='TxSts']", {})
            )
            entry.reason_code = (
                _text(tx, ".//p:StsRsnInf/p:Rsn/p:Cd", ns) if ns
                else _text(tx, ".//*[local-name()='Rsn']/*[local-name()='Cd']", {})
            )
            entry.reason_text = (
                _text(tx, ".//p:StsRsnInf/p:AddtlInf", ns) if ns
                else _text(tx, ".//*[local-name()='AddtlInf']", {})
            )
            results.append(entry)

        return results


# --- CBI Rendicontazione Parser ---

@dataclass
class CBIRendicontazioneRecord:
    tipo_record: str = ""
    riferimento: str = ""
    data_operazione: date | None = None
    importo: Decimal = Decimal("0")
    segno: str = ""  # "C" or "D"
    causale: str = ""
    descrizione: str = ""


class CBIRendicontazioneParser:
    """Parse CBI Rendicontazione fixed-width format (120 char records).

    Record types:
    - IB: Header
    - 14: Record di movimento
    - 20/30/40/50/51/70: Informazioni aggiuntive
    - EF: Footer
    """

    def parse(self, file_bytes: bytes) -> list[CBIRendicontazioneRecord]:
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("iso-8859-1")

        results = []
        current_record: CBIRendicontazioneRecord | None = None

        for line in content.splitlines():
            if len(line) < 2:
                continue

            tipo = line[:2].strip()

            if tipo == "14" and len(line) >= 113:
                # Record di movimento
                current_record = CBIRendicontazioneRecord()
                current_record.tipo_record = "14"

                try:
                    current_record.data_operazione = date(
                        2000 + int(line[10:12]), int(line[12:14]), int(line[14:16])
                    )
                except (ValueError, IndexError):
                    pass

                segno = line[16:17].strip()
                current_record.segno = segno

                try:
                    importo_str = line[17:30].strip()
                    if importo_str:
                        importo_cents = int(importo_str)
                        current_record.importo = Decimal(importo_cents) / Decimal(100)
                except (ValueError, InvalidOperation):
                    pass

                current_record.causale = line[30:32].strip()
                current_record.riferimento = line[32:55].strip()
                current_record.descrizione = line[55:113].strip()

                results.append(current_record)

            elif tipo in ("20", "30", "40", "50", "51", "70") and current_record:
                # Additional info - append to description
                extra = line[2:].strip()
                if extra:
                    current_record.descrizione += " " + extra

        return results


def validate_sepa_xml(file_bytes: bytes) -> dict:
    """Validate a SEPA XML file and return validation result.

    Returns dict with: valid, errors, file_type, message_id
    """
    errors = []
    file_type = None
    message_id = None

    try:
        tree = etree.fromstring(file_bytes)
    except etree.XMLSyntaxError as e:
        return {"valid": False, "errors": [f"XML non valido: {e}"], "file_type": None, "message_id": None}

    root = tree if not hasattr(tree, "getroot") else tree.getroot()
    nsmap = root.nsmap

    # Detect file type from namespace
    for ns_uri in nsmap.values():
        if not ns_uri:
            continue
        if "pain.001" in ns_uri:
            file_type = "pain.001 (SCT - Bonifico SEPA)"
        elif "pain.002" in ns_uri:
            file_type = "pain.002 (Esito pagamento)"
        elif "pain.008" in ns_uri:
            file_type = "pain.008 (SDD - Addebito diretto)"
        elif "camt.053" in ns_uri:
            file_type = "camt.053 (Estratto conto)"
        elif "camt.054" in ns_uri:
            file_type = "camt.054 (Notifica addebito/accredito)"

    if not file_type:
        errors.append("Namespace SEPA/ISO 20022 non riconosciuto")

    # Extract message ID
    msg_ids = root.xpath("//*[local-name()='MsgId']")
    if msg_ids:
        message_id = msg_ids[0].text
    else:
        errors.append("MsgId non trovato nel documento")

    # Basic structure checks
    if not root.xpath("//*[local-name()='GrpHdr']"):
        errors.append("GrpHdr (Group Header) mancante")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "file_type": file_type,
        "message_id": message_id,
    }
