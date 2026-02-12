"""Dashboard Service — aggregation queries from all modules."""
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session

from app.models.bank_account import BankAccount
from app.models.bank_account_balance import BankAccountBalance
from app.models.cash_flow_alert import CashFlowAlert
from app.models.cash_flow_forecast_line import CashFlowForecastLine
from app.models.dashboard_snapshot import DashboardSnapshot
from app.models.dashboard_widget import DashboardWidget
from app.models.enums import (
    AccountStatus, AlertStatus, BatchStatus, FlowDirection,
    PaymentOrderStatus, ScheduleStatus, WidgetSize, WidgetType,
)
from app.models.import_batch import ImportBatch
from app.models.payment_order import PaymentOrder
from app.models.schedule import Schedule
from app.models.transaction import Transaction


# --- Default widget layout ---

DEFAULT_WIDGETS = [
    (WidgetType.SALDO_TOTALE, 0, 0, WidgetSize.LARGE),
    (WidgetType.CASH_FLOW_MINI, 1, 0, WidgetSize.LARGE),
    (WidgetType.ENTRATE_USCITE, 2, 0, WidgetSize.MEDIUM),
    (WidgetType.SCADENZE, 2, 1, WidgetSize.MEDIUM),
    (WidgetType.RICONCILIAZIONE, 3, 0, WidgetSize.SMALL),
    (WidgetType.PAGAMENTI_PENDENTI, 3, 1, WidgetSize.SMALL),
    (WidgetType.ALERT, 4, 0, WidgetSize.MEDIUM),
    (WidgetType.ATTIVITA_RECENTI, 4, 1, WidgetSize.MEDIUM),
    (WidgetType.AZIONI_RAPIDE, 5, 0, WidgetSize.SMALL),
    (WidgetType.SALDI_PER_CONTO, 5, 1, WidgetSize.SMALL),
]


# --- Main aggregation ---

def get_dashboard_data(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    period_start: date | None = None,
    period_end: date | None = None,
    account_ids: list[uuid.UUID] | None = None,
) -> dict:
    today = date.today()
    start = period_start or (today - timedelta(days=30))
    end = period_end or today

    return {
        "saldi": _get_saldi(db, company_id, account_ids),
        "cash_flow": _get_cashflow_preview(db, company_id),
        "entrate_uscite": _get_entrate_uscite(db, company_id, start, end, account_ids),
        "scadenze": _get_scadenze(db, company_id),
        "riconciliazione": _get_riconciliazione(db, company_id),
        "pagamenti": _get_pagamenti(db, company_id),
        "alert": _get_alert(db, company_id),
        "attivita_recenti": _get_attivita_recenti(db, company_id),
        "quick_actions": get_quick_actions(db, company_id),
        "aggiornato_a": datetime.now(timezone.utc),
    }


def get_dashboard_section(
    db: Session,
    company_id: uuid.UUID,
    section_name: str,
    period_start: date | None = None,
    period_end: date | None = None,
    account_ids: list[uuid.UUID] | None = None,
) -> dict:
    today = date.today()
    start = period_start or (today - timedelta(days=30))
    end = period_end or today

    sections = {
        "saldi": lambda: _get_saldi(db, company_id, account_ids),
        "cash_flow": lambda: _get_cashflow_preview(db, company_id),
        "entrate_uscite": lambda: _get_entrate_uscite(db, company_id, start, end, account_ids),
        "scadenze": lambda: _get_scadenze(db, company_id),
        "riconciliazione": lambda: _get_riconciliazione(db, company_id),
        "pagamenti": lambda: _get_pagamenti(db, company_id),
        "alert": lambda: _get_alert(db, company_id),
        "attivita_recenti": lambda: _get_attivita_recenti(db, company_id),
        "quick_actions": lambda: get_quick_actions(db, company_id),
    }
    getter = sections.get(section_name)
    if getter is None:
        return {}
    return getter()


# --- Private aggregation functions ---

def _get_saldi(db: Session, company_id: uuid.UUID, account_ids: list[uuid.UUID] | None = None) -> dict:
    q = db.query(BankAccount).filter(
        BankAccount.company_id == company_id,
        BankAccount.status == AccountStatus.ACTIVE,
    )
    if account_ids:
        q = q.filter(BankAccount.id.in_(account_ids))

    accounts = q.all()

    # Get yesterday's balances for variation calculation
    yesterday = date.today() - timedelta(days=1)
    yesterday_balances = {}
    for bal in db.query(BankAccountBalance).filter(
        BankAccountBalance.company_id == company_id,
        BankAccountBalance.balance_date == yesterday,
    ).all():
        yesterday_balances[bal.bank_account_id] = bal.current_balance or Decimal("0")

    totale = Decimal("0")
    disponibile = Decimal("0")
    totale_ieri = Decimal("0")
    conti = []

    for acct in accounts:
        saldo = acct.current_balance or Decimal("0")
        disp = acct.available_balance or Decimal("0")
        saldo_ieri = yesterday_balances.get(acct.id, saldo)
        variazione = saldo - saldo_ieri

        totale += saldo
        disponibile += disp
        totale_ieri += saldo_ieri

        conti.append({
            "id": acct.id,
            "nome": acct.nickname or acct.iban or "Conto",
            "banca": acct.bank_name,
            "saldo": saldo,
            "variazione_giorno": variazione,
            "colore": acct.color or "#6b7280",
        })

    variazione_giorno = totale - totale_ieri
    variazione_pct = (
        (variazione_giorno / totale_ieri * 100) if totale_ieri != 0 else Decimal("0")
    )

    return {
        "totale": totale,
        "disponibile": disponibile,
        "variazione_giorno": variazione_giorno,
        "variazione_percentuale": variazione_pct.quantize(Decimal("0.01")),
        "conti": conti,
    }


def _get_entrate_uscite(
    db: Session,
    company_id: uuid.UUID,
    start: date,
    end: date,
    account_ids: list[uuid.UUID] | None = None,
) -> dict:
    q = db.query(
        Transaction.direction,
        func.sum(func.abs(Transaction.amount)),
    ).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_date >= start,
        Transaction.transaction_date <= end,
    )
    if account_ids:
        q = q.filter(Transaction.bank_account_id.in_(account_ids))

    results = q.group_by(Transaction.direction).all()

    entrate = Decimal("0")
    uscite = Decimal("0")
    for direction, total in results:
        if direction == FlowDirection.INFLOW:
            entrate = total or Decimal("0")
        else:
            uscite = total or Decimal("0")

    # Previous period comparison
    period_length = (end - start).days
    prev_start = start - timedelta(days=period_length)
    prev_end = start - timedelta(days=1)

    q_prev = db.query(
        func.sum(case(
            (Transaction.direction == FlowDirection.INFLOW, func.abs(Transaction.amount)),
            else_=Decimal("0"),
        )),
        func.sum(case(
            (Transaction.direction == FlowDirection.OUTFLOW, func.abs(Transaction.amount)),
            else_=Decimal("0"),
        )),
    ).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_date >= prev_start,
        Transaction.transaction_date <= prev_end,
    )
    if account_ids:
        q_prev = q_prev.filter(Transaction.bank_account_id.in_(account_ids))

    prev_entrate, prev_uscite = q_prev.one()
    prev_netto = (prev_entrate or Decimal("0")) - (prev_uscite or Decimal("0"))
    netto = entrate - uscite
    confronto = (
        ((netto - prev_netto) / abs(prev_netto) * 100) if prev_netto != 0 else Decimal("0")
    )

    # Top categories
    top_cats_q = db.query(
        func.coalesce(
            db.query(func.max(
                # Subquery approach - simplify to just use category_id
            )).correlate(Transaction).scalar_subquery(),
            "Non categorizzato"
        ),
        func.sum(func.abs(Transaction.amount)),
    ).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_date >= start,
        Transaction.transaction_date <= end,
    ).group_by(Transaction.category_id).order_by(
        func.sum(func.abs(Transaction.amount)).desc()
    ).limit(5)

    # Simplified: get top categories by amount
    from app.models.category import Category
    top_results = db.query(
        Category.name,
        func.sum(func.abs(Transaction.amount)).label("total"),
    ).join(
        Category, Transaction.category_id == Category.id, isouter=True
    ).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_date >= start,
        Transaction.transaction_date <= end,
    ).group_by(Category.name).order_by(
        func.sum(func.abs(Transaction.amount)).desc()
    ).limit(5).all()

    total_amount = entrate + uscite
    top_categorie = []
    for nome, importo in top_results:
        pct = (importo / total_amount * 100) if total_amount > 0 else Decimal("0")
        top_categorie.append({
            "nome": nome or "Non categorizzato",
            "importo": importo,
            "percentuale": pct.quantize(Decimal("0.01")),
        })

    return {
        "entrate": entrate,
        "uscite": uscite,
        "saldo_netto": netto,
        "confronto_mese_precedente": confronto.quantize(Decimal("0.01")),
        "top_categorie": top_categorie,
    }


def _get_cashflow_preview(db: Session, company_id: uuid.UUID) -> dict:
    today = date.today()

    # Use cash flow summary from existing service
    from app.services import cash_flow_service
    summary = cash_flow_service.get_summary(db, company_id)

    # Mini chart: last 14 days of snapshots
    snapshots = db.query(DashboardSnapshot).filter(
        DashboardSnapshot.company_id == company_id,
        DashboardSnapshot.data >= today - timedelta(days=14),
    ).order_by(DashboardSnapshot.data.asc()).all()

    mini_chart = []
    for snap in snapshots:
        mini_chart.append({
            "data": snap.data,
            "entrate": snap.entrate_giorno,
            "uscite": snap.uscite_giorno,
            "saldo": snap.saldo_totale,
        })

    trend_30 = summary.get("trend_30gg", Decimal("0"))
    if trend_30 > 1000:
        trend = "crescente"
    elif trend_30 < -1000:
        trend = "decrescente"
    else:
        trend = "stabile"

    alert = summary.get("prossimo_alert")
    prossimo_alert_msg = None
    if alert:
        prossimo_alert_msg = alert.messaggio if hasattr(alert, "messaggio") else str(alert)

    return {
        "previsione_7gg": summary.get("previsione_7gg", Decimal("0")),
        "previsione_30gg": summary.get("previsione_30gg", Decimal("0")),
        "trend": trend,
        "prossimo_alert": prossimo_alert_msg,
        "mini_chart_data": mini_chart,
    }


def _get_scadenze(db: Session, company_id: uuid.UUID) -> dict:
    today = date.today()
    in_7gg = today + timedelta(days=7)

    # Count by urgency
    counts = db.query(
        func.count(case(
            (and_(Schedule.data_scadenza == today, Schedule.stato.in_([ScheduleStatus.APERTA, ScheduleStatus.PARZIALMENTE_PAGATA])), 1),
        )),
        func.count(case(
            (and_(Schedule.data_scadenza > today, Schedule.data_scadenza <= in_7gg, Schedule.stato.in_([ScheduleStatus.APERTA, ScheduleStatus.PARZIALMENTE_PAGATA])), 1),
        )),
        func.count(case(
            (Schedule.stato == ScheduleStatus.SCADUTA, 1),
        )),
        func.sum(case(
            (Schedule.stato == ScheduleStatus.SCADUTA, Schedule.importo_totale - Schedule.importo_pagato),
            else_=Decimal("0"),
        )),
    ).filter(
        Schedule.company_id == company_id,
    ).one()

    in_scadenza_oggi = counts[0] or 0
    in_scadenza_7gg = counts[1] or 0
    scadute_conteggio = counts[2] or 0
    scadute_importo = counts[3] or Decimal("0")

    # Next 5 upcoming
    prossime = db.query(Schedule).filter(
        Schedule.company_id == company_id,
        Schedule.data_scadenza >= today,
        Schedule.stato.in_([ScheduleStatus.APERTA, ScheduleStatus.PARZIALMENTE_PAGATA]),
    ).order_by(Schedule.data_scadenza.asc()).limit(5).all()

    prossime_list = []
    for s in prossime:
        prossime_list.append({
            "id": s.id,
            "descrizione": getattr(s, "descrizione", None) or getattr(s, "nome", None),
            "importo": s.importo_totale - s.importo_pagato,
            "data_scadenza": s.data_scadenza,
            "stato": s.stato.value,
        })

    return {
        "in_scadenza_oggi": in_scadenza_oggi,
        "in_scadenza_7gg": in_scadenza_7gg,
        "scadute_conteggio": scadute_conteggio,
        "scadute_importo": scadute_importo,
        "prossime": prossime_list,
    }


def _get_riconciliazione(db: Session, company_id: uuid.UUID) -> dict:
    # Count total and unreconciled transactions
    total_tx = db.query(func.count(Transaction.id)).filter(
        Transaction.company_id == company_id,
    ).scalar() or 0

    verified_tx = db.query(func.count(Transaction.id)).filter(
        Transaction.company_id == company_id,
        Transaction.verified.is_(True),
    ).scalar() or 0

    non_riconciliati = total_tx - verified_tx
    percentuale = (Decimal(verified_tx) / Decimal(total_tx) * 100) if total_tx > 0 else Decimal("0")

    # Unreconciled amount
    importo_non_ric = db.query(func.sum(func.abs(Transaction.amount))).filter(
        Transaction.company_id == company_id,
        Transaction.verified.is_(False),
    ).scalar() or Decimal("0")

    return {
        "percentuale": percentuale.quantize(Decimal("0.01")),
        "movimenti_non_riconciliati": non_riconciliati,
        "importo_non_riconciliato": importo_non_ric,
        "suggerimenti_pendenti": 0,
    }


def _get_pagamenti(db: Session, company_id: uuid.UUID) -> dict:
    today = date.today()
    first_of_month = today.replace(day=1)

    counts = db.query(
        func.count(case(
            (PaymentOrder.stato == PaymentOrderStatus.DA_APPROVARE, 1),
        )),
        func.sum(case(
            (PaymentOrder.stato == PaymentOrderStatus.DA_APPROVARE, PaymentOrder.importo_totale),
            else_=Decimal("0"),
        )),
        func.count(case(
            (PaymentOrder.stato.in_([PaymentOrderStatus.APPROVATA, PaymentOrderStatus.FILE_GENERATO, PaymentOrderStatus.INVIATA_BANCA]), 1),
        )),
        func.count(case(
            (and_(PaymentOrder.stato == PaymentOrderStatus.ESEGUITA, PaymentOrder.updated_at >= datetime(first_of_month.year, first_of_month.month, first_of_month.day, tzinfo=timezone.utc)), 1),
        )),
    ).filter(
        PaymentOrder.company_id == company_id,
    ).one()

    return {
        "da_approvare_conteggio": counts[0] or 0,
        "da_approvare_importo": counts[1] or Decimal("0"),
        "in_attesa_esecuzione": counts[2] or 0,
        "eseguiti_mese": counts[3] or 0,
    }


def _get_alert(db: Session, company_id: uuid.UUID) -> dict:
    alerts = db.query(CashFlowAlert).filter(
        CashFlowAlert.company_id == company_id,
        CashFlowAlert.stato == AlertStatus.ATTIVO,
    ).order_by(CashFlowAlert.data_prevista.asc()).limit(10).all()

    items = []
    for a in alerts:
        gravita = "critical" if a.tipo.value in ("saldo_negativo",) else "warning"
        items.append({
            "id": a.id,
            "tipo": a.tipo.value,
            "messaggio": a.messaggio,
            "gravita": gravita,
            "data_prevista": a.data_prevista,
        })

    return {
        "items": items,
        "totale": len(items),
    }


def _get_attivita_recenti(db: Session, company_id: uuid.UUID, limit: int = 10) -> list[dict]:
    activities = []

    # Recent imports
    imports = db.query(ImportBatch).filter(
        ImportBatch.company_id == company_id,
        ImportBatch.status == BatchStatus.COMPLETED,
    ).order_by(ImportBatch.completed_at.desc().nullslast()).limit(5).all()

    for imp in imports:
        activities.append({
            "tipo": "import",
            "descrizione": f"Importazione completata ({getattr(imp, 'total_count', '?')} movimenti)",
            "data": imp.completed_at or imp.created_at,
            "link": "/movimenti",
        })

    # Recent schedules
    schedules = db.query(Schedule).filter(
        Schedule.company_id == company_id,
    ).order_by(Schedule.created_at.desc()).limit(5).all()

    for s in schedules:
        desc = getattr(s, "descrizione", None) or getattr(s, "nome", None) or "Scadenza"
        activities.append({
            "tipo": "schedule",
            "descrizione": f"Scadenza: {desc}",
            "data": s.created_at,
            "link": f"/scadenzario",
        })

    # Recent payments
    payments = db.query(PaymentOrder).filter(
        PaymentOrder.company_id == company_id,
    ).order_by(PaymentOrder.updated_at.desc()).limit(5).all()

    for p in payments:
        activities.append({
            "tipo": "payment",
            "descrizione": f"Pagamento {p.stato.value}: {p.importo_totale} EUR",
            "data": p.updated_at,
            "link": "/pagamenti",
        })

    # Recent alerts
    alerts = db.query(CashFlowAlert).filter(
        CashFlowAlert.company_id == company_id,
    ).order_by(CashFlowAlert.created_at.desc()).limit(5).all()

    for a in alerts:
        activities.append({
            "tipo": "alert",
            "descrizione": a.messaggio,
            "data": a.created_at,
            "link": "/cash-flow",
        })

    # Sort by date descending and take limit
    activities.sort(key=lambda x: x["data"], reverse=True)
    return activities[:limit]


# --- Widget CRUD ---

def get_or_create_widgets(
    db: Session, user_id: uuid.UUID, company_id: uuid.UUID
) -> list[DashboardWidget]:
    widgets = db.query(DashboardWidget).filter(
        DashboardWidget.user_id == user_id,
        DashboardWidget.company_id == company_id,
    ).order_by(DashboardWidget.posizione.asc(), DashboardWidget.colonna.asc()).all()

    if not widgets:
        widgets = _create_default_widgets(db, user_id, company_id)

    return widgets


def _create_default_widgets(
    db: Session, user_id: uuid.UUID, company_id: uuid.UUID
) -> list[DashboardWidget]:
    widgets = []
    for wtype, pos, col, size in DEFAULT_WIDGETS:
        w = DashboardWidget(
            user_id=user_id,
            company_id=company_id,
            widget_type=wtype,
            posizione=pos,
            colonna=col,
            dimensione=size,
            visibile=True,
        )
        db.add(w)
        widgets.append(w)

    db.commit()
    for w in widgets:
        db.refresh(w)
    return widgets


def update_widgets(
    db: Session,
    user_id: uuid.UUID,
    company_id: uuid.UUID,
    widgets_data: list[dict],
) -> list[DashboardWidget]:
    # Delete existing widgets for this user/company
    db.query(DashboardWidget).filter(
        DashboardWidget.user_id == user_id,
        DashboardWidget.company_id == company_id,
    ).delete()

    widgets = []
    for wd in widgets_data:
        w = DashboardWidget(
            user_id=user_id,
            company_id=company_id,
            widget_type=WidgetType(wd["widget_type"]),
            posizione=wd["posizione"],
            colonna=wd.get("colonna", 0),
            dimensione=WidgetSize(wd.get("dimensione", "medium")),
            visibile=wd.get("visibile", True),
            configurazione=wd.get("configurazione"),
        )
        db.add(w)
        widgets.append(w)

    db.commit()
    for w in widgets:
        db.refresh(w)
    return widgets


def reset_widgets(
    db: Session, user_id: uuid.UUID, company_id: uuid.UUID
) -> list[DashboardWidget]:
    db.query(DashboardWidget).filter(
        DashboardWidget.user_id == user_id,
        DashboardWidget.company_id == company_id,
    ).delete()
    db.commit()
    return _create_default_widgets(db, user_id, company_id)


# --- Snapshot ---

def generate_snapshot(db: Session, company_id: uuid.UUID) -> DashboardSnapshot:
    today = date.today()

    # Gather current data
    saldi = _get_saldi(db, company_id)
    riconciliazione = _get_riconciliazione(db, company_id)
    scadenze = _get_scadenze(db, company_id)
    pagamenti = _get_pagamenti(db, company_id)
    alert_data = _get_alert(db, company_id)

    # Today's transactions
    entrate_oggi = db.query(func.sum(func.abs(Transaction.amount))).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_date == today,
        Transaction.direction == FlowDirection.INFLOW,
    ).scalar() or Decimal("0")

    uscite_oggi = db.query(func.sum(func.abs(Transaction.amount))).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_date == today,
        Transaction.direction == FlowDirection.OUTFLOW,
    ).scalar() or Decimal("0")

    # Cash flow forecast 30gg
    from app.services import cash_flow_service
    summary = cash_flow_service.get_summary(db, company_id)

    # Upsert snapshot
    existing = db.query(DashboardSnapshot).filter(
        DashboardSnapshot.company_id == company_id,
        DashboardSnapshot.data == today,
    ).first()

    if existing:
        existing.saldo_totale = saldi["totale"]
        existing.entrate_giorno = entrate_oggi
        existing.uscite_giorno = uscite_oggi
        existing.movimenti_non_riconciliati = riconciliazione["movimenti_non_riconciliati"]
        existing.scadenze_scadute_importo = scadenze["scadute_importo"]
        existing.scadenze_scadute_conteggio = scadenze["scadute_conteggio"]
        existing.pagamenti_da_approvare = pagamenti["da_approvare_conteggio"]
        existing.previsione_30gg = summary.get("previsione_30gg", Decimal("0"))
        existing.alert_attivi = alert_data["totale"]
        db.commit()
        db.refresh(existing)
        return existing

    snapshot = DashboardSnapshot(
        company_id=company_id,
        data=today,
        saldo_totale=saldi["totale"],
        entrate_giorno=entrate_oggi,
        uscite_giorno=uscite_oggi,
        movimenti_non_riconciliati=riconciliazione["movimenti_non_riconciliati"],
        scadenze_scadute_importo=scadenze["scadute_importo"],
        scadenze_scadute_conteggio=scadenze["scadute_conteggio"],
        pagamenti_da_approvare=pagamenti["da_approvare_conteggio"],
        previsione_30gg=summary.get("previsione_30gg", Decimal("0")),
        alert_attivi=alert_data["totale"],
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_snapshots(
    db: Session,
    company_id: uuid.UUID,
    data_da: date | None = None,
    data_a: date | None = None,
) -> list[DashboardSnapshot]:
    q = db.query(DashboardSnapshot).filter(
        DashboardSnapshot.company_id == company_id,
    )
    if data_da:
        q = q.filter(DashboardSnapshot.data >= data_da)
    if data_a:
        q = q.filter(DashboardSnapshot.data <= data_a)

    return q.order_by(DashboardSnapshot.data.asc()).all()


# --- Trend ---

def get_trend(
    db: Session,
    company_id: uuid.UUID,
    kpi: str,
    periodo: str = "30g",
) -> dict:
    days = {"7g": 7, "30g": 30, "90g": 90, "1a": 365}.get(periodo, 30)
    data_da = date.today() - timedelta(days=days)

    snapshots = get_snapshots(db, company_id, data_da=data_da)

    kpi_map = {
        "saldo_totale": "saldo_totale",
        "entrate": "entrate_giorno",
        "uscite": "uscite_giorno",
        "non_riconciliati": "movimenti_non_riconciliati",
        "scadute": "scadenze_scadute_conteggio",
        "alert": "alert_attivi",
    }

    field = kpi_map.get(kpi, "saldo_totale")
    punti = []
    for snap in snapshots:
        punti.append({
            "data": snap.data,
            "valore": Decimal(str(getattr(snap, field, 0))),
        })

    # Calculate variation
    variazione = Decimal("0")
    trend = "stabile"
    if len(punti) >= 2:
        first_val = punti[0]["valore"]
        last_val = punti[-1]["valore"]
        if first_val != 0:
            variazione = ((last_val - first_val) / abs(first_val) * 100).quantize(Decimal("0.01"))
        if last_val > first_val:
            trend = "crescente"
        elif last_val < first_val:
            trend = "decrescente"

    return {
        "kpi": kpi,
        "punti": punti,
        "variazione": variazione,
        "trend": trend,
    }


# --- Quick Actions ---

def get_quick_actions(db: Session, company_id: uuid.UUID) -> list[dict]:
    actions = []
    today = date.today()

    # Check unreconciled transactions
    non_ric = db.query(func.count(Transaction.id)).filter(
        Transaction.company_id == company_id,
        Transaction.verified.is_(False),
    ).scalar() or 0

    if non_ric > 10:
        actions.append({
            "azione": "riconcilia",
            "titolo": "Riconcilia movimenti",
            "descrizione": f"{non_ric} movimenti da riconciliare",
            "link": "/riconciliazione",
            "priorita": 1,
            "icona": "check-circle",
        })

    # Check overdue schedules
    scadute = db.query(func.count(Schedule.id)).filter(
        Schedule.company_id == company_id,
        Schedule.stato == ScheduleStatus.SCADUTA,
    ).scalar() or 0

    if scadute > 0:
        actions.append({
            "azione": "verifica_scadenze",
            "titolo": "Verifica scadenze scadute",
            "descrizione": f"{scadute} scadenze scadute",
            "link": "/scadenzario?stato=scaduta",
            "priorita": 2,
            "icona": "alert-triangle",
        })

    # Check pending approvals
    da_approvare = db.query(func.count(PaymentOrder.id)).filter(
        PaymentOrder.company_id == company_id,
        PaymentOrder.stato == PaymentOrderStatus.DA_APPROVARE,
    ).scalar() or 0

    if da_approvare > 0:
        actions.append({
            "azione": "approva_pagamenti",
            "titolo": "Approva pagamenti",
            "descrizione": f"{da_approvare} pagamenti in attesa",
            "link": "/pagamenti?stato=da_approvare",
            "priorita": 3,
            "icona": "credit-card",
        })

    # Check if no recent imports
    recent_import = db.query(ImportBatch).filter(
        ImportBatch.company_id == company_id,
        ImportBatch.created_at >= datetime(
            (today - timedelta(days=7)).year,
            (today - timedelta(days=7)).month,
            (today - timedelta(days=7)).day,
            tzinfo=timezone.utc,
        ),
    ).first()

    if not recent_import:
        actions.append({
            "azione": "importa",
            "titolo": "Importa movimenti",
            "descrizione": "Nessuna importazione negli ultimi 7 giorni",
            "link": "/movimenti",
            "priorita": 4,
            "icona": "upload",
        })

    # Check active alerts
    alert_count = db.query(func.count(CashFlowAlert.id)).filter(
        CashFlowAlert.company_id == company_id,
        CashFlowAlert.stato == AlertStatus.ATTIVO,
    ).scalar() or 0

    if alert_count > 0:
        actions.append({
            "azione": "verifica_alert",
            "titolo": "Verifica alert",
            "descrizione": f"{alert_count} alert attivi",
            "link": "/cash-flow",
            "priorita": 5,
            "icona": "bell",
        })

    actions.sort(key=lambda x: x["priorita"])
    return actions
