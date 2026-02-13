# Direttiva 01 — Ricognizione Tecnica

## Obiettivo
Effettuare la ricognizione tecnica iniziale di Sibill (app.sibill.com) per identificare stack tecnologico, flusso di autenticazione, e struttura dell'applicazione.

## Pre-requisiti
- Credenziali in `credenziali.env`
- Playwright MCP attivo

## Procedura

### 1. Preparazione
- Abilitare network monitoring PRIMA di navigare
- Preparare directory output: `assets/screenshots/`, `assets/api-traces/`, `assets/js-sources/`

### 2. Login
1. Navigare a https://app.sibill.com/
2. Con network monitoring attivo, completare il login
3. Salvare TUTTE le richieste di rete del flusso login in `assets/api-traces/01-auth-flow.json`
4. Documentare:
   - Endpoint di login (URL, metodo, payload)
   - Tipo di token (JWT, session cookie, altro)
   - Endpoint di refresh token (se presente)
   - Durata sessione/token

### 3. Ispezione Post-Login
1. Ispezionare cookie: `document.cookie`
2. Ispezionare localStorage: `Object.keys(localStorage)`
3. Ispezionare sessionStorage: `Object.keys(sessionStorage)`
4. Catturare screenshot dashboard: `assets/screenshots/01-dashboard.png`

### 4. Identificazione Stack
1. Cercare nel DOM: `__NEXT_DATA__` (Next.js), `__NUXT__` (Nuxt), `ng-version` (Angular), `data-reactroot` (React)
2. Ispezionare tag `<script>` per identificare bundle principali
3. Cercare source maps (`.map` files)
4. Estrarre e salvare i file JS principali in `assets/js-sources/`

### 5. Cattura JS Sources
Per ogni file JS principale:
1. Ottenere l'URL dal DOM (`document.querySelectorAll('script[src]')`)
2. Scaricare il contenuto
3. Salvare in `assets/js-sources/` con nome significativo

## Output Attesi
- `assets/api-traces/01-auth-flow.json` — trace del flusso auth
- `assets/screenshots/01-dashboard.png` — screenshot dashboard
- `assets/js-sources/` — file JS principali
- `docs/02-auth-sessioni.md` (bozza) — documentazione autenticazione
- `.tmp/tech-stack.json` — stack tecnologico identificato

## Lezioni Apprese
(aggiornare man mano)
