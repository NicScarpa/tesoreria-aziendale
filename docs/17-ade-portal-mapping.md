# Mapping Portale AdE (Fatture e Corrispettivi)

Questo progetto importa **Fatture** e **Corrispettivi** dal portale AdE usando automazione browser (Playwright).

Il portale puo' cambiare spesso: la parte di navigazione e download e' quindi *best-effort* e può richiedere
aggiustamenti (selettori, voci menu, bottoni export).

## Prerequisiti

1. Backend: Playwright installato

```bash
cd backend
pip install -r requirements.txt
python -m playwright install chromium
```

2. Credenziali configurate in app

- UI: `Integrazioni -> Agenzia Entrate` (CF + Password + PIN)

Nota: e' supportato solo l'inserimento credenziali via UI (cifrate in DB). E' possibile forzare un URL di login
alternativo via env (`ADE_LOGIN_URL`) oppure via `IntegrationConfig.config.ade_login_url`.

## Debug

Gli endpoint supportano `debug=true` (body per sync, query per test).

Quando `debug` e' attivo, il backend salva artefatti in:

- `uploads/ade_debug/<company_id>/<timestamp>/`
  - `*.png` screenshot
  - `*.html` sorgente pagina

Questo e' il modo piu' veloce per capire "dove si e' rotto" il flusso (CAPTCHA, portale cambiato, bottoni non trovati).

## Checklist di mapping (manuale)

Esegui questi passi nel browser (anche senza automazione) e annota:

1. **URL di ingresso**
   - pagina dove selezioni l'accesso con Entratel/Fisconline

2. **Dopo login**
   - c'e' una tile/link "Fatture e Corrispettivi"? Si apre in nuova pagina?

3. **Fatture**
   - percorso menu: `Consultazione -> Fatture emesse` / `Consultazione -> Fatture ricevute`
   - come imposti il range data (campo "Dal" / "Al")?
   - qual e' il bottone che genera il file (ZIP/XML)? testo esatto (es. "Scarica XML", "Esporta")?

4. **Corrispettivi**
   - percorso menu: `Consultazione -> Corrispettivi`
   - export produce un file per giorno? un ZIP? un JSON unico con lista? un CSV?

## Se serve stabilizzare (prossimo step)

L'attuale implementazione prova a navigare per testo (role/label) e a scaricare col primo bottone "Scarica/Download/Esporta".

Se non basta, il passo successivo e' rendere configurabili:

- URL diretti per "fatture emesse/ricevute" e "corrispettivi"
- selettori per campi data + bottone ricerca + bottone export

La UI puo' salvare questi valori dentro `IntegrationConfig.config` (tipo `agenzia_entrate`) e il backend li usera'
al posto delle euristiche.
