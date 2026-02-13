#!/usr/bin/env python3
"""
Capture transaction detail API responses by clicking on each row.

This script:
1. Logs into Sibill
2. Navigates to /transactions/movements (and optionally /outstanding)
3. Clicks on EVERY visible transaction row to trigger detail API calls
4. Paginates through all pages
5. Saves all captured API responses

Usage: python3 execution/capture_transaction_details.py
"""

import json
import os
import sys
import time
import hashlib
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

BASE_URL = "https://app.sibill.com"
PROJECT_ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
CRED_FILE = PROJECT_ROOT / "credenziali.env"
CAPTURE_DIR = PROJECT_ROOT / ".tmp" / "capture" / "transaction-details"
API_RESPONSES_DIR = PROJECT_ROOT / "sibill-offline" / "api-responses"

# Pages to capture row details from
PAGES_TO_CAPTURE = [
    "/transactions/movements",
    "/outstanding",
]

MAX_PAGES = 10  # max pagination pages per section


def load_credentials():
    creds = {}
    with open(CRED_FILE) as f:
        for line in f:
            line = line.strip()
            if ":" in line and not line.startswith("http"):
                key, val = line.split(":", 1)
                creds[key.strip()] = val.strip()
    return creds


def normalize_url(url):
    """Normalize URL for consistent hashing (same as build_offline.py)."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    sorted_params = sorted(params.items())
    # Rebuild query string with sorted params
    parts = []
    for key, values in sorted_params:
        for val in sorted(values):
            parts.append(f"{key}={val}")
    normalized_query = "&".join(parts)
    return f"{parsed.path}?{normalized_query}" if normalized_query else parsed.path


def url_to_hash(url):
    """Convert URL to MD5 hash filename (same as build_offline.py)."""
    normalized = normalize_url(url)
    return hashlib.md5(normalized.encode()).hexdigest()


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def main():
    from playwright.sync_api import sync_playwright

    creds = load_credentials()
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    (CAPTURE_DIR / "screenshots").mkdir(exist_ok=True)

    captured_details = []  # list of {url, path, response, hash}
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        page = context.new_page()

        # --- Intercept API responses ---
        def handle_response(response):
            try:
                url = response.request.url
                parsed = urlparse(url)

                # Only capture transaction detail API calls
                # Pattern: /api/v1/transactions/{uuid}
                # Also capture: /api/v1/outstanding/{uuid}, /api/v1/receivables/{uuid}
                detail_patterns = [
                    "/api/v1/transactions/",
                    "/api/v1/outstanding/",
                    "/api/v1/receivables/",
                    "/api/v1/payables/",
                ]

                is_detail = False
                for pattern in detail_patterns:
                    if parsed.path.startswith(pattern):
                        # Check it's a UUID path (detail, not list)
                        remaining = parsed.path[len(pattern):]
                        if remaining and "/" not in remaining.rstrip("/") and len(remaining) > 10:
                            is_detail = True
                            break

                if not is_detail:
                    return

                content_type = response.headers.get("content-type", "")
                if "json" not in content_type:
                    return

                if url in seen_urls:
                    return
                seen_urls.add(url)

                try:
                    body = response.json()
                except Exception:
                    return

                if response.status != 200:
                    log(f"  [SKIP] {parsed.path} — status {response.status}")
                    return

                url_hash = url_to_hash(url)
                captured_details.append({
                    "url": url,
                    "path": parsed.path,
                    "hash": url_hash,
                    "response": body,
                    "status": response.status,
                })
                log(f"  [OK] {parsed.path[:80]}... → {url_hash}.json")

            except Exception as e:
                pass

        page.on("response", handle_response)

        # --- Login ---
        log("=== LOGIN ===")
        page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=30000)
        time.sleep(3)

        # Debug screenshot
        page.screenshot(path=str(CAPTURE_DIR / "screenshots" / "00-login.png"))

        # Try multiple selectors for email/password fields
        email_selectors = [
            'input[type="email"]', 'input[name="email"]', 'input[name="username"]',
            '#email', '#username', 'input[autocomplete="email"]',
            'input[placeholder*="mail"]', 'input[placeholder*="Mail"]',
        ]
        password_selectors = [
            'input[type="password"]', 'input[name="password"]', '#password',
        ]

        email_input = None
        for sel in email_selectors:
            el = page.query_selector(sel)
            if el:
                email_input = el
                log(f"  Email input trovato: {sel}")
                break

        password_input = None
        for sel in password_selectors:
            el = page.query_selector(sel)
            if el:
                password_input = el
                log(f"  Password input trovato: {sel}")
                break

        # Fallback: try to find inputs by position (first two visible inputs)
        if not email_input or not password_input:
            all_inputs = page.query_selector_all("input:visible")
            log(f"  Fallback: trovati {len(all_inputs)} input visibili")
            for inp in all_inputs:
                inp_type = inp.get_attribute("type") or ""
                log(f"    input type={inp_type}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}")
            if len(all_inputs) >= 2 and not email_input:
                email_input = all_inputs[0]
                log(f"  Usando primo input come email")
            if len(all_inputs) >= 2 and not password_input:
                password_input = all_inputs[1]
                log(f"  Usando secondo input come password")

        if email_input and password_input:
            email_input.fill(creds.get("user", ""))
            password_input.fill(creds.get("password", ""))
            time.sleep(0.5)

            # Find submit button
            submit_selectors = [
                'button[type="submit"]', 'button:has-text("Accedi")',
                'button:has-text("Login")', 'button:has-text("Sign in")',
                'input[type="submit"]',
            ]
            for sel in submit_selectors:
                btn = page.query_selector(sel)
                if btn:
                    log(f"  Submit button trovato: {sel}")
                    btn.click()
                    break

            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(3)
            log("Login completato")
        else:
            log(f"[ERROR] Form login non trovato! email={email_input is not None}, password={password_input is not None}")
            page.screenshot(path=str(CAPTURE_DIR / "screenshots" / "00-login-error.png"))
            browser.close()
            return

        page.screenshot(path=str(CAPTURE_DIR / "screenshots" / "01-after-login.png"))

        # --- Capture transaction details for each page ---
        for page_path in PAGES_TO_CAPTURE:
            log(f"\n=== SEZIONE: {page_path} ===")

            page.goto(f"{BASE_URL}{page_path}", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            page_label = page_path.replace("/", "_").strip("_")
            page.screenshot(path=str(CAPTURE_DIR / "screenshots" / f"02-{page_label}-initial.png"))

            total_rows_clicked = 0
            current_page_num = 1

            while current_page_num <= MAX_PAGES:
                log(f"\n  --- Pagina {current_page_num} ---")

                # Wait for table to load
                time.sleep(2)

                # Find all clickable rows
                rows = page.query_selector_all("tbody tr")
                if not rows:
                    # Try alternative selectors
                    rows = page.query_selector_all('[role="row"]')
                    # Filter out header rows
                    rows = [r for r in rows if r.query_selector("td")]

                if not rows:
                    log(f"  Nessuna riga trovata")
                    break

                log(f"  Trovate {len(rows)} righe")

                # Click each row
                for i, row in enumerate(rows):
                    try:
                        if not row.is_visible():
                            continue

                        # Get some info about the row for logging
                        row_text = ""
                        try:
                            cells = row.query_selector_all("td")
                            if cells and len(cells) > 1:
                                row_text = cells[1].inner_text().strip()[:40]
                        except Exception:
                            pass

                        before_count = len(captured_details)

                        row.click()
                        time.sleep(1.5)

                        # Wait for network to settle (detail API call)
                        try:
                            page.wait_for_load_state("networkidle", timeout=5000)
                        except Exception:
                            pass

                        after_count = len(captured_details)
                        new_captures = after_count - before_count

                        if new_captures > 0:
                            log(f"    Riga {i+1}/{len(rows)}: '{row_text}' — {new_captures} API catturate")
                        else:
                            log(f"    Riga {i+1}/{len(rows)}: '{row_text}' — (gia' in cache o nessuna API)")

                        total_rows_clicked += 1

                        # Take screenshot of first detail panel
                        if i == 0 and current_page_num == 1:
                            page.screenshot(
                                path=str(CAPTURE_DIR / "screenshots" / f"03-{page_label}-detail-panel.png")
                            )

                        # Close detail panel (press Escape or click close button)
                        close_btn = page.query_selector('[aria-label="Close"], [class*="close"]:visible, button:has-text("×")')
                        if close_btn:
                            try:
                                close_btn.click()
                                time.sleep(0.5)
                            except Exception:
                                page.keyboard.press("Escape")
                                time.sleep(0.5)
                        else:
                            page.keyboard.press("Escape")
                            time.sleep(0.5)

                    except Exception as e:
                        log(f"    Riga {i+1}: errore — {e}")

                # Try to go to next page
                next_btn = None
                pagination_selectors = [
                    'button[aria-label*="next"]',
                    'button[aria-label*="Next"]',
                    '[class*="pagination"] button:last-child',
                    '[class*="Pagination"] button:last-child',
                    'button:has-text(">")',
                ]
                for sel in pagination_selectors:
                    try:
                        btns = page.query_selector_all(sel)
                        for btn in btns:
                            if btn.is_visible() and btn.is_enabled():
                                next_btn = btn
                                break
                        if next_btn:
                            break
                    except Exception:
                        continue

                if next_btn:
                    try:
                        next_btn.click()
                        time.sleep(2)
                        page.wait_for_load_state("networkidle", timeout=10000)
                        current_page_num += 1
                        log(f"  Navigato a pagina {current_page_num}")
                    except Exception as e:
                        log(f"  Paginazione fallita: {e}")
                        break
                else:
                    log(f"  Nessun pulsante 'avanti' trovato — fine paginazione")
                    break

            log(f"\n  Totale righe cliccate in {page_path}: {total_rows_clicked}")
            page.screenshot(path=str(CAPTURE_DIR / "screenshots" / f"04-{page_label}-final.png"))

        context.close()
        browser.close()

    # --- Save captured detail responses ---
    log(f"\n=== SALVATAGGIO ===")
    log(f"Dettagli catturati: {len(captured_details)}")

    # Save to api-responses directory
    API_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0
    for detail in captured_details:
        out_file = API_RESPONSES_DIR / f"{detail['hash']}.json"
        with open(out_file, "w") as f:
            json.dump(detail["response"], f, ensure_ascii=False)
        saved += 1

    log(f"Salvati: {saved} file in {API_RESPONSES_DIR}")

    # Save index for reference
    index = []
    for d in captured_details:
        index.append({
            "url": d["url"],
            "path": d["path"],
            "hash": d["hash"],
            "status": d["status"],
        })

    index_path = CAPTURE_DIR / "captured-details-index.json"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    log(f"Indice salvato: {index_path}")

    # Now update the SW API_MAP with the new entries
    log(f"\n=== AGGIORNAMENTO SW ===")
    log(f"Devo aggiungere {len(captured_details)} entry alla API_MAP nel Service Worker")
    log(f"Esegui: python3 execution/build_offline.py per rigenerare sw.js")

    # Save URL-to-hash mapping for build_offline.py integration
    url_map = {}
    for d in captured_details:
        normalized = normalize_url(d["url"])
        url_map[normalized] = d["hash"]

    url_map_path = CAPTURE_DIR / "url-hash-map.json"
    with open(url_map_path, "w") as f:
        json.dump(url_map, f, indent=2, ensure_ascii=False)
    log(f"URL map salvata: {url_map_path}")

    log(f"\n=== RIEPILOGO ===")
    log(f"Dettagli transazione catturati: {len(captured_details)}")
    log(f"File API response salvati: {saved}")
    log(f"Prossimo step: rigenerare sw.js con build_offline.py")


if __name__ == "__main__":
    main()
