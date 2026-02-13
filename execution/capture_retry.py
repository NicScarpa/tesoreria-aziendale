#!/usr/bin/env python3
"""
Retry capture for pages that timed out with networkidle.
Uses domcontentloaded + manual wait instead.
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

BASE_URL = "https://app.sibill.com"
PROJECT_ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
CRED_FILE = PROJECT_ROOT / "credenziali.env"
CAPTURE_DIR = PROJECT_ROOT / ".tmp" / "capture"

def load_credentials():
    creds = {}
    with open(CRED_FILE) as f:
        for line in f:
            line = line.strip()
            if ":" in line and not line.startswith("http"):
                key, val = line.split(":", 1)
                creds[key.strip()] = val.strip()
    return creds

def capture_with_retry(section_name, page_paths):
    from playwright.sync_api import sync_playwright

    creds = load_credentials()
    out_dir = CAPTURE_DIR / section_name
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "screenshots").mkdir(exist_ok=True)

    captured_requests = []
    all_asset_urls = set()
    log_lines = []

    def log(msg):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        log_lines.append(entry)
        print(entry)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        page = context.new_page()

        def handle_response(response):
            try:
                url = response.request.url
                parsed = urlparse(url)
                content_type = response.headers.get("content-type", "")

                skip_domains = ('google', 'facebook', 'analytics', 'hotjar', 'sentry', 'segment', 'intercom', 'crisp', 'mixpanel')
                if any(d in parsed.netloc for d in skip_domains):
                    return

                if any(ext in parsed.path for ext in ('.png', '.jpg', '.svg', '.ico', '.woff', '.gif')):
                    all_asset_urls.add(url)
                    return
                if "javascript" in content_type or "css" in content_type or "font" in content_type:
                    all_asset_urls.add(url)
                if "image" in content_type:
                    all_asset_urls.add(url)

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
                        post_data = response.request.post_data
                        if post_data:
                            try:
                                post_data = json.loads(post_data)
                            except (json.JSONDecodeError, TypeError):
                                pass
                    except Exception:
                        pass

                    captured_requests.append({
                        "url": url,
                        "path": parsed.path,
                        "query": parse_qs(parsed.query),
                        "method": response.request.method,
                        "requestBody": post_data,
                        "responseBody": body,
                        "statusCode": response.status,
                        "contentType": content_type,
                        "trigger": "page_interaction",
                        "page": "pending",
                        "timestamp": datetime.now().isoformat(),
                    })
            except Exception as e:
                log(f"  [WARN] Error: {e}")

        page.on("response", handle_response)

        # Login
        log("=== LOGIN ===")
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)

        for sel in ['input[type="email"]', 'input[name="email"]', '#email']:
            el = page.query_selector(sel)
            if el:
                el.fill(creds.get("user", ""))
                break
        for sel in ['input[type="password"]', 'input[name="password"]', '#password']:
            el = page.query_selector(sel)
            if el:
                el.fill(creds.get("password", ""))
                break

        for sel in ['button[type="submit"]', 'button:has-text("Accedi")', 'button:has-text("Login")']:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                break

        time.sleep(5)
        log(f"Login OK — URL: {page.url}")

        # Navigate to each page with relaxed timeout
        for page_idx, page_path in enumerate(page_paths, start=1):
            page_url = f"{BASE_URL}{page_path}"
            page_label = page_path.replace("/", "_").strip("_")
            log(f"\n=== PAGINA {page_idx}/{len(page_paths)}: {page_path} ===")

            capture_start = len(captured_requests)

            try:
                # Use domcontentloaded instead of networkidle, longer timeout
                page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
                log("  domcontentloaded raggiunto, attendo 8s per API...")
                time.sleep(8)  # Wait for API calls to complete
                log(f"  Navigato a {page_url}")
            except Exception as e:
                log(f"  [ERROR] Navigazione fallita anche con domcontentloaded: {e}")
                # Try one more time with just commit
                try:
                    page.goto(page_url, wait_until="commit", timeout=60000)
                    time.sleep(10)
                    log(f"  Retry con commit riuscito")
                except Exception as e2:
                    log(f"  [ERROR] Anche commit fallito: {e2}")
                    continue

            page.screenshot(path=str(out_dir / "screenshots" / f"retry-{page_idx:02d}-{page_label}.png"), full_page=True)

            # Try interactions
            # Tabs
            tabs = page.query_selector_all('[role="tab"]')
            if tabs and len(tabs) > 1:
                log(f"  {len(tabs)} tab trovati")
                for i, tab in enumerate(tabs):
                    try:
                        if tab.is_visible():
                            tab.click()
                            time.sleep(2)
                            log(f"    Tab {i}: click")
                    except Exception:
                        pass

            # Scroll
            for _ in range(3):
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                time.sleep(1)

            # Wait for remaining API calls
            time.sleep(3)

            page.screenshot(path=str(out_dir / "screenshots" / f"retry-{page_idx:02d}-{page_label}-final.png"), full_page=True)

            for req in captured_requests[capture_start:]:
                if req["page"] == "pending":
                    req["page"] = page_path

            log(f"  API catturate: {len(captured_requests) - capture_start}")

        context.close()
        browser.close()

    # Save - append to existing if present
    existing_calls = []
    api_file = out_dir / "api-calls.json"
    if api_file.exists():
        try:
            with open(api_file) as f:
                existing_calls = json.load(f)
            log(f"Merge con {len(existing_calls)} chiamate esistenti")
        except Exception:
            pass

    all_calls = existing_calls + captured_requests
    with open(api_file, "w") as f:
        json.dump(all_calls, f, indent=2, ensure_ascii=False, default=str)
    log(f"Totale API salvate: {len(all_calls)} ({len(existing_calls)} esistenti + {len(captured_requests)} nuove)")

    # Save log
    log_file = out_dir / "interactions-retry.log"
    with open(log_file, "w") as f:
        f.write("\n".join(log_lines))

    log(f"\n=== COMPLETATO ===")
    log(f"Nuove API: {len(captured_requests)}")
    log(f"Screenshot: {len(list((out_dir / 'screenshots').glob('retry-*.png')))}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 capture_retry.py <section_name> <page1_path> [page2_path] ...")
        sys.exit(1)
    capture_with_retry(sys.argv[1], sys.argv[2:])
