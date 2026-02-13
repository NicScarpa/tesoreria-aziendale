from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin


class AdePortalError(RuntimeError):
    pass


@dataclass(frozen=True)
class AdePortalConfig:
    # Best-effort default entrypoint; can be overridden by integration config.
    login_url: str = "https://ivaservizi.agenziaentrate.gov.it/portale/"


class AdEPortalClient:
    """
    Best-effort browser automation for AdE "Fatture e Corrispettivi".

    This code is intentionally defensive and stores debug artifacts (screenshots/html)
    when `debug_dir` is provided.
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        timeout_ms: int = 60_000,
        debug_dir: Path | None = None,
    ) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.debug_dir = debug_dir

        self._pw = None
        self._browser = None
        self._context = None
        self._page = None

    def __enter__(self) -> "AdEPortalClient":
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as e:  # pragma: no cover
            raise AdePortalError(
                "Playwright non installato nel backend. Installa con: pip install playwright && python -m playwright install chromium"
            ) from e

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(
            accept_downloads=True,
            locale="it-IT",
        )
        self._page = self._context.new_page()
        self._page.set_default_timeout(self.timeout_ms)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        finally:
            self._pw = None
            self._browser = None
            self._context = None
            self._page = None

    @property
    def page(self):
        if not self._page:
            raise AdePortalError("Browser non inizializzato")
        return self._page

    def _debug_save(self, name: str) -> None:
        if not self.debug_dir:
            return
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.page.screenshot(path=str(self.debug_dir / f"{name}.png"), full_page=True)
        except Exception:
            pass
        try:
            html = self.page.content()
            (self.debug_dir / f"{name}.html").write_text(html, encoding="utf-8")
        except Exception:
            pass

    def debug_save(self, name: str) -> None:
        """Public wrapper used by sync flows when `debug_dir` is enabled."""
        self._debug_save(name)

    def _click_first_by_role(self, role: str, patterns: Iterable[str], *, strict: bool = False) -> bool:
        for p in patterns:
            try:
                loc = self.page.get_by_role(role, name=re.compile(p, re.I))
                if loc.count() > 0:
                    self._safe_click(loc.first)
                    return True
            except Exception:
                continue
        if strict:
            raise AdePortalError(f"Elemento non trovato: role={role} patterns={list(patterns)}")
        return False

    def _safe_click(self, locator) -> None:
        """
        Click handling popups when a link opens a new tab/window.

        Some AdE service entries open in a new page; in that case we
        switch `self._page` to the popup.
        """
        try:
            from playwright.sync_api import TimeoutError as PwTimeout  # type: ignore
        except Exception:  # pragma: no cover
            locator.click()
            return

        # Ensure the element is interactable before attempting to click.
        try:
            locator.wait_for(state="visible", timeout=10_000)
        except Exception:
            pass

        # Avoid double-clicking: we click once and then (briefly) check if a popup appeared.
        before_pages = 0
        try:
            before_pages = len(getattr(self._context, "pages", []) or [])
        except Exception:
            before_pages = 0

        locator.click()

        # If a popup/tab was opened, adopt it as the active page.
        try:
            self.page.wait_for_timeout(750)
        except Exception:
            pass

        try:
            pages = getattr(self._context, "pages", []) or []
            if len(pages) > before_pages:
                new_page = pages[-1]
                self._page = new_page
                self._page.set_default_timeout(self.timeout_ms)
        except Exception:
            pass

    def _fill_by_label_or_placeholder(self, patterns: Iterable[str], value: str) -> bool:
        for p in patterns:
            try:
                loc = self.page.get_by_label(re.compile(p, re.I))
                if loc.count() > 0:
                    loc.first.fill(value)
                    return True
            except Exception:
                pass
            try:
                loc = self.page.get_by_placeholder(re.compile(p, re.I))
                if loc.count() > 0:
                    loc.first.fill(value)
                    return True
            except Exception:
                pass
        return False

    def _maybe_accept_cookies(self) -> None:
        # Best-effort cookie banner dismissal.
        try:
            self._click_first_by_role("button", ["Accetta", "Accetto", "Accept"], strict=False)
        except Exception:
            pass

    def _maybe_close_informativa(self) -> None:
        """
        Close the privacy/informativa overlay sometimes shown on Fatture e Corrispettivi home.

        The overlay can block interaction with the page underneath.
        """
        try:
            btn = self.page.locator("#chiudi_informativa:visible")
            if btn.count() > 0:
                self._safe_click(btn.first)
                try:
                    self.page.wait_for_timeout(500)
                except Exception:
                    pass
        except Exception:
            pass

    def _page_has_text(self, pattern: str) -> bool:
        try:
            loc = self.page.get_by_text(re.compile(pattern, re.I))
            return loc.count() > 0
        except Exception:
            try:
                html = (self.page.content() or "").lower()
                return re.search(pattern, html, re.I) is not None
            except Exception:
                return False

    def _is_fec_home(self) -> bool:
        try:
            url = (self.page.url or "").lower()
        except Exception:
            url = ""

        if "/portale/web/guest/home" in url:
            return True
        # Home exposes SPA links to other services (mass-web etc.).
        try:
            if self.page.locator("a.link_spa[href*='/cons/mass-web']").count() > 0:
                return True
        except Exception:
            pass
        return False

    def _ensure_utenza_di_lavoro(
        self,
        *,
        working_mode: str = "auto",
        incaricante: str | None = None,
        company_vat: str | None = None,
        timeout_ms: int = 120_000,
    ) -> None:
        """
        Complete the "Scelta utenza di lavoro" workflow when present.

        Variants observed:
        1) Step 1: choose "Me stesso" or "Incaricato" then click OK (#tipo_ut_button)
        2) If "Incaricato": step 2 dropdown (#ut2a) + OK (#tipo_incarico_submit)
        3) "Utenza di lavoro selezionata": accept checkbox (#chekc_prosegui) then click Prosegui link.

        `working_mode`:
          - "auto" (default): try Me stesso, fallback to Incaricato if unauthorized
          - "me_stesso"
          - "incaricato"
        """
        mode = (working_mode or "auto").strip().lower()
        if mode in {"mestesso", "me-stesso", "me stesso", "me"}:
            mode = "me_stesso"
        if mode not in {"auto", "me_stesso", "incaricato"}:
            mode = "auto"

        try:
            from playwright.sync_api import TimeoutError as PwTimeout  # type: ignore
        except Exception:  # pragma: no cover
            PwTimeout = Exception  # type: ignore

        deadline_ms = timeout_ms
        me_stesso_tried = False

        def _wait_short() -> None:
            try:
                self.page.wait_for_load_state("domcontentloaded")
            except Exception:
                pass
            try:
                self.page.wait_for_load_state("networkidle")
            except Exception:
                pass
            self._maybe_accept_cookies()

        def _goto_scelt_utenza() -> None:
            # Prefer clicking "Cambia utenza di lavoro" if present.
            try:
                link = self.page.get_by_role("link", name=re.compile(r"Cambia utenza di lavoro", re.I))
                if link.count() > 0:
                    self._safe_click(link.first)
                    _wait_short()
                    return
            except Exception:
                pass
            try:
                self.page.goto("https://ivaservizi.agenziaentrate.gov.it/portale/scelta-utenza-lavoro", wait_until="domcontentloaded")
            except Exception:
                pass
            _wait_short()

        # Iterate state machine until we can see the app home or menu.
        start = None
        try:
            start = self.page.evaluate("() => Date.now()")
        except Exception:
            start = None

        while True:
            self._maybe_accept_cookies()
            self._maybe_close_informativa()

            # Success conditions: either FEC home (preferred) OR at least we can see "Consultazione".
            if self._is_fec_home():
                self._maybe_close_informativa()
                return
            try:
                if self.page.get_by_role("link", name=re.compile(r"Consultazione", re.I)).count() > 0:
                    return
            except Exception:
                pass

            # Timeout check (best-effort).
            if start is not None:
                try:
                    now = self.page.evaluate("() => Date.now()")
                    if isinstance(now, (int, float)) and now - start > deadline_ms:
                        break
                except Exception:
                    pass

            # Step 3: accept page
            try:
                if self.page.locator("#chekc_prosegui").count() > 0:
                    self._debug_save("utenza_accept_before")
                    try:
                        # Old jQuery checks attr('checked') instead of property.
                        self.page.evaluate(
                            """() => {
                                const cb = document.querySelector('#chekc_prosegui');
                                if (!cb) return false;
                                cb.setAttribute('checked', 'checked');
                                cb.checked = true;
                                cb.dispatchEvent(new Event('change', { bubbles: true }));
                                return true;
                            }"""
                        )
                    except Exception:
                        try:
                            self.page.locator("#chekc_prosegui").first.click()
                        except Exception:
                            pass
                    try:
                        self.page.wait_for_selector("#prosegui:visible a", timeout=10_000)
                    except Exception:
                        pass
                    try:
                        link = self.page.locator("#prosegui a")
                        if link.count() > 0:
                            self._safe_click(link.first)
                            _wait_short()
                            self._maybe_close_informativa()
                            self._debug_save("utenza_accept_after_prosegui")
                            continue
                    except Exception:
                        pass
            except Exception:
                pass

            # Step 2: incaricato - choose subject in dropdown.
            try:
                if self.page.locator("#ut2a").count() > 0 and self.page.locator("#tipo_incarico_submit").count() > 0:
                    self._debug_save("utenza_incaricato_step2_before")
                    options: list[dict] = []
                    try:
                        options = self.page.evaluate(
                            """() => Array.from(document.querySelectorAll('#ut2a option')).map(o => ({
                                value: (o.getAttribute('value') || ''),
                                text: (o.textContent || '').trim()
                            }))"""
                        ) or []
                    except Exception:
                        options = []

                    def _norm(s: str) -> str:
                        return re.sub(r"\s+", "", (s or "")).lower()

                    want = _norm(incaricante or "")
                    vat = _norm(company_vat or "")

                    chosen = None
                    for opt in options:
                        val = str(opt.get("value") or "")
                        txt = str(opt.get("text") or "")
                        if not val:
                            continue
                        if want and (want in _norm(val) or want in _norm(txt)):
                            chosen = val
                            break
                    if not chosen and vat:
                        for opt in options:
                            val = str(opt.get("value") or "")
                            txt = str(opt.get("text") or "")
                            if not val:
                                continue
                            if vat in _norm(val) or vat in _norm(txt):
                                chosen = val
                                break
                    if not chosen:
                        for opt in options:
                            val = str(opt.get("value") or "")
                            if val:
                                chosen = val
                                break
                    if not chosen:
                        raise AdePortalError("Nessun incaricante disponibile in 'Scelta utenza di lavoro'.")

                    try:
                        self.page.select_option("#ut2a", value=chosen)
                    except Exception:
                        # Fallback: set value via JS
                        try:
                            self.page.evaluate(
                                """(v) => {
                                    const sel = document.querySelector('#ut2a');
                                    if (!sel) return false;
                                    sel.value = v;
                                    sel.dispatchEvent(new Event('change', { bubbles: true }));
                                    return true;
                                }""",
                                chosen,
                            )
                        except Exception:
                            pass

                    self._debug_save("utenza_incaricato_step2_selected")
                    try:
                        self._safe_click(self.page.locator("#tipo_incarico_submit").first)
                    except Exception:
                        raise AdePortalError("Impossibile confermare 'Scelta per chi operare' (OK).")
                    _wait_short()
                    self._debug_save("utenza_incaricato_step2_after_ok")
                    continue
            except AdePortalError:
                raise
            except Exception:
                pass

            # Step 1: selection page
            try:
                if self.page.locator("#tipo_ut_button").count() > 0:
                    self._debug_save("utenza_step1_before")

                    def _click_radio(sel: str) -> None:
                        try:
                            r = self.page.locator(sel)
                            if r.count() > 0:
                                self._safe_click(r.first)
                                return
                        except Exception:
                            pass
                        try:
                            self.page.evaluate(
                                """(id) => {
                                    const el = document.querySelector(id);
                                    if (!el) return false;
                                    el.checked = true;
                                    el.dispatchEvent(new Event('change', { bubbles: true }));
                                    return true;
                                }""",
                                sel,
                            )
                        except Exception:
                            pass

                    desired = mode
                    if desired == "auto":
                        desired = "me_stesso" if not me_stesso_tried else "incaricato"

                    if desired == "me_stesso":
                        me_stesso_tried = True
                        _click_radio("#ut1a1")
                    else:
                        _click_radio("#ut1a2")

                    try:
                        self._safe_click(self.page.locator("#tipo_ut_button").first)
                    except Exception:
                        raise AdePortalError("Impossibile confermare 'Utenza di lavoro' (OK).")

                    _wait_short()
                    self._debug_save("utenza_step1_after_ok")

                    # If we tried "Me stesso" and it's unauthorized, fallback to incaricato (auto) or error.
                    if desired == "me_stesso" and self._page_has_text(r"senza\s+autorizzazioni"):
                        self._debug_save("utenza_step1_unauthorized_mestesso")
                        if mode == "me_stesso":
                            raise AdePortalError("Utenza di lavoro 'Me stesso' senza autorizzazioni su Fatture e Corrispettivi.")
                        # Auto fallback: go back to selection and try incaricato.
                        _goto_scelt_utenza()
                        continue

                    continue
            except AdePortalError:
                raise
            except Exception:
                pass

            # If we get here, we didn't match any known step and we're not ready.
            # Try to reach the selection page explicitly if we see the unauthorized box.
            if self._page_has_text(r"Utenza\s+di\s+lavoro\s+senza\s+autorizzazioni"):
                _goto_scelt_utenza()
                continue

            break

        self._debug_save("utenza_flow_failed")
        raise AdePortalError(
            "Impossibile completare la scelta dell'utenza di lavoro (Me stesso/Incaricato) per entrare in Fatture e Corrispettivi."
        )

    def _maybe_select_utenza_di_lavoro(self, *, timeout_ms: int = 5_000) -> bool:
        """
        After SSO, AdE may show a "Scelta utenza lavoro" step before entering the app.

        The page typically contains an "OK" button with id `tipo_ut_button` that submits
        the selected radio option ("Me stesso" by default).
        """
        self._maybe_accept_cookies()
        ok_btn = None
        try:
            # Detect the selection step quickly without hanging other flows.
            self.page.wait_for_selector("#tipo_ut_button", timeout=timeout_ms)
            ok_btn = self.page.locator("#tipo_ut_button:visible")
        except Exception:
            ok_btn = None

        if not ok_btn:
            # Fallback: some variants expose it as a semantic button with name "OK".
            try:
                ok_btn = self.page.get_by_role("button", name=re.compile(r"^OK$", re.I))
            except Exception:
                ok_btn = None

        try:
            if not ok_btn or ok_btn.count() == 0:
                return False
        except Exception:
            return False

        try:
            self._safe_click(ok_btn.first)
        except Exception:
            return False

        # Wait for navigation away from the selection step.
        try:
            self.page.wait_for_selector("#tipo_ut_button", state="detached", timeout=30_000)
        except Exception:
            pass
        try:
            self.page.wait_for_load_state("domcontentloaded")
        except Exception:
            pass
        try:
            self.page.wait_for_load_state("networkidle")
        except Exception:
            pass
        self._maybe_accept_cookies()
        # Best-effort: the app home should expose "Consultazione" in its menu.
        try:
            self.page.get_by_role("link", name=re.compile(r"Consultazione", re.I)).first.wait_for(timeout=30_000)
        except Exception:
            pass
        return True

    def login_entratel_fisconline(self, *, cf: str, password: str, pin: str, cfg: AdePortalConfig) -> None:
        """
        Perform login via Entratel/Fisconline.

        This is best-effort because the portal can change and may show CAPTCHAs.
        """
        try:
            self.page.goto(cfg.login_url, wait_until="networkidle")
        except Exception as e:
            self._debug_save("login_goto_failed")
            raise AdePortalError(f"Impossibile aprire la pagina di login: {e}") from e

        self._maybe_accept_cookies()

        # If there's a tab/button/link to choose Entratel/Fisconline, try to click it.
        self._click_first_by_role("tab", ["Entratel", "Fisconline"], strict=False)
        self._click_first_by_role("button", ["Entratel", "Fisconline"], strict=False)
        self._click_first_by_role("link", ["Entratel", "Fisconline"], strict=False)

        ok_cf = self._fill_by_label_or_placeholder(["Codice fiscale", "Codice Fiscale", "CF", "Username", "User"], cf)
        ok_pwd = self._fill_by_label_or_placeholder(["Password", "Pwd"], password)
        ok_pin = self._fill_by_label_or_placeholder(["PIN", "Pin", "Codice PIN", "Codice personale"], pin)

        if not ok_cf:
            self._debug_save("login_cf_not_found")
            raise AdePortalError("Campo Codice Fiscale non trovato (portale cambiato o selettori non compatibili).")

        # Password/PIN: if label-based search fails, fallback to password inputs.
        if not (ok_pwd and ok_pin):
            try:
                pw_inputs = self.page.locator("input[type='password']:visible")
                if pw_inputs.count() >= 2:
                    pw_inputs.nth(0).fill(password)
                    pw_inputs.nth(1).fill(pin)
                    ok_pwd = ok_pin = True
            except Exception:
                pass

        if not ok_pwd:
            self._debug_save("login_password_not_found")
            raise AdePortalError("Campo Password non trovato (portale cambiato).")
        if not ok_pin:
            self._debug_save("login_pin_not_found")
            raise AdePortalError("Campo PIN non trovato (portale cambiato).")

        # Submit
        clicked = self._click_first_by_role("button", ["Entra", "Accedi", "Login", "Continua"], strict=False)
        if not clicked:
            # Fallback: submit by pressing Enter in last field.
            try:
                self.page.keyboard.press("Enter")
                clicked = True
            except Exception:
                clicked = False

        if not clicked:
            self._debug_save("login_submit_not_found")
            raise AdePortalError("Bottone di accesso non trovato.")

        try:
            self.page.wait_for_load_state("networkidle")
        except Exception:
            # Some apps never go fully idle; ignore.
            pass

        # Detect common blocks/errors
        content = ""
        try:
            content = self.page.content().lower()
        except Exception:
            pass

        if "captcha" in content or "recaptcha" in content:
            self._debug_save("login_captcha")
            raise AdePortalError("Login bloccato da CAPTCHA. Serve gestire manualmente o cambiare approccio.")

        if "credenzial" in content and ("errat" in content or "non valid" in content):
            self._debug_save("login_invalid_credentials")
            raise AdePortalError("Credenziali non valide (password/PIN).")

        # Best-effort: if we're still on login url, assume failure.
        try:
            if self.page.url and cfg.login_url.rstrip("/") in self.page.url.rstrip("/"):
                # Might still be ok if app is SPA; keep weak check.
                pass
        except Exception:
            pass

    def goto_fatture_e_corrispettivi(
        self,
        *,
        working_mode: str = "auto",
        incaricante: str | None = None,
        company_vat: str | None = None,
    ) -> None:
        """
        Navigate to the "Fatture e Corrispettivi" application.

        With Entratel/Fisconline login, after authentication users typically land on the
        "Area riservata" home (PortaleWeb). From there, the correct path is:
        - click service tile "Fatturazione elettronica" (accessoFatturazione)
        - then enter "Fatture e Corrispettivi" portal (for titolari P.IVA)

        This navigation is best-effort and intentionally defensive.
        """
        self._maybe_accept_cookies()

        # If we're already on ivaservizi, no-op (still keep trying to reach the app).
        try:
            current_url = self.page.url or ""
        except Exception:
            current_url = ""

        # Step 1: from Area Riservata, open "Fatturazione elettronica" service
        # (href usually contains "accessoFatturazione"). The tile may be in a carousel and not
        # visible; when present in DOM we navigate using its href to avoid flaky visibility checks.
        try:
            href = None
            loc = self.page.locator("a[href*='accessoFatturazione']")
            if loc.count() > 0:
                try:
                    href = loc.first.get_attribute("href")
                except Exception:
                    href = None

            if href:
                target = href if href.lower().startswith("http") else urljoin(current_url or self.page.url or "", href)
            else:
                # Last resort: known relative path on Area Riservata.
                target = urljoin(current_url or self.page.url or "", "/PortaleWeb/servizi/accessoFatturazione")

            # Don't wait for networkidle: portals can keep connections open.
            self.page.goto(target, wait_until="domcontentloaded")
            self._maybe_accept_cookies()
            # SPA: wait for either the service cards OR the "utenza di lavoro" selection step.
            try:
                self.page.wait_for_selector("[data-testid='card-container'], #tipo_ut_button", timeout=30_000)
            except Exception:
                pass
            self._debug_save("goto_01_after_accesso_fatturazione")

            # Some flows redirect directly into the "Fatture e Corrispettivi" portal (selection step).
            try:
                # Avoid calling the state machine on unrelated pages: probe for known selectors first.
                probe = self.page.locator("#tipo_ut_button, #ut2a, #chekc_prosegui, a.link_spa[href*='/cons/mass-web']")
                if probe.count() > 0:
                    self._ensure_utenza_di_lavoro(
                        working_mode=working_mode,
                        incaricante=incaricante,
                        company_vat=company_vat,
                        timeout_ms=90_000,
                    )
                    self._debug_save("goto_02_after_utenza_flow")
                    return
            except AdePortalError:
                # If we're not in the selection flow yet, continue with normal navigation.
                pass
        except Exception:
            # If navigation fails, try a best-effort click by text.
            self._click_first_by_role("link", ["Fatturazione elettronica", "Vai al servizio"], strict=False)
            try:
                self.page.wait_for_load_state("domcontentloaded")
            except Exception:
                pass
            self._maybe_accept_cookies()
            try:
                self.page.wait_for_selector("[data-testid='card-container'], #tipo_ut_button", timeout=30_000)
            except Exception:
                pass
            self._debug_save("goto_01b_after_click_service")
            try:
                probe = self.page.locator("#tipo_ut_button, #ut2a, #chekc_prosegui, a.link_spa[href*='/cons/mass-web']")
                if probe.count() > 0:
                    self._ensure_utenza_di_lavoro(
                        working_mode=working_mode,
                        incaricante=incaricante,
                        company_vat=company_vat,
                        timeout_ms=90_000,
                    )
                    self._debug_save("goto_02b_after_utenza_flow")
                    return
            except AdePortalError:
                pass

        # Step 2: enter "Fatture e corrispettivi" card and click its "Accedi" button.
        # On the "Fatturazione elettronica" page there are multiple "Accedi" buttons;
        # we MUST scope the click to the right card.
        try:
            title = self.page.get_by_test_id("card-title").filter(
                has_text=re.compile(r"Fatture\s+e\s+corrispettivi", re.I)
            )
            card = self.page.get_by_test_id("card-container").filter(has=title)
            if card.count() > 0:
                btn = card.first.get_by_role("button", name=re.compile(r"Accedi", re.I))
                if btn.count() > 0:
                    self._safe_click(btn.first)
                    # Give the new app a chance to load (some opens a popup).
                    try:
                        self.page.wait_for_load_state("domcontentloaded")
                    except Exception:
                        pass
                    try:
                        self.page.wait_for_load_state("networkidle")
                    except Exception:
                        pass
                    self._maybe_accept_cookies()
                    self._debug_save("goto_03_after_click_card_accedi")

                    # Wait until either the working-profile selection step OR the app menu appears.
                    try:
                        self.page.wait_for_selector(
                            "#tipo_ut_button, a:has-text('Consultazione'), button:has-text('Consultazione')",
                            timeout=30_000,
                        )
                    except Exception:
                        pass

                    # If we land on the working-profile selection step (or any intermediate step), handle it now.
                    try:
                        self._ensure_utenza_di_lavoro(
                            working_mode=working_mode,
                            incaricante=incaricante,
                            company_vat=company_vat,
                            timeout_ms=120_000,
                        )
                        self._debug_save("goto_04_after_utenza_flow")
                        return
                    except AdePortalError:
                        pass
                    try:
                        self.page.get_by_role("link", name=re.compile(r"Consultazione", re.I)).first.wait_for(timeout=10_000)
                        self._debug_save("goto_04_after_consultazione_visible")
                        return
                    except Exception:
                        pass
        except Exception:
            pass

        # Fallback: click the last visible "Accedi" button (usually the "Fatture e corrispettivi" one)
        # Only do this if we are on the Fatturazione elettronica page.
        try:
            if "Fatturazione elettronica" in (self.page.content() or ""):
                accedi = self.page.get_by_role("button", name=re.compile(r"Accedi", re.I))
                if accedi.count() >= 2:
                    self._safe_click(accedi.nth(accedi.count() - 1))
                    try:
                        self.page.wait_for_load_state("domcontentloaded")
                    except Exception:
                        pass
                    try:
                        self.page.wait_for_load_state("networkidle")
                    except Exception:
                        pass
                    self._maybe_accept_cookies()
                    self._debug_save("goto_03b_after_fallback_click_accedi")

                    try:
                        self.page.wait_for_selector(
                            "#tipo_ut_button, a:has-text('Consultazione'), button:has-text('Consultazione')",
                            timeout=30_000,
                        )
                    except Exception:
                        pass

                    try:
                        self._ensure_utenza_di_lavoro(
                            working_mode=working_mode,
                            incaricante=incaricante,
                            company_vat=company_vat,
                            timeout_ms=120_000,
                        )
                        self._debug_save("goto_04b_after_utenza_flow")
                        return
                    except AdePortalError:
                        pass
                    try:
                        self.page.get_by_role("link", name=re.compile(r"Consultazione", re.I)).first.wait_for(timeout=10_000)
                        self._debug_save("goto_04b_after_consultazione_visible")
                        return
                    except Exception:
                        pass
        except Exception:
            pass

        # Final fallback: semantic click by text (less reliable).
        ok = (
            self._click_first_by_role(
                "link",
                ["Fatture e Corrispettivi", "Fatture e corrispettivi"],
                strict=False,
            )
            or self._click_first_by_role(
                "button",
                ["Fatture e Corrispettivi", "Fatture e corrispettivi", "Accedi"],
                strict=False,
            )
        )
        if ok:
            try:
                self.page.wait_for_load_state("domcontentloaded")
            except Exception:
                pass
            try:
                self.page.wait_for_load_state("networkidle")
            except Exception:
                pass
            self._maybe_accept_cookies()
            self._debug_save("goto_03c_after_semantic_click")
            try:
                self.page.wait_for_selector(
                    "#tipo_ut_button, a:has-text('Consultazione'), button:has-text('Consultazione')",
                    timeout=30_000,
                )
            except Exception:
                pass
            try:
                self._ensure_utenza_di_lavoro(
                    working_mode=working_mode,
                    incaricante=incaricante,
                    company_vat=company_vat,
                    timeout_ms=120_000,
                )
                self._debug_save("goto_04c_after_utenza_flow")
                return
            except AdePortalError:
                pass
            try:
                self.page.get_by_role("link", name=re.compile(r"Consultazione", re.I)).first.wait_for(timeout=10_000)
                self._debug_save("goto_04c_after_consultazione_visible")
                return
            except Exception:
                pass

        # If we get here, we failed to enter the actual application.
        # As a last resort: if we are on the working-profile selection page, try to complete it now.
        try:
            title = (self.page.title() or "").lower()
        except Exception:
            title = ""
        if "scelta utenza" in title or "scelta-utenza" in (self.page.url or "").lower():
            try:
                self._ensure_utenza_di_lavoro(
                    working_mode=working_mode,
                    incaricante=incaricante,
                    company_vat=company_vat,
                    timeout_ms=120_000,
                )
                self._debug_save("goto_04d_after_utenza_flow")
                return
            except AdePortalError:
                pass

        self._debug_save("goto_fatture_e_corrispettivi_failed")
        raise AdePortalError(
            "Impossibile aprire il portale 'Fatture e corrispettivi' dall'Area riservata (clic 'Accedi' non riuscito)."
        )
