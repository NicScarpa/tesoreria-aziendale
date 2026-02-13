"""
Lightweight "cron" for Agenzia Entrate sync.

We run twice a day (07:00 and 13:00 Europe/Rome) and, for each company that has
the AdE integration enabled, we attempt to import the latest invoices (and
optionally corrispettivi).

Why a thread instead of a system cron:
- Works on Railway/containers without OS-level cron.
- Can still be triggered externally if needed in the future.

Safety:
- Uses a Postgres advisory lock to avoid duplicate runs when multiple web
  instances are running.
"""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import case, text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.company import Company
from app.models.enums import (
    IntegrationType,
    UserCompanyStatus,
    UserRole,
)
from app.models.integration_config import IntegrationConfig
from app.models.user_company import UserCompany
from app.services import ade_integration_service

logger = logging.getLogger(__name__)

try:
    _TZ = ZoneInfo("Europe/Rome")
except Exception:
    # Some slim containers may not ship tzdata. Fall back to UTC rather than crashing at import.
    _TZ = timezone.utc
_HOURS = (7, 13)

# 64-bit constant used for pg_try_advisory_lock. Must be stable across deploys.
_LOCK_KEY = 7_13_26_02_13  # arbitrary, but constant

_stop_event = threading.Event()
_thread: threading.Thread | None = None


@dataclass(frozen=True)
class AdeAutoSyncSettings:
    invoice_lookback_days: int = 7
    do_issued: bool = True
    do_received: bool = True
    do_corrispettivi: bool = False  # opt-in for now (requests are async/pending)


def _get_company_user_id(db: Session, company_id: uuid.UUID) -> uuid.UUID:
    """
    Best-effort user id for imports triggered by automation.

    `invoice_import_service` currently doesn't use the user_id, but we keep it
    stable and real to avoid future surprises.
    """
    role_rank = case(
        (UserCompany.role == UserRole.OWNER, 0),
        (UserCompany.role == UserRole.ADMIN, 1),
        (UserCompany.role == UserRole.EDITOR, 2),
        else_=3,
    )
    uc = (
        db.query(UserCompany)
        .filter(
            UserCompany.company_id == company_id,
            UserCompany.status == UserCompanyStatus.ACTIVE,
        )
        .order_by(role_rank.asc(), UserCompany.created_at.asc())
        .first()
    )
    if uc:
        return uc.user_id
    return uuid.UUID(int=0)


def _try_advisory_lock(db: Session) -> bool:
    try:
        return bool(db.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": _LOCK_KEY}).scalar())
    except Exception:
        # If DB doesn't support advisory locks (unlikely), just run.
        return True


def _advisory_unlock(db: Session) -> None:
    try:
        db.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _LOCK_KEY})
    except Exception:
        pass


def _next_run_time(now: datetime) -> datetime:
    assert now.tzinfo is not None
    candidates: list[datetime] = []
    for h in _HOURS:
        dt = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if dt <= now:
            dt = dt + timedelta(days=1)
        candidates.append(dt)
    return min(candidates)


def _load_settings(cfg: IntegrationConfig) -> AdeAutoSyncSettings:
    c = cfg.config or {}
    try:
        lookback = int(c.get("ade_auto_invoice_lookback_days") or 7)
    except Exception:
        lookback = 7
    lookback = max(1, min(30, lookback))

    def _bool(key: str, default: bool) -> bool:
        v = c.get(key)
        if v is None:
            return default
        return bool(v)

    return AdeAutoSyncSettings(
        invoice_lookback_days=lookback,
        do_issued=_bool("ade_auto_sync_issued", True),
        do_received=_bool("ade_auto_sync_received", True),
        do_corrispettivi=_bool("ade_auto_sync_corrispettivi", False),
    )


def run_ade_auto_sync_once(*, debug: bool = False) -> None:
    """
    Execute one full AdE autosync cycle for all enabled companies.

    Intended to be called by the scheduler thread (and can be called manually).
    """
    db = SessionLocal()
    locked = False
    try:
        locked = _try_advisory_lock(db)
        if not locked:
            logger.info("AdE autosync: another instance is running, skipping this run.")
            return

        cfgs = (
            db.query(IntegrationConfig)
            .filter(
                IntegrationConfig.integration_type == IntegrationType.AGENZIA_ENTRATE,
                IntegrationConfig.is_enabled.is_(True),
                IntegrationConfig.encrypted_credentials.isnot(None),
            )
            .order_by(IntegrationConfig.updated_at.desc())
            .all()
        )

        if not cfgs:
            logger.info("AdE autosync: no enabled integrations.")
            return

        today_it = datetime.now(_TZ).date()

        for cfg in cfgs:
            company = db.get(Company, cfg.company_id)
            if not company:
                continue

            s = _load_settings(cfg)
            user_id = _get_company_user_id(db, company.id)
            date_to = today_it
            date_from = today_it - timedelta(days=s.invoice_lookback_days - 1)

            logger.info(
                "AdE autosync: company=%s range=%s..%s issued=%s received=%s receipts=%s",
                str(company.id),
                date_from.isoformat(),
                date_to.isoformat(),
                s.do_issued,
                s.do_received,
                s.do_corrispettivi,
            )

            if s.do_issued:
                try:
                    ade_integration_service.sync_invoices(
                        db,
                        company,
                        user_id=user_id,
                        date_from=date_from,
                        date_to=date_to,
                        direction="issued",
                        debug=debug,
                    )
                except HTTPException as e:
                    logger.warning("AdE autosync (issued) failed for company %s: %s", str(company.id), getattr(e, "detail", str(e)))
                except Exception as e:
                    logger.exception("AdE autosync (issued) crashed for company %s: %s", str(company.id), e)

            if s.do_received:
                try:
                    ade_integration_service.sync_invoices(
                        db,
                        company,
                        user_id=user_id,
                        date_from=date_from,
                        date_to=date_to,
                        direction="received",
                        debug=debug,
                    )
                except HTTPException as e:
                    logger.warning("AdE autosync (received) failed for company %s: %s", str(company.id), getattr(e, "detail", str(e)))
                except Exception as e:
                    logger.exception("AdE autosync (received) crashed for company %s: %s", str(company.id), e)

            if s.do_corrispettivi:
                # First, try to download any previously submitted pending requests (can take days).
                try:
                    ade_integration_service.sync_corrispettivi_pending(
                        db,
                        company,
                        debug=debug,
                    )
                except HTTPException as e:
                    logger.warning(
                        "AdE autosync (corrispettivi pending) failed for company %s: %s",
                        str(company.id),
                        getattr(e, "detail", str(e)),
                    )
                except Exception as e:
                    logger.exception(
                        "AdE autosync (corrispettivi pending) crashed for company %s: %s",
                        str(company.id),
                        e,
                    )

                # Daily corrispettivi usually refer to yesterday's business date.
                yday = today_it - timedelta(days=1)
                try:
                    ade_integration_service.sync_corrispettivi(
                        db,
                        company,
                        date_from=yday,
                        date_to=yday,
                        debug=debug,
                    )
                except HTTPException as e:
                    logger.warning("AdE autosync (corrispettivi) failed for company %s: %s", str(company.id), getattr(e, "detail", str(e)))
                except Exception as e:
                    logger.exception("AdE autosync (corrispettivi) crashed for company %s: %s", str(company.id), e)

    finally:
        try:
            if locked:
                _advisory_unlock(db)
        finally:
            db.close()


def _scheduler_loop() -> None:
    while not _stop_event.is_set():
        try:
            now = datetime.now(_TZ)
            next_dt = _next_run_time(now)
            sleep_s = max(0.0, (next_dt - now).total_seconds())
            logger.info("AdE autosync scheduler: next run at %s (in %.0fs)", next_dt.isoformat(), sleep_s)
            if _stop_event.wait(timeout=sleep_s):
                break
            run_ade_auto_sync_once()
        except Exception as e:
            logger.exception("AdE autosync scheduler loop error: %s", e)
            # Avoid tight loop on repeated failures.
            _stop_event.wait(timeout=60)


def start_ade_auto_sync_scheduler() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_scheduler_loop, name="ade-auto-sync", daemon=True)
    _thread.start()


def stop_ade_auto_sync_scheduler() -> None:
    global _thread
    _stop_event.set()
    if _thread and _thread.is_alive():
        _thread.join(timeout=5)
    _thread = None
