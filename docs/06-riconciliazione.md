# Riconciliazione Bancaria — Analisi Funzionale

**Data analisi:** 10 febbraio 2026
**Modulo:** Riconciliazione Bancaria
**URL principale:** `/reconciliations`

---

## Panoramica

Il modulo Riconciliazione e' il cuore operativo di Sibill per la gestione contabile. Il suo scopo e' **abbinare automaticamente i movimenti bancari (transazioni) con le scadenze/fatture (flow/document)**, verificando che ogni incasso o pagamento corrisponda a un documento contabile.

La riconciliazione puo' essere:
- **Automatica** — Il sistema propone match basandosi su regole di matching
- **Manuale** — L'utente conferma, corregge o crea match manualmente

---

## Interfaccia

### Layout Principale

La pagina `/reconciliations` si raggiunge dalla sidebar sotto "Transazioni > Riconciliazioni automatiche". Il layout presenta:

1. **Tabella riconciliazioni** — Lista delle riconciliazioni con stato, fonte, data creazione
2. **Filtri** — Per stato, periodo, conto
3. **Azioni** — Conferma, rifiuta, modifica match

### 🎨 PATTERN UI/UX — Verifica Transazioni

Il sistema utilizza un flag `verificationStatus` sulle transazioni:
- `TO_VERIFY` — Transazione con match proposto, da verificare
- La UI evidenzia le transazioni da verificare nella lista movimenti

L'endpoint `GET /api/v1/transactions/reconciliations` restituisce i match proposti per un set di transazioni filtrate per `verificationStatus__eq=TO_VERIFY`. 🟢

---

## Entita' e Dati

### Entita' Coinvolte

| Entita' | Ruolo nel Modulo | Rif. Data Model |
|---|---|---|
| `reconciliation` | Record di riconciliazione (match tra transaction e flow) | §2.12 |
| `transaction` | Movimento bancario da riconciliare | §3.4 |
| `document` | Fattura/documento contabile | §2.10 |
| `flow` | Scadenza di pagamento (legata al document) | §3.3 |
| `account` | Conto bancario di riferimento | §2.4 |

### Struttura dell'Entita' Reconciliation

| Campo | Tipo | Descrizione | Confidenza |
|---|---|---|---|
| `id` | UUID | Identificativo unico | 🟢 Alta |
| `status` | string | Stato della riconciliazione | 🟢 Alta |
| `source` | string | `AUTOMATIC` o `MANUAL` | 🟢 Alta |
| `createdAt` | datetime | Data creazione | 🟢 Alta |

**Relazione principale:** `transaction` (belongs_to) — ogni riconciliazione e' legata a una transazione.

### Dati Osservati

Dalle trace API osservate, le riconciliazioni vengono caricate con:
```
GET /api/v1/reconciliations/?filter[id__in]=uuid1,uuid2,...&include=transaction
```
Questo pattern indica che il frontend:
1. Carica i movimenti (`GET /api/v1/transactions`)
2. Dai movimenti, estrae gli ID delle riconciliazioni associate
3. Carica i dettagli delle riconciliazioni con le transazioni incluse

---

## Logiche di Business

### 📐 LB-RIC-01: Matching Transazione-Scadenza

Confidenza: 🟡 Media (la logica di matching e' server-side, non osservabile direttamente)

Il matching avviene tra:
- **Transazioni** (movimenti bancari dal conto)
- **Flow** (scadenze derivanti da fatture/documenti)

L'endpoint `GET /api/v1/transactions/reconciliations` restituisce:
```json
[
  {
    "transaction_id": "uuid-transazione",
    "flow_ids": ["uuid-flow"]
  }
]
```

Questo suggerisce un matching **1:N** (una transazione puo' essere abbinata a piu' flow/scadenze). 🟢

### 📐 LB-RIC-02: Criteri di Matching (Ipotizzati)

Confidenza: 🔴 Bassa (dedotto dal comportamento, non confermato da codice)

Basandosi sulle best practice del settore e sui dati osservati, i criteri probabili sono:

1. **Importo** — Match per importo esatto o con soglia di tolleranza
   - Matching 1:1 → importo transazione = importo flow
   - Matching 1:N → somma flow = importo transazione
   - Tolleranza possibile per differenze centesimali (commissioni, arrotondamenti)

2. **Controparte** — Abbinamento per nome/P.IVA controparte
   - La transazione contiene una descrizione con il nome della controparte
   - Il flow e' legato a un document che ha `counterpartName` e `counterpartIdentifier`

3. **Data** — Prossimita' temporale
   - Data della transazione vicina alla data di scadenza del flow
   - Tolleranza di qualche giorno (tipicamente 3-7 giorni nel settore)

4. **Conto bancario** — Stesso conto per transazione e flow

### 📐 LB-RIC-03: Fonte della Riconciliazione

Confidenza: 🟢 Alta

```
source:
  - "AUTOMATIC" → Match proposto automaticamente dal sistema
  - "MANUAL"    → Match confermato o creato manualmente dall'utente
```

### LB-RIC-04: Stato della Riconciliazione

Confidenza: 🟡 Media

Lo stato della riconciliazione indica se il match e' confermato, in attesa, o rifiutato. I valori esatti non sono stati osservati nelle trace, ma il campo `status` e' presente nell'entita'.

### LB-RIC-05: Verifica Transazioni

Confidenza: 🟢 Alta

Le transazioni hanno un campo `verificationStatus` che puo' essere:
- `TO_VERIFY` — la transazione ha un match proposto dal sistema ma non ancora verificato dall'utente

L'endpoint specifico `GET /api/v1/transactions/reconciliations` usa questo filtro:
```
filter[verificationStatus__eq]=TO_VERIFY
```

### LB-RIC-06: Riconciliazione nella Vista Movimenti

Confidenza: 🟢 Alta

Nella vista movimenti (`/transactions/movements`), le transazioni includono le riconciliazioni associate tramite `include=reconciliations`. Questo permette di mostrare nella tabella movimenti lo stato di riconciliazione di ogni transazione.

---

## API Coinvolte

| Endpoint | Metodo | Scopo | Rif. API |
|---|---|---|---|
| `/api/v1/reconciliations/` | GET | Lista riconciliazioni con filtri | §10 |
| `/api/v1/transactions/reconciliations` | GET | Match proposti per transazioni da verificare | §4 |
| `/api/v1/transactions` | GET | Lista movimenti (con include reconciliations) | §4 |

### Pattern di Chiamata Osservato

```
1. GET /api/v1/transactions?filter[company.id__eq]=UUID&include=...reconciliations...
   → Ottiene movimenti con riconciliazioni associate

2. GET /api/v1/transactions/reconciliations?filter[id__in]=uuid1,uuid2&filter[verificationStatus__eq]=TO_VERIFY
   → Ottiene match proposti per transazioni specifiche da verificare

3. GET /api/v1/reconciliations/?filter[id__in]=uuid1,uuid2&include=transaction
   → Carica dettagli riconciliazioni con transazioni incluse
```

---

## Filtri e Ricerca

| Filtro | Tipo | Descrizione | Confidenza |
|---|---|---|---|
| ID riconciliazione | Lista UUID | Filtra per ID specifici (`filter[id__in]`) | 🟢 Alta |
| Status verifica | Stringa | Filtra transazioni da verificare (`filter[verificationStatus__eq]`) | 🟢 Alta |
| Conto | Multi-select | Filtra per conto bancario | 🟡 Media |
| Periodo | Range date | Filtra per data | 🟡 Media |

---

## Azioni Disponibili

| Azione | Descrizione | Tipo | Confidenza |
|---|---|---|---|
| **Visualizza riconciliazioni** | Lista match automatici e manuali | Read | 🟢 Alta |
| **Verifica match** | Conferma un match proposto | Update | 🟡 Media |
| **Rifiuta match** | Rifiuta un match proposto | Update | 🟡 Media |
| **Riconciliazione manuale** | Crea un match manualmente | Create | 🟡 Media |
| **Rimuovi riconciliazione** | Elimina un match esistente | Delete | 🔴 Bassa |

> 🟡 **ATTENZIONE**: Le azioni di scrittura (POST, PATCH, DELETE) non sono state osservate nelle API traces perche' non sono state eseguite durante la sessione di analisi. La loro esistenza e' dedotta dalla logica dell'interfaccia.

---

## Limitazioni Osservate

1. **Dati limitati nel TRIAL:** L'account di test ha pochi movimenti e scadenze, rendendo difficile osservare il matching automatico in azione. 🟢

2. **Operazioni di scrittura non catturate:** Non sono state eseguite operazioni di riconciliazione manuale durante l'analisi, quindi gli endpoint POST/PATCH per la riconciliazione non sono documentati. 🟡

3. **Regole di riconciliazione:** Nella sidebar c'e' una sezione "Regole" (`/transactions/rules`) che probabilmente contiene regole di categorizzazione automatica e potenzialmente regole di matching per la riconciliazione. La relazione tra queste regole e il matching automatico non e' stata chiarita. 🟡

4. **Matching N:M:** Non e' stato possibile osservare scenari di matching N:M (piu' transazioni verso piu' flow). L'endpoint osservato suggerisce 1:N (una transazione, piu' flow), ma non e' chiaro se sia supportato anche N:1 o N:M. 🔴

---

## Note

- La riconciliazione e' strettamente integrata con il modulo movimenti. Le due sezioni condividono lo stesso include di riconciliazioni nelle query transazioni.
- Il pattern di caricamento "prima transazioni, poi riconciliazioni per ID" e' efficiente e suggerisce un'architettura backend ben progettata.
- L'entita' `flow` (scadenza di pagamento) e' il ponte tra i documenti/fatture e le transazioni bancarie. Un documento puo' avere piu' flow (es. pagamento rateale), e ogni flow puo' essere riconciliato con una transazione.
- La riconciliazione e' fondamentale per il calcolo delle "partite aperte" (scadenze non ancora pagate) che alimentano le previsioni di cassa nel modulo Cash Flow.
- Per un'analisi piu' approfondita dell'algoritmo di matching, sarebbe necessario analizzare il codice JavaScript della pagina riconciliazioni o eseguire operazioni di riconciliazione manuale per catturare gli endpoint di scrittura.

---

## Aggiornamento Fase 4 — Analisi JS Bundle (10/02/2026)

**Fonte:** Analisi del bundle JavaScript principale `index-N-OxfZQQ.js` (4.5 MB) e API traces.

### Stati della Riconciliazione (Confermati)

🟢 **Alta confidenza** — Estratti direttamente dalle definizioni enum nel JS.

#### Status della Riconciliazione (`y_`)

| Valore | Significato |
|--------|-------------|
| `VERIFIED` | Riconciliazione confermata/accettata |
| `REJECTED` | Riconciliazione rifiutata |

#### Source della Riconciliazione (`qS`)

| Valore | Significato | Label IT |
|--------|-------------|----------|
| `MANUAL` | Creata manualmente dall'utente | "Manuale" |
| `AUTOMATIC` | Generata automaticamente dal sistema | "Automatica" |
| `PROPOSAL` | Proposta dal sistema, in attesa di conferma | "Proposta" |
| `PAYMENT` | Generata da un pagamento (es. via Sibill Pay) | "Pagamento" |

**Tooltip di stato:**
- `AUTOMATIC` → "Automatically reconciled on {{date}}"
- `MANUAL` → "Manually reconciled on {{date}}"
- `PROPOSAL` → "Reconciled from a proposal on {{date}}"
- `PAYMENT` → "Reconciled via a payment on {{date}}"

#### Verification Status su Flow (`Ttn`)

| Valore | Significato |
|--------|-------------|
| `VERIFIED` | Flow verificato / "Verificato" |
| `TO_VERIFY` | Flow da verificare / "Da verificare" |

#### Verification Status su Transaction (`z6`)

| Valore | Significato |
|--------|-------------|
| `VERIFIED` | Transazione verificata |
| `TO_VERIFY` | Transazione da verificare |

> 📐 **FORMULA/ALGORITMO** — Il toggle verifica funziona cosi': se `verificationStatus === VERIFIED` → imposta `TO_VERIFY`, e viceversa. La mutation `Sar` chiama `Tae({id, verificationStatus})` per aggiornare lo stato. 🟢

---

### API di Riconciliazione (Complete)

🟢 **Alta confidenza** — Endpoint estratti dal codice JS con metodo, payload e logica.

#### Creazione Riconciliazione

```
POST /api/v1/reconciliations
Content-Type: application/vnd.api+json

Payload (JSON:API serialized):
{
  "data": {
    "type": "reconciliation",
    "attributes": {
      "status": "VERIFIED" | "REJECTED",
      "source": "MANUAL" | "AUTOMATIC" | "PROPOSAL" | "PAYMENT"
    },
    "relationships": {
      "company": { "data": { "type": "company", "id": "UUID" } },
      "flow": { "data": { "type": "flow", "id": "UUID" } },
      "transaction": { "data": { "type": "transaction", "id": "UUID" } }
    }
  }
}
```

#### Eliminazione Riconciliazione

```
DELETE /api/v1/reconciliations/{reconciliationId}
```

#### Lista Riconciliazioni (con paginazione infinita)

```
GET /api/v1/reconciliations
  include=flow,flow.document,transaction
  filter[companyId]=UUID
  page[size]=N, page[cursor]=...
```

#### Riconciliazioni per Transazioni TO_VERIFY

```
GET /api/v1/transactions/reconciliations
  filter[id__in]=uuid1,uuid2,...
  filter[verificationStatus__eq]=TO_VERIFY

Response:
[
  { "transaction_id": "UUID", "flow_ids": ["UUID", ...] }
]
```

#### Transazioni Raccomandate per Flow

Query key: `["Flows", flowId, "Recommended", ...]`
Il sistema propone transazioni bancarie da abbinare a un flow specifico. Il campo `recommendedReconciliationFlowId` nelle bookkeeping transactions collega una registrazione contabile a un flow suggerito per la riconciliazione. 🟢

---

### Logica di Conferma e Rifiuto Riconciliazione

🟢 **Alta confidenza** — Estratta dal codice delle mutations React Query.

#### Conferma Match (`ztr`)

```pseudocode
function confermaRiconciliazione(flowId, transactionId, source):
  // Crea la riconciliazione con status VERIFIED
  POST /api/v1/reconciliations {
    status: "VERIFIED",
    source: source,  // MANUAL o PROPOSAL
    company: companyId,
    flow: flowId,
    transaction: transactionId
  }

  // Tracking analytics
  if source == "MANUAL":
    track("RECONCILIATION_CREATED")
  elif source == "PROPOSAL":
    track("RECONCILIATION_MATCHED")

  // Invalida cache: riconciliazioni, cashflow, flows, outstanding chart
```

#### Rifiuto Proposta (`Utr`)

```pseudocode
function rifiutaProposta(flowId, transactionId):
  POST /api/v1/reconciliations {
    status: "REJECTED",
    source: "PROPOSAL",
    company: companyId,
    flow: flowId,
    transaction: transactionId
  }

  track("RECONCILIATION_REJECTED")
  // Invalida cache
```

#### Eliminazione Riconciliazione (`Vtr`)

```pseudocode
function eliminaRiconciliazione(reconciliationId):
  DELETE /api/v1/reconciliations/{reconciliationId}
  // Invalida cache
```

> 📐 **FORMULA/ALGORITMO** — Il rifiuto NON elimina la riconciliazione esistente: crea una NUOVA riconciliazione con status REJECTED e source PROPOSAL. L'eliminazione (DELETE) e' un'operazione separata. 🟢

---

### Dialog di Riconciliazione Manuale

🟢 **Alta confidenza** — Struttura estratta dai testi i18n nel JS.

**Titolo:** "Reconcile movement" / "Riconcilia movimento"

**Struttura del dialog:**

1. **Sezione Flow** — Dettagli della scadenza da riconciliare
   - Importo flow
   - Data scadenza (`Expire on`)

2. **Sezione Transaction** — Dettagli del movimento bancario
   - Riconciliazioni esistenti: `"{{count}} existing reconciliation(s)"`
   - Oppure: `"No reconciliation"`

3. **Ricerca movimenti** — "Search for movements to reconcile"
   - Risultati ricerca con azioni per-riga
   - Azioni riga: `Ignore` / `Reconcile` / `Selected`

4. **Proposte riconciliazione** — "Reconciliation proposals"
   - Movimenti suggeriti dal sistema

5. **Split payment** — Gestione importi diversi
   - Se l'importo della transazione != importo del flow:
     - `"A new flow will be created with the remaining amount"` → Crea nuova scadenza
     - `"The remaining amount will be added to the flow with payment date {{paymentDate}}"` → Aggiunge a flow esistente

6. **Riepilogo**
   - `Tot. reconciled` — totale riconciliato
   - `Lump sum` — pagamento unico
   - `Payment {{number}} of {{total}}` — pagamento frazionato

7. **Azioni**
   - `Riconcile` / `Riconcile transaction` — conferma
   - `Cancel` — annulla

**Messaggi di feedback:**
- Successo: `"Flow reconciled"` / `"Flow riconciliato"`
- Errore: `"There was an error during the flow reconciliation"`
- Errore rifiuto: `"Something went wrong during the reconciliation rejection"`

---

### Sezione Riconciliazione (Vista Dettaglio)

🟢 **Alta confidenza** — Struttura estratta dal componente `bat`.

La vista riconciliazioni e' un componente complesso con:

| Elemento | Label | Descrizione |
|----------|-------|-------------|
| `title` | "Reconciliations" / "Riconciliazioni" | Titolo sezione |
| `match` | "Accept" | Accetta la riconciliazione |
| `preview` | "Preview" | Anteprima |
| `partially_reconcile` | "Partially reconcile" | Riconciliazione parziale |
| `split` | "Split" | Divisione importo |
| `split_tooltip` | "The unpaid amount will be saved as a new deadline" | Tooltip split |
| `reconcile_amount` | "Amount to reconcile" | Importo da riconciliare |
| `dissociate` | "Dissociates" | Dissocia riconciliazione |
| `confirm` | "Confirm" | Conferma |
| `advance_amount` | "Advance" | Anticipo |
| `partial_reconciliation` | Partial reconciliation | Riconciliazione parziale |
| `remove_reconciliation` | Remove reconciliation | Rimuovi riconciliazione |

**Filtro per source:**
- "All reconciliations" / "{{ count }} selected"
- Filtri: Automatic, Manual, Proposal, Payment

**Proposta (`proposal`):** sezione dedicata alle proposte di riconciliazione.

---

### Split Payment — Riconciliazione Parziale

🟢 **Alta confidenza** — Estratta dal componente `Unt`.

Quando l'importo del movimento bancario e' diverso dall'importo della scadenza:

| Campo | Label | Descrizione |
|-------|-------|-------------|
| `flow_amount` | "Flow amount" | Importo originale della scadenza |
| `reconciliation_amount` | "Amount to reconcile" | Importo da riconciliare |
| `remaining_amount_new_flow` | "Remaining amount" | Importo residuo |
| `remaining_amount_info` | "The remaining import will be saved in a new flow" | Crea nuova scadenza con residuo |
| `remaining_amount_add_to_existing_flow` | "Add to existing due date with payment date {{paymentDate}} (flow {{flowIndex}} of {{flowsQuantity}})" | Aggiunge residuo a scadenza esistente |

> 📐 **FORMULA/ALGORITMO** — La riconciliazione parziale funziona cosi':
> 1. L'utente riconcilia una transazione con un flow di importo diverso
> 2. Il sistema calcola il residuo: `residuo = flow_amount - reconciliation_amount`
> 3. L'utente sceglie: creare un nuovo flow con il residuo, OPPURE aggiungerlo a un flow esistente dello stesso documento
> 4. Il nuovo flow eredita i dati del flow originale ma con l'importo residuo
>
> Questo supporta il pattern **1:N** (una transazione riconciliata con piu' flow parziali). 🟢

---

### Pattern di Matching 1:N, N:1 e Split

🟢 **Alta confidenza** — Confermato dalla struttura del dialog e delle API.

| Pattern | Supporto | Evidenza |
|---------|----------|----------|
| **1:1** | Si' | Match diretto transazione-flow |
| **1:N** | Si' | Una transazione puo' avere piu' riconciliazioni, con split payment |
| **N:1** | Si' | Un flow puo' avere piu' transazioni riconciliate (pagamento frazionato: "Payment {{number}} of {{total}}") |
| **N:M** | Composito | Combinazione di 1:N e N:1 tramite split payment |

Il campo `transaction_existing_reconciliations_one/other` nel dialog mostra quante riconciliazioni gia' esistono per una transazione, confermando il supporto N:1.

---

### Regole di Categorizzazione delle Transazioni

🟢 **Alta confidenza** — Struttura completa estratta dal JS.

Due sistemi di regole completamente separati:

#### 1. Transaction Rules (Regole Movimenti)

**Path:** `/transactions/rules`
**Sotto-sezioni:** Inflow rules / Outflow rules

**Criteri di matching (enum `FBn`):**

| Criterio | Codice | Descrizione |
|----------|--------|-------------|
| Keywords | `KEYWORDS` | Transazioni contenenti almeno una keyword |
| Account | `ACCOUNT` | Transazioni su un conto specifico |
| Counterparts | `COUNTERPARTS` | Transazioni con una controparte specifica |
| Transaction Type | `TYPE` | Transazioni di un tipo specifico |
| Document Type | `DOCUMENT_TYPE` | Tipo documento associato |
| Payment Method | `PAYMENT_METHOD` | Metodo di pagamento |

**Azioni disponibili (enum `jBn`):**

| Azione | Codice | Descrizione |
|--------|--------|-------------|
| Imposta categoria | `SET_CATEGORY` | Applica una categoria e sottocategoria |
| Nascondi | `HIDE` | Nascondi dalla lista movimenti |
| Imposta conto flow | `SET_ACCOUNT` | Imposta il conto della scadenza associata |
| Segna come verificato | `VERIFY` | Marca come verificato |
| Auto-riconciliazione | `AUTO_RECONCILIATION` | Crea e riconcilia automaticamente un movimento |

**Source regola (enum `BBn`):**
- `USER` — Creata dall'utente
- `PROPOSED` — Proposta dal sistema

**Entity type (enum `zBn`):**
- `TRANSACTION` — Regola sui movimenti
- `DOCUMENT` — Regola sui documenti

**Comportamento:**
- Le regole si applicano **nell'ordine visualizzato** (priorita' per posizione)
- Al salvataggio, l'utente sceglie se applicare anche allo storico:
  - "No, apply to future transactions only"
  - "Yes, update all matching transactions ({{total}})"
  - "Yes, update category of matching uncategorized transactions ({{total}})"

#### 2. Outstanding Rules (Regole Scadenze)

**Path:** `/outstanding/rules`
**Sotto-sezioni:** Received rules / Issued rules

**Criteri di matching:**

| Criterio | Descrizione |
|----------|-------------|
| Document Type | Tipo documento della scadenza |
| Payment Method | Metodo di pagamento della scadenza |
| Account | Conto bancario (default: tutti) |
| Direction | Direzione (Inflow/Outflow) |

**Azione principale:**

- **AUTO_RECONCILIATION** — "Create and Riconcile Transaction"
  - Quando una scadenza incontra i criteri, il sistema **crea automaticamente un movimento bancario e lo riconcilia** con la scadenza
  - Questo e' il cuore dell'automazione: elimina la necessita' di registrare manualmente i movimenti per scadenze ricorrenti

**Tabella regole:** Account | Document type | Payment method | Action | Owned by | Last edit

> 📐 **FORMULA/ALGORITMO** — La regola AUTO_RECONCILIATION delle Outstanding Rules e' il meccanismo piu' potente di automazione: quando una scadenza matcha i criteri (tipo documento + metodo pagamento + conto + direzione), il sistema crea UN NUOVO movimento bancario e lo riconcilia automaticamente con la scadenza. Questo bypassa completamente il flusso manuale. 🟢

---

### Invalidazione Cache Post-Riconciliazione

🟢 **Alta confidenza** — Estratta dal codice della mutation `Mne()`.

Dopo ogni operazione di riconciliazione (create/delete), vengono invalidate:

| Cache | Query Key | Motivo |
|-------|-----------|--------|
| Riconciliazioni | `g_.all` | Aggiorna lista riconciliazioni |
| Cashflow | `qo.all` | Ricalcola previsioni di cassa |
| Transactions | `va.all` | Aggiorna stato transazioni |
| Flows | `rd.all` | Aggiorna stato scadenze |
| Outstanding Chart | `PA.all` | Aggiorna grafico scadenze |

Questo conferma che la riconciliazione impatta **cinque aree dell'app**: riconciliazioni, cashflow, transazioni, flows e chart outstanding.

---

### Categorization Source delle Transazioni

🟢 **Alta confidenza** — Filtro disponibile nella UI.

| Source | Label | Descrizione |
|--------|-------|-------------|
| `automatic` | "Automatic" / "Automatica" | Categorizzazione automatica dal sistema |
| `user` | "Manual" / "Manuale" | Categorizzazione manuale dall'utente |
| `rules` | "Rules" / "Regole" | Categorizzazione da regole configurate |
| `other` | "Other" / "Altro" | Altra fonte |

---

### Bookkeeping Integration

🟡 **Media confidenza** — Osservata nella struttura JS ma non testata live.

Il sistema di registrazione contabile (bookkeeping) integra la riconciliazione:
- "Recommended reconciliation" appare come tooltip nelle righe della registrazione
- Il campo `recommendedReconciliationFlowId` nelle bookkeeping transactions suggerisce un flow per la riconciliazione automatica
- La registrazione contabile puo' essere creata direttamente dal dialog di riconciliazione (`"Create Transaction"` / `"Create movement"`)
