"""Agenzia Entrate integration (best-effort Playwright automation)."""

from __future__ import annotations

import io
import json
import logging
import re
import uuid
import zipfile
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.encryption import decrypt_value
from app.models.ade_sync_log import AdeSyncLog
from app.models.company import Company
from app.models.enums import (
    IntegrationConnectionStatus,
    IntegrationType,
    InvoiceSource,
)
from app.models.integration_config import IntegrationConfig
from app.services.ade_portal.client import AdEPortalClient, AdePortalConfig, AdePortalError
from app.services import invoice_import_service, receipt_import_service

logger = logging.getLogger(__name__)

DEBUG_BASE = Path("uploads/ade_debug")


def _debug_dir(company_id: uuid.UUID) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return DEBUG_BASE / str(company_id) / ts


def _get_cfg(db: Session, company_id: uuid.UUID) -> IntegrationConfig:
    cfg = db.query(IntegrationConfig).filter(
        IntegrationConfig.company_id == company_id,
        IntegrationConfig.integration_type == IntegrationType.AGENZIA_ENTRATE,
    ).first()
    if not cfg:
        cfg = IntegrationConfig(
            company_id=company_id,
            integration_type=IntegrationType.AGENZIA_ENTRATE,
            status=IntegrationConnectionStatus.NON_CONFIGURATA,
            is_enabled=False,
        )
        db.add(cfg)
        db.flush()
    return cfg


def _load_credentials(cfg: IntegrationConfig) -> dict:
    if not cfg.encrypted_credentials:
        raise HTTPException(
            status_code=400,
            detail="Credenziali Agenzia Entrate non configurate. Vai in Integrazioni > Agenzia Entrate e salva CF, password e PIN.",
        )
    try:
        plaintext = decrypt_value(cfg.encrypted_credentials)
        creds = json.loads(plaintext)
    except ValueError as e:
        logger.error(f"Failed to decrypt AdE credentials (key mismatch): {e}")
        raise HTTPException(
            status_code=400,
            detail="Le credenziali salvate non sono più leggibili. Ri-salva CF, password e PIN dalla pagina Integrazioni > Agenzia Entrate.",
        )
    except Exception as e:
        logger.error(f"Failed to decrypt/parse AdE credentials: {e}")
        raise HTTPException(status_code=500, detail="Credenziali AdE non leggibili (cifratura/config)")

    cf = (creds or {}).get("cf") or (creds or {}).get("codice_fiscale")
    password = (creds or {}).get("password")
    pin = (creds or {}).get("pin")
    if not (cf and password and pin):
        raise HTTPException(status_code=400, detail="Credenziali AdE incomplete (cf/password/pin)")
    return {"cf": str(cf), "password": str(password), "pin": str(pin)}


def _portal_cfg(cfg: IntegrationConfig) -> AdePortalConfig:
    login_url = None
    try:
        login_url = (cfg.config or {}).get("ade_login_url")
    except Exception:
        login_url = None
    if login_url:
        return AdePortalConfig(login_url=str(login_url))
    env_url = settings.ADE_LOGIN_URL
    if env_url:
        return AdePortalConfig(login_url=str(env_url))
    return AdePortalConfig()


def _portal_working_user_cfg(cfg: IntegrationConfig) -> tuple[str, str | None, str]:
    """
    Optional working-user selection config for AdE:
      - `ade_working_mode`: auto | me_stesso | incaricato
      - `ade_incaricante`: string to match dropdown option (value or visible text)
      - `ade_corrispettivo_tipo`: RT | MC | DA | DC | RC
    """
    mode = "auto"
    incaricante = None
    tipo = "RT"
    try:
        c = cfg.config or {}
        mode = str(c.get("ade_working_mode") or "auto")
        incaricante = c.get("ade_incaricante")
        if incaricante is not None:
            incaricante = str(incaricante)
        tipo = str(c.get("ade_corrispettivo_tipo") or "RT").upper()
    except Exception:
        pass
    if tipo not in {"RT", "MC", "DA", "DC", "RC"}:
        tipo = "RT"
    return mode, incaricante, tipo


def test_connection(db: Session, company_id: uuid.UUID, *, debug: bool = False) -> dict:
    cfg = _get_cfg(db, company_id)
    creds = _load_credentials(cfg)
    portal_cfg = _portal_cfg(cfg)

    debug_dir = _debug_dir(company_id) if debug else None

    try:
        with AdEPortalClient(headless=True, debug_dir=debug_dir) as client:
            client.login_entratel_fisconline(cf=creds["cf"], password=creds["password"], pin=creds["pin"], cfg=portal_cfg)
        cfg.status = IntegrationConnectionStatus.CONNESSA
        cfg.last_test_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()
        return {"success": True, "message": "Connessione AdE riuscita"}
    except AdePortalError as e:
        cfg.status = IntegrationConnectionStatus.ERRORE
        cfg.last_test_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()
        return {"success": False, "message": str(e)}


def _format_date_it(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _click_first(page, role: str, patterns: list[str]) -> bool:
    import playwright.sync_api as pw  # type: ignore

    for p in patterns:
        try:
            loc = page.get_by_role(role, name=re.compile(p, re.I))
            if loc.count() > 0:
                loc.first.click()
                return True
        except pw.TimeoutError:
            continue
        except Exception:
            continue
    return False


def _fill_date_range(page, date_from: date, date_to: date) -> None:
    # Try common Italian labels first.
    from_str = _format_date_it(date_from)
    to_str = _format_date_it(date_to)

    filled_from = False
    filled_to = False

    for pat in ["Dal", "Da", "Data da", "Data inizio", "Periodo da"]:
        try:
            loc = page.get_by_label(re.compile(pat, re.I))
            if loc.count() > 0:
                loc.first.fill(from_str)
                filled_from = True
                break
        except Exception:
            pass
    for pat in ["Al", "A", "Data a", "Data fine", "Periodo a"]:
        try:
            loc = page.get_by_label(re.compile(pat, re.I))
            if loc.count() > 0:
                loc.first.fill(to_str)
                filled_to = True
                break
        except Exception:
            pass

    # Fallback: first two visible date/text inputs.
    if not (filled_from and filled_to):
        try:
            inputs = page.locator("input:visible").filter(has_not=page.locator("[disabled]"))
            # Prefer date inputs
            date_inputs = page.locator("input[type='date']:visible")
            if date_inputs.count() >= 2:
                date_inputs.nth(0).fill(from_str)
                date_inputs.nth(1).fill(to_str)
                return

            if inputs.count() >= 2:
                inputs.nth(0).fill(from_str)
                inputs.nth(1).fill(to_str)
                return
        except Exception:
            pass

    if not (filled_from and filled_to):
        raise AdePortalError("Impossibile impostare il range date (campi non trovati).")


def _download_first_export(page, *, timeout_ms: int = 60_000) -> tuple[str, bytes]:
    """
    Try to click an export/download button and capture the download.
    Returns (filename, bytes).
    """
    from playwright.sync_api import TimeoutError as PwTimeout  # type: ignore

    patterns = [
        "Scarica.*XML",
        "Download.*XML",
        "Esporta.*XML",
        "Scarica",
        "Download",
        "Esporta",
    ]

    # Candidate locators: buttons then links
    for role in ["button", "link"]:
        for p in patterns:
            try:
                loc = page.get_by_role(role, name=re.compile(p, re.I))
                if loc.count() == 0:
                    continue
                with page.expect_download(timeout=timeout_ms) as dl_info:
                    loc.first.click()
                dl = dl_info.value
                filename = dl.suggested_filename or "download"
                path = dl.path()
                if path:
                    data = Path(path).read_bytes()
                    return filename, data

                # Fallback: save to a temporary file and read it back.
                import tempfile
                import os

                fd, tmp_path = tempfile.mkstemp(prefix="ade-download-", suffix=Path(filename).suffix or ".bin")
                os.close(fd)
                try:
                    dl.save_as(tmp_path)
                    data = Path(tmp_path).read_bytes()
                    return filename, data
                finally:
                    try:
                        Path(tmp_path).unlink(missing_ok=True)
                    except Exception:
                        pass
            except PwTimeout:
                continue
            except Exception:
                continue

    raise AdePortalError("Download non riuscito: bottone/link export non trovato oppure non ha generato un file.")


def sync_invoices(
    db: Session,
    company: Company,
    *,
    user_id: uuid.UUID,
    date_from: date,
    date_to: date,
    direction: str,
    debug: bool = False,
) -> dict:
    cfg = _get_cfg(db, company.id)
    creds = _load_credentials(cfg)
    portal_cfg = _portal_cfg(cfg)
    working_mode, incaricante, _tipo_corr = _portal_working_user_cfg(cfg)

    debug_dir = _debug_dir(company.id) if debug else None

    log = AdeSyncLog(
        company_id=company.id,
        scope=f"invoices:{direction}",
        date_from=date_from,
        date_to=date_to,
        status="error",
    )
    db.add(log)
    db.flush()

    imported_new = 0
    updated = 0
    failed = 0

    try:
        with AdEPortalClient(headless=True, debug_dir=debug_dir) as client:
            client.login_entratel_fisconline(cf=creds["cf"], password=creds["password"], pin=creds["pin"], cfg=portal_cfg)
            if debug_dir:
                client.debug_save("01_after_login")
            client.goto_fatture_e_corrispettivi(
                working_mode=working_mode,
                incaricante=incaricante,
                company_vat=company.vat_number or None,
            )
            if debug_dir:
                client.debug_save("02_after_goto_service")

            # Best-effort navigation
            # Some portals require clicking "Consultazione" first.
            _click_first(client.page, "link", ["Consultazione"])
            _click_first(client.page, "button", ["Consultazione"])
            if debug_dir:
                client.debug_save("03_after_consultazione")

            if direction == "issued":
                ok = _click_first(client.page, "link", ["Fatture emesse", "Emesse", "Fatture vendita"])
                ok = ok or _click_first(client.page, "button", ["Fatture emesse", "Emesse", "Fatture vendita"])
            else:
                ok = _click_first(client.page, "link", ["Fatture ricevute", "Ricevute", "Fatture acquisto"])
                ok = ok or _click_first(client.page, "button", ["Fatture ricevute", "Ricevute", "Fatture acquisto"])

            if ok:
                try:
                    client.page.wait_for_load_state("networkidle")
                except Exception:
                    pass
            if debug_dir:
                client.debug_save("04_after_nav_invoice_section")

            _fill_date_range(client.page, date_from, date_to)
            if debug_dir:
                client.debug_save("05_after_fill_dates")

            # Search
            _click_first(client.page, "button", ["Ricerca", "Cerca", "Visualizza", "Applica"])
            try:
                client.page.wait_for_load_state("networkidle")
            except Exception:
                pass
            if debug_dir:
                client.debug_save("06_after_search")

            filename, data = _download_first_export(client.page, timeout_ms=90_000)

        # Process download: zip -> multiple, else single
        files: list[tuple[str, bytes]] = []
        if filename.lower().endswith(".zip") or data[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    name = Path(info.filename).name
                    if not name.lower().endswith((".xml", ".p7m")):
                        continue
                    files.append((name, zf.read(info)))
        else:
            files.append((filename, data))

        for name, content in files:
            try:
                _inv, created = invoice_import_service.import_single_with_source(
                    db,
                    company.id,
                    user_id,
                    content,
                    name,
                    fonte=InvoiceSource.CASSETTO_FISCALE,
                    batch_id=None,
                    company_piva=company.vat_number or "",
                )
                if created:
                    imported_new += 1
                else:
                    updated += 1
            except Exception as e:
                failed += 1
                logger.error(f"Invoice import failed ({name}): {e}")

        log.status = "success" if failed == 0 else "partial"
        log.imported_new = imported_new
        log.updated = updated
        log.failed = failed
        log.ended_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()

        return {
            "success": True,
            "scope": f"invoices:{direction}",
            "imported_new": imported_new,
            "updated": updated,
            "failed": failed,
            "message": f"Import fatture completato ({len(files)} file).",
        }
    except AdePortalError as e:
        log.status = "error"
        log.error_message = str(e)
        log.ended_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.status = "error"
        log.error_message = str(e)
        log.ended_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()
        raise HTTPException(status_code=500, detail=f"Errore sync fatture AdE: {e}")


def _save_receipt_raw(company_id: uuid.UUID, filename: str, content: bytes) -> str:
    base = Path("uploads/receipts")
    now = datetime.now(timezone.utc)
    dir_path = base / str(company_id) / str(now.year) / f"{now.month:02d}"
    dir_path.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)[:200] or "corrispettivo.bin"
    out = dir_path / f"{now.strftime('%Y%m%dT%H%M%S')}_{safe_name}"
    out.write_bytes(content)
    return str(out)


def _get_pending_corr_requests(cfg: IntegrationConfig) -> list[dict]:
    try:
        items = (cfg.config or {}).get("ade_pending_corrispettivi_requests")
        if isinstance(items, list):
            out: list[dict] = []
            for it in items:
                if isinstance(it, dict) and it.get("id"):
                    out.append(it)
            return out
    except Exception:
        pass
    return []


def _set_pending_corr_requests(cfg: IntegrationConfig, items: list[dict]) -> None:
    c = cfg.config or {}
    c["ade_pending_corrispettivi_requests"] = items
    cfg.config = c


def _open_mass_web_corrispettivi(client: AdEPortalClient, *, debug_dir: Path | None = None) -> str:
    """
    Enter the "Consultazioni e Download massivi" SPA and navigate to the corrispettivi request page.
    Returns the base URL (without hash) of the SPA, used to jump between routes.
    """
    page = client.page

    # Prefer the SPA link exposed on FEC home.
    try:
        link = page.locator("a.link_spa[href*='/cons/mass-web']").filter(has_text=re.compile(r"Consultazioni", re.I))
        if link.count() > 0:
            client._safe_click(link.first)  # noqa: SLF001 - internal helper to handle popups
    except Exception:
        pass

    # Fallback: direct navigation (works if session cookies are set).
    try:
        if "/cons/mass-web" not in (page.url or ""):
            page.goto("https://ivaservizi.agenziaentrate.gov.it/cons/mass-web/#/home", wait_until="domcontentloaded")
    except Exception:
        pass

    # Wait for the app shell.
    try:
        page.wait_for_function(
            """() => /Consultazioni\\s+e\\s+Download\\s+massivi/i.test(document.title || '')""",
            timeout=60_000,
        )
    except Exception:
        pass

    base = (page.url or "").split("#", 1)[0]
    if not base:
        base = "https://ivaservizi.agenziaentrate.gov.it/cons/mass-web/"

    # Jump directly to the corrispettivi request page.
    try:
        page.goto(f"{base}#/richieste/corrispettivi", wait_until="domcontentloaded")
    except Exception:
        page.goto(f"{base}#/richieste/corrispettivi", wait_until="load")

    # Wait for inputs.
    try:
        page.wait_for_selector("input#dal, input#al, #stato-select", timeout=60_000)
    except Exception:
        pass

    if debug_dir:
        client.debug_save("massweb_01_richieste_corrispettivi")

    return base


def _create_corrispettivi_mass_request(
    client: AdEPortalClient,
    *,
    base_url: str,
    date_from: date,
    date_to: date,
    tipo: str = "RT",
    debug_dir: Path | None = None,
) -> str:
    """
    Create and submit a "Richieste di Corrispettivi" mass request.
    Returns the `idRichiesta` (identificativo).
    """
    page = client.page

    # Ensure we're on the right route.
    try:
        if "#/richieste/corrispettivi" not in (page.url or ""):
            page.goto(f"{base_url}#/richieste/corrispettivi", wait_until="domcontentloaded")
    except Exception:
        pass

    # Fill dates and type.
    from_str = _format_date_it(date_from)
    to_str = _format_date_it(date_to)
    try:
        page.locator("input#dal").first.fill(from_str)
        page.locator("input#al").first.fill(to_str)
    except Exception:
        _fill_date_range(page, date_from, date_to)
    try:
        page.select_option("#stato-select", value=tipo)
    except Exception:
        pass

    if debug_dir:
        client.debug_save("massweb_02_after_fill_dates")

    # Generate request -> opens modal with XML.
    try:
        page.get_by_role("button", name=re.compile(r"Genera richiesta", re.I)).first.click()
    except Exception:
        try:
            page.locator("form[name='vm.inputCorrispettiviForm'] button[type='submit']").first.click()
        except Exception as e:
            raise AdePortalError(f"Impossibile generare richiesta corrispettivi: {e}") from e

    try:
        page.wait_for_selector("#modal-xml", state="visible", timeout=60_000)
    except Exception:
        page.wait_for_selector("#modal-xml", timeout=60_000)

    if debug_dir:
        client.debug_save("massweb_03_modal_generated")

    # Submit request.
    try:
        invia = page.locator("#modal-xml a").filter(has_text=re.compile(r"Invia richiesta", re.I))
        if invia.count() == 0:
            raise AdePortalError("Bottone 'Invia richiesta' non disponibile (richiesta già inviata?).")
        invia.first.click()
    except AdePortalError:
        raise
    except Exception as e:
        raise AdePortalError(f"Impossibile inviare richiesta corrispettivi: {e}") from e

    # Wait for success alert and extract identifier.
    try:
        page.wait_for_selector("#modal-xml p.alert-success", timeout=60_000)
    except Exception as e:
        raise AdePortalError(f"Invio richiesta non confermato (alert success non trovato): {e}") from e

    request_id = None
    try:
        txt = page.locator("#modal-xml").inner_text()
        m = re.search(r"(\d{10,})", txt or "")
        if m:
            request_id = m.group(1)
    except Exception:
        request_id = None

    if not request_id:
        try:
            strongs = page.locator("#modal-xml strong").all_inner_texts()
            for s in strongs:
                m = re.search(r"(\d{10,})", s or "")
                if m:
                    request_id = m.group(1)
                    break
        except Exception:
            pass

    if not request_id:
        if debug_dir:
            client.debug_save("massweb_04_after_invia_noid")
        raise AdePortalError("Impossibile estrarre identificativo richiesta corrispettivi dalla modale (UI cambiata).")

    if debug_dir:
        client.debug_save("massweb_04_after_invia")

    # Close modal so it doesn't block page interactions.
    try:
        close_btn = page.locator("#modal-xml button[data-dismiss='modal']").first
        close_btn.click()
        try:
            page.wait_for_selector("#modal-xml", state="hidden", timeout=15_000)
        except Exception:
            pass
    except Exception:
        pass

    return request_id


def _wait_spinner_gone(page, *, timeout_ms: int = 60_000) -> None:
    try:
        page.wait_for_function(
            """() => {
                const el = document.querySelector('#spinner');
                if (!el) return true;
                const style = window.getComputedStyle(el);
                return style.display === 'none' || style.visibility === 'hidden' || el.offsetParent === null;
            }""",
            timeout=timeout_ms,
        )
    except Exception:
        pass


def _download_corrispettivi_response_zip(
    client: AdEPortalClient,
    *,
    base_url: str,
    request_id: str,
    debug_dir: Path | None = None,
    timeout_ms: int = 60_000,
) -> tuple[str, bytes] | None:
    """
    Try to download the produced ZIP for a given request id from the "Risposte" list.
    Returns (filename, bytes) if available, else None.
    """
    from playwright.sync_api import TimeoutError as PwTimeout  # type: ignore

    page = client.page

    try:
        page.goto(f"{base_url}#/risposte/elenco", wait_until="domcontentloaded")
    except Exception:
        try:
            page.goto(f"{base_url}#/risposte/elenco", wait_until="load")
        except Exception:
            pass

    _wait_spinner_gone(page, timeout_ms=timeout_ms)
    try:
        page.wait_for_selector("#table-elenco", timeout=timeout_ms)
    except Exception:
        pass

    if debug_dir:
        client.debug_save("massweb_05_risposte_elenco")

    row = page.locator("#table-elenco tbody tr").filter(has_text=re.compile(re.escape(request_id)))
    if row.count() == 0:
        return None

    # Open detail modal.
    try:
        detail = row.first.locator("a.btn.btn-primary.btn-xs")
        if detail.count() == 0:
            return None
        detail.first.click()
    except Exception:
        return None

    try:
        page.wait_for_selector("#modal-risposta", state="visible", timeout=timeout_ms)
    except Exception:
        return None

    # Produced files download buttons are within the ordered list.
    btn = page.locator("#modal-risposta ol.text-list button[title*='prodotto']")
    if btn.count() == 0:
        # Not ready (or no produced file).
        try:
            page.locator("#modal-risposta button[data-dismiss='modal']").first.click()
        except Exception:
            pass
        return None

    try:
        with page.expect_download(timeout=timeout_ms) as dl_info:
            btn.first.click()
        dl = dl_info.value
        filename = dl.suggested_filename or "corrispettivi.zip"
        path = dl.path()
        if path:
            data = Path(path).read_bytes()
        else:
            import tempfile
            import os

            fd, tmp_path = tempfile.mkstemp(prefix="ade-massweb-", suffix=Path(filename).suffix or ".bin")
            os.close(fd)
            try:
                dl.save_as(tmp_path)
                data = Path(tmp_path).read_bytes()
            finally:
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except Exception:
                    pass
    except PwTimeout:
        return None
    except Exception:
        return None

    # Close modal.
    try:
        page.locator("#modal-risposta button[data-dismiss='modal']").first.click()
    except Exception:
        pass

    return filename, data


def _dec(text: str | None) -> Decimal | None:
    if text is None:
        return None
    t = str(text).strip()
    if not t:
        return None
    try:
        return Decimal(t)
    except Exception:
        try:
            return Decimal(t.replace(",", "."))
        except Exception:
            return None


def _parse_corrispettivi_xml(xml_bytes: bytes) -> dict:
    """
    Parse AdE corrispettivi XML (schema_risposta_CORR.xsd) into our internal receipt fields.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return {}

    ns = {"c": "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/corrispettivi/dati/v1.0"}

    def t(path: str) -> str | None:
        try:
            v = root.findtext(path, namespaces=ns)
            if v is None:
                return None
            v = str(v).strip()
            return v or None
        except Exception:
            return None

    piva = t("c:Trasmissione/c:PIVAEsercente")
    device_id = t("c:Trasmissione/c:Dispositivo/c:IdDispositivo")
    dt_raw = t("c:DataOraRilevazione") or t("c:Trasmissione/c:DataOraTrasmissione")
    time_rilevazione = None
    business_date = None
    if dt_raw:
        try:
            s = dt_raw.replace("Z", "+00:00")
            time_rilevazione = datetime.fromisoformat(s)
        except Exception:
            time_rilevazione = None
        if time_rilevazione:
            business_date = time_rilevazione.date()

    riepilogo = root.findall("c:DatiRT/c:Riepilogo", namespaces=ns)
    evid_net = 0
    evid_gross = 0
    lines: list[dict] = []

    for r in riepilogo:
        ammontare = _dec(r.findtext("c:Ammontare", namespaces=ns))
        importo_parziale = _dec(r.findtext("c:ImportoParziale", namespaces=ns))
        imposta = None
        iva_el = r.find("c:IVA", namespaces=ns)
        aliquota = None
        if iva_el is not None:
            aliquota = _dec(iva_el.findtext("c:AliquotaIVA", namespaces=ns))
            imposta = _dec(iva_el.findtext("c:Imposta", namespaces=ns))
            if imposta is None and aliquota is not None and ammontare is not None:
                try:
                    imposta = (ammontare * aliquota / Decimal(100)).quantize(Decimal("0.01"))
                except Exception:
                    imposta = None

        if ammontare is not None and importo_parziale is not None:
            if imposta is not None:
                try:
                    if abs(importo_parziale - (ammontare + imposta)) <= Decimal("0.02"):
                        evid_net += 1
                    if abs(importo_parziale - ammontare) <= Decimal("0.02"):
                        evid_gross += 1
                except Exception:
                    pass
            else:
                try:
                    if abs(importo_parziale - ammontare) <= Decimal("0.02"):
                        evid_gross += 1
                except Exception:
                    pass

        lines.append(
            {
                "ammontare": ammontare,
                "imposta": imposta,
                "importo_parziale": importo_parziale,
                "aliquota": aliquota,
            }
        )

    assume_net = True
    if evid_gross > evid_net:
        assume_net = False

    gross_total = Decimal(0)
    net_total = Decimal(0)
    vat_total = Decimal(0)
    any_amount = False

    for ln in lines:
        amt = ln.get("ammontare")
        imp = ln.get("imposta") or Decimal(0)
        parz = ln.get("importo_parziale")
        if amt is None and parz is None:
            continue

        any_amount = True
        if assume_net:
            imponibile = amt if amt is not None else (parz - imp if parz is not None else None)
            if imponibile is None:
                continue
            net_total += imponibile
            vat_total += imp
            gross_total += imponibile + imp
        else:
            gross = amt if amt is not None else parz
            if gross is None:
                continue
            gross_total += gross
            vat_total += imp
            net_total += gross - imp

    if not any_amount:
        return {
            "business_date": business_date,
            "external_id": None,
            "device_id": device_id,
            "time_rilevazione": time_rilevazione,
            "gross_total": None,
            "net_total": None,
            "vat_total": None,
            "metadata_extra": {"piva": piva, "xml_schema": "schema_risposta_CORR.xsd"},
        }

    return {
        "business_date": business_date,
        "external_id": None,
        "device_id": device_id,
        "time_rilevazione": time_rilevazione,
        "gross_total": gross_total,
        "net_total": net_total,
        "vat_total": vat_total,
        "metadata_extra": {
            "piva": piva,
            "xml_schema": "schema_risposta_CORR.xsd",
            "assume_ammontare_is_net": assume_net,
        },
    }


def sync_corrispettivi(
    db: Session,
    company: Company,
    *,
    date_from: date,
    date_to: date,
    debug: bool = False,
) -> dict:
    if date_to < date_from:
        raise HTTPException(status_code=400, detail="date_to deve essere >= date_from")
    # AdE mass-web enforces max 3 months range (see UI smart-date-limit-months=3).
    if (date_to - date_from).days > 93:
        raise HTTPException(status_code=400, detail="Il periodo richiesto non può superare il trimestre (max ~3 mesi).")

    cfg = _get_cfg(db, company.id)
    creds = _load_credentials(cfg)
    portal_cfg = _portal_cfg(cfg)
    working_mode, incaricante, tipo_corr = _portal_working_user_cfg(cfg)

    debug_dir = _debug_dir(company.id) if debug else None

    log = AdeSyncLog(
        company_id=company.id,
        scope="receipts",
        date_from=date_from,
        date_to=date_to,
        status="error",
    )
    db.add(log)
    db.flush()

    imported_new = 0
    updated = 0
    failed = 0
    pending = False
    external_request_id: str | None = None

    try:
        with AdEPortalClient(headless=True, debug_dir=debug_dir) as client:
            client.login_entratel_fisconline(cf=creds["cf"], password=creds["password"], pin=creds["pin"], cfg=portal_cfg)
            if debug_dir:
                client.debug_save("01_after_login")
            client.goto_fatture_e_corrispettivi(
                working_mode=working_mode,
                incaricante=incaricante,
                company_vat=company.vat_number or None,
            )
            if debug_dir:
                client.debug_save("02_after_goto_service")

            base = _open_mass_web_corrispettivi(client, debug_dir=debug_dir)

            pending_items = _get_pending_corr_requests(cfg)

            def _matches_range(it: dict) -> bool:
                return (
                    str(it.get("date_from") or "") == date_from.isoformat()
                    and str(it.get("date_to") or "") == date_to.isoformat()
                    and str(it.get("tipo") or "RT").upper() == tipo_corr
                )

            existing = next((it for it in pending_items if _matches_range(it)), None)
            if existing:
                external_request_id = str(existing.get("id"))
            else:
                external_request_id = _create_corrispettivi_mass_request(
                    client,
                    base_url=base,
                    date_from=date_from,
                    date_to=date_to,
                    tipo=tipo_corr,
                    debug_dir=debug_dir,
                )
                pending_items.append(
                    {
                        "id": external_request_id,
                        "date_from": date_from.isoformat(),
                        "date_to": date_to.isoformat(),
                        "tipo": tipo_corr,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                _set_pending_corr_requests(cfg, pending_items)
                db.flush()
                db.commit()

            filename_data = None
            for _attempt in range(1, 7):  # ~1 minute total
                filename_data = _download_corrispettivi_response_zip(
                    client,
                    base_url=base,
                    request_id=external_request_id,
                    debug_dir=debug_dir,
                    timeout_ms=60_000,
                )
                if filename_data:
                    break
                try:
                    client.page.wait_for_timeout(10_000)
                except Exception:
                    pass

            if not filename_data:
                pending = True
            else:
                filename, data = filename_data

        if pending:
            log.status = "pending"
            log.imported_new = 0
            log.updated = 0
            log.failed = 0
            log.ended_at = datetime.now(timezone.utc)
            db.flush()
            db.commit()
            return {
                "success": True,
                "scope": "receipts",
                "imported_new": 0,
                "updated": 0,
                "failed": 0,
                "pending": True,
                "external_request_id": external_request_id,
                "message": "Richiesta corrispettivi inviata ad AdE. La risposta non è ancora disponibile: riprova più tardi (può richiedere fino a 5 giorni).",
            }

        raw_files: list[tuple[str, bytes]] = []
        if filename.lower().endswith(".zip") or data[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    name = Path(info.filename).name
                    if not name.lower().endswith(".xml"):
                        continue
                    raw_files.append((name, zf.read(info)))
        else:
            # Unexpected format; still store as raw for debugging.
            raw_files.append((filename, data))

        for name, content in raw_files:
            try:
                parsed = _parse_corrispettivi_xml(content)
                biz = parsed.get("business_date")
                if not isinstance(biz, date):
                    biz = date_from if date_from == date_to else None
                if not isinstance(biz, date):
                    raise AdePortalError("Impossibile determinare la data del corrispettivo dal file XML.")

                raw_path = _save_receipt_raw(company.id, name, content)
                meta = (parsed.get("metadata_extra") or {}) if isinstance(parsed.get("metadata_extra"), dict) else {}
                meta = {**meta, "filename": name, "ade_request_id": external_request_id, "source_file": filename}
                _rec, created = receipt_import_service.upsert_receipt(
                    db,
                    company.id,
                    business_date=biz,
                    external_id=parsed.get("external_id"),
                    device_id=parsed.get("device_id"),
                    time_rilevazione=parsed.get("time_rilevazione"),
                    gross_total=parsed.get("gross_total"),
                    net_total=parsed.get("net_total"),
                    vat_total=parsed.get("vat_total"),
                    raw_attachment_path=raw_path,
                    metadata_extra=meta,
                )
                if created:
                    imported_new += 1
                else:
                    updated += 1
            except Exception as e:
                failed += 1
                logger.error(f"Receipt import failed ({name}): {e}")

        # Remove the request from pending list once we got a response (even if parsing had errors).
        try:
            pending_items = _get_pending_corr_requests(cfg)
            pending_items = [it for it in pending_items if str(it.get("id")) != str(external_request_id)]
            _set_pending_corr_requests(cfg, pending_items)
        except Exception:
            pass

        log.status = "success" if failed == 0 else "partial"
        log.imported_new = imported_new
        log.updated = updated
        log.failed = failed
        log.ended_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()

        return {
            "success": True,
            "scope": "receipts",
            "imported_new": imported_new,
            "updated": updated,
            "failed": failed,
            "pending": False,
            "external_request_id": external_request_id,
            "message": f"Import corrispettivi completato ({len(raw_files)} file).",
        }
    except AdePortalError as e:
        log.status = "error"
        log.error_message = str(e)
        log.ended_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.status = "error"
        log.error_message = str(e)
        log.ended_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()
        raise HTTPException(status_code=500, detail=f"Errore sync corrispettivi AdE: {e}")


def sync_corrispettivi_pending(
    db: Session,
    company: Company,
    *,
    max_requests: int = 20,
    debug: bool = False,
) -> dict:
    """
    Poll and download any pending AdE "mass-web" corrispettivi requests.

    This is needed because AdE processing can take hours/days; we store pending
    request ids in IntegrationConfig.config and must periodically check for
    responses.
    """
    cfg = _get_cfg(db, company.id)
    pending_items = _get_pending_corr_requests(cfg)
    if not pending_items:
        return {
            "success": True,
            "scope": "receipts",
            "imported_new": 0,
            "updated": 0,
            "failed": 0,
            "pending": False,
            "external_request_id": None,
            "message": "Nessuna richiesta corrispettivi in attesa.",
        }

    # Deduplicate by id (keep the newest entry).
    dedup: dict[str, dict] = {}
    for it in pending_items:
        try:
            rid = str(it.get("id") or "").strip()
        except Exception:
            rid = ""
        if not rid:
            continue
        dedup[rid] = it
    pending_items = list(dedup.values())

    creds = _load_credentials(cfg)
    portal_cfg = _portal_cfg(cfg)
    working_mode, incaricante, _tipo_corr = _portal_working_user_cfg(cfg)

    debug_dir = _debug_dir(company.id) if debug else None

    imported_new = 0
    updated = 0
    failed = 0
    completed_ids: list[str] = []
    still_pending: list[dict] = []
    now_utc = datetime.now(timezone.utc)

    try:
        with AdEPortalClient(headless=True, debug_dir=debug_dir) as client:
            client.login_entratel_fisconline(cf=creds["cf"], password=creds["password"], pin=creds["pin"], cfg=portal_cfg)
            if debug_dir:
                client.debug_save("01_after_login")
            client.goto_fatture_e_corrispettivi(
                working_mode=working_mode,
                incaricante=incaricante,
                company_vat=company.vat_number or None,
            )
            if debug_dir:
                client.debug_save("02_after_goto_service")

            base = _open_mass_web_corrispettivi(client, debug_dir=debug_dir)

            limit = max(1, int(max_requests))
            to_process = pending_items[:limit]
            rest_items = pending_items[limit:]

            for it in to_process:
                rid = str(it.get("id") or "").strip()
                if not rid:
                    continue

                # Drop very old requests to avoid infinite buildup (AdE says max 5 days).
                try:
                    created_raw = it.get("created_at")
                    created = datetime.fromisoformat(str(created_raw).replace("Z", "+00:00")) if created_raw else None
                except Exception:
                    created = None
                if created and (now_utc - created) > timedelta(days=14):
                    failed += 1
                    logger.warning("Dropping stale AdE pending corrispettivi request %s (created_at=%s)", rid, str(created_raw))
                    continue

                filename_data = _download_corrispettivi_response_zip(
                    client,
                    base_url=base,
                    request_id=rid,
                    debug_dir=debug_dir,
                    timeout_ms=60_000,
                )
                if not filename_data:
                    still_pending.append(it)
                    continue

                filename, data = filename_data
                completed_ids.append(rid)

                # Mirror sync_corrispettivi import logic.
                raw_files: list[tuple[str, bytes]] = []
                if filename.lower().endswith(".zip") or data[:2] == b"PK":
                    with zipfile.ZipFile(io.BytesIO(data)) as zf:
                        for info in zf.infolist():
                            if info.is_dir():
                                continue
                            name = Path(info.filename).name
                            if not name.lower().endswith(".xml"):
                                continue
                            raw_files.append((name, zf.read(info)))
                else:
                    raw_files.append((filename, data))

                # Best-effort range info for logging.
                try:
                    date_from = date.fromisoformat(str(it.get("date_from")))
                    date_to = date.fromisoformat(str(it.get("date_to")))
                except Exception:
                    date_from = now_utc.date()
                    date_to = now_utc.date()

                log = AdeSyncLog(
                    company_id=company.id,
                    scope="receipts",
                    date_from=date_from,
                    date_to=date_to,
                    status="error",
                )
                db.add(log)
                db.flush()

                req_imported_new = 0
                req_updated = 0
                req_failed = 0

                for name, content in raw_files:
                    try:
                        parsed = _parse_corrispettivi_xml(content)
                        biz = parsed.get("business_date")
                        if not isinstance(biz, date):
                            biz = date_from if date_from == date_to else None
                        if not isinstance(biz, date):
                            raise AdePortalError("Impossibile determinare la data del corrispettivo dal file XML.")

                        raw_path = _save_receipt_raw(company.id, name, content)
                        meta = (parsed.get("metadata_extra") or {}) if isinstance(parsed.get("metadata_extra"), dict) else {}
                        meta = {**meta, "filename": name, "ade_request_id": rid, "source_file": filename}
                        _rec, created = receipt_import_service.upsert_receipt(
                            db,
                            company.id,
                            business_date=biz,
                            external_id=parsed.get("external_id"),
                            device_id=parsed.get("device_id"),
                            time_rilevazione=parsed.get("time_rilevazione"),
                            gross_total=parsed.get("gross_total"),
                            net_total=parsed.get("net_total"),
                            vat_total=parsed.get("vat_total"),
                            raw_attachment_path=raw_path,
                            metadata_extra=meta,
                        )
                        if created:
                            req_imported_new += 1
                        else:
                            req_updated += 1
                    except Exception as e:
                        req_failed += 1
                        logger.error("Receipt import failed (%s, req %s): %s", name, rid, e)

                imported_new += req_imported_new
                updated += req_updated
                failed += req_failed

                log.status = "success" if req_failed == 0 else "partial"
                log.imported_new = req_imported_new
                log.updated = req_updated
                log.failed = req_failed
                log.ended_at = datetime.now(timezone.utc)
                db.flush()

        # Keep only requests that are still pending and not stale.
        completed_set = set(completed_ids)
        final_pending: list[dict] = []

        # Items we didn't process this run remain pending.
        final_pending.extend(rest_items)

        for it in still_pending:
            try:
                rid = str(it.get("id") or "").strip()
            except Exception:
                rid = ""
            if rid and rid not in completed_set:
                final_pending.append(it)

        _set_pending_corr_requests(cfg, final_pending)
        db.flush()
        db.commit()

        return {
            "success": True,
            "scope": "receipts",
            "imported_new": imported_new,
            "updated": updated,
            "failed": failed,
            "pending": bool(final_pending),
            "external_request_id": None,
            "message": f"Richieste pending processate: {len(completed_ids)} completate, {len(final_pending)} ancora in attesa.",
        }
    except AdePortalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore sync corrispettivi pending AdE: {e}")
