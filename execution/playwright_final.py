#!/usr/bin/env python3
"""
T3 — Script finale: navigation, accounts detail, cashflow aside.
"""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
REPORTS_DIR = ROOT / "assets" / "reports"
SCREENSHOTS_DIR = ROOT / "assets" / "screenshots" / "fase4"
TMP_DIR = ROOT / ".tmp"

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
        print(f"  [SS] {name}")
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

observations = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    page = context.new_page()
    login(page)

    # ==========================================
    # 1. NAVIGATION STRUCTURE
    # ==========================================
    print("\n=== 1. NAVIGATION ===")
    if safe_goto(page, "https://app.sibill.com/cashflow"):
        time.sleep(3)

        # Get full DOM for analysis of sidebar
        all_links = page.query_selector_all("a[href]")
        nav_links = []
        seen_hrefs = set()
        for link in all_links:
            try:
                href = link.get_attribute("href") or ""
                text = link.inner_text().strip()
                if href and href not in seen_hrefs and (href.startswith('/') or 'sibill' in href):
                    nav_links.append({"text": text[:50], "href": href})
                    seen_hrefs.add(href)
            except: pass

        print(f"  [OK] Found {len(nav_links)} unique links:")
        for item in nav_links:
            print(f"    {item['text']}: {item['href']}")
        observations.append({"type": "navigation", "items": nav_links})

        # Save navigation
        with open(TMP_DIR / "navigation-structure.json", "w") as f:
            json.dump(nav_links, f, indent=2)

    # ==========================================
    # 2. ACCOUNTS DETAIL
    # ==========================================
    print("\n=== 2. ACCOUNTS ===")
    if safe_goto(page, "https://app.sibill.com/accounts"):
        time.sleep(3)

        # Get the page content to understand structure
        content = page.content()

        # Find account-like elements
        # Look for links that might lead to account detail
        account_links = page.query_selector_all('a[href*="account"], a[href*="conto"]')
        for link in account_links[:5]:
            try:
                href = link.get_attribute("href")
                text = link.inner_text().strip()
                print(f"  Account link: '{text}' -> {href}")
                if href:
                    link.click()
                    time.sleep(2)
                    screenshot(page, "account-detail", f"Dettaglio conto: {page.url}")
                    observations.append({"type": "account_detail", "url": page.url})
                    page.go_back()
                    time.sleep(2)
                    break
            except: continue

        # Also try clicking on cards or table rows
        cards = page.query_selector_all('[class*="card" i], [class*="Card"]')
        for card in cards[:3]:
            try:
                if card.is_visible():
                    card.click()
                    time.sleep(2)
                    new_url = page.url
                    if 'accounts' in new_url and new_url != "https://app.sibill.com/accounts":
                        screenshot(page, "account-card-detail", f"Account card detail: {new_url}")
                        observations.append({"type": "account_card_click", "url": new_url})
                        page.go_back()
                        time.sleep(2)
                        break
            except: continue

    # ==========================================
    # 3. CASHFLOW TABLE STRUCTURE
    # ==========================================
    print("\n=== 3. CASHFLOW TABLE ===")
    if safe_goto(page, "https://app.sibill.com/cashflow"):
        time.sleep(4)

        # Analyze the cashflow page more carefully
        # The cashflow might not use standard <table>/<tr> - it could be a custom component

        # Get all elements with data-testid
        test_ids = page.query_selector_all('[data-testid]')
        print(f"  [INFO] Elements with data-testid: {len(test_ids)}")
        for el in test_ids[:15]:
            try:
                tid = el.get_attribute("data-testid")
                tag = el.evaluate("el => el.tagName")
                text = el.inner_text()[:50] if el.inner_text() else ""
                print(f"    {tag} data-testid={tid} text={text}")
            except: pass

        # Get all elements with role attributes
        roles = page.query_selector_all('[role]')
        print(f"\n  [INFO] Elements with role: {len(roles)}")
        for el in roles[:15]:
            try:
                role = el.get_attribute("role")
                tag = el.evaluate("el => el.tagName")
                cls = (el.get_attribute("class") or "")[:40]
                print(f"    {tag} role={role} class={cls}")
            except: pass

        # Try to find clickable amounts — look for spans/divs with currency values
        all_elements = page.query_selector_all('span, div, td, p')
        money_elements = []
        for el in all_elements[:200]:
            try:
                text = el.inner_text().strip()
                # Match patterns like "1.234,56" or "€ 1.234" or "-1.234,56"
                if text and len(text) < 20 and any(c.isdigit() for c in text):
                    if ',' in text or '€' in text or ('.' in text and any(c.isdigit() for c in text)):
                        bbox = el.bounding_box()
                        if bbox and bbox["width"] > 20 and bbox["height"] > 10:
                            money_elements.append({"text": text, "tag": el.evaluate("el => el.tagName"),
                                                  "class": (el.get_attribute("class") or "")[:40]})
            except: pass

        if money_elements:
            print(f"\n  [INFO] Found {len(money_elements)} money-like elements:")
            for me in money_elements[:10]:
                print(f"    {me['tag']} class={me['class']} text={me['text']}")
            observations.append({"type": "cashflow_money_elements", "count": len(money_elements), "samples": money_elements[:10]})

        # Try clicking on a specific amount element
        for el_data in money_elements[:5]:
            try:
                # Re-query for the element
                text = el_data["text"]
                matches = page.query_selector_all(f'text="{text}"')
                for match in matches:
                    try:
                        if match.is_visible():
                            match.click()
                            time.sleep(2)
                            # Check for panel
                            for sel in ['[class*="drawer" i]', '[class*="side" i]', '[role="dialog"]',
                                       '[class*="sheet" i]', '[class*="panel" i]', '[class*="detail" i]']:
                                panel = page.query_selector(sel)
                                if panel and panel.is_visible():
                                    bbox = panel.bounding_box()
                                    if bbox and bbox["width"] > 150:
                                        screenshot(page, "cashflow-money-click-panel", f"Panel after money click: {text}")
                                        print(f"  [FOUND] Panel after clicking '{text}': {sel}")
                                        panel_text = panel.inner_text()[:300]
                                        observations.append({"type": "cashflow_panel", "trigger": text, "content": panel_text})
                                        page.keyboard.press("Escape")
                                        break
                            break
                    except: continue
            except: continue

    # ==========================================
    # 4. FORM FIELDS CAPTURE
    # ==========================================
    print("\n=== 4. PAYMENT FORM FIELDS ===")
    if safe_goto(page, "https://app.sibill.com/transactions/payments"):
        time.sleep(3)

        # Find "Aggiungi" or create button
        for sel in ['button:has-text("Aggiungi")', 'button:has-text("Crea")', 'button:has-text("Nuovo")']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    time.sleep(3)

                    # Check if a modal or new page appeared
                    screenshot(page, "payment-create-step1", "Payment creation step 1")

                    # Get all form elements
                    inputs = page.query_selector_all("input, select, textarea, [role='combobox'], [role='listbox']")
                    form_data = []
                    for inp in inputs:
                        try:
                            info = {
                                "tag": inp.evaluate("el => el.tagName"),
                                "type": inp.get_attribute("type") or "",
                                "name": inp.get_attribute("name") or "",
                                "placeholder": inp.get_attribute("placeholder") or "",
                                "id": inp.get_attribute("id") or "",
                                "aria-label": inp.get_attribute("aria-label") or "",
                                "required": inp.get_attribute("required") is not None,
                                "class": (inp.get_attribute("class") or "")[:50],
                            }
                            form_data.append(info)
                        except: pass

                    print(f"  [OK] Found {len(form_data)} form fields:")
                    for fd in form_data:
                        print(f"    {fd['tag']} type={fd['type']} name={fd['name']} placeholder={fd['placeholder']} id={fd['id']}")

                    observations.append({"type": "payment_form_fields", "fields": form_data})

                    # Look for labels
                    labels = page.query_selector_all("label")
                    label_texts = []
                    for label in labels:
                        try:
                            text = label.inner_text().strip()
                            for_attr = label.get_attribute("for") or ""
                            if text:
                                label_texts.append({"text": text, "for": for_attr})
                        except: pass
                    if label_texts:
                        print(f"  [OK] Labels: {json.dumps(label_texts, indent=2)}")
                        observations.append({"type": "payment_form_labels", "labels": label_texts})

                    page.go_back()
                    time.sleep(2)
                    break
            except: continue

    # ==========================================
    # 5. F24 PAGE DETAIL
    # ==========================================
    print("\n=== 5. F24 DETAIL ===")
    if safe_goto(page, "https://app.sibill.com/f24"):
        time.sleep(3)

        # Get all text content for F24 page
        main_content = page.query_selector('main, [class*="main" i], [class*="content" i], [role="main"]')
        if main_content:
            f24_text = main_content.inner_text()[:2000]
            print(f"  [INFO] F24 page content:\n{f24_text[:500]}")
            observations.append({"type": "f24_page_content", "text": f24_text})

        # Look for FAQ/info sections
        faq = page.query_selector_all('[class*="faq" i], [class*="accordion" i], [class*="collapse" i], details, summary')
        if faq:
            print(f"  [INFO] Found {len(faq)} FAQ/accordion elements")
            for f in faq:
                try:
                    f.click()
                    time.sleep(0.5)
                except: pass
            screenshot(page, "f24-faq-expanded", "F24 FAQ espanse")

    # ==========================================
    # 6. COUNTERPARTS DETAIL
    # ==========================================
    print("\n=== 6. COUNTERPARTS ===")
    if safe_goto(page, "https://app.sibill.com/counterparts"):
        time.sleep(3)

        # Try to find counterpart entries
        rows = page.query_selector_all("tr, [class*='row'], [class*='item']")
        for row in rows[1:5]:
            try:
                if row.is_visible():
                    text = row.inner_text().strip()[:50]
                    row.click()
                    time.sleep(2)
                    new_url = page.url
                    if new_url != "https://app.sibill.com/counterparts":
                        screenshot(page, "counterpart-detail", f"Dettaglio controparte: {new_url}")
                        observations.append({"type": "counterpart_detail", "url": new_url})
                        page.go_back()
                        time.sleep(2)
                        break
            except: continue

    # ==========================================
    # 7. API ENDPOINTS DOCUMENTATION
    # ==========================================
    print("\n=== 7. DOCUMENTING ALL URLs ===")
    # Navigate to all known URLs and document the DOM structure
    test_urls = [
        "/dashboard",
        "/reports",
        "/analytics",
        "/billing",
        "/subscription",
        "/notifications",
        "/help",
        "/support",
        "/profile",
        "/user/settings",
    ]

    found_pages = []
    for path in test_urls:
        try:
            resp = page.goto(f"https://app.sibill.com{path}", wait_until="domcontentloaded", timeout=10000)
            time.sleep(1)
            current = page.url
            status = resp.status if resp else 0
            if status < 400 and 'login' not in current.lower():
                found_pages.append({"path": path, "actual_url": current, "status": status})
                print(f"  [FOUND] {path} -> {current} (status {status})")
                screenshot(page, f"extra-{path.strip('/').replace('/', '-')}", f"Extra page: {path}")
        except:
            continue

    if found_pages:
        observations.append({"type": "extra_pages", "pages": found_pages})

    # ==========================================
    # SAVE ALL
    # ==========================================
    print("\n=== SAVING ===")
    with open(TMP_DIR / "t3-final-observations.json", "w") as f:
        json.dump(observations, f, indent=2, default=str)
    print(f"  Saved {len(observations)} observations")

    # Update merged findings
    findings_path = TMP_DIR / "t3-playwright-findings.json"
    try:
        with open(findings_path) as f:
            merged = json.load(f)
    except:
        merged = {"observations": [], "screenshots_taken": [], "files_downloaded": [], "api_endpoints_captured": [], "limitations": []}

    # Add new observations
    for obs in observations:
        merged["observations"].append(json.dumps(obs)[:500])

    # Count all screenshots and reports
    import os
    ss_count = len(os.listdir(SCREENSHOTS_DIR))
    reports = os.listdir(REPORTS_DIR)
    merged["total_screenshots"] = ss_count
    merged["total_reports"] = [f for f in reports if not f.startswith('.')]

    with open(findings_path, "w") as f:
        json.dump(merged, f, indent=2, default=str)

    print(f"\n  Total screenshots: {ss_count}")
    print(f"  Total reports: {reports}")

    browser.close()

print("\n=== DONE ===")
