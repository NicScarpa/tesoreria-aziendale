#!/usr/bin/env python3
"""
Build Offline Package — Sibill Full Site

Trasforma i dati catturati (HAR + HTML + localStorage) nel pacchetto offline servibile.
Genera: offline/index.html, sw.js, sw-config.json, assets/, api-responses/, fonts/

Uso: python3 build/build-offline.py
Prerequisiti: prima eseguire capture/capture-site.js
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
    (re.compile(r'"password"\s*:\s*"[^"]*"'), '"password": "***"'),
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
    """Estrae asset statici (JS, CSS, immagini) e li salva."""
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

        # Favicon e altre immagini da app.sibill.com
        elif 'app.sibill.com' in hostname and any(path.endswith(ext) for ext in ['.png', '.svg', '.ico', '.jpg', '.jpeg', '.webp']):
            filename = path.split('/')[-1]
            local_path = OFFLINE_DIR / 'assets' / filename
            local_path.write_bytes(body)
            assets_map[url] = f'assets/{filename}'

    print(f'  Asset estratti: {len(assets_map)}')
    return assets_map


def extract_fonts(entries: list[dict]) -> dict:
    """
    Scarica i font Google Fonts usati dall'app direttamente dalla CDN.
    Rileva automaticamente le URL dei font CSS dal HAR, scarica il CSS fresco
    da Google Fonts (con User-Agent Chrome per ottenere woff2), poi scarica
    i file woff2 referenziati e aggiorna il CSS con path locali.
    """
    import urllib.request

    print('\nEstrazione font (download da Google Fonts)...')
    fonts_map = {}  # url_originale -> local_path

    # 1. Trova gli URL CSS di Google Fonts nel HAR
    google_font_css_urls = set()
    for entry in entries:
        url = entry['url']
        parsed = urlparse(url)
        if parsed.hostname and 'fonts.googleapis.com' in parsed.hostname:
            google_font_css_urls.add(url)

    if not google_font_css_urls:
        print('  Nessun font Google Fonts trovato nel HAR')
        return fonts_map

    print(f'  Trovati {len(google_font_css_urls)} CSS font nel HAR')

    # 2. Per ogni CSS font, scarica la versione fresca da Google Fonts
    # Chrome 110 UA per ottenere CSS con subset separati (latin, latin-ext, vietnamese)
    # Chrome 120+ restituisce un CSS minimalista con solo 2 URL variable-font
    chrome_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    all_woff2_urls = {}  # url_woff2 -> local_filename

    for css_url in google_font_css_urls:
        parsed = urlparse(css_url)
        params = parse_qs(parsed.query)
        family = params.get('family', ['fonts'])[0]
        css_name = family.split(':')[0].replace('+', '-').replace(' ', '-').lower()

        print(f'  Scaricamento CSS: {css_name}...')

        try:
            req = urllib.request.Request(css_url, headers={'User-Agent': chrome_ua})
            with urllib.request.urlopen(req, timeout=15) as resp:
                css_text = resp.read().decode('utf-8')
        except Exception as e:
            print(f'    ERRORE download CSS {css_url}: {e}')
            continue

        # 3. Estrai tutti gli URL woff2 dal CSS
        woff2_urls = re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)', css_text)
        unique_woff2 = list(dict.fromkeys(woff2_urls))  # preserva ordine, rimuovi duplicati

        print(f'    {len(unique_woff2)} file woff2 da scaricare')

        # 4. Scarica ogni file woff2 — usa il filename originale di Google
        for woff2_url in unique_woff2:
            local_filename = urlparse(woff2_url).path.split('/')[-1]
            local_path = OFFLINE_DIR / 'fonts' / local_filename

            if not local_path.exists() or local_path.stat().st_size == 0:
                try:
                    req = urllib.request.Request(woff2_url, headers={'User-Agent': chrome_ua})
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        local_path.write_bytes(resp.read())
                    print(f'    Scaricato: {local_filename} ({local_path.stat().st_size:,} bytes)')
                except Exception as e:
                    print(f'    ERRORE download {woff2_url}: {e}')
                    continue
            else:
                print(f'    Già presente: {local_filename}')

            all_woff2_urls[woff2_url] = local_filename
            fonts_map[woff2_url] = f'fonts/{local_filename}'

        # 5. Sostituisci gli URL nel CSS con i path locali
        for orig_url, local_name in all_woff2_urls.items():
            css_text = css_text.replace(orig_url, f'/fonts/{local_name}')

        # 6. Salva il CSS locale
        css_filename = f'{css_name}.css'
        css_path = OFFLINE_DIR / 'fonts' / css_filename
        css_path.write_text(css_text, encoding='utf-8')
        fonts_map[css_url] = f'fonts/{css_filename}'
        print(f'    CSS locale: {css_filename}')

    print(f'  Totale font map: {len(fonts_map)}')
    return fonts_map


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


def generate_sw_config(api_routes: dict, path_fallbacks: dict, assets_map: dict, fonts_map: dict):
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
        },
        'fontRoutes': {
            url: local_path for url, local_path in fonts_map.items()
        }
    }

    config_path = OFFLINE_DIR / 'sw-config.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f'  sw-config.json: {config_path} ({config_path.stat().st_size / 1024:.0f} KB)')


def generate_service_worker():
    """Genera sw.js — il Service Worker per il replay offline."""
    print('\nGenerazione sw.js...')

    sw_code = r"""// sw.js — Service Worker per Replay Offline Sibill (Full Site)
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
          Object.keys(c.assetRoutes).length, 'asset routes,',
          Object.keys(c.fontRoutes || {}).length, 'font routes');
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

  // 6. Font Google → serve locali (dynamic matching via config)
  if (hostname.includes('fonts.googleapis.com') || hostname.includes('fonts.gstatic.com')) {
    const fontRoutes = config.fontRoutes || {};
    const fontRoute = fontRoutes[event.request.url];
    if (fontRoute) {
      console.log('[SW] Font (exact match):', url.pathname, '→', fontRoute);
      event.respondWith(fetch('/' + fontRoute));
      return;
    }

    // Fallback: cerca per path parziale tra i font salvati
    const matchingFont = Object.entries(fontRoutes).find(([origUrl]) => {
      try {
        const origParsed = new URL(origUrl);
        return origParsed.hostname === hostname && origParsed.pathname === url.pathname;
      } catch(e) { return false; }
    });
    if (matchingFont) {
      console.log('[SW] Font (path match):', url.pathname, '→', matchingFont[1]);
      event.respondWith(fetch('/' + matchingFont[1]));
      return;
    }

    // Ultimo fallback: serve il primo font CSS o file disponibile
    const isCSS = hostname.includes('googleapis.com');
    const fallbackFont = Object.values(fontRoutes).find(p =>
      isCSS ? p.endsWith('.css') : (p.endsWith('.woff2') || p.endsWith('.woff'))
    );
    if (fallbackFont) {
      console.log('[SW] Font (type fallback):', url.pathname, '→', fallbackFont);
      event.respondWith(fetch('/' + fallbackFont));
      return;
    }

    // Nessun font disponibile — 204
    event.respondWith(new Response('', { status: 204 }));
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


def generate_index_html(localStorage_data: dict, fonts_map: dict):
    """Genera index.html con bootstrap SW e localStorage pre-population."""
    print('\nGenerazione index.html...')

    # Leggi l'HTML originale
    if not INDEX_HTML_PATH.exists():
        print(f'  ERRORE: {INDEX_HTML_PATH} non trovato!')
        sys.exit(1)

    html = INDEX_HTML_PATH.read_text(encoding='utf-8')

    # Copia tutto il localStorage as-is (i token servono all'app per funzionare)
    safe_storage = {k: v for k, v in localStorage_data.items() if v is not None}

    # Script di bootstrap da iniettare
    bootstrap_script = f"""
<script>
// === OFFLINE MODE BOOTSTRAP ===
// Strategia: blocca TUTTI gli script dell'app fino a quando il SW è controller.
// Al primo caricamento: registra SW, ricarica. Al secondo: SW è controller, app parte.

(function() {{
  'use strict';

  // --- 1. Blocca redirect a /logout ---
  var origPush = history.pushState.bind(history);
  var origReplace = history.replaceState.bind(history);
  history.pushState = function(state, title, url) {{
    if (url && url.toString().includes('/logout')) {{
      console.log('[OFFLINE] Blocked pushState to /logout');
      return;
    }}
    return origPush(state, title, url);
  }};
  history.replaceState = function(state, title, url) {{
    if (url && url.toString().includes('/logout')) {{
      console.log('[OFFLINE] Blocked replaceState to /logout');
      return;
    }}
    return origReplace(state, title, url);
  }};

  // --- 2. Pre-popola localStorage ---
  var OFFLINE_STORAGE = {json.dumps(safe_storage, ensure_ascii=False)};
  Object.keys(OFFLINE_STORAGE).forEach(function(key) {{
    try {{ localStorage.setItem(key, OFFLINE_STORAGE[key]); }} catch(e) {{}}
  }});
  console.log('[OFFLINE] localStorage pre-populated:', Object.keys(OFFLINE_STORAGE).length, 'keys');

  // --- 3. Registra SW e blocca/sblocca l'app ---
  // Gli script dell'app hanno type="offline-blocked" nell'HTML (non vengono eseguiti).
  // Questo bootstrap li sblocca SOLO dopo che il SW è controller.
  if (!('serviceWorker' in navigator)) {{
    console.error('[OFFLINE] Service Worker non supportato — sblocco app comunque');
    unblockAppScripts();
    return;
  }}

  function unblockAppScripts() {{
    // Sblocca i <link rel="offline-preload"> → modulepreload
    var blockedLinks = document.querySelectorAll('link[rel="offline-preload"]');
    console.log('[OFFLINE] Sblocco', blockedLinks.length, 'modulepreload links');
    blockedLinks.forEach(function(orig) {{
      var link = document.createElement('link');
      link.rel = 'modulepreload';
      link.crossOrigin = orig.crossOrigin || '';
      link.href = orig.href;
      orig.parentNode.insertBefore(link, orig);
      orig.remove();
    }});

    // Sblocca gli <script type="offline-blocked"> → module
    var blocked = document.querySelectorAll('script[type="offline-blocked"]');
    console.log('[OFFLINE] Sblocco', blocked.length, 'script dell\\'app');
    blocked.forEach(function(orig) {{
      var s = document.createElement('script');
      s.type = 'module';
      s.crossOrigin = orig.crossOrigin || '';
      if (orig.src) s.src = orig.src;
      if (orig.textContent) s.textContent = orig.textContent;
      orig.parentNode.insertBefore(s, orig.nextSibling);
      orig.remove();
    }});
  }}

  // Se il SW è già controller → sblocca l'app immediatamente
  if (navigator.serviceWorker.controller) {{
    console.log('[OFFLINE] SW già controller — sblocco app');
    unblockAppScripts();
    return;
  }}

  // SW NON è controller → registra e aspetta
  console.log('[OFFLINE] SW non controller — registro e aspetto...');

  // Mostra loading screen (gli script bloccati non produrranno UI)
  document.addEventListener('DOMContentLoaded', function() {{
    var root = document.getElementById('root');
    if (root) {{
      root.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;background:#f5f5f5;"><div style="text-align:center;"><div style="width:40px;height:40px;border:4px solid #ddd;border-top-color:#333;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 16px;"></div><p style="color:#666;">Inizializzazione modalit\\u00e0 offline...</p></div></div><style>@keyframes spin{{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}</style>';
    }}
  }});

  navigator.serviceWorker.register('/sw.js').then(function(reg) {{
    console.log('[OFFLINE] SW registrato');

    // Ascolta il messaggio controllerchange — questo scatta quando clients.claim() ha effetto
    navigator.serviceWorker.addEventListener('controllerchange', function() {{
      console.log('[OFFLINE] Controller cambiato — sblocco app');
      unblockAppScripts();
    }});

    // Se il SW è già active (ma non controller), clients.claim() lo renderà controller
    // e scatterà 'controllerchange' sopra
    if (reg.active) {{
      console.log('[OFFLINE] SW già active, aspetto controllerchange...');
      return;
    }}

    // Aspetta installazione → attivazione → controllerchange
    var sw = reg.installing || reg.waiting;
    if (sw) {{
      sw.addEventListener('statechange', function() {{
        console.log('[OFFLINE] SW state:', sw.state);
        // controllerchange gestirà lo sblocco
      }});
    }}
  }}).catch(function(err) {{
    console.error('[OFFLINE] Registrazione SW fallita:', err);
    // Sblocca comunque — meglio provare che restare sulla loading screen
    unblockAppScripts();
  }});
}})();
</script>
"""

    # Inietta il bootstrap come PRIMO elemento in <head>
    html = html.replace('<head>', f'<head>\n{bootstrap_script}', 1)

    # Sostituisci Google Fonts CDN con versioni locali
    # Raccogli tutti i CSS font locali generati
    local_font_css_files = [
        local_path for url, local_path in fonts_map.items()
        if local_path.endswith('.css')
    ]

    if local_font_css_files:
        # Sostituisci TUTTI i link a fonts.googleapis.com con i CSS locali
        # Prima rimuovi tutti i link font esistenti
        html = re.sub(
            r'<link[^>]*href="https://fonts\.googleapis\.com[^"]*"[^>]*/?>',
            '',
            html
        )
        # Poi aggiungi i link ai CSS locali in <head>
        font_links = '\n'.join(
            f'<link rel="stylesheet" href="/{css_file}">'
            for css_file in local_font_css_files
        )
        html = html.replace('<head>', f'<head>\n{font_links}', 1)

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

    # BLOCCA gli script dell'app: cambia type="module" in type="offline-blocked"
    # per gli script con src verso /assets/ (l'entry point React e i suoi chunk)
    # Il bootstrap li sbloccherà dopo che il SW è controller
    html = re.sub(
        r'<script\s+type="module"\s+crossorigin(?:="")?(\s+src="/assets/[^"]+")>',
        r'<script type="offline-blocked" crossorigin=""\1>',
        html
    )
    # Anche i <link rel="modulepreload"> devono essere bloccati (il browser li pre-carica ed esegue)
    # Li trasformiamo in <link rel="offline-preload"> per evitare il caricamento
    html = re.sub(
        r'<link\s+rel="modulepreload"\s+crossorigin(?:="")?(\s+href="/assets/[^"]+")>',
        r'<link rel="offline-preload" crossorigin=""\1>',
        html
    )

    # Salva
    output_path = OFFLINE_DIR / 'index.html'
    output_path.write_text(html, encoding='utf-8')
    print(f'  index.html: {output_path} ({output_path.stat().st_size / 1024:.0f} KB)')


def generate_server_script():
    """Genera server.py — server HTTP con SPA fallback routing."""
    print('\nGenerazione server.py...')

    server_code = '''#!/usr/bin/env python3
"""Server HTTP con SPA fallback — serve index.html per tutte le route non-file."""
import http.server
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Se il path corrisponde a un file reale, servilo
        file_path = os.path.join(DIRECTORY, self.path.lstrip('/'))
        if os.path.isfile(file_path):
            return super().do_GET()

        # Altrimenti, serve index.html (SPA routing)
        self.path = '/index.html'
        return super().do_GET()


if __name__ == '__main__':
    with http.server.HTTPServer(('', PORT), SPAHandler) as httpd:
        print(f'Sibill Offline — http://localhost:{PORT}')
        print('Premi Ctrl+C per fermare')
        httpd.serve_forever()
'''

    server_path = OFFLINE_DIR / 'server.py'
    server_path.write_text(server_code, encoding='utf-8')
    print(f'  server.py: {server_path}')


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
    print(f'  index.html + sw.js + sw-config.json + server.py')
    print(f'  assets/: {len(assets)} file (JS, CSS, immagini)')
    print(f'  api-responses/: {len(apis)} file (risposte API)')
    print(f'  fonts/: {len(fonts)} file')

    print(f'\nPer avviare:')
    print(f'  cd {OFFLINE_DIR}')
    print(f'  python3 server.py')
    print(f'  Apri http://localhost:8080 nel browser')


def main():
    print('=' * 60)
    print('BUILD OFFLINE PACKAGE — Sibill Full Site')
    print('=' * 60)

    # Verifica prerequisiti
    if not HAR_PATH.exists():
        print(f'\nERRORE: {HAR_PATH} non trovato!')
        print('Esegui prima: node capture/capture-site.js')
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

    # Step 2: Estrazione asset (senza font)
    assets_map = extract_assets(entries)

    # Step 3: Estrazione font (auto-discovery)
    fonts_map = extract_fonts(entries)

    # Step 4: Estrazione API
    api_routes, path_fallbacks = extract_api_responses(entries)

    # Step 5: Generazione sw-config.json (ora include fontRoutes)
    generate_sw_config(api_routes, path_fallbacks, assets_map, fonts_map)

    # Step 6: Generazione sw.js
    generate_service_worker()

    # Step 7: Generazione index.html
    generate_index_html(localStorage_data, fonts_map)

    # Step 8: Generazione server.py
    generate_server_script()

    # Riepilogo
    print_summary()


if __name__ == '__main__':
    main()
