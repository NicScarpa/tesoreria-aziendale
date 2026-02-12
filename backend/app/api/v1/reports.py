"""Reports API endpoints."""
import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import ReportExecutionStatus, UserRole
from app.schemas.report import (
    ReportDefinitionCreateRequest,
    ReportDefinitionListResponse,
    ReportDefinitionResponse,
    ReportDefinitionUpdateRequest,
    ReportExecutionListResponse,
    ReportExecutionResponse,
    ReportGenerateQuickRequest,
    ReportGenerateRequest,
    ReportScheduleCreateRequest,
    ReportScheduleListResponse,
    ReportScheduleResponse,
    ReportScheduleUpdateRequest,
)
from app.services import report_service
from app.services.report_formatter import format_report
from app.services.report_generator import generate_report_data

router = APIRouter(prefix="/reports", tags=["reports"])


# --- Report Definitions ---

@router.get("", response_model=ReportDefinitionListResponse)
def list_report_definitions(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    tipo: str | None = Query(None),
    is_preferito: bool | None = Query(None),
    search: str | None = Query(None),
):
    company, _uc = company_data
    items = report_service.list_definitions(
        db, company.id, tipo=tipo, is_preferito=is_preferito, search=search
    )
    return {
        "items": [ReportDefinitionResponse.model_validate(d) for d in items],
        "total": len(items),
    }


@router.get("/{definition_id}", response_model=ReportDefinitionResponse)
def get_report_definition(
    definition_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    definition = report_service.get_definition(db, definition_id, company.id)
    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report non trovato")
    return ReportDefinitionResponse.model_validate(definition)


@router.post("", response_model=ReportDefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_report_definition(
    body: ReportDefinitionCreateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    definition = report_service.create_definition(db, company.id, data)
    return ReportDefinitionResponse.model_validate(definition)


@router.put("/{definition_id}", response_model=ReportDefinitionResponse)
def update_report_definition(
    definition_id: uuid.UUID,
    body: ReportDefinitionUpdateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    definition = report_service.update_definition(db, definition_id, company.id, data)
    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report non trovato o non modificabile (report di sistema)",
        )
    return ReportDefinitionResponse.model_validate(definition)


@router.delete("/{definition_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report_definition(
    definition_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    if not report_service.delete_definition(db, definition_id, company.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report non trovato o non eliminabile (report di sistema)",
        )


@router.put("/{definition_id}/toggle-preferito", response_model=ReportDefinitionResponse)
def toggle_preferito(
    definition_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    definition = report_service.toggle_preferito(db, definition_id, company.id)
    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report non trovato")
    return ReportDefinitionResponse.model_validate(definition)


# --- Report Generation ---

@router.post("/{definition_id}/generate", response_model=ReportExecutionResponse)
def generate_report(
    definition_id: uuid.UUID,
    body: ReportGenerateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    definition = report_service.get_definition(db, definition_id, company.id)
    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report non trovato")

    formato = body.formato or definition.formato_default.value
    parametri = body.parametri or definition.parametri_default or {}

    execution = report_service.create_execution(
        db, company.id, current_user.id,
        nome=definition.nome,
        tipo=definition.tipo.value,
        formato=formato,
        parametri=parametri,
        report_definition_id=definition.id,
    )

    # Synchronous generation
    try:
        execution.stato = ReportExecutionStatus.IN_GENERAZIONE
        db.commit()

        report_data = generate_report_data(db, company.id, definition.tipo.value, parametri)
        file_path, file_size = format_report(
            report_data, formato, company.id, company.name
        )
        execution = report_service.complete_execution(
            db, execution, file_path, file_size,
            righe_totali=len(report_data.get("rows", [])),
            risultato=report_data.get("metadata"),
        )
    except Exception as e:
        execution = report_service.fail_execution(db, execution, str(e))

    return ReportExecutionResponse.model_validate(execution)


@router.post("/generate-quick", response_model=ReportExecutionResponse)
def generate_quick_report(
    body: ReportGenerateQuickRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    nome = body.nome or f"Report {body.tipo}"
    formato = body.formato

    execution = report_service.create_execution(
        db, company.id, current_user.id,
        nome=nome,
        tipo=body.tipo,
        formato=formato,
        parametri=body.parametri,
    )

    try:
        execution.stato = ReportExecutionStatus.IN_GENERAZIONE
        db.commit()

        report_data = generate_report_data(db, company.id, body.tipo, body.parametri)
        file_path, file_size = format_report(
            report_data, formato, company.id, company.name
        )
        execution = report_service.complete_execution(
            db, execution, file_path, file_size,
            righe_totali=len(report_data.get("rows", [])),
            risultato=report_data.get("metadata"),
        )
    except Exception as e:
        execution = report_service.fail_execution(db, execution, str(e))

    return ReportExecutionResponse.model_validate(execution)


# --- Report Executions ---

@router.get("/executions", response_model=ReportExecutionListResponse)
def list_executions(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    tipo: str | None = Query(None),
    stato: str | None = Query(None),
    report_definition_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    company, _uc = company_data
    items, total = report_service.list_executions(
        db, company.id, tipo=tipo, stato=stato,
        report_definition_id=report_definition_id,
        page=page, page_size=per_page,
    )
    return {
        "items": [ReportExecutionResponse.model_validate(e) for e in items],
        "total": total,
        "page": page,
        "page_size": per_page,
    }


@router.get("/executions/{execution_id}", response_model=ReportExecutionResponse)
def get_execution(
    execution_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    execution = report_service.get_execution(db, execution_id, company.id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esecuzione non trovata")
    return ReportExecutionResponse.model_validate(execution)


@router.get("/executions/{execution_id}/download")
def download_execution(
    execution_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    execution = report_service.get_execution(db, execution_id, company.id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esecuzione non trovata")

    if execution.stato.value != "completato" or not execution.file_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File non disponibile")

    if not os.path.exists(execution.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File non trovato sul server")

    media_types = {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv; charset=utf-8",
    }
    formato = execution.formato.value
    media_type = media_types.get(formato, "application/octet-stream")
    filename = os.path.basename(execution.file_path)

    return FileResponse(
        path=execution.file_path,
        media_type=media_type,
        filename=filename,
    )


@router.delete("/executions/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_execution(
    execution_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    if not report_service.delete_execution(db, execution_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esecuzione non trovata")


# --- Report Schedules ---

@router.get("/schedules", response_model=ReportScheduleListResponse)
def list_schedules(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    items = report_service.list_schedules(db, company.id)
    return {
        "items": [ReportScheduleResponse.model_validate(s) for s in items],
        "total": len(items),
    }


@router.post("/schedules", response_model=ReportScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    body: ReportScheduleCreateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    schedule = report_service.create_schedule(db, company.id, current_user.id, data)
    return ReportScheduleResponse.model_validate(schedule)


@router.put("/schedules/{schedule_id}", response_model=ReportScheduleResponse)
def update_schedule(
    schedule_id: uuid.UUID,
    body: ReportScheduleUpdateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    schedule = report_service.update_schedule(db, schedule_id, company.id, data)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedulazione non trovata")
    return ReportScheduleResponse.model_validate(schedule)


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    if not report_service.delete_schedule(db, schedule_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedulazione non trovata")


@router.post("/schedules/{schedule_id}/run-now", response_model=ReportExecutionResponse)
def run_schedule_now(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    schedule = report_service.get_schedule(db, schedule_id, company.id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedulazione non trovata")

    definition = report_service.get_definition(db, schedule.report_definition_id, company.id)
    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report associato non trovato")

    formato = schedule.formato.value
    parametri = schedule.parametri or definition.parametri_default or {}

    execution = report_service.create_execution(
        db, company.id, current_user.id,
        nome=f"{definition.nome} (schedulato)",
        tipo=definition.tipo.value,
        formato=formato,
        parametri=parametri,
        report_definition_id=definition.id,
    )

    try:
        execution.stato = ReportExecutionStatus.IN_GENERAZIONE
        db.commit()

        report_data = generate_report_data(db, company.id, definition.tipo.value, parametri)
        file_path, file_size = format_report(
            report_data, formato, company.id, company.name
        )
        execution = report_service.complete_execution(
            db, execution, file_path, file_size,
            righe_totali=len(report_data.get("rows", [])),
            risultato=report_data.get("metadata"),
        )

        # Update schedule
        from datetime import datetime, timezone
        schedule.ultima_esecuzione = datetime.now(timezone.utc)
        from app.models.enums import ReportFrequency
        schedule.prossima_esecuzione = report_service._calcola_prossima_esecuzione(schedule.frequenza)
        db.commit()
    except Exception as e:
        execution = report_service.fail_execution(db, execution, str(e))

    return ReportExecutionResponse.model_validate(execution)
