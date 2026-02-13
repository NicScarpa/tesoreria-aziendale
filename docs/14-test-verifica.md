# Test e Verifica — Documentazione

**Data analisi:** 10 febbraio 2026
**Metodologia:** Analisi statica di API traces, JavaScript client-side, e dati osservati

---

## 1. Dati Reali Osservati nell'Account di Test

### 1.1 Account di Test

| Parametro | Valore | Fonte | Confidenza |
|---|---|---|---|
| **Azienda** | WEISS S.R.L. | API `/api/v1/companies/` | 🟢 Alta |
| **Piano** | TRIAL | API `/api/v1/subscriptions` (status: "TRIAL") | 🟢 Alta |
| **Ruolo utente** | ADMIN | API company.userRole | 🟢 Alta |
| **Stato utente** | ACTIVE | API company.userStatus | 🟢 Alta |
| **N. conti bancari** | 2 | API `/api/v1/accounts` (count) | 🟢 Alta |
| **N. transazioni** | 42 | API `/api/v1/transactions/metadata` (total) | 🟢 Alta |
| **N. ricorrenze** | 0 | API `/api/v1/recurrences` (data: []) | 🟢 Alta |
| **N. pagamenti** | 0 | API `/api/v1/payments` (total: 0) | 🟢 Alta |
| **N. carte** | 0 | API `/api/v1/cards` (has_created_card: false) | 🟢 Alta |

### 1.2 Saldi Bancari

| Metrica | Valore | Fonte | Confidenza |
|---|---|---|---|
| **Saldo contabile totale** | 12.093,43 EUR | API `/api/v1/accounts/metadata` | 🟢 Alta |
| **Saldo disponibile totale** | 10.190,17 EUR | API `/api/v1/accounts/metadata` | 🟢 Alta |
| **Differenza** | 1.903,26 EUR | Calcolato: current - available | 🟢 Alta |
| **N. conti nel calcolo** | 2 | API `balances_converted.count` | 🟢 Alta |

### 1.3 Transazioni

| Metrica | Valore | Fonte | Confidenza |
|---|---|---|---|
| **Totale transazioni** | 42 | API `/api/v1/transactions/metadata` | 🟢 Alta |
| **Entrate totali** | 5.645,30 EUR | API `totalsEur.positive.amount` | 🟢 Alta |
| **Uscite totali** | -5.181,79 EUR | API `totalsEur.negative.amount` | 🟢 Alta |
| **Non categorizzate** | 7 | API `totalUncategorised` | 🟢 Alta |
| **Flusso netto** | +463,51 EUR | Calcolato: 5645.30 - 5181.79 | 🟢 Alta |

### 1.4 Categorie

| Categoria | Sottocategorie Osservate | Fonte | Confidenza |
|---|---|---|---|
| **Gestione** | Locazione, Commissioni, Utenze | API + UI | 🟢 Alta |
| **Incassi** | Pos | API + UI | 🟢 Alta |
| **Finanziamenti, mutui, leasing** | - | API + UI | 🟢 Alta |
| **Personale** | - | API + UI | 🟢 Alta |
| **Non categorizzata** | - | API + UI | 🟢 Alta |
| *(Altre)* | - | API (6 totali) | 🟢 Alta |

### 1.5 Tipi di Transazione Osservati

| Tipo | Esempio | Confidenza |
|---|---|---|
| **Bonifico** | Pagamento affitto, fornitori, incassi POS (Worldline) | 🟢 Alta |
| **Commissioni** | Commissioni su bonifico, commissioni SEPA B2B | 🟢 Alta |
| **Addebito diretto** | SDD Core (utenze, SEPA) | 🟢 Alta |

### 1.6 Connessioni Bancarie

| Parametro | Valore | Confidenza |
|---|---|---|
| **Provider Open Banking** | SWAN | 🟢 Alta |
| **N. consents attivi** | Almeno 1 (status: AUTHORIZED) | 🟢 Alta |
| **Istituzione** | "Conto Sibill" | 🟢 Alta |

---

## 2. Verifiche Effettuate per Modulo

### 2.1 Cash Flow e Previsioni

| # | Verifica | Risultato | Confidenza |
|---|---|---|---|
| V-CF-01 | API `/cashflow/chart` restituisce saldi per mese | Confermato — struttura con `balance.start` e `balance.end` per ogni mese | 🟢 Alta |
| V-CF-02 | API `/cashflow/table` restituisce dettaglio per categoria | Confermato — 35 righe con combinazioni mese x direzione x categoria | 🟢 Alta |
| V-CF-03 | Inversione segno per outflow avviene client-side | Confermato — funzione `pt(money, isOutflow)` nel JS | 🟢 Alta |
| V-CF-04 | Budget solo in numeri interi EUR | Confermato — `maxDecimalPlaces: 0`, `onlyPositive: true` | 🟢 Alta |
| V-CF-05 | Suggerimenti budget: mese precedente, media 3 mesi, anno precedente | Confermato — logica nel JS `CashFlowPage--BaMgJEI.js` | 🟢 Alta |
| V-CF-06 | Periodo default: -5/+6 mesi | Confermato — `subMonths(today, 5)` / `addMonths(today, 6)` | 🟢 Alta |
| V-CF-07 | Range periodo: min 3, max 12 mesi | Confermato — logica di validazione nel JS | 🟢 Alta |
| V-CF-08 | Date API in UTC con offset Europe/Rome | Confermato — `2025-08-31T22:00:00.000Z` = 1 Set 2025 CEST | 🟢 Alta |
| V-CF-09 | Flag `includeBudgets`, `includeOverdue`, `includePastdue` | Confermato — presenti come parametri opzionali nelle API | 🟢 Alta |
| V-CF-10 | Visibilita' categorie salvata in localStorage | Confermato — chiave `cashflow-visibility-overrides-{direction}` | 🟢 Alta |

### 2.2 Riconciliazione Bancaria

| # | Verifica | Risultato | Confidenza |
|---|---|---|---|
| V-RIC-01 | Entita' `reconciliation` con campi status, source, createdAt | Confermato — 3 chiamate a `/api/v1/reconciliations/` | 🟢 Alta |
| V-RIC-02 | Source puo' essere AUTOMATIC o MANUAL | Confermato — campo `source` nell'entita' | 🟢 Alta |
| V-RIC-03 | Endpoint `/transactions/reconciliations` per match proposti | Confermato — filtro `verificationStatus__eq=TO_VERIFY` | 🟢 Alta |
| V-RIC-04 | Risposta match: `{transaction_id, flow_ids}` | Confermato — struttura JSON osservata | 🟢 Alta |
| V-RIC-05 | Matching 1:N (una transazione, piu' flow) | Confermato — `flow_ids` e' un array | 🟢 Alta |
| V-RIC-06 | Algoritmo di matching server-side | Non verificabile — logica non osservabile | 🔴 Bassa |
| V-RIC-07 | Soglie di tolleranza per il matching | Non verificabile — non osservabile client-side | 🔴 Bassa |

### 2.3 Scadenzario

| # | Verifica | Risultato | Confidenza |
|---|---|---|---|
| V-SC-01 | Flow inclusi nei documenti via `include=flows` | Confermato — relazione has_many document→flows | 🟢 Alta |
| V-SC-02 | Ricorrenze vuote nell'account di test | Confermato — `data: []` da `/api/v1/recurrences` | 🟢 Alta |
| V-SC-03 | Include ricorrenze: account, category, subcategory | Confermato — parametro include osservato | 🟢 Alta |
| V-SC-04 | Flag `isFromRecurrence` sui documenti | Confermato — campo booleano nel document | 🟢 Alta |
| V-SC-05 | Stato `ToPay` nel paymentStatus | Confermato — enum nel JS | 🟢 Alta |
| V-SC-06 | Struttura dettagliata del flow | Non verificata — campi interni del flow non osservati | 🟡 Media |

### 2.4 Pagamenti

| # | Verifica | Risultato | Confidenza |
|---|---|---|---|
| V-PAG-01 | 5 stati pagamento: PENDING, ACCEPTED, SUCCEEDED, FAILED, TIMEOUT | Confermato — filtro `status__in` nell'API | 🟢 Alta |
| V-PAG-02 | Relazione parent per pagamenti bulk | Confermato — `parent` nell'include | 🟢 Alta |
| V-PAG-03 | Retry attempts per pagamenti falliti | Confermato — `retry_attempts` nell'include | 🟢 Alta |
| V-PAG-04 | Polling per pagamenti TIMEOUT | Confermato — 29 chiamate a `/payments/metadata?status__in=TIMEOUT` | 🟢 Alta |
| V-PAG-05 | Nessun pagamento nell'account di test | Confermato — `total: 0` | 🟢 Alta |
| V-PAG-06 | Endpoint validate-iban | Non testato — nessun pagamento creato | 🟡 Media |
| V-PAG-07 | Generazione file SEPA XML | Non testato — richiede creazione pagamento | 🔴 Bassa |

### 2.5 Connessione Bancaria

| # | Verifica | Risultato | Confidenza |
|---|---|---|---|
| V-CB-01 | Provider Open Banking: SWAN | Confermato — `filter[source__eq]=SWAN` | 🟢 Alta |
| V-CB-02 | Calcolo saldi aggregati con esclusioni | Confermato — filtri `ignoreBalance__eq=false`, `consent.status__neq=DISABLED` | 🟢 Alta |
| V-CB-03 | Saldi: contabile 12.093,43, disponibile 10.190,17 | Confermato — dati API esatti | 🟢 Alta |
| V-CB-04 | 2 conti attivi | Confermato — `balances_converted.count: 2` | 🟢 Alta |
| V-CB-05 | Campo `allowBalanceChange` per modifica manuale saldo | Confermato — campo booleano nell'account | 🟢 Alta |
| V-CB-06 | Campo `ignoreBalance` per esclusione da aggregati | Confermato — campo booleano nell'account | 🟢 Alta |
| V-CB-07 | Consent SDI con wizard 3 step | Confermato — codice JS `AddAccountingConsent-DQhKurMl.js` | 🟢 Alta |
| V-CB-08 | Scadenza consent PSD2 (90 giorni) | Non verificato — nessun consent scaduto osservato | 🟡 Media |
| V-CB-09 | Frequenza sincronizzazione | Non verificato — solo `lastRunAt` osservato | 🟡 Media |

### 2.6 Reportistica e Dashboard

| # | Verifica | Risultato | Confidenza |
|---|---|---|---|
| V-REP-01 | Dashboard fatture con ricavi/costi/IVA | Confermato — API `/documents-dashboard/summary` | 🟢 Alta |
| V-REP-02 | Top clienti e fornitori con percentuali | Confermato — struttura JSON con `amountPercentage` | 🟢 Alta |
| V-REP-03 | Filtro anno corrente per dashboard fatture | Confermato — `creationDate__gte/lte` = anno corrente | 🟢 Alta |
| V-REP-04 | Export Excel cashflow | Confermato — tracking event `CASHFLOW_EXPORTED` | 🟢 Alta |
| V-REP-05 | 183 elementi SVG nel grafico cashflow | Confermato — conteggio dalla mappatura pagine | 🟢 Alta |
| V-REP-06 | Esclusione DRAFT e DISCARDED dalla dashboard | Confermato — `status__notIn=DRAFT,DISCARDED` | 🟢 Alta |

---

## 3. Riepilogo Livelli di Confidenza

### Per Modulo

| Modulo | 🟢 Alta | 🟡 Media | 🔴 Bassa | Totale Verifiche |
|---|---|---|---|---|
| **Cash Flow** | 10 | 0 | 0 | 10 |
| **Riconciliazione** | 5 | 0 | 2 | 7 |
| **Scadenzario** | 5 | 1 | 0 | 6 |
| **Pagamenti** | 5 | 1 | 1 | 7 |
| **Connessione Bancaria** | 7 | 2 | 0 | 9 |
| **Reportistica** | 6 | 0 | 0 | 6 |
| **TOTALE** | **38** | **4** | **3** | **45** |

### Distribuzione Percentuale

- 🟢 **Alta (confermata):** 84% (38/45)
- 🟡 **Media (coerente):** 9% (4/45)
- 🔴 **Bassa (ipotetica):** 7% (3/45)

---

## 4. Cosa NON e' Stato Possibile Verificare

### 4.1 Limitazioni del Piano TRIAL

| Funzionalita' | Motivazione | Impatto |
|---|---|---|
| **Budget avanzati** | Il piano TRIAL potrebbe non includere la funzionalita' budget | Non e' stato possibile verificare la creazione/modifica di budget |
| **Pagamenti** | Nessun pagamento presente nel piano TRIAL | Struttura dettagliata del payment non osservata |
| **F24** | Il servizio F24 potrebbe richiedere un piano superiore | Nessuna API specifica catturata |
| **Export PDF/CSV** | Solo l'export Excel e' stato confermato | Non e' chiaro se esistano altri formati |

### 4.2 Limitazioni dell'Analisi (Solo Lettura)

| Funzionalita' | Motivazione | Impatto |
|---|---|---|
| **Creazione pagamento** | Non sono state eseguite operazioni di scrittura | Endpoint POST per payments non catturati |
| **Riconciliazione manuale** | Non sono state eseguite operazioni di matching | Flusso completo di riconciliazione non documentato |
| **Creazione ricorrenza** | Non sono state create ricorrenze | Struttura entita' recurrence non dettagliata |
| **Connessione nuova banca** | Non e' stata eseguita una nuova connessione | Flusso consent completo non catturato |
| **Creazione fattura** | Non sono state create fatture | Endpoint POST per documents non catturati |
| **Generazione file SEPA** | Non e' stata generata una disposizione | Formato XML non catturato |

### 4.3 Logiche Server-Side Non Osservabili

| Logica | Motivo | Confidenza Assegnata |
|---|---|---|
| **Algoritmo matching riconciliazione** | La logica di matching e' interamente server-side | 🔴 Bassa |
| **Soglie di tolleranza matching** | Non esposte nell'API o nel JS | 🔴 Bassa |
| **Frequenza sincronizzazione bancaria** | Gestita dal backend/provider SWAN | 🟡 Media |
| **Generazione file SEPA XML** | Processata server-side | 🔴 Bassa |
| **Calcolo scadenze da fatture** | La creazione dei flow avviene server-side | 🟡 Media |

---

## 5. Fonti di Verifica Utilizzate

| Fonte | Tipo | N. File/Endpoint | Affidabilita' |
|---|---|---|---|
| **API traces** | Intercettazione rete | 800 richieste, 31 endpoint | Molto alta — dati reali dal backend |
| **JavaScript client-side** | Analisi statica | 7+ file JS analizzati | Alta — logica effettiva del frontend |
| **API catalog** | Aggregazione automatica | 1 file JSON | Alta — generato da script deterministico |
| **Screenshot** | Cattura visuale | 68 file, 23 pagine reali | Alta — evidenza visiva diretta |
| **DOM inspection** | Ispezione elementi | Via Playwright snapshot | Alta — struttura UI effettiva |

---

## 6. Raccomandazioni per Verifiche Future

Per completare l'analisi con livello di confidenza 🟢 su tutti i punti, si raccomanda:

1. **Creare un pagamento di test** (bonifico SEPA) per:
   - Catturare l'endpoint POST `/api/v1/payments`
   - Osservare la validazione IBAN
   - Verificare la generazione del file SEPA XML
   - Documentare il flusso completo: creazione → approvazione → esecuzione

2. **Eseguire una riconciliazione manuale** per:
   - Catturare l'endpoint di riconciliazione manuale
   - Osservare i criteri di matching nell'interfaccia
   - Documentare il flusso di verifica e conferma

3. **Creare una ricorrenza** per:
   - Osservare i campi dell'entita' recurrence
   - Documentare la logica di generazione automatica scadenze

4. **Creare una fattura** per:
   - Catturare l'endpoint POST `/api/v1/documents`
   - Osservare la creazione automatica di flow/scadenze
   - Documentare la struttura dettagliata del flow

5. **Connettere un nuovo conto** per:
   - Catturare il flusso OAuth2 completo
   - Documentare il consent flow end-to-end
   - Osservare la prima sincronizzazione

6. **Testare con piano superiore al TRIAL** per:
   - Verificare quali funzionalita' sono gate-kept
   - Sbloccare potenzialmente: budget, pagamenti, F24, export avanzati

---

## 7. Riepilogo Formule e Algoritmi Identificati

| ID | Formula/Algoritmo | Modulo | Confidenza | Riferimento |
|---|---|---|---|---|
| 📐 LB-CF-01 | Aggregazione dati cashflow (4 fonti) | Cash Flow | 🟢 | docs/05-cash-flow.md |
| 📐 LB-CF-02 | Calcolo saldo e variazione | Cash Flow | 🟢 | docs/05-cash-flow.md |
| 📐 LB-CF-03 | Inversione segno outflow | Cash Flow | 🟢 | docs/05-cash-flow.md |
| 📐 LB-CF-04 | Gestione budget multi-livello | Cash Flow | 🟢 | docs/05-cash-flow.md |
| 📐 LB-CF-05 | Suggerimenti budget (3 metodi) | Cash Flow | 🟢 | docs/05-cash-flow.md |
| 📐 LB-CF-07 | Importo residuo budget | Cash Flow | 🟢 | docs/05-cash-flow.md |
| 📐 LB-CF-09 | Dominio Y del grafico | Cash Flow | 🟢 | docs/05-cash-flow.md |
| 📐 LB-CB-04 | Calcolo saldi aggregati | Connessione Bancaria | 🟢 | docs/09-connessione-bancaria.md |
| 📐 LB-REP-01 | Riepilogo ricavi/costi/IVA | Reportistica | 🟢 | docs/11-reportistica.md |
| 📐 LB-REP-02 | Ranking clienti/fornitori | Reportistica | 🟢 | docs/11-reportistica.md |
| 📐 LB-REP-03 | Metriche movimenti | Reportistica | 🟢 | docs/11-reportistica.md |
| 📐 4.1 | Percentuale budget vs actual | Regole Business | 🟢 | docs/13-regole-business.md |
| 📐 4.2 | Percentuale di importo | Regole Business | 🟢 | docs/13-regole-business.md |
| 📐 4.3 | Importo residuo budget (dettaglio) | Regole Business | 🟢 | docs/13-regole-business.md |
| 📐 4.4 | Suggerimenti budget (dettaglio) | Regole Business | 🟢 | docs/13-regole-business.md |
| 📐 4.5 | Aggregazione dati cashflow (dettaglio) | Regole Business | 🟢 | docs/13-regole-business.md |
| 📐 4.7 | Punti linea bilancio (grafico) | Regole Business | 🟢 | docs/13-regole-business.md |
| 📐 4.8 | Dominio Y grafico (dettaglio) | Regole Business | 🟢 | docs/13-regole-business.md |
