# Direttiva 03 — Cattura API

## Obiettivo
Intercettare e documentare TUTTE le chiamate API dell'applicazione Sibill navigando ogni sezione con network monitoring attivo.

## Pre-requisiti
- Login completato (Direttiva 01)
- Network monitoring attivo
- Directory `assets/api-traces/` pronta

## Principi
1. **Network monitoring PRIMA di navigare** — Le SPA caricano dati via API al mount dei componenti
2. **Cattura TUTTO** — Anche le chiamate di lookup, autocomplete, validazione
3. **Documenta il trigger** — Quale azione UI ha provocato la chiamata
4. **Salva payload completi** — Request body + response body + headers

## Procedura per ogni sezione

### Per ogni pagina/sezione:
1. Abilitare network monitoring (se non già attivo)
2. Navigare alla sezione
3. Attendere caricamento completo (verificare che le API abbiano risposto)
4. Catturare le richieste di rete: `browser_network_requests`
5. Per ogni API trovata, documentare:
   - **URL** completo (base + path + query params)
   - **Metodo** HTTP (GET, POST, PUT, DELETE, PATCH)
   - **Headers** rilevanti (Authorization, Content-Type, custom headers)
   - **Request body** (se presente)
   - **Response body** (struttura JSON)
   - **Status code**
   - **Trigger UI** (caricamento pagina, click su bottone, filtro, etc.)

### Azioni aggiuntive per ogni sezione:
- Applicare filtri diversi e catturare come cambiano i query params
- Aprire form di creazione/modifica e catturare le API di lookup
- Cliccare su dettagli di un elemento e catturare le API di dettaglio
- Provare paginazione e catturare i pattern
- Tentare export e catturare l'endpoint di download

## Ordine di navigazione (priorità)
1. Dashboard
2. Tesoreria / Cash Flow
3. Conti Bancari
4. Movimenti
5. Fatturazione
6. Scadenzario
7. Riconciliazione
8. Pagamenti
9. Carte
10. Impostazioni / Configurazione

## Formato output per ogni sezione

Salvare in `assets/api-traces/XX-nome-sezione.json`:
```json
{
  "section": "Nome Sezione",
  "url": "https://app.sibill.com/path",
  "timestamp": "ISO 8601",
  "apis": [
    {
      "endpoint": "/api/v1/resource",
      "method": "GET",
      "trigger": "page load",
      "request": {
        "headers": {},
        "params": {},
        "body": null
      },
      "response": {
        "status": 200,
        "headers": {},
        "body": {}
      }
    }
  ]
}
```

## Pattern da identificare
- **Base URL API**: tipicamente `/api/v1/` o simile
- **Autenticazione**: Bearer token, cookie, API key
- **Paginazione**: offset/limit, cursor, page/pageSize
- **Filtri**: query params, body params
- **Ordinamento**: sort, orderBy
- **Errori**: struttura errori, codici custom

## Output Attesi
- `assets/api-traces/` — un file per sezione
- `.tmp/api-catalog.json` — catalogo aggregato di tutti gli endpoint
- `docs/04-api-reference.md` (bozza) — documentazione API

## Lezioni Apprese
(aggiornare man mano)
