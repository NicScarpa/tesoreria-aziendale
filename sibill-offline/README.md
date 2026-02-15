# Sibill Offline Replica

Replica congelata dell'applicazione Sibill (app.sibill.com).
Dati catturati il: 11/02/2026 23:44

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
