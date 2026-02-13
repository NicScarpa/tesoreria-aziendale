#!/usr/bin/env python3
"""
Build Sibill Offline Replay System
Reads captured API calls and assets, generates Service Worker + HTML wrapper.
Extracts Vite bundles from HAR files for full SPA rendering.
"""

import json
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode
from datetime import datetime

PROJECT_ROOT = Path("/Users/nicolascarpa/Desktop/Progetti/sibill-re")
CAPTURE_DIR = PROJECT_ROOT / ".tmp" / "capture"
OUTPUT_DIR = PROJECT_ROOT / "sibill-offline"

# All captured sections
SECTIONS = ["full-recapture", "transaction-details", "conti", "cashflow-f24", "scadenze", "fatture", "pagine-extra"]


def aggregate_api_calls():
    """Read all api-calls.json and create URL->Response map."""
    all_calls = []

    for section in SECTIONS:
        api_file = CAPTURE_DIR / section / "api-calls.json"
        if api_file.exists():
            with open(api_file) as f:
                calls = json.load(f)
            print(f"  {section}: {len(calls)} chiamate")
            all_calls.extend(calls)
        else:
            print(f"  {section}: MANCANTE")

    print(f"  Totale: {len(all_calls)} chiamate")
    return all_calls


def normalize_url(url):
    """Remove domain, keep path + sorted query params."""
    parsed = urlparse(url)
    path = parsed.path
    # Sort query params for consistent matching
    params = parse_qs(parsed.query, keep_blank_values=True)
    sorted_params = urlencode(sorted(params.items()), doseq=True)
    return f"{path}{'?' + sorted_params if sorted_params else ''}"


def build_api_map(all_calls):
    """Create method:path -> response mapping with variants."""
    api_map = {}
    sibill_domains = ["api.sibill.com", "app.sibill.com", "sibill.com"]
    skipped = 0

    for call in all_calls:
        url = call.get("url", "")
        parsed = urlparse(url)

        # Only include Sibill API calls with JSON responses
        if not any(d in parsed.netloc for d in sibill_domains):
            skipped += 1
            continue

        content_type = call.get("contentType", "")
        status = call.get("statusCode", 0)

        # Skip non-JSON, non-200, and auth/tracking calls
        if status != 200:
            continue
        if "json" not in content_type and not parsed.path.startswith("/api/"):
            continue

        response_body = call.get("responseBody")
        if response_body is None:
            continue

        method = call.get("method", "GET")
        norm_url = normalize_url(url)
        key = f"{method}:{norm_url}"

        # Store response - keep first successful response per key
        if key not in api_map:
            api_map[key] = {
                "method": method,
                "path": parsed.path,
                "query": parse_qs(parsed.query),
                "statusCode": status,
                "contentType": content_type,
                "responseBody": response_body,
                "requestBody": call.get("requestBody"),
            }

    print(f"  API uniche: {len(api_map)} (skipped {skipped} non-Sibill)")
    return api_map


def save_api_responses(api_map):
    """Save each response as individual JSON file and create index."""
    responses_dir = OUTPUT_DIR / "api-responses"
    responses_dir.mkdir(parents=True, exist_ok=True)

    index = {}
    for key, data in api_map.items():
        # Create filename from key hash
        file_hash = hashlib.md5(key.encode()).hexdigest()
        filename = f"{file_hash}.json"

        # Save response
        with open(responses_dir / filename, "w") as f:
            json.dump(data["responseBody"], f, ensure_ascii=False)

        # Add to index
        index[key] = {
            "file": filename,
            "method": data["method"],
            "path": data["path"],
            "statusCode": data["statusCode"],
            "contentType": data["contentType"],
        }

    # Save index
    with open(OUTPUT_DIR / "api-map.json", "w") as f:
        json.dump(index, f, indent=2)

    print(f"  Salvate {len(index)} risposte in {responses_dir}")
    return index


def extract_har_assets():
    """Extract Vite bundles from HAR files using extract_har_assets.py."""
    script = PROJECT_ROOT / "execution" / "extract_har_assets.py"
    if script.exists():
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"  [WARN] Errore estrazione: {result.stderr}")
    else:
        print("  [WARN] Script extract_har_assets.py non trovato")


def extract_spa_shell():
    """Find and extract the SPA HTML shell from HAR files."""
    shell_path = OUTPUT_DIR / "app-shell.html"
    if shell_path.exists():
        print(f"  HTML shell gia' presente: {shell_path}")
        return True

    # Search HAR files for the HTML shell
    for section in SECTIONS:
        har_path = CAPTURE_DIR / section / "recording.har"
        if not har_path.exists():
            continue

        with open(har_path) as f:
            har = json.load(f)

        for entry in har["log"]["entries"]:
            url = entry["request"]["url"]
            content = entry["response"]["content"]
            mime = content.get("mimeType", "")
            status = entry["response"]["status"]

            if (
                "text/html" in mime
                and status == 200
                and "app.sibill.com" in url
                and "/login" not in url
                and "_file" in content
            ):
                file_path = har_path.parent / content["_file"]
                if file_path.exists():
                    shutil.copy2(str(file_path), str(shell_path))
                    print(f"  HTML shell estratto da {section}: {url}")
                    return True

    print("  [WARN] Nessun HTML shell trovato nei HAR")
    return False


def generate_service_worker(api_index):
    """Generate sw.js that intercepts all requests with SPA fallback."""

    # Build a lookup structure for the SW
    path_map = {}
    for key, data in api_index.items():
        method, url = key.split(":", 1)
        path = url.split("?")[0]
        if path not in path_map:
            path_map[path] = []
        path_map[path].append({
            "key": key,
            "method": method,
            "fullUrl": url,
            "file": data["file"],
            "contentType": data["contentType"],
        })

    sw_content = f"""// Sibill Offline Service Worker
// Generated: {datetime.now().isoformat()}
// API endpoints cached: {len(api_index)}

const CACHE_NAME = 'sibill-offline-v1';
const API_MAP = {json.dumps(path_map, indent=2)};

// Known static file extensions
const STATIC_EXTENSIONS = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.json', '.map'];

// Install: pre-cache all API responses
self.addEventListener('install', (event) => {{
  console.log('[SW] Installing Sibill Offline Service Worker');
  self.skipWaiting();
}});

// Activate: take control immediately
self.addEventListener('activate', (event) => {{
  console.log('[SW] Activating - taking control');
  event.waitUntil(clients.claim());
}});

// Normalize URL for matching
function normalizeUrl(url) {{
  try {{
    const parsed = new URL(url);
    const params = new URLSearchParams(parsed.search);
    const sorted = new URLSearchParams([...params.entries()].sort());
    return parsed.pathname + (sorted.toString() ? '?' + sorted.toString() : '');
  }} catch(e) {{
    return url;
  }}
}}

// Find matching API response
function findMatch(method, url) {{
  const parsed = new URL(url);
  const path = parsed.pathname;
  const fullNorm = normalizeUrl(url);

  const candidates = API_MAP[path];
  if (!candidates) return null;

  // Try exact match first (method + path + params)
  const exactKey = method + ':' + fullNorm;
  for (const c of candidates) {{
    if (c.key === exactKey) return c;
  }}

  // Try method + path match (ignore params)
  for (const c of candidates) {{
    if (c.method === method) return c;
  }}

  return null;
}}

// Check if path looks like a static file
function isStaticFile(pathname) {{
  return STATIC_EXTENSIONS.some(ext => pathname.endsWith(ext));
}}

// Fetch interceptor
self.addEventListener('fetch', (event) => {{
  const url = event.request.url;
  const method = event.request.method;

  // Block tracking/analytics domains
  const trackingDomains = ['google', 'facebook', 'segment', 'hotjar', 'sentry', 'intercom', 'crisp', 'mixpanel', 'analytics', 'customer.io', 'customerioforms', 'gist.build', 'hubapi.com', 'hscollectedforms.net', 'hs-banner.com', 'satismeter.com', 'exceptions.sibill.com', 'realtime.cloud.gist.build'];
  try {{
    const hostname = new URL(url).hostname;
    if (trackingDomains.some(d => hostname.includes(d))) {{
      event.respondWith(new Response('', {{ status: 204 }}));
      return;
    }}
  }} catch(e) {{}}

  // Try to match API call
  const match = findMatch(method, url);

  if (match) {{
    event.respondWith(
      fetch('/api-responses/' + match.file)
        .then(r => r.text())
        .then(body => {{
          return new Response(body, {{
            status: 200,
            headers: {{
              'Content-Type': match.contentType || 'application/json',
              'Access-Control-Allow-Origin': '*',
              'X-Sibill-Offline': 'cached',
            }}
          }});
        }})
        .catch(err => {{
          console.warn('[SW] [CACHE-ERROR]', method, url, err);
          return new Response(JSON.stringify({{error: 'cache miss'}}), {{
            status: 200,
            headers: {{ 'Content-Type': 'application/json' }}
          }});
        }})
    );
    return;
  }}

  // Try to serve static assets locally
  try {{
    const pathname = new URL(url).pathname;

    // Static file or known path prefix — try to serve directly
    if (isStaticFile(pathname) || pathname.startsWith('/assets/') || pathname.startsWith('/api-responses/') || pathname.startsWith('/favicon/')) {{
      event.respondWith(
        fetch(pathname).then(r => {{
          if (r.ok) return r;
          console.warn('[SW] [MISS]', method, url);
          return new Response('', {{ status: 200 }});
        }}).catch(() => {{
          console.warn('[SW] [MISS]', method, url);
          return new Response('', {{ status: 200 }});
        }})
      );
      return;
    }}

    // SPA fallback: for non-file routes, serve the app shell HTML
    // This is critical for React Router to work — all routes like
    // /cashflow, /counterparts, /invoices/dashboard etc. need the HTML shell
    if (method === 'GET' && pathname !== '/' && pathname !== '/index.html' && pathname !== '/sw.js') {{
      event.respondWith(
        fetch('/app-shell.html').then(r => {{
          if (r.ok) {{
            return new Response(r.body, {{
              status: 200,
              headers: {{ 'Content-Type': 'text/html; charset=utf-8' }}
            }});
          }}
          return r;
        }}).catch(() => {{
          console.warn('[SW] [MISS] SPA fallback failed for', pathname);
          return new Response('', {{ status: 200 }});
        }})
      );
      return;
    }}
  }} catch(e) {{}}

  // Fallback: log miss and return empty
  console.warn('[SW] [MISS]', method, url);
  event.respondWith(new Response('', {{ status: 200 }}));
}});
"""

    with open(OUTPUT_DIR / "sw.js", "w") as f:
        f.write(sw_content)
    print(f"  Service Worker generato: {OUTPUT_DIR / 'sw.js'}")


def generate_index_html():
    """Generate index.html wrapper that registers SW and provides navigation."""

    capture_date = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sibill - Replica Offline</title>
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
    <link rel="preconnect" href="https://fonts.googleapis.com"/>
    <link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}

        #offline-banner {{
            background: linear-gradient(135deg, #ff6b35, #f7931e);
            color: white;
            padding: 8px 16px;
            text-align: center;
            font-size: 13px;
            font-weight: 500;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 99999;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        #offline-banner .close-btn {{
            float: right;
            cursor: pointer;
            opacity: 0.8;
            margin-left: 16px;
        }}
        #offline-banner .close-btn:hover {{ opacity: 1; }}

        #loading {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            color: #333;
        }}
        #loading h1 {{ font-size: 24px; margin-bottom: 16px; }}
        #loading p {{ color: #666; margin-bottom: 8px; }}
        .spinner {{
            width: 40px; height: 40px;
            border: 4px solid #e0e0e0;
            border-top-color: #ff6b35;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-bottom: 24px;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

        nav#offline-nav {{
            background: #1a1a2e;
            padding: 10px 24px;
            display: flex;
            gap: 4px;
            align-items: center;
            margin-top: 36px;
            flex-wrap: wrap;
        }}
        nav#offline-nav a {{
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            padding: 7px 14px;
            border-radius: 6px;
            font-size: 13px;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        nav#offline-nav a:hover, nav#offline-nav a.active {{
            background: rgba(255,255,255,0.15);
            color: white;
        }}
        nav#offline-nav .brand {{
            font-weight: 700;
            font-size: 18px;
            color: white;
            margin-right: 20px;
        }}
        nav#offline-nav .sep {{
            color: rgba(255,255,255,0.2);
            margin: 0 4px;
        }}

        #app-frame {{
            width: 100%;
            height: calc(100vh - 84px);
            border: none;
        }}
    </style>
</head>
<body>
    <div id="offline-banner">
        REPLICA OFFLINE — Dati congelati al {capture_date}
        <span class="close-btn" onclick="this.parentElement.style.display='none'">&times;</span>
    </div>

    <nav id="offline-nav">
        <span class="brand">Sibill Offline</span>
        <a href="#conti" onclick="navigate('transactions/movements', this)">Movimenti</a>
        <a href="#pagamenti" onclick="navigate('transactions/payments', this)">Pagamenti</a>
        <span class="sep">|</span>
        <a href="#cashflow" onclick="navigate('cashflow', this)">Cashflow</a>
        <a href="#scadenze" onclick="navigate('outstanding', this)">Scadenze</a>
        <span class="sep">|</span>
        <a href="#fatture" onclick="navigate('invoices/dashboard', this)">Fatture</a>
        <a href="#import" onclick="navigate('invoices/import', this)">Import</a>
        <a href="#f24" onclick="navigate('f24', this)">F24</a>
        <span class="sep">|</span>
        <a href="#controparti" onclick="navigate('counterparts', this)">Controparti</a>
        <a href="#riconciliazioni" onclick="navigate('reconciliations', this)">Riconciliazioni</a>
        <span class="sep">|</span>
        <a href="#conti" onclick="navigate('accounts', this)">Gestisci Conti</a>
        <a href="#regole" onclick="navigate('transactions/rules/inflow/list', this)">Regole</a>
        <a href="#impostazioni" onclick="navigate('settings', this)">Impostazioni</a>
        <a href="#profilo" onclick="navigate('invoices/profile/company-data', this)">Profilo</a>
    </nav>

    <div id="loading">
        <div class="spinner"></div>
        <h1>Sibill Offline</h1>
        <p>Registrazione Service Worker...</p>
        <p id="sw-status"></p>
    </div>

    <iframe id="app-frame" style="display:none"></iframe>

    <script>
        const SW_STATUS = document.getElementById('sw-status');
        const LOADING = document.getElementById('loading');
        const FRAME = document.getElementById('app-frame');

        // Register Service Worker
        if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/sw.js', {{ scope: '/' }})
                .then(reg => {{
                    console.log('[App] SW registered:', reg.scope);
                    SW_STATUS.textContent = 'Service Worker registrato!';

                    // Wait for activation
                    if (reg.active) {{
                        onReady();
                    }} else {{
                        const sw = reg.installing || reg.waiting;
                        sw.addEventListener('statechange', () => {{
                            if (sw.state === 'activated') onReady();
                        }});
                    }}
                }})
                .catch(err => {{
                    console.error('[App] SW registration failed:', err);
                    SW_STATUS.textContent = 'Errore: ' + err.message;
                }});
        }} else {{
            SW_STATUS.textContent = 'Service Worker non supportato dal browser';
        }}

        function onReady() {{
            SW_STATUS.textContent = 'Pronto!';
            setTimeout(() => {{
                LOADING.style.display = 'none';
                FRAME.style.display = 'block';
                // Load default page
                navigate('cashflow', document.querySelector('a[href="#cashflow"]'));
            }}, 500);
        }}

        function navigate(path, el) {{
            FRAME.src = '/' + path;
            // Update active nav link
            document.querySelectorAll('#offline-nav a').forEach(a => a.classList.remove('active'));
            if (el) el.classList.add('active');
        }}

        // Log all SW misses
        navigator.serviceWorker.addEventListener('message', (event) => {{
            if (event.data.type === 'miss') {{
                console.warn('[MISS]', event.data.url);
            }}
        }});
    </script>
</body>
</html>"""

    with open(OUTPUT_DIR / "index.html", "w") as f:
        f.write(html)
    print(f"  index.html generato")


def generate_server():
    """Generate serve.py for local hosting."""

    server_code = '''#!/usr/bin/env python3
"""Local server for Sibill Offline Replay."""
import http.server
import os
import socket
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class DualStackHTTPServer(http.server.HTTPServer):
    """HTTPServer that binds to both IPv4 and IPv6 (dual-stack)."""
    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


class SibillHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Serve index.html for SPA routes
        path = self.path.split("?")[0]
        full_path = os.path.join(DIRECTORY, path.lstrip("/"))

        if not os.path.exists(full_path) and not path.startswith("/api-responses/") and not path.startswith("/assets/"):
            # SPA fallback: serve app-shell.html for app routes, index.html for root
            shell = os.path.join(DIRECTORY, "app-shell.html")
            if os.path.exists(shell) and path != "/":
                self.path = "/app-shell.html"
            else:
                self.path = "/index.html"

        return super().do_GET()

    def end_headers(self):
        # Add CORS and Service Worker headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        if self.path == "/sw.js":
            self.send_header("Service-Worker-Allowed", "/")
        super().end_headers()

    def log_message(self, format, *args):
        # Color-code log output
        path = args[0].split(" ")[1] if args else ""
        if "/api-responses/" in path:
            print(f"\\033[32m{format % args}\\033[0m")
        elif "/assets/" in path:
            print(f"\\033[36m{format % args}\\033[0m")
        else:
            print(format % args)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    try:
        httpd = DualStackHTTPServer(("::", port), SibillHandler)
    except OSError:
        # Fallback to IPv4 only if dual-stack not supported
        httpd = http.server.HTTPServer(("", port), SibillHandler)
    with httpd:
        print(f"\\n  Sibill Offline Server")
        print(f"  http://localhost:{port}")
        print(f"  Directory: {DIRECTORY}")
        print(f"  Ctrl+C per fermare\\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nServer fermato.")
'''

    with open(OUTPUT_DIR / "serve.py", "w") as f:
        f.write(server_code)
    print(f"  serve.py generato")


def copy_assets():
    """Copy shared assets, then overlay HAR-extracted Vite bundles."""
    dst = OUTPUT_DIR / "assets"
    dst.mkdir(parents=True, exist_ok=True)

    # Step 1: Extract Vite bundles from HAR files (the critical step)
    print("  Estrazione bundle Vite da HAR...")
    extract_har_assets()

    # Step 2: Count what we have
    if dst.exists():
        files = [f for f in dst.rglob("*") if f.is_file()]
        js_count = len([f for f in files if f.suffix == ".js"])
        css_count = len([f for f in files if f.suffix == ".css"])
        total_size = sum(f.stat().st_size for f in files)
        print(f"  Asset totali: {len(files)} file ({js_count} JS, {css_count} CSS, {total_size / 1024 / 1024:.1f} MB)")
    else:
        print("  [WARN] Directory asset non trovata dopo estrazione")


def generate_readme():
    """Generate README with usage instructions."""
    readme = f"""# Sibill Offline Replica

Replica congelata dell'applicazione Sibill (app.sibill.com).
Dati catturati il: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Come usare

1. Apri un terminale in questa directory
2. Esegui: `python3 serve.py`
3. Apri il browser: http://localhost:8080

## Struttura

- `index.html` — Wrapper con navigazione e registrazione Service Worker
- `app-shell.html` — HTML shell del SPA React (servito per tutte le route)
- `sw.js` — Service Worker che intercetta richieste API e serve asset cached
- `api-map.json` — Indice delle API cached
- `api-responses/` — Risposte API in formato JSON
- `assets/` — Bundle Vite (JS, CSS), font, immagini
- `serve.py` — Server locale

## Sezioni disponibili

- **Movimenti** — Movimenti bancari
- **Pagamenti** — Pagamenti e bonifici
- **Cashflow** — Previsioni e categorie
- **Scadenze** — Scadenzario e ricorrenze
- **Fatture** — Dashboard, ricevute, emesse, corrispettivi
- **Import** — Import fatture
- **F24** — Modelli F24
- **Controparti** — Gestione controparti
- **Profilo** — Profilo azienda

## Note

- I dati sono congelati al momento della cattura
- Nessuna connessione a server esterni
- Le API che non hanno una risposta cached vengono logate come [MISS] in console
- Il Service Worker serve `app-shell.html` per tutte le route SPA
"""
    with open(OUTPUT_DIR / "README.md", "w") as f:
        f.write(readme)
    print(f"  README.md generato")


def main():
    print(f"=== Build Sibill Offline ===")
    print(f"Output: {OUTPUT_DIR}")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Aggregate API calls
    print("1. Aggregazione API calls...")
    all_calls = aggregate_api_calls()

    # Step 2: Build API map
    print("\n2. Costruzione API map...")
    api_map = build_api_map(all_calls)

    # Step 3: Save responses
    print("\n3. Salvataggio risposte...")
    api_index = save_api_responses(api_map)

    # Step 4: Copy/extract assets (Vite bundles from HAR)
    print("\n4. Copia e estrazione asset...")
    copy_assets()

    # Step 5: Extract SPA shell
    print("\n5. Estrazione HTML shell SPA...")
    extract_spa_shell()

    # Step 6: Generate Service Worker
    print("\n6. Generazione Service Worker...")
    generate_service_worker(api_index)

    # Step 7: Generate HTML wrapper
    print("\n7. Generazione index.html...")
    generate_index_html()

    # Step 8: Generate server
    print("\n8. Generazione serve.py...")
    generate_server()

    # Step 9: README
    print("\n9. Generazione README...")
    generate_readme()

    # Summary
    print(f"\n=== BUILD COMPLETATA ===")
    total_files = sum(1 for _ in OUTPUT_DIR.rglob("*") if _.is_file())
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file())
    print(f"File totali: {total_files}")
    print(f"Dimensione: {total_size / 1024 / 1024:.1f} MB")

    # Asset breakdown
    assets_dir = OUTPUT_DIR / "assets"
    if assets_dir.exists():
        js_files = list(assets_dir.glob("*.js"))
        css_files = list(assets_dir.glob("*.css"))
        print(f"Bundle JS: {len(js_files)}, CSS: {len(css_files)}")

    api_responses = OUTPUT_DIR / "api-responses"
    if api_responses.exists():
        print(f"API cached: {len(list(api_responses.glob('*.json')))}")

    print(f"\nPer avviare: cd {OUTPUT_DIR} && python3 serve.py")


if __name__ == "__main__":
    main()
