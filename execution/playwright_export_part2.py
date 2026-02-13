#!/usr/bin/env python3
"""
T3 Part 2 — Completa gli step rimasti dal primo run:
- Step 7: Cashflow interactions (aside panel, expanded categories)
- Step 8: Settings & accounts
- Step 9: Reconciliation details
- Step 10: Additional pages
- Export aggiuntivi (movimenti, scadenzario, fatture)
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
REPORTS_DIR = ROOT / "assets" / "reports"
SCREENSHOTS_DIR = ROOT / "assets" / "screenshots" / "fase4"
API_TRACES_DIR = ROOT / "assets" / "api-traces" / "fase4"
TMP_DIR = ROOT / ".tmp"

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
        if ':' in line:
            key, val = line.split(':', 1)
            creds[key.strip().lower()] = val.strip()
        elif '=' in line:
            key, val = line.split('=', 1)
            creds[key.strip().lower()] = val.strip()

email = creds.get('user', creds.get('email', ''))
password = creds.get('password', creds.get('pass', ''))

from playwright.sync_api import sync_playwright

findings = {
    "timestamp": datetime.now().isoformat(),
    "files_downloaded": [],
    "api_endpoints_captured": [],
    "observations": [],
    "limitations": [],
    "screenshots_taken": []
}

api_calls = []

def on_response(response):
    url = response.url
    if 'api.' in url or '/api/' in url or 'graphql' in url.lower() or 'sibill' in url:
        try:
            entry = {
                "url": url,
                "method": response.request.method,
                "status": response.status,
                "content_type": response.headers.get('content-type', ''),
                "timestamp": datetime.now().isoformat()
            }
            if 'json' in entry["content_type"] and response.status < 400:
                try:
                    body = response.json()
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

def screenshot(page, name, desc=""):
    path = SCREENSHOTS_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        findings["screenshots_taken"].append({"name": name, "description": desc})
        print(f"  [SCREENSHOT] {name}: {desc}")
    except Exception as e:
        print(f"  [ERROR] Screenshot {name}: {e}")

def wait_load(page, t=5000):
    try:
        page.wait_for_load_state("networkidle", timeout=t)
    except:
        time.sleep(2)

def safe_goto(page, url, timeout=30000):
    """Navigate with fallback."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        time.sleep(2)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except:
            pass
        return True
    except Exception as e:
        print(f"  [ERROR] Navigation to {url}: {e}")
        return False

def save_download(download, filename):
    path = REPORTS_DIR / filename
    download.save_as(str(path))
    findings["files_downloaded"].append({"filename": filename, "path": str(path)})
    print(f"  [DOWNLOAD] {filename}")

def try_export(page, page_name):
    """Try to find and click an export button, return True if download started."""
    selectors = [
        'button:has-text("Esporta")',
        'button:has-text("Export")',
        'button:has-text("Download")',
        'button:has-text("Scarica")',
        'button:has-text("Excel")',
        'button:has-text("CSV")',
        '[aria-label*="export" i]',
        '[aria-label*="download" i]',
    ]
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                print(f"  [OK] Found export '{sel}' on {page_name}")
                try:
                    with page.expect_download(timeout=15000) as dl_info:
                        el.click()
                        time.sleep(3)
                    download = dl_info.value
                    fname = download.suggested_filename or f"{page_name}-export.xlsx"
                    save_download(download, fname)
                    return True
                except Exception as e:
                    print(f"  [WARNING] Download didn't trigger: {e}")
                    screenshot(page, f"{page_name}-export-modal", f"Dopo click export su {page_name}")
                    # Maybe a modal opened - check for confirm
                    for confirm in ['button:has-text("Conferma")', 'button:has-text("OK")',
                                   'button:has-text("Scarica")', 'button:has-text("Download")']:
                        try:
                            btn = page.query_selector(confirm)
                            if btn and btn.is_visible():
                                try:
                                    with page.expect_download(timeout=10000) as dl_info:
                                        btn.click()
                                        time.sleep(2)
                                    download = dl_info.value
                                    fname = download.suggested_filename or f"{page_name}-export.xlsx"
                                    save_download(download, fname)
                                    return True
                                except:
                                    pass
                        except:
                            continue
                    page.keyboard.press("Escape")
                    time.sleep(1)
                    return False
        except:
            continue
    return False


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        accept_downloads=True
    )
    page = context.new_page()
    page.on("response", on_response)

    # LOGIN
    print("\n=== LOGIN ===")
    safe_goto(page, "https://app.sibill.com/")
    time.sleep(2)

    # Fill login
    for sel in ['input[type="email"]', 'input[type="text"]']:
        try:
            el = page.query_selector(sel)
            if el:
                el.fill(email)
                break
        except:
            continue

    for sel in ['input[type="password"]']:
        try:
            el = page.query_selector(sel)
            if el:
                el.fill(password)
                break
        except:
            continue

    for sel in ['button[type="submit"]']:
        try:
            el = page.query_selector(sel)
            if el:
                el.click()
                break
        except:
            continue

    time.sleep(5)
    wait_load(page, 10000)
    current = page.url
    print(f"  [INFO] After login: {current}")

    if 'login' in current.lower():
        page.keyboard.press("Enter")
        time.sleep(5)
        wait_load(page)
        print(f"  [INFO] After Enter: {page.url}")

    # ==========================================
    # STEP 7: CASHFLOW INTERACTIONS
    # ==========================================
    print("\n=== STEP 7: CASHFLOW INTERACTIONS ===")
    if safe_goto(page, "https://app.sibill.com/cashflow"):
        time.sleep(3)
        screenshot(page, "07-cashflow-fresh", "Cashflow pagina fresca")

        # Try to find clickable elements in the cashflow table
        # Look for the table first
        table = page.query_selector("table, [role='table'], [class*='table']")
        if table:
            print("  [OK] Found table element")
            # Try clicking on a data cell
            cells = page.query_selector_all("td")
            clicked = False
            for cell in cells[:30]:
                try:
                    text = cell.inner_text().strip()
                    # Look for cells with monetary values
                    if text and any(c.isdigit() for c in text):
                        bbox = cell.bounding_box()
                        if bbox and bbox["width"] > 10:
                            cell.click()
                            time.sleep(2)
                            screenshot(page, "07a-cashflow-cell-clicked", f"Cashflow dopo click su cella: {text[:30]}")
                            clicked = True

                            # Check for aside panel / drawer / modal
                            for aside_sel in ['[class*="aside"]', '[class*="drawer"]', '[class*="panel"]',
                                            '[class*="sidebar"]', '[role="dialog"]', '[class*="modal"]',
                                            '[class*="Drawer"]', '[class*="Sheet"]']:
                                aside = page.query_selector(aside_sel)
                                if aside and aside.is_visible():
                                    screenshot(page, "07b-cashflow-aside", "Aside panel cashflow")
                                    print(f"  [OK] Found aside panel with selector: {aside_sel}")
                                    break

                            page.keyboard.press("Escape")
                            time.sleep(1)
                            break
                except:
                    continue

            if not clicked:
                print("  [INFO] No clickable data cells found in cashflow table")
                findings["observations"].append("Cashflow table cells may not be clickable or no data")
        else:
            print("  [WARNING] No table element found on cashflow page")

        # Try to find period/view selectors
        for view_text in ["Settimanale", "Mensile", "Giornaliero", "Trimestrale", "Annuale"]:
            try:
                btn = page.query_selector(f'button:has-text("{view_text}"), [role="tab"]:has-text("{view_text}"), text="{view_text}"')
                if btn and btn.is_visible():
                    btn.click()
                    time.sleep(2)
                    wait_load(page)
                    screenshot(page, f"07c-cashflow-{view_text.lower()}", f"Cashflow vista {view_text}")
                    print(f"  [OK] Switched to {view_text} view")
            except:
                continue

        # Look for account selectors / filters
        try:
            account_filter = page.query_selector('[class*="select"], [class*="dropdown"], [class*="filter"]')
            if account_filter and account_filter.is_visible():
                account_filter.click()
                time.sleep(1)
                screenshot(page, "07d-cashflow-account-filter", "Filtro conti cashflow")
                page.keyboard.press("Escape")
        except:
            pass

        # Try expanding categories (look for arrows/chevrons)
        try:
            expand_btns = page.query_selector_all('button[class*="expand"], [class*="toggle"], [class*="accordion"], [data-testid*="expand"]')
            if expand_btns:
                for btn in expand_btns[:3]:
                    try:
                        if btn.is_visible():
                            btn.click()
                            time.sleep(0.5)
                    except:
                        continue
                time.sleep(1)
                screenshot(page, "07e-cashflow-categories-expanded", "Cashflow categorie espanse")
        except:
            pass

    # ==========================================
    # STEP 8: SETTINGS & CONFIGURATION
    # ==========================================
    print("\n=== STEP 8: SETTINGS ===")

    settings_pages = [
        ("/settings", "08a-settings", "Impostazioni principali"),
        ("/settings/company", "08b-settings-company", "Dati aziendali"),
        ("/settings/users", "08c-settings-users", "Utenti"),
        ("/settings/integrations", "08d-settings-integrations", "Integrazioni"),
        ("/accounts", "08e-accounts", "Conti bancari"),
        ("/counterparts", "08f-counterparts", "Controparti"),
    ]

    for path, ss_name, desc in settings_pages:
        if safe_goto(page, f"https://app.sibill.com{path}"):
            time.sleep(2)
            screenshot(page, ss_name, desc)
            # Document the page content
            try:
                title = page.title()
                h1 = page.query_selector("h1, h2, [class*='title']")
                h1_text = h1.inner_text() if h1 else ""
                findings["observations"].append(f"{path}: title='{title}', heading='{h1_text}'")
            except:
                pass

    # ==========================================
    # STEP 9: EXPORT MOVIMENTI
    # ==========================================
    print("\n=== STEP 9: EXPORT MOVIMENTI ===")
    if safe_goto(page, "https://app.sibill.com/transactions/movements"):
        time.sleep(3)

        exported = try_export(page, "movements")
        if not exported:
            findings["limitations"].append("No export button found on movements page")

    # ==========================================
    # STEP 10: EXPORT SCADENZARIO
    # ==========================================
    print("\n=== STEP 10: EXPORT SCADENZARIO ===")
    if safe_goto(page, "https://app.sibill.com/outstanding"):
        time.sleep(3)

        exported = try_export(page, "outstanding")
        if not exported:
            findings["limitations"].append("No export button found on outstanding page")

    # ==========================================
    # STEP 11: TRANSACTION DETAIL & RECONCILIATION
    # ==========================================
    print("\n=== STEP 11: TRANSACTION DETAIL ===")
    if safe_goto(page, "https://app.sibill.com/transactions/movements"):
        time.sleep(3)

        # Click on a row to see transaction detail
        rows = page.query_selector_all("table tr, [class*='row']")
        for row in rows[1:15]:
            try:
                if row.is_visible():
                    # Check if this is a data row (not header)
                    tds = row.query_selector_all("td")
                    if len(tds) >= 3:
                        tds[0].click()
                        time.sleep(2)
                        wait_load(page)
                        screenshot(page, "11a-transaction-detail", "Dettaglio transazione")

                        # Look for reconciliation info
                        recon_text = page.query_selector('[class*="reconcil"], [class*="match"], text="Riconcilia"')
                        if recon_text:
                            screenshot(page, "11b-transaction-reconciliation", "Info riconciliazione transazione")

                        # Check for category assignment
                        cat = page.query_selector('[class*="categor"], text="Categoria"')
                        if cat:
                            screenshot(page, "11c-transaction-category", "Categoria transazione")

                        # Go back
                        page.go_back()
                        time.sleep(2)
                        break
            except:
                continue

    # ==========================================
    # STEP 12: RULES PAGE
    # ==========================================
    print("\n=== STEP 12: RULES ===")
    if safe_goto(page, "https://app.sibill.com/transactions/rules"):
        time.sleep(2)
        screenshot(page, "12a-rules-page", "Pagina regole transazioni")

        # Try to click "Add rule"
        for sel in ['button:has-text("Aggiungi")', 'button:has-text("Nuova regola")',
                   'button:has-text("Crea")', 'button:has-text("Add")']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    time.sleep(2)
                    screenshot(page, "12b-rules-create-form", "Form creazione regola")
                    page.keyboard.press("Escape")
                    time.sleep(1)
                    break
            except:
                continue

    # ==========================================
    # STEP 13: INVOICES EXPORT
    # ==========================================
    print("\n=== STEP 13: INVOICES EXPORT ===")
    for inv_path, inv_name in [("/invoices/issued", "invoices-issued"),
                                ("/invoices/received", "invoices-received")]:
        if safe_goto(page, f"https://app.sibill.com{inv_path}"):
            time.sleep(3)
            exported = try_export(page, inv_name)
            if not exported:
                findings["limitations"].append(f"No export on {inv_path}")

    # ==========================================
    # STEP 14: ADDITIONAL SCREENSHOT STATES
    # ==========================================
    print("\n=== STEP 14: ADDITIONAL STATES ===")

    # Cashflow categories page
    if safe_goto(page, "https://app.sibill.com/cashflow/categories"):
        time.sleep(2)
        screenshot(page, "14a-cashflow-categories", "Categorie cashflow")

    # Invoices profile
    if safe_goto(page, "https://app.sibill.com/invoices/profile"):
        time.sleep(2)
        screenshot(page, "14b-invoices-profile", "Profilo fatturazione")

    # Try /bank-connections or /connections
    for conn_path in ["/bank-connections", "/connections", "/settings/bank-connections",
                      "/settings/connections"]:
        if safe_goto(page, f"https://app.sibill.com{conn_path}"):
            time.sleep(2)
            if "404" not in page.content() and "not found" not in page.content().lower():
                screenshot(page, "14c-bank-connections", f"Connessioni bancarie ({conn_path})")
                findings["observations"].append(f"Bank connections page found at: {conn_path}")
                break

    # ==========================================
    # STEP 15: RESPONSIVE SCREENSHOTS
    # ==========================================
    print("\n=== STEP 15: RESPONSIVE SCREENSHOTS ===")

    # Mobile viewport
    if safe_goto(page, "https://app.sibill.com/cashflow"):
        time.sleep(3)

        for width, label in [(375, "mobile"), (768, "tablet"), (1024, "desktop-sm")]:
            page.set_viewport_size({"width": width, "height": 900})
            time.sleep(1)
            screenshot(page, f"15-cashflow-{label}-{width}px", f"Cashflow responsive {label} ({width}px)")

        # Reset viewport
        page.set_viewport_size({"width": 1440, "height": 900})

    # ==========================================
    # STEP 16: EMPTY STATES & ERROR STATES
    # ==========================================
    print("\n=== STEP 16: EMPTY/ERROR STATES ===")

    # Try a URL that likely has no data or doesn't exist
    empty_candidates = [
        "/transactions/payments?status=rejected",
        "/invoices/received?status=draft",
        "/outstanding?status=expired",
    ]

    for url_path in empty_candidates:
        if safe_goto(page, f"https://app.sibill.com{url_path}"):
            time.sleep(2)
            # Check for empty state
            empty_indicators = page.query_selector_all('[class*="empty"], [class*="no-data"], [class*="nodata"]')
            if empty_indicators:
                slug = url_path.split("?")[0].split("/")[-1]
                screenshot(page, f"16-empty-{slug}", f"Empty state per {url_path}")
                print(f"  [OK] Found empty state at {url_path}")

    # ==========================================
    # SAVE ALL DATA
    # ==========================================
    print("\n=== SAVING DATA ===")

    # Save API traces
    sanitized = []
    for call in api_calls:
        c = dict(call)
        url = c.get("url", "")
        if any(s in url.lower() for s in ["token=", "key=", "auth="]):
            parts = url.split("?")
            c["url"] = parts[0] + "?[PARAMS_REDACTED]"
        sanitized.append(c)

    api_path = API_TRACES_DIR / "part2-api-calls.json"
    with open(api_path, "w") as f:
        json.dump(sanitized, f, indent=2, default=str)

    endpoints = set()
    for c in sanitized:
        base = c.get("url", "").split("?")[0]
        method = c.get("method", "GET")
        endpoints.add(f"{method} {base}")

    findings["api_endpoints_captured"] = sorted(list(endpoints))

    # Load part 1 findings if exists
    part1_path = TMP_DIR / "t3-playwright-findings.json"
    merged_findings = findings.copy()
    if part1_path.exists():
        try:
            with open(part1_path) as f:
                part1 = json.load(f)
            # Merge
            merged_findings["files_downloaded"] = part1.get("files_downloaded", []) + findings["files_downloaded"]
            merged_findings["screenshots_taken"] = part1.get("screenshots_taken", []) + findings["screenshots_taken"]
            merged_findings["observations"] = part1.get("observations", []) + findings["observations"]
            merged_findings["limitations"] = part1.get("limitations", []) + findings["limitations"]
            merged_findings["api_endpoints_captured"] = sorted(
                set(part1.get("api_endpoints_captured", []) + findings["api_endpoints_captured"])
            )
        except:
            pass

    findings_path = TMP_DIR / "t3-playwright-findings.json"
    with open(findings_path, "w") as f:
        json.dump(merged_findings, f, indent=2, default=str)

    print(f"\n=== SUMMARY ===")
    print(f"  Screenshots: {len(findings['screenshots_taken'])}")
    print(f"  Downloads: {len(findings['files_downloaded'])}")
    print(f"  API endpoints: {len(findings['api_endpoints_captured'])}")
    print(f"  Observations: {len(findings['observations'])}")
    print(f"  Limitations: {len(findings['limitations'])}")
    print(f"  Total merged screenshots: {len(merged_findings['screenshots_taken'])}")
    print(f"  Total merged downloads: {len(merged_findings['files_downloaded'])}")

    browser.close()

print("\n=== DONE ===")
