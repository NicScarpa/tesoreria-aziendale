#!/usr/bin/env python3
"""
Sibill Section Capture Script
Cattura tutte le richieste API, screenshot e asset per una sezione di Sibill.
Usa Playwright Python library per automazione browser con HAR recording.

Uso: python3 capture_section.py <section_name> <page1_path> [page2_path] ...
Esempio: python3 capture_section.py conti /transactions/movements /transactions/payments
"""

import json
import os
import sys
import time
import hashlib
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode
from datetime import datetime

# --- Configuration ---
BASE_URL = "https://app.sibill.com"
PROJECT_ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
CRED_FILE = PROJECT_ROOT / "credenziali.env"
CAPTURE_DIR = PROJECT_ROOT / ".tmp" / "capture"

def load_credentials():
    """Load credentials from credenziali.env"""
    creds = {}
    with open(CRED_FILE) as f:
        for line in f:
            line = line.strip()
            if ":" in line and not line.startswith("http"):
                key, val = line.split(":", 1)
                creds[key.strip()] = val.strip()
    return creds

def setup_output_dir(section_name):
    """Create output directory structure"""
    out = CAPTURE_DIR / section_name
    (out / "screenshots").mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    return out

def capture_section(section_name, page_paths):
    """Main capture function for a section"""
    from playwright.sync_api import sync_playwright

    creds = load_credentials()
    out_dir = setup_output_dir(section_name)
    all_api_calls = []
    all_asset_urls = set()
    interactions_log = []
    request_responses = {}  # track request_id -> response data

    def log_interaction(msg):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        interactions_log.append(entry)
        print(entry)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            record_har_path=str(out_dir / "recording.har"),
            record_har_content="attach",
        )
        page = context.new_page()

        # --- Network interception ---
        captured_requests = []

        def handle_response(response):
            try:
                request = response.request
                url = request.url
                parsed = urlparse(url)

                # Skip non-relevant requests
                skip_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot')
                skip_domains = ('google', 'facebook', 'analytics', 'hotjar', 'sentry', 'segment', 'intercom', 'crisp', 'mixpanel')

                if any(parsed.path.endswith(ext) for ext in skip_extensions):
                    all_asset_urls.add(url)
                    return

                if any(d in parsed.netloc for d in skip_domains):
                    return

                # Capture CSS and JS as assets
                content_type = response.headers.get("content-type", "")
                if "javascript" in content_type or parsed.path.endswith(".js"):
                    all_asset_urls.add(url)
                if "css" in content_type or parsed.path.endswith(".css"):
                    all_asset_urls.add(url)
                if "font" in content_type:
                    all_asset_urls.add(url)
                if "image" in content_type:
                    all_asset_urls.add(url)

                # Capture API calls (JSON responses)
                if "json" in content_type or "api" in parsed.path or parsed.path.startswith("/v"):
                    try:
                        body = response.json()
                    except Exception:
                        try:
                            body = response.text()
                        except Exception:
                            body = None

                    post_data = None
                    try:
                        post_data = request.post_data
                        if post_data:
                            try:
                                post_data = json.loads(post_data)
                            except (json.JSONDecodeError, TypeError):
                                pass
                    except Exception:
                        pass

                    entry = {
                        "url": url,
                        "path": parsed.path,
                        "query": parse_qs(parsed.query),
                        "method": request.method,
                        "requestBody": post_data,
                        "responseBody": body,
                        "statusCode": response.status,
                        "contentType": content_type,
                        "trigger": "pending",  # updated later
                        "page": "pending",  # updated later
                        "timestamp": datetime.now().isoformat(),
                    }
                    captured_requests.append(entry)
            except Exception as e:
                log_interaction(f"  [WARN] Error capturing response for {response.url}: {e}")

        page.on("response", handle_response)

        # --- Login ---
        log_interaction("=== LOGIN ===")
        page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Take screenshot of login page
        page.screenshot(path=str(out_dir / "screenshots" / "00-login.png"))

        # Find and fill login form
        try:
            # Try common selectors for email/password
            email_selectors = ['input[type="email"]', 'input[name="email"]', 'input[name="username"]', '#email', '#username']
            password_selectors = ['input[type="password"]', 'input[name="password"]', '#password']

            email_input = None
            for sel in email_selectors:
                try:
                    el = page.query_selector(sel)
                    if el:
                        email_input = el
                        break
                except Exception:
                    continue

            password_input = None
            for sel in password_selectors:
                try:
                    el = page.query_selector(sel)
                    if el:
                        password_input = el
                        break
                except Exception:
                    continue

            if email_input and password_input:
                email_input.fill(creds.get("user", ""))
                password_input.fill(creds.get("password", ""))
                time.sleep(0.5)

                # Find and click submit button
                submit_selectors = ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Login")', 'button:has-text("Accedi")', 'button:has-text("Sign in")']
                for sel in submit_selectors:
                    try:
                        btn = page.query_selector(sel)
                        if btn:
                            btn.click()
                            break
                    except Exception:
                        continue

                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(3)
                log_interaction("Login completato")
            else:
                log_interaction(f"[WARN] Login form non trovato. email_input={email_input is not None}, password_input={password_input is not None}")
                # Try screenshot to debug
                page.screenshot(path=str(out_dir / "screenshots" / "00-login-debug.png"))
        except Exception as e:
            log_interaction(f"[ERROR] Login fallito: {e}")
            page.screenshot(path=str(out_dir / "screenshots" / "00-login-error.png"))

        page.screenshot(path=str(out_dir / "screenshots" / "01-after-login.png"))
        log_interaction(f"URL dopo login: {page.url}")

        # --- Capture each page ---
        for page_idx, page_path in enumerate(page_paths, start=1):
            page_url = f"{BASE_URL}{page_path}"
            page_label = page_path.replace("/", "_").strip("_")
            log_interaction(f"\n=== PAGINA {page_idx}/{len(page_paths)}: {page_path} ===")

            # Mark start of this page's captures
            capture_start_idx = len(captured_requests)

            # Navigate
            try:
                page.goto(page_url, wait_until="networkidle", timeout=30000)
                time.sleep(3)
                log_interaction(f"Navigato a {page_url}")
            except Exception as e:
                log_interaction(f"[ERROR] Navigazione fallita: {e}")
                continue

            # Screenshot initial state
            page.screenshot(path=str(out_dir / "screenshots" / f"{page_idx:02d}-{page_label}-initial.png"), full_page=True)

            # --- Interactions ---

            # 1. Tabs
            log_interaction("  Cercando tab...")
            tab_selectors = [
                '[role="tab"]',
                '.tab', '.tabs button', '.tabs a',
                'button[data-state]',
                '[class*="tab"]',
            ]
            for sel in tab_selectors:
                try:
                    tabs = page.query_selector_all(sel)
                    if tabs and len(tabs) > 1:
                        log_interaction(f"  Trovati {len(tabs)} tab con selector '{sel}'")
                        for i, tab in enumerate(tabs):
                            try:
                                tab_text = tab.inner_text().strip()[:50]
                                if tab.is_visible() and tab.is_enabled():
                                    tab.click()
                                    time.sleep(2)
                                    page.wait_for_load_state("networkidle", timeout=10000)
                                    page.screenshot(path=str(out_dir / "screenshots" / f"{page_idx:02d}-{page_label}-tab{i}-{tab_text[:20]}.png"))
                                    log_interaction(f"    Tab {i}: '{tab_text}' — click OK")
                            except Exception as e:
                                log_interaction(f"    Tab {i}: errore — {e}")
                        break  # found working tab selector
                except Exception:
                    continue

            # 2. Filters / Dropdowns
            log_interaction("  Cercando filtri/dropdown...")
            filter_selectors = [
                'select', '[role="combobox"]', '[role="listbox"]',
                'button[class*="filter"]', 'button[class*="select"]',
                '[class*="dropdown"]', '[class*="Filter"]',
            ]
            for sel in filter_selectors:
                try:
                    filters = page.query_selector_all(sel)
                    if filters:
                        log_interaction(f"  Trovati {len(filters)} filtri con selector '{sel}'")
                        for i, flt in enumerate(filters[:5]):  # max 5 filters
                            try:
                                if flt.is_visible():
                                    flt.click()
                                    time.sleep(1)
                                    # Try to select an option if it's a dropdown
                                    options = page.query_selector_all('[role="option"]')
                                    if options and len(options) > 1:
                                        options[1].click()  # select second option
                                        time.sleep(2)
                                        page.wait_for_load_state("networkidle", timeout=10000)
                                        log_interaction(f"    Filtro {i}: selezionata opzione")
                                    else:
                                        # Close by clicking elsewhere
                                        page.keyboard.press("Escape")
                                    page.screenshot(path=str(out_dir / "screenshots" / f"{page_idx:02d}-{page_label}-filter{i}.png"))
                            except Exception as e:
                                log_interaction(f"    Filtro {i}: errore — {e}")
                except Exception:
                    continue

            # 3. Pagination
            log_interaction("  Cercando paginazione...")
            pagination_selectors = [
                'button[aria-label*="next"]', 'button[aria-label*="Next"]',
                'a[aria-label*="next"]', '[class*="pagination"] button',
                'button:has-text(">")', 'button:has-text("Avanti")',
                '[class*="Pagination"] button',
            ]
            for sel in pagination_selectors:
                try:
                    next_btns = page.query_selector_all(sel)
                    for btn in next_btns:
                        if btn.is_visible() and btn.is_enabled():
                            for pg in range(2):  # go 2 pages forward
                                btn.click()
                                time.sleep(2)
                                page.wait_for_load_state("networkidle", timeout=10000)
                                log_interaction(f"    Paginazione: pagina avanti")
                                page.screenshot(path=str(out_dir / "screenshots" / f"{page_idx:02d}-{page_label}-page{pg+2}.png"))
                            break
                    break
                except Exception:
                    continue

            # 4. Table sorting (click headers)
            log_interaction("  Cercando colonne ordinabili...")
            try:
                th_elements = page.query_selector_all('th[role="columnheader"], th button, thead th')
                if th_elements:
                    for i, th in enumerate(th_elements[:3]):  # max 3 columns
                        try:
                            if th.is_visible():
                                th.click()
                                time.sleep(1.5)
                                page.wait_for_load_state("networkidle", timeout=10000)
                                log_interaction(f"    Colonna {i}: click ordinamento")
                        except Exception:
                            pass
            except Exception:
                pass

            # 5. Row details (click first 2-3 rows)
            log_interaction("  Cercando righe cliccabili...")
            row_selectors = [
                'tbody tr', '[role="row"]', 'table tr:not(:first-child)',
                '[class*="row"]', '[class*="Row"]',
            ]
            for sel in row_selectors:
                try:
                    rows = page.query_selector_all(sel)
                    if rows and len(rows) > 0:
                        log_interaction(f"  Trovate {len(rows)} righe con selector '{sel}'")
                        for i, row in enumerate(rows[:3]):
                            try:
                                if row.is_visible():
                                    row.click()
                                    time.sleep(2)
                                    page.wait_for_load_state("networkidle", timeout=10000)
                                    page.screenshot(path=str(out_dir / "screenshots" / f"{page_idx:02d}-{page_label}-detail{i}.png"))
                                    log_interaction(f"    Riga {i}: click dettaglio")

                                    # Check if a modal/drawer opened
                                    modals = page.query_selector_all('[role="dialog"], [class*="modal"], [class*="Modal"], [class*="drawer"], [class*="Drawer"], [class*="sheet"], [class*="Sheet"]')
                                    if modals:
                                        log_interaction(f"    Modal/drawer aperto")
                                        page.screenshot(path=str(out_dir / "screenshots" / f"{page_idx:02d}-{page_label}-modal{i}.png"))
                                        # Close modal
                                        close_btns = page.query_selector_all('[aria-label="Close"], [class*="close"], button:has-text("×"), button:has-text("Chiudi")')
                                        for cb in close_btns:
                                            try:
                                                if cb.is_visible():
                                                    cb.click()
                                                    time.sleep(1)
                                                    break
                                            except Exception:
                                                pass
                                        else:
                                            page.keyboard.press("Escape")
                                            time.sleep(1)
                            except Exception as e:
                                log_interaction(f"    Riga {i}: errore — {e}")
                        break
                except Exception:
                    continue

            # 6. Buttons (export, create, etc) - open but don't save
            log_interaction("  Cercando bottoni azione...")
            action_selectors = [
                'button:has-text("Export")', 'button:has-text("Esporta")',
                'button:has-text("Scarica")', 'button:has-text("Download")',
                'button:has-text("Nuovo")', 'button:has-text("Crea")',
                'button:has-text("Aggiungi")', 'button:has-text("Importa")',
            ]
            for sel in action_selectors:
                try:
                    btns = page.query_selector_all(sel)
                    for btn in btns[:2]:
                        if btn.is_visible() and btn.is_enabled():
                            btn_text = btn.inner_text().strip()[:30]
                            # Don't click destructive buttons
                            if any(word in btn_text.lower() for word in ['elimina', 'delete', 'cancella', 'rimuovi']):
                                continue
                            btn.click()
                            time.sleep(2)
                            page.wait_for_load_state("networkidle", timeout=10000)
                            page.screenshot(path=str(out_dir / "screenshots" / f"{page_idx:02d}-{page_label}-action-{btn_text[:15]}.png"))
                            log_interaction(f"    Bottone '{btn_text}': click")
                            # Close any opened modal/form
                            page.keyboard.press("Escape")
                            time.sleep(1)
                except Exception:
                    continue

            # 7. Scroll to trigger lazy loading
            log_interaction("  Scrollando per lazy loading...")
            try:
                for scroll_i in range(3):
                    page.evaluate("window.scrollBy(0, window.innerHeight)")
                    time.sleep(1.5)
                page.wait_for_load_state("networkidle", timeout=10000)
                page.screenshot(path=str(out_dir / "screenshots" / f"{page_idx:02d}-{page_label}-scrolled.png"), full_page=True)
                log_interaction("  Scroll completato")
            except Exception:
                pass

            # Tag all captured requests from this page
            for req in captured_requests[capture_start_idx:]:
                if req["trigger"] == "pending":
                    req["trigger"] = "page_interaction"
                if req["page"] == "pending":
                    req["page"] = page_path

            # Final screenshot
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)
            page.screenshot(path=str(out_dir / "screenshots" / f"{page_idx:02d}-{page_label}-final.png"), full_page=True)

            log_interaction(f"  API catturate per questa pagina: {len(captured_requests) - capture_start_idx}")

        # --- Save outputs ---
        log_interaction(f"\n=== SALVATAGGIO OUTPUT ===")

        # Close context to save HAR
        context.close()
        browser.close()

    # Save api-calls.json
    api_calls_path = out_dir / "api-calls.json"
    with open(api_calls_path, "w") as f:
        json.dump(captured_requests, f, indent=2, ensure_ascii=False, default=str)
    log_interaction(f"API calls salvate: {len(captured_requests)} chiamate in {api_calls_path}")

    # Save asset URLs
    assets_path = out_dir / "assets-urls.json"
    with open(assets_path, "w") as f:
        json.dump(sorted(list(all_asset_urls)), f, indent=2)
    log_interaction(f"Asset URLs salvati: {len(all_asset_urls)} URLs in {assets_path}")

    # Save interactions log
    log_path = out_dir / "interactions.log"
    with open(log_path, "w") as f:
        f.write("\n".join(interactions_log))
    log_interaction(f"Log interazioni salvato in {log_path}")

    # Summary
    log_interaction(f"\n=== RIEPILOGO ===")
    log_interaction(f"Sezione: {section_name}")
    log_interaction(f"Pagine catturate: {len(page_paths)}")
    log_interaction(f"API calls totali: {len(captured_requests)}")
    log_interaction(f"Asset URLs: {len(all_asset_urls)}")
    log_interaction(f"Screenshots: {len(list((out_dir / 'screenshots').glob('*.png')))}")
    log_interaction(f"HAR file: {out_dir / 'recording.har'}")
    log_interaction(f"Output directory: {out_dir}")

    return {
        "section": section_name,
        "pages": len(page_paths),
        "api_calls": len(captured_requests),
        "asset_urls": len(all_asset_urls),
        "output_dir": str(out_dir),
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 capture_section.py <section_name> <page1_path> [page2_path] ...")
        print("Esempio: python3 capture_section.py conti /transactions/movements /transactions/payments")
        sys.exit(1)

    section_name = sys.argv[1]
    page_paths = sys.argv[2:]

    print(f"Cattura sezione '{section_name}' — {len(page_paths)} pagine")
    print(f"Pagine: {page_paths}")
    print()

    result = capture_section(section_name, page_paths)
    print(f"\nRisultato: {json.dumps(result, indent=2)}")
