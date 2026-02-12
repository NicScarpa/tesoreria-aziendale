"""Test per il parser FatturaPA."""
import os

import pytest
from datetime import date
from decimal import Decimal

from app.services.parsers.fatturapa_parser import parse, ParsedInvoice

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _read_fixture(name: str) -> bytes:
    with open(os.path.join(FIXTURES_DIR, name), "rb") as f:
        return f.read()


# =====================================================================
# TD01 STANDARD
# =====================================================================


class TestParseTD01Standard:
    """Test fatturapa_td01.xml - Fattura standard Tecnoparts SRL."""

    def test_returns_single_invoice(self):
        results = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")
        assert len(results) == 1
        assert isinstance(results[0], ParsedInvoice)

    def test_tipo_documento(self):
        inv = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")[0]
        assert inv.tipo_documento_codice == "TD01"
        assert inv.tipo_documento_tipo == "fattura"

    def test_cedente(self):
        inv = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")[0]
        assert inv.cedente_denominazione == "Tecnoparts SRL"
        assert inv.cedente_piva == "02345678901"
        assert inv.cedente_cf == "02345678901"

    def test_cessionario(self):
        inv = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")[0]
        assert inv.cessionario_denominazione == "Azienda Test SRL"
        assert inv.cessionario_piva == "01234567890"

    def test_numero_data(self):
        inv = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")[0]
        assert inv.numero_fattura == "FPA-2026-001"
        assert inv.data_fattura == date(2026, 1, 15)

    def test_importi(self):
        inv = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")[0]
        assert inv.importo_totale == Decimal("12200.00")
        assert inv.imponibile_totale == Decimal("10000.00")
        assert inv.iva_totale == Decimal("2200.00")
        assert inv.valuta == "EUR"

    def test_pagamento(self):
        inv = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")[0]
        assert inv.modalita_pagamento == "MP05"
        assert inv.modalita_pagamento_desc == "bonifico"
        assert inv.data_scadenza_pagamento == date(2026, 2, 15)
        assert inv.iban_pagamento == "IT60X0542811101000000123456"
        assert inv.condizioni_pagamento == "TP02"

    def test_linee_dettaglio(self):
        inv = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")[0]
        assert len(inv.linee_dettaglio) == 2
        linea1 = inv.linee_dettaglio[0]
        assert linea1["descrizione"] == "Componenti elettronici lotto A"
        assert linea1["prezzo_totale"] == "5000.00"
        assert linea1["aliquota_iva"] == "22.00"

        linea2 = inv.linee_dettaglio[1]
        assert linea2["descrizione"] == "Componenti elettronici lotto B"
        assert linea2["prezzo_totale"] == "5000.00"

    def test_riepilogo_iva(self):
        inv = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")[0]
        assert len(inv.riepilogo_iva) == 1
        rie = inv.riepilogo_iva[0]
        assert rie["aliquota"] == "22.00"
        assert rie["imponibile"] == "10000.00"
        assert rie["imposta"] == "2200.00"

    def test_identificativo_sdi(self):
        inv = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")[0]
        assert inv.identificativo_sdi == "00001"

    def test_no_allegato(self):
        inv = parse(_read_fixture("fatturapa_td01.xml"), "fatturapa_td01.xml")[0]
        assert inv.pdf_allegato_base64 == ""
        assert inv.pdf_allegato_nome == ""


# =====================================================================
# TD04 NOTA DI CREDITO
# =====================================================================


class TestParseTD04CreditNote:
    """Test fatturapa_td04.xml - Nota di credito."""

    def test_tipo_documento(self):
        inv = parse(_read_fixture("fatturapa_td04.xml"), "fatturapa_td04.xml")[0]
        assert inv.tipo_documento_codice == "TD04"
        assert inv.tipo_documento_tipo == "nota_credito"

    def test_importi_nota_credito(self):
        inv = parse(_read_fixture("fatturapa_td04.xml"), "fatturapa_td04.xml")[0]
        assert inv.importo_totale == Decimal("1220.00")
        assert inv.imponibile_totale == Decimal("1000.00")
        assert inv.iva_totale == Decimal("220.00")

    def test_numero_fattura(self):
        inv = parse(_read_fixture("fatturapa_td04.xml"), "fatturapa_td04.xml")[0]
        assert inv.numero_fattura == "NC-2026-001"
        assert inv.data_fattura == date(2026, 1, 20)

    def test_cedente_same_as_td01(self):
        inv = parse(_read_fixture("fatturapa_td04.xml"), "fatturapa_td04.xml")[0]
        assert inv.cedente_denominazione == "Tecnoparts SRL"
        assert inv.cedente_piva == "02345678901"

    def test_single_linea_dettaglio(self):
        inv = parse(_read_fixture("fatturapa_td04.xml"), "fatturapa_td04.xml")[0]
        assert len(inv.linee_dettaglio) == 1
        assert inv.linee_dettaglio[0]["descrizione"] == "Reso componenti difettosi"


# =====================================================================
# MULTI-BODY
# =====================================================================


class TestParseMultiBody:
    """Test fatturapa_multi_body.xml - 2 FatturaElettronicaBody."""

    def test_returns_two_invoices(self):
        results = parse(_read_fixture("fatturapa_multi_body.xml"), "fatturapa_multi_body.xml")
        assert len(results) == 2

    def test_first_body(self):
        results = parse(_read_fixture("fatturapa_multi_body.xml"), "fatturapa_multi_body.xml")
        inv1 = results[0]
        assert inv1.numero_fattura == "FPA-2026-010"
        assert inv1.importo_totale == Decimal("6100.00")
        assert inv1.imponibile_totale == Decimal("5000.00")
        assert inv1.iva_totale == Decimal("1100.00")

    def test_second_body(self):
        results = parse(_read_fixture("fatturapa_multi_body.xml"), "fatturapa_multi_body.xml")
        inv2 = results[1]
        assert inv2.numero_fattura == "FPA-2026-011"
        assert inv2.importo_totale == Decimal("2440.00")
        assert inv2.imponibile_totale == Decimal("2000.00")
        assert inv2.iva_totale == Decimal("440.00")

    def test_shared_header(self):
        results = parse(_read_fixture("fatturapa_multi_body.xml"), "fatturapa_multi_body.xml")
        # Header is shared across bodies
        for inv in results:
            assert inv.cedente_denominazione == "Tecnoparts SRL"
            assert inv.cedente_piva == "02345678901"
            assert inv.cessionario_denominazione == "Azienda Test SRL"

    def test_both_are_td01(self):
        results = parse(_read_fixture("fatturapa_multi_body.xml"), "fatturapa_multi_body.xml")
        for inv in results:
            assert inv.tipo_documento_codice == "TD01"
            assert inv.tipo_documento_tipo == "fattura"


# =====================================================================
# CON ALLEGATO PDF
# =====================================================================


class TestParseConAllegato:
    """Test fatturapa_con_allegato.xml - Fattura con allegato PDF base64."""

    def test_allegato_present(self):
        inv = parse(_read_fixture("fatturapa_con_allegato.xml"), "fatturapa_con_allegato.xml")[0]
        assert inv.pdf_allegato_base64 != ""
        assert inv.pdf_allegato_base64 == "dGVzdCBQREYgY29udGVudA=="

    def test_allegato_nome(self):
        inv = parse(_read_fixture("fatturapa_con_allegato.xml"), "fatturapa_con_allegato.xml")[0]
        assert inv.pdf_allegato_nome == "fattura.pdf"

    def test_importi(self):
        inv = parse(_read_fixture("fatturapa_con_allegato.xml"), "fatturapa_con_allegato.xml")[0]
        assert inv.importo_totale == Decimal("610.00")
        assert inv.imponibile_totale == Decimal("500.00")
        assert inv.iva_totale == Decimal("110.00")


# =====================================================================
# EDGE CASES
# =====================================================================


class TestParseEdgeCases:
    """Test casi limite e input non validi."""

    def test_parse_invalid_xml_raises(self):
        """Garbage bytes should raise an exception from lxml."""
        with pytest.raises(Exception):
            parse(b"this is not xml at all!!!", "garbage.xml")

    def test_parse_empty_xml_no_bodies(self):
        """Minimal valid XML without FatturaElettronicaBody returns empty list."""
        empty_xml = b'<?xml version="1.0" encoding="UTF-8"?><root></root>'
        results = parse(empty_xml, "empty.xml")
        assert results == []

    def test_parse_valid_xml_without_fattura_namespace(self):
        """Valid XML but not a FatturaPA document returns empty list."""
        xml = b'<?xml version="1.0"?><document><item>test</item></document>'
        results = parse(xml, "not_fatturapa.xml")
        assert results == []

    def test_parse_with_empty_bytes(self):
        """Empty bytes should raise an exception."""
        with pytest.raises(Exception):
            parse(b"", "empty.xml")
