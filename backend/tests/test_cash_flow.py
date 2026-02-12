"""Tests for Module 9: Cash Flow."""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models import (
    CashFlowForecast, CashFlowForecastLine, CashFlowScenario, CashFlowAlert,
    ForecastStatus, ForecastType, CashFlowLineType, CashFlowSource,
    ConfidenceLevel, ScenarioAdjustmentType, CashFlowAlertType, AlertStatus,
    Schedule, ScheduleType, ScheduleStatus,
)
from app.services import cash_flow_engine, cash_flow_service


# --- Fixtures ---

@pytest.fixture()
def auth_headers_with_company(client, test_user, test_user_company, test_company) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "Test1234!"})
    tokens = resp.json()
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Company-ID": str(test_company.id),
    }


@pytest.fixture()
def test_forecast(db_session, test_company, test_user) -> CashFlowForecast:
    today = date.today()
    forecast = CashFlowForecast(
        company_id=test_company.id,
        creato_da_user_id=test_user.id,
        nome="Test Forecast",
        descrizione="Test forecast description",
        data_inizio=today - timedelta(days=15),
        data_fine=today + timedelta(days=15),
        saldo_iniziale=Decimal("10000.00"),
        saldo_finale_previsto=Decimal("8500.00"),
        totale_entrate_previste=Decimal("5000.00"),
        totale_uscite_previste=Decimal("6500.00"),
        stato=ForecastStatus.ATTIVA,
        tipo=ForecastType.BASE,
    )
    db_session.add(forecast)
    db_session.flush()
    return forecast


@pytest.fixture()
def test_forecast_lines(db_session, test_forecast) -> list[CashFlowForecastLine]:
    today = date.today()
    lines = []
    running = Decimal("10000.00")

    # 5 past lines (realized)
    for i in range(5):
        importo = Decimal("1000.00")
        running += importo
        line = CashFlowForecastLine(
            forecast_id=test_forecast.id,
            data=today - timedelta(days=10 - i * 2),
            tipo=CashFlowLineType.ENTRATA,
            importo=importo,
            categoria="Incassi Clienti",
            descrizione=f"Incasso test {i}",
            fonte=CashFlowSource.MOVIMENTO_REALE,
            confidenza=ConfidenceLevel.CERTA,
            saldo_progressivo=running,
            is_realizzata=True,
        )
        lines.append(line)

    # 5 future lines (forecasted)
    for i in range(5):
        importo = Decimal("1300.00")
        running -= importo
        line = CashFlowForecastLine(
            forecast_id=test_forecast.id,
            data=today + timedelta(days=i * 3 + 1),
            tipo=CashFlowLineType.USCITA,
            importo=importo,
            categoria="Fornitori",
            descrizione=f"Pagamento test {i}",
            fonte=CashFlowSource.SCADENZA,
            confidenza=ConfidenceLevel.ALTA,
            saldo_progressivo=running,
            is_realizzata=False,
        )
        lines.append(line)

    db_session.add_all(lines)
    db_session.flush()
    return lines


@pytest.fixture()
def test_scenario(db_session, test_forecast) -> CashFlowScenario:
    scenario = CashFlowScenario(
        forecast_id=test_forecast.id,
        nome="Scenario test",
        descrizione="Test scenario",
        tipo_aggiustamento=ScenarioAdjustmentType.AGGIUNTA,
        importo_modificato=Decimal("5000.00"),
        tipo_movimento=CashFlowLineType.ENTRATA,
        categoria="Incassi Clienti",
        data_modificata=date.today() + timedelta(days=5),
        attivo=True,
    )
    db_session.add(scenario)
    db_session.flush()
    return scenario


@pytest.fixture()
def test_alert(db_session, test_company, test_forecast) -> CashFlowAlert:
    alert = CashFlowAlert(
        company_id=test_company.id,
        forecast_id=test_forecast.id,
        tipo=CashFlowAlertType.SOTTO_SOGLIA_MINIMA,
        data_prevista=date.today() + timedelta(days=10),
        saldo_previsto=Decimal("5000.00"),
        soglia=Decimal("10000.00"),
        messaggio="Test alert: saldo sotto soglia",
        stato=AlertStatus.ATTIVO,
    )
    db_session.add(alert)
    db_session.flush()
    return alert


@pytest.fixture()
def test_schedule_for_cf(db_session, test_company, test_bank_account) -> Schedule:
    s = Schedule(
        company_id=test_company.id,
        tipo=ScheduleType.PASSIVA,
        stato=ScheduleStatus.APERTA,
        descrizione="Fattura fornitore test CF",
        importo_totale=Decimal("3000.00"),
        importo_pagato=Decimal("0"),
        data_scadenza=date.today() + timedelta(days=10),
        bank_account_id=test_bank_account.id,
    )
    db_session.add(s)
    db_session.flush()
    return s


# --- Engine Tests ---

class TestCashFlowEngine:

    def test_projection_returns_correct_structure(
        self, db_session, test_company, test_bank_account, test_transaction
    ):
        result = cash_flow_engine.generate_cash_flow_projection(
            db_session, test_company.id
        )
        assert "saldo_iniziale" in result
        assert "saldo_finale" in result
        assert "totale_entrate" in result
        assert "totale_uscite" in result
        assert "lines" in result
        assert isinstance(result["lines"], list)

    def test_projection_includes_transactions(
        self, db_session, test_company, test_bank_account, test_transaction
    ):
        result = cash_flow_engine.generate_cash_flow_projection(
            db_session, test_company.id,
            data_inizio=date.today() - timedelta(days=1),
            data_fine=date.today() + timedelta(days=1),
        )
        tx_lines = [l for l in result["lines"] if l["fonte"] == "movimento_reale"]
        assert len(tx_lines) >= 1

    def test_projection_includes_schedules(
        self, db_session, test_company, test_bank_account, test_schedule_for_cf
    ):
        result = cash_flow_engine.generate_cash_flow_projection(
            db_session, test_company.id,
            data_inizio=date.today(),
            data_fine=date.today() + timedelta(days=30),
        )
        sched_lines = [l for l in result["lines"] if l["fonte"] == "scadenza"]
        assert len(sched_lines) >= 1
        assert sched_lines[0]["importo"] == Decimal("3000.00")

    def test_running_balance_is_consistent(
        self, db_session, test_company, test_bank_account, test_transaction
    ):
        result = cash_flow_engine.generate_cash_flow_projection(
            db_session, test_company.id,
            data_inizio=date.today() - timedelta(days=1),
            data_fine=date.today() + timedelta(days=1),
        )
        if result["lines"]:
            last_line = result["lines"][-1]
            assert last_line["saldo_progressivo"] == result["saldo_finale"]

    def test_confidence_by_days(self):
        assert cash_flow_engine._confidence_by_days(3) == ConfidenceLevel.CERTA
        assert cash_flow_engine._confidence_by_days(15) == ConfidenceLevel.ALTA
        assert cash_flow_engine._confidence_by_days(60) == ConfidenceLevel.MEDIA
        assert cash_flow_engine._confidence_by_days(120) == ConfidenceLevel.BASSA

    def test_detect_alerts(self, db_session, test_company):
        lines = [
            {"data": date.today() + timedelta(days=5), "tipo": "uscita",
             "importo": Decimal("5000"), "saldo_progressivo": Decimal("8000")},
            {"data": date.today() + timedelta(days=10), "tipo": "uscita",
             "importo": Decimal("5000"), "saldo_progressivo": Decimal("-2000")},
        ]
        alerts = cash_flow_engine.detect_alerts(
            db_session, test_company.id, lines,
            min_cash_threshold=Decimal("10000"),
            critical_cash_threshold=Decimal("0"),
        )
        assert len(alerts) == 2
        assert alerts[0]["tipo"] == "sotto_soglia_minima"
        assert alerts[1]["tipo"] == "saldo_negativo"


class TestCashFlowVariance:

    def test_variance_with_forecast(
        self, db_session, test_forecast, test_forecast_lines, test_company, test_bank_account
    ):
        result = cash_flow_engine.calculate_variance(db_session, test_forecast.id)
        assert result["forecast_id"] == test_forecast.id
        assert "accuracy" in result
        assert "lines" in result


class TestCashFlowRunway:

    def test_runway_calculation(
        self, db_session, test_company, test_bank_account, test_transaction
    ):
        result = cash_flow_engine.calculate_runway(db_session, test_company.id)
        assert "saldo_attuale" in result
        assert "burn_rate_mensile" in result
        assert "runway_mesi" in result
        assert result["saldo_attuale"] == test_bank_account.current_balance


class TestCashFlowSeasonality:

    def test_seasonality_returns_12_months(
        self, db_session, test_company, test_bank_account, test_transaction
    ):
        result = cash_flow_engine.calculate_seasonality(db_session, test_company.id)
        assert len(result["mesi"]) == 12
        assert result["periodo_analisi_mesi"] == 12


class TestCashFlowTrends:

    def test_trends_calculation(
        self, db_session, test_company, test_bank_account, test_transaction
    ):
        result = cash_flow_engine.calculate_trends(db_session, test_company.id, mesi=3)
        assert "punti" in result
        assert result["raggruppamento"] == "mensile"
        assert result["trend_entrate"] in ("crescente", "decrescente", "stabile")


class TestScenarios:

    def test_apply_scenarios_adds_line(
        self, db_session, test_forecast, test_forecast_lines, test_scenario
    ):
        result = cash_flow_engine.apply_scenarios(db_session, test_forecast.id)
        assert result["saldo_finale"] > test_forecast.saldo_finale_previsto
        scenario_lines = [l for l in result["lines"] if l.get("fonte_id") == str(test_scenario.id)]
        assert len(scenario_lines) == 1


# --- API Tests ---

class TestCashFlowAPI:

    def test_get_projection(self, client, auth_headers_with_company, test_bank_account):
        resp = client.get("/api/v1/cashflow", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert "saldo_iniziale" in data
        assert "lines" in data

    def test_get_summary(self, client, auth_headers_with_company, test_bank_account):
        resp = client.get("/api/v1/cashflow/summary", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert "saldo_attuale" in data
        assert "previsione_7gg" in data

    def test_create_forecast(self, client, auth_headers_with_company, test_bank_account):
        today = date.today()
        resp = client.post(
            "/api/v1/cashflow/forecasts",
            headers=auth_headers_with_company,
            json={
                "nome": "Test Previsione API",
                "data_inizio": today.isoformat(),
                "data_fine": (today + timedelta(days=30)).isoformat(),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nome"] == "Test Previsione API"
        assert data["stato"] == "bozza"

    def test_list_forecasts(self, client, auth_headers_with_company, test_forecast):
        resp = client.get("/api/v1/cashflow/forecasts", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_get_forecast_detail(self, client, auth_headers_with_company, test_forecast, test_forecast_lines):
        resp = client.get(
            f"/api/v1/cashflow/forecasts/{test_forecast.id}",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["nome"] == "Test Forecast"
        assert len(data["lines"]) == len(test_forecast_lines)

    def test_update_forecast(self, client, auth_headers_with_company, test_forecast):
        resp = client.put(
            f"/api/v1/cashflow/forecasts/{test_forecast.id}",
            headers=auth_headers_with_company,
            json={"nome": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Updated Name"

    def test_delete_forecast(self, client, auth_headers_with_company, test_forecast):
        resp = client.delete(
            f"/api/v1/cashflow/forecasts/{test_forecast.id}",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 204

    def test_forecast_not_found(self, client, auth_headers_with_company):
        fake_id = uuid.uuid4()
        resp = client.get(
            f"/api/v1/cashflow/forecasts/{fake_id}",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 404


class TestScenarioAPI:

    def test_create_scenario(self, client, auth_headers_with_company, test_forecast):
        today = date.today()
        resp = client.post(
            f"/api/v1/cashflow/forecasts/{test_forecast.id}/scenarios",
            headers=auth_headers_with_company,
            json={
                "nome": "Nuovo scenario",
                "tipo_aggiustamento": "aggiunta",
                "importo_modificato": 5000,
                "tipo_movimento": "entrata",
                "data_modificata": (today + timedelta(days=5)).isoformat(),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nome"] == "Nuovo scenario"

    def test_list_scenarios(self, client, auth_headers_with_company, test_forecast, test_scenario):
        resp = client.get(
            f"/api/v1/cashflow/forecasts/{test_forecast.id}/scenarios",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_apply_scenarios(
        self, client, auth_headers_with_company, test_forecast, test_forecast_lines, test_scenario
    ):
        resp = client.post(
            f"/api/v1/cashflow/forecasts/{test_forecast.id}/scenarios/apply",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "saldo_finale" in data


class TestAlertAPI:

    def test_list_alerts(self, client, auth_headers_with_company, test_alert):
        resp = client.get("/api/v1/cashflow/alerts", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_resolve_alert(self, client, auth_headers_with_company, test_alert):
        resp = client.put(
            f"/api/v1/cashflow/alerts/{test_alert.id}/resolve",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 200
        assert resp.json()["stato"] == "risolto"

    def test_ignore_alert(self, client, auth_headers_with_company, test_alert):
        resp = client.put(
            f"/api/v1/cashflow/alerts/{test_alert.id}/ignore",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 200
        assert resp.json()["stato"] == "ignorato"

    def test_alert_count(self, client, auth_headers_with_company, test_alert):
        resp = client.get("/api/v1/cashflow/alerts/count", headers=auth_headers_with_company)
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


class TestAnalysisAPI:

    def test_seasonality(self, client, auth_headers_with_company, test_bank_account, test_transaction):
        resp = client.get("/api/v1/cashflow/analysis/seasonality", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["mesi"]) == 12

    def test_trends(self, client, auth_headers_with_company, test_bank_account, test_transaction):
        resp = client.get(
            "/api/v1/cashflow/analysis/trends?mesi=3",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 200

    def test_runway(self, client, auth_headers_with_company, test_bank_account, test_transaction):
        resp = client.get("/api/v1/cashflow/analysis/runway", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert "saldo_attuale" in data
        assert "burn_rate_mensile" in data


class TestChartTableAPI:

    def test_chart(self, client, auth_headers_with_company, test_bank_account):
        resp = client.get("/api/v1/cashflow/chart", headers=auth_headers_with_company)
        assert resp.status_code == 200
        assert "punti" in resp.json()

    def test_table(self, client, auth_headers_with_company, test_bank_account):
        resp = client.get("/api/v1/cashflow/table", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert "righe" in data
        assert "periodi" in data
