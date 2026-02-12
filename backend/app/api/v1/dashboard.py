"""Dashboard API endpoints."""
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.dashboard import (
    DashboardResponse,
    DashboardSnapshotResponse,
    DashboardTrendResponse,
    DashboardWidgetResponse,
    DashboardWidgetUpdateRequest,
    QuickActionItem,
)
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    account_ids: str | None = Query(None, description="Comma-separated UUIDs"),
):
    company, _uc = company_data
    parsed_ids = None
    if account_ids:
        parsed_ids = [uuid.UUID(aid.strip()) for aid in account_ids.split(",")]

    data = dashboard_service.get_dashboard_data(
        db, company.id, current_user.id,
        period_start=period_start,
        period_end=period_end,
        account_ids=parsed_ids,
    )
    return data


@router.get("/section/{section}", response_model=dict)
def get_dashboard_section(
    section: str,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    account_ids: str | None = Query(None, description="Comma-separated UUIDs"),
):
    company, _uc = company_data
    parsed_ids = None
    if account_ids:
        parsed_ids = [uuid.UUID(aid.strip()) for aid in account_ids.split(",")]

    valid_sections = [
        "saldi", "cash_flow", "entrate_uscite", "scadenze",
        "riconciliazione", "pagamenti", "alert", "attivita_recenti", "quick_actions",
    ]
    if section not in valid_sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sezione non valida. Sezioni disponibili: {', '.join(valid_sections)}",
        )

    data = dashboard_service.get_dashboard_section(
        db, company.id, section,
        period_start=period_start,
        period_end=period_end,
        account_ids=parsed_ids,
    )
    return data


@router.get("/widgets", response_model=list[DashboardWidgetResponse])
def get_widgets(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    widgets = dashboard_service.get_or_create_widgets(db, current_user.id, company.id)
    return [DashboardWidgetResponse.model_validate(w) for w in widgets]


@router.put("/widgets", response_model=list[DashboardWidgetResponse])
def update_widgets(
    body: DashboardWidgetUpdateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    widgets_data = [w.model_dump() for w in body.widgets]
    widgets = dashboard_service.update_widgets(db, current_user.id, company.id, widgets_data)
    return [DashboardWidgetResponse.model_validate(w) for w in widgets]


@router.post("/widgets/reset", response_model=list[DashboardWidgetResponse])
def reset_widgets(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    widgets = dashboard_service.reset_widgets(db, current_user.id, company.id)
    return [DashboardWidgetResponse.model_validate(w) for w in widgets]


@router.get("/trend", response_model=DashboardTrendResponse)
def get_trend(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    kpi: str = Query("saldo_totale"),
    periodo: str = Query("30g"),
):
    company, _uc = company_data
    return dashboard_service.get_trend(db, company.id, kpi, periodo)


@router.post("/snapshot", response_model=DashboardSnapshotResponse)
def generate_snapshot(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    snapshot = dashboard_service.generate_snapshot(db, company.id)
    return DashboardSnapshotResponse.model_validate(snapshot)


@router.get("/snapshots", response_model=list[DashboardSnapshotResponse])
def get_snapshots(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    data_da: date | None = Query(None),
    data_a: date | None = Query(None),
):
    company, _uc = company_data
    snapshots = dashboard_service.get_snapshots(db, company.id, data_da=data_da, data_a=data_a)
    return [DashboardSnapshotResponse.model_validate(s) for s in snapshots]


@router.get("/quick-actions", response_model=list[QuickActionItem])
def get_quick_actions(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return dashboard_service.get_quick_actions(db, company.id)
