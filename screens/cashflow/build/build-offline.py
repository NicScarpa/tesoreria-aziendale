#!/usr/bin/env python3
"""
Build Offline Package — Sibill Cashflow

Trasforma i dati catturati (HAR + HTML + localStorage) nel pacchetto offline servibile.
Genera: offline/index.html, sw.js, sw-config.json, assets/, api-responses/, fonts/

Uso: python3 build/build-offline.py
Prerequisiti: prima eseguire capture/capture-cashflow.js
"""

import json
import os
import sys
import hashlib
import base64
import re
from urllib.parse import urlparse, urlencode, parse_qs
from pathlib import Path

# Paths
SCREENS_DIR = Path(__file__).parent.parent
CAPTURED_DIR = SCREENS_DIR / 'captured'
OFFLINE_DIR = SCREENS_DIR / 'offline'
HAR_PATH = CAPTURED_DIR / 'har-complete.har'
INDEX_HTML_PATH = CAPTURED_DIR / 'index.html'
LOCALSTORAGE_PATH = CAPTURED_DIR / 'localStorage.json'

# Domini di tracking da bloccare
BLOCKED_DOMAINS = [
    'satismeter.com',
    'gist.build',
    'customer.io',
    'linkedin.com',
    'hubspot.com',
    'hotjar.com',
    'facebook.net',
    'facebook.com',
    'fbcdn.net',
    'exceptions.sibill.com',
    'tracking.sibill.com',
    'sentry.io',
    'intercom.io',
    'intercomcdn.com',
    'segment.io',
    'segment.com',
    'google-analytics.com',
    'googletagmanager.com',
    'doubleclick.net',
]

# Pattern per redazione dati sensibili
SENSITIVE_PATTERNS = [
    (re.compile(r'"email"\s*:\s*"[^"]*"'), '"email": "user@example.com"'),
    (re.compile(r'"password"\s*:\s*"[^"]*"'), '"password": "***"'),
    (re.compile(r'"token"\s*:\s*"[^"]{20,}"'), '"token": "REDACTED"'),
    (re.compile(r'"accessToken"\s*:\s*"[^"]{20,}"'), '"accessToken": "REDACTED"'),
    (re.compile(r'"refreshToken"\s*:\s*"[^"]{20,}"'), '"refreshToken": "REDACTED"'),
    (re.compile(r'Bearer\s+[A-Za-z0-9._-]{20,}'), 'Bearer REDACTED'),
]


def ensure_dirs():
    """Crea la struttura directory di output."""
    for subdir in ['assets', 'api-responses', 'fonts']:
        (OFFLINE_DIR / subdir).mkdir(parents=True, exist_ok=True)


def normalize_api_url(url: str) -> str:
    """Normalizza un URL API ordinando i query params."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    # Ordina params per chiave, poi per valore
    sorted_params = sorted(
        [(k, sorted(v)) for k, v in params.items()],
        key=lambda x: x[0]
    )
    # Ricostruisci query string normalizzata
    normalized_query = '&'.join(
        f'{k}={v[0]}' if len(v) == 1 else '&'.join(f'{k}={vi}' for vi in v)
        for k, v in sorted_params
    )
    return f'{parsed.scheme}://{parsed.netloc}{parsed.path}{"?" + normalized_query if normalized_query else ""}'


def url_to_filename(url: str) -> str:
    """Genera un nome file deterministico da un URL."""
    parsed = urlparse(url)
    # Usa path + query hash per unicità
    path_part = parsed.path.replace('/', '_').strip('_')
    if parsed.query:
        query_hash = hashlib.md5(parsed.query.encode()).hexdigest()[:8]
        return f'{path_part}_{query_hash}.json'
    return f'{path_part}.json'


def redact_sensitive(text: str) -> str:
    """Redatta dati sensibili dal testo."""
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def is_blocked_domain(url: str) -> bool:
    """Controlla se un URL appartiene a un dominio bloccato."""
    try:
        hostname = urlparse(url).hostname or ''
        return any(blocked in hostname for blocked in BLOCKED_DOMAINS)
    except Exception:
        return False


def decode_har_body(content: dict) -> bytes | None:
    """Decodifica il body di una entry HAR."""
    if not content:
        return None

    text = content.get('text', '')
    if not text:
        return None

    encoding = content.get('encoding', '')
    if encoding == 'base64':
        try:
            return base64.b64decode(text)
        except Exception:
            return None

    if isinstance(text, str):
        return text.encode('utf-8')

    return None


def parse_har(har_path: Path) -> list[dict]:
    """Parsa il file HAR e restituisce le entry con body decodificati."""
    print(f'Parsing HAR: {har_path}')

    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)

    entries = har.get('log', {}).get('entries', [])
    print(f'  Entries totali: {len(entries)}')

    result = []
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')

        if is_blocked_domain(url):
            continue

        body = decode_har_body(response.get('content', {}))
        mime_type = response.get('content', {}).get('mimeType', '')
        status = response.get('status', 0)

        result.append({
            'url': url,
            'method': request.get('method', 'GET'),
            'status': status,
            'mime_type': mime_type,
            'body': body,
            'response_headers': {
                h['name'].lower(): h['value']
                for h in response.get('headers', [])
            }
        })

    with_body = sum(1 for e in result if e['body'])
    print(f'  Entries utili: {len(result)} ({with_body} con body)')
    return result


def extract_assets(entries: list[dict]) -> dict:
    """Estrae asset statici (JS, CSS, immagini, font) e li salva."""
    print('\nEstrazione asset statici...')
    assets_map = {}  # url -> local_path

    for entry in entries:
        url = entry['url']
        body = entry['body']
        if not body:
            continue

        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        path = parsed.path

        # Asset da app.sibill.com/assets/
        if 'app.sibill.com' in hostname and '/assets/' in path:
            filename = path.split('/')[-1]
            if not filename:
                continue

            local_path = OFFLINE_DIR / 'assets' / filename
            local_path.write_bytes(body)
            assets_map[url] = f'assets/{filename}'

        # Font da Google
        elif 'fonts.gstatic.com' in hostname and path.endswith('.woff2'):
            filename = path.split('/')[-1]
            local_path = OFFLINE_DIR / 'fonts' / filename
            local_path.write_bytes(body)
            assets_map[url] = f'fonts/{filename}'

        elif 'fonts.googleapis.com' in hostname:
            # CSS dei font — salva e modifica i path
            css_text = body.decode('utf-8', errors='replace')
            # Sostituisci URL font con path locali
            css_text = re.sub(
                r'https://fonts\.gstatic\.com/[^\)]+\.woff2',
                '/fonts/public-sans.woff2',
                css_text
            )
            local_path = OFFLINE_DIR / 'fonts' / 'public-sans.css'
            local_path.write_text(css_text, encoding='utf-8')
            assets_map[url] = 'fonts/public-sans.css'

        # Favicon e altre immagini da app.sibill.com
        elif 'app.sibill.com' in hostname and any(path.endswith(ext) for ext in ['.png', '.svg', '.ico', '.jpg', '.jpeg', '.webp']):
            filename = path.split('/')[-1]
            local_path = OFFLINE_DIR / 'assets' / filename
            local_path.write_bytes(body)
            assets_map[url] = f'assets/{filename}'

    print(f'  Asset estratti: {len(assets_map)}')
    return assets_map


def extract_api_responses(entries: list[dict]) -> dict:
    """Estrae risposte API e le salva come JSON."""
    print('\nEstrazione risposte API...')
    api_routes = {}     # normalized_url -> {file, contentType, status}
    path_fallbacks = {} # api_path -> file (prima risposta vista per quel path)

    for entry in entries:
        url = entry['url']
        body = entry['body']
        if not body:
            continue

        parsed = urlparse(url)
        hostname = parsed.hostname or ''

        if 'api.sibill.com' not in hostname:
            continue

        # Normalizza URL per matching
        normalized = normalize_api_url(url)

        # Nome file deterministico
        filename = url_to_filename(url)

        # Redatta dati sensibili nel body
        try:
            body_text = body.decode('utf-8')
            body_text = redact_sensitive(body_text)
            body_bytes = body_text.encode('utf-8')
        except UnicodeDecodeError:
            body_bytes = body

        # Salva
        local_path = OFFLINE_DIR / 'api-responses' / filename
        local_path.write_bytes(body_bytes)

        content_type = entry.get('mime_type', 'application/json')
        if 'json' not in content_type:
            content_type = 'application/json'

        api_routes[normalized] = {
            'file': f'api-responses/{filename}',
            'contentType': content_type,
            'status': entry['status']
        }

        # Path fallback (primo per ogni path)
        api_path = parsed.path
        if api_path not in path_fallbacks:
            path_fallbacks[api_path] = f'api-responses/{filename}'

    print(f'  API responses: {len(api_routes)}')
    print(f'  Path fallbacks: {len(path_fallbacks)}')
    return api_routes, path_fallbacks


def generate_sw_config(api_routes: dict, path_fallbacks: dict, assets_map: dict):
    """Genera sw-config.json."""
    print('\nGenerazione sw-config.json...')

    config = {
        'version': '1.0.0',
        'generatedAt': __import__('datetime').datetime.now().isoformat(),
        'routes': api_routes,
        'pathFallbacks': path_fallbacks,
        'blockedDomains': BLOCKED_DOMAINS,
        'assetRoutes': {
            url: local_path for url, local_path in assets_map.items()
        }
    }

    config_path = OFFLINE_DIR / 'sw-config.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f'  sw-config.json: {config_path} ({config_path.stat().st_size / 1024:.0f} KB)')


def generate_service_worker():
    """Genera sw.js — il Service Worker per il replay offline."""
    print('\nGenerazione sw.js...')

    sw_code = r"""// sw.js — Service Worker per Replay Offline Sibill Cashflow
// Generato automaticamente da build-offline.py

const SW_VERSION = '1.0.0';
const CONFIG_URL = '/sw-config.json';
let config = null;

// Install: carica la configurazione
self.addEventListener('install', (event) => {
  console.log('[SW] Installing v' + SW_VERSION);
  event.waitUntil(
    fetch(CONFIG_URL)
      .then(r => r.json())
      .then(c => {
        config = c;
        console.log('[SW] Config loaded:', Object.keys(c.routes).length, 'API routes,',
          Object.keys(c.assetRoutes).length, 'asset routes');
      })
      .then(() => self.skipWaiting())
  );
});

// Activate: prendi controllo immediato di tutti i client
self.addEventListener('activate', (event) => {
  console.log('[SW] Activated');
  event.waitUntil(self.clients.claim());
});

// Normalizza URL ordinando i query params
function normalizeUrl(urlStr) {
  try {
    const url = new URL(urlStr);
    const params = new URLSearchParams(url.search);
    const sorted = [...params.entries()].sort((a, b) => a[0].localeCompare(b[0]));
    url.search = new URLSearchParams(sorted).toString();
    return url.toString();
  } catch (e) {
    return urlStr;
  }
}

// Fetch: intercetta tutte le richieste
self.addEventListener('fetch', (event) => {
  if (!config) {
    // Config non ancora caricata — lascia passare
    return;
  }

  const url = new URL(event.request.url);
  const hostname = url.hostname;

  // 1. Blocca domini di tracking
  if (config.blockedDomains.some(d => hostname.includes(d))) {
    event.respondWith(new Response('', { status: 204 }));
    return;
  }

  // 2. Navigation requests → serve index.html (SPA routing)
  if (event.request.mode === 'navigate') {
    console.log('[SW] Navigate:', url.pathname, '→ /index.html');
    event.respondWith(fetch('/index.html'));
    return;
  }

  // 3. API requests (api.sibill.com)
  if (hostname === 'api.sibill.com' || url.pathname.startsWith('/api/')) {
    const normalized = normalizeUrl(event.request.url);
    const route = config.routes[normalized];

    if (route) {
      // Match esatto
      console.log('[SW] API exact match:', url.pathname);
      event.respondWith(
        fetch('/' + route.file).then(r =>
          new Response(r.body, {
            status: route.status || 200,
            headers: {
              'Content-Type': route.contentType || 'application/vnd.api+json',
              'Access-Control-Allow-Origin': '*',
              'Access-Control-Allow-Credentials': 'true',
              'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept'
            }
          })
        )
      );
      return;
    }

    // Fallback per path (senza query params)
    const apiPath = url.pathname;
    const fallback = config.pathFallbacks[apiPath];
    if (fallback) {
      console.log('[SW] API path fallback:', apiPath);
      event.respondWith(
        fetch('/' + fallback).then(r =>
          new Response(r.body, {
            status: 200,
            headers: {
              'Content-Type': 'application/vnd.api+json',
              'Access-Control-Allow-Origin': '*',
              'Access-Control-Allow-Credentials': 'true'
            }
          })
        )
      );
      return;
    }

    // Fallback generico — risposta vuota JSON:API
    console.log('[SW] API no match (empty response):', url.pathname + url.search);
    event.respondWith(new Response(
      JSON.stringify({ data: [] }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/vnd.api+json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    ));
    return;
  }

  // 4. CORS preflight
  if (event.request.method === 'OPTIONS') {
    event.respondWith(new Response('', {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept',
        'Access-Control-Max-Age': '86400'
      }
    }));
    return;
  }

  // 5. Asset da app.sibill.com → serve localmente
  if (hostname === 'app.sibill.com' || hostname === location.hostname) {
    const assetRoute = config.assetRoutes[event.request.url];
    if (assetRoute) {
      event.respondWith(fetch('/' + assetRoute));
      return;
    }

    // Prova il path diretto (per risorse relative)
    if (url.pathname.startsWith('/assets/')) {
      event.respondWith(fetch(url.pathname));
      return;
    }
  }

  // 6. Font Google → serve locali
  if (hostname.includes('fonts.googleapis.com')) {
    console.log('[SW] Font CSS → local');
    event.respondWith(fetch('/fonts/public-sans.css'));
    return;
  }
  if (hostname.includes('fonts.gstatic.com')) {
    console.log('[SW] Font file → local');
    event.respondWith(fetch('/fonts/public-sans.woff2'));
    return;
  }

  // 7. EventSource/SSE → blocca (l'app gestisce gracefully)
  if (event.request.headers.get('accept')?.includes('text/event-stream')) {
    event.respondWith(new Response('', { status: 204 }));
    return;
  }

  // 8. Fallback generico — prova a servire localmente, altrimenti 204
  if (hostname === location.hostname) {
    // Risorsa locale — lascia passare al server HTTP
    return;
  }

  // Risorsa esterna non mappata — blocca silenziosamente
  event.respondWith(new Response('', { status: 204 }));
});
"""

    sw_path = OFFLINE_DIR / 'sw.js'
    sw_path.write_text(sw_code, encoding='utf-8')
    print(f'  sw.js: {sw_path}')


def generate_index_html(localStorage_data: dict):
    """Genera index.html con bootstrap SW e localStorage pre-population."""
    print('\nGenerazione index.html...')

    # Leggi l'HTML originale
    if not INDEX_HTML_PATH.exists():
        print(f'  ERRORE: {INDEX_HTML_PATH} non trovato!')
        sys.exit(1)

    html = INDEX_HTML_PATH.read_text(encoding='utf-8')

    # Redatta dati sensibili nel localStorage
    safe_storage = {}
    for key, value in localStorage_data.items():
        if value is None:
            continue
        # Redatta token e credenziali
        if any(sensitive in key.lower() for sensitive in ['token', 'auth', 'password', 'credential']):
            # Mantieni la chiave ma redatta il valore se sembra un token
            if len(str(value)) > 50:
                safe_storage[key] = 'OFFLINE_MODE_TOKEN'
            else:
                safe_storage[key] = value
        else:
            safe_storage[key] = value

    # Script di bootstrap da iniettare
    bootstrap_script = f"""
<script>
// === OFFLINE MODE BOOTSTRAP ===
// Pre-popola localStorage con lo stato catturato
(function() {{
  var OFFLINE_STORAGE = {json.dumps(safe_storage, ensure_ascii=False)};
  Object.keys(OFFLINE_STORAGE).forEach(function(key) {{
    try {{
      localStorage.setItem(key, OFFLINE_STORAGE[key]);
    }} catch(e) {{}}
  }});
  console.log('[OFFLINE] localStorage pre-populated with', Object.keys(OFFLINE_STORAGE).length, 'keys');
}})();

// Registra Service Worker
if ('serviceWorker' in navigator) {{
  navigator.serviceWorker.register('/sw.js').then(function(reg) {{
    console.log('[OFFLINE] Service Worker registered');
    if (reg.active) {{
      console.log('[OFFLINE] SW already active');
      return;
    }}
    var sw = reg.installing || reg.waiting;
    if (sw) {{
      sw.addEventListener('statechange', function() {{
        if (sw.state === 'activated') {{
          console.log('[OFFLINE] SW activated — reloading');
          location.reload();
        }}
      }});
    }}
  }}).catch(function(err) {{
    console.error('[OFFLINE] SW registration failed:', err);
  }});
}}
</script>
"""

    # Inietta il bootstrap come PRIMO elemento in <head>
    html = html.replace('<head>', f'<head>\n{bootstrap_script}', 1)

    # Sostituisci Google Fonts CDN con versione locale
    html = re.sub(
        r'<link[^>]*href="https://fonts\.googleapis\.com[^"]*"[^>]*>',
        '<link rel="stylesheet" href="/fonts/public-sans.css">',
        html
    )

    # Rimuovi script di tracking inline noti
    tracking_patterns = [
        r'<script[^>]*satismeter[^>]*>.*?</script>',
        r'<script[^>]*hotjar[^>]*>.*?</script>',
        r'<script[^>]*customer\.io[^>]*>.*?</script>',
        r'<script[^>]*intercom[^>]*>.*?</script>',
        r'<script[^>]*gist\.build[^>]*>.*?</script>',
        r'<script[^>]*google-analytics[^>]*>.*?</script>',
        r'<script[^>]*googletagmanager[^>]*>.*?</script>',
        r'<script[^>]*segment[^>]*>.*?</script>',
        r'<script[^>]*facebook[^>]*>.*?</script>',
        r'<script[^>]*linkedin[^>]*>.*?</script>',
    ]
    for pattern in tracking_patterns:
        html = re.sub(pattern, '', html, flags=re.DOTALL | re.IGNORECASE)

    # Riscrivi path degli asset da app.sibill.com a relativi
    html = html.replace('https://app.sibill.com/assets/', '/assets/')

    # Salva
    output_path = OFFLINE_DIR / 'index.html'
    output_path.write_text(html, encoding='utf-8')
    print(f'  index.html: {output_path} ({output_path.stat().st_size / 1024:.0f} KB)')


def print_summary():
    """Stampa un riepilogo del pacchetto generato."""
    print('\n' + '=' * 60)
    print('PACCHETTO OFFLINE GENERATO')
    print('=' * 60)

    total_size = 0
    for root, dirs, files in os.walk(OFFLINE_DIR):
        for file in files:
            filepath = Path(root) / file
            size = filepath.stat().st_size
            total_size += size

    print(f'\nDirectory: {OFFLINE_DIR}')
    print(f'Dimensione totale: {total_size / 1024 / 1024:.1f} MB')

    # Conta per tipo
    assets = list((OFFLINE_DIR / 'assets').glob('*')) if (OFFLINE_DIR / 'assets').exists() else []
    apis = list((OFFLINE_DIR / 'api-responses').glob('*')) if (OFFLINE_DIR / 'api-responses').exists() else []
    fonts = list((OFFLINE_DIR / 'fonts').glob('*')) if (OFFLINE_DIR / 'fonts').exists() else []

    print(f'\nFile:')
    print(f'  index.html + sw.js + sw-config.json')
    print(f'  assets/: {len(assets)} file (JS, CSS, immagini)')
    print(f'  api-responses/: {len(apis)} file (risposte API)')
    print(f'  fonts/: {len(fonts)} file')

    print(f'\nPer avviare:')
    print(f'  cd {OFFLINE_DIR}')
    print(f'  python3 -m http.server 8080')
    print(f'  Apri http://localhost:8080 nel browser')


def main():
    print('=' * 60)
    print('BUILD OFFLINE PACKAGE — Sibill Cashflow')
    print('=' * 60)

    # Verifica prerequisiti
    if not HAR_PATH.exists():
        print(f'\nERRORE: {HAR_PATH} non trovato!')
        print('Esegui prima: node capture/capture-cashflow.js')
        sys.exit(1)

    if not INDEX_HTML_PATH.exists():
        print(f'\nERRORE: {INDEX_HTML_PATH} non trovato!')
        sys.exit(1)

    # Carica localStorage
    localStorage_data = {}
    if LOCALSTORAGE_PATH.exists():
        with open(LOCALSTORAGE_PATH, 'r', encoding='utf-8') as f:
            localStorage_data = json.load(f)

    # Crea directory
    ensure_dirs()

    # Step 1: Parsing HAR
    entries = parse_har(HAR_PATH)

    # Step 2: Estrazione asset
    assets_map = extract_assets(entries)

    # Step 3: Estrazione API
    api_routes, path_fallbacks = extract_api_responses(entries)

    # Step 4: Generazione sw-config.json
    generate_sw_config(api_routes, path_fallbacks, assets_map)

    # Step 5: Generazione sw.js
    generate_service_worker()

    # Step 6: Generazione index.html
    generate_index_html(localStorage_data)

    # Riepilogo
    print_summary()


if __name__ == '__main__':
    main()
