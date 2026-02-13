#!/usr/bin/env python3
"""
T3 — Playwright: Export, screenshot e test live di tutti i moduli Sibill.
Scarica report/export, cattura screenshot degli stati, e documenta le API.
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Project root
ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
REPORTS_DIR = ROOT / "assets" / "reports"
SCREENSHOTS_DIR = ROOT / "assets" / "screenshots" / "fase4"
API_TRACES_DIR = ROOT / "assets" / "api-traces" / "fase4"
TMP_DIR = ROOT / ".tmp"

# Ensure directories
for d in [REPORTS_DIR, SCREENSHOTS_DIR, API_TRACES_DIR, TMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Load credentials
env_path = ROOT / "credenziali.env"
creds = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('http'):
            continue
        # Handle both key: value and key=value formats
        if ':' in line:
            key, val = line.split(':', 1)
            creds[key.strip().lower()] = val.strip()
        elif '=' in line:
            key, val = line.split('=', 1)
            creds[key.strip().lower()] = val.strip()

email = creds.get('user', creds.get('email', ''))
password = creds.get('password', creds.get('pass', ''))

if not email or not password:
    print(f"ERROR: Could not load credentials. Keys found: {list(creds.keys())}")
    sys.exit(1)

print(f"[OK] Credentials loaded for: {email[:3]}***")

from playwright.sync_api import sync_playwright

# Collect findings
findings = {
    "timestamp": datetime.now().isoformat(),
    "files_downloaded": [],
    "api_endpoints_captured": [],
    "observations": [],
    "limitations": [],
    "screenshots_taken": []
}

# Track API calls
api_calls = []

def on_response(response):
    """Capture API responses."""
    url = response.url
    if 'api.' in url or '/api/' in url or 'graphql' in url.lower():
        try:
            status = response.status
            method = response.request.method
            content_type = response.headers.get('content-type', '')

            entry = {
                "url": url,
                "method": method,
                "status": status,
                "content_type": content_type,
                "timestamp": datetime.now().isoformat()
            }

            # Try to get JSON body for API calls
            if 'json' in content_type and status < 400:
                try:
                    body = response.json()
                    # Limit size
                    body_str = json.dumps(body)
                    if len(body_str) > 50000:
                        entry["body_truncated"] = True
                        entry["body_preview"] = body_str[:5000]
                    else:
                        entry["body"] = body
                except:
                    pass

            api_calls.append(entry)
        except:
            pass

def screenshot(page, name, description=""):
    """Take a screenshot and log it."""
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    findings["screenshots_taken"].append({"name": name, "description": description, "path": str(path)})
    print(f"  [SCREENSHOT] {name}: {description}")

def wait_for_load(page, timeout=5000):
    """Wait for network to be idle."""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except:
        time.sleep(2)

def save_download(download, filename):
    """Save a download to reports directory."""
    path = REPORTS_DIR / filename
    download.save_as(str(path))
    findings["files_downloaded"].append({"filename": filename, "path": str(path)})
    print(f"  [DOWNLOAD] Saved: {filename}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        accept_downloads=True
    )
    page = context.new_page()

    # Listen for API responses
    page.on("response", on_response)

    # ==========================================
    # STEP 1: LOGIN
    # ==========================================
    print("\n=== STEP 1: LOGIN ===")
    page.goto("https://app.sibill.com/", wait_until="networkidle", timeout=30000)
    time.sleep(2)
    screenshot(page, "00-login-page", "Pagina di login")

    # Fill login form
    # Try different selectors for email
    email_selectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[placeholder*="email" i]',
        'input[placeholder*="mail" i]',
        '#email',
        'input[type="text"]'
    ]

    email_filled = False
    for sel in email_selectors:
        try:
            el = page.query_selector(sel)
            if el:
                el.fill(email)
                email_filled = True
                print(f"  [OK] Email filled using selector: {sel}")
                break
        except:
            continue

    if not email_filled:
        print("  [ERROR] Could not find email field")
        # Try to get page HTML to debug
        html = page.content()[:2000]
        print(f"  Page content preview: {html[:500]}")

    # Fill password
    pw_selectors = [
        'input[type="password"]',
        'input[name="password"]',
        '#password'
    ]

    pw_filled = False
    for sel in pw_selectors:
        try:
            el = page.query_selector(sel)
            if el:
                el.fill(password)
                pw_filled = True
                print(f"  [OK] Password filled using selector: {sel}")
                break
        except:
            continue

    # Click login button
    login_selectors = [
        'button[type="submit"]',
        'button:has-text("Login")',
        'button:has-text("Accedi")',
        'button:has-text("Sign in")',
        'button:has-text("Entra")',
        'input[type="submit"]'
    ]

    for sel in login_selectors:
        try:
            el = page.query_selector(sel)
            if el:
                el.click()
                print(f"  [OK] Login button clicked: {sel}")
                break
        except:
            continue

    # Wait for navigation after login
    time.sleep(5)
    wait_for_load(page, timeout=15000)

    current_url = page.url
    print(f"  [INFO] Current URL after login: {current_url}")
    screenshot(page, "01-after-login", "Stato dopo il login")

    # Check if login was successful
    if 'login' in current_url.lower() or 'signin' in current_url.lower():
        print("  [WARNING] May still be on login page. Trying alternative login approach...")
        # Take screenshot for debugging
        screenshot(page, "01b-login-debug", "Debug: possibile login fallito")
        # Try pressing Enter instead
        page.keyboard.press("Enter")
        time.sleep(5)
        wait_for_load(page)
        current_url = page.url
        print(f"  [INFO] URL after Enter: {current_url}")

    findings["observations"].append(f"Login result URL: {current_url}")

    # ==========================================
    # STEP 2: EXPORT CASHFLOW (PRIORITÀ MASSIMA)
    # ==========================================
    print("\n=== STEP 2: EXPORT CASHFLOW ===")
    page.goto("https://app.sibill.com/cashflow", wait_until="networkidle", timeout=30000)
    time.sleep(3)
    wait_for_load(page)
    screenshot(page, "02-cashflow-main", "Pagina cashflow principale")

    # Look for export button
    export_selectors = [
        'button:has-text("Esporta")',
        'button:has-text("Export")',
        'button:has-text("Download")',
        'button:has-text("Scarica")',
        '[aria-label*="export" i]',
        '[aria-label*="download" i]',
        '[aria-label*="scarica" i]',
        'button svg[data-testid*="download" i]',
        'a[href*="export"]',
        'a[href*="download"]',
        # Icons - common patterns for download buttons
        'button:has(svg)',
    ]

    export_found = False
    for sel in export_selectors[:-1]:  # Skip the generic svg one for now
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                print(f"  [OK] Found export button: {sel}")
                export_found = True

                # Set up download listener
                with page.expect_download(timeout=15000) as download_info:
                    el.click()
                    time.sleep(2)
                download = download_info.value
                save_download(download, "cashflow-export." + (download.suggested_filename.split('.')[-1] if download.suggested_filename else "xlsx"))
                break
        except Exception as e:
            continue

    if not export_found:
        print("  [INFO] No direct export button found. Looking for menu/dropdown...")
        # Try clicking on three-dot menus or similar
        menu_selectors = [
            'button[aria-label*="more" i]',
            'button[aria-label*="menu" i]',
            'button[aria-label*="opzioni" i]',
            '[data-testid*="more"]',
            '.MuiIconButton-root',
        ]
        for sel in menu_selectors:
            try:
                els = page.query_selector_all(sel)
                for el in els:
                    if el.is_visible():
                        el.click()
                        time.sleep(1)
                        screenshot(page, "02b-cashflow-menu-opened", "Menu aperto su cashflow")
                        # Look for export option in dropdown
                        for text in ["Esporta", "Export", "Download", "Excel", "CSV"]:
                            try:
                                menu_item = page.query_selector(f'text="{text}"')
                                if menu_item and menu_item.is_visible():
                                    print(f"  [OK] Found '{text}' in menu")
                                    with page.expect_download(timeout=15000) as download_info:
                                        menu_item.click()
                                        time.sleep(3)
                                    download = download_info.value
                                    fname = download.suggested_filename or "cashflow-export.xlsx"
                                    save_download(download, fname)
                                    export_found = True
                                    break
                            except:
                                continue
                        if export_found:
                            break
                        # Close menu if nothing found
                        page.keyboard.press("Escape")
                        time.sleep(0.5)
            except:
                continue

    if not export_found:
        findings["limitations"].append("Export cashflow: pulsante di export non trovato o non disponibile nel piano trial")
        print("  [WARNING] Could not find/use cashflow export")
        # Document the page structure for analysis
        buttons = page.query_selector_all("button")
        btn_texts = []
        for b in buttons:
            try:
                txt = b.inner_text()
                if txt.strip():
                    btn_texts.append(txt.strip()[:50])
            except:
                pass
        findings["observations"].append(f"Cashflow page buttons: {btn_texts}")

    # Try different cashflow views
    print("  [INFO] Trying different cashflow views...")

    # Look for period selectors
    period_selectors = ['text="Settimanale"', 'text="Mensile"', 'text="Giornaliero"',
                       'text="Weekly"', 'text="Monthly"', 'text="Daily"']
    for sel in period_selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                time.sleep(2)
                wait_for_load(page)
                view_name = sel.split('"')[1].lower()
                screenshot(page, f"02c-cashflow-{view_name}", f"Cashflow vista {view_name}")
                break
        except:
            continue

    # ==========================================
    # STEP 3: INVOICES / FATTURE
    # ==========================================
    print("\n=== STEP 3: INVOICES DASHBOARD ===")

    invoice_pages = [
        ("/invoices/dashboard", "03a-invoices-dashboard", "Dashboard fatture"),
        ("/invoices/issued", "03b-invoices-issued", "Fatture emesse"),
        ("/invoices/received", "03c-invoices-received", "Fatture ricevute"),
        ("/invoices/bills", "03d-invoices-bills", "Fatture da pagare"),
    ]

    for path, ss_name, desc in invoice_pages:
        try:
            page.goto(f"https://app.sibill.com{path}", wait_until="networkidle", timeout=20000)
            time.sleep(2)
            wait_for_load(page)
            screenshot(page, ss_name, desc)

            # Try to find export button
            for sel in ['button:has-text("Esporta")', 'button:has-text("Export")',
                       'button:has-text("Download")', 'button:has-text("Excel")',
                       'button:has-text("CSV")']:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        print(f"  [OK] Found export on {path}: {sel}")
                        try:
                            with page.expect_download(timeout=10000) as download_info:
                                el.click()
                                time.sleep(2)
                            download = download_info.value
                            fname = download.suggested_filename or f"invoices-{path.split('/')[-1]}.xlsx"
                            save_download(download, fname)
                        except Exception as e:
                            print(f"  [WARNING] Export click didn't trigger download: {e}")
                            screenshot(page, f"{ss_name}-after-export-click", f"Dopo click export su {path}")
                        break
                except:
                    continue
        except Exception as e:
            print(f"  [ERROR] {path}: {e}")
            findings["limitations"].append(f"Errore navigazione {path}: {str(e)[:100]}")

    # ==========================================
    # STEP 4: MOVIMENTI / TRANSACTIONS
    # ==========================================
    print("\n=== STEP 4: MOVIMENTI ===")
    page.goto("https://app.sibill.com/transactions/movements", wait_until="networkidle", timeout=20000)
    time.sleep(3)
    wait_for_load(page)
    screenshot(page, "04a-movements-list", "Lista movimenti")

    # Look for filters
    filter_selectors = ['button:has-text("Filtra")', 'button:has-text("Filter")',
                       '[aria-label*="filter" i]', '[aria-label*="filtr" i]']
    for sel in filter_selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                time.sleep(1)
                screenshot(page, "04b-movements-filters", "Filtri movimenti aperti")
                page.keyboard.press("Escape")
                break
        except:
            continue

    # Look for TO_VERIFY transactions
    try:
        verify_items = page.query_selector_all('[class*="verify" i], [data-status*="verify" i], :text("Da verificare"), :text("TO_VERIFY")')
        if verify_items:
            print(f"  [INFO] Found {len(verify_items)} items to verify")
            # Click on first one
            for item in verify_items:
                if item.is_visible():
                    item.click()
                    time.sleep(2)
                    wait_for_load(page)
                    screenshot(page, "04c-movement-detail-verify", "Dettaglio movimento da verificare")
                    break
    except:
        pass

    # Try export on movements
    for sel in ['button:has-text("Esporta")', 'button:has-text("Export")', 'button:has-text("Excel")']:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                try:
                    with page.expect_download(timeout=10000) as download_info:
                        el.click()
                        time.sleep(2)
                    download = download_info.value
                    fname = download.suggested_filename or "movements-export.xlsx"
                    save_download(download, fname)
                except:
                    screenshot(page, "04d-movements-export-attempt", "Tentativo export movimenti")
                break
        except:
            continue

    # ==========================================
    # STEP 5: SCADENZARIO / OUTSTANDING
    # ==========================================
    print("\n=== STEP 5: SCADENZARIO ===")

    outstanding_pages = [
        ("/outstanding", "05a-outstanding-main", "Scadenzario principale"),
        ("/outstanding/recurrences/received", "05b-recurrences-received", "Ricorrenze ricevute"),
        ("/outstanding/recurrences/issued", "05c-recurrences-issued", "Ricorrenze emesse"),
        ("/outstanding/rules", "05d-outstanding-rules", "Regole scadenzario"),
    ]

    for path, ss_name, desc in outstanding_pages:
        try:
            page.goto(f"https://app.sibill.com{path}", wait_until="networkidle", timeout=20000)
            time.sleep(2)
            wait_for_load(page)
            screenshot(page, ss_name, desc)

            # Try export
            for sel in ['button:has-text("Esporta")', 'button:has-text("Export")']:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        try:
                            with page.expect_download(timeout=10000) as download_info:
                                el.click()
                                time.sleep(2)
                            download = download_info.value
                            fname = download.suggested_filename or f"outstanding-{path.split('/')[-1]}.xlsx"
                            save_download(download, fname)
                        except:
                            screenshot(page, f"{ss_name}-export-attempt", f"Tentativo export {desc}")
                        break
                except:
                    continue
        except Exception as e:
            print(f"  [ERROR] {path}: {e}")

    # ==========================================
    # STEP 6: PAGAMENTI / PAYMENTS
    # ==========================================
    print("\n=== STEP 6: PAGAMENTI ===")
    page.goto("https://app.sibill.com/transactions/payments", wait_until="networkidle", timeout=20000)
    time.sleep(3)
    wait_for_load(page)
    screenshot(page, "06a-payments-list", "Lista pagamenti")

    # Look for "Create payment" button
    create_selectors = [
        'button:has-text("Crea")',
        'button:has-text("Nuovo")',
        'button:has-text("Aggiungi")',
        'button:has-text("New")',
        'button:has-text("Create")',
        'a:has-text("Crea pagamento")',
        'button:has-text("Paga")',
    ]

    for sel in create_selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                print(f"  [OK] Found create button: {sel}")
                el.click()
                time.sleep(2)
                wait_for_load(page)
                screenshot(page, "06b-payment-create-form", "Form creazione pagamento")

                # Capture the form fields
                inputs = page.query_selector_all("input, select, textarea")
                form_fields = []
                for inp in inputs:
                    try:
                        field_info = {
                            "tag": inp.evaluate("el => el.tagName"),
                            "type": inp.get_attribute("type") or "",
                            "name": inp.get_attribute("name") or "",
                            "placeholder": inp.get_attribute("placeholder") or "",
                            "id": inp.get_attribute("id") or "",
                            "aria-label": inp.get_attribute("aria-label") or "",
                        }
                        form_fields.append(field_info)
                    except:
                        pass

                findings["observations"].append(f"Payment form fields: {json.dumps(form_fields, indent=2)}")

                # Go back without submitting
                page.go_back()
                time.sleep(2)
                break
        except:
            continue

    # F24 page
    print("  [INFO] Navigating to F24...")
    page.goto("https://app.sibill.com/f24", wait_until="networkidle", timeout=20000)
    time.sleep(2)
    wait_for_load(page)
    screenshot(page, "06c-f24-page", "Pagina F24")

    # Check for F24 form
    f24_btn_selectors = [
        'button:has-text("Paga F24")',
        'button:has-text("Nuovo F24")',
        'button:has-text("Carica F24")',
        'a:has-text("F24")',
    ]
    for sel in f24_btn_selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                time.sleep(2)
                screenshot(page, "06d-f24-form", "Form F24")
                page.go_back()
                time.sleep(1)
                break
        except:
            continue

    # ==========================================
    # STEP 7: CASHFLOW INTERACTIONS
    # ==========================================
    print("\n=== STEP 7: CASHFLOW INTERACTIONS ===")
    page.goto("https://app.sibill.com/cashflow", wait_until="networkidle", timeout=20000)
    time.sleep(3)
    wait_for_load(page)

    # Try clicking on a table cell to open aside panel
    try:
        # Look for table cells with amounts
        cells = page.query_selector_all("td, [role='cell'], [class*='cell']")
        for cell in cells[:20]:
            try:
                text = cell.inner_text()
                if any(c.isdigit() for c in text) and ('€' in text or ',' in text or '.' in text):
                    cell.click()
                    time.sleep(2)
                    screenshot(page, "07a-cashflow-cell-click", "Cashflow dopo click su cella con importo")
                    # Check if aside/drawer opened
                    aside = page.query_selector('[class*="aside"], [class*="drawer"], [class*="panel"], [class*="sidebar"], [role="dialog"]')
                    if aside:
                        screenshot(page, "07b-cashflow-aside-panel", "Aside panel del cashflow")
                    page.keyboard.press("Escape")
                    time.sleep(1)
                    break
            except:
                continue
    except:
        pass

    # Try expanding categories
    try:
        expandable = page.query_selector_all('[class*="expand"], [class*="toggle"], [class*="accordion"], button:has(svg[class*="chevron"])')
        for exp in expandable[:5]:
            try:
                if exp.is_visible():
                    exp.click()
                    time.sleep(1)
            except:
                continue
        screenshot(page, "07c-cashflow-expanded", "Cashflow con categorie espanse")
    except:
        pass

    # ==========================================
    # STEP 8: SETTINGS & ACCOUNTS
    # ==========================================
    print("\n=== STEP 8: SETTINGS ===")

    settings_pages = [
        ("/settings", "08a-settings-main", "Settings principale"),
        ("/accounts", "08b-accounts", "Conti bancari"),
        ("/counterparts", "08c-counterparts", "Controparti"),
        ("/transactions/rules", "08d-transaction-rules", "Regole transazioni"),
    ]

    for path, ss_name, desc in settings_pages:
        try:
            page.goto(f"https://app.sibill.com{path}", wait_until="networkidle", timeout=20000)
            time.sleep(2)
            wait_for_load(page)
            screenshot(page, ss_name, desc)
        except Exception as e:
            print(f"  [ERROR] {path}: {e}")

    # ==========================================
    # STEP 9: RECONCILIATION DETAILS
    # ==========================================
    print("\n=== STEP 9: RICONCILIAZIONE ===")
    page.goto("https://app.sibill.com/transactions/movements", wait_until="networkidle", timeout=20000)
    time.sleep(3)
    wait_for_load(page)

    # Try to find and click on a specific transaction to see reconciliation
    try:
        rows = page.query_selector_all("tr, [role='row'], [class*='row']")
        for row in rows[1:10]:  # Skip header
            try:
                if row.is_visible():
                    row.click()
                    time.sleep(2)
                    wait_for_load(page)
                    current = page.url
                    if current != "https://app.sibill.com/transactions/movements":
                        screenshot(page, "09a-transaction-detail", f"Dettaglio transazione: {current}")
                        # Look for reconciliation panel
                        page.go_back()
                        time.sleep(1)
                        break
            except:
                continue
    except:
        pass

    # Try reconciliations page directly
    page.goto("https://app.sibill.com/reconciliations", wait_until="networkidle", timeout=15000)
    time.sleep(2)
    screenshot(page, "09b-reconciliations-page", "Pagina riconciliazioni")

    # ==========================================
    # STEP 10: ADDITIONAL PAGES
    # ==========================================
    print("\n=== STEP 10: PAGINE AGGIUNTIVE ===")

    additional_pages = [
        ("/cashflow/categories", "10a-cashflow-categories", "Categorie cashflow"),
        ("/invoices/profile", "10b-invoices-profile", "Profilo fatturazione"),
        ("/integrations", "10c-integrations", "Integrazioni"),
        ("/connections", "10d-connections", "Connessioni bancarie"),
    ]

    for path, ss_name, desc in additional_pages:
        try:
            page.goto(f"https://app.sibill.com{path}", wait_until="networkidle", timeout=15000)
            time.sleep(2)
            wait_for_load(page)
            screenshot(page, ss_name, desc)
        except Exception as e:
            print(f"  [INFO] {path}: {e}")

    # ==========================================
    # SAVE API TRACES
    # ==========================================
    print("\n=== SAVING API TRACES ===")

    # Save all captured API calls
    api_trace_path = API_TRACES_DIR / "all-api-calls.json"
    # Sanitize - remove any auth tokens
    sanitized_calls = []
    for call in api_calls:
        sanitized = dict(call)
        url = sanitized.get("url", "")
        # Don't include calls with tokens in URL
        if "token=" in url.lower() or "key=" in url.lower():
            url_parts = url.split("?")
            sanitized["url"] = url_parts[0] + "?[PARAMS_REDACTED]"
        sanitized_calls.append(sanitized)

    with open(api_trace_path, "w") as f:
        json.dump(sanitized_calls, f, indent=2, default=str)
    print(f"  [OK] Saved {len(sanitized_calls)} API calls to {api_trace_path}")

    # Extract unique endpoints
    endpoints = set()
    for call in sanitized_calls:
        url = call.get("url", "")
        method = call.get("method", "GET")
        # Remove query params for uniqueness
        base_url = url.split("?")[0]
        endpoints.add(f"{method} {base_url}")

    findings["api_endpoints_captured"] = sorted(list(endpoints))

    # ==========================================
    # FINAL SUMMARY
    # ==========================================
    print("\n=== SUMMARY ===")
    print(f"  Screenshots taken: {len(findings['screenshots_taken'])}")
    print(f"  Files downloaded: {len(findings['files_downloaded'])}")
    print(f"  API endpoints captured: {len(findings['api_endpoints_captured'])}")
    print(f"  Observations: {len(findings['observations'])}")
    print(f"  Limitations: {len(findings['limitations'])}")

    # Save findings
    findings_path = TMP_DIR / "t3-playwright-findings.json"
    with open(findings_path, "w") as f:
        json.dump(findings, f, indent=2, default=str)
    print(f"\n  [OK] Findings saved to {findings_path}")

    browser.close()

print("\n=== DONE ===")
