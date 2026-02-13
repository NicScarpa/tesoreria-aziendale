# Documentazione API — Sibill

**Data analisi:** 10 febbraio 2026
**Base URL:** `https://api.sibill.com`
**Formato:** JSON:API (`application/vnd.api+json`)
**Autenticazione:** Cookie `_sibill_key` (httpOnly, secure)
**Richieste analizzate:** 800 API calls, 30 endpoint unici

---

## Indice

1. [Pattern comuni](#1-pattern-comuni)
2. [Autenticazione](#2-autenticazione)
3. [Conti bancari](#3-conti-bancari)
4. [Movimenti (Transazioni)](#4-movimenti-transazioni)
5. [Cashflow e Dashboard](#5-cashflow-e-dashboard)
6. [Categorie](#6-categorie)
7. [Fatture e Documenti](#7-fatture-e-documenti)
8. [Controparti (Clienti e Fornitori)](#8-controparti-clienti-e-fornitori)
9. [Pagamenti](#9-pagamenti)
10. [Riconciliazioni](#10-riconciliazioni)
11. [Ricorrenze (Scadenzario)](#11-ricorrenze-scadenzario)
12. [Impostazioni (Company, Team, Subscription)](#12-impostazioni-company-team-subscription)
13. [F24](#13-f24)
14. [Riepilogo endpoint](#14-riepilogo-endpoint)

---

## 1. Pattern comuni

### 1.1 Headers obbligatori

Tutte le richieste API osservate includono: Confidenza: 🟢 Alta

```
Accept: application/vnd.api+json
Content-Type: application/vnd.api+json
Cookie: _sibill_key=<session_token>
```

### 1.2 Filtro company obbligatorio

La quasi totalita' degli endpoint richiede il filtro company: Confidenza: 🟢 Alta

```
filter[company.id__eq]=<UUID>
```

Il UUID dell'azienda viene recuperato da `localStorage["sibill-company-id"]`.

### 1.3 Paginazione (cursor-based)

| Parametro | Tipo | Default | Descrizione |
|---|---|---|---|
| `page[size]` | integer | Variabile (20-100) | Elementi per pagina |
| `page[cursor]` | string | null | Token per pagina successiva |

La risposta include `meta.page.cursor` per la pagina successiva. Se `null`, non ci sono altre pagine.

Confidenza: 🟢 Alta

### 1.4 Operatori di filtro

| Operatore | Sintassi | Esempio |
|---|---|---|
| Uguale | `__eq` | `filter[status__eq]=ACTIVE` |
| Diverso | `__neq` | `filter[kind__neq]=VIRTUAL` |
| In lista | `__in` | `filter[status__in]=ACCEPTED,PENDING,FAILED` |
| Non in lista | `__notIn` | `filter[status__notIn]=AUTHORIZED,DISABLED` |
| Maggiore o uguale | `__gte` | `filter[date__gte]=2025-08-31T22:00:00.000Z` |
| Minore o uguale | `__lte` | `filter[date__lte]=2026-08-31T21:59:59.999Z` |
| E' vuoto/null | `__empty` | `filter[hiddenAt__empty]=true` |
| Contiene | `__contains` | `filter[types__contains]=BANKING` |

Supportano relazioni nested: `filter[account.hiddenAt__empty]=true`, `filter[consent.status__neq]=DISABLED`

Confidenza: 🟢 Alta

### 1.5 Ordinamento

```
sort=-date,-createdAt,-id
```
Prefisso `-` = discendente. Campi multipli separati da virgola.

Confidenza: 🟢 Alta

### 1.6 Include (eager loading relazioni)

```
include=consent.institution,allocations.category
```
Carica relazioni nested in una singola richiesta. Le entita' correlate appaiono nell'array `included` della risposta.

Confidenza: 🟢 Alta

---

## 2. Autenticazione

### POST /api/auth/login

**Descrizione:** Login utente con email e password.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | POST |
| **URL** | `https://api.sibill.com/api/auth/login` |
| **Occorrenze osservate** | 1 |

**Request body:**
```json
{
  "username": "email@esempio.it",
  "password": "[REDACTED]"
}
```

**Response (200 OK):**
```json
{
  "token": "[REDACTED]"
}
```

**Side effect:** il server imposta il cookie `_sibill_key` via `Set-Cookie`.

**Status osservati:** `200`

---

### POST /api/auth/logout

**Descrizione:** Logout e invalidazione sessione.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | POST |
| **URL** | `https://api.sibill.com/api/auth/logout` |

**Side effect:** il server invalida il cookie `_sibill_key`.

---

### GET /api/v1/users/me

**Descrizione:** Recupera il profilo dell'utente corrente con le aziende associate.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/users/me` |
| **Occorrenze osservate** | 124 |

**Query parameters:**

| Parametro | Tipo | Esempio | Obbligatorio |
|---|---|---|---|
| `include` | string | `companies,companies.companyIdentity,companies.companySettings` | No |

**Response (200 OK):** risorsa JSON:API di tipo `user`

| Campo | Tipo |
|---|---|
| `email` | string |
| `firstName` | string |
| `lastName` | string |
| `phone` | string |
| `referralCode` | string |
| `identificationStatus` | null/string |
| `createdAt` | datetime |
| `updatedAt` | datetime |

**Relazioni incluse:** `companies` (con `company-identity`, `company-settings`)

**Status osservati:** `200`, `401`

---

### GET /api/v1/users/token

**Descrizione:** Refresh/rinnovo del token di sessione.
**Confidenza:** 🟡 Media

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/users/token` |
| **Occorrenze osservate** | 60 |

**Response (200 OK):**
```json
{
  "token": "[REDACTED]"
}
```

**Status osservati:** `200`, `0` (cancellato/timeout)

**Note:** chiamato ad ogni navigazione di pagina come heartbeat per mantenere la sessione attiva.

---

### GET /api/v1/users/chat-token

**Descrizione:** Token per l'integrazione Intercom (chat di supporto).
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/users/chat-token` |
| **Occorrenze osservate** | 62 |

**Response (200 OK):**
```json
{
  "token": "[REDACTED]"
}
```

**Status osservati:** `200`, `0`

---

## 3. Conti bancari

### GET /api/v1/accounts

**Descrizione:** Lista dei conti bancari dell'azienda.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/accounts` |
| **Occorrenze osservate** | 27 |

**Query parameters:**

| Parametro | Tipo | Esempio | Obbligatorio |
|---|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` | Si |
| `include` | string | `consent.institution` | No |
| `page[size]` | integer | `100` | No |

**Response (200 OK):** collection JSON:API di tipo `account`

| Campo | Tipo | Descrizione |
|---|---|---|
| `nickname` | string | Nome del conto |
| `currency` | string | Valuta (es. "EUR") |
| `currentBalance` | `{currency, amount}` | Saldo contabile |
| `currentBalanceEur` | float | Saldo contabile in EUR |
| `availableBalance` | `{currency, amount}` | Saldo disponibile |
| `availableBalanceEur` | float | Saldo disponibile in EUR |
| `balanceDate` | datetime | Data ultimo saldo |
| `status` | string | Stato conto |
| `identifiers` | `[{type, value}]` | IBAN, BIC, etc. |
| `allowBalanceChange` | boolean | Modifica manuale saldo |
| `ignoreBalance` | boolean | Escludi da aggregati |
| `creditLimit` | null/dict | Fido bancario |
| `creditLimitEur` | null/float | Fido in EUR |
| `hiddenAt` | null/datetime | Se nascosto |
| `cashbackAgreedAt` | null/datetime | Accettazione cashback |
| `lastUpdatedAt` | datetime | Ultima sync |
| `createdAt` | datetime | Creazione |
| `updatedAt` | datetime | Aggiornamento |

**Relazioni:** `company` (belongs_to), `consent` (belongs_to)
**Included types:** `consent`, `institution`

**Status osservati:** `200`, `0`

---

### GET /api/v1/accounts/metadata

**Descrizione:** Saldi aggregati di tutti i conti.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/accounts/metadata` |
| **Occorrenze osservate** | 3 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `filter[ignoreBalance__eq]` | boolean | `false` |
| `filter[consent.status__neq]` | string | `DISABLED` |

**Response (200 OK):** (NON JSON:API standard)
```json
{
  "balances_converted": {
    "count": 2,
    "available": {"currency": "EUR", "amount": "10190.17"},
    "current": {"currency": "EUR", "amount": "12093.43"}
  },
  "balances": [
    {
      "count": 2,
      "available": {"currency": "EUR", "amount": "10190.17"},
      "current": {"currency": "EUR", "amount": "12093.43"}
    }
  ]
}
```

**Status osservati:** `200`

---

### GET /api/v1/consents

**Descrizione:** Lista dei consensi Open Banking (PSD2) dell'azienda.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/consents` |
| **Occorrenze osservate** | 211 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `filter[status__notIn]` | string | `AUTHORIZED,DISABLED` |
| `filter[for_consent.id__empty]` | boolean | `true` |
| `filter[institution.id__empty]` | boolean | valore |
| `filter[institution.types__contains]` | string | valore |
| `filter[purpose__eq]` | string | valore |
| `include` | string | `accounts` |
| `page[size]` | integer | `100` |

**Response (200 OK):** collection JSON:API di tipo `consent`

**Status osservati:** `200`, `0`

**Note:** l'alto numero di occorrenze (211) indica che questo endpoint viene chiamato frequentemente, probabilmente per verificare lo stato dei consensi bancari ad ogni navigazione.

---

### GET /api/v1/institutions

**Descrizione:** Catalogo degli istituti bancari disponibili.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/institutions` |
| **Occorrenze osservate** | 1 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[types__contains]` | string | `BANKING` |
| `filter[source__eq]` | string | `SWAN` |
| `page[size]` | integer | `20` |

**Response (200 OK):** collection JSON:API di tipo `institution`

| Campo | Tipo |
|---|---|
| `name` | string |
| `fullName` | null/string |
| `source` | string |
| `types` | list |
| `flags` | list |
| `hidden` | boolean |
| `iconUrl` | string |
| `logoUrl` | string |

**Status osservati:** `200`

**Note:** l'unico source osservato e' "SWAN" (provider Open Banking europeo).

---

### GET /api/v1/user-bank-accounts

**Descrizione:** Associazione utente-conto bancario (per gestione permessi).
**Confidenza:** 🟡 Media

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/user-bank-accounts` |
| **Occorrenze osservate** | 56 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[bankAccount.company.id__eq]` | UUID | `14196c00-...` |
| `filter[source__eq]` | string | valore |
| `filter[status__in]` | string | valore |
| `filter[user.id__eq]` | UUID | valore |
| `include` | string | valore |

**Status osservati:** `200`

---

### GET /api/v1/cards

**Descrizione:** Lista delle carte associate all'azienda.
**Confidenza:** 🟡 Media

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/cards` |
| **Occorrenze osservate** | 2 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `include` | string | `company` |
| `page[size]` | integer | `100` |

**Response (200 OK):** collection JSON:API (vuota nella sessione analizzata)
```json
{
  "data": [],
  "meta": {"page": {"size": 100, "cursor": null}, "has_created_card": false}
}
```

**Status osservati:** `200`

---

## 4. Movimenti (Transazioni)

### GET /api/v1/transactions

**Descrizione:** Lista dei movimenti bancari.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/transactions` |
| **Occorrenze osservate** | 3 |

**Query parameters:**

| Parametro | Tipo | Esempio | Obbligatorio |
|---|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` | Si |
| `filter[account.hiddenAt__empty]` | boolean | `true` | No |
| `filter[account.id__in]` | UUID (lista) | `fd828a13-...` | No |
| `sort` | string | `-date,-createdAt,-id` | No |
| `include` | string | (vedi sotto) | No |
| `page[size]` | integer | `50` | No |

**Include tipico (molto ricco):**
```
account,account.consent.institution,allocations,allocations.category,
allocations.subcategory,attachments,card,category,reconciliations,
subcategory,payment,payment.attachments
```

**Response (200 OK):** collection JSON:API di tipo `transaction`

**Status osservati:** `200`

---

### GET /api/v1/transactions/metadata

**Descrizione:** Metadati aggregati dei movimenti (totali, conteggi).
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/transactions/metadata` |
| **Occorrenze osservate** | 1 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `filter[account.id__in]` | UUID | `fd828a13-...` |

**Response (200 OK):** (NON JSON:API standard)
```json
{
  "total": 42,
  "totals": [{
    "currency": "EUR",
    "positive": {"currency": "EUR", "amount": "5645.30"},
    "negative": {"currency": "EUR", "amount": "-5181.79"}
  }],
  "totalsEur": {
    "currency": "EUR",
    "positive": {"currency": "EUR", "amount": "5645.30"},
    "negative": {"currency": "EUR", "amount": "-5181.79"}
  },
  "totalUncategorised": 7,
  "totalsEurSucceeded": {
    "currency": "EUR",
    "positive": {"currency": "EUR", "amount": "5645.30"},
    "negative": {"currency": "EUR", "amount": "-5181.79"}
  }
}
```

**Status osservati:** `200`

---

### GET /api/v1/transactions/reconciliations

**Descrizione:** Stato riconciliazione per un set di transazioni.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/transactions/reconciliations` |
| **Occorrenze osservate** | 2 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[id__in]` | UUID (lista) | `f60910f0-...,88be70e4-...,44091c7a-...` |
| `filter[verificationStatus__eq]` | string | `TO_VERIFY` |

**Response (200 OK):** (NON JSON:API standard)
```json
[
  {
    "transaction_id": "uuid-transazione",
    "flow_ids": ["uuid-flow"]
  }
]
```

**Status osservati:** `200`

**Note:** restituisce i match tra transazioni e flow (scadenze) per le transazioni da verificare.

---

## 5. Cashflow e Dashboard

### GET /api/v1/cashflow/chart

**Descrizione:** Dati per il grafico cashflow (saldi inizio/fine mese).
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/cashflow/chart` |
| **Occorrenze osservate** | 2 |

**Query parameters:**

| Parametro | Tipo | Esempio | Obbligatorio |
|---|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` | Si |
| `timezone` | string | `Europe/Rome` | Si |
| `from` | datetime | `2025-08-31T22:00:00.000Z` | Si |
| `to` | datetime | `2026-08-31T21:59:59.999Z` | Si |
| `includeBudgets` | boolean | `false` | No |
| `includeOverdue` | boolean | `false` | No |
| `includePastdue` | boolean | `false` | No |

**Response (200 OK):**
```json
{
  "data": [
    {
      "month": 9,
      "year": 2025,
      "balance": {
        "start": {"currency": "EUR", "amount": "15000.00"},
        "end": {"currency": "EUR", "amount": "12500.00"}
      }
    }
  ]
}
```

12 elementi (un mese per periodo selezionato).

**Status osservati:** `200`

---

### GET /api/v1/cashflow/table

**Descrizione:** Dati per la tabella cashflow (dettaglio entrate/uscite per mese e categoria).
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/cashflow/table` |
| **Occorrenze osservate** | 4 |

**Query parameters:**

| Parametro | Tipo | Esempio | Obbligatorio |
|---|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` | Si |
| `filter[date__gte]` | datetime | `2025-08-31T22:00:00.000Z` | Si |
| `filter[date__lte]` | datetime | `2026-08-31T21:59:59.999Z` | Si |
| `filter[hiddenAt__empty]` | boolean | `true` | No |
| `timezone` | string | `Europe/Rome` | Si |
| `includeBudgets` | boolean | `false` | No |
| `includeOverdue` | boolean | `false` | No |
| `includePastdue` | boolean | `false` | No |

**Response (200 OK):**
```json
{
  "data": [
    {
      "month": 9,
      "year": 2025,
      "is_inflow": true,
      "categoryId": null,
      "subcategoryId": null,
      "outstandingAmount": {"currency": "EUR", "amount": "0.00"},
      "pastdueAmount": {"currency": "EUR", "amount": "0.00"},
      "transactionsAmount": {"currency": "EUR", "amount": "5200.00"}
    }
  ]
}
```

35 elementi (combinazioni mese x inflow/outflow x categoria).

**Status osservati:** `200`

**Note:** i parametri `includeBudgets`, `includeOverdue`, `includePastdue` suggeriscono funzionalita' avanzate di previsione e gestione scaduti. Confidenza: 🟡 Media

---

## 6. Categorie

### GET /api/v1/categories

**Descrizione:** Lista delle categorie di transazione per l'azienda.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/categories` |
| **Occorrenze osservate** | 8 |

**Query parameters:**

| Parametro | Tipo | Esempio | Obbligatorio |
|---|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` | Si |
| `include` | string | `subcategories` | No |
| `page[size]` | integer | `100` | No |

**Response (200 OK):** collection JSON:API di tipo `category`

| Campo | Tipo | Descrizione |
|---|---|---|
| `name` | string | Nome categoria |
| `color` | string | Colore hex |

**Relazioni:** `company` (belongs_to), `subcategories` (has_many)
**Included types:** `subcategory` (con campo `name`)

6 categorie osservate con 8 sottocategorie.

**Status osservati:** `200`

---

## 7. Fatture e Documenti

### GET /api/v1/documents

**Descrizione:** Lista fatture e documenti fiscali.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/documents` |
| **Occorrenze osservate** | 3 |

**Query parameters:**

| Parametro | Tipo | Esempio | Obbligatorio |
|---|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` | Si |
| `filter[documentDirection__eq]` | string | `ISSUED` | No |
| `filter[documentType__in]` | string | `INVOICE,CREDIT_NOTE,DEBIT_NOTE,PARCEL,SELF_INVOICE` | No |
| `filter[status__in]` | string | `CREATED,SENT,DELIVERED,NOT_DELIVERED` | No |
| `include` | string | `flows,category,subcategory,counterpart` | No |
| `sort` | string | `-searchDate,-creationDate,-createdAt,-id` | No |
| `page[size]` | integer | `50` | No |

**Response (200 OK):** collection JSON:API di tipo `document`

| Campo | Tipo | Descrizione |
|---|---|---|
| `number` | string | Numero documento |
| `documentType` | string | INVOICE, CREDIT_NOTE, DEBIT_NOTE, PARCEL, SELF_INVOICE, BILL |
| `direction` | string | ISSUED / RECEIVED |
| `status` | string | CREATED, SENT, DELIVERED, NOT_DELIVERED, DRAFT, DISCARDED |
| `paymentStatus` | string | Stato pagamento |
| `grossAmount` | dict | Importo lordo |
| `vatAmount` | dict | IVA |
| `vatAmountCompensation` | dict | Compensazione IVA |
| `counterpartName` | string | Nome controparte |
| `counterpartIdentifier` | string | P.IVA / CF controparte |
| `isEInvoice` | boolean | Fattura elettronica |
| `eInvoiceType` | null/string | Tipo FE (TD01, etc.) |
| `format` | string | Formato documento |
| `source` | string | Fonte |
| `creationDate` | string | Data documento |
| `deliveryDate` | null/string | Data consegna |
| `deliveryStatus` | null/string | Stato consegna SDI |
| `detectionDatetime` | null/string | Data rilevamento auto |
| `isInflow` | boolean | E' un'entrata |
| `isFromRecurrence` | boolean | Da ricorrenza |
| `subjectToReverseCharge` | boolean | Reverse charge |
| `withholdingTax` | null/dict | Ritenuta d'acconto |
| `vatCollection` | null/string | Regime IVA |
| `hasAttachment` | boolean | Ha allegati |
| `lastEmail` | null/string | Ultima email |
| `notes` | null/string | Note |
| `editable` | boolean | Modificabile |
| `deletable` | boolean | Eliminabile |
| `duplicable` | boolean | Duplicabile |
| `hiddenAt` | null/datetime | Data nascondimento |
| `createdAt` | datetime | Creazione record |
| `updatedAt` | datetime | Aggiornamento |

**Relazioni:** `company` (belongs_to), `counterpart` (belongs_to), `flows` (has_many)
**Included types:** `counterpart`, `flow`

**Status osservati:** `200`

---

### GET /api/v1/documents-dashboard/summary

**Descrizione:** Riepilogo dashboard fatture (ricavi, costi, IVA, top clienti/fornitori).
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/documents-dashboard/summary` |
| **Occorrenze osservate** | 1 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `filter[creationDate__gte]` | date | `2026-01-01` |
| `filter[creationDate__lte]` | date | `2026-12-31` |
| `filter[documentType__in]` | string | `INVOICE,CREDIT_NOTE,DEBIT_NOTE,BILL,SELF_INVOICE,PARCEL` |
| `filter[status__notIn]` | string | `DRAFT,DISCARDED` |
| `filter[hiddenAt__empty]` | boolean | `true` |

**Response (200 OK):** (NON JSON:API standard)
```json
{
  "customers": [
    {
      "counterpartId": "uuid",
      "counterpartName": "Nome Cliente",
      "counterpartIdentifier": "P.IVA",
      "amount": {"currency": "EUR", "amount": "5000.00"},
      "amountPercentage": 25.5,
      "numberOfDocuments": 3
    }
  ],
  "suppliers": ["..."],
  "revenueSummary": {
    "data": [
      {
        "month": 1, "year": 2026,
        "revenuesAmount": {"currency": "EUR", "amount": "..."},
        "costsAmount": {"currency": "EUR", "amount": "..."},
        "vatDebitAmount": {"currency": "EUR", "amount": "..."},
        "vatCreditAmount": {"currency": "EUR", "amount": "..."}
      }
    ],
    "totals": {
      "revenuesAmount": {"currency": "EUR", "amount": "..."},
      "costsAmount": {"currency": "EUR", "amount": "..."},
      "netAmount": {"currency": "EUR", "amount": "..."}
    }
  },
  "taxesSummary": {
    "data": ["..."],
    "totals": {"...": "..."}
  }
}
```

**Status osservati:** `200`

---

### GET /api/v1/documents/metadata

**Descrizione:** Conteggi dei documenti per tipo.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/documents/metadata` |
| **Occorrenze osservate** | 1 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `filter[documentType__in]` | string | `INVOICE,CREDIT_NOTE,...` |

**Status osservati:** `200`

---

## 8. Controparti (Clienti e Fornitori)

### GET /api/v1/counterparts

**Descrizione:** Lista clienti e fornitori.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/counterparts` |
| **Occorrenze osservate** | 4 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `filter[kind__eq]` | string | `VIRTUAL` |
| `filter[kind__neq]` | string | `VIRTUAL` |
| `filter[parent.id__empty]` | boolean | `true` |
| `filter[contactEmail__empty]` | boolean | `false` |
| `include` | string | `receivedCategory,receivedSubcategory` |
| `page[size]` | integer | `50` |
| `sort` | string | valore |

**Response (200 OK):** collection JSON:API di tipo `counterpart`

**Note:** le controparti possono essere `VIRTUAL` (create automaticamente dai movimenti) o `REAL` (create manualmente o da fatture). Il filtro `parent.id__empty` suggerisce una struttura gerarchica (societa' madri/figlie).

**Status osservati:** `200`

---

### GET /api/v1/counterparts/metadata

**Descrizione:** Conteggio controparti filtrate.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/counterparts/metadata` |
| **Occorrenze osservate** | 1 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `filter[kind__neq]` | string | `VIRTUAL` |
| `filter[parent.id__empty]` | boolean | `true` |
| `filter[contactEmail__empty]` | boolean | `false` |

**Response (200 OK):**
```json
{"total": 5}
```

**Status osservati:** `200`

---

### GET /api/v1/counterparts/suggested

**Descrizione:** Controparti suggerite (per auto-completamento).
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/counterparts/suggested` |
| **Occorrenze osservate** | 1 |

**Query parameters:** stessi di `/counterparts/metadata`

**Status osservati:** `200`

---

## 9. Pagamenti

### GET /api/v1/payments

**Descrizione:** Lista delle disposizioni di pagamento.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/payments` |
| **Occorrenze osservate** | 1 |

**Query parameters:**

| Parametro | Tipo | Esempio | Obbligatorio |
|---|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` | Si |
| `filter[status__in]` | string | `ACCEPTED,PENDING,FAILED,SUCCEEDED,TIMEOUT` | No |
| `sort` | string | `-createdAt` | No |
| `include` | string | `account,account.consent,account.consent.institution,counterpart,attachments,transactions,parent,retry_attempts` | No |
| `page[size]` | integer | `50` | No |

**Response (200 OK):** collection JSON:API

**Status possibili dei pagamenti:**

| Status | Descrizione |
|---|---|
| `PENDING` | In attesa |
| `ACCEPTED` | Accettato |
| `SUCCEEDED` | Completato |
| `FAILED` | Fallito |
| `TIMEOUT` | Scaduto |

Confidenza: 🟢 Alta

---

### GET /api/v1/payments/metadata

**Descrizione:** Conteggio pagamenti per stato.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/payments/metadata` |
| **Occorrenze osservate** | 29 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `filter[status__in]` | string | `TIMEOUT` |

**Response (200 OK):**
```json
{"total": 0}
```

**Status osservati:** `200`, `0`

**Note:** l'alto numero di occorrenze (29) e il filtro su `TIMEOUT` suggeriscono che il frontend fa polling per controllare se ci sono pagamenti in timeout che richiedono attenzione. Confidenza: 🟡 Media

---

## 10. Riconciliazioni

### GET /api/v1/reconciliations/

**Descrizione:** Lista delle riconciliazioni automatiche.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/reconciliations/` |
| **Occorrenze osservate** | 3 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[id__in]` | UUID (lista) | `d5e7a653-...,17b114f2-...` |
| `include` | string | `transaction` |

**Response (200 OK):** collection JSON:API di tipo `reconciliation`

| Campo | Tipo | Descrizione |
|---|---|---|
| `status` | string | Stato riconciliazione |
| `source` | string | Fonte (AUTOMATIC, MANUAL) |
| `createdAt` | datetime | Data creazione |

**Relazioni:** `transaction` (belongs_to)
**Included types:** `transaction`

**Status osservati:** `200`

**Note:** le riconciliazioni vengono caricate tramite `filter[id__in]` (lista di UUID specifici), il che suggerisce che il frontend prima recupera i movimenti e poi chiede le riconciliazioni per quegli ID specifici. Confidenza: 🟢 Alta

---

## 11. Ricorrenze (Scadenzario)

### GET /api/v1/recurrences

**Descrizione:** Lista delle ricorrenze (pagamenti/incassi periodici).
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/recurrences` |
| **Occorrenze osservate** | 2 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `include` | string | `account,account.consent,account.consent.institution,category,subcategory` |
| `page[size]` | integer | `100` |

**Response (200 OK):** collection JSON:API (vuota nella sessione analizzata)

**Status osservati:** `200`

---

## 12. Impostazioni (Company, Team, Subscription)

### GET /api/v1/companies/

**Descrizione:** Lista di tutte le aziende dell'utente.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/companies/` |
| **Occorrenze osservate** | 1 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `include` | string | `companyIdentity,companySettings` |

**Response (200 OK):** collection JSON:API di tipo `company` (vedi dettaglio campi nel Data Model).

**Included types:** `company-identity`, `company-settings`

**Status osservati:** `200`

---

### GET /api/v1/companies/{id}

**Descrizione:** Dettaglio di una singola azienda.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/companies/{id}` |
| **Occorrenze osservate** | 123 |

**Path parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `id` | UUID | `14196c00-6ac1-4bab-9874-9b01c2fe17a7` |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `include` | string | `companyIdentity,companySettings` |
| `filter[id__eq]` | UUID | `14196c00-...` |

**Response (200 OK):** singola risorsa JSON:API di tipo `company`

**Meta:** `has_documents` (boolean)
**Included types:** `company-identity`, `company-settings`

**Status osservati:** `200`, `0`

**Note:** l'altissimo numero di occorrenze (123) indica che i dati azienda vengono ricaricati ad ogni navigazione di pagina.

---

### GET /api/v1/company-users

**Descrizione:** Lista degli utenti associati all'azienda (per gestione team).
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/company-users` |
| **Occorrenze osservate** | 2 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `include` | string | `user` |

**Response (200 OK):** collection JSON:API di tipo `company-user`

| Campo | Tipo |
|---|---|
| `role` | string |
| `status` | string |
| `features` | list |

**Relazioni:** `company` (belongs_to), `user` (belongs_to)
**Included types:** `user`

**Status osservati:** `200`

---

### GET /api/v1/subscriptions

**Descrizione:** Stato dell'abbonamento dell'azienda.
**Confidenza:** 🟢 Alta

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **URL** | `https://api.sibill.com/api/v1/subscriptions` |
| **Occorrenze osservate** | 61 |

**Query parameters:**

| Parametro | Tipo | Esempio |
|---|---|---|
| `filter[company.id__eq]` | UUID | `14196c00-...` |
| `page[size]` | integer | valore |

**Response (200 OK):** collection JSON:API di tipo `subscription`

| Campo | Tipo |
|---|---|
| `status` | string (es. "TRIAL") |
| `externalId` | string |
| `createdAt` | datetime |
| `updatedAt` | datetime |

**Status osservati:** `200`, `0`

---

## 13. F24

La sezione F24 e' stata visitata ma **non sono state catturate chiamate API specifiche** nella sessione analizzata. La pagina contiene FAQ statiche e un pulsante "Paga F24". Confidenza: 🟡 Media

Il servizio di pagamento F24 potrebbe utilizzare endpoint non ancora scoperti (probabilmente attivati solo quando si effettua un pagamento reale).

---

## 14. Riepilogo endpoint

| # | Metodo | Endpoint | Sezione | Occorrenze | Confidenza |
|---|---|---|---|---|---|
| 1 | POST | `/api/auth/login` | Autenticazione | 1 | 🟢 Alta |
| 2 | POST | `/api/auth/logout` | Autenticazione | n/d | 🟢 Alta |
| 3 | GET | `/api/v1/users/me` | Autenticazione | 124 | 🟢 Alta |
| 4 | GET | `/api/v1/users/token` | Autenticazione | 60 | 🟡 Media |
| 5 | GET | `/api/v1/users/chat-token` | Autenticazione | 62 | 🟢 Alta |
| 6 | GET | `/api/v1/accounts` | Conti | 27 | 🟢 Alta |
| 7 | GET | `/api/v1/accounts/metadata` | Conti | 3 | 🟢 Alta |
| 8 | GET | `/api/v1/consents` | Conti | 211 | 🟢 Alta |
| 9 | GET | `/api/v1/institutions` | Conti | 1 | 🟢 Alta |
| 10 | GET | `/api/v1/user-bank-accounts` | Conti | 56 | 🟡 Media |
| 11 | GET | `/api/v1/cards` | Conti | 2 | 🟡 Media |
| 12 | GET | `/api/v1/transactions` | Movimenti | 3 | 🟢 Alta |
| 13 | GET | `/api/v1/transactions/metadata` | Movimenti | 1 | 🟢 Alta |
| 14 | GET | `/api/v1/transactions/reconciliations` | Movimenti | 2 | 🟢 Alta |
| 15 | GET | `/api/v1/cashflow/chart` | Cashflow | 2 | 🟢 Alta |
| 16 | GET | `/api/v1/cashflow/table` | Cashflow | 4 | 🟢 Alta |
| 17 | GET | `/api/v1/categories` | Categorie | 8 | 🟢 Alta |
| 18 | GET | `/api/v1/documents` | Fatture | 3 | 🟢 Alta |
| 19 | GET | `/api/v1/documents-dashboard/summary` | Fatture | 1 | 🟢 Alta |
| 20 | GET | `/api/v1/documents/metadata` | Fatture | 1 | 🟢 Alta |
| 21 | GET | `/api/v1/counterparts` | Controparti | 4 | 🟢 Alta |
| 22 | GET | `/api/v1/counterparts/metadata` | Controparti | 1 | 🟢 Alta |
| 23 | GET | `/api/v1/counterparts/suggested` | Controparti | 1 | 🟢 Alta |
| 24 | GET | `/api/v1/payments` | Pagamenti | 1 | 🟢 Alta |
| 25 | GET | `/api/v1/payments/metadata` | Pagamenti | 29 | 🟢 Alta |
| 26 | GET | `/api/v1/reconciliations/` | Riconciliazioni | 3 | 🟢 Alta |
| 27 | GET | `/api/v1/recurrences` | Ricorrenze | 2 | 🟢 Alta |
| 28 | GET | `/api/v1/companies/` | Impostazioni | 1 | 🟢 Alta |
| 29 | GET | `/api/v1/companies/{id}` | Impostazioni | 123 | 🟢 Alta |
| 30 | GET | `/api/v1/company-users` | Impostazioni | 2 | 🟢 Alta |
| 31 | GET | `/api/v1/subscriptions` | Impostazioni | 61 | 🟢 Alta |

**Totale:** 31 endpoint unici (29 GET + 2 POST)
**Richieste totali analizzate:** 800

### Endpoint non ancora scoperti (probabili)

Basandosi sulla struttura dell'applicazione e sulle entita' menzionate nella UI, questi endpoint potrebbero esistere ma non sono stati catturati nella sessione analizzata. Confidenza: 🔴 Bassa

| Endpoint probabile | Sezione | Motivazione |
|---|---|---|
| `POST /api/v1/transactions` | Movimenti | Creazione manuale movimenti |
| `PATCH /api/v1/transactions/{id}` | Movimenti | Modifica categoria, note, verificato |
| `POST /api/v1/payments` | Pagamenti | Creazione disposizione di pagamento |
| `POST /api/v1/documents` | Fatture | Creazione fattura |
| `PATCH /api/v1/documents/{id}` | Fatture | Modifica fattura |
| `DELETE /api/v1/documents/{id}` | Fatture | Eliminazione fattura |
| `POST /api/v1/counterparts` | Controparti | Creazione controparte |
| `PATCH /api/v1/counterparts/{id}` | Controparti | Modifica controparte |
| `POST /api/v1/recurrences` | Ricorrenze | Creazione ricorrenza |
| `POST /api/v1/reconciliations` | Riconciliazioni | Riconciliazione manuale |
| `POST /api/v1/consents` | Conti | Avvio nuovo consenso Open Banking |
| `POST /api/v1/categories` | Categorie | Creazione categoria |
| `PATCH /api/v1/categories/{id}` | Categorie | Modifica categoria |
| `GET/POST /api/v1/f24` | F24 | Gestione pagamenti F24 |
| `GET /api/v1/rules` | Regole | Regole di categorizzazione |
| `POST /api/v1/documents/import` | Fatture | Import fatture |
| `GET /api/v1/exports/*` | Esportazione | Download report/export |

**Note:** nella sessione catturata sono state osservate solo operazioni di lettura (GET). Le operazioni di scrittura (POST, PATCH, DELETE) richiederebbero azioni specifiche nell'interfaccia (creazione fattura, modifica movimento, etc.) che non sono state eseguite durante la fase di raccolta dati.
