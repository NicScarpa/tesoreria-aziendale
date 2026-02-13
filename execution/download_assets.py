#!/usr/bin/env python3
"""Download all Sibill static assets using authenticated Playwright session."""

import json
import time
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")

def main():
    from playwright.sync_api import sync_playwright

    assets_dir = PROJECT_ROOT / ".tmp" / "capture" / "shared-assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    with open(PROJECT_ROOT / ".tmp" / "capture" / "all-assets-urls.json") as f:
        data = json.load(f)

    urls = data.get("sibill", []) + data.get("other", [])
    print(f"Scaricando {len(urls)} asset...")

    # Load credentials
    creds = {}
    with open(PROJECT_ROOT / "credenziali.env") as f:
        for line in f:
            line = line.strip()
            if ":" in line and not line.startswith("http"):
                k, v = line.split(":", 1)
                creds[k.strip()] = v.strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Login
        page.goto("https://app.sibill.com/login", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        for sel in ['input[type="email"]', 'input[name="email"]']:
            el = page.query_selector(sel)
            if el:
                el.fill(creds.get("user", ""))
                break
        for sel in ['input[type="password"]', 'input[name="password"]']:
            el = page.query_selector(sel)
            if el:
                el.fill(creds.get("password", ""))
                break
        for sel in ['button[type="submit"]', 'button:has-text("Accedi")']:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                break
        time.sleep(4)
        print("Login OK")

        downloaded = 0
        skipped = 0
        errors = 0

        for i, url in enumerate(urls):
            parsed = urlparse(url)
            path = parsed.path.lstrip("/")
            if not path:
                path = "index.html"

            # Add query string hash for uniqueness if needed
            if parsed.query:
                import hashlib
                qhash = hashlib.md5(parsed.query.encode()).hexdigest()[:8]
                base, ext = (path.rsplit(".", 1) + [""])[:2]
                path = f"{base}_{qhash}.{ext}" if ext else f"{base}_{qhash}"

            out_path = assets_dir / path
            if out_path.exists():
                skipped += 1
                continue

            out_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                resp = page.request.get(url, timeout=15000)
                if resp.status == 200:
                    body = resp.body()
                    with open(out_path, "wb") as f:
                        f.write(body)
                    downloaded += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                if errors <= 10:
                    print(f"  [{errors}] Error {url}: {e}")

            if (i + 1) % 50 == 0:
                print(f"  Progresso: {i+1}/{len(urls)} (scaricati: {downloaded}, errori: {errors})")

        context.close()
        browser.close()

    print(f"\nRisultato: Scaricati={downloaded}, Saltati={skipped}, Errori={errors}")
    print(f"Directory: {assets_dir}")

    # Calculate total size
    total_size = sum(f.stat().st_size for f in assets_dir.rglob("*") if f.is_file())
    print(f"Dimensione totale: {total_size / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    main()
