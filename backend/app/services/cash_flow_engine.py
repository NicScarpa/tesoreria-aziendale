"""Cash Flow Engine — core calculation logic.

Generates projections by combining real transactions, scheduled payments,
planned payment orders, recurring schedules, and historical estimates.
"""
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.bank_account import BankAccount
from app.models.enums import (
    AccountStatus, CashFlowLineType, CashFlowSource, ConfidenceLevel,
    FlowDirection, PaymentOrderStatus, RecurrenceType,
    ScheduleStatus, TransactionStatus,
)
from app.models.schedule import Schedule
from app.models.transaction import Transaction
from app.models.payment_order import PaymentOrder


_RECURRENCE_DELTAS = {
    RecurrenceType.SETTIMANALE: relativedelta(weeks=1),
    RecurrenceType.MENSILE: relativedelta(months=1),
    RecurrenceType.BIMESTRALE: relativedelta(months=2),
    RecurrenceType.TRIMESTRALE: relativedelta(months=3),
    RecurrenceType.SEMESTRALE: relativedelta(months=6),
    RecurrenceType.ANNUALE: relativedelta(years=1),
}


def _confidence_by_days(days_until: int) -> ConfidenceLevel:
    """Assign confidence based on how far in the future the date is."""
    if days_until <= 7:
        return ConfidenceLevel.CERTA
    elif days_until <= 30:
        return ConfidenceLevel.ALTA
    elif days_until <= 90:
        return ConfidenceLevel.MEDIA
    return ConfidenceLevel.BASSA


def _get_category_name(db: Session, category_id: uuid.UUID | None) -> str | None:
    if not category_id:
        return None
    from app.models.category import Category
    cat = db.get(Category, category_id)
    return cat.name if cat else None


def generate_cash_flow_projection(
    db: Session,
    company_id: uuid.UUID,
    *,
    data_inizio: date | None = None,
    data_fine: date | None = None,
    bank_account_ids: list[uuid.UUID] | None = None,
    includi_scadenze: bool = True,
    includi_pagamenti: bool = True,
    includi_ricorrenze: bool = True,
    includi_stime_storiche: bool = False,
) -> dict:
    """Generate a real-time cash flow projection."""
    today = date.today()
    data_inizio = data_inizio or today - timedelta(days=30)
    data_fine = data_fine or today + timedelta(days=90)

    # 1. Calculate initial balance
    account_q = db.query(BankAccount).filter(
        BankAccount.company_id == company_id,
        BankAccount.status == AccountStatus.ACTIVE,
    )
    if bank_account_ids:
        account_q = account_q.filter(BankAccount.id.in_(bank_account_ids))
    accounts = account_q.all()
    account_ids = [a.id for a in accounts]

    saldo_iniziale = sum(
        (a.current_balance or Decimal("0")) for a in accounts
    )

    lines: list[dict] = []

    # 2. Real transactions (past & present)
    txs = (
        db.query(Transaction)
        .filter(
            Transaction.company_id == company_id,
            Transaction.bank_account_id.in_(account_ids) if account_ids else True,
            Transaction.status == TransactionStatus.BOOKED,
            Transaction.hidden_at.is_(None),
            Transaction.transaction_date >= data_inizio,
            Transaction.transaction_date <= min(today, data_fine),
        )
        .order_by(Transaction.transaction_date.asc())
        .all()
    )
    for tx in txs:
        is_entrata = tx.direction == FlowDirection.INFLOW
        importo = abs(tx.amount)
        lines.append({
            "data": tx.transaction_date,
            "tipo": CashFlowLineType.ENTRATA.value if is_entrata else CashFlowLineType.USCITA.value,
            "importo": importo,
            "categoria": _get_category_name(db, tx.category_id),
            "descrizione": tx.description,
            "fonte": CashFlowSource.MOVIMENTO_REALE.value,
            "fonte_id": str(tx.id),
            "confidenza": ConfidenceLevel.CERTA.value,
            "is_realizzata": True,
        })

    # 3. Scheduled payments (future, open/partial only — not paid!)
    if includi_scadenze:
        open_statuses = [ScheduleStatus.APERTA, ScheduleStatus.PARZIALMENTE_PAGATA]
        schedules = (
            db.query(Schedule)
            .filter(
                Schedule.company_id == company_id,
                Schedule.stato.in_(open_statuses),
                Schedule.data_scadenza > today,
                Schedule.data_scadenza <= data_fine,
            )
            .all()
        )
        for s in schedules:
            importo_residuo = s.importo_totale - s.importo_pagato
            if importo_residuo <= 0:
                continue
            days_until = (s.data_scadenza - today).days
            is_entrata = s.tipo.value == "attiva"
            lines.append({
                "data": s.data_scadenza,
                "tipo": CashFlowLineType.ENTRATA.value if is_entrata else CashFlowLineType.USCITA.value,
                "importo": importo_residuo,
                "categoria": _get_category_name(db, s.categoria_id),
                "descrizione": s.descrizione,
                "fonte": CashFlowSource.SCADENZA.value,
                "fonte_id": str(s.id),
                "confidenza": _confidence_by_days(days_until).value,
                "is_realizzata": False,
            })

    # 4. Payment orders (approved/sent to bank, not yet executed)
    if includi_pagamenti:
        active_po_statuses = [
            PaymentOrderStatus.APPROVATA,
            PaymentOrderStatus.FILE_GENERATO,
            PaymentOrderStatus.INVIATA_BANCA,
        ]
        payment_orders = (
            db.query(PaymentOrder)
            .filter(
                PaymentOrder.company_id == company_id,
                PaymentOrder.stato.in_(active_po_statuses),
                PaymentOrder.data_esecuzione_richiesta > today,
                PaymentOrder.data_esecuzione_richiesta <= data_fine,
            )
            .all()
        )
        for po in payment_orders:
            lines.append({
                "data": po.data_esecuzione_richiesta,
                "tipo": CashFlowLineType.USCITA.value,
                "importo": po.importo_totale,
                "categoria": None,
                "descrizione": f"Ordine pagamento {po.riferimento_interno}",
                "fonte": CashFlowSource.PAGAMENTO_PIANIFICATO.value,
                "fonte_id": str(po.id),
                "confidenza": ConfidenceLevel.CERTA.value,
                "is_realizzata": False,
            })

    # 5. Recurring schedule projections
    if includi_ricorrenze:
        recurring = (
            db.query(Schedule)
            .filter(
                Schedule.company_id == company_id,
                Schedule.is_ricorrente == True,  # noqa: E712
                Schedule.ricorrenza_attiva == True,  # noqa: E712
                Schedule.ricorrenza_tipo.isnot(None),
            )
            .all()
        )
        for s in recurring:
            delta = _RECURRENCE_DELTAS.get(s.ricorrenza_tipo)
            if not delta:
                continue
            next_date = s.ricorrenza_prossima_generazione or (s.data_scadenza + delta)
            is_entrata = s.tipo.value == "attiva"
            max_projections = 12
            count = 0
            while next_date <= data_fine and count < max_projections:
                if next_date > today:
                    if s.ricorrenza_fine and next_date > s.ricorrenza_fine:
                        break
                    days_until = (next_date - today).days
                    lines.append({
                        "data": next_date,
                        "tipo": CashFlowLineType.ENTRATA.value if is_entrata else CashFlowLineType.USCITA.value,
                        "importo": s.importo_totale,
                        "categoria": _get_category_name(db, s.categoria_id),
                        "descrizione": f"Ricorrenza: {s.descrizione}",
                        "fonte": CashFlowSource.RICORRENZA.value,
                        "fonte_id": str(s.id),
                        "confidenza": _confidence_by_days(days_until).value,
                        "is_realizzata": False,
                    })
                next_date = next_date + delta
                count += 1

    # 6. Historical estimates (optional)
    if includi_stime_storiche:
        estimates = _calculate_historical_estimates(db, company_id, account_ids, today, data_fine)
        lines.extend(estimates)

    # Sort chronologically and calculate running balance
    lines.sort(key=lambda x: x["data"])

    running = saldo_iniziale
    totale_entrate = Decimal("0")
    totale_uscite = Decimal("0")

    for line in lines:
        importo = line["importo"]
        if line["tipo"] == CashFlowLineType.ENTRATA.value:
            running += importo
            totale_entrate += importo
        else:
            running -= importo
            totale_uscite += importo
        line["saldo_progressivo"] = running

    return {
        "saldo_iniziale": saldo_iniziale,
        "saldo_finale": running,
        "totale_entrate": totale_entrate,
        "totale_uscite": totale_uscite,
        "data_inizio": data_inizio,
        "data_fine": data_fine,
        "lines": lines,
    }


def _calculate_historical_estimates(
    db: Session,
    company_id: uuid.UUID,
    account_ids: list[uuid.UUID],
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Generate estimates based on 3-month weighted moving average by category."""
    three_months_ago = start_date - timedelta(days=90)

    rows = (
        db.query(
            Transaction.category_id,
            Transaction.direction,
            func.avg(Transaction.amount).label("avg_amount"),
        )
        .filter(
            Transaction.company_id == company_id,
            Transaction.bank_account_id.in_(account_ids) if account_ids else True,
            Transaction.status == TransactionStatus.BOOKED,
            Transaction.hidden_at.is_(None),
            Transaction.transaction_date >= three_months_ago,
            Transaction.transaction_date <= start_date,
        )
        .group_by(Transaction.category_id, Transaction.direction)
        .all()
    )

    estimates = []
    for cat_id, direction, avg_amount in rows:
        if avg_amount is None or abs(avg_amount) < 1:
            continue
        cat_name = _get_category_name(db, cat_id)
        is_entrata = direction == FlowDirection.INFLOW
        # Project monthly for remaining period
        current = start_date + timedelta(days=15)
        while current <= end_date:
            estimates.append({
                "data": current,
                "tipo": CashFlowLineType.ENTRATA.value if is_entrata else CashFlowLineType.USCITA.value,
                "importo": abs(Decimal(str(avg_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "categoria": cat_name,
                "descrizione": f"Stima storica: {cat_name or 'Non categorizzato'}",
                "fonte": CashFlowSource.STIMA_STORICA.value,
                "fonte_id": None,
                "confidenza": ConfidenceLevel.BASSA.value,
                "is_realizzata": False,
            })
            current += relativedelta(months=1)

    return estimates


def calculate_variance(db: Session, forecast_id: uuid.UUID) -> dict:
    """Compare forecast lines vs actual transactions for past dates."""
    from app.models.cash_flow_forecast import CashFlowForecast
    from app.models.cash_flow_forecast_line import CashFlowForecastLine

    forecast = db.get(CashFlowForecast, forecast_id)
    if not forecast:
        return {"forecast_id": forecast_id, "accuracy": Decimal("0"), "totale_previsto": Decimal("0"),
                "totale_reale": Decimal("0"), "varianza_totale": Decimal("0"), "lines": []}

    today = date.today()
    past_lines = (
        db.query(CashFlowForecastLine)
        .filter(
            CashFlowForecastLine.forecast_id == forecast_id,
            CashFlowForecastLine.data <= today,
        )
        .all()
    )

    # Get actual transactions for the same period
    actual_by_date: dict[date, Decimal] = defaultdict(Decimal)
    txs = (
        db.query(Transaction)
        .filter(
            Transaction.company_id == forecast.company_id,
            Transaction.status == TransactionStatus.BOOKED,
            Transaction.hidden_at.is_(None),
            Transaction.transaction_date >= forecast.data_inizio,
            Transaction.transaction_date <= today,
        )
        .all()
    )
    for tx in txs:
        sign = Decimal("1") if tx.direction == FlowDirection.INFLOW else Decimal("-1")
        actual_by_date[tx.transaction_date] += abs(tx.amount) * sign

    variance_lines = []
    totale_previsto = Decimal("0")
    totale_reale = Decimal("0")

    for line in past_lines:
        previsto = line.importo if line.tipo.value == "entrata" else -line.importo
        reale = actual_by_date.get(line.data, Decimal("0"))
        varianza = reale - previsto
        pct = (varianza / abs(previsto) * 100) if previsto != 0 else None

        totale_previsto += abs(previsto)
        totale_reale += abs(reale)

        variance_lines.append({
            "data": line.data,
            "categoria": line.categoria,
            "importo_previsto": abs(previsto),
            "importo_reale": abs(reale),
            "varianza": varianza,
            "varianza_percentuale": pct.quantize(Decimal("0.01")) if pct is not None else None,
        })

    varianza_totale = totale_reale - totale_previsto
    accuracy = Decimal("0")
    if totale_previsto > 0:
        accuracy = max(Decimal("0"),
                      (Decimal("1") - abs(varianza_totale) / totale_previsto) * 100)
        accuracy = accuracy.quantize(Decimal("0.01"))

    return {
        "forecast_id": forecast_id,
        "accuracy": accuracy,
        "totale_previsto": totale_previsto,
        "totale_reale": totale_reale,
        "varianza_totale": varianza_totale,
        "lines": variance_lines,
    }


def calculate_runway(db: Session, company_id: uuid.UUID) -> dict:
    """Calculate burn rate and runway based on last 3 months."""
    today = date.today()
    three_months_ago = today - timedelta(days=90)

    # Current balance
    accounts = (
        db.query(BankAccount)
        .filter(
            BankAccount.company_id == company_id,
            BankAccount.status == AccountStatus.ACTIVE,
        )
        .all()
    )
    saldo_attuale = sum((a.current_balance or Decimal("0")) for a in accounts)

    # Net cash flow last 3 months
    outflows = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.company_id == company_id,
            Transaction.direction == FlowDirection.OUTFLOW,
            Transaction.status == TransactionStatus.BOOKED,
            Transaction.hidden_at.is_(None),
            Transaction.transaction_date >= three_months_ago,
            Transaction.transaction_date <= today,
        )
        .scalar()
    )
    inflows = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.company_id == company_id,
            Transaction.direction == FlowDirection.INFLOW,
            Transaction.status == TransactionStatus.BOOKED,
            Transaction.hidden_at.is_(None),
            Transaction.transaction_date >= three_months_ago,
            Transaction.transaction_date <= today,
        )
        .scalar()
    )

    net_outflow_3m = abs(Decimal(str(outflows))) - abs(Decimal(str(inflows)))
    burn_rate_mensile = (net_outflow_3m / 3).quantize(Decimal("0.01")) if net_outflow_3m > 0 else Decimal("0")

    runway_mesi = Decimal("0")
    data_esaurimento = None
    if burn_rate_mensile > 0:
        runway_mesi = (saldo_attuale / burn_rate_mensile).quantize(Decimal("0.1"))
        days_until = int(runway_mesi * 30)
        data_esaurimento = today + timedelta(days=days_until)

    return {
        "saldo_attuale": saldo_attuale,
        "burn_rate_mensile": burn_rate_mensile,
        "runway_mesi": runway_mesi,
        "data_esaurimento": data_esaurimento,
        "mesi_analisi": 3,
    }


def calculate_seasonality(db: Session, company_id: uuid.UUID) -> dict:
    """Analyze transaction patterns by month over available history."""
    twelve_months_ago = date.today() - timedelta(days=365)

    rows = (
        db.query(
            func.extract("month", Transaction.transaction_date).label("mese"),
            Transaction.direction,
            func.sum(Transaction.amount).label("totale"),
            func.count(func.distinct(
                func.extract("year", Transaction.transaction_date)
            )).label("anni"),
        )
        .filter(
            Transaction.company_id == company_id,
            Transaction.status == TransactionStatus.BOOKED,
            Transaction.hidden_at.is_(None),
            Transaction.transaction_date >= twelve_months_ago,
        )
        .group_by("mese", Transaction.direction)
        .all()
    )

    monthly: dict[int, dict] = {}
    for mese, direction, totale, anni in rows:
        mese_int = int(mese)
        if mese_int not in monthly:
            monthly[mese_int] = {"entrate": Decimal("0"), "uscite": Decimal("0"), "anni": 1}
        divisore = max(int(anni), 1)
        avg = (abs(Decimal(str(totale))) / divisore).quantize(Decimal("0.01"))
        if direction == FlowDirection.INFLOW:
            monthly[mese_int]["entrate"] = avg
        else:
            monthly[mese_int]["uscite"] = avg
        monthly[mese_int]["anni"] = max(monthly[mese_int]["anni"], int(anni))

    mesi = []
    for m in range(1, 13):
        data = monthly.get(m, {"entrate": Decimal("0"), "uscite": Decimal("0")})
        mesi.append({
            "mese": m,
            "entrate_medie": data["entrate"],
            "uscite_medie": data["uscite"],
            "saldo_netto_medio": data["entrate"] - data["uscite"],
        })

    return {
        "mesi": mesi,
        "periodo_analisi_mesi": 12,
    }


def calculate_trends(
    db: Session,
    company_id: uuid.UUID,
    *,
    mesi: int = 6,
    raggruppamento: str = "mensile",
) -> dict:
    """Calculate entry/exit trends over the specified period."""
    today = date.today()
    start = today - relativedelta(months=mesi)

    txs = (
        db.query(Transaction)
        .filter(
            Transaction.company_id == company_id,
            Transaction.status == TransactionStatus.BOOKED,
            Transaction.hidden_at.is_(None),
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= today,
        )
        .order_by(Transaction.transaction_date.asc())
        .all()
    )

    # Group by period
    buckets: dict[str, dict] = defaultdict(lambda: {"entrate": Decimal("0"), "uscite": Decimal("0")})
    for tx in txs:
        if raggruppamento == "settimanale":
            key = tx.transaction_date.strftime("%G-W%V")
        elif raggruppamento == "giornaliero":
            key = tx.transaction_date.isoformat()
        else:  # mensile
            key = tx.transaction_date.strftime("%Y-%m")

        importo = abs(tx.amount)
        if tx.direction == FlowDirection.INFLOW:
            buckets[key]["entrate"] += importo
        else:
            buckets[key]["uscite"] += importo

    punti = []
    for periodo in sorted(buckets.keys()):
        data = buckets[periodo]
        punti.append({
            "periodo": periodo,
            "entrate": data["entrate"],
            "uscite": data["uscite"],
            "saldo_netto": data["entrate"] - data["uscite"],
        })

    # Determine trend direction
    def _trend_direction(values: list[Decimal]) -> str:
        if len(values) < 2:
            return "stabile"
        first_half = sum(values[:len(values)//2]) / max(len(values)//2, 1)
        second_half = sum(values[len(values)//2:]) / max(len(values) - len(values)//2, 1)
        delta = second_half - first_half
        threshold = first_half * Decimal("0.05")
        if delta > threshold:
            return "crescente"
        elif delta < -threshold:
            return "decrescente"
        return "stabile"

    entrate_vals = [p["entrate"] for p in punti]
    uscite_vals = [p["uscite"] for p in punti]

    return {
        "punti": punti,
        "trend_entrate": _trend_direction(entrate_vals),
        "trend_uscite": _trend_direction(uscite_vals),
        "raggruppamento": raggruppamento,
    }


def apply_scenarios(db: Session, forecast_id: uuid.UUID) -> dict:
    """Apply active scenarios to a forecast and return adjusted projection."""
    from app.models.cash_flow_forecast import CashFlowForecast
    from app.models.cash_flow_forecast_line import CashFlowForecastLine
    from app.models.cash_flow_scenario import CashFlowScenario

    forecast = db.get(CashFlowForecast, forecast_id)
    if not forecast:
        return {}

    # Get base lines
    base_lines = (
        db.query(CashFlowForecastLine)
        .filter(CashFlowForecastLine.forecast_id == forecast_id)
        .order_by(CashFlowForecastLine.data.asc())
        .all()
    )

    # Get active scenarios
    scenarios = (
        db.query(CashFlowScenario)
        .filter(
            CashFlowScenario.forecast_id == forecast_id,
            CashFlowScenario.attivo == True,  # noqa: E712
        )
        .all()
    )

    # Convert to mutable dicts
    adjusted_lines = []
    for line in base_lines:
        adjusted_lines.append({
            "data": line.data,
            "tipo": line.tipo.value,
            "importo": line.importo,
            "categoria": line.categoria,
            "descrizione": line.descrizione,
            "fonte": line.fonte.value,
            "fonte_id": line.fonte_id,
            "confidenza": line.confidenza.value,
            "is_realizzata": line.is_realizzata,
            "saldo_progressivo": Decimal("0"),
        })

    # Apply each scenario
    for sc in scenarios:
        adj_type = sc.tipo_aggiustamento.value

        if adj_type == "aggiunta":
            adjusted_lines.append({
                "data": sc.data_modificata or date.today(),
                "tipo": sc.tipo_movimento.value if sc.tipo_movimento else CashFlowLineType.ENTRATA.value,
                "importo": sc.importo_modificato or Decimal("0"),
                "categoria": sc.categoria,
                "descrizione": f"Scenario: {sc.nome}",
                "fonte": CashFlowSource.MANUALE.value,
                "fonte_id": str(sc.id),
                "confidenza": ConfidenceLevel.BASSA.value,
                "is_realizzata": False,
                "saldo_progressivo": Decimal("0"),
            })

        elif adj_type == "rimozione":
            adjusted_lines = [
                l for l in adjusted_lines
                if not (l["data"] == sc.data_originale and
                       l["categoria"] == sc.categoria and
                       not l["is_realizzata"])
            ]

        elif adj_type == "modifica_importo":
            for l in adjusted_lines:
                if (l["data"] == sc.data_originale and
                    l["categoria"] == sc.categoria and
                    not l["is_realizzata"]):
                    l["importo"] = sc.importo_modificato or l["importo"]

        elif adj_type == "spostamento_data":
            for l in adjusted_lines:
                if (l["data"] == sc.data_originale and
                    l["categoria"] == sc.categoria and
                    not l["is_realizzata"]):
                    l["data"] = sc.data_modificata or l["data"]

    # Re-sort and recalculate running balance
    adjusted_lines.sort(key=lambda x: x["data"])
    running = forecast.saldo_iniziale
    totale_entrate = Decimal("0")
    totale_uscite = Decimal("0")

    for line in adjusted_lines:
        importo = line["importo"]
        if line["tipo"] == CashFlowLineType.ENTRATA.value:
            running += importo
            totale_entrate += importo
        else:
            running -= importo
            totale_uscite += importo
        line["saldo_progressivo"] = running

    return {
        "saldo_iniziale": forecast.saldo_iniziale,
        "saldo_finale": running,
        "totale_entrate": totale_entrate,
        "totale_uscite": totale_uscite,
        "data_inizio": forecast.data_inizio,
        "data_fine": forecast.data_fine,
        "lines": adjusted_lines,
    }


def detect_alerts(
    db: Session,
    company_id: uuid.UUID,
    projection_lines: list[dict],
    *,
    min_cash_threshold: Decimal = Decimal("10000"),
    critical_cash_threshold: Decimal = Decimal("0"),
) -> list[dict]:
    """Detect alert conditions from projection lines."""
    alerts = []
    seen_dates: set[date] = set()

    for line in projection_lines:
        saldo = line.get("saldo_progressivo", Decimal("0"))
        line_date = line["data"]

        if line_date in seen_dates:
            continue

        if saldo < critical_cash_threshold:
            alerts.append({
                "tipo": "saldo_negativo",
                "data_prevista": line_date,
                "saldo_previsto": saldo,
                "soglia": critical_cash_threshold,
                "messaggio": f"Saldo previsto negativo ({saldo} EUR) il {line_date.isoformat()}",
            })
            seen_dates.add(line_date)
        elif saldo < min_cash_threshold:
            alerts.append({
                "tipo": "sotto_soglia_minima",
                "data_prevista": line_date,
                "saldo_previsto": saldo,
                "soglia": min_cash_threshold,
                "messaggio": f"Saldo previsto sotto soglia ({saldo} EUR < {min_cash_threshold} EUR) il {line_date.isoformat()}",
            })
            seen_dates.add(line_date)

    return alerts
