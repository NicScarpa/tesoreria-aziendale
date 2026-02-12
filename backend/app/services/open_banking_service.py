"""Open Banking service."""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.enums import (
    OpenBankingConnectionStatus, OpenBankingProvider,
    SyncFrequency, SyncLogStatus,
)
from app.models.open_banking_connection import OpenBankingConnection
from app.models.open_banking_sync_log import OpenBankingSyncLog
from app.models.bank_account import BankAccount
from app.models.transaction import Transaction
from app.models.enums import FlowDirection, TransactionStatus, TransactionType
from app.services.open_banking_adapter import OpenBankingAdapterFactory

logger = logging.getLogger(__name__)

SYNC_INTERVALS = {
    SyncFrequency.OGNI_ORA: timedelta(hours=1),
    SyncFrequency.OGNI_6_ORE: timedelta(hours=6),
    SyncFrequency.GIORNALIERO: timedelta(days=1),
    SyncFrequency.MANUALE: timedelta(days=365),
}


def list_institutions(db: Session, company_id: uuid.UUID, search: str = "", country: str = "IT") -> list[dict]:
    adapter = OpenBankingAdapterFactory.get("mock")
    institutions = adapter.get_institutions(country=country)
    if search:
        search_lower = search.lower()
        institutions = [i for i in institutions if search_lower in i["name"].lower()]
    return institutions


def initiate_connection(
    db: Session, company_id: uuid.UUID,
    institution_id: str, redirect_url: str,
) -> dict:
    adapter = OpenBankingAdapterFactory.get("mock")
    result = adapter.create_connection(institution_id, redirect_url)

    # Find institution name
    institutions = adapter.get_institutions()
    inst = next((i for i in institutions if i["id"] == institution_id), None)

    conn = OpenBankingConnection(
        company_id=company_id,
        provider=OpenBankingProvider.NORDIGEN_GOCARDLESS,
        provider_connection_id=result["connection_id"],
        institution_id=institution_id,
        institution_nome=inst["name"] if inst else institution_id,
        institution_logo_url=inst.get("logo") if inst else None,
        stato=OpenBankingConnectionStatus.IN_ATTESA_CONSENSO,
        consenso_id=result.get("consent_id"),
        consenso_creato_at=datetime.now(timezone.utc),
    )
    db.add(conn)
    db.flush()
    db.commit()

    return {
        "connection_id": str(conn.id),
        "authorization_url": result["authorization_url"],
    }


def handle_callback(
    db: Session, company_id: uuid.UUID, reference: str, code: str,
) -> OpenBankingConnection | None:
    conn = db.query(OpenBankingConnection).filter(
        OpenBankingConnection.company_id == company_id,
        OpenBankingConnection.provider_connection_id == reference,
    ).first()

    if not conn:
        return None

    adapter = OpenBankingAdapterFactory.get("mock")
    result = adapter.handle_callback(code, reference)

    conn.provider_account_id = result.get("account_id")
    conn.stato = OpenBankingConnectionStatus.ATTIVA
    conn.consenso_scadenza = datetime.now(timezone.utc) + timedelta(days=90)
    conn.prossimo_sync = datetime.now(timezone.utc)

    # Try to auto-link by IBAN
    iban = result.get("iban")
    if iban:
        account = db.query(BankAccount).filter(
            BankAccount.company_id == company_id,
            BankAccount.iban == iban,
        ).first()
        if account:
            conn.bank_account_id = account.id

    db.flush()
    db.commit()
    db.refresh(conn)
    return conn


def list_connections(db: Session, company_id: uuid.UUID) -> list[OpenBankingConnection]:
    return db.query(OpenBankingConnection).filter(
        OpenBankingConnection.company_id == company_id,
    ).order_by(OpenBankingConnection.created_at.desc()).all()


def get_connection(db: Session, connection_id: uuid.UUID, company_id: uuid.UUID) -> OpenBankingConnection | None:
    return db.query(OpenBankingConnection).filter(
        OpenBankingConnection.id == connection_id,
        OpenBankingConnection.company_id == company_id,
    ).first()


def delete_connection(db: Session, connection_id: uuid.UUID, company_id: uuid.UUID) -> bool:
    conn = get_connection(db, connection_id, company_id)
    if not conn:
        return False

    adapter = OpenBankingAdapterFactory.get("mock")
    adapter.revoke_connection(conn.provider_connection_id or "")

    conn.stato = OpenBankingConnectionStatus.REVOCATA
    conn.sync_attivo = False
    db.flush()
    db.commit()
    return True


def sync_connection(db: Session, connection_id: uuid.UUID, company_id: uuid.UUID) -> OpenBankingSyncLog:
    conn = get_connection(db, connection_id, company_id)
    if not conn:
        raise ValueError("Connessione non trovata")

    start = datetime.now(timezone.utc)
    adapter = OpenBankingAdapterFactory.get("mock")

    try:
        date_from = (conn.ultimo_sync or (datetime.now(timezone.utc) - timedelta(days=30))).date()
        if hasattr(date_from, 'date'):
            date_from = date_from
        date_to = datetime.now(timezone.utc).date()

        txs = adapter.get_transactions(conn.provider_account_id or "", date_from, date_to)

        new_count = 0
        dup_count = 0

        for tx_data in txs:
            # Dedup by reference
            ref = tx_data.get("reference", "")
            if ref and conn.bank_account_id:
                existing = db.query(Transaction).filter(
                    Transaction.bank_account_id == conn.bank_account_id,
                    Transaction.external_reference == ref,
                ).first()
                if existing:
                    dup_count += 1
                    continue

            if conn.bank_account_id:
                from decimal import Decimal
                amount = tx_data.get("amount", Decimal("0"))
                if tx_data.get("direction") == "outflow":
                    amount = -abs(amount)
                else:
                    amount = abs(amount)

                tx = Transaction(
                    company_id=company_id,
                    bank_account_id=conn.bank_account_id,
                    amount=amount,
                    currency=tx_data.get("currency", "EUR"),
                    direction=FlowDirection.INFLOW if tx_data.get("direction") == "inflow" else FlowDirection.OUTFLOW,
                    transaction_date=tx_data.get("date"),
                    description=tx_data.get("description", ""),
                    counterpart_name=tx_data.get("counterpart_name"),
                    external_reference=ref,
                    transaction_type=TransactionType.CREDIT_TRANSFER,
                    status=TransactionStatus.BOOKED,
                )
                db.add(tx)
                new_count += 1

        # Update balance
        balance_updated = False
        if conn.bank_account_id:
            balance = adapter.get_balance(conn.provider_account_id or "")
            account = db.get(BankAccount, conn.bank_account_id)
            if account and balance:
                account.current_balance = balance.get("current", account.current_balance)
                account.available_balance = balance.get("available", account.available_balance)
                account.balance_date = datetime.now(timezone.utc)
                balance_updated = True

        duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

        conn.ultimo_sync = datetime.now(timezone.utc)
        interval = SYNC_INTERVALS.get(conn.frequenza_sync, timedelta(days=1))
        conn.prossimo_sync = datetime.now(timezone.utc) + interval
        conn.errore_ultimo = None
        conn.errore_conteggio = 0

        log = OpenBankingSyncLog(
            connection_id=conn.id,
            stato=SyncLogStatus.SUCCESSO,
            movimenti_scaricati=len(txs),
            movimenti_nuovi=new_count,
            movimenti_duplicati=dup_count,
            saldo_aggiornato=balance_updated,
            periodo_da=datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc),
            periodo_a=datetime.combine(date_to, datetime.min.time()).replace(tzinfo=timezone.utc),
            durata_ms=duration,
            request_id=f"sync-{uuid.uuid4().hex[:8]}",
        )
        db.add(log)
        db.flush()
        db.commit()
        db.refresh(log)
        return log

    except Exception as e:
        duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        conn.errore_ultimo = str(e)
        conn.errore_conteggio += 1

        log = OpenBankingSyncLog(
            connection_id=conn.id,
            stato=SyncLogStatus.ERRORE,
            durata_ms=duration,
            errore_dettaglio=str(e),
            request_id=f"sync-err-{uuid.uuid4().hex[:8]}",
        )
        db.add(log)
        db.flush()
        db.commit()
        db.refresh(log)
        return log


def link_to_bank_account(
    db: Session, connection_id: uuid.UUID, bank_account_id: uuid.UUID, company_id: uuid.UUID
) -> OpenBankingConnection | None:
    conn = get_connection(db, connection_id, company_id)
    if not conn:
        return None
    conn.bank_account_id = bank_account_id
    db.flush()
    db.commit()
    db.refresh(conn)
    return conn


def renew_consent(db: Session, connection_id: uuid.UUID, company_id: uuid.UUID) -> dict | None:
    conn = get_connection(db, connection_id, company_id)
    if not conn:
        return None

    adapter = OpenBankingAdapterFactory.get("mock")
    result = adapter.create_connection(conn.institution_id or "", "")

    conn.consenso_id = result.get("consent_id")
    conn.consenso_creato_at = datetime.now(timezone.utc)
    conn.stato = OpenBankingConnectionStatus.IN_ATTESA_CONSENSO
    db.flush()
    db.commit()

    return {"authorization_url": result["authorization_url"]}


def get_sync_logs(
    db: Session, connection_id: uuid.UUID, company_id: uuid.UUID,
    page: int = 1, page_size: int = 20,
) -> tuple[list[OpenBankingSyncLog], int]:
    # Verify ownership
    conn = get_connection(db, connection_id, company_id)
    if not conn:
        return [], 0

    q = db.query(OpenBankingSyncLog).filter(
        OpenBankingSyncLog.connection_id == connection_id,
    ).order_by(OpenBankingSyncLog.data_sync.desc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total
