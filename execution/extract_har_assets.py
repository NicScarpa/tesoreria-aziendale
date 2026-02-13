#!/usr/bin/env python3
"""
Extract Vite bundles and static assets from Playwright HAR recordings.

Playwright's record_har_content="attach" stores response bodies as separate files
(referenced via _file in the HAR JSON). This script finds all app.sibill.com/assets/*
entries and copies the referenced files to sibill-offline/assets/ with their original names.

Usage: python3 extract_har_assets.py [--dry-run]
"""

import json
import os
import shutil
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
CAPTURE_DIR = PROJECT_ROOT / ".tmp" / "capture"
OUTPUT_DIR = PROJECT_ROOT / "sibill-offline" / "assets"

# All sections that have HAR recordings
HAR_SECTIONS = ["full-recapture", "fatture", "scadenze", "cashflow-f24", "conti", "pagine-extra"]


def find_har_files():
    """Find all recording.har files in capture directories."""
    hars = []
    for section in HAR_SECTIONS:
        har_path = CAPTURE_DIR / section / "recording.har"
        if har_path.exists():
            hars.append((section, har_path))
    return hars


def extract_assets_from_har(har_path, section_name):
    """Extract asset entries from a single HAR file.

    Returns dict of {asset_filename: {file_ref, har_dir, size, mime}}
    """
    har_dir = har_path.parent
    assets = {}

    with open(har_path) as f:
        har = json.load(f)

    for entry in har["log"]["entries"]:
        url = entry["request"]["url"]

        # Match Sibill app assets
        if "app.sibill.com/assets/" not in url:
            continue

        filename = url.split("/assets/")[-1].split("?")[0]
        content = entry["response"]["content"]

        # Skip if no _file reference (browser cache hit, no body captured)
        if "_file" not in content:
            continue

        file_ref = content["_file"]
        file_path = har_dir / file_ref

        if not file_path.exists():
            continue

        # Keep first occurrence (they're all identical for same filename)
        if filename not in assets:
            assets[filename] = {
                "file_ref": str(file_path),
                "section": section_name,
                "size": content.get("size", 0),
                "mime": content.get("mimeType", ""),
            }

    return assets


def extract_html_page(har_path, section_name):
    """Extract the main HTML page response (for SPA shell).

    Returns the _file path for the HTML response of the app root, if found.
    """
    har_dir = har_path.parent

    with open(har_path) as f:
        har = json.load(f)

    for entry in har["log"]["entries"]:
        url = entry["request"]["url"]
        content = entry["response"]["content"]
        mime = content.get("mimeType", "")
        status = entry["response"]["status"]

        # Look for the main HTML page (not /login)
        if (
            "text/html" in mime
            and status == 200
            and "app.sibill.com" in url
            and "/login" not in url
            and "_file" in content
        ):
            file_path = har_dir / content["_file"]
            if file_path.exists():
                return str(file_path), url

    return None, None


def main():
    dry_run = "--dry-run" in sys.argv

    print("=== Estrazione Asset da HAR ===")
    print(f"Output: {OUTPUT_DIR}")
    if dry_run:
        print("(DRY RUN - nessun file scritto)")
    print()

    # Find all HAR files
    hars = find_har_files()
    if not hars:
        print("ERRORE: Nessun file HAR trovato!")
        sys.exit(1)

    print(f"HAR trovati: {len(hars)}")
    for section, path in hars:
        size_mb = path.stat().st_size / 1024 / 1024
        print(f"  {section}: {path.name} ({size_mb:.1f} MB)")
    print()

    # Extract assets from all HARs
    all_assets = {}
    for section, har_path in hars:
        assets = extract_assets_from_har(har_path, section)
        print(f"  {section}: {len(assets)} asset trovati")
        # Merge, keeping first occurrence
        for filename, info in assets.items():
            if filename not in all_assets:
                all_assets[filename] = info

    print(f"\nAsset unici totali: {len(all_assets)}")

    # Classify by type
    by_ext = defaultdict(list)
    for filename, info in all_assets.items():
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "unknown"
        by_ext[ext].append((filename, info))

    for ext in sorted(by_ext.keys()):
        items = by_ext[ext]
        total_size = sum(i[1]["size"] for i in items)
        print(f"  .{ext}: {len(items)} file ({total_size / 1024 / 1024:.1f} MB)")

    # Copy files to output
    if not dry_run:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    copied = 0
    errors = 0
    for filename, info in sorted(all_assets.items()):
        src = Path(info["file_ref"])
        dst = OUTPUT_DIR / filename

        if dry_run:
            print(f"  [DRY] {filename} <- {src.name}")
            copied += 1
            continue

        try:
            shutil.copy2(str(src), str(dst))
            copied += 1
        except Exception as e:
            print(f"  [ERRORE] {filename}: {e}")
            errors += 1

    print(f"\nCopiati: {copied} file")
    if errors:
        print(f"Errori: {errors}")

    # Also try to extract SPA HTML shell
    print("\n--- Ricerca HTML shell SPA ---")
    html_shell_path = None
    for section, har_path in hars:
        html_path, html_url = extract_html_page(har_path, section)
        if html_path:
            print(f"  Trovato HTML shell da {section}: {html_url}")
            if not dry_run:
                dst = PROJECT_ROOT / "sibill-offline" / "app-shell.html"
                shutil.copy2(html_path, str(dst))
                print(f"  Salvato in: {dst}")
                html_shell_path = str(dst)
            break

    if not html_shell_path:
        print("  Nessun HTML shell trovato")

    # Summary
    print(f"\n=== COMPLETATO ===")
    print(f"Asset estratti: {copied}")
    print(f"Directory: {OUTPUT_DIR}")

    # Verify
    if not dry_run:
        actual_files = list(OUTPUT_DIR.rglob("*"))
        actual_files = [f for f in actual_files if f.is_file()]
        js_count = len([f for f in actual_files if f.suffix == ".js"])
        css_count = len([f for f in actual_files if f.suffix == ".css"])
        total_size = sum(f.stat().st_size for f in actual_files)
        print(f"Verifica: {len(actual_files)} file ({js_count} JS, {css_count} CSS), {total_size / 1024 / 1024:.1f} MB")

    return all_assets


if __name__ == "__main__":
    main()
