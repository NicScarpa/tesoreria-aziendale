"""Integration module API endpoints."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.core.deps import DB, CurrentUser, CurrentCompany, require_role
from app.models.enums import IntegrationType, InvoiceStatus, UserRole, WebhookType
from app.schemas.integration import (
    CAMT053ImportResponse,
    CBIParseResponse,
    IntegrationAlertsCount,
    IntegrationConfigResponse,
    IntegrationConfigUpdate,
    IntegrationOverviewResponse,
    IntegrationStatusItem,
    IntegrationToggle,
    InstitutionResponse,
    InvoiceBatchElaborateRequest,
    InvoiceBatchListResponse,
    InvoiceElaborateResponse,
    InvoiceImportBatchResponse,
    InvoiceImportListResponse,
    InvoiceImportResponse,
    OpenBankingConnectRequest,
    OpenBankingConnectionListResponse,
    OpenBankingConnectionResponse,
    OpenBankingLinkRequest,
    OpenBankingSyncLogResponse,
    SEPAValidationResponse,
    SyncLogListResponse,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    WebhookListResponse,
)
from app.services import (
    integration_config_service,
    invoice_import_service,
    open_banking_service,
    webhook_service,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])

MAX_XML_SIZE = 5 * 1024 * 1024  # 5MB
MAX_BATCH_SIZE = 50 * 1024 * 1024  # 50MB


# ===== Config Hub =====

@router.get("", response_model=IntegrationOverviewResponse)
def get_overview(db: DB, company_data: CurrentCompany):
    company, _uc = company_data
    items = integration_config_service.get_overview(db, company.id)
    return IntegrationOverviewResponse(
        integrations=[IntegrationStatusItem(**i) for i in items]
    )


@router.get("/alerts-count", response_model=IntegrationAlertsCount)
def get_alerts_count(db: DB, company_data: CurrentCompany):
    company, _uc = company_data
    return integration_config_service.get_alerts_count(db, company.id)


# ===== Open Banking =====

@router.get("/open-banking/institutions", response_model=list[InstitutionResponse])
def list_institutions(
    db: DB, company_data: CurrentCompany,
    search: str = "", country: str = "IT",
):
    company, _uc = company_data
    items = open_banking_service.list_institutions(db, company.id, search, country)
    return [InstitutionResponse(**i) for i in items]


@router.post("/open-banking/connect")
def connect_bank(
    data: OpenBankingConnectRequest, db: DB,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
):
    company, _uc = company_data
    return open_banking_service.initiate_connection(
        db, company.id, data.institution_id, data.redirect_url,
    )


@router.get("/open-banking/callback")
def ob_callback(
    db: DB, company_data: CurrentCompany,
    ref: str = "", code: str = "",
):
    company, _uc = company_data
    conn = open_banking_service.handle_callback(db, company.id, ref, code)
    if not conn:
        raise HTTPException(status_code=404, detail="Connessione non trovata")
    return OpenBankingConnectionResponse.model_validate(conn)


@router.get("/open-banking/connections", response_model=OpenBankingConnectionListResponse)
def list_connections(db: DB, company_data: CurrentCompany):
    company, _uc = company_data
    items = open_banking_service.list_connections(db, company.id)
    return OpenBankingConnectionListResponse(
        items=[OpenBankingConnectionResponse.model_validate(c) for c in items],
        total=len(items),
    )


@router.get("/open-banking/connections/{connection_id}", response_model=OpenBankingConnectionResponse)
def get_connection(connection_id: uuid.UUID, db: DB, company_data: CurrentCompany):
    company, _uc = company_data
    conn = open_banking_service.get_connection(db, connection_id, company.id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connessione non trovata")
    return OpenBankingConnectionResponse.model_validate(conn)


@router.delete("/open-banking/connections/{connection_id}")
def delete_connection(
    connection_id: uuid.UUID, db: DB,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
):
    company, _uc = company_data
    ok = open_banking_service.delete_connection(db, connection_id, company.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Connessione non trovata")
    return {"message": "Connessione revocata"}


@router.post("/open-banking/connections/{connection_id}/sync", response_model=OpenBankingSyncLogResponse)
def sync_connection(
    connection_id: uuid.UUID, db: DB,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
):
    company, _uc = company_data
    try:
        log = open_banking_service.sync_connection(db, connection_id, company.id)
        return OpenBankingSyncLogResponse.model_validate(log)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/open-banking/connections/{connection_id}/link", response_model=OpenBankingConnectionResponse)
def link_connection(
    connection_id: uuid.UUID, data: OpenBankingLinkRequest,
    db: DB, company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
):
    company, _uc = company_data
    conn = open_banking_service.link_to_bank_account(
        db, connection_id, uuid.UUID(data.bank_account_id), company.id,
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connessione non trovata")
    return OpenBankingConnectionResponse.model_validate(conn)


@router.post("/open-banking/connections/{connection_id}/renew")
def renew_consent(
    connection_id: uuid.UUID, db: DB,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
):
    company, _uc = company_data
    result = open_banking_service.renew_consent(db, connection_id, company.id)
    if not result:
        raise HTTPException(status_code=404, detail="Connessione non trovata")
    return result


@router.get("/open-banking/connections/{connection_id}/logs", response_model=SyncLogListResponse)
def get_sync_logs(
    connection_id: uuid.UUID, db: DB, company_data: CurrentCompany,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    company, _uc = company_data
    items, total = open_banking_service.get_sync_logs(db, connection_id, company.id, page, page_size)
    return SyncLogListResponse(
        items=[OpenBankingSyncLogResponse.model_validate(l) for l in items],
        total=total,
    )


@router.post("/open-banking/sync-all")
def sync_all(
    db: DB, company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
):
    company, _uc = company_data
    connections = open_banking_service.list_connections(db, company.id)
    results = []
    for conn in connections:
        if conn.sync_attivo and conn.stato.value == "attiva":
            try:
                log = open_banking_service.sync_connection(db, conn.id, company.id)
                results.append({"connection_id": str(conn.id), "status": "ok"})
            except Exception as e:
                results.append({"connection_id": str(conn.id), "error": str(e)})
    return {"synced": len(results), "results": results}


# ===== Fatture Elettroniche =====

@router.post("/invoices/upload", response_model=InvoiceImportResponse)
async def upload_invoice(
    db: DB, current_user: CurrentUser, company_data: CurrentCompany,
    file: UploadFile = File(...),
):
    company, _uc = company_data
    content = await file.read()
    if len(content) > MAX_XML_SIZE:
        raise HTTPException(status_code=413, detail="File troppo grande (max 5MB)")

    inv = invoice_import_service.upload_single(
        db, company.id, current_user.id, content, file.filename or "upload.xml",
        company_piva=company.vat_number or "",
    )
    db.commit()
    db.refresh(inv)
    return InvoiceImportResponse.model_validate(inv)


@router.post("/invoices/upload-batch", response_model=InvoiceImportBatchResponse)
async def upload_batch(
    db: DB, current_user: CurrentUser, company_data: CurrentCompany,
    files: list[UploadFile] = File(...),
):
    company, _uc = company_data
    file_list = []
    for f in files:
        content = await f.read()
        if len(content) > MAX_XML_SIZE:
            continue
        file_list.append((content, f.filename or "upload.xml"))

    if not file_list:
        raise HTTPException(status_code=400, detail="Nessun file valido")

    batch = invoice_import_service.upload_batch(
        db, company.id, current_user.id, file_list,
        company_piva=company.vat_number or "",
    )
    return InvoiceImportBatchResponse.model_validate(batch)


@router.get("/invoices", response_model=InvoiceImportListResponse)
def list_invoices(
    db: DB, company_data: CurrentCompany,
    tipo_documento: str | None = None,
    stato: str | None = None,
    data_da: str | None = None,
    data_a: str | None = None,
    cedente_piva: str | None = None,
    search: str | None = None,
    importo_min: float | None = None,
    importo_max: float | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    company, _uc = company_data
    from datetime import date as date_type
    d_da = date_type.fromisoformat(data_da) if data_da else None
    d_a = date_type.fromisoformat(data_a) if data_a else None

    items, total = invoice_import_service.list_invoices(
        db, company.id,
        tipo_documento=tipo_documento, stato=stato,
        data_da=d_da, data_a=d_a,
        cedente_piva=cedente_piva, search=search,
        importo_min=importo_min, importo_max=importo_max,
        page=page, page_size=page_size,
    )
    return InvoiceImportListResponse(
        items=[InvoiceImportResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/invoices/batches", response_model=InvoiceBatchListResponse)
def list_batches(
    db: DB, company_data: CurrentCompany,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    company, _uc = company_data
    items, total = invoice_import_service.list_batches(db, company.id, page, page_size)
    return InvoiceBatchListResponse(
        items=[InvoiceImportBatchResponse.model_validate(b) for b in items],
        total=total,
    )


@router.get("/invoices/batches/{batch_id}", response_model=InvoiceImportBatchResponse)
def get_batch(batch_id: uuid.UUID, db: DB, company_data: CurrentCompany):
    company, _uc = company_data
    batch = invoice_import_service.get_batch(db, batch_id, company.id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch non trovato")
    return InvoiceImportBatchResponse.model_validate(batch)


@router.get("/invoices/{invoice_id}", response_model=InvoiceImportResponse)
def get_invoice(invoice_id: uuid.UUID, db: DB, company_data: CurrentCompany):
    company, _uc = company_data
    inv = invoice_import_service.get_invoice(db, invoice_id, company.id)
    if not inv:
        raise HTTPException(status_code=404, detail="Fattura non trovata")
    return InvoiceImportResponse.model_validate(inv)


@router.get("/invoices/{invoice_id}/xml")
def download_xml(invoice_id: uuid.UUID, db: DB, company_data: CurrentCompany):
    company, _uc = company_data
    inv = invoice_import_service.get_invoice(db, invoice_id, company.id)
    if not inv or not inv.xml_file_path:
        raise HTTPException(status_code=404, detail="File XML non trovato")
    return FileResponse(
        inv.xml_file_path,
        filename=inv.xml_file_nome or "fattura.xml",
        media_type="application/xml",
    )


@router.get("/invoices/{invoice_id}/pdf")
def download_pdf(invoice_id: uuid.UUID, db: DB, company_data: CurrentCompany):
    company, _uc = company_data
    inv = invoice_import_service.get_invoice(db, invoice_id, company.id)
    if not inv or not inv.pdf_allegato_path:
        raise HTTPException(status_code=404, detail="PDF allegato non trovato")
    return FileResponse(
        inv.pdf_allegato_path,
        filename=f"{inv.numero_fattura or 'fattura'}.pdf",
        media_type="application/pdf",
    )


@router.post("/invoices/{invoice_id}/elaborate", response_model=InvoiceElaborateResponse)
def elaborate_invoice(
    invoice_id: uuid.UUID, db: DB,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
):
    company, _uc = company_data
    try:
        result = invoice_import_service.elaborate(db, invoice_id, company.id, current_user.id)
        return InvoiceElaborateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invoices/elaborate-batch")
def elaborate_batch(
    data: InvoiceBatchElaborateRequest,
    db: DB, current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
):
    company, _uc = company_data
    results = invoice_import_service.elaborate_batch(
        db, company.id, current_user.id,
        invoice_ids=data.invoice_ids,
        filter_stato=data.filter_stato.value if data.filter_stato else None,
    )
    return {"results": results, "total": len(results)}


@router.post("/invoices/{invoice_id}/ignore", response_model=InvoiceImportResponse)
def ignore_invoice(
    invoice_id: uuid.UUID, db: DB,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
):
    company, _uc = company_data
    inv = invoice_import_service.ignore(db, invoice_id, company.id)
    if not inv:
        raise HTTPException(status_code=404, detail="Fattura non trovata")
    return InvoiceImportResponse.model_validate(inv)


# ===== CBI/SEPA =====

@router.post("/cbi/parse", response_model=CBIParseResponse)
async def parse_cbi(
    db: DB, company_data: CurrentCompany,
    file: UploadFile = File(...),
):
    content = await file.read()
    from app.services.parsers.cbi_sepa_parsers import CBIRendicontazioneParser
    parser = CBIRendicontazioneParser()
    records = parser.parse(content)
    return CBIParseResponse(
        records_parsed=len(records),
        records=[{
            "tipo_record": r.tipo_record,
            "riferimento": r.riferimento,
            "data_operazione": r.data_operazione.isoformat() if r.data_operazione else None,
            "importo": str(r.importo),
            "segno": r.segno,
            "causale": r.causale,
            "descrizione": r.descrizione,
        } for r in records],
    )


@router.post("/sepa/validate", response_model=SEPAValidationResponse)
async def validate_sepa(
    db: DB, company_data: CurrentCompany,
    file: UploadFile = File(...),
):
    content = await file.read()
    from app.services.parsers.cbi_sepa_parsers import validate_sepa_xml
    result = validate_sepa_xml(content)
    return SEPAValidationResponse(**result)


@router.post("/cbi/import-rendicontazione")
async def import_rendicontazione(
    db: DB, company_data: CurrentCompany,
    file: UploadFile = File(...),
):
    content = await file.read()
    from app.services.parsers.cbi_sepa_parsers import CBIRendicontazioneParser
    parser = CBIRendicontazioneParser()
    records = parser.parse(content)
    return {"records_imported": len(records), "message": f"Importati {len(records)} record"}


@router.post("/sepa/import-camt053", response_model=CAMT053ImportResponse)
async def import_camt053(
    db: DB, company_data: CurrentCompany,
    file: UploadFile = File(...),
):
    content = await file.read()
    from app.services.parsers.cbi_sepa_parsers import CAMT053Parser
    parser = CAMT053Parser()
    statements = parser.parse(content)

    total_imported = 0
    total_dup = 0
    iban = None

    for stmt in statements:
        iban = stmt.account_iban or iban
        total_imported += len(stmt.entries)

    return CAMT053ImportResponse(
        transactions_imported=total_imported,
        transactions_duplicated=total_dup,
        balance_updated=len(statements) > 0,
        account_iban=iban,
    )


# ===== Webhook =====

@router.get("/webhooks", response_model=WebhookListResponse)
def list_webhooks(db: DB, company_data: CurrentCompany):
    company, _uc = company_data
    items = webhook_service.list_webhooks(db, company.id)
    return WebhookListResponse(
        items=[WebhookEndpointResponse.model_validate(w) for w in items],
        total=len(items),
    )


@router.post("/webhooks", response_model=WebhookEndpointResponse)
def create_webhook(
    data: WebhookEndpointCreate, db: DB,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
):
    company, _uc = company_data
    wh = webhook_service.create_webhook(db, company.id, data.tipo)
    return WebhookEndpointResponse.model_validate(wh)


@router.delete("/webhooks/{webhook_id}")
def delete_webhook(
    webhook_id: uuid.UUID, db: DB,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
):
    company, _uc = company_data
    ok = webhook_service.delete_webhook(db, webhook_id, company.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Webhook non trovato")
    return {"message": "Webhook eliminato"}


# ===== Config by Type (MUST be after all specific routes to avoid path conflicts) =====

@router.get("/{tipo}", response_model=IntegrationConfigResponse)
def get_config(tipo: IntegrationType, db: DB, company_data: CurrentCompany):
    company, _uc = company_data
    cfg = integration_config_service.get_config(db, company.id, tipo)
    return IntegrationConfigResponse.model_validate(cfg)


@router.put("/{tipo}", response_model=IntegrationConfigResponse)
def update_config(
    tipo: IntegrationType, data: IntegrationConfigUpdate,
    db: DB, company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
):
    company, _uc = company_data
    cfg = integration_config_service.update_config(db, company.id, tipo, data.model_dump(exclude_none=True))
    return IntegrationConfigResponse.model_validate(cfg)


@router.post("/{tipo}/test")
def test_connection(
    tipo: IntegrationType, db: DB,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
):
    company, _uc = company_data
    return integration_config_service.test_connection(db, company.id, tipo)


@router.put("/{tipo}/toggle", response_model=IntegrationConfigResponse)
def toggle_integration(
    tipo: IntegrationType, data: IntegrationToggle,
    db: DB, company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
):
    company, _uc = company_data
    cfg = integration_config_service.toggle(db, company.id, tipo, data.is_enabled)
    return IntegrationConfigResponse.model_validate(cfg)
