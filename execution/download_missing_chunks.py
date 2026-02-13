#!/usr/bin/env python3
"""
Download missing Vite chunks from app.sibill.com.

Reads all chunk filenames referenced by index-DS9gJP3A.js,
compares with files already in sibill-offline/assets/,
and downloads the missing ones.

Usage: python3 execution/download_missing_chunks.py [--dry-run]
"""

import re
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
ASSETS_DIR = PROJECT_ROOT / "sibill-offline" / "assets"
MAIN_BUNDLE = ASSETS_DIR / "index-C7GZzpi3.js"
BASE_URL = "https://app.sibill.com/assets"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def find_referenced_chunks():
    """Extract all chunk filenames referenced in the main Vite bundle."""
    with open(MAIN_BUNDLE, "r") as f:
        content = f.read()

    chunks = set()

    # Pattern 1: import('./filename.js')
    for m in re.finditer(r'import\(["\']\.\/([^"\']+\.(?:js|css))["\']\)', content):
        chunks.add(m.group(1))

    # Pattern 2: "assets/filename.js" or "assets/filename.css"
    for m in re.finditer(r'["\']assets\/([^"\'\s]+\.(?:js|css))["\']', content):
        chunks.add(m.group(1))

    return sorted(chunks)


def find_missing_chunks(referenced):
    """Compare referenced chunks with existing files."""
    existing = set(os.listdir(ASSETS_DIR)) if ASSETS_DIR.exists() else set()
    missing = [c for c in referenced if c not in existing]
    present = [c for c in referenced if c in existing]
    return missing, present


def download_file(filename, dry_run=False):
    """Download a single file with retry logic. Returns (success, size)."""
    url = f"{BASE_URL}/{filename}"
    dst = ASSETS_DIR / filename

    if dry_run:
        print(f"  [DRY] {filename}")
        return True, 0

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Encoding": "identity",
                "Origin": "https://app.sibill.com",
                "Referer": "https://app.sibill.com/",
                "Sec-Fetch-Dest": "script",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Cookie": "sibill_locale=it",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()

            # Validate: check it's not an HTML fallback
            text_start = data[:50].decode("utf-8", errors="replace").strip().lower()
            if text_start.startswith("<!doctype") or text_start.startswith("<html"):
                if attempt < MAX_RETRIES:
                    print(f"  RETRY {attempt}/{MAX_RETRIES} {filename}: got HTML instead of JS/CSS")
                    time.sleep(RETRY_DELAY * attempt)
                    continue
                else:
                    print(f"  SKIP {filename}: server returns HTML (SPA fallback)")
                    return False, 0

            with open(dst, "wb") as f:
                f.write(data)

            size_kb = len(data) / 1024
            print(f"  OK  {filename} ({size_kb:.1f} KB)")
            return True, len(data)

        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt < MAX_RETRIES:
                print(f"  RETRY {attempt}/{MAX_RETRIES} {filename}: {e}")
                time.sleep(RETRY_DELAY * attempt)
            else:
                print(f"  FAIL {filename}: {e}")
                return False, 0


def main():
    dry_run = "--dry-run" in sys.argv

    print("=== Download Chunk Mancanti ===")
    print(f"Bundle: {MAIN_BUNDLE.name}")
    print(f"Output: {ASSETS_DIR}")
    if dry_run:
        print("(DRY RUN)")
    print()

    # Step 1: Find referenced chunks
    referenced = find_referenced_chunks()
    print(f"Chunk referenziati nel bundle: {len(referenced)}")

    # Step 2: Find missing
    missing, present = find_missing_chunks(referenced)
    print(f"Gia' presenti: {len(present)}")
    print(f"Da scaricare: {len(missing)}")

    if not missing:
        print("\nTutti i chunk sono gia' presenti!")
        return

    print(f"\nInizio download di {len(missing)} file...\n")

    # Step 3: Download missing chunks
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    success = 0
    failed = 0
    total_bytes = 0
    failed_files = []

    for i, filename in enumerate(missing, 1):
        ok, size = download_file(filename, dry_run)
        if ok:
            success += 1
            total_bytes += size
        else:
            failed += 1
            failed_files.append(filename)

        # Brief pause to avoid rate limiting
        if not dry_run and i % 10 == 0:
            time.sleep(0.5)

    # Report
    print(f"\n=== REPORT ===")
    print(f"Scaricati: {success}/{len(missing)}")
    print(f"Falliti: {failed}")
    if not dry_run:
        print(f"Dimensione totale: {total_bytes / 1024 / 1024:.1f} MB")

    if failed_files:
        print(f"\nFile falliti:")
        for f in failed_files:
            print(f"  {f}")

    # Final verification
    if not dry_run:
        print(f"\n--- Verifica finale ---")
        all_referenced = find_referenced_chunks()
        still_missing, now_present = find_missing_chunks(all_referenced)
        print(f"Chunk referenziati: {len(all_referenced)}")
        print(f"Presenti: {len(now_present)}")
        print(f"Ancora mancanti: {len(still_missing)}")
        if still_missing:
            for f in still_missing:
                print(f"  MANCANTE: {f}")


if __name__ == "__main__":
    main()
