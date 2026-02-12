"""Cash Flow Service — CRUD for Forecasts, Scenarios, Alerts.

Delegates calculations to CashFlowEngine.
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cash_flow_alert import CashFlowAlert
from app.models.cash_flow_forecast import CashFlowForecast
from app.models.cash_flow_forecast_line import CashFlowForecastLine
from app.models.cash_flow_scenario import CashFlowScenario
from app.models.enums import (
    AlertStatus, CashFlowAlertType, CashFlowLineType, CashFlowSource,
    ConfidenceLevel, ForecastStatus, ForecastType, ScenarioAdjustmentType,
)
from app.services import cash_flow_engine


# --- Forecast CRUD ---

def list_forecasts(
    db: Session,
    company_id: uuid.UUID,
    *,
    stato: str | None = None,
    tipo: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[CashFlowForecast], int]:
    q = db.query(CashFlowForecast).filter(CashFlowForecast.company_id == company_id)

    if stato:
        q = q.filter(CashFlowForecast.stato == stato)
    if tipo:
        q = q.filter(CashFlowForecast.tipo == tipo)

    total = q.count()
    items = (
        q.order_by(CashFlowForecast.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_forecast(
    db: Session, forecast_id: uuid.UUID, company_id: uuid.UUID
) -> CashFlowForecast | None:
    return (
        db.query(CashFlowForecast)
        .filter(
            CashFlowForecast.id == forecast_id,
            CashFlowForecast.company_id == company_id,
        )
        .first()
    )


def create_forecast(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    data: dict,
) -> CashFlowForecast:
    # Generate projection
    projection = cash_flow_engine.generate_cash_flow_projection(
        db, company_id,
        data_inizio=data.get("data_inizio"),
        data_fine=data.get("data_fine"),
        bank_account_ids=data.get("bank_account_ids"),
        includi_scadenze=data.get("includi_scadenze", True),
        includi_pagamenti=data.get("includi_pagamenti", True),
        includi_ricorrenze=data.get("includi_ricorrenze", True),
        includi_stime_storiche=data.get("includi_stime_storiche", False),
    )

    forecast = CashFlowForecast(
        company_id=company_id,
        creato_da_user_id=user_id,
        nome=data["nome"],
        descrizione=data.get("descrizione"),
        data_inizio=data["data_inizio"],
        data_fine=data["data_fine"],
        saldo_iniziale=projection["saldo_iniziale"],
        saldo_finale_previsto=projection["saldo_finale"],
        totale_entrate_previste=projection["totale_entrate"],
        totale_uscite_previste=projection["totale_uscite"],
        stato=ForecastStatus.BOZZA,
        tipo=ForecastType(data.get("tipo", "base")),
        parametri={
            "bank_account_ids": [str(id) for id in (data.get("bank_account_ids") or [])],
            "includi_scadenze": data.get("includi_scadenze", True),
            "includi_pagamenti": data.get("includi_pagamenti", True),
            "includi_ricorrenze": data.get("includi_ricorrenze", True),
            "includi_stime_storiche": data.get("includi_stime_storiche", False),
        },
    )
    db.add(forecast)
    db.flush()

    # Save projection lines
    for line_data in projection["lines"]:
        line = CashFlowForecastLine(
            forecast_id=forecast.id,
            data=line_data["data"],
            tipo=CashFlowLineType(line_data["tipo"]),
            importo=line_data["importo"],
            categoria=line_data.get("categoria"),
            descrizione=line_data.get("descrizione"),
            fonte=CashFlowSource(line_data["fonte"]),
            fonte_id=line_data.get("fonte_id"),
            confidenza=ConfidenceLevel(line_data["confidenza"]),
            saldo_progressivo=line_data["saldo_progressivo"],
            is_realizzata=line_data.get("is_realizzata", False),
        )
        db.add(line)

    db.commit()
    db.refresh(forecast)
    return forecast


def update_forecast(
    db: Session,
    forecast_id: uuid.UUID,
    company_id: uuid.UUID,
    data: dict,
) -> CashFlowForecast | None:
    forecast = get_forecast(db, forecast_id, company_id)
    if not forecast:
        return None

    for key, value in data.items():
        if value is not None:
            if key == "stato":
                setattr(forecast, key, ForecastStatus(value))
            else:
                setattr(forecast, key, value)

    db.commit()
    db.refresh(forecast)
    return forecast


def delete_forecast(
    db: Session, forecast_id: uuid.UUID, company_id: uuid.UUID
) -> bool:
    forecast = get_forecast(db, forecast_id, company_id)
    if not forecast:
        return False

    db.delete(forecast)
    db.commit()
    return True


def refresh_forecast(
    db: Session, forecast_id: uuid.UUID, company_id: uuid.UUID
) -> CashFlowForecast | None:
    """Regenerate forecast lines from current data."""
    forecast = get_forecast(db, forecast_id, company_id)
    if not forecast:
        return None

    # Delete existing lines
    db.query(CashFlowForecastLine).filter(
        CashFlowForecastLine.forecast_id == forecast_id
    ).delete()

    # Regenerate
    params = forecast.parametri or {}
    bank_account_ids = None
    if params.get("bank_account_ids"):
        bank_account_ids = [uuid.UUID(id) for id in params["bank_account_ids"]]

    projection = cash_flow_engine.generate_cash_flow_projection(
        db, company_id,
        data_inizio=forecast.data_inizio,
        data_fine=forecast.data_fine,
        bank_account_ids=bank_account_ids,
        includi_scadenze=params.get("includi_scadenze", True),
        includi_pagamenti=params.get("includi_pagamenti", True),
        includi_ricorrenze=params.get("includi_ricorrenze", True),
        includi_stime_storiche=params.get("includi_stime_storiche", False),
    )

    forecast.saldo_iniziale = projection["saldo_iniziale"]
    forecast.saldo_finale_previsto = projection["saldo_finale"]
    forecast.totale_entrate_previste = projection["totale_entrate"]
    forecast.totale_uscite_previste = projection["totale_uscite"]

    for line_data in projection["lines"]:
        line = CashFlowForecastLine(
            forecast_id=forecast.id,
            data=line_data["data"],
            tipo=CashFlowLineType(line_data["tipo"]),
            importo=line_data["importo"],
            categoria=line_data.get("categoria"),
            descrizione=line_data.get("descrizione"),
            fonte=CashFlowSource(line_data["fonte"]),
            fonte_id=line_data.get("fonte_id"),
            confidenza=ConfidenceLevel(line_data["confidenza"]),
            saldo_progressivo=line_data["saldo_progressivo"],
            is_realizzata=line_data.get("is_realizzata", False),
        )
        db.add(line)

    db.commit()
    db.refresh(forecast)
    return forecast


# --- Scenario CRUD ---

def list_scenarios(
    db: Session, forecast_id: uuid.UUID, company_id: uuid.UUID
) -> list[CashFlowScenario]:
    forecast = get_forecast(db, forecast_id, company_id)
    if not forecast:
        return []
    return (
        db.query(CashFlowScenario)
        .filter(CashFlowScenario.forecast_id == forecast_id)
        .order_by(CashFlowScenario.created_at.asc())
        .all()
    )


def create_scenario(
    db: Session,
    forecast_id: uuid.UUID,
    company_id: uuid.UUID,
    data: dict,
) -> CashFlowScenario | None:
    forecast = get_forecast(db, forecast_id, company_id)
    if not forecast:
        return None

    tipo_mov = None
    if data.get("tipo_movimento"):
        tipo_mov = CashFlowLineType(data["tipo_movimento"])

    scenario = CashFlowScenario(
        forecast_id=forecast_id,
        nome=data["nome"],
        descrizione=data.get("descrizione"),
        tipo_aggiustamento=ScenarioAdjustmentType(data["tipo_aggiustamento"]),
        data_originale=data.get("data_originale"),
        data_modificata=data.get("data_modificata"),
        importo_originale=data.get("importo_originale"),
        importo_modificato=data.get("importo_modificato"),
        tipo_movimento=tipo_mov,
        categoria=data.get("categoria"),
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def update_scenario(
    db: Session,
    forecast_id: uuid.UUID,
    scenario_id: uuid.UUID,
    company_id: uuid.UUID,
    data: dict,
) -> CashFlowScenario | None:
    forecast = get_forecast(db, forecast_id, company_id)
    if not forecast:
        return None

    scenario = (
        db.query(CashFlowScenario)
        .filter(
            CashFlowScenario.id == scenario_id,
            CashFlowScenario.forecast_id == forecast_id,
        )
        .first()
    )
    if not scenario:
        return None

    for key, value in data.items():
        if value is not None:
            if key == "tipo_aggiustamento":
                setattr(scenario, key, ScenarioAdjustmentType(value))
            elif key == "tipo_movimento":
                setattr(scenario, key, CashFlowLineType(value))
            else:
                setattr(scenario, key, value)

    db.commit()
    db.refresh(scenario)
    return scenario


def delete_scenario(
    db: Session,
    forecast_id: uuid.UUID,
    scenario_id: uuid.UUID,
    company_id: uuid.UUID,
) -> bool:
    forecast = get_forecast(db, forecast_id, company_id)
    if not forecast:
        return False

    scenario = (
        db.query(CashFlowScenario)
        .filter(
            CashFlowScenario.id == scenario_id,
            CashFlowScenario.forecast_id == forecast_id,
        )
        .first()
    )
    if not scenario:
        return False

    db.delete(scenario)
    db.commit()
    return True


# --- Alert CRUD ---

def list_alerts(
    db: Session,
    company_id: uuid.UUID,
    *,
    tipo: str | None = None,
    stato: str | None = None,
    data_da: date | None = None,
    data_a: date | None = None,
) -> list[CashFlowAlert]:
    q = db.query(CashFlowAlert).filter(CashFlowAlert.company_id == company_id)

    if tipo:
        q = q.filter(CashFlowAlert.tipo == tipo)
    if stato:
        q = q.filter(CashFlowAlert.stato == stato)
    if data_da:
        q = q.filter(CashFlowAlert.data_prevista >= data_da)
    if data_a:
        q = q.filter(CashFlowAlert.data_prevista <= data_a)

    return q.order_by(CashFlowAlert.data_prevista.asc()).all()


def resolve_alert(
    db: Session, alert_id: uuid.UUID, company_id: uuid.UUID
) -> CashFlowAlert | None:
    alert = (
        db.query(CashFlowAlert)
        .filter(CashFlowAlert.id == alert_id, CashFlowAlert.company_id == company_id)
        .first()
    )
    if not alert:
        return None

    alert.stato = AlertStatus.RISOLTO
    db.commit()
    db.refresh(alert)
    return alert


def ignore_alert(
    db: Session, alert_id: uuid.UUID, company_id: uuid.UUID
) -> CashFlowAlert | None:
    alert = (
        db.query(CashFlowAlert)
        .filter(CashFlowAlert.id == alert_id, CashFlowAlert.company_id == company_id)
        .first()
    )
    if not alert:
        return None

    alert.stato = AlertStatus.IGNORATO
    db.commit()
    db.refresh(alert)
    return alert


def check_and_create_alerts(
    db: Session,
    company_id: uuid.UUID,
) -> list[CashFlowAlert]:
    """Run projection and create alerts for threshold violations."""
    projection = cash_flow_engine.generate_cash_flow_projection(db, company_id)

    # Get thresholds from company features
    from app.models.company import Company
    company = db.get(Company, company_id)
    features = (company.features or {}) if company else {}
    treasury = features.get("treasury_settings", {})
    min_threshold = Decimal(str(treasury.get("min_cash_threshold", 10000)))
    critical_threshold = Decimal(str(treasury.get("critical_cash_threshold", 0)))

    detected = cash_flow_engine.detect_alerts(
        db, company_id, projection["lines"],
        min_cash_threshold=min_threshold,
        critical_cash_threshold=critical_threshold,
    )

    created_alerts = []
    for alert_data in detected:
        # Check for existing active alert on same date/type
        existing = (
            db.query(CashFlowAlert)
            .filter(
                CashFlowAlert.company_id == company_id,
                CashFlowAlert.tipo == alert_data["tipo"],
                CashFlowAlert.data_prevista == alert_data["data_prevista"],
                CashFlowAlert.stato == AlertStatus.ATTIVO,
            )
            .first()
        )
        if existing:
            continue

        alert = CashFlowAlert(
            company_id=company_id,
            tipo=CashFlowAlertType(alert_data["tipo"]),
            data_prevista=alert_data["data_prevista"],
            saldo_previsto=alert_data["saldo_previsto"],
            soglia=alert_data["soglia"],
            messaggio=alert_data["messaggio"],
            stato=AlertStatus.ATTIVO,
        )
        db.add(alert)
        created_alerts.append(alert)

    db.commit()
    for a in created_alerts:
        db.refresh(a)
    return created_alerts


def get_summary(db: Session, company_id: uuid.UUID) -> dict:
    """Generate a summary for the dashboard."""
    today = date.today()

    # Current balance
    from app.models.bank_account import BankAccount
    from app.models.enums import AccountStatus
    accounts = (
        db.query(BankAccount)
        .filter(BankAccount.company_id == company_id, BankAccount.status == AccountStatus.ACTIVE)
        .all()
    )
    saldo_attuale = sum((a.current_balance or Decimal("0")) for a in accounts)

    # Projections at different horizons
    proj_7 = cash_flow_engine.generate_cash_flow_projection(
        db, company_id, data_inizio=today, data_fine=today + timedelta(days=7)
    )
    proj_30 = cash_flow_engine.generate_cash_flow_projection(
        db, company_id, data_inizio=today, data_fine=today + timedelta(days=30)
    )
    proj_90 = cash_flow_engine.generate_cash_flow_projection(
        db, company_id, data_inizio=today, data_fine=today + timedelta(days=90)
    )

    # Trend calculation (delta from current)
    trend_7 = proj_7["saldo_finale"] - saldo_attuale
    trend_30 = proj_30["saldo_finale"] - saldo_attuale

    # Next active alert
    next_alert = (
        db.query(CashFlowAlert)
        .filter(
            CashFlowAlert.company_id == company_id,
            CashFlowAlert.stato == AlertStatus.ATTIVO,
            CashFlowAlert.data_prevista >= today,
        )
        .order_by(CashFlowAlert.data_prevista.asc())
        .first()
    )

    # Runway
    runway = cash_flow_engine.calculate_runway(db, company_id)

    return {
        "saldo_attuale": saldo_attuale,
        "previsione_7gg": proj_7["saldo_finale"],
        "previsione_30gg": proj_30["saldo_finale"],
        "previsione_90gg": proj_90["saldo_finale"],
        "trend_7gg": trend_7,
        "trend_30gg": trend_30,
        "prossimo_alert": next_alert,
        "runway_mesi": runway["runway_mesi"],
        "burn_rate_mensile": runway["burn_rate_mensile"],
    }


def count_active_alerts(db: Session, company_id: uuid.UUID) -> int:
    """Return count of active alerts for sidebar badge."""
    return (
        db.query(func.count(CashFlowAlert.id))
        .filter(
            CashFlowAlert.company_id == company_id,
            CashFlowAlert.stato == AlertStatus.ATTIVO,
        )
        .scalar()
    ) or 0
