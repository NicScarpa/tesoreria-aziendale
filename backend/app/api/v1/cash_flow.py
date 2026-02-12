"""Cash Flow API endpoints."""
import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.cash_flow import (
    CashFlowAlertListResponse,
    CashFlowAlertResponse,
    CashFlowForecastCreateRequest,
    CashFlowForecastDetailResponse,
    CashFlowForecastListResponse,
    CashFlowForecastResponse,
    CashFlowForecastUpdateRequest,
    CashFlowProjectionResponse,
    CashFlowScenarioCreateRequest,
    CashFlowScenarioResponse,
    CashFlowScenarioUpdateRequest,
    CashFlowSummaryResponse,
    RunwayResponse,
    ScenarioCompareResponse,
    SeasonalityResponse,
    TrendResponse,
    VarianceResponse,
    CashFlowChartResponse,
    CashFlowTableResponse,
    CashFlowCellDetailResponse,
)
from app.services import cash_flow_engine, cash_flow_service

router = APIRouter(prefix="/cashflow", tags=["cashflow"])


# --- Real-time projection endpoints ---

@router.get("", response_model=CashFlowProjectionResponse)
def get_cash_flow_projection(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    data_inizio: date | None = Query(None),
    data_fine: date | None = Query(None),
    bank_account_ids: str | None = Query(None, description="Comma-separated UUIDs"),
    includi_scadenze: bool = Query(True),
    includi_pagamenti: bool = Query(True),
    includi_ricorrenze: bool = Query(True),
    includi_stime_storiche: bool = Query(False),
):
    company, _uc = company_data
    account_ids = None
    if bank_account_ids:
        account_ids = [uuid.UUID(id.strip()) for id in bank_account_ids.split(",")]

    projection = cash_flow_engine.generate_cash_flow_projection(
        db, company.id,
        data_inizio=data_inizio,
        data_fine=data_fine,
        bank_account_ids=account_ids,
        includi_scadenze=includi_scadenze,
        includi_pagamenti=includi_pagamenti,
        includi_ricorrenze=includi_ricorrenze,
        includi_stime_storiche=includi_stime_storiche,
    )
    return projection


@router.get("/summary", response_model=CashFlowSummaryResponse)
def get_summary(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return cash_flow_service.get_summary(db, company.id)


# --- Chart/Table endpoints (PRD-08) ---

@router.get("/chart", response_model=CashFlowChartResponse)
def get_chart_data(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    data_inizio: date | None = Query(None),
    data_fine: date | None = Query(None),
    raggruppamento: str = Query("mensile"),
):
    company, _uc = company_data
    from datetime import timedelta
    today = date.today()
    start = data_inizio or today - timedelta(days=180)
    end = data_fine or today + timedelta(days=90)

    projection = cash_flow_engine.generate_cash_flow_projection(
        db, company.id, data_inizio=start, data_fine=end
    )

    from collections import defaultdict
    buckets: dict[str, dict] = defaultdict(lambda: {"saldo": Decimal("0"), "entrate": Decimal("0"), "uscite": Decimal("0")})

    for line in projection["lines"]:
        if raggruppamento == "settimanale":
            key = line["data"].strftime("%G-W%V")
        elif raggruppamento == "giornaliero":
            key = line["data"].isoformat()
        else:
            key = line["data"].strftime("%Y-%m")

        if line["tipo"] == "entrata":
            buckets[key]["entrate"] += line["importo"]
        else:
            buckets[key]["uscite"] += line["importo"]
        buckets[key]["saldo"] = line["saldo_progressivo"]

    punti = [
        {"periodo": k, "saldo": v["saldo"], "entrate": v["entrate"], "uscite": v["uscite"]}
        for k, v in sorted(buckets.items())
    ]

    return {"punti": punti, "raggruppamento": raggruppamento}


@router.get("/table", response_model=CashFlowTableResponse)
def get_table_data(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    data_inizio: date | None = Query(None),
    data_fine: date | None = Query(None),
):
    company, _uc = company_data
    from datetime import timedelta
    from collections import defaultdict

    today = date.today()
    start = data_inizio or today - timedelta(days=180)
    end = data_fine or today + timedelta(days=90)

    projection = cash_flow_engine.generate_cash_flow_projection(
        db, company.id, data_inizio=start, data_fine=end
    )

    # Build category x period matrix
    cat_data: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    totali_entrate: dict[str, Decimal] = defaultdict(Decimal)
    totali_uscite: dict[str, Decimal] = defaultdict(Decimal)
    periodi_set: set[str] = set()

    for line in projection["lines"]:
        periodo = line["data"].strftime("%Y-%m")
        periodi_set.add(periodo)
        cat = line.get("categoria") or "Non categorizzato"
        tipo = line["tipo"]
        key = (cat, tipo)
        cat_data[key][periodo] += line["importo"]
        if tipo == "entrata":
            totali_entrate[periodo] += line["importo"]
        else:
            totali_uscite[periodo] += line["importo"]

    periodi = sorted(periodi_set)
    saldi_netti = {p: totali_entrate.get(p, Decimal("0")) - totali_uscite.get(p, Decimal("0")) for p in periodi}

    righe = []
    for (cat, tipo), per_data in sorted(cat_data.items()):
        totale = sum(per_data.values())
        righe.append({
            "categoria": cat,
            "tipo": tipo,
            "periodi": dict(per_data),
            "totale": totale,
        })

    return {
        "righe": righe,
        "periodi": periodi,
        "totali_entrate": dict(totali_entrate),
        "totali_uscite": dict(totali_uscite),
        "saldi_netti": saldi_netti,
    }


@router.get("/cell-detail", response_model=CashFlowCellDetailResponse)
def get_cell_detail(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    categoria: str = Query(...),
    periodo: str = Query(..., description="Format: YYYY-MM"),
    tipo: str = Query(..., description="entrata or uscita"),
):
    company, _uc = company_data
    from datetime import timedelta

    # Parse period
    try:
        year, month = periodo.split("-")
        start = date(int(year), int(month), 1)
        if int(month) == 12:
            end = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(int(year), int(month) + 1, 1) - timedelta(days=1)
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Formato periodo non valido. Usa YYYY-MM")

    projection = cash_flow_engine.generate_cash_flow_projection(
        db, company.id, data_inizio=start, data_fine=end
    )

    items = []
    totale = Decimal("0")
    for line in projection["lines"]:
        cat = line.get("categoria") or "Non categorizzato"
        if cat == categoria and line["tipo"] == tipo:
            items.append({
                "data": line["data"],
                "descrizione": line.get("descrizione"),
                "importo": line["importo"],
                "fonte": line["fonte"],
                "controparte": None,
            })
            totale += line["importo"]

    return {
        "categoria": categoria,
        "periodo": periodo,
        "tipo": tipo,
        "items": items,
        "totale": totale,
    }


# --- Alert count for sidebar ---

@router.get("/alerts/count")
def get_alert_count(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    count = cash_flow_service.count_active_alerts(db, company.id)
    return {"count": count}


# --- Forecast CRUD ---

@router.get("/forecasts", response_model=CashFlowForecastListResponse)
def list_forecasts(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    stato: str | None = Query(None),
    tipo: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    company, _uc = company_data
    items, total = cash_flow_service.list_forecasts(
        db, company.id, stato=stato, tipo=tipo, page=page, page_size=per_page
    )
    return {
        "items": [CashFlowForecastResponse.model_validate(f) for f in items],
        "total": total,
        "page": page,
        "page_size": per_page,
    }


@router.get("/forecasts/{forecast_id}", response_model=CashFlowForecastDetailResponse)
def get_forecast(
    forecast_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    forecast = cash_flow_service.get_forecast(db, forecast_id, company.id)
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previsione non trovata")
    return CashFlowForecastDetailResponse.model_validate(forecast)


@router.post("/forecasts", response_model=CashFlowForecastResponse, status_code=status.HTTP_201_CREATED)
def create_forecast(
    body: CashFlowForecastCreateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    forecast = cash_flow_service.create_forecast(db, company.id, current_user.id, data)
    return CashFlowForecastResponse.model_validate(forecast)


@router.put("/forecasts/{forecast_id}", response_model=CashFlowForecastResponse)
def update_forecast(
    forecast_id: uuid.UUID,
    body: CashFlowForecastUpdateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    forecast = cash_flow_service.update_forecast(db, forecast_id, company.id, data)
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previsione non trovata")
    return CashFlowForecastResponse.model_validate(forecast)


@router.delete("/forecasts/{forecast_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_forecast(
    forecast_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    if not cash_flow_service.delete_forecast(db, forecast_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previsione non trovata")


@router.post("/forecasts/{forecast_id}/refresh", response_model=CashFlowForecastResponse)
def refresh_forecast(
    forecast_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    forecast = cash_flow_service.refresh_forecast(db, forecast_id, company.id)
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previsione non trovata")
    return CashFlowForecastResponse.model_validate(forecast)


@router.get("/forecasts/{forecast_id}/variance", response_model=VarianceResponse)
def get_variance(
    forecast_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    forecast = cash_flow_service.get_forecast(db, forecast_id, company.id)
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previsione non trovata")
    return cash_flow_engine.calculate_variance(db, forecast_id)


# --- Scenarios ---

@router.get("/forecasts/{forecast_id}/scenarios", response_model=list[CashFlowScenarioResponse])
def list_scenarios(
    forecast_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    scenarios = cash_flow_service.list_scenarios(db, forecast_id, company.id)
    return [CashFlowScenarioResponse.model_validate(s) for s in scenarios]


@router.post("/forecasts/{forecast_id}/scenarios", response_model=CashFlowScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(
    forecast_id: uuid.UUID,
    body: CashFlowScenarioCreateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    scenario = cash_flow_service.create_scenario(db, forecast_id, company.id, data)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previsione non trovata")
    return CashFlowScenarioResponse.model_validate(scenario)


@router.put("/forecasts/{forecast_id}/scenarios/{scenario_id}", response_model=CashFlowScenarioResponse)
def update_scenario(
    forecast_id: uuid.UUID,
    scenario_id: uuid.UUID,
    body: CashFlowScenarioUpdateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    scenario = cash_flow_service.update_scenario(db, forecast_id, scenario_id, company.id, data)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario non trovato")
    return CashFlowScenarioResponse.model_validate(scenario)


@router.delete("/forecasts/{forecast_id}/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    forecast_id: uuid.UUID,
    scenario_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    if not cash_flow_service.delete_scenario(db, forecast_id, scenario_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario non trovato")


@router.post("/forecasts/{forecast_id}/scenarios/apply", response_model=CashFlowProjectionResponse)
def apply_scenarios(
    forecast_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    forecast = cash_flow_service.get_forecast(db, forecast_id, company.id)
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previsione non trovata")
    result = cash_flow_engine.apply_scenarios(db, forecast_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previsione non trovata")
    return result


@router.get("/forecasts/{forecast_id}/compare", response_model=ScenarioCompareResponse)
def compare_scenarios(
    forecast_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    forecast = cash_flow_service.get_forecast(db, forecast_id, company.id)
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previsione non trovata")

    # Base projection from saved lines
    from app.models.cash_flow_forecast_line import CashFlowForecastLine
    base_lines = (
        db.query(CashFlowForecastLine)
        .filter(CashFlowForecastLine.forecast_id == forecast_id)
        .order_by(CashFlowForecastLine.data.asc())
        .all()
    )

    base_entrate = sum(l.importo for l in base_lines if l.tipo.value == "entrata")
    base_uscite = sum(l.importo for l in base_lines if l.tipo.value == "uscita")
    base_response = {
        "saldo_iniziale": forecast.saldo_iniziale,
        "saldo_finale": forecast.saldo_finale_previsto,
        "totale_entrate": base_entrate,
        "totale_uscite": base_uscite,
        "data_inizio": forecast.data_inizio,
        "data_fine": forecast.data_fine,
        "lines": [{
            "data": l.data,
            "tipo": l.tipo.value,
            "importo": l.importo,
            "categoria": l.categoria,
            "descrizione": l.descrizione,
            "fonte": l.fonte.value,
            "fonte_id": l.fonte_id,
            "confidenza": l.confidenza.value,
            "saldo_progressivo": l.saldo_progressivo,
            "is_realizzata": l.is_realizzata,
        } for l in base_lines],
    }

    # With scenarios
    adjusted = cash_flow_engine.apply_scenarios(db, forecast_id)

    return {
        "base": base_response,
        "con_scenari": adjusted,
        "delta_saldo_finale": adjusted["saldo_finale"] - forecast.saldo_finale_previsto,
    }


# --- Alerts ---

@router.get("/alerts", response_model=CashFlowAlertListResponse)
def list_alerts(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    tipo: str | None = Query(None),
    stato: str | None = Query(None),
    data_da: date | None = Query(None),
    data_a: date | None = Query(None),
):
    company, _uc = company_data
    alerts = cash_flow_service.list_alerts(
        db, company.id, tipo=tipo, stato=stato, data_da=data_da, data_a=data_a
    )
    return {
        "items": [CashFlowAlertResponse.model_validate(a) for a in alerts],
        "total": len(alerts),
    }


@router.put("/alerts/{alert_id}/resolve", response_model=CashFlowAlertResponse)
def resolve_alert(
    alert_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    alert = cash_flow_service.resolve_alert(db, alert_id, company.id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert non trovato")
    return CashFlowAlertResponse.model_validate(alert)


@router.put("/alerts/{alert_id}/ignore", response_model=CashFlowAlertResponse)
def ignore_alert(
    alert_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    alert = cash_flow_service.ignore_alert(db, alert_id, company.id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert non trovato")
    return CashFlowAlertResponse.model_validate(alert)


@router.post("/check-alerts", response_model=list[CashFlowAlertResponse])
def check_alerts(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    alerts = cash_flow_service.check_and_create_alerts(db, company.id)
    return [CashFlowAlertResponse.model_validate(a) for a in alerts]


# --- Analysis ---

@router.get("/analysis/seasonality", response_model=SeasonalityResponse)
def get_seasonality(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return cash_flow_engine.calculate_seasonality(db, company.id)


@router.get("/analysis/trends", response_model=TrendResponse)
def get_trends(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    mesi: int = Query(6, ge=1, le=24),
    raggruppamento: str = Query("mensile"),
):
    company, _uc = company_data
    return cash_flow_engine.calculate_trends(
        db, company.id, mesi=mesi, raggruppamento=raggruppamento
    )


@router.get("/analysis/runway", response_model=RunwayResponse)
def get_runway(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return cash_flow_engine.calculate_runway(db, company.id)
