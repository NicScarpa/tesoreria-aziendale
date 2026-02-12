"""Report Generator — produce dati strutturati per ogni tipo di report.

Ogni generatore ritorna un dict con:
- headers: list[dict] con name, label, align, format
- rows: list[dict]
- totals: dict (riga di totali)
- metadata: dict (titolo, periodo, note)
"""
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.bank_account import BankAccount
from app.models.bank_account_balance import BankAccountBalance
from app.models.enums import (
    AccountStatus, FlowDirection, ScheduleStatus, ScheduleType,
)
from app.models.transaction import Transaction
from app.models.category import Category


def generate_report_data(
    db: Session,
    company_id: uuid.UUID,
    tipo: str,
    parametri: dict | None = None,
) -> dict:
    """Dispatcher: chiama il generatore appropriato per il tipo."""
    params = parametri or {}
    generators = {
        "saldi_conti": _gen_saldi_conti,
        "movimenti": _gen_movimenti,
        "entrate_uscite": _gen_entrate_uscite,
        "riconciliazione": _gen_riconciliazione,
        "scadenzario": _gen_scadenzario,
        "aging": _gen_aging,
        "cash_flow": _gen_cash_flow,
        "pagamenti": _gen_pagamenti,
        "controparte": _gen_controparte,
        "personalizzato": _gen_personalizzato,
    }
    gen_fn = generators.get(tipo, _gen_personalizzato)
    return gen_fn(db, company_id, params)


def _parse_date_param(params: dict, key: str, default: date) -> date:
    val = params.get(key)
    if val:
        if isinstance(val, str):
            return date.fromisoformat(val)
        return val
    return default


def _fmt_importo(val: Decimal) -> str:
    """Formato italiano: 1.234,56"""
    s = f"{val:,.2f}"
    # swap . and ,
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


# --- Generatori ---

def _gen_saldi_conti(db: Session, company_id: uuid.UUID, params: dict) -> dict:
    includi_chiusi = params.get("includi_conti_chiusi", False)
    q = db.query(BankAccount).filter(BankAccount.company_id == company_id)
    if not includi_chiusi:
        q = q.filter(BankAccount.status == AccountStatus.ACTIVE)
    accounts = q.order_by(BankAccount.nickname.asc()).all()

    headers = [
        {"name": "conto", "label": "Conto", "align": "left"},
        {"name": "iban", "label": "IBAN", "align": "left"},
        {"name": "saldo_contabile", "label": "Saldo Contabile", "align": "right", "format": "currency"},
        {"name": "saldo_disponibile", "label": "Saldo Disponibile", "align": "right", "format": "currency"},
        {"name": "data_aggiornamento", "label": "Aggiornamento", "align": "center", "format": "date"},
    ]

    rows = []
    tot_contabile = Decimal("0")
    tot_disponibile = Decimal("0")
    for a in accounts:
        saldo_c = a.current_balance or Decimal("0")
        saldo_d = a.available_balance or Decimal("0")
        tot_contabile += saldo_c
        tot_disponibile += saldo_d
        rows.append({
            "conto": a.nickname or a.bank_name or "N/D",
            "iban": a.iban or "",
            "saldo_contabile": saldo_c,
            "saldo_disponibile": saldo_d,
            "data_aggiornamento": a.balance_date,
        })

    return {
        "headers": headers,
        "rows": rows,
        "totals": {"conto": "TOTALE", "saldo_contabile": tot_contabile, "saldo_disponibile": tot_disponibile},
        "metadata": {
            "titolo": "Situazione Saldi",
            "data_generazione": date.today().isoformat(),
            "numero_conti": len(rows),
        },
    }


def _gen_movimenti(db: Session, company_id: uuid.UUID, params: dict) -> dict:
    today = date.today()
    data_inizio = _parse_date_param(params, "data_inizio", today - timedelta(days=30))
    data_fine = _parse_date_param(params, "data_fine", today)
    conto_id = params.get("conto_id")

    q = (
        db.query(Transaction)
        .filter(
            Transaction.company_id == company_id,
            Transaction.transaction_date >= data_inizio,
            Transaction.transaction_date <= data_fine,
        )
    )
    if conto_id:
        q = q.filter(Transaction.bank_account_id == uuid.UUID(conto_id) if isinstance(conto_id, str) else conto_id)

    txs = q.order_by(Transaction.transaction_date.asc()).all()

    headers = [
        {"name": "data", "label": "Data", "align": "center", "format": "date"},
        {"name": "descrizione", "label": "Descrizione", "align": "left"},
        {"name": "controparte", "label": "Controparte", "align": "left"},
        {"name": "dare", "label": "Dare", "align": "right", "format": "currency"},
        {"name": "avere", "label": "Avere", "align": "right", "format": "currency"},
    ]

    rows = []
    tot_dare = Decimal("0")
    tot_avere = Decimal("0")
    for tx in txs:
        amt = abs(tx.amount)
        is_out = tx.direction == FlowDirection.OUTFLOW
        dare = amt if is_out else Decimal("0")
        avere = amt if not is_out else Decimal("0")
        tot_dare += dare
        tot_avere += avere
        rows.append({
            "data": tx.transaction_date,
            "descrizione": tx.description or "",
            "controparte": tx.counterpart_name or "",
            "dare": dare,
            "avere": avere,
        })

    return {
        "headers": headers,
        "rows": rows,
        "totals": {"descrizione": "TOTALE", "dare": tot_dare, "avere": tot_avere},
        "metadata": {
            "titolo": "Estratto Conto",
            "periodo": f"{data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}",
            "numero_movimenti": len(rows),
        },
    }


def _gen_entrate_uscite(db: Session, company_id: uuid.UUID, params: dict) -> dict:
    today = date.today()
    data_inizio = _parse_date_param(params, "data_inizio", today - timedelta(days=30))
    data_fine = _parse_date_param(params, "data_fine", today)

    txs = (
        db.query(Transaction)
        .filter(
            Transaction.company_id == company_id,
            Transaction.transaction_date >= data_inizio,
            Transaction.transaction_date <= data_fine,
        )
        .all()
    )

    # Load categories
    cats = {c.id: c.name for c in db.query(Category).filter(Category.company_id == company_id).all()}

    cat_data: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"entrate": Decimal("0"), "uscite": Decimal("0")})
    for tx in txs:
        cat_name = cats.get(tx.category_id, "Non categorizzato") if tx.category_id else "Non categorizzato"
        amt = abs(tx.amount)
        if tx.direction == FlowDirection.INFLOW:
            cat_data[cat_name]["entrate"] += amt
        else:
            cat_data[cat_name]["uscite"] += amt

    headers = [
        {"name": "categoria", "label": "Categoria", "align": "left"},
        {"name": "entrate", "label": "Entrate", "align": "right", "format": "currency"},
        {"name": "uscite", "label": "Uscite", "align": "right", "format": "currency"},
        {"name": "saldo_netto", "label": "Saldo Netto", "align": "right", "format": "currency"},
    ]

    rows = []
    tot_e = Decimal("0")
    tot_u = Decimal("0")
    for cat_name, vals in sorted(cat_data.items()):
        netto = vals["entrate"] - vals["uscite"]
        tot_e += vals["entrate"]
        tot_u += vals["uscite"]
        rows.append({
            "categoria": cat_name,
            "entrate": vals["entrate"],
            "uscite": vals["uscite"],
            "saldo_netto": netto,
        })

    return {
        "headers": headers,
        "rows": rows,
        "totals": {"categoria": "TOTALE", "entrate": tot_e, "uscite": tot_u, "saldo_netto": tot_e - tot_u},
        "metadata": {
            "titolo": "Entrate e Uscite per Categoria",
            "periodo": f"{data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}",
        },
    }


def _gen_riconciliazione(db: Session, company_id: uuid.UUID, params: dict) -> dict:
    today = date.today()
    data_inizio = _parse_date_param(params, "data_inizio", today - timedelta(days=30))
    data_fine = _parse_date_param(params, "data_fine", today)

    txs = (
        db.query(Transaction)
        .filter(
            Transaction.company_id == company_id,
            Transaction.transaction_date >= data_inizio,
            Transaction.transaction_date <= data_fine,
        )
        .all()
    )

    # Group by account
    from app.models.bank_account import BankAccount
    accounts = {a.id: a for a in db.query(BankAccount).filter(BankAccount.company_id == company_id).all()}

    acct_data: dict[uuid.UUID, dict] = defaultdict(lambda: {"totale": 0, "riconciliati": 0, "non_riconciliati": 0})
    for tx in txs:
        acct_data[tx.bank_account_id]["totale"] += 1
        if tx.verified:
            acct_data[tx.bank_account_id]["riconciliati"] += 1
        else:
            acct_data[tx.bank_account_id]["non_riconciliati"] += 1

    headers = [
        {"name": "conto", "label": "Conto", "align": "left"},
        {"name": "totale_movimenti", "label": "Totale Movimenti", "align": "right"},
        {"name": "riconciliati", "label": "Riconciliati", "align": "right"},
        {"name": "non_riconciliati", "label": "Non Riconciliati", "align": "right"},
        {"name": "percentuale", "label": "% Riconciliazione", "align": "right", "format": "percentage"},
    ]

    rows = []
    for acct_id, vals in acct_data.items():
        acct = accounts.get(acct_id)
        pct = (vals["riconciliati"] / vals["totale"] * 100) if vals["totale"] else 0
        rows.append({
            "conto": acct.nickname if acct else str(acct_id),
            "totale_movimenti": vals["totale"],
            "riconciliati": vals["riconciliati"],
            "non_riconciliati": vals["non_riconciliati"],
            "percentuale": round(pct, 1),
        })

    return {
        "headers": headers,
        "rows": rows,
        "totals": {},
        "metadata": {
            "titolo": "Stato Riconciliazione",
            "periodo": f"{data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}",
        },
    }


def _gen_scadenzario(db: Session, company_id: uuid.UUID, params: dict) -> dict:
    from app.models.schedule import Schedule

    tipo_scad = params.get("tipo_scadenzario", "attiva")
    includi_scadute = params.get("includi_scadute", True)

    q = db.query(Schedule).filter(Schedule.company_id == company_id)

    if tipo_scad == "attiva":
        q = q.filter(Schedule.tipo == ScheduleType.ATTIVA)
    elif tipo_scad == "passiva":
        q = q.filter(Schedule.tipo == ScheduleType.PASSIVA)

    if not includi_scadute:
        q = q.filter(Schedule.stato != ScheduleStatus.ANNULLATA)

    schedules = q.order_by(Schedule.data_scadenza.asc()).all()

    headers = [
        {"name": "controparte", "label": "Controparte", "align": "left"},
        {"name": "descrizione", "label": "Descrizione", "align": "left"},
        {"name": "scadenza", "label": "Scadenza", "align": "center", "format": "date"},
        {"name": "importo", "label": "Importo", "align": "right", "format": "currency"},
        {"name": "stato", "label": "Stato", "align": "center"},
    ]

    rows = []
    tot = Decimal("0")
    for s in schedules:
        tot += s.importo or Decimal("0")
        rows.append({
            "controparte": s.controparte_nome or "",
            "descrizione": s.descrizione or "",
            "scadenza": s.data_scadenza,
            "importo": s.importo or Decimal("0"),
            "stato": s.stato.value if s.stato else "",
        })

    titolo = "Scadenzario Attivo" if tipo_scad == "attiva" else "Scadenzario Passivo"
    return {
        "headers": headers,
        "rows": rows,
        "totals": {"controparte": "TOTALE", "importo": tot},
        "metadata": {"titolo": titolo, "numero_scadenze": len(rows)},
    }


def _gen_aging(db: Session, company_id: uuid.UUID, params: dict) -> dict:
    from app.models.schedule import Schedule

    fasce = params.get("fasce_giorni", [0, 30, 60, 90, 120])
    today = date.today()

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.company_id == company_id,
            Schedule.stato.in_([ScheduleStatus.APERTA, ScheduleStatus.SCADUTA, ScheduleStatus.PARZIALMENTE_PAGATA]),
        )
        .all()
    )

    # Group by counterpart and age bucket
    aging_data: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    labels = []
    for i in range(len(fasce)):
        if i == len(fasce) - 1:
            labels.append(f"Oltre {fasce[i]}gg")
        else:
            labels.append(f"{fasce[i]}-{fasce[i+1]}gg")

    for s in schedules:
        if not s.data_scadenza:
            continue
        days_overdue = (today - s.data_scadenza).days
        controparte = s.controparte_nome or "N/D"
        importo = s.importo or Decimal("0")

        # Find bucket
        bucket_idx = len(fasce) - 1
        for i in range(len(fasce) - 1):
            if days_overdue < fasce[i + 1]:
                bucket_idx = i
                break
        aging_data[controparte][labels[bucket_idx]] += importo

    headers = [{"name": "controparte", "label": "Controparte", "align": "left"}]
    for label in labels:
        headers.append({"name": label, "label": label, "align": "right", "format": "currency"})
    headers.append({"name": "totale", "label": "Totale", "align": "right", "format": "currency"})

    rows = []
    for controparte, buckets in sorted(aging_data.items()):
        row = {"controparte": controparte}
        tot = Decimal("0")
        for label in labels:
            val = buckets.get(label, Decimal("0"))
            row[label] = val
            tot += val
        row["totale"] = tot
        rows.append(row)

    return {
        "headers": headers,
        "rows": rows,
        "totals": {},
        "metadata": {"titolo": "Aging Crediti/Debiti", "fasce": fasce},
    }


def _gen_cash_flow(db: Session, company_id: uuid.UUID, params: dict) -> dict:
    from app.services import cash_flow_engine

    today = date.today()
    data_inizio = _parse_date_param(params, "data_inizio", today)
    data_fine = _parse_date_param(params, "data_fine", today + timedelta(days=90))

    projection = cash_flow_engine.generate_cash_flow_projection(
        db, company_id,
        data_inizio=data_inizio,
        data_fine=data_fine,
        includi_scadenze=params.get("includi_scadenze", True),
        includi_ricorrenze=params.get("includi_ricorrenze", True),
    )

    # Aggregate by month
    monthly: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"entrate": Decimal("0"), "uscite": Decimal("0"), "saldo": Decimal("0")}
    )
    for line in projection.get("lines", []):
        periodo = line["data"].strftime("%Y-%m")
        if line["tipo"] == "entrata":
            monthly[periodo]["entrate"] += line["importo"]
        else:
            monthly[periodo]["uscite"] += line["importo"]
        monthly[periodo]["saldo"] = line["saldo_progressivo"]

    headers = [
        {"name": "periodo", "label": "Periodo", "align": "center"},
        {"name": "entrate", "label": "Entrate", "align": "right", "format": "currency"},
        {"name": "uscite", "label": "Uscite", "align": "right", "format": "currency"},
        {"name": "saldo_netto", "label": "Saldo Netto", "align": "right", "format": "currency"},
        {"name": "saldo_progressivo", "label": "Saldo Progressivo", "align": "right", "format": "currency"},
    ]

    rows = []
    for periodo in sorted(monthly):
        vals = monthly[periodo]
        netto = vals["entrate"] - vals["uscite"]
        rows.append({
            "periodo": periodo,
            "entrate": vals["entrate"],
            "uscite": vals["uscite"],
            "saldo_netto": netto,
            "saldo_progressivo": vals["saldo"],
        })

    return {
        "headers": headers,
        "rows": rows,
        "totals": {
            "periodo": "TOTALE",
            "entrate": projection.get("totale_entrate", Decimal("0")),
            "uscite": projection.get("totale_uscite", Decimal("0")),
            "saldo_netto": projection.get("totale_entrate", Decimal("0")) - projection.get("totale_uscite", Decimal("0")),
        },
        "metadata": {
            "titolo": "Previsione Cash Flow",
            "periodo": f"{data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}",
            "saldo_iniziale": projection.get("saldo_iniziale", Decimal("0")),
            "saldo_finale": projection.get("saldo_finale", Decimal("0")),
        },
    }


def _gen_pagamenti(db: Session, company_id: uuid.UUID, params: dict) -> dict:
    from app.models.payment_order import PaymentOrder

    today = date.today()
    data_inizio = _parse_date_param(params, "data_inizio", today - timedelta(days=30))
    data_fine = _parse_date_param(params, "data_fine", today)

    q = (
        db.query(PaymentOrder)
        .filter(
            PaymentOrder.company_id == company_id,
            PaymentOrder.created_at >= data_inizio,
        )
    )
    orders = q.order_by(PaymentOrder.created_at.desc()).all()

    headers = [
        {"name": "data", "label": "Data", "align": "center", "format": "date"},
        {"name": "tipo", "label": "Tipo", "align": "center"},
        {"name": "beneficiario", "label": "Beneficiario", "align": "left"},
        {"name": "importo", "label": "Importo", "align": "right", "format": "currency"},
        {"name": "stato", "label": "Stato", "align": "center"},
    ]

    rows = []
    tot = Decimal("0")
    for o in orders:
        importo = o.importo_totale or Decimal("0")
        tot += importo
        rows.append({
            "data": o.created_at.date() if o.created_at else None,
            "tipo": o.tipo.value if o.tipo else "",
            "beneficiario": o.beneficiario_nome or "",
            "importo": importo,
            "stato": o.stato.value if o.stato else "",
        })

    return {
        "headers": headers,
        "rows": rows,
        "totals": {"beneficiario": "TOTALE", "importo": tot},
        "metadata": {
            "titolo": "Riepilogo Pagamenti",
            "periodo": f"{data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}",
            "numero_ordini": len(rows),
        },
    }


def _gen_controparte(db: Session, company_id: uuid.UUID, params: dict) -> dict:
    controparte_nome = params.get("controparte_nome", "")
    today = date.today()
    data_inizio = _parse_date_param(params, "data_inizio", today - timedelta(days=365))
    data_fine = _parse_date_param(params, "data_fine", today)

    q = (
        db.query(Transaction)
        .filter(
            Transaction.company_id == company_id,
            Transaction.transaction_date >= data_inizio,
            Transaction.transaction_date <= data_fine,
        )
    )
    if controparte_nome:
        q = q.filter(Transaction.counterpart_name.ilike(f"%{controparte_nome}%"))

    txs = q.order_by(Transaction.transaction_date.asc()).all()

    headers = [
        {"name": "data", "label": "Data", "align": "center", "format": "date"},
        {"name": "descrizione", "label": "Descrizione", "align": "left"},
        {"name": "dare", "label": "Dare", "align": "right", "format": "currency"},
        {"name": "avere", "label": "Avere", "align": "right", "format": "currency"},
    ]

    rows = []
    tot_dare = Decimal("0")
    tot_avere = Decimal("0")
    for tx in txs:
        amt = abs(tx.amount)
        is_out = tx.direction == FlowDirection.OUTFLOW
        dare = amt if is_out else Decimal("0")
        avere = amt if not is_out else Decimal("0")
        tot_dare += dare
        tot_avere += avere
        rows.append({
            "data": tx.transaction_date,
            "descrizione": tx.description or "",
            "dare": dare,
            "avere": avere,
        })

    return {
        "headers": headers,
        "rows": rows,
        "totals": {"descrizione": "TOTALE", "dare": tot_dare, "avere": tot_avere},
        "metadata": {
            "titolo": f"Scheda Controparte: {controparte_nome}",
            "periodo": f"{data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}",
            "saldo": tot_avere - tot_dare,
        },
    }


def _gen_personalizzato(db: Session, company_id: uuid.UUID, params: dict) -> dict:
    return {
        "headers": [{"name": "nota", "label": "Nota", "align": "left"}],
        "rows": [{"nota": "Report personalizzato — configurare i parametri"}],
        "totals": {},
        "metadata": {"titolo": "Report Personalizzato"},
    }
