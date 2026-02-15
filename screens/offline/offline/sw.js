// sw.js — Service Worker per Replay Offline Sibill (Full Site)
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
