# Scadenzario — Analisi Funzionale

**Data analisi:** 10 febbraio 2026
**Modulo:** Scadenzario
**URL principale:** `/outstanding`
**URL ricorrenze pagamenti:** `/outstanding/recurrences/received`
**URL ricorrenze incassi:** `/outstanding/recurrences/issued`
**URL regole:** `/outstanding/rules`

---

## Panoramica

Lo Scadenzario e' il modulo di gestione delle scadenze attive (incassi da ricevere) e passive (pagamenti da effettuare). Fornisce una vista consolidata di tutte le scadenze legate ai documenti/fatture, con possibilita' di gestire ricorrenze e regole automatiche.

Il modulo si compone di tre sotto-sezioni accessibili tramite tab:
1. **Scadenzario** — Vista principale delle scadenze
2. **Ricorrenze** — Pagamenti/incassi periodici (con sotto-tab Pagamenti/Incassi)
3. **Regole** — Regole di automazione per lo scadenzario

---

## Interfaccia

### Tab di Navigazione

Il modulo usa un sistema a **tab** nella barra superiore:

```
[Scadenzario] [Ricorrenze] [Regole]
                  |
           [Pagamenti] [Incassi]
```

### 🎨 PATTERN UI/UX — Tab con Sotto-tab

Le ricorrenze hanno un ulteriore livello di navigazione con due sotto-tab:
- **Pagamenti** (`/outstanding/recurrences/received`) — Pagamenti ricorrenti da effettuare
- **Incassi** (`/outstanding/recurrences/issued`) — Incassi ricorrenti da ricevere

La naming convention URL e' inversa rispetto alla prospettiva dell'azienda:
- `received` = fatture ricevute = pagamenti da fare (scadenze passive)
- `issued` = fatture emesse = incassi da ricevere (scadenze attive)

### Pagina Scadenzario (`/outstanding`)

La pagina principale mostra una tabella con:
- Scadenze raggruppabili per stato, controparte, periodo
- Filtri per data, importo, stato, controparte
- Azioni di gestione (pagamento, chiusura, modifica)

### Pagina Ricorrenze

La pagina ricorrenze mostra le operazioni periodiche configurate:
- Pagamenti ricorrenti (affitto, utenze, stipendi)
- Incassi ricorrenti (canoni, servizi periodici)
- Ciascuna ricorrenza e' legata a un conto bancario e una categoria

### Pagina Regole (`/outstanding/rules`)

La pagina regole contiene le regole di automazione per lo scadenzario:
- Creazione automatica di scadenze da fatture importate
- Categorizzazione automatica
- Matching con movimenti

---

## Entita' e Dati

### Entita' Coinvolte

| Entita' | Ruolo nel Modulo | Rif. Data Model |
|---|---|---|
| `document` | Fattura/documento generatore della scadenza | §2.10 |
| `flow` | Scadenza di pagamento (inclusa nel document) | §3.3 |
| `counterpart` | Controparte della scadenza (cliente/fornitore) | §2.11 |
| `recurrence` | Pagamento/incasso ricorrente | §3.7 |
| `category` / `subcategory` | Categorizzazione della ricorrenza | §2.8, §2.9 |
| `account` | Conto bancario associato alla ricorrenza | §2.4 |

### Relazioni Chiave

```
Document 1:N Flow (una fattura puo' avere piu' scadenze/rate)
Flow → Reconciliation (una scadenza puo' essere riconciliata con un movimento)
Recurrence → Account (la ricorrenza e' associata a un conto)
Recurrence → Category/Subcategory (la ricorrenza ha una categoria)
```

### Dati Osservati

- **Ricorrenze:** array vuoto nella sessione analizzata (nessuna ricorrenza configurata nell'account di test) 🟢
- **Scadenze:** presenti come `flow` inclusi nelle risposte di `/api/v1/documents` 🟢

---

## Logiche di Business

### LB-SC-01: Struttura della Scadenza (Flow)

Confidenza: 🟡 Media

Ogni documento/fattura genera una o piu' scadenze (`flow`). Una fattura con pagamento rateale genera un flow per ogni rata.

Campi rilevanti del documento che influenzano le scadenze:
- `paymentStatus` — Stato pagamento del documento (legato alle scadenze)
- `isInflow` — Determina se la scadenza e' un incasso (attiva) o un pagamento (passiva)
- `grossAmount` — Importo lordo della fattura (la scadenza puo' avere importo uguale o frazionato)

### LB-SC-02: Stati dello Scadenzario

Confidenza: 🟢 Alta (dal JS)

```
PaymentStatus:
  - "ToPay" → Scadenza da pagare (usato nei filtri cashflow aside)
```

Altri stati probabili (non confermati direttamente):
- `Paid` — Pagata/incassata 🟡
- `Overdue` — Scaduta (data scadenza superata) 🟡
- `PartiallyPaid` — Parzialmente pagata 🔴

### LB-SC-03: Integrazione con Cash Flow

Confidenza: 🟢 Alta

Le scadenze alimentano il cashflow previsionale:
```
Per ogni mese futuro:
  outstandingAmount = somma delle scadenze aperte con data in quel mese
  pastdueAmount = somma delle scadenze scadute non pagate
```

Questo dato viene restituito dall'API `/api/v1/cashflow/table` nei campi:
- `outstandingAmount` — Importo scadenze aperte
- `pastdueAmount` — Importo scadenze scadute

### LB-SC-04: Ricorrenze

Confidenza: 🟢 Alta (struttura API confermata)

Le ricorrenze sono operazioni periodiche configurate dall'utente. Ogni ricorrenza:
- E' associata a un **conto bancario** (tramite relazione `account`)
- Ha una **categoria** e opzionalmente una **sottocategoria**
- Genera automaticamente scadenze nel tempo

Include tipico delle ricorrenze:
```
include=account,account.consent,account.consent.institution,category,subcategory
```

### LB-SC-05: Flag `isFromRecurrence` sui Documenti

Confidenza: 🟢 Alta

I documenti generati da una ricorrenza hanno il flag `isFromRecurrence=true`. Questo permette di:
- Distinguere le scadenze automatiche da quelle manuali
- Tracciare la fonte della scadenza nella UI

### LB-SC-06: Direzione delle Scadenze

Confidenza: 🟢 Alta

Le scadenze seguono la direzione del documento padre:
```
if document.direction == "ISSUED":
  → Scadenza attiva (incasso da ricevere)
  → URL ricorrenze: /outstanding/recurrences/issued

if document.direction == "RECEIVED":
  → Scadenza passiva (pagamento da effettuare)
  → URL ricorrenze: /outstanding/recurrences/received
```

---

## API Coinvolte

| Endpoint | Metodo | Scopo | Rif. API |
|---|---|---|---|
| `/api/v1/documents` | GET | Fatture con flow (scadenze) inclusi | §7 |
| `/api/v1/recurrences` | GET | Lista ricorrenze | §11 |
| `/api/v1/cashflow/table` | GET | Importi scadenze aggregati per mese | §5 |
| `/api/v1/transactions/reconciliations` | GET | Match tra transazioni e flow | §4 |

### Parametri Chiave per le Ricorrenze

```
GET /api/v1/recurrences
  filter[company.id__eq]=UUID
  include=account,account.consent,account.consent.institution,category,subcategory
  page[size]=100
```

### Parametri Chiave per le Scadenze (via Documents)

```
GET /api/v1/documents
  filter[company.id__eq]=UUID
  filter[documentDirection__eq]=ISSUED|RECEIVED
  filter[status__in]=CREATED,SENT,DELIVERED,NOT_DELIVERED
  include=flows,category,subcategory,counterpart
  sort=-searchDate,-creationDate,-createdAt,-id
```

---

## Filtri e Ricerca

| Filtro | Tipo | Descrizione | Confidenza |
|---|---|---|---|
| Direzione | Tab | Emesse (incassi) / Ricevute (pagamenti) | 🟢 Alta |
| Stato | Multi-select | Filtra per stato pagamento | 🟡 Media |
| Periodo | Range date | Filtra per data scadenza | 🟡 Media |
| Controparte | Ricerca/select | Filtra per cliente/fornitore | 🟡 Media |
| Importo | Range numerico | Filtra per importo | 🟡 Media |
| Conto | Multi-select | Filtra per conto bancario (nelle ricorrenze) | 🟢 Alta |
| Categoria | Select | Filtra per categoria (nelle ricorrenze) | 🟢 Alta |

---

## Azioni Disponibili

| Azione | Descrizione | Tipo | Confidenza |
|---|---|---|---|
| **Visualizza scadenze** | Lista scadenze con dettagli | Read | 🟢 Alta |
| **Crea ricorrenza** | Configura un pagamento/incasso periodico | Create | 🟡 Media |
| **Modifica ricorrenza** | Modifica una ricorrenza esistente | Update | 🟡 Media |
| **Elimina ricorrenza** | Rimuove una ricorrenza | Delete | 🟡 Media |
| **Crea regola** | Configura una regola di automazione | Create | 🟡 Media |
| **Chiudi scadenza** | Segna una scadenza come pagata/incassata | Update | 🔴 Bassa |
| **Chiusura parziale** | Registra un pagamento parziale | Update | 🔴 Bassa |

---

## Limitazioni Osservate

1. **Nessuna ricorrenza nell'account di test:** L'array delle ricorrenze e' vuoto, impedendo l'analisi dei campi dell'entita' `recurrence`. 🟢

2. **Struttura flow non dettagliata:** L'entita' `flow` e' osservata solo come `included` nei documenti, senza un endpoint diretto catturato. I campi esatti (importo, data scadenza, stato) non sono documentati. 🟡

3. **Regole scadenzario non catturate:** La pagina `/outstanding/rules` non ha generato chiamate API specifiche catturate nelle trace. Le regole dello scadenzario potrebbero usare un endpoint dedicato non osservato. 🟡

4. **Operazioni di scrittura non catturate:** Nessuna operazione di creazione/modifica scadenza o ricorrenza e' stata eseguita durante l'analisi. 🟡

---

## Note

- Lo scadenzario e' strettamente integrato con il modulo Fatture (condividono l'entita' `document` e `flow`) e con il Cash Flow (le scadenze alimentano i dati previsionali).
- La distinzione tra `received` e `issued` nelle ricorrenze segue la prospettiva del **documento** (fattura ricevuta = pagamento, fattura emessa = incasso), non dell'**azione** dell'utente.
- Il campo `paymentStatus` sui documenti sembra essere un campo calcolato che riflette lo stato aggregato dei flow associati (tutte le rate pagate → Paid, alcune → PartiallyPaid, nessuna → ToPay).
- Per un'analisi completa, sarebbe necessario creare delle ricorrenze di test e delle scadenze per osservare il comportamento del sistema.

---

## Aggiornamento Fase 4 — Analisi JS Bundle (10/02/2026)

**Fonte:** Analisi del bundle JavaScript principale `index-N-OxfZQQ.js` (4.5 MB) e API traces.

### Struttura Completa dell'Entita' Flow

🟢 **Alta confidenza** — Estratta da Zod schema, enum e relazioni nel JS.

#### Tipo Entita'

Il flow ha tipo JSON:API `"flow"` (costante `Ane = "flow"`).

#### Schema di Validazione (Zod — `gtr`)

| Campo | Tipo | Vincoli | Descrizione |
|-------|------|---------|-------------|
| `expectedPaymentDate` | date | required | Data scadenza prevista |
| `paymentStatus` | enum `Ka` | required | Stato pagamento (PAID / TO_PAY) |
| `totalAmount` | number | required | Importo totale della scadenza |
| `paymentMethod` | enum `wi` | required | Metodo di pagamento |
| `currency` | string | required | Valuta (es. "EUR") |
| `paymentAccount` | string | required | Conto di pagamento |
| `account` | object | `{id: nullable}` | Conto bancario associato |
| `notes` | string | optional | Note libere |

#### Campi Aggiuntivi (dal codice di serializzazione)

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `paymentDate` | date | Data di pagamento effettivo (diversa da expectedPaymentDate) |
| `verificationStatus` | enum `Ttn` | VERIFIED / TO_VERIFY |
| `id` | UUID | Identificativo unico |
| `createdAt` | datetime | Data creazione |

#### Enum Payment Status (`Ka`)

| Valore | Label EN | Label IT |
|--------|----------|----------|
| `PAID` | Received (inflow) / Paid (outflow) | Incassato / Pagato |
| `TO_PAY` | To receive (inflow) / To pay (outflow) | Da incassare / Da pagare |

#### Enum Extended Payment Status (`Dtn`)

| Valore | Label | Descrizione |
|--------|-------|-------------|
| `PAID` | Paid | Pagamento completato |
| `PAYMENT_SENT` | Payment sent / "Pagamento inviato" | Pagamento inviato, in attesa conferma banca |
| `TO_PAY` | To pay | Da pagare |

> 🔵 **NOTA** — `extendedPaymentStatus` estende `paymentStatus` con lo stato intermedio `PAYMENT_SENT` usato per i pagamenti via Sibill Pay: "We are waiting for confirmation from your bank. The invoice will be automatically reconciled once the bank transfer has been processed."

#### Enum Payment Method (`wi`)

| Valore | Codice | Label IT |
|--------|--------|----------|
| Transfer | `TRANSFER` | Bonifico |
| Cash | `CASH` | Contanti |
| Card | `CARD` | Carta |
| Check | `CHECK` | Assegno |
| Postal | `POSTAL` | Postale |
| Riba | `RIBA` | RIBA |
| Sdd | `SDD` | SDD |
| FiscalCredit | `FISCAL_CREDIT` | Credito fiscale |
| Deferred | `DEFERRED` | Senza incasso |
| TaxForm | `TAX_FORM` | F24 |
| Other | `OTHER` | Altro |

#### Enum Verification Status Flow (`Ttn`)

| Valore | Label IT |
|--------|----------|
| `VERIFIED` | "Verificato" |
| `TO_VERIFY` | "Da verificare" |

---

### Relazioni dell'Entita' Flow

🟢 **Alta confidenza** — Estratte dal codice di include nelle chiamate API.

```
Flow
├── company (azienda proprietaria)
├── document (documento/fattura padre)
│   ├── document.flows (scadenze sorelle dello stesso documento)
│   ├── document.category
│   ├── document.subcategory
│   └── document.counterpart (cliente/fornitore)
├── account (conto bancario associato)
│   ├── account.consent
│   │   └── account.consent.institution (banca)
├── payments (pagamenti effettuati)
└── reconciliations (riconciliazioni associate)
```

---

### API Endpoint dei Flow (Complete)

🟢 **Alta confidenza** — Estratte dal codice JS.

| Endpoint | Metodo | Scopo |
|----------|--------|-------|
| `GET /api/v1/flows` | GET | Lista flow con filtri, paginazione cursor-based |
| `GET /api/v1/flows/{id}` | GET | Dettaglio flow con relazioni |
| `PATCH /api/v1/flows/{id}` | PATCH | Aggiorna flow (data, stato, importo, metodo, conto) |
| `POST /api/v1/flows` | POST | Crea nuovo flow (con company, document, account) |
| `DELETE /api/v1/flows/{id}` | DELETE | Elimina flow |
| `POST /api/v1/flows/bulk-update` | POST | Aggiornamento massivo flow |
| `GET /api/v1/flows/metadata` | GET | Metadata dei flow (es. conteggi per filtro) |
| `POST /api/v1/outstanding/export` | POST | Esporta scadenze in file `scadenze.xlsx` |

#### Paginazione

- **Tipo:** cursor-based
- **Page size standard:** 25 (lista standard), 35 (vista infinita)
- **Sorting default:** `paymentDate ASC`, `createdAt ASC`, `id ASC`

---

### Filtri dei Flow (Parametri API Completi)

🟢 **Alta confidenza** — Estratti dalla funzione di filter builder nel JS.

| Parametro API | Tipo | Descrizione |
|---------------|------|-------------|
| `filter[company.id__eq]` | UUID | Azienda |
| `filter[document.direction__eq]` | string | ISSUED / RECEIVED |
| `filter[document.isInflow__eq]` | boolean | Entrata (true) / Uscita (false) |
| `filter[document.number__ilike]` | string | Ricerca nel numero documento |
| `filter[document.documentType__in]` | array | Tipi documento (INVOICE, CREDIT_NOTE, ...) |
| `filter[paymentStatus__eq]` | string | PAID / TO_PAY |
| `filter[extendedPaymentStatus__eq]` | string | PAID / PAYMENT_SENT / TO_PAY |
| `filter[verificationStatus__eq]` | string | VERIFIED / TO_VERIFY |
| `filter[expectedPaymentDate__gte]` | date | Data scadenza da |
| `filter[expectedPaymentDate__lt]` | date | Data scadenza a (esclusa, +1 giorno fine mese) |
| `filter[paymentMethod__in]` | array | Metodi di pagamento |
| `filter[paymentMethod__notIn]` | array | Metodi di pagamento esclusi |
| `filter[account.id__in]` | array UUID | Conti bancari |
| `filter[account.id__empty]` | boolean | Flow senza conto assegnato |
| `filter[document.category.id__eq]` | UUID | Categoria |
| `filter[document.subcategory.id__eq]` | UUID | Sottocategoria |
| `filter[customCounterpartId__eq]` | UUID | Controparte specifica |
| `filter[id__in]` | array UUID | ID specifici |
| `filter[id__notIn]` | array UUID | ID esclusi |
| `filter[document.hiddenAt__empty]` | boolean | Escludi documenti nascosti (sempre true) |

---

### Filtri Default dello Scadenzario

🟢 **Alta confidenza** — Oggetto `AFe` nel JS.

```javascript
{
  search: "",
  dateRange: [null, null],
  documentDirection: null,
  isInflow: "",
  accountId: [],
  paymentStatus: "TO_PAY",       // ← Default: mostra solo scadenze da pagare
  extendedPaymentStatus: null,
  paymentMethod: [],
  documentType: ["INVOICE", "CREDIT_NOTE", "DEBIT_NOTE", "PARCEL", "SELF_INVOICE", "BILL"],
  category: null,
  verificationStatus: null
}
```

> 🔵 **NOTA** — Il default esclude `DELIVERY_NOTE`, `OTHER`, `QUOTE` dai tipi documento. Mostra solo scadenze `TO_PAY` (non le pagate). Questo e' il filtro "operativo" tipico di uno scadenzario.

---

### Quick Filter dello Scadenzario

🟢 **Alta confidenza** — Estratti dai testi i18n.

| Filtro | Label IT | Descrizione |
|--------|----------|-------------|
| `all` | "Tutte le scadenze" | Nessun filtro |
| `due` | "Fatture da saldare" | Solo TO_PAY |
| `inflow` | "Incassi" | Solo entrate |
| `outflow` | "Pagamenti" | Solo uscite |
| `overdue` | "Fatture scadute" | Scadenze passate non pagate |
| `paid` | "Fatture saldate" | Solo pagate |
| `pay_with_sibill` | "Paga con Sibill" | Pagamento tramite Sibill |
| `to_pay_next_7_days` | "Da pagare nei prossimi 7 giorni" | Quick filter temporale |
| `to_receive_next_7_days` | "Da incassare nei prossimi 7 giorni" | Quick filter temporale |
| `expired` | "Scadute" | Scadenze passate |
| `this_year` | "Anno corrente ({{year}})" | Filtro anno |
| `previous_year` | "Anno precedente ({{year}})" | Filtro anno precedente |

---

### Colonne della Tabella Scadenzario

🟢 **Alta confidenza** — Estratte dalla struttura i18n `Mnt` e `Fnt`.

| Colonna | Label IT | Descrizione |
|---------|----------|-------------|
| `actions` | "Azioni" | Menu azioni per riga |
| `type` | "Tipo" | Tipo documento |
| `description` | "Descrizione" | Descrizione della scadenza |
| `document_type` | "Tipo documento" | INVOICE, CREDIT_NOTE, ecc. |
| `payment` | "Pagamento" | Dettagli pagamento |
| `status` | "Stato" | Stato pagamento |
| `amount` | "Importo" | Importo della scadenza |
| `account` | "Conto" | Conto bancario (fallback: "Unassigned") |
| `category` | "Categoria" | Categoria associata |
| `verify` | "Verifica" | Flag verifica |

**Tab della tabella v2:**
- "Tutte le scadenze" / "Incassi" / "Uscite"

---

### Form Nuova Scadenza (Pnt)

🟢 **Alta confidenza** — Estratto dalla struttura i18n.

| Campo | Label IT | Tipo | Note |
|-------|----------|------|------|
| `direction` | "Direzione" | Select | Inflow / Outflow |
| `creation_issue` | "Data creazione/emissione" | Date | |
| `document_number` | "Numero documento" | Text | |
| `flow_amount` | "Importo scadenza" | Number | |
| `payment_date` | "Data pagamento" | Date | |
| `payment_method` | "Metodo di pagamento" | Select | Enum `wi` |
| `payment_status` | "Stato pagamento" | Select | Paid / To pay |
| `payment_account` | "Conto pagamento" | Select | |
| `category` | "Categoria" | Select | |
| `description` | "Descrizione" | Text | |
| `total` | "Totale" | Number | Calcolato |

**Azioni:** "Submit" / "Cancel"
**Titolo:** "Add payment/prevision" / "Aggiungi pagamento/previsione"

---

### Azioni di Aggiornamento Massivo (Bulk)

🟢 **Alta confidenza** — Estratte dalla struttura i18n.

| Azione | Descrizione |
|--------|-------------|
| `bulk_update_account` | Aggiornamento massivo del conto bancario |
| `bulk_update_status` | Aggiornamento massivo dello stato |
| `bulk_update_payment_date` | Aggiornamento massivo della data di pagamento |
| `bulk_update_verification_status` | Aggiornamento massivo dello stato di verifica |
| `edit_flow_account_dialog` | Dialog per modifica conto del flow |

---

### Aging Buckets (Fasce di Scadenza)

🟢 **Alta confidenza** — Enum `vr` estratto dal JS.

| Valore | Significato |
|--------|-------------|
| `15` | 15 giorni |
| `30` | 30 giorni |
| `60` | 60 giorni |
| `90` | 90 giorni |
| `120` | 120 giorni |
| `150` | 150 giorni |
| `EOM` | Fine mese |
| `30EOM` | 30 giorni fine mese |
| `60EOM` | 60 giorni fine mese |
| `90EOM` | 90 giorni fine mese |
| `120EOM` | 120 giorni fine mese |
| `150EOM` | 150 giorni fine mese |

> 🏦 **FORMATO BANCARIO** — Le fasce `EOM` (End of Month) sono standard nel settore bancario italiano per le condizioni di pagamento. "30EOM" significa "30 giorni dalla fine del mese di emissione".

---

### Struttura Completa delle Ricorrenze

🟢 **Alta confidenza** — Estratta dallo schema Zod `Nir` nel JS.

#### Schema di Validazione (Zod — `Nir`)

| Campo | Tipo | Vincoli | Descrizione |
|-------|------|---------|-------------|
| `amount` | number | min: 1 | Importo della ricorrenza |
| `description` | string | min: 1 | Descrizione |
| `paymentMethod` | enum `wi` | nullable | Metodo di pagamento |
| `category` | string | nullish | Categoria |
| `subcategory` | string | nullish | Sottocategoria |
| `direction` | enum `rr` | required | ISSUED / RECEIVED |
| `account` | string | nullable | Conto bancario |
| `frequency` | object | required | Configurazione frequenza |

#### Oggetto Frequenza

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `start` | date | Data inizio ricorrenza |
| `end` | date | Data fine ricorrenza |
| `mode` | enum `rUe` | Frequenza (WEEKLY, MONTHLY, ecc.) |
| `hasEnd` | boolean | Se la ricorrenza ha una data di fine |
| `param` | number | Parametro aggiuntivo (giorno della settimana o del mese) |

#### Enum Frequenza (`rUe`)

| Valore | Label | Descrizione |
|--------|-------|-------------|
| `WEEKLY` | Settimanale | Ogni settimana |
| `BIWEEKLY` | Bisettimanale | Ogni 2 settimane |
| `MONTHLY` | Mensile | Ogni mese |
| `BIMONTHLY` | Bimestrale | Ogni 2 mesi |
| `QUARTERLY` | Trimestrale | Ogni 3 mesi |
| `SEMIANNUAL` | Semestrale | Ogni 6 mesi |
| `ANNUAL` | Annuale | Ogni anno |

#### Form Ricorrenza (campi UI)

| Campo | Label IT |
|-------|----------|
| `description_label` | Descrizione |
| `category_label` | Categoria |
| `amount_label` | Importo |
| `frequency_label` | Frequenza |
| `account_label` | Conto |
| `payment_method_label` | Metodo di pagamento |
| `start_date_label` | Data inizio |
| `end_date_label` | Data fine |
| `mode_label` | Modalita' |
| `has_end_label` | Ha una data di fine |
| `week_day_label` | Giorno della settimana |
| `month_day_label` | Giorno del mese |

**Azioni:**
- "Add new recurring payment" / "Aggiungi nuovo pagamento ricorrente"
- "Add new recurring income" / "Aggiungi nuovo incasso ricorrente"
- Delete: "Delete future" / "Delete all"

**Messaggi:**
- Successo creazione con fine: "We will generate all expected deadlines immediately"
- Successo creazione senza fine: "Recurring payment created"
- Successo eliminazione: "The recurring payment has been removed"

#### API Ricorrenze

| Endpoint | Metodo | Scopo |
|----------|--------|-------|
| `GET /api/v1/recurrences` | GET | Lista ricorrenze con filtri |

**Query keys:** `["Recurrences"]`, `["Recurrences", {companyId}]`, `["Recurrences", {companyId}, "chart", ...]`

**Parametri:**
```
filter[company.id__eq]=UUID
include=account,account.consent,account.consent.institution,category,subcategory
page[size]=100
```

---

### Routing e Navigazione dello Scadenzario

🟢 **Alta confidenza** — Estratto dalle definizioni delle route nel JS.

| Route | Path | Descrizione |
|-------|------|-------------|
| `Outstanding` | `/outstanding` | Scadenzario principale |
| `OutstandingFlowsInflow` | `/outstanding/flows/inflow` | Scadenze in entrata |
| `OutstandingFlowsOutflow` | `/outstanding/flows/outflow` | Scadenze in uscita |
| `OutstandingFlowsAll` | `/outstanding/flows/all` | Tutte le scadenze |
| `Recurrences` | `/outstanding/recurrences` | Ricorrenze |
| `OutstandingRules` | `/outstanding/rules` | Regole |
| `PayOutstandingFlows` | `/outstanding/flows/pay` | Pagamento scadenze |

**Menu sidebar:**
```
Scadenze (label: "AP&AR")
├── Scadenzario (Deadlines)
├── Ricorrenze (Recurring payment)
├── Organizza (Manage)
└── Regole (Rules)
```

---

### Tipi Documento (Enum `nt`)

🟢 **Alta confidenza** — Enum completo estratto dal JS.

| Valore | Codice | Label IT |
|--------|--------|----------|
| `Invoice` | `INVOICE` | Fattura |
| `SelfInvoice` | `SELF_INVOICE` | Autofattura |
| `Parcel` | `PARCEL` | Parcella |
| `CreditNote` | `CREDIT_NOTE` | Nota di credito |
| `DebitNote` | `DEBIT_NOTE` | Nota di debito |
| `Bill` | `BILL` | Bolletta |
| `DeliveryNote` | `DELIVERY_NOTE` | DDT |
| `Other` | `OTHER` | Altro |
| `Quote` | `QUOTE` | Preventivo |

#### Codici Tipo Documento SDI (Enum `Nn`)

| Codice | Tipo SDI | Descrizione |
|--------|----------|-------------|
| `TD01` | Fattura | Fattura ordinaria |
| `TD02` | AccontoFattura | Fattura di acconto |
| `TD04` | NotaDiCredito | Nota di credito |
| `TD05` | NotaDiDebito | Nota di debito |
| `TD06` | Parcella | Parcella professionale |
| `TD16` | AutofatturaReverseCharge | Autofattura reverse charge |
| `TD17` | AutofatturaServiziEsteri | Autofattura servizi esteri |
| `TD18` | AutofatturaBeniEU | Autofattura beni UE |
| `TD19` | AutofatturaBeniEsteri | Autofattura beni esteri |
| `TD24` | FatturaDifferita | Fattura differita |
| `TD26` | CessioneDiBeniAmmortizzabili | Cessione beni ammortizzabili |
| `TD27` | AutofatturaPerAutoconsumo | Autofattura per autoconsumo |
| `TD29` | CommunicationOmittedIrregularInvoice | Comunicazione fatture irregolari |

#### Formato Fattura Elettronica (Enum `US`)

| Codice | Descrizione |
|--------|-------------|
| `FPA12` | Fattura PA (Pubblica Amministrazione) |
| `FPR12` | Fattura PR (soggetti privati) |
| `FSM10` | Fattura semplificata |

#### Stato Pagamento Documento (Enum `bw`)

| Valore | Label IT | Descrizione |
|--------|----------|-------------|
| `PAID` | Pagato | Tutte le rate pagate |
| `PARTIALLY_PAID` | Parzialmente pagato | Alcune rate pagate |
| `TO_PAY` | Da pagare | Nessuna rata pagata |

> 📐 **FORMULA/ALGORITMO** — Lo stato pagamento del documento (`bw`) e' un campo calcolato/aggregato: riflette lo stato dei flow figli. Se tutti i flow sono PAID → documento PAID. Se almeno uno PAID e uno TO_PAY → PARTIALLY_PAID. Se tutti TO_PAY → TO_PAY. 🟡

---

### Integrazione con Cash Flow — Dettagli

🟢 **Alta confidenza** — Estratti dalla struttura del grafico cashflow.

Il grafico cashflow ha opzioni per la visualizzazione delle scadenze:

| Opzione | Label IT | Descrizione |
|---------|----------|-------------|
| `predictions` | "Previsioni" | Stime di entrate/uscite aggiunte manualmente |
| `overdue` | "In scadenza" | Entrate/uscite in scadenza a partire da oggi |
| `pastdue` | "Scaduto" | Entrate/uscite scadute incluse nel mese corrente |

**Dettaglio tooltip overdue:**
- Include zero line / Exclude zero line
- Show/Hide overdue
- Overdue to cash in / Overdue to pay
- Final balance overdue

---

### Regole dello Scadenzario (Outstanding Rules)

🟢 **Alta confidenza** — Struttura completa estratta dal JS (vedi doc 06-riconciliazione.md per i dettagli delle regole).

Le regole dello scadenzario vivono in `/outstanding/rules` con sotto-tab "Received rules" / "Issued rules".

**Criteri:** Document type, Payment method, Account, Direction
**Azione principale:** `AUTO_RECONCILIATION` — crea automaticamente un movimento bancario e lo riconcilia con la scadenza che matcha i criteri.

> 📐 **FORMULA/ALGORITMO** — Il flusso di auto-riconciliazione:
> 1. Una scadenza (flow) viene creata o importata
> 2. Il sistema controlla le regole outstanding nell'ordine di priorita'
> 3. Se una regola matcha (tipo documento + metodo pagamento + conto + direzione)
> 4. Il sistema crea automaticamente un movimento bancario (transaction)
> 5. Il sistema crea una riconciliazione tra il flow e la transaction con source=AUTOMATIC
> 6. La scadenza risulta automaticamente riconciliata
>
> Confidenza: 🟡 Media — la logica server-side non e' osservabile, il flusso e' dedotto dalla struttura della UI e dai campi disponibili.
