"""Test per i parser CBI e SEPA (camt.053, camt.054, pain.002, CBI Rendicontazione)."""
import os

import pytest
from datetime import date
from decimal import Decimal

from app.services.parsers.cbi_sepa_parsers import (
    CAMT053Parser,
    CAMT053Statement,
    CAMT054Parser,
    PAIN002Parser,
    PaymentStatusEntry,
    CBIRendicontazioneParser,
    CBIRendicontazioneRecord,
    validate_sepa_xml,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _read_fixture(name: str) -> bytes:
    with open(os.path.join(FIXTURES_DIR, name), "rb") as f:
        return f.read()


# =====================================================================
# CAMT.053 - Bank-to-Customer Statement
# =====================================================================


class TestCAMT053Parser:
    """Test camt053_sample.xml - 1 statement, 3 entries."""

    def test_parse_returns_one_statement(self):
        parser = CAMT053Parser()
        statements = parser.parse(_read_fixture("camt053_sample.xml"))
        assert len(statements) == 1
        assert isinstance(statements[0], CAMT053Statement)

    def test_account_iban(self):
        parser = CAMT053Parser()
        stmt = parser.parse(_read_fixture("camt053_sample.xml"))[0]
        assert stmt.account_iban == "IT60X0542811101000000123456"

    def test_account_currency(self):
        parser = CAMT053Parser()
        stmt = parser.parse(_read_fixture("camt053_sample.xml"))[0]
        assert stmt.account_currency == "EUR"

    def test_statement_id(self):
        parser = CAMT053Parser()
        stmt = parser.parse(_read_fixture("camt053_sample.xml"))[0]
        assert stmt.statement_id == "STMT-001"

    def test_opening_balance(self):
        parser = CAMT053Parser()
        stmt = parser.parse(_read_fixture("camt053_sample.xml"))[0]
        assert stmt.opening_balance == Decimal("150000.00")

    def test_closing_balance(self):
        parser = CAMT053Parser()
        stmt = parser.parse(_read_fixture("camt053_sample.xml"))[0]
        assert stmt.closing_balance == Decimal("155500.00")

    def test_three_entries(self):
        parser = CAMT053Parser()
        stmt = parser.parse(_read_fixture("camt053_sample.xml"))[0]
        assert len(stmt.entries) == 3

    def test_first_entry_inflow_abc_srl(self):
        parser = CAMT053Parser()
        entry = parser.parse(_read_fixture("camt053_sample.xml"))[0].entries[0]
        assert entry["amount"] == Decimal("15000.00")
        assert entry["direction"] == "inflow"
        assert entry["counterpart_name"] == "ABC SRL"
        assert entry["reference"] == "REF-001"
        assert entry["description"] == "Pagamento fattura FV-2026-001"
        assert entry["booking_date"] == date(2026, 2, 1)

    def test_second_entry_outflow_mario_rossi(self):
        parser = CAMT053Parser()
        entry = parser.parse(_read_fixture("camt053_sample.xml"))[0].entries[1]
        assert entry["amount"] == Decimal("3500.00")
        assert entry["direction"] == "outflow"
        assert entry["counterpart_name"] == "Mario Rossi"
        assert entry["reference"] == "REF-002"

    def test_third_entry_inflow_xyz_trading(self):
        parser = CAMT053Parser()
        entry = parser.parse(_read_fixture("camt053_sample.xml"))[0].entries[2]
        assert entry["amount"] == Decimal("8000.00")
        assert entry["direction"] == "inflow"
        assert entry["counterpart_name"] == "XYZ Trading SPA"
        assert entry["reference"] == "REF-003"

    def test_all_entries_have_value_date(self):
        parser = CAMT053Parser()
        entries = parser.parse(_read_fixture("camt053_sample.xml"))[0].entries
        for entry in entries:
            assert entry["value_date"] == date(2026, 2, 1)

    def test_all_entries_currency_eur(self):
        parser = CAMT053Parser()
        entries = parser.parse(_read_fixture("camt053_sample.xml"))[0].entries
        for entry in entries:
            assert entry["currency"] == "EUR"


# =====================================================================
# PAIN.002 - Payment Status Report
# =====================================================================


class TestPAIN002Parser:
    """Test pain002_sample.xml - 2 TxInfAndSts."""

    def test_parse_returns_two_entries(self):
        parser = PAIN002Parser()
        entries = parser.parse(_read_fixture("pain002_sample.xml"))
        assert len(entries) == 2
        assert isinstance(entries[0], PaymentStatusEntry)

    def test_first_entry_accepted(self):
        parser = PAIN002Parser()
        entry = parser.parse(_read_fixture("pain002_sample.xml"))[0]
        assert entry.original_instruction_id == "INSTR-001"
        assert entry.original_end_to_end_id == "E2E-PAYMENT-001"
        assert entry.status == "ACCP"
        assert entry.reason_code == ""

    def test_second_entry_rejected(self):
        parser = PAIN002Parser()
        entry = parser.parse(_read_fixture("pain002_sample.xml"))[1]
        assert entry.original_instruction_id == "INSTR-002"
        assert entry.original_end_to_end_id == "E2E-PAYMENT-002"
        assert entry.status == "RJCT"
        assert entry.reason_code == "AC04"
        assert entry.reason_text == "Conto chiuso"


# =====================================================================
# CBI Rendicontazione - Fixed-width format
# =====================================================================


class TestCBIRendicontazioneParser:
    """Test CBI Rendicontazione parser con dati mock fixed-width."""

    @staticmethod
    def _build_cbi_line(tipo: str = "14", data_ymd: str = "260201",
                        segno: str = "C", importo_cents: str = "0000001500000",
                        causale: str = "48", riferimento: str = "RIF-TEST-001             ",
                        descrizione: str = "") -> str:
        """Build a CBI fixed-width record (120 chars minimum)."""
        # tipo (2) + padding (8) + date AAMMGG (6) + segno (1) + importo 13 + causale 2 + riferimento 23 + descrizione 58
        line = tipo
        line += " " * 8  # padding to position 10
        line += data_ymd  # positions 10-15: AAMMGG
        line += segno     # position 16
        line += importo_cents  # positions 17-29: importo in centesimi
        line += causale   # positions 30-31
        line += riferimento.ljust(23)  # positions 32-54
        line += descrizione.ljust(58)  # positions 55-112
        # Pad to at least 113 chars
        line = line.ljust(120)
        return line

    def test_parse_single_record(self):
        parser = CBIRendicontazioneParser()
        line = self._build_cbi_line(
            tipo="14", data_ymd="260201", segno="C",
            importo_cents="0000001500000", causale="48",
            riferimento="RIF-TEST-001",
            descrizione="Bonifico da ABC SRL",
        )
        records = parser.parse(line.encode("utf-8"))
        assert len(records) == 1

    def test_record_fields(self):
        parser = CBIRendicontazioneParser()
        line = self._build_cbi_line(
            tipo="14", data_ymd="260201", segno="C",
            importo_cents="0000001500000", causale="48",
            riferimento="RIF-TEST-001",
            descrizione="Bonifico da ABC SRL",
        )
        record = parser.parse(line.encode("utf-8"))[0]
        assert isinstance(record, CBIRendicontazioneRecord)
        assert record.tipo_record == "14"
        assert record.segno == "C"
        assert record.importo == Decimal("15000.00")
        assert record.causale == "48"
        assert record.data_operazione == date(2026, 2, 1)

    def test_parse_debit_record(self):
        parser = CBIRendicontazioneParser()
        line = self._build_cbi_line(
            tipo="14", data_ymd="260215", segno="D",
            importo_cents="0000000350000", causale="27",
            riferimento="PAG-STIP-001",
            descrizione="Stipendio febbraio",
        )
        record = parser.parse(line.encode("utf-8"))[0]
        assert record.segno == "D"
        assert record.importo == Decimal("3500.00")
        assert record.data_operazione == date(2026, 2, 15)

    def test_parse_multiple_records(self):
        parser = CBIRendicontazioneParser()
        lines = "\n".join([
            self._build_cbi_line(tipo="14", segno="C", importo_cents="0000001000000"),
            self._build_cbi_line(tipo="14", segno="D", importo_cents="0000000500000"),
            self._build_cbi_line(tipo="14", segno="C", importo_cents="0000000200000"),
        ])
        records = parser.parse(lines.encode("utf-8"))
        assert len(records) == 3

    def test_additional_info_appended(self):
        """Record types 20/30/40/50/51/70 append to the description of the current record."""
        parser = CBIRendicontazioneParser()
        line14 = self._build_cbi_line(
            tipo="14", descrizione="Bonifico iniziale",
        )
        line20 = "20" + "Info aggiuntiva riga 20".ljust(118)
        content = (line14 + "\n" + line20).encode("utf-8")
        records = parser.parse(content)
        assert len(records) == 1
        assert "Info aggiuntiva riga 20" in records[0].descrizione

    def test_skip_header_footer(self):
        """IB (header) and EF (footer) are not parsed as records."""
        parser = CBIRendicontazioneParser()
        header = "IB" + " " * 118
        footer = "EF" + " " * 118
        record = self._build_cbi_line(tipo="14")
        content = (header + "\n" + record + "\n" + footer).encode("utf-8")
        records = parser.parse(content)
        assert len(records) == 1
        assert records[0].tipo_record == "14"

    def test_empty_input(self):
        parser = CBIRendicontazioneParser()
        records = parser.parse(b"")
        assert records == []

    def test_iso_encoding(self):
        """CBI files may use ISO-8859-1 encoding."""
        parser = CBIRendicontazioneParser()
        line = self._build_cbi_line(tipo="14", descrizione="Pagamento caf\xe9")
        records = parser.parse(line.encode("iso-8859-1"))
        assert len(records) == 1


# =====================================================================
# validate_sepa_xml
# =====================================================================


class TestValidateSepaXml:
    """Test funzione validate_sepa_xml."""

    def test_validate_camt053_valid(self):
        result = validate_sepa_xml(_read_fixture("camt053_sample.xml"))
        assert result["valid"] is True
        assert result["file_type"] is not None
        assert "camt.053" in result["file_type"]
        assert result["message_id"] == "CAMT053-20260201-001"
        assert result["errors"] == []

    def test_validate_pain002_valid(self):
        result = validate_sepa_xml(_read_fixture("pain002_sample.xml"))
        assert result["valid"] is True
        assert result["file_type"] is not None
        assert "pain.002" in result["file_type"]
        assert result["message_id"] == "PAIN002-20260201-001"

    def test_validate_invalid_xml(self):
        result = validate_sepa_xml(b"this is not xml")
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert result["file_type"] is None

    def test_validate_valid_xml_wrong_namespace(self):
        """Valid XML but not a SEPA document."""
        xml = b'<?xml version="1.0"?><document><item>test</item></document>'
        result = validate_sepa_xml(xml)
        assert result["valid"] is False
        assert any("Namespace" in e or "GrpHdr" in e for e in result["errors"])

    def test_validate_missing_grphdr(self):
        """SEPA namespace present but missing GrpHdr."""
        xml = b'<?xml version="1.0"?><Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02"><BkToCstmrStmt></BkToCstmrStmt></Document>'
        result = validate_sepa_xml(xml)
        assert result["valid"] is False
        assert any("GrpHdr" in e for e in result["errors"])
