# Riproduzione Offline — Sibill Cashflow

Replica offline interattiva della pagina `/cashflow` di Sibill.
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
node screens/cashflow/capture/capture-cashflow.js
```

Lo script:
- Effettua login a Sibill
- Naviga a `/cashflow`
- Interagisce con filtri, grafici, tabella e aside panel
- Registra un HAR completo con tutti i response body (JS, CSS, API, font)
- Salva HTML e localStorage

Output in `captured/`:
- `har-complete.har` — HAR con tutti i body
- `index.html` — HTML della pagina
- `localStorage.json` — stato localStorage

### 2. Build pacchetto offline

```bash
python3 screens/cashflow/build/build-offline.py
```

Lo script:
- Parsa il HAR
- Estrae asset statici (JS, CSS, font, immagini)
- Estrae risposte API e le redatta (rimuove token/credenziali)
- Genera il Service Worker (`sw.js`)
- Genera la mappa di routing (`sw-config.json`)
- Modifica `index.html` con il bootstrap del SW

Output in `offline/`:
- `index.html` — con bootstrap SW e localStorage pre-popolato
- `sw.js` — Service Worker
- `sw-config.json` — mappa URL → file locale
- `assets/` — JS, CSS, immagini
- `api-responses/` — risposte API congelate
- `fonts/` — font locali

### 3. Avvio

```bash
./serve.sh
```

## Come funziona

```
Browser → Service Worker (sw.js)
              ├── Navigation → index.html (SPA routing)
              ├── app.sibill.com/assets/* → file locali JS/CSS
              ├── api.sibill.com/* → JSON pre-registrati
              ├── fonts.googleapis.com → font locali
              ├── domini tracking → 204 (bloccati)
              └── tutto il resto → 204 fallback
```

Il Service Worker intercetta **tutte** le richieste HTTP prima che lascino il browser. Le API rispondono con i dati catturati durante la sessione. L'app React gira identica a quella live, ma con dati congelati.

## Prerequisiti

- **Node.js** + **Playwright** (`npm i playwright`) — per la cattura
- **Python 3** — per il build e il server
- **Credenziali Sibill** in `credenziali.env` alla root del progetto — per la cattura

## Struttura

```
screens/cashflow/
├── capture/
│   └── capture-cashflow.js       # Script Playwright per cattura
├── build/
│   └── build-offline.py          # Genera il pacchetto offline
├── captured/                     # Dati grezzi (gitignored)
├── offline/                      # Pacchetto servibile
│   ├── index.html
│   ├── sw.js
│   ├── sw-config.json
│   ├── assets/
│   ├── api-responses/
│   └── fonts/
├── serve.sh                      # Avvio rapido
└── README.md                     # Questo file
```

## Troubleshooting

**Il grafico non si vede:**
- Apri DevTools > Application > Service Workers — verifica che il SW sia registrato e attivo
- Se il SW è "waiting to activate", ricarica con Shift+Ctrl+R

**Console piena di errori 204:**
- Normale per i domini di tracking bloccati. Verifica che non ci siano errori su `api.sibill.com`

**I filtri non cambiano i dati:**
- Il SW serve la risposta API più vicina ai parametri richiesti. Se la combinazione di filtri non era stata catturata, viene servita la risposta di fallback (stessi dati)

**Come ri-catturare con nuovi dati:**
1. Elimina `captured/` e `offline/`
2. Riesegui cattura + build
