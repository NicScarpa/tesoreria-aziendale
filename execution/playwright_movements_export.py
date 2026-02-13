#!/usr/bin/env python3
"""
T3 — Download specifico dei movimenti e prima nota + cashflow aside panel.
"""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
REPORTS_DIR = ROOT / "assets" / "reports"
SCREENSHOTS_DIR = ROOT / "assets" / "screenshots" / "fase4"

creds = {}
with open(ROOT / "credenziali.env") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('http'): continue
        if ':' in line:
            k, v = line.split(':', 1)
            creds[k.strip().lower()] = v.strip()

email = creds.get('user', '')
password = creds.get('password', '')

def screenshot(page, name, desc=""):
    path = SCREENSHOTS_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        print(f"  [SS] {name}: {desc}")
    except: pass

def safe_goto(page, url):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        try: page.wait_for_load_state("networkidle", timeout=8000)
        except: pass
        return True
    except: return False

def login(page):
    safe_goto(page, "https://app.sibill.com/")
    time.sleep(2)
    try:
        page.query_selector('input[type="text"]').fill(email)
        page.query_selector('input[type="password"]').fill(password)
        page.query_selector('button[type="submit"]').click()
    except: pass
    time.sleep(5)
    try: page.wait_for_load_state("networkidle", timeout=10000)
    except: pass
    if 'login' in page.url.lower():
        page.keyboard.press("Enter")
        time.sleep(5)
    print(f"  [LOGIN] {page.url}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    page = context.new_page()
    login(page)

    # ==========================================
    # 1. MOVIMENTI EXPORT — Scarica movimenti
    # ==========================================
    print("\n=== 1. SCARICA MOVIMENTI ===")
    if safe_goto(page, "https://app.sibill.com/transactions/movements"):
        time.sleep(3)

        # Click "Scarica" button
        btn = page.query_selector('button:has-text("Scarica")')
        if btn and btn.is_visible():
            btn.click()
            time.sleep(2)

            # Find the dialog
            dialog = page.query_selector('[role="dialog"]')
            if dialog:
                screenshot(page, "movements-dialog", "Dialog scarica movimenti/prima nota")

                # Get all clickable items in dialog
                items = dialog.query_selector_all('button, a, [role="button"], div[class*="item"], div[class*="option"]')
                print(f"  [INFO] Dialog items: {len(items)}")

                for item in items:
                    try:
                        txt = item.inner_text().strip()
                        print(f"    Item: '{txt}'")
                    except: pass

                # Click "Scarica movimenti"
                for sel in ['text="Scarica movimenti"', 'button:has-text("Scarica movimenti")',
                           'div:has-text("Scarica movimenti")']:
                    try:
                        el = dialog.query_selector(sel)
                        if not el:
                            el = page.query_selector(sel)
                        if el and el.is_visible():
                            print(f"  [OK] Clicking 'Scarica movimenti'")
                            try:
                                with page.expect_download(timeout=15000) as dl:
                                    el.click()
                                    time.sleep(3)
                                download = dl.value
                                fname = download.suggested_filename or "movimenti.xlsx"
                                path = REPORTS_DIR / f"movimenti-export.xlsx"
                                download.save_as(str(path))
                                print(f"  [DOWNLOAD] movimenti-export.xlsx ({path.stat().st_size} bytes)")
                            except Exception as e:
                                print(f"  [WARNING] Download movimenti: {e}")
                                screenshot(page, "movements-download-attempt", "Tentativo download movimenti")
                            break
                    except: continue

        # Wait and close any modal
        time.sleep(2)
        page.keyboard.press("Escape")
        time.sleep(1)

    # ==========================================
    # 2. MOVIMENTI EXPORT — Scarica prima nota
    # ==========================================
    print("\n=== 2. SCARICA PRIMA NOTA ===")
    if safe_goto(page, "https://app.sibill.com/transactions/movements"):
        time.sleep(3)

        btn = page.query_selector('button:has-text("Scarica")')
        if btn and btn.is_visible():
            btn.click()
            time.sleep(2)

            dialog = page.query_selector('[role="dialog"]')
            if dialog:
                # Click "Scarica prima nota"
                for sel in ['text="Scarica prima nota"', 'button:has-text("prima nota")',
                           'div:has-text("prima nota")']:
                    try:
                        el = dialog.query_selector(sel)
                        if not el:
                            el = page.query_selector(sel)
                        if el and el.is_visible():
                            print(f"  [OK] Clicking 'Scarica prima nota'")
                            try:
                                with page.expect_download(timeout=15000) as dl:
                                    el.click()
                                    time.sleep(3)
                                download = dl.value
                                fname = download.suggested_filename or "prima-nota.xlsx"
                                path = REPORTS_DIR / f"prima-nota-export.xlsx"
                                download.save_as(str(path))
                                print(f"  [DOWNLOAD] prima-nota-export.xlsx ({path.stat().st_size} bytes)")
                            except Exception as e:
                                print(f"  [WARNING] Download prima nota: {e}")
                                screenshot(page, "prima-nota-download-attempt", "Tentativo download prima nota")
                            break
                    except: continue

        time.sleep(2)
        page.keyboard.press("Escape")
        time.sleep(1)

    # ==========================================
    # 3. CASHFLOW — Click su righe tabella
    # ==========================================
    print("\n=== 3. CASHFLOW ASIDE PANEL ===")
    if safe_goto(page, "https://app.sibill.com/cashflow"):
        time.sleep(4)

        # Debug: get all interactive elements
        page_html = page.content()

        # Find table rows
        all_trs = page.query_selector_all("tr")
        print(f"  [INFO] Total <tr> elements: {len(all_trs)}")

        for i, tr in enumerate(all_trs):
            try:
                text = tr.inner_text().strip()[:80]
                cls = tr.get_attribute("class") or ""
                print(f"    tr[{i}]: class={cls[:40]} text={text[:40]}")
            except: pass
            if i > 15: break

        # Try clicking on different row elements
        for i, tr in enumerate(all_trs[1:8]):  # Skip header
            try:
                tds = tr.query_selector_all("td")
                if len(tds) >= 2:
                    # Click on the first td (usually the category name)
                    tds[0].click()
                    time.sleep(2)

                    # Check for any panel/drawer
                    found = False
                    for sel in ['[class*="side"]', '[class*="Side"]', '[class*="drawer"]',
                               '[class*="Drawer"]', '[class*="panel"]', '[class*="Panel"]',
                               '[class*="detail"]', '[class*="Detail"]', '[role="dialog"]',
                               '[class*="Sheet"]', '[class*="modal"]']:
                        panel = page.query_selector(sel)
                        if panel and panel.is_visible():
                            bbox = panel.bounding_box()
                            if bbox and bbox["width"] > 200:
                                screenshot(page, f"cashflow-panel-{i}", f"Panel cashflow row {i}")
                                content = panel.inner_text()[:300]
                                print(f"  [FOUND] Panel via {sel}: {content[:100]}")
                                found = True
                                break

                    if found:
                        page.keyboard.press("Escape")
                        break

                    # Try clicking a monetary value cell
                    for td in tds[1:]:
                        try:
                            td_text = td.inner_text().strip()
                            if any(c.isdigit() for c in td_text):
                                td.click()
                                time.sleep(2)
                                for sel in ['[class*="side"]', '[class*="drawer"]', '[role="dialog"]',
                                           '[class*="Sheet"]', '[class*="panel"]']:
                                    panel = page.query_selector(sel)
                                    if panel and panel.is_visible():
                                        bbox = panel.bounding_box()
                                        if bbox and bbox["width"] > 200:
                                            screenshot(page, f"cashflow-amount-panel-{i}", f"Panel da cella importo row {i}")
                                            print(f"  [FOUND] Amount panel: {sel}")
                                            found = True
                                            break
                                if found: break
                        except: continue

                    if found:
                        page.keyboard.press("Escape")
                        break

                    page.keyboard.press("Escape")
                    time.sleep(0.5)
            except Exception as e:
                continue

        if not found:
            print("  [INFO] No aside panel found on cashflow - may require specific interaction")
            # Try clicking directly on category text links
            links = page.query_selector_all('a, [role="link"], [class*="link"]')
            for link in links[:10]:
                try:
                    text = link.inner_text().strip()
                    href = link.get_attribute("href") or ""
                    if text and 'cashflow' in href:
                        print(f"  [INFO] Found link in cashflow: '{text}' -> {href}")
                except: pass

    # ==========================================
    # 4. CONTI BANCARI DETTAGLIO
    # ==========================================
    print("\n=== 4. CONTI BANCARI ===")
    if safe_goto(page, "https://app.sibill.com/accounts"):
        time.sleep(3)
        screenshot(page, "accounts-detail", "Dettaglio conti bancari")

        # Click on first account to see details
        rows = page.query_selector_all("tr, [class*='row'], [class*='card']")
        for row in rows[1:5]:
            try:
                if row.is_visible():
                    row.click()
                    time.sleep(2)
                    new_url = page.url
                    if new_url != "https://app.sibill.com/accounts":
                        screenshot(page, "account-single-detail", f"Dettaglio singolo conto: {new_url}")
                        print(f"  [OK] Account detail: {new_url}")
                        page.go_back()
                        time.sleep(2)
                        break
            except: continue

    # ==========================================
    # 5. NAVIGAZIONE COMPLETA
    # ==========================================
    print("\n=== 5. NAVIGAZIONE SIDEBAR ===")
    if safe_goto(page, "https://app.sibill.com/cashflow"):
        time.sleep(3)

        # Try to find sidebar navigation
        nav = page.query_selector('nav, aside, [class*="sidebar" i], [class*="Sidebar"]')
        if nav:
            links = nav.query_selector_all("a")
            nav_structure = []
            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    text = link.inner_text().strip()
                    if text:
                        nav_structure.append({"text": text, "href": href})
                except: pass
            print(f"  [OK] Found {len(nav_structure)} nav items:")
            for item in nav_structure:
                print(f"    - {item['text']}: {item['href']}")

            # Save nav structure
            nav_path = ROOT / ".tmp" / "navigation-structure.json"
            with open(nav_path, "w") as f:
                json.dump(nav_structure, f, indent=2)
            print(f"  [SAVED] {nav_path}")
        else:
            # Try getting all links on the page
            all_links = page.query_selector_all("a[href]")
            sibill_links = []
            for link in all_links:
                try:
                    href = link.get_attribute("href") or ""
                    text = link.inner_text().strip()
                    if 'sibill' in href or href.startswith('/'):
                        sibill_links.append({"text": text, "href": href})
                except: pass
            if sibill_links:
                print(f"  [OK] Found {len(sibill_links)} Sibill links:")
                for item in sibill_links[:20]:
                    print(f"    - {item['text']}: {item['href']}")
                nav_path = ROOT / ".tmp" / "navigation-structure.json"
                with open(nav_path, "w") as f:
                    json.dump(sibill_links, f, indent=2)

    browser.close()

print("\n=== DONE ===")
