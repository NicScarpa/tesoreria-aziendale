"""Parser for FatturaPA (Italian electronic invoice) XML files.

Supports:
- FatturaPA v1.2, v1.2.1, v1.2.2
- .xml and .xml.p7m (signed) files
- Multi-body invoices
- Encoding detection (UTF-8, ISO-8859-1, Windows-1252)
"""
import base64
import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

from lxml import etree

logger = logging.getLogger(__name__)

# FatturaPA namespace
FPA_NS = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"
FPA_NAMESPACES = {
    "p": FPA_NS,
    "ds": "http://www.w3.org/2000/09/xmldsig#",
}

# TipoDocumento mapping
TIPO_DOCUMENTO_MAP = {
    "TD01": "fattura",      # Fattura
    "TD02": "fattura",      # Acconto/anticipo
    "TD03": "fattura",      # Acconto/anticipo su parcella
    "TD04": "nota_credito", # Nota di credito
    "TD05": "nota_debito",  # Nota di debito
    "TD06": "fattura",      # Parcella
    # Autofatture (TD16-TD27)
    "TD16": "autofattura",
    "TD17": "autofattura",
    "TD18": "autofattura",
    "TD19": "autofattura",
    "TD20": "autofattura",
    "TD21": "autofattura",
    "TD22": "autofattura",
    "TD23": "autofattura",
    "TD24": "autofattura",
    "TD25": "autofattura",
    "TD26": "autofattura",
    "TD27": "autofattura",
}

# ModalitaPagamento mapping
MODALITA_PAGAMENTO_MAP = {
    "MP01": "contanti",
    "MP02": "assegno",
    "MP03": "assegno_circolare",
    "MP04": "contanti_tesoreria",
    "MP05": "bonifico",
    "MP06": "vaglia_cambiario",
    "MP07": "bollettino_bancario",
    "MP08": "carta",
    "MP09": "rid",
    "MP10": "rid_utenze",
    "MP11": "rid_veloce",
    "MP12": "riba",
    "MP13": "mav",
    "MP14": "quietanza_erario",
    "MP15": "giroconto",
    "MP16": "domiciliazione_bancaria",
    "MP17": "domiciliazione_postale",
    "MP18": "bollettino_postale",
    "MP19": "sepa_dd",
    "MP20": "sepa_dd_core",
    "MP21": "sepa_dd_b2b",
    "MP22": "trattenuta_somme",
    "MP23": "pagopa",
}


@dataclass
class ParsedInvoice:
    """Represents a parsed invoice from FatturaPA XML."""
    # Tipo
    tipo_documento_codice: str = ""  # TD01, TD04, etc.
    tipo_documento_tipo: str = ""    # fattura, nota_credito, autofattura

    # Cedente (seller)
    cedente_denominazione: str = ""
    cedente_piva: str = ""
    cedente_cf: str = ""
    cedente_regime_fiscale: str = ""

    # Cessionario (buyer)
    cessionario_denominazione: str = ""
    cessionario_piva: str = ""
    cessionario_cf: str = ""

    # Fattura
    numero_fattura: str = ""
    data_fattura: date | None = None

    # Importi
    importo_totale: Decimal = Decimal("0")
    imponibile_totale: Decimal = Decimal("0")
    iva_totale: Decimal = Decimal("0")
    valuta: str = "EUR"

    # Pagamento
    condizioni_pagamento: str = ""
    modalita_pagamento: str = ""  # Codice originale (MP05, ecc.)
    modalita_pagamento_desc: str = ""  # Descrizione mappata
    data_scadenza_pagamento: date | None = None
    iban_pagamento: str = ""

    # SDI
    identificativo_sdi: str = ""

    # Allegati
    pdf_allegato_base64: str = ""
    pdf_allegato_nome: str = ""

    # Dettaglio linee
    linee_dettaglio: list[dict] = field(default_factory=list)

    # Riepilogo IVA
    riepilogo_iva: list[dict] = field(default_factory=list)


def _detect_encoding(file_bytes: bytes) -> str:
    """Auto-detect encoding: try UTF-8, then fall back to latin-1."""
    for enc in ["utf-8-sig", "utf-8", "iso-8859-1", "windows-1252"]:
        try:
            file_bytes.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def _extract_xml_from_p7m(file_bytes: bytes) -> bytes:
    """Extract XML content from a .p7m (PKCS#7 signed) file."""
    try:
        from asn1crypto.cms import ContentInfo
        content_info = ContentInfo.load(file_bytes)
        content = content_info["content"]
        encap = content["encap_content_info"]
        xml_bytes = encap["content"].native
        if isinstance(xml_bytes, str):
            xml_bytes = xml_bytes.encode("utf-8")
        return xml_bytes
    except Exception as e:
        logger.warning(f"P7M extraction failed, trying raw XML: {e}")
        # Maybe it's just XML with wrong extension
        return file_bytes


def _text(element, xpath: str, namespaces: dict | None = None) -> str:
    """Extract text from first matching element, or empty string."""
    ns = namespaces or FPA_NAMESPACES
    results = element.xpath(xpath, namespaces=ns)
    if results:
        el = results[0]
        return el.text.strip() if el.text else ""
    return ""


def _parse_date(date_str: str) -> date | None:
    """Parse date from YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        parts = date_str[:10].split("-")
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None


def _parse_decimal(value_str: str) -> Decimal:
    """Parse decimal from string."""
    if not value_str:
        return Decimal("0")
    try:
        return Decimal(value_str.strip())
    except InvalidOperation:
        return Decimal("0")


def _find_root_with_namespace(tree) -> tuple:
    """Find the FatturaPA root element handling various namespace versions."""
    root = tree.getroot() if hasattr(tree, "getroot") else tree

    # Try with explicit namespace
    nsmap = root.nsmap

    # Build namespace dict trying multiple versions
    ns = dict(FPA_NAMESPACES)
    for prefix, uri in nsmap.items():
        if "fatture" in (uri or ""):
            ns["p"] = uri
            break

    return root, ns


def parse(file_bytes: bytes, filename: str = "") -> list[ParsedInvoice]:
    """Parse a FatturaPA XML file and return list of ParsedInvoice.

    Args:
        file_bytes: Raw file content
        filename: Original filename (used to detect .p7m)

    Returns:
        List of ParsedInvoice (one per FatturaElettronicaBody)
    """
    # Handle .p7m signed files
    if filename.lower().endswith(".p7m"):
        file_bytes = _extract_xml_from_p7m(file_bytes)

    # Detect encoding and parse
    encoding = _detect_encoding(file_bytes)
    try:
        # lxml handles encoding declaration in XML
        tree = etree.fromstring(file_bytes)
    except etree.XMLSyntaxError:
        # Try decoding and re-encoding
        content = file_bytes.decode(encoding, errors="replace")
        tree = etree.fromstring(content.encode("utf-8"))

    root, ns = _find_root_with_namespace(tree)

    results = []

    # Extract header (shared across bodies)
    header = root.xpath(".//p:FatturaElettronicaHeader", namespaces=ns)
    if not header:
        # Try without namespace
        header = root.xpath(".//*[local-name()='FatturaElettronicaHeader']")

    cedente_denominazione = ""
    cedente_piva = ""
    cedente_cf = ""
    cedente_regime = ""
    cessionario_denominazione = ""
    cessionario_piva = ""
    cessionario_cf = ""
    identificativo_sdi = ""

    if header:
        h = header[0]
        # Cedente/Prestatore
        cedente_denominazione = (
            _text(h, ".//p:CedentePrestatore//p:Denominazione", ns)
            or (
                _text(h, ".//p:CedentePrestatore//p:Nome", ns) + " " +
                _text(h, ".//p:CedentePrestatore//p:Cognome", ns)
            ).strip()
        )
        cedente_piva = _text(h, ".//p:CedentePrestatore//p:IdCodice", ns)
        cedente_cf = _text(h, ".//p:CedentePrestatore//p:CodiceFiscale", ns)
        cedente_regime = _text(h, ".//p:CedentePrestatore//p:RegimeFiscale", ns)

        # Cessionario/Committente
        cessionario_denominazione = (
            _text(h, ".//p:CessionarioCommittente//p:Denominazione", ns)
            or (
                _text(h, ".//p:CessionarioCommittente//p:Nome", ns) + " " +
                _text(h, ".//p:CessionarioCommittente//p:Cognome", ns)
            ).strip()
        )
        cessionario_piva = _text(h, ".//p:CessionarioCommittente//p:IdCodice", ns)
        cessionario_cf = _text(h, ".//p:CessionarioCommittente//p:CodiceFiscale", ns)

        # SDI
        identificativo_sdi = _text(h, ".//p:DatiTrasmissione//p:ProgressivoInvio", ns)

    # Find all bodies
    bodies = root.xpath(".//p:FatturaElettronicaBody", namespaces=ns)
    if not bodies:
        bodies = root.xpath(".//*[local-name()='FatturaElettronicaBody']")

    for body in bodies:
        invoice = ParsedInvoice()
        invoice.cedente_denominazione = cedente_denominazione
        invoice.cedente_piva = cedente_piva
        invoice.cedente_cf = cedente_cf
        invoice.cedente_regime_fiscale = cedente_regime
        invoice.cessionario_denominazione = cessionario_denominazione
        invoice.cessionario_piva = cessionario_piva
        invoice.cessionario_cf = cessionario_cf
        invoice.identificativo_sdi = identificativo_sdi

        # DatiGeneraliDocumento
        tipo_doc = _text(body, ".//p:DatiGeneraliDocumento/p:TipoDocumento", ns)
        if not tipo_doc:
            tipo_doc = _text(body, ".//*[local-name()='TipoDocumento']", {})
        invoice.tipo_documento_codice = tipo_doc
        invoice.tipo_documento_tipo = TIPO_DOCUMENTO_MAP.get(tipo_doc, "fattura")

        invoice.valuta = _text(body, ".//p:DatiGeneraliDocumento/p:Divisa", ns) or "EUR"
        invoice.numero_fattura = _text(body, ".//p:DatiGeneraliDocumento/p:Numero", ns)
        invoice.data_fattura = _parse_date(
            _text(body, ".//p:DatiGeneraliDocumento/p:Data", ns)
        )

        # ImportoTotaleDocumento
        importo_totale_str = _text(body, ".//p:DatiGeneraliDocumento/p:ImportoTotaleDocumento", ns)
        if importo_totale_str:
            invoice.importo_totale = _parse_decimal(importo_totale_str)

        # Dettaglio linee
        linee = body.xpath(".//p:DettaglioLinee", namespaces=ns)
        if not linee:
            linee = body.xpath(".//*[local-name()='DettaglioLinee']")

        imponibile_sum = Decimal("0")
        for linea in linee:
            num_linea = _text(linea, "p:NumeroLinea", ns) or _text(linea, "*[local-name()='NumeroLinea']", {})
            descrizione = _text(linea, "p:Descrizione", ns) or _text(linea, "*[local-name()='Descrizione']", {})
            prezzo_unitario = _parse_decimal(
                _text(linea, "p:PrezzoUnitario", ns) or _text(linea, "*[local-name()='PrezzoUnitario']", {})
            )
            prezzo_totale = _parse_decimal(
                _text(linea, "p:PrezzoTotale", ns) or _text(linea, "*[local-name()='PrezzoTotale']", {})
            )
            aliquota_iva = _parse_decimal(
                _text(linea, "p:AliquotaIVA", ns) or _text(linea, "*[local-name()='AliquotaIVA']", {})
            )

            imponibile_sum += prezzo_totale

            invoice.linee_dettaglio.append({
                "numero_linea": num_linea,
                "descrizione": descrizione,
                "prezzo_unitario": str(prezzo_unitario),
                "prezzo_totale": str(prezzo_totale),
                "aliquota_iva": str(aliquota_iva),
            })

        # Riepilogo IVA (DatiRiepilogo)
        riepiloghi = body.xpath(".//p:DatiRiepilogo", namespaces=ns)
        if not riepiloghi:
            riepiloghi = body.xpath(".//*[local-name()='DatiRiepilogo']")

        iva_sum = Decimal("0")
        imponibile_riepilogo = Decimal("0")
        for riepilogo in riepiloghi:
            aliquota = _parse_decimal(
                _text(riepilogo, "p:AliquotaIVA", ns) or _text(riepilogo, "*[local-name()='AliquotaIVA']", {})
            )
            imponibile = _parse_decimal(
                _text(riepilogo, "p:ImponibileImporto", ns) or _text(riepilogo, "*[local-name()='ImponibileImporto']", {})
            )
            imposta = _parse_decimal(
                _text(riepilogo, "p:Imposta", ns) or _text(riepilogo, "*[local-name()='Imposta']", {})
            )

            iva_sum += imposta
            imponibile_riepilogo += imponibile

            invoice.riepilogo_iva.append({
                "aliquota": str(aliquota),
                "imponibile": str(imponibile),
                "imposta": str(imposta),
            })

        invoice.imponibile_totale = imponibile_riepilogo or imponibile_sum
        invoice.iva_totale = iva_sum

        # If importo_totale not in XML, calculate
        if invoice.importo_totale == Decimal("0"):
            invoice.importo_totale = invoice.imponibile_totale + invoice.iva_totale

        # Pagamento
        pagamenti = body.xpath(".//p:DatiPagamento", namespaces=ns)
        if not pagamenti:
            pagamenti = body.xpath(".//*[local-name()='DatiPagamento']")

        if pagamenti:
            pag = pagamenti[0]
            invoice.condizioni_pagamento = (
                _text(pag, "p:CondizioniPagamento", ns)
                or _text(pag, "*[local-name()='CondizioniPagamento']", {})
            )

            # DettaglioPagamento (prendi il primo)
            dettagli = pag.xpath(".//p:DettaglioPagamento", namespaces=ns)
            if not dettagli:
                dettagli = pag.xpath(".//*[local-name()='DettaglioPagamento']")

            if dettagli:
                det = dettagli[0]
                mp = (
                    _text(det, "p:ModalitaPagamento", ns)
                    or _text(det, "*[local-name()='ModalitaPagamento']", {})
                )
                invoice.modalita_pagamento = mp
                invoice.modalita_pagamento_desc = MODALITA_PAGAMENTO_MAP.get(mp, mp)

                invoice.data_scadenza_pagamento = _parse_date(
                    _text(det, "p:DataScadenzaPagamento", ns)
                    or _text(det, "*[local-name()='DataScadenzaPagamento']", {})
                )
                invoice.iban_pagamento = (
                    _text(det, "p:IBAN", ns)
                    or _text(det, "*[local-name()='IBAN']", {})
                )

        # Allegati (cerca PDF)
        allegati = body.xpath(".//p:Allegati", namespaces=ns)
        if not allegati:
            allegati = body.xpath(".//*[local-name()='Allegati']")

        for allegato in allegati:
            nome = (
                _text(allegato, "p:NomeAttachment", ns)
                or _text(allegato, "*[local-name()='NomeAttachment']", {})
            )
            formato = (
                _text(allegato, "p:FormatoAttachment", ns)
                or _text(allegato, "*[local-name()='FormatoAttachment']", {})
            )
            attachment_data = (
                _text(allegato, "p:Attachment", ns)
                or _text(allegato, "*[local-name()='Attachment']", {})
            )

            if attachment_data and (
                formato.upper() == "PDF"
                or nome.lower().endswith(".pdf")
            ):
                invoice.pdf_allegato_base64 = attachment_data
                invoice.pdf_allegato_nome = nome
                break  # Take first PDF

        results.append(invoice)

    return results
