# Riproduzione Offline — Sibill Full Site

Replica offline interattiva di **tutte le 23 sezioni** di Sibill.
L'app React originale gira localmente con un Service Worker che intercetta ogni richiesta HTTP e serve risposte pre-registrate (dati congelati).

## Quick Start

Se il pacchetto `offline/` è già stato generato:

```bash
./serve.sh
# oppure: cd offline && python3 -m http.server 8080
```

Apri `http://localhost:8080` nel browser.

## Generazione Completa (da zero)

### 1. Cattura (richiede accesso a Sibill)

```bash
cd /Users/nicolascarpa/Desktop/Progetti/sibill-re
node screens/offline/capture/capture-site.js
```

Lo script:
- Effettua login a Sibill
- Naviga **tutte le 23 pagine** (cashflow, movimenti, fatture, scadenzario, ecc.)
- Per ogni pagina: interagisce con elementi UI (tab, righe espandibili, pannelli laterali)
- Per cashflow: interazioni specifiche (toggle filtri, click grafici)
- Registra un HAR completo con tutti i response body (JS, CSS, API, font)
- Salva HTML, localStorage, sessionStorage e screenshot per ogni pagina

Output in `captured/`:
- `har-complete.har` — HAR con tutti i body
- `index.html` — HTML della pagina
- `localStorage.json` — stato localStorage
- `sessionStorage.json` — stato sessionStorage
- `screenshots/` — uno screenshot per ogni pagina
- `capture-report.json` — report della navigazione

### 2. Build pacchetto offline

```bash
python3 screens/offline/build/build-offline.py
```

Lo script:
- Parsa il HAR
- Estrae asset statici (JS, CSS, immagini)
- Estrae risposte API e le redatta (rimuove token/credenziali)
- **Auto-discovery font**: estrae TUTTI i font da Google Fonts (non solo Public Sans)
- Genera il Service Worker (`sw.js`)
- Genera la mappa di routing (`sw-config.json`)
- Modifica `index.html` con il bootstrap del SW

Output in `offline/`:
- `index.html` — con bootstrap SW e localStorage pre-popolato
- `sw.js` — Service Worker
- `sw-config.json` — mappa URL → file locale
- `assets/` — JS, CSS, immagini
- `api-responses/` — risposte API congelate
- `fonts/` — font locali (auto-discovery)

### 3. Avvio

```bash
./serve.sh
```

## Sezioni incluse

| # | Sezione | Path |
|---|---------|------|
| 1 | Cashflow | `/cashflow` |
| 2 | Categorie Cashflow | `/cashflow/categories` |
| 3 | Movimenti Bancari | `/transactions/movements` |
| 4 | Pagamenti | `/transactions/payments` |
| 5 | Regole Categorizzazione | `/transactions/rules` |
| 6 | Riconciliazioni | `/reconciliations` |
| 7 | Conti Bancari | `/accounts` |
| 8 | Scadenzario | `/outstanding` |
| 9 | Ricorrenze Ricevute | `/outstanding/recurrences/received` |
| 10 | Ricorrenze Emesse | `/outstanding/recurrences/issued` |
| 11 | Regole Scadenzario | `/outstanding/rules` |
| 12 | Dashboard Fatture | `/invoices/dashboard` |
| 13 | Fatture Emesse | `/invoices/issued` |
| 14 | Fatture Ricevute | `/invoices/received` |
| 15 | Corrispettivi | `/invoices/bills` |
| 16 | Controparti | `/counterparts` |
| 17 | Profilo Fatturazione | `/invoices/profile/company-data` |
| 18 | Default Fatturazione | `/invoices/profile/defaults` |
| 19 | Crea Fattura | `/invoices/info` |
| 20 | Import Fatture | `/invoices/import` |
| 21 | F24 | `/f24` |
| 22 | Team | `/settings/team` |
| 23 | Referral | `/referral` |

## Come funziona

```
Browser → Service Worker (sw.js)
              ├── Navigation → index.html (SPA routing per tutte le sezioni)
              ├── app.sibill.com/assets/* → file locali JS/CSS
              ├── api.sibill.com/* → JSON pre-registrati
              ├── fonts.googleapis.com → font CSS locali (auto-discovery)
              ├── fonts.gstatic.com → font file locali (auto-discovery)
              ├── domini tracking → 204 (bloccati)
              └── tutto il resto → 204 fallback
```

Il Service Worker intercetta **tutte** le richieste HTTP prima che lascino il browser. Le API rispondono con i dati catturati durante la sessione. L'app React gira identica a quella live, ma con dati congelati.

La navigazione tra sezioni funziona normalmente grazie al SPA routing: ogni request di navigazione serve lo stesso `index.html`, e React Router gestisce il routing client-side.

## Prerequisiti

- **Node.js** + **Playwright** (`npm i playwright`) — per la cattura
- **Python 3** — per il build e il server
- **Credenziali Sibill** in `credenziali.env` alla root del progetto — per la cattura

## Struttura

```
screens/offline/
├── capture/
│   └── capture-site.js              # Script Playwright per cattura (23 pagine)
├── build/
│   └── build-offline.py             # Genera il pacchetto offline
├── captured/                        # Dati grezzi (gitignored)
│   ├── har-complete.har
│   ├── index.html
│   ├── localStorage.json
│   ├── sessionStorage.json
│   ├── capture-report.json
│   └── screenshots/
├── offline/                         # Pacchetto servibile
│   ├── index.html
│   ├── sw.js
│   ├── sw-config.json
│   ├── assets/
│   ├── api-responses/
│   └── fonts/
├── serve.sh                         # Avvio rapido
└── README.md                        # Questo file
```

## Differenze rispetto alla versione cashflow-only

| Aspetto | `screens/cashflow/` | `screens/offline/` |
|---------|--------------------|--------------------|
| Pagine | Solo `/cashflow` | Tutte le 23 sezioni |
| Interazioni | Specifiche cashflow | Generiche + specifiche cashflow |
| Font | Solo Public Sans (hardcoded) | Auto-discovery di tutti i font |
| Screenshot | Singolo | Uno per pagina |
| HAR atteso | ~18 MB | ~30-50 MB |

## Troubleshooting

**Il grafico non si vede:**
- Apri DevTools > Application > Service Workers — verifica che il SW sia registrato e attivo
- Se il SW è "waiting to activate", ricarica con Shift+Ctrl+R

**Console piena di errori 204:**
- Normale per i domini di tracking bloccati. Verifica che non ci siano errori su `api.sibill.com`

**Una sezione mostra dati vuoti:**
- Il SW serve `{data: []}` per API non catturate. Se la combinazione di filtri/parametri non era stata catturata, viene servita la risposta di fallback
- Controlla nella console del browser se ci sono `[SW] API no match` per quella sezione

**I filtri non cambiano i dati:**
- Il SW serve la risposta API più vicina ai parametri richiesti. Se la combinazione non era stata catturata, viene servita la risposta di fallback (stessi dati)

**Come ri-catturare con nuovi dati:**
1. Elimina `captured/` e `offline/`
2. Riesegui cattura + build
