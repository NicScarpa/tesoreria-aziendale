# PRD-02: Dashboard Homepage

**Versione:** 1.0
**Data:** 10 febbraio 2026
**Modulo:** Dashboard Homepage
**Basato su:** RE Sibill docs/05-cash-flow.md, docs/11-reportistica.md, docs/01-app-map.md, docs/13-regole-business.md
**Contratto DB:** `.tmp/db-schema.md`

---

## 1. Panoramica

La Dashboard Homepage e' la prima schermata visibile dopo il login. Corrisponde alla route `/cashflow` in Sibill, che funge sia da dashboard sia da modulo cash flow.

Nel nostro gestionale la dashboard ha un ruolo piu' ampio: aggrega KPI finanziari, widget operativi e un grafico trend in un'unica vista, fornendo all'utente un colpo d'occhio sulla salute finanziaria dell'azienda.

**Obiettivo:** fornire in una singola schermata tutte le informazioni critiche per la gestione quotidiana della tesoreria, minimizzando i click per le azioni piu' frequenti.

---

## 2. Layout Homepage

### 2.1 Struttura Generale

```
+------------------------------------------------------------------+
| Header: Nome azienda + Selettore periodo + Selettore conti       |
+------------------------------------------------------------------+
| KPI Cards (4 card in fila)                                       |
| [Saldo totale] [Entrate periodo] [Uscite periodo] [Variazione]  |
+------------------------------------------------------------------+
| Grafico Cash Flow Trend (Recharts line+bar chart)                |
| Entrate vs Uscite vs Saldo cumulativo                            |
+------------------------------------------------------------------+
| +---------------------------+ +--------------------------------+ |
| | Widget Scadenze           | | Widget Movimenti Recenti       | |
| | Imminenti (5-10)          | | (ultimi 10 non categorizzati)  | |
| +---------------------------+ +--------------------------------+ |
| +---------------------------+ +--------------------------------+ |
| | Widget Stato              | | Widget Saldi per Conto         | |
| | Riconciliazione           | | (breakdown per bank_account)   | |
| +---------------------------+ +--------------------------------+ |
+------------------------------------------------------------------+
```

### 2.2 Header Dashboard

- **Nome azienda**: da `companies.name` (company corrente)
- **Selettore periodo**: dropdown con preset (Ultimo mese, Ultimi 3 mesi, Ultimi 6 mesi, Anno corrente, Custom). Default: mese corrente
- **Selettore conti**: multi-select da `bank_accounts` con `status = 'ACTIVE'` e `hidden_at IS NULL`. Default: tutti i conti attivi

---

## 3. KPI Cards

### 3.1 Saldo Totale

| Proprieta' | Dettaglio |
|---|---|
| **Titolo** | "Saldo totale" |
| **Valore** | Somma di `bank_accounts.current_balance` per tutti i conti attivi selezionati con `ignore_balance = FALSE` |
| **Sottotitolo** | "Disponibile: {somma available_balance}" |
| **Tabella DB** | `bank_accounts` |
| **Query** | `SELECT SUM(current_balance) FROM bank_accounts WHERE company_id = :cid AND status = 'ACTIVE' AND hidden_at IS NULL AND ignore_balance = FALSE` |
| **Refresh rate** | Ad ogni navigazione alla dashboard + dopo sync bancaria |
| **Formato** | Valuta EUR con separatore migliaia |

### 3.2 Entrate del Periodo

| Proprieta' | Dettaglio |
|---|---|
| **Titolo** | "Entrate" |
| **Valore** | Somma `transactions.amount` dove `direction = 'INFLOW'` e `status = 'BOOKED'` nel periodo selezionato |
| **Sottotitolo** | "+{n} rispetto al periodo precedente" oppure "-{n}" (variazione assoluta) |
| **Tabella DB** | `transactions` |
| **Query** | `SELECT SUM(amount) FROM transactions WHERE company_id = :cid AND direction = 'INFLOW' AND status = 'BOOKED' AND transaction_date BETWEEN :start AND :end AND hidden_at IS NULL` |
| **Refresh rate** | Stessa della dashboard |
| **Icona colore** | Verde |

### 3.3 Uscite del Periodo

| Proprieta' | Dettaglio |
|---|---|
| **Titolo** | "Uscite" |
| **Valore** | Somma `ABS(transactions.amount)` dove `direction = 'OUTFLOW'` e `status = 'BOOKED'` nel periodo selezionato |
| **Sottotitolo** | Variazione rispetto al periodo precedente (stessa durata, mesi precedenti) |
| **Tabella DB** | `transactions` |
| **Query** | `SELECT SUM(ABS(amount)) FROM transactions WHERE company_id = :cid AND direction = 'OUTFLOW' AND status = 'BOOKED' AND transaction_date BETWEEN :start AND :end AND hidden_at IS NULL` |
| **Refresh rate** | Stessa della dashboard |
| **Icona colore** | Rosso |

### 3.4 Variazione Periodo

| Proprieta' | Dettaglio |
|---|---|
| **Titolo** | "Variazione netta" |
| **Valore** | Entrate - Uscite del periodo |
| **Sottotitolo** | Percentuale variazione rispetto al periodo precedente |
| **Calcolo** | `(entrate_periodo - uscite_periodo)` |
| **Colore** | Verde se positivo, rosso se negativo |

### 3.5 Variazione Rispetto al Periodo Precedente

```
periodo_precedente_start = start - (end - start)
periodo_precedente_end = start - 1 giorno

variazione_assoluta = valore_corrente - valore_precedente
variazione_percentuale = ((valore_corrente - valore_precedente) / ABS(valore_precedente)) * 100

Se valore_precedente == 0: mostrare solo variazione assoluta
```

Confidenza: 🟢 Alta (pattern derivato da docs/11 LB-REP-03 e LB-REP-04)

---

## 4. Grafico Cash Flow Trend

### 4.1 Specifiche Grafiche

| Proprieta' | Valore |
|---|---|
| **Libreria** | Recharts |
| **Tipo** | ComposedChart (BarChart + LineChart) |
| **Altezza** | 300px |
| **Barre** | Entrate (verde) e Uscite (rosso) per mese |
| **Linea** | Saldo cumulativo — continua per passato, tratteggiata per futuro (`strokeDasharray: 4`) |
| **Tooltip** | Mostra entrate, uscite, saldo per il mese hovering |
| **Larghezza colonna** | 77.5px |
| **Larghezza barra** | 16px |
| **Spessore linea** | 2px |
| **Font tick** | 13px |

Basato su: docs/05 LB-CF-09 (dominio Y), LB-CF-10 (separazione passato/futuro), docs/13 sezione 2.2 (costanti grafiche).

### 4.2 Dati del Grafico

Per ogni mese nel periodo selezionato:

```
{
  month, year,
  inflow: SUM(transactions.amount) WHERE direction='INFLOW' AND status='BOOKED',
  outflow: ABS(SUM(transactions.amount)) WHERE direction='OUTFLOW' AND status='BOOKED',
  balance_start: saldo inizio mese (da cash_flow_entries),
  balance_end: saldo fine mese (da cash_flow_entries)
}
```

### 4.3 Periodo Selezionabile

- Default: 6 mesi passati + 6 mesi futuri (come Sibill, docs/05 LB-CF-08)
- Minimo: 3 mesi
- Massimo: 12 mesi
- Range assoluto: da Gennaio 2020 a fine anno corrente + 5 anni

### 4.4 Separazione Passato/Futuro (LB-CF-10)

```
if mese/anno < mese_corrente/anno_corrente: "past"   → linea continua
if mese/anno == mese_corrente/anno_corrente: "current" → giunzione
if mese/anno > mese_corrente/anno_corrente: "future"  → linea tratteggiata
```

---

## 5. Widget Scadenze Imminenti

### 5.1 Dati

| Proprieta' | Dettaglio |
|---|---|
| **Fonte** | `invoice_payments` |
| **Query** | `SELECT ip.*, i.counterpart_name FROM invoice_payments ip JOIN invoices i ON ip.invoice_id = i.id WHERE ip.company_id = :cid AND ip.payment_status IN ('UNPAID', 'PARTIALLY_PAID') AND ip.due_date >= CURRENT_DATE ORDER BY ip.due_date ASC LIMIT 10` |
| **Colonne** | Controparte, Importo, Data scadenza, Giorni rimanenti, Direzione (badge INFLOW/OUTFLOW) |

### 5.2 Calcolo Giorni Rimanenti

```
giorni_rimanenti = due_date - CURRENT_DATE
Se giorni_rimanenti < 0: mostrare badge "Scaduto" (rosso) con |giorni| giorni
Se giorni_rimanenti == 0: mostrare badge "Oggi" (arancione)
Se giorni_rimanenti <= 7: mostrare badge "Urgente" (arancione)
Se giorni_rimanenti > 7: mostrare giorni_rimanenti + " gg" (grigio)
```

### 5.3 Azioni

- Click sulla riga: naviga al dettaglio della fattura (`/invoices/{invoice_id}`)
- Link "Vedi tutte": naviga a `/outstanding`

---

## 6. Widget Movimenti Recenti

### 6.1 Dati

| Proprieta' | Dettaglio |
|---|---|
| **Fonte** | `transactions` |
| **Query** | `SELECT * FROM transactions WHERE company_id = :cid AND hidden_at IS NULL AND status = 'BOOKED' ORDER BY transaction_date DESC, created_at DESC LIMIT 10` |
| **Variant filtro** | [MIGLIORAMENTO] Opzione per mostrare solo i non categorizzati (`category_id IS NULL`) |
| **Colonne** | Data, Descrizione (troncata a 50 char), Importo, Categoria (o badge "Non categorizzato") |

### 6.2 Azioni

- Click sulla riga: apre drawer laterale con dettaglio transazione e possibilita' di categorizzare
- Link "Vedi tutti": naviga a `/transactions/movements`

---

## 7. Widget Stato Riconciliazione

### 7.1 Dati

| Proprieta' | Dettaglio |
|---|---|
| **Percentuale riconciliata** | `(count(transactions con almeno 1 reconciliation_match confermato) / count(totale transactions BOOKED)) * 100` |
| **Partite aperte per aging** | Count di `invoice_payments` con `payment_status IN ('UNPAID','PARTIALLY_PAID')` raggruppate per fasce |
| **Tabelle** | `transactions`, `reconciliation_matches`, `invoice_payments` |

### 7.2 Aging Partite Aperte

```
Fasce di aging (basate su docs/11 pattern aging):
  0-30 giorni:   due_date >= CURRENT_DATE - 30 AND due_date <= CURRENT_DATE
  31-60 giorni:  due_date >= CURRENT_DATE - 60 AND due_date < CURRENT_DATE - 30
  61-90 giorni:  due_date >= CURRENT_DATE - 90 AND due_date < CURRENT_DATE - 60
  > 90 giorni:   due_date < CURRENT_DATE - 90
```

### 7.3 Visualizzazione

- Progress bar con percentuale riconciliata
- Mini-tabella aging con conteggio e importo per fascia
- Colori: verde (0-30), giallo (31-60), arancione (61-90), rosso (>90)
- Link "Gestisci": naviga a `/reconciliations`

---

## 8. Widget Saldi per Conto

[MIGLIORAMENTO] Sibill mostra i saldi nella pagina `/accounts`. Nel nostro gestionale li mostriamo anche nella dashboard per maggiore visibilita'.

### 8.1 Dati

| Proprieta' | Dettaglio |
|---|---|
| **Fonte** | `bank_accounts` JOIN `institutions` (via `bank_connections`) |
| **Query** | `SELECT ba.nickname, ba.iban, ba.current_balance, ba.available_balance, i.name as institution_name, i.icon_url FROM bank_accounts ba LEFT JOIN bank_connections bc ON ba.bank_connection_id = bc.id LEFT JOIN institutions i ON bc.institution_id = i.id WHERE ba.company_id = :cid AND ba.status = 'ACTIVE' AND ba.hidden_at IS NULL ORDER BY ba.current_balance DESC` |
| **Colonne** | Logo banca, Nome conto, IBAN (ultimi 4 digit), Saldo contabile, Saldo disponibile |

---

## 9. Empty State

### 9.1 Primo Accesso (Nessun Conto Collegato)

Basato su docs/05 (empty state Sibill) e docs/13 sezione 8.1:

```
Se count(bank_accounts WHERE company_id = :cid AND status = 'ACTIVE') == 0:
  Mostrare:
    - Illustrazione onboarding
    - Titolo: "Benvenuto nel tuo gestionale di tesoreria"
    - Sottotitolo: "Collega il tuo primo conto bancario per iniziare"
    - CTA primaria: "Collega conto bancario" → /accounts/connect
    - CTA secondaria: "Importa movimenti" → /import
    - [MIGLIORAMENTO] Checklist onboarding:
      [ ] Collega conto bancario
      [ ] Importa le prime fatture
      [ ] Configura le categorie
      [ ] Invita il tuo team
```

### 9.2 Conto Collegato ma Nessun Dato

```
Se count(bank_accounts ACTIVE) > 0 AND count(transactions) == 0:
  Mostrare:
    - Messaggio "Sincronizzazione in corso..."
    - Progress indicator
    - Testo: "I movimenti saranno visibili entro pochi minuti"
```

---

## 10. Responsive Design

### 10.1 Breakpoint

| Viewport | Layout |
|---|---|
| Desktop (>= 1440px) | Layout completo a 4 colonne KPI, 2 colonne widget |
| Laptop (1024-1439px) | 4 colonne KPI, 2 colonne widget (compresse) |
| Tablet (768-1023px) | 2 colonne KPI (2 righe), 1 colonna widget (stacked) |
| Mobile (< 768px) | 1 colonna KPI (4 righe), 1 colonna widget (stacked), grafico semplificato |

### 10.2 Mobile

- KPI cards diventano swipeable orizzontalmente
- Grafico ridotto a altezza 200px, senza label asse X (solo tooltip)
- Widget in stack verticale, collassabili
- Tabelle widget in formato card compatto (1 riga = 1 card)

---

## 11. Personalizzazione (P3)

[MIGLIORAMENTO] Non osservato in Sibill. Feature opzionale a bassa priorita'.

- Widget riordinabili via drag & drop
- Widget collassabili (stato salvato in `localStorage` o tabella `user_preferences`)
- Possibilita' di nascondere widget non utilizzati
- Preferenze per utente per company

---

## 12. API Endpoints

### 12.1 GET /api/v1/dashboard/summary

**Descrizione:** Endpoint aggregato per tutti i KPI della dashboard. Una singola chiamata per minimizzare la latenza.

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **Path** | `/api/v1/dashboard/summary` |
| **Auth** | Cookie session (httpOnly) |

**Query parameters:**

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `company_id` | UUID | Si | ID azienda |
| `period_start` | date | Si | Inizio periodo (YYYY-MM-DD) |
| `period_end` | date | Si | Fine periodo (YYYY-MM-DD) |
| `account_ids` | UUID[] | No | Filtro conti (default: tutti attivi) |

**Response (200):**

```json
{
  "balances": {
    "total_current": { "amount": "12093.43", "currency": "EUR" },
    "total_available": { "amount": "10190.17", "currency": "EUR" },
    "accounts_count": 2
  },
  "period": {
    "inflow_total": { "amount": "5645.30", "currency": "EUR" },
    "outflow_total": { "amount": "5181.79", "currency": "EUR" },
    "net_change": { "amount": "463.51", "currency": "EUR" },
    "previous_period": {
      "inflow_total": { "amount": "4800.00", "currency": "EUR" },
      "outflow_total": { "amount": "4500.00", "currency": "EUR" },
      "net_change": { "amount": "300.00", "currency": "EUR" }
    }
  },
  "reconciliation": {
    "total_transactions": 42,
    "reconciled_transactions": 35,
    "reconciliation_rate": 83.3,
    "aging": {
      "0_30": { "count": 5, "amount": "2500.00" },
      "31_60": { "count": 2, "amount": "1200.00" },
      "61_90": { "count": 1, "amount": "800.00" },
      "over_90": { "count": 0, "amount": "0.00" }
    }
  },
  "uncategorized_count": 7
}
```

### 12.2 GET /api/v1/dashboard/chart

**Descrizione:** Dati per il grafico cash flow trend.

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **Path** | `/api/v1/dashboard/chart` |

**Query parameters:**

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `company_id` | UUID | Si | ID azienda |
| `from` | date | Si | Data inizio |
| `to` | date | Si | Data fine |
| `account_ids` | UUID[] | No | Filtro conti |
| `timezone` | string | Si | Timezone (default: Europe/Rome) |

**Response (200):**

```json
{
  "data": [
    {
      "month": 9, "year": 2025,
      "inflow": { "amount": "5200.00", "currency": "EUR" },
      "outflow": { "amount": "4800.00", "currency": "EUR" },
      "balance_start": { "amount": "15000.00", "currency": "EUR" },
      "balance_end": { "amount": "15400.00", "currency": "EUR" },
      "time_position": "past"
    }
  ]
}
```

### 12.3 GET /api/v1/dashboard/upcoming-payments

**Descrizione:** Scadenze imminenti per il widget.

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **Path** | `/api/v1/dashboard/upcoming-payments` |

**Query parameters:**

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `company_id` | UUID | Si | ID azienda |
| `limit` | integer | No | Default: 10 |

**Response (200):**

```json
{
  "data": [
    {
      "id": "uuid",
      "invoice_id": "uuid",
      "counterpart_name": "Fornitore SRL",
      "amount": { "amount": "1500.00", "currency": "EUR" },
      "due_date": "2026-02-15",
      "days_remaining": 5,
      "direction": "OUTFLOW",
      "payment_status": "UNPAID"
    }
  ]
}
```

### 12.4 GET /api/v1/dashboard/recent-transactions

**Descrizione:** Movimenti recenti per il widget.

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **Path** | `/api/v1/dashboard/recent-transactions` |

**Query parameters:**

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `company_id` | UUID | Si | ID azienda |
| `limit` | integer | No | Default: 10 |
| `uncategorized_only` | boolean | No | Default: false |

**Response (200):**

```json
{
  "data": [
    {
      "id": "uuid",
      "transaction_date": "2026-02-09",
      "description": "Bonifico da Cliente SRL",
      "amount": { "amount": "1200.00", "currency": "EUR" },
      "direction": "INFLOW",
      "category_name": null,
      "bank_account_nickname": "Conto principale"
    }
  ]
}
```

### 12.5 GET /api/v1/dashboard/accounts-balances

**Descrizione:** Saldi per conto per il widget.

| Proprieta' | Valore |
|---|---|
| **Metodo** | GET |
| **Path** | `/api/v1/dashboard/accounts-balances` |

**Query parameters:**

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `company_id` | UUID | Si | ID azienda |

**Response (200):**

```json
{
  "data": [
    {
      "id": "uuid",
      "nickname": "Conto principale",
      "iban_last4": "1821",
      "institution_name": "UniCredit",
      "institution_icon_url": "https://...",
      "current_balance": { "amount": "8000.00", "currency": "EUR" },
      "available_balance": { "amount": "7500.00", "currency": "EUR" },
      "balance_date": "2026-02-10T10:00:00Z"
    }
  ]
}
```

---

## 13. Requisiti Funzionali

### FR-DASH-001: Visualizzazione KPI Saldo Totale

**Priorita':** P0

**Given** un utente autenticato con almeno un conto bancario attivo
**When** accede alla dashboard homepage
**Then** visualizza il saldo totale corrente aggregato di tutti i conti attivi non nascosti con `ignore_balance = FALSE`, formattato in EUR con separatore migliaia

---

### FR-DASH-002: Visualizzazione KPI Entrate/Uscite Periodo

**Priorita':** P0

**Given** un utente autenticato con transazioni nel periodo selezionato
**When** accede alla dashboard o cambia il periodo
**Then** visualizza il totale entrate e il totale uscite del periodo, calcolati dalle transazioni con `status = 'BOOKED'` e `hidden_at IS NULL`, con variazione rispetto al periodo precedente (stessa durata, mesi precedenti)

---

### FR-DASH-003: Grafico Cash Flow Trend

**Priorita':** P0

**Given** un utente autenticato con transazioni
**When** accede alla dashboard
**Then** visualizza un grafico combinato barre+linea con:
- Barre verdi (entrate) e rosse (uscite) per ogni mese
- Linea del saldo cumulativo continua per il passato, tratteggiata per il futuro
- Tooltip al hover che mostra entrate, uscite e saldo del mese
- Periodo default: 6 mesi passati + 6 mesi futuri

---

### FR-DASH-004: Widget Scadenze Imminenti

**Priorita':** P1

**Given** un utente autenticato con scadenze future non pagate
**When** accede alla dashboard
**Then** visualizza le prossime 10 scadenze ordinate per data, con controparte, importo, giorni rimanenti e badge di urgenza (scaduto/oggi/urgente/normale)

**Given** l'utente clicca su una scadenza
**When** la riga viene selezionata
**Then** naviga al dettaglio della fattura corrispondente

---

### FR-DASH-005: Widget Movimenti Recenti

**Priorita':** P1

**Given** un utente autenticato con transazioni
**When** accede alla dashboard
**Then** visualizza gli ultimi 10 movimenti bancari contabilizzati, con data, descrizione troncata, importo e categoria (o badge "Non categorizzato")

**Given** l'utente attiva il filtro "Solo non categorizzati"
**When** il toggle viene attivato
**Then** il widget mostra solo le transazioni con `category_id IS NULL`

---

### FR-DASH-006: Widget Stato Riconciliazione

**Priorita':** P1

**Given** un utente autenticato con transazioni e scadenze
**When** accede alla dashboard
**Then** visualizza: percentuale di riconciliazione (progress bar), aging delle partite aperte (0-30, 31-60, 61-90, >90 giorni) con conteggio e importo per fascia

---

### FR-DASH-007: Widget Saldi per Conto

**Priorita':** P1

**Given** un utente autenticato con conti bancari attivi
**When** accede alla dashboard
**Then** visualizza la lista dei conti con: logo banca, nome conto, IBAN (ultimi 4 cifre), saldo contabile e saldo disponibile

---

### FR-DASH-008: Selettore Periodo

**Priorita':** P0

**Given** un utente sulla dashboard
**When** seleziona un periodo diverso (preset o custom)
**Then** tutti i KPI, il grafico e i widget si aggiornano per riflettere il nuovo periodo. I preset disponibili sono: Ultimo mese, Ultimi 3 mesi, Ultimi 6 mesi, Anno corrente, Custom (con date picker)

---

### FR-DASH-009: Selettore Conti

**Priorita':** P1

**Given** un utente sulla dashboard con piu' conti bancari
**When** seleziona/deseleziona conti dal multi-select
**Then** tutti i KPI, il grafico e i widget si aggiornano filtrando solo i conti selezionati

---

### FR-DASH-010: Empty State Onboarding

**Priorita':** P0

**Given** un utente autenticato senza conti bancari collegati (`count(bank_accounts ACTIVE) == 0`)
**When** accede alla dashboard
**Then** visualizza la pagina di onboarding con: illustrazione, messaggio di benvenuto, CTA "Collega conto bancario", CTA "Importa movimenti", checklist onboarding

---

### FR-DASH-011: Responsive Mobile

**Priorita':** P2

**Given** un utente accede alla dashboard da dispositivo mobile (viewport < 768px)
**When** la pagina viene renderizzata
**Then** il layout si adatta: KPI cards in stack verticale (o swipeable), grafico ridotto a 200px, widget in stack verticale collassabili, tabelle in formato card compatto

---

### FR-DASH-012: Endpoint Aggregato Dashboard

**Priorita':** P0

**Given** il frontend carica la dashboard
**When** viene effettuata la chiamata API
**Then** una singola chiamata `GET /api/v1/dashboard/summary` restituisce tutti i KPI (saldi, entrate, uscite, variazione, riconciliazione, non categorizzati) per minimizzare il numero di round-trip

---

### FR-DASH-013: Navigazione dai Widget

**Priorita':** P1

**Given** un utente visualizza un widget sulla dashboard
**When** clicca su "Vedi tutti" o "Gestisci"
**Then** viene navigato alla pagina di dettaglio corrispondente:
- Scadenze → `/outstanding`
- Movimenti → `/transactions/movements`
- Riconciliazione → `/reconciliations`
- Conti → `/accounts`

---

## 14. Tabelle DB Coinvolte

| Tabella | Ruolo nella Dashboard |
|---|---|
| `bank_accounts` | Saldi, lista conti, filtro conti |
| `transactions` | KPI entrate/uscite, movimenti recenti, conteggio non categorizzati |
| `invoice_payments` | Scadenze imminenti, aging |
| `invoices` | Nome controparte per scadenze |
| `reconciliation_matches` | Percentuale riconciliazione |
| `cash_flow_entries` | Dati grafico (saldi inizio/fine mese pre-calcolati) |
| `categories` | Nome categoria per movimenti |
| `institutions` | Logo e nome banca per widget saldi |
| `bank_connections` | Join per ottenere institution |
| `companies` | Nome azienda nell'header |
