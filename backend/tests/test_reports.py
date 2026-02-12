"""Tests for the Reports module."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.models.enums import (
    ReportExecutionStatus, ReportFormat, ReportFrequency, ReportType,
)
from app.models.report_definition import ReportDefinition
from app.models.report_execution import ReportExecution
from app.models.report_schedule import ReportSchedule
from app.services.report_generator import generate_report_data


class TestReportModels:
    """Test model creation and defaults."""

    def test_report_definition_defaults(self):
        rd = ReportDefinition(
            nome="Test Report",
            tipo=ReportType.SALDI_CONTI,
        )
        assert rd.nome == "Test Report"
        assert rd.tipo == ReportType.SALDI_CONTI
        assert rd.is_system is False
        assert rd.is_preferito is False
        assert rd.sort_order == 0

    def test_report_execution_defaults(self):
        re = ReportExecution(
            company_id=uuid.uuid4(),
            nome="Test Execution",
            tipo="saldi_conti",
            formato=ReportFormat.PDF,
        )
        assert re.stato == ReportExecutionStatus.IN_CODA
        assert re.nome == "Test Execution"
        assert re.formato == ReportFormat.PDF

    def test_report_schedule_defaults(self):
        rs = ReportSchedule(
            company_id=uuid.uuid4(),
            report_definition_id=uuid.uuid4(),
            nome="Test Schedule",
            frequenza=ReportFrequency.MENSILE,
        )
        assert rs.attivo is True
        assert rs.frequenza == ReportFrequency.MENSILE


class TestReportEnums:
    """Test enum values."""

    def test_report_type_values(self):
        assert ReportType.SALDI_CONTI.value == "saldi_conti"
        assert ReportType.MOVIMENTI.value == "movimenti"
        assert ReportType.PERSONALIZZATO.value == "personalizzato"
        assert len(ReportType) == 10

    def test_report_format_values(self):
        assert ReportFormat.PDF.value == "pdf"
        assert ReportFormat.XLSX.value == "xlsx"
        assert ReportFormat.CSV.value == "csv"
        assert len(ReportFormat) == 3

    def test_report_execution_status_values(self):
        assert ReportExecutionStatus.IN_CODA.value == "in_coda"
        assert ReportExecutionStatus.COMPLETATO.value == "completato"
        assert len(ReportExecutionStatus) == 4

    def test_report_frequency_values(self):
        assert ReportFrequency.GIORNALIERO.value == "giornaliero"
        assert ReportFrequency.TRIMESTRALE.value == "trimestrale"
        assert len(ReportFrequency) == 4


class TestReportGenerator:
    """Test report data generation."""

    def test_generate_personalizzato(self):
        mock_db = MagicMock()
        company_id = uuid.uuid4()
        result = generate_report_data(mock_db, company_id, "personalizzato")
        assert "headers" in result
        assert "rows" in result
        assert "totals" in result
        assert "metadata" in result

    def test_generate_unknown_type_falls_back_to_personalizzato(self):
        mock_db = MagicMock()
        company_id = uuid.uuid4()
        result = generate_report_data(mock_db, company_id, "tipo_inesistente")
        assert result["metadata"]["titolo"] == "Report Personalizzato"

    def test_generate_saldi_conti(self):
        mock_db = MagicMock()
        company_id = uuid.uuid4()

        # Create mock accounts
        mock_account = MagicMock()
        mock_account.nickname = "Conto BPM"
        mock_account.iban = "IT60X0542811101000000123456"
        mock_account.current_balance = Decimal("150000.00")
        mock_account.available_balance = Decimal("148000.00")
        mock_account.balance_date = date.today()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_account]
        mock_db.query.return_value = mock_query

        result = generate_report_data(mock_db, company_id, "saldi_conti")
        assert result["metadata"]["titolo"] == "Situazione Saldi"
        assert len(result["rows"]) == 1
        assert result["rows"][0]["conto"] == "Conto BPM"
        assert result["totals"]["saldo_contabile"] == Decimal("150000.00")


class TestReportFormatter:
    """Test report formatting."""

    def test_fmt_value_currency(self):
        from app.services.report_formatter import _fmt_value
        assert _fmt_value(Decimal("1234.56"), "currency") == "1.234,56"
        assert _fmt_value(Decimal("0.00"), "currency") == "0,00"

    def test_fmt_value_date(self):
        from app.services.report_formatter import _fmt_value
        assert _fmt_value(date(2026, 2, 11)) == "11/02/2026"

    def test_fmt_value_percentage(self):
        from app.services.report_formatter import _fmt_value
        assert _fmt_value(85.5, "percentage") == "85.5%"

    def test_fmt_value_none(self):
        from app.services.report_formatter import _fmt_value
        assert _fmt_value(None) == ""

    def test_generate_filename(self):
        from app.services.report_formatter import generate_filename
        name = generate_filename("saldi_conti", "pdf", "azienda")
        assert name.startswith("saldi_conti_")
        assert name.endswith("_azienda.pdf")


class TestReportService:
    """Test service layer functions."""

    def test_calcola_prossima_esecuzione_giornaliero(self):
        from app.services.report_service import _calcola_prossima_esecuzione
        result = _calcola_prossima_esecuzione(ReportFrequency.GIORNALIERO)
        assert result > datetime.now(timezone.utc)

    def test_calcola_prossima_esecuzione_mensile(self):
        from app.services.report_service import _calcola_prossima_esecuzione
        result = _calcola_prossima_esecuzione(ReportFrequency.MENSILE)
        assert result > datetime.now(timezone.utc)
