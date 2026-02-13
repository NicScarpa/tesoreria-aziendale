#!/usr/bin/env python3
"""
T3 — Script mirato per export specifici:
1. Fatture emesse (documenti-emesse.xlsx) - rinomina per distinguere
2. Export movimenti (investigare il modal/flow)
3. Verifica e rinomina fatture ricevute
"""
import json, time
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
REPORTS_DIR = ROOT / "assets" / "reports"
SCREENSHOTS_DIR = ROOT / "assets" / "screenshots" / "fase4"
TMP_DIR = ROOT / ".tmp"

# Credentials
creds = {}
with open(ROOT / "credenziali.env") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('http'):
            continue
        if ':' in line:
            k, v = line.split(':', 1)
            creds[k.strip().lower()] = v.strip()

email = creds.get('user', '')
password = creds.get('password', '')

results = {"downloads": [], "observations": []}

def screenshot(page, name, desc=""):
    path = SCREENSHOTS_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        print(f"  [SCREENSHOT] {name}: {desc}")
    except:
        pass

def safe_goto(page, url):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except:
            pass
        return True
    except:
        return False

def login(page):
    safe_goto(page, "https://app.sibill.com/")
    time.sleep(2)
    for sel in ['input[type="email"]', 'input[type="text"]']:
        try:
            el = page.query_selector(sel)
            if el: el.fill(email); break
        except: continue
    for sel in ['input[type="password"]']:
        try:
            el = page.query_selector(sel)
            if el: el.fill(password); break
        except: continue
    page.query_selector('button[type="submit"]').click()
    time.sleep(5)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass
    if 'login' in page.url.lower():
        page.keyboard.press("Enter")
        time.sleep(5)
    print(f"  [LOGIN] URL: {page.url}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    page = context.new_page()

    login(page)

    # ==========================================
    # 1. FATTURE EMESSE EXPORT
    # ==========================================
    print("\n=== 1. EXPORT FATTURE EMESSE ===")
    if safe_goto(page, "https://app.sibill.com/invoices/issued"):
        time.sleep(3)
        for sel in ['button:has-text("Scarica")', 'button:has-text("Esporta")', 'button:has-text("Export")']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    with page.expect_download(timeout=15000) as dl:
                        el.click()
                        time.sleep(3)
                    download = dl.value
                    path = REPORTS_DIR / "documenti-emesse.xlsx"
                    download.save_as(str(path))
                    results["downloads"].append(f"documenti-emesse.xlsx ({path.stat().st_size} bytes)")
                    print(f"  [OK] Downloaded documenti-emesse.xlsx")
                    break
            except Exception as e:
                print(f"  [WARNING] {sel}: {e}")

    # ==========================================
    # 2. FATTURE RICEVUTE EXPORT
    # ==========================================
    print("\n=== 2. EXPORT FATTURE RICEVUTE ===")
    if safe_goto(page, "https://app.sibill.com/invoices/received"):
        time.sleep(3)
        for sel in ['button:has-text("Scarica")', 'button:has-text("Esporta")', 'button:has-text("Export")']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    with page.expect_download(timeout=15000) as dl:
                        el.click()
                        time.sleep(3)
                    download = dl.value
                    path = REPORTS_DIR / "documenti-ricevute.xlsx"
                    download.save_as(str(path))
                    results["downloads"].append(f"documenti-ricevute.xlsx ({path.stat().st_size} bytes)")
                    print(f"  [OK] Downloaded documenti-ricevute.xlsx")
                    break
            except Exception as e:
                print(f"  [WARNING] {sel}: {e}")

    # ==========================================
    # 3. EXPORT MOVIMENTI - INVESTIGAZIONE
    # ==========================================
    print("\n=== 3. EXPORT MOVIMENTI (INVESTIGAZIONE) ===")
    if safe_goto(page, "https://app.sibill.com/transactions/movements"):
        time.sleep(3)

        # List ALL buttons on page
        buttons = page.query_selector_all("button")
        print("  [INFO] Buttons on movements page:")
        for btn in buttons:
            try:
                text = btn.inner_text().strip()
                visible = btn.is_visible()
                aria = btn.get_attribute("aria-label") or ""
                cls = btn.get_attribute("class") or ""
                if text or aria:
                    print(f"    - '{text}' | aria='{aria}' | visible={visible} | class={cls[:50]}")
            except:
                continue

        # Try clicking "Scarica" - it might open a modal/dropdown
        for sel in ['button:has-text("Scarica")', 'button:has-text("Esporta")']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    print(f"\n  [INFO] Clicking '{sel}'...")
                    el.click()
                    time.sleep(3)

                    # Check what appeared
                    screenshot(page, "movements-export-investigation", "Dopo click Scarica su movimenti")

                    # Look for any modal/dropdown/dialog
                    for container_sel in ['[role="dialog"]', '[class*="modal"]', '[class*="dropdown"]',
                                         '[class*="popover"]', '[class*="menu"]', '[class*="Menu"]',
                                         '[class*="Popover"]', '[class*="Dialog"]']:
                        container = page.query_selector(container_sel)
                        if container and container.is_visible():
                            print(f"  [OK] Found overlay: {container_sel}")
                            # Get content
                            content = container.inner_text()
                            print(f"  [CONTENT] {content[:300]}")
                            results["observations"].append(f"Movements export overlay ({container_sel}): {content[:500]}")

                            # Look for download links or buttons inside
                            inner_btns = container.query_selector_all("button, a")
                            for ib in inner_btns:
                                try:
                                    ib_text = ib.inner_text().strip()
                                    if ib_text:
                                        print(f"    Inner button: '{ib_text}'")
                                        # Try clicking if it says download/export
                                        if any(kw in ib_text.lower() for kw in ["scarica", "download", "esporta", "excel", "csv", "conferma"]):
                                            try:
                                                with page.expect_download(timeout=10000) as dl:
                                                    ib.click()
                                                    time.sleep(3)
                                                download = dl.value
                                                fname = download.suggested_filename or "movimenti-export.xlsx"
                                                path = REPORTS_DIR / fname
                                                download.save_as(str(path))
                                                results["downloads"].append(f"{fname} ({path.stat().st_size} bytes)")
                                                print(f"  [OK] Downloaded {fname}")
                                            except Exception as e:
                                                print(f"    Download attempt: {e}")
                                except:
                                    continue
                            break

                    # Check for a toast/notification
                    time.sleep(2)
                    for toast_sel in ['[class*="toast"]', '[class*="notification"]', '[class*="alert"]',
                                     '[class*="snack"]', '[class*="Toast"]', '[class*="Snack"]']:
                        toast = page.query_selector(toast_sel)
                        if toast and toast.is_visible():
                            toast_text = toast.inner_text().strip()
                            print(f"  [TOAST] {toast_text}")
                            results["observations"].append(f"Movements export toast: {toast_text}")
                            screenshot(page, "movements-export-toast", f"Toast: {toast_text[:50]}")

                    page.keyboard.press("Escape")
                    time.sleep(1)
                    break
            except Exception as e:
                print(f"  [ERROR] {sel}: {e}")

    # ==========================================
    # 4. CASHFLOW ASIDE PANEL - RETRY
    # ==========================================
    print("\n=== 4. CASHFLOW ASIDE PANEL ===")
    if safe_goto(page, "https://app.sibill.com/cashflow"):
        time.sleep(4)

        # Get page structure for debugging
        page_html = page.content()

        # Look for clickable rows in cashflow table
        # Try different selectors
        for row_sel in ['tr[class*="row"]', 'tr', 'div[class*="row"]', '[role="row"]']:
            rows = page.query_selector_all(row_sel)
            if len(rows) > 1:
                print(f"  [INFO] Found {len(rows)} rows with '{row_sel}'")
                for i, row in enumerate(rows[1:6]):  # Skip header, try first 5
                    try:
                        if row.is_visible():
                            # Double-click might open panel
                            row.dblclick()
                            time.sleep(2)

                            # Check for panel
                            panel_found = False
                            for panel_sel in ['[class*="aside"]', '[class*="drawer"]', '[class*="panel"]',
                                            '[class*="sidebar"]', '[role="dialog"]', '[class*="Drawer"]',
                                            '[class*="Sheet"]', '[class*="detail"]']:
                                panel = page.query_selector(panel_sel)
                                if panel and panel.is_visible():
                                    screenshot(page, f"cashflow-aside-{i}", f"Aside panel cashflow (row {i})")
                                    content = panel.inner_text()[:500]
                                    results["observations"].append(f"Cashflow aside panel: {content}")
                                    print(f"  [OK] Found panel: {panel_sel}")
                                    panel_found = True
                                    break

                            if panel_found:
                                page.keyboard.press("Escape")
                                break

                            # Try single click
                            row.click()
                            time.sleep(2)
                            for panel_sel in ['[class*="aside"]', '[class*="drawer"]',
                                            '[role="dialog"]', '[class*="Sheet"]']:
                                panel = page.query_selector(panel_sel)
                                if panel and panel.is_visible():
                                    screenshot(page, f"cashflow-aside-click-{i}", f"Aside panel via click (row {i})")
                                    panel_found = True
                                    break

                            if panel_found:
                                page.keyboard.press("Escape")
                                break

                            page.keyboard.press("Escape")
                            time.sleep(0.5)
                    except:
                        continue
                if panel_found:
                    break

    # ==========================================
    # 5. NAVIGATION MENU CAPTURE
    # ==========================================
    print("\n=== 5. NAVIGATION MENU ===")
    if safe_goto(page, "https://app.sibill.com/cashflow"):
        time.sleep(3)

        # Capture the sidebar/navigation
        nav_selectors = ['nav', '[class*="sidebar"]', '[class*="Sidebar"]', '[class*="navigation"]',
                        '[class*="menu"]', 'aside']
        for sel in nav_selectors:
            nav = page.query_selector(sel)
            if nav and nav.is_visible():
                # Get all links in nav
                links = nav.query_selector_all("a")
                nav_items = []
                for link in links:
                    try:
                        href = link.get_attribute("href") or ""
                        text = link.inner_text().strip()
                        if text:
                            nav_items.append({"text": text, "href": href})
                    except:
                        continue
                if nav_items:
                    results["observations"].append(f"Navigation items: {json.dumps(nav_items, indent=2)}")
                    print(f"  [OK] Found {len(nav_items)} navigation items")
                    for item in nav_items:
                        print(f"    - {item['text']}: {item['href']}")
                break

    # ==========================================
    # SAVE RESULTS
    # ==========================================
    print("\n=== RESULTS ===")
    results_path = TMP_DIR / "t3-targeted-exports.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"  Downloads: {results['downloads']}")
    print(f"  Observations: {len(results['observations'])}")

    browser.close()

print("\n=== DONE ===")
