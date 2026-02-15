# PRD-08: Cash Flow e Previsioni

**Versione:** 1.0
**Data:** 10 febbraio 2026
**Modulo:** Cash Flow e Previsioni
**Basato su:** RE Sibill docs/05-cash-flow.md (10 algoritmi LB-CF-01..LB-CF-10), docs/13-regole-business.md, docs/04-api-reference.md sezione 5-6
**Contratto DB:** `.tmp/db-schema.md`

---

## 1. Panoramica

Il Cash Flow Previsionale e' il cuore della pianificazione di tesoreria. Mostra entrate e uscite attese per periodo, con drill-down per categoria, confronto tra consuntivo, previsionale e budget, e la possibilita' di impostare previsioni manuali.

In Sibill corrisponde alla pagina `/cashflow`, che combina:
- Un **grafico combinato** barre+linea (entrate/uscite + saldo cumulativo)
- Una **tabella gerarchica** espandibile per categoria/sottocategoria e mese
- Un **aside panel** per il dettaglio di ogni cella
- La gestione **budget/previsioni** per categoria

Il modulo aggrega dati da tre fonti: movimenti bancari (consuntivo), scadenze aperte (previsionale), e budget manuali.

---

## 2. Algoritmi — TUTTI I 10 ALGORITMI (LB-CF-01..LB-CF-10)

### 2.1 LB-CF-01: Aggregazione Dati Cash Flow

**ID:** LB-CF-01
**Nome:** Aggregazione Dati Cash Flow
**Confidenza:** 🟢 Alta (docs/05-cash-flow.md)

**Descrizione:** Il grafico e la tabella combinano dati da tre fonti distinte per ogni mese nel periodo selezionato.

**Input:**
- `transactions` (tabella DB) — movimenti bancari con `status = 'BOOKED'` e `hidden_at IS NULL`
- `invoice_payments` (tabella DB) — scadenze con `payment_status IN ('UNPAID', 'PARTIALLY_PAID', 'OVERDUE')`
- `budgets` (tabella DB) — previsioni manuali per categoria/mese
- Periodo selezionato (date inizio/fine)
- Conti selezionati (opzionale)

**Pseudocodice:**

```
Per ogni mese nel periodo selezionato:

  1. CONSUNTIVO (transactions_amount)
     = SUM(transactions.amount)
       WHERE status = 'BOOKED'
       AND hidden_at IS NULL
       AND transaction_date BETWEEN primo_giorno_mese AND ultimo_giorno_mese
       AND (account_ids IS NULL OR bank_account_id IN account_ids)
     Separati in:
       transactions_inflow  (WHERE direction = 'INFLOW')
       transactions_outflow (WHERE direction = 'OUTFLOW')

  2. PREVISIONALE - Scadenze Aperte (outstanding_amount)
     = SUM(invoice_payments.amount - invoice_payments.paid_amount)
       WHERE payment_status IN ('UNPAID', 'PARTIALLY_PAID')
       AND due_date BETWEEN primo_giorno_mese AND ultimo_giorno_mese
     Solo per mesi futuri o mese corrente
     Separati per direction: outstanding_inflow, outstanding_outflow

  3. PREVISIONALE - Scaduto (pastdue_amount)
     = SUM(invoice_payments.amount - invoice_payments.paid_amount)
       WHERE payment_status IN ('UNPAID', 'PARTIALLY_PAID', 'OVERDUE')
       AND due_date < primo_giorno_mese
     Riportato come scaduto nel mese di appartenenza
     Separati per direction: pastdue_inflow, pastdue_outflow

  4. BUDGET (budget_amount)
     = budgets.amount
       WHERE year = mese.year AND month = mese.month
       AND (category_id, subcategory_id, direction) corrispondono
```

**Output:** Tabella `cash_flow_entries` (aggregato per mese) + `cash_flow_categories` (dettaglio per categoria/mese)

---

### 2.2 LB-CF-02: Calcolo Saldo e Variazione

**ID:** LB-CF-02
**Nome:** Calcolo Saldo e Variazione
**Confidenza:** 🟢 Alta

**Descrizione:** Per ogni mese, calcola il saldo di inizio/fine mese e la variazione.

**Input:**
- `cash_flow_entries` (tabella DB) — `balance_start`, `balance_end` per mese
- Oppure calcolato da: saldo conto ad inizio periodo + somma progressiva dei movimenti

**Pseudocodice:**

```
Per ogni mese:
  saldo_inizio = cash_flow_entries.balance_start
  saldo_fine   = cash_flow_entries.balance_end
  variazione   = saldo_fine - saldo_inizio

Per il totale (riga "Variazione bilancio"):
  variazione_totale = SUM(variazione per ogni mese nel periodo)

Invariante: saldo_inizio[mese N+1] == saldo_fine[mese N]

Calcolo iniziale (mese piu' vecchio nel periodo):
  saldo_inizio = SUM(bank_accounts.current_balance)
                 - SUM(transactions.amount WHERE transaction_date >= primo_giorno_mese)
```

**Output:** Per ogni mese: `balance_start`, `balance_end`, `balance_change`

---

### 2.3 LB-CF-03: Inversione Segno per Uscite

**ID:** LB-CF-03
**Nome:** Inversione Segno per Uscite
**Confidenza:** 🟢 Alta

**Descrizione:** Il server restituisce importi positivi per entrambe le direzioni. La negazione avviene lato client per la visualizzazione.

**Input:**
- Importo dal server (sempre positivo per outflow)
- Flag `direction` (INFLOW/OUTFLOW)

**Pseudocodice:**

```
function inverti_segno(importo, direction):
    if direction == 'OUTFLOW':
        return -importo
    return importo

// Applicato a: tabella, grafico, aside panel
// Il server restituisce: outflow = 5000 (positivo)
// La UI mostra: outflow = -5000 (negativo)
```

**Output:** Importo con segno corretto per la visualizzazione

---

### 2.4 LB-CF-04: Gestione Budget / Previsioni

**ID:** LB-CF-04
**Nome:** Gestione Budget / Previsioni
**Confidenza:** 🟢 Alta

**Descrizione:** Il sistema di budget permette di inserire previsioni manuali per categoria o sottocategoria, per ogni mese e direzione.

**Input:**
- `budgets` (tabella DB) — `company_id`, `category_id`, `subcategory_id`, `direction`, `level`, `year`, `month`, `amount`
- Budget level: `CATEGORY` o `SUBCATEGORY`

**Pseudocodice:**

```
Livelli budget:
  CATEGORY     — budget a livello categoria (applica a tutte le sottocategorie)
  SUBCATEGORY  — budget a livello sottocategoria (override del budget categoria)

Conflitti (regola esclusione reciproca):
  Se si inserisce un budget a livello SUBCATEGORY
  quando esiste un budget CATEGORY per lo stesso mese/direzione/categoria:
    → Il budget CATEGORY viene ELIMINATO per quel mese

  Se si inserisce un budget a livello CATEGORY
  quando esistono budget SUBCATEGORY per lo stesso mese/direzione/categoria:
    → TUTTI i budget SUBCATEGORY vengono ELIMINATI per quel mese

  Warning mostrato all'utente prima della sovrascrittura:
    - "Il budget della sottocategoria sovrascrivera' il budget della categoria"
    - "Il budget della categoria sovrascrivera' i budget delle sottocategorie"

Validazione input budget:
  - Solo valori positivi (onlyPositive: true)
  - Solo numeri interi (maxDecimalPlaces: 0) → budgets.amount e' NUMERIC(15,0)
  - Valuta fissa: EUR
```

**Output:** Record in `budgets` creato/aggiornato/eliminato

---

### 2.5 LB-CF-05: Suggerimenti Budget

**ID:** LB-CF-05
**Nome:** Suggerimenti Budget
**Confidenza:** 🟢 Alta

**Descrizione:** Quando l'utente crea un budget, il sistema suggerisce 3 valori basati su dati storici.

**Input:**
- Mese e anno target
- Direzione (INFLOW/OUTFLOW)
- Categoria e sottocategoria
- Dati storici da `cash_flow_categories` o `transactions` aggregati

**Pseudocodice:**

```
function suggerimenti_budget(month, year, direction, category_id, subcategory_id):

  // 1. "Mese precedente" — valore del budget/consuntivo del mese M-1
  prev_month_data = get_month_data(month - 1, year, direction, category_id, subcategory_id)
  prev_month_value = prev_month_data.budget_amount OR prev_month_data.transactions_amount
  suggerimento_1 = prev_month_value

  // 2. "Media ultimi 3 mesi" — media(M-1, M-2, M-3)
  m1 = get_month_total(month - 1, year, ...)  // importo totale (consuntivo + scadenze)
  m2 = get_month_total(month - 2, year, ...)
  m3 = get_month_total(month - 3, year, ...)
  valid_months = [m1, m2, m3].filter(non_null)
  suggerimento_2 = ROUND(SUM(valid_months) / 3, 0, ROUND_HALF_UP)
  // NOTA: se meno di 3 mesi hanno dati, divide COMUNQUE per 3

  // 3. "Stesso mese anno precedente" — valore del mese M dell'anno Y-1
  prev_year_data = get_month_data(month, year - 1, direction, category_id, subcategory_id)
  suggerimento_3 = prev_year_data.budget_amount OR prev_year_data.transactions_amount

  return {
    prevMonthBudget: suggerimento_1,
    lastPeriodAverageBudget: suggerimento_2,
    prevYearBudget: suggerimento_3
  }
```

**Output:** 3 valori suggeriti per il form budget

---

### 2.6 LB-CF-06: Estensione Budget su Piu' Mesi

**ID:** LB-CF-06
**Nome:** Estensione Budget su Piu' Mesi
**Confidenza:** 🟢 Alta

**Descrizione:** L'utente puo' estendere un budget su N mesi successivi con la checkbox "Estendi".

**Input:**
- Dati budget (amount, direction, level, category_id, subcategory_id)
- Mese di partenza
- Numero di mesi di estensione (N > 0)

**Pseudocodice:**

```
function estendi_budget(data, mese_start, anno_start, num_mesi):
  // Validazione: se "Estendi" attivo, num_mesi deve essere > 0
  assert num_mesi > 0

  for i in range(0, num_mesi):
    mese = mese_start + i  // con wrap anno
    anno = anno_start + (mese_start + i - 1) / 12

    // 1. Elimina budget di livello opposto (se presente)
    opposite_level = 'SUBCATEGORY' if data.level == 'CATEGORY' else 'CATEGORY'
    existing_opposite = SELECT FROM budgets
      WHERE company_id = data.company_id
      AND category_id = data.category_id
      AND level = opposite_level
      AND month = mese AND year = anno
      AND direction = data.direction
    DELETE existing_opposite

    // 2. Se esiste budget stesso livello con importo diverso: aggiorna
    existing_same = SELECT FROM budgets
      WHERE company_id = data.company_id
      AND category_id = data.category_id
      AND subcategory_id = data.subcategory_id
      AND level = data.level
      AND month = mese AND year = anno
      AND direction = data.direction

    if existing_same AND existing_same.amount != data.amount:
      UPDATE budgets SET amount = data.amount WHERE id = existing_same.id

    // 3. Se non esiste: crea nuovo budget
    if NOT existing_same:
      INSERT INTO budgets (company_id, category_id, subcategory_id,
        direction, level, year, month, amount)
      VALUES (data.company_id, data.category_id, data.subcategory_id,
        data.direction, data.level, anno, mese, data.amount)
```

**Output:** N record `budgets` creati/aggiornati

---

### 2.7 LB-CF-07: Importo Residuo Budget

**ID:** LB-CF-07
**Nome:** Importo Residuo Budget
**Confidenza:** 🟢 Alta

**Descrizione:** Per ogni cella della tabella con un budget impostato, calcola quanto budget rimane o se si e' in over-budget.

**Input:**
- `budget_amount` — importo budget per la cella
- `transactions_amount` — consuntivo (movimenti contabilizzati)
- `outstanding_amount` — scadenze aperte
- `pastdue_amount` — scadenze scadute

**Pseudocodice:**

```
function importo_residuo(budget_amount, transactions_amount, outstanding_amount, pastdue_amount):
  total_used = transactions_amount + outstanding_amount + pastdue_amount
  residuo = budget_amount - total_used

  if residuo < 0:
    return { type: "OVER_BUDGET", amount: ABS(residuo) }
    // UI: badge rosso "Over budget: {amount} EUR"
  else if residuo > 0:
    return { type: "REMAINING", amount: residuo }
    // UI: testo verde "Rimanente: {amount} EUR"
  else:
    return { type: "EXACT", amount: 0 }
    // UI: testo "Budget esaurito"
```

**Output:** Tipo (OVER_BUDGET/REMAINING/EXACT) + importo per l'aside panel

---

### 2.8 LB-CF-08: Periodo Default

**ID:** LB-CF-08
**Nome:** Periodo Default
**Confidenza:** 🟢 Alta

**Descrizione:** Calcola il periodo default da mostrare all'apertura del cash flow.

**Input:**
- Data corrente (`CURRENT_DATE`)

**Pseudocodice:**

```
function periodo_default():
  oggi = CURRENT_DATE

  data_inizio = primo_giorno_del_mese(oggi - 5 mesi)
  data_fine   = ultimo_giorno_del_mese(oggi + 6 mesi)

  // Formato: "YYYY-MM-DD/YYYY-MM-DD"
  return format(data_inizio, "YYYY-MM-DD") + "/" + format(data_fine, "YYYY-MM-DD")

// Esempio: se oggi e' 10/02/2026
//   data_inizio = 2025-09-01 (settembre 2025)
//   data_fine   = 2026-08-31 (agosto 2026)
//   Periodo: 12 mesi (6 passati incluso il corrente + 6 futuri)

Vincoli:
  - Range minimo: 3 mesi
  - Range massimo: 12 mesi
  - Data minima assoluta: 2020-01-01
  - Data massima assoluta: ultimo giorno dell'anno corrente + 5 anni
```

**Output:** Stringa periodo "YYYY-MM-DD/YYYY-MM-DD"

---

### 2.9 LB-CF-09: Calcolo Dominio Y del Grafico

**ID:** LB-CF-09
**Nome:** Calcolo Dominio Y del Grafico
**Confidenza:** 🟢 Alta

**Descrizione:** Determina il range dell'asse Y del grafico combinato barre+linea.

**Input:**
- Array di dati mensili con: saldi, budget, totali entrate+scadenze, totali uscite+scadenze

**Pseudocodice:**

```
function calcola_dominio_y(data):
  y_min = 0
  y_max = 0

  for each mese in data:
    values = [
      mese.balance_start,
      mese.balance_end,
      mese.budgets_inflow,
      mese.budgets_outflow,
      mese.transactions_inflow + mese.outstanding_inflow + mese.pastdue_inflow,
      mese.transactions_outflow + mese.outstanding_outflow + mese.pastdue_outflow
    ]
    y_min = MIN(y_min, ...values)
    y_max = MAX(y_max, ...values)

  // Arrotondamento ai milliari (padding per leggibilita')
  y_min_arrotondato = y_min - (1000 + y_min % 1000)
  y_max_arrotondato = y_max + (1000 - y_max % 1000)

  return [y_min_arrotondato, y_max_arrotondato]

// Esempio:
//   y_min = -4200 → -4200 - (1000 + (-4200 % 1000)) = -4200 - (1000 + 800) = -6000
//   y_max = 15300 → 15300 + (1000 - (15300 % 1000)) = 15300 + (1000 - 300) = 16000
```

**Output:** Array [y_min, y_max] per la proprieta' `domain` di Recharts

---

### 2.10 LB-CF-10: Separazione Passato/Futuro nel Grafico

**ID:** LB-CF-10
**Nome:** Separazione Passato/Futuro nel Grafico
**Confidenza:** 🟢 Alta

**Descrizione:** La linea del saldo si divide in continua (passato) e tratteggiata (futuro) al mese corrente.

**Input:**
- Array di dati mensili con `month` e `year`
- Data corrente (`CURRENT_DATE`)

**Pseudocodice:**

```
function classifica_posizione_temporale(mese, anno):
  mese_corrente = EXTRACT(MONTH FROM CURRENT_DATE)
  anno_corrente = EXTRACT(YEAR FROM CURRENT_DATE)

  if anno < anno_corrente OR (anno == anno_corrente AND mese < mese_corrente):
    return "past"
  if anno == anno_corrente AND mese == mese_corrente:
    return "current"
  if anno > anno_corrente OR (anno == anno_corrente AND mese > mese_corrente):
    return "future"

// Per la linea del bilancio nel grafico:
function calcola_punti_linea(data):
  punti = []

  for each mese in data:
    posizione = classifica_posizione_temporale(mese.month, mese.year)
    punto = {
      month: mese.month,
      year: mese.year,
      balance: mese.balance_start,
      time_position: posizione
    }

    // Per ogni punto:
    if posizione != "future":
      punto.past_balance = mese.balance_start     // serie linea continua
    if posizione != "past":
      punto.future_balance = mese.balance_start    // serie linea tratteggiata

    // Il mese "current" appare in ENTRAMBE le serie (punto di giunzione)
    punti.push(punto)

  // Aggiunge punto finale (balance_end dell'ultimo mese)
  ultimo = data.last()
  mese_dopo = ultimo.month + 1
  anno_dopo = ultimo.year + (mese_dopo > 12 ? 1 : 0)
  mese_dopo = mese_dopo > 12 ? mese_dopo - 12 : mese_dopo

  punti.push({
    month: mese_dopo,
    year: anno_dopo,
    balance: ultimo.balance_end,
    future_balance: ultimo.balance_end
  })

  return punti

// Rendering Recharts:
// <Line dataKey="past_balance" strokeDasharray="0" stroke="#3b82f6" />
// <Line dataKey="future_balance" strokeDasharray="4" stroke="#3b82f6" />
```

**Output:** Array di punti con `past_balance` e `future_balance` per le due serie della linea

---

## 3. Tabella Gerarchica

### 3.1 Struttura

La tabella cash flow ha una struttura a righe gerarchiche espandibili:

```
+----------+--------+--------+--------+--------+--------+--------+--------+
| Etichetta | Set 25 | Ott 25 | Nov 25 | Dic 25 | Gen 26 | Feb 26 | Totale |
+==========+========+========+========+========+========+========+========+
| ▶ ENTRATE TOTALI  |  5200  |  4800  |  6100  |  3200  |  5600  |  4900  | 29800  |
|   ▶ Incassi       |  3000  |  2800  |  3500  |  1800  |  3200  |  2900  | 17200  |
|     POS            |  2000  |  1800  |  2500  |  1200  |  2200  |  1900  | 11600  |
|     Bonifici       |  1000  |  1000  |  1000  |   600  |  1000  |  1000  |  5600  |
|   ▶ Altro          |  2200  |  2000  |  2600  |  1400  |  2400  |  2000  | 12600  |
+----------+--------+--------+--------+--------+--------+--------+--------+
| ▶ USCITE TOTALI   | -4800  | -4500  | -5800  | -3000  | -5200  | -4600  | -27900 |
|   ▶ Gestione      | -2000  | -1800  | -2200  | -1200  | -2000  | -1800  | -11000 |
|     Affitto        | -1500  | -1500  | -1500  | -1500  | -1500  | -1500  | -9000  |
|     Utenze         |  -500  |  -300  |  -700  |   300  |  -500  |  -300  | -2000  |
+----------+--------+--------+--------+--------+--------+--------+--------+
| SALDO INIZIO      | 15000  | 15400  | 15700  | 16000  | 16200  | 16600  |        |
| SALDO FINE        | 15400  | 15700  | 16000  | 16200  | 16600  | 16900  |        |
| VARIAZIONE        |   400  |   300  |   300  |   200  |   400  |   300  |  1900  |
+----------+--------+--------+--------+--------+--------+--------+--------+
```

### 3.2 Tipi di Riga (docs/13 sezione 3.4)

| Tipo | Descrizione | Stile |
|---|---|---|
| `header` | Riga totale (ENTRATE TOTALI / USCITE TOTALI) | Grassetto, sfondo colorato |
| `category` | Categoria senza sottocategorie | Normale, indentata 1 livello |
| `category-with-subcategories` | Categoria con sottocategorie (freccia espansione) | Normale + icona expand |
| `subcategory` | Sottocategoria | Indentata 2 livelli, font piu' piccolo |

### 3.3 Dimensioni (docs/13 sezione 2.2)

| Elemento | Valore |
|---|---|
| Colonna label (sinistra) | 232px |
| Colonna totale (destra) | 120px |
| Colonne mesi (centro) | Equidistribuite nello spazio rimanente |

### 3.4 Visibilita' Categorie

L'utente puo' nascondere/mostrare categorie individualmente. La visibilita' e' salvata in `localStorage`:

```
Chiave: "cashflow-visibility-overrides-{inflow|outflow}"
Formato: { "categoryId": "hidden"|"shown", "categoryId:subcategoryId": "hidden"|"shown" }
Default: tutte visibili
```

Pattern basato su docs/13 sezione 9.

### 3.5 Ordinamento Categorie

| Opzione | Comportamento |
|---|---|
| `alphabetical` | Ordine alfabetico per `categories.name` |
| `amount-desc` | Ordine per totale importo decrescente (somma assoluta su tutti i mesi) |

---

## 4. Aside Panel

### 4.1 Apertura

Si apre al click su una cella della tabella (intersezione categoria x mese).

### 4.2 Contenuto

| Sezione | Descrizione |
|---|---|
| **Header** | Nome categoria, mese/anno, totale |
| **Tab Movimenti** | Lista movimenti (`transactions`) per quella categoria e mese |
| **Tab Scadenze** | Lista scadenze (`invoice_payments`) per quella categoria e mese |
| **Tab Ricorrenze** | Ricorrenze per quella categoria |
| **Budget** | Importo budget impostato, importo residuo (LB-CF-07), badge Over/Remaining |
| **Azione "Aggiungi previsione"** | Apre il form budget per la cella |
| **Azione "Vedi tutti"** | Naviga a `/transactions/movements` con filtri pre-applicati |

### 4.3 Dati Tab Movimenti

```
SELECT t.*, c.name as category_name
FROM transactions t
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.company_id = :cid
  AND t.category_id = :category_id
  AND t.direction = :direction
  AND t.status = 'BOOKED'
  AND t.hidden_at IS NULL
  AND t.transaction_date BETWEEN primo_giorno_mese AND ultimo_giorno_mese
ORDER BY t.transaction_date DESC
```

### 4.4 Dati Tab Scadenze

```
SELECT ip.*, i.counterpart_name, i.number
FROM invoice_payments ip
JOIN invoices i ON ip.invoice_id = i.id
WHERE ip.company_id = :cid
  AND ip.category_id = :category_id
  AND ip.direction = :direction
  AND ip.payment_status IN ('UNPAID', 'PARTIALLY_PAID')
  AND ip.due_date BETWEEN primo_giorno_mese AND ultimo_giorno_mese
ORDER BY ip.due_date ASC
```

---

## 5. Periodo e Granularita'

### 5.1 Granularita' Temporale

| Granularita' | Colonne | Uso tipico |
|---|---|---|
| **Mese** | 3-12 colonne | Default, vista operativa |
| **Trimestre** | 4-8 colonne | Vista strategica |
| **Anno** | 1-5 colonne | Confronto pluriennale |

### 5.2 Regole Periodo (docs/13 sezione 2.1)

| Vincolo | Valore |
|---|---|
| Range minimo | 3 mesi (o 1 trimestre o 1 anno) |
| Range massimo | 12 mesi (o 4 trimestri o 5 anni) |
| Data minima | 2020-01-01 |
| Data massima | Fine anno corrente + 5 anni |
| Default | -5 mesi / +6 mesi dal mese corrente (LB-CF-08) |

---

## 6. Budget

### 6.1 Creazione Budget

Il form di creazione budget si apre dall'aside panel o dal click sul valore budget nella cella.

| Campo | Tipo | Validazione | Fonte DB |
|---|---|---|---|
| Importo | Currency input | Solo interi positivi, NUMERIC(15,0) | `budgets.amount` |
| Estendi | Checkbox | Se attivo, `months` obbligatorio | — |
| Mesi estensione | Number input | > 0 se "Estendi" attivo | — |
| Livello | Automatico | CATEGORY se cella = categoria, SUBCATEGORY se cella = sottocategoria | `budgets.level` |

### 6.2 Suggerimenti (LB-CF-05)

Il form mostra 3 suggerimenti cliccabili:
1. **Mese precedente**: valore M-1
2. **Media ultimi 3 mesi**: media(M-1, M-2, M-3), arrotondamento ROUND_HALF_UP a 0 decimali
3. **Stesso mese anno precedente**: valore M dell'anno Y-1

### 6.3 Eliminazione Budget Futuri

- Si possono eliminare solo budget futuri (mese corrente e successivi)
- Conferma: "Vuoi eliminare {N} previsioni future per {nome_categoria}?"

---

## 7. Export

### 7.1 Export Excel

| Proprieta' | Valore |
|---|---|
| Formato | XLSX (Excel) |
| Contenuto | Stessa struttura della tabella UI: categorie x mesi + totali |
| Trigger | Pulsante "Esporta" nella toolbar |
| Tracking | `CASHFLOW_EXPORTED` |

### 7.2 [MIGLIORAMENTO] Export PDF

Sibill supporta solo Excel. Aggiungiamo:
- Export PDF con layout professionale (logo azienda, header, tabella formattata)
- Formato A4 landscape per tabelle larghe
- Include il grafico come immagine

### 7.3 [MIGLIORAMENTO] Export CSV

- CSV semplice per import in altri tool

---

## 8. Filtri

| Filtro | Tipo | Descrizione |
|---|---|---|
| Periodo | Range date (preset/custom) | 3-12 mesi |
| Conti | Multi-select | Filtra per `bank_account_id` |
| Direzione | Toggle tab | Entrate / Uscite (tab separate nella tabella) |
| Categorie | Toggle visibilita' | Nasconde/mostra categorie individuali |
| Ordinamento | Select | Alfabetico / Per importo decrescente |
| Solo previsionali | Checkbox | Mostra solo dati futuri |
| Solo consuntivo | Checkbox | Mostra solo dati passati (movimenti contabilizzati) |

---

## 9. API Endpoints

### 9.1 GET /api/v1/cashflow/chart

**Descrizione:** Dati per il grafico (saldi inizio/fine mese). Corrisponde a Sibill `/api/v1/cashflow/chart`.

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `company_id` | UUID | Si | ID azienda |
| `from` | datetime | Si | Inizio periodo (UTC) |
| `to` | datetime | Si | Fine periodo (UTC) |
| `timezone` | string | Si | Timezone (default: Europe/Rome) |
| `account_ids` | UUID[] | No | Filtro conti |
| `include_budgets` | boolean | No | Includi totali budget (default: false) |
| `include_overdue` | boolean | No | Includi scadute (default: false) |
| `include_pastdue` | boolean | No | Includi past due (default: false) |

**Response (200):**

```json
{
  "data": [
    {
      "month": 9, "year": 2025,
      "balance": {
        "start": { "amount": "15000.00", "currency": "EUR" },
        "end": { "amount": "15400.00", "currency": "EUR" }
      },
      "time_position": "past"
    }
  ]
}
```

### 9.2 GET /api/v1/cashflow/table

**Descrizione:** Dati per la tabella (dettaglio per mese x categoria x direzione). Corrisponde a Sibill `/api/v1/cashflow/table`.

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `company_id` | UUID | Si | ID azienda |
| `date_from` | datetime | Si | Inizio periodo |
| `date_to` | datetime | Si | Fine periodo |
| `timezone` | string | Si | Timezone |
| `account_ids` | UUID[] | No | Filtro conti |
| `include_budgets` | boolean | No | — |
| `include_overdue` | boolean | No | — |
| `include_pastdue` | boolean | No | — |

**Response (200):**

```json
{
  "data": [
    {
      "month": 9, "year": 2025,
      "direction": "INFLOW",
      "category_id": "uuid-or-null",
      "subcategory_id": "uuid-or-null",
      "transactions_amount": { "amount": "5200.00", "currency": "EUR" },
      "outstanding_amount": { "amount": "0.00", "currency": "EUR" },
      "pastdue_amount": { "amount": "0.00", "currency": "EUR" },
      "budget_amount": { "amount": "5000.00", "currency": "EUR" }
    }
  ]
}
```

### 9.3 GET /api/v1/cashflow/cell-detail

**Descrizione:** Dettaglio per l'aside panel (movimenti + scadenze per cella).

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `company_id` | UUID | Si | ID azienda |
| `month` | integer | Si | Mese (1-12) |
| `year` | integer | Si | Anno |
| `direction` | enum | Si | INFLOW / OUTFLOW |
| `category_id` | UUID | No | Filtro categoria |
| `subcategory_id` | UUID | No | Filtro sottocategoria |
| `tab` | string | Si | `transactions` / `payments` / `recurrences` |
| `page_size` | integer | No | Default: 20 |

**Response (200):**

```json
{
  "transactions": [
    {
      "id": "uuid",
      "transaction_date": "2025-09-15",
      "description": "Bonifico da Cliente SRL",
      "amount": { "amount": "1200.00", "currency": "EUR" },
      "counterpart_name": "Cliente SRL"
    }
  ],
  "budget": {
    "amount": { "amount": "5000.00", "currency": "EUR" },
    "remaining": { "type": "REMAINING", "amount": "800.00" }
  },
  "meta": { "total": 15, "page": { "size": 20, "cursor": null } }
}
```

### 9.4 POST /api/v1/budgets

**Descrizione:** Creazione/aggiornamento budget.

**Request body:**

```json
{
  "company_id": "uuid",
  "category_id": "uuid",
  "subcategory_id": "uuid-or-null",
  "direction": "OUTFLOW",
  "level": "CATEGORY",
  "year": 2026,
  "month": 3,
  "amount": 5000,
  "extend": false,
  "extend_months": 0
}
```

### 9.5 DELETE /api/v1/budgets/future

**Descrizione:** Eliminazione budget futuri per una categoria.

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `company_id` | UUID | Si | — |
| `category_id` | UUID | Si | — |
| `subcategory_id` | UUID | No | — |
| `direction` | enum | Si | INFLOW / OUTFLOW |
| `from_month` | integer | Si | Mese corrente |
| `from_year` | integer | Si | Anno corrente |

### 9.6 GET /api/v1/cashflow/export

**Descrizione:** Export Excel/CSV/PDF del cash flow.

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `company_id` | UUID | Si | — |
| `date_from` | datetime | Si | — |
| `date_to` | datetime | Si | — |
| `format` | string | Si | `xlsx`, `csv`, `pdf` |
| `account_ids` | UUID[] | No | — |

**Response:** File binary con header `Content-Disposition: attachment`

---

## 10. Requisiti Funzionali

### FR-CASH-001: Vista Tabella Cash Flow

**Priorita':** P0

**Given** un utente autenticato con transazioni e/o scadenze
**When** accede alla pagina cash flow
**Then** visualizza una tabella gerarchica con:
- Righe: categorie espandibili in sottocategorie, raggruppate per ENTRATE e USCITE
- Colonne: un mese per ogni mese nel periodo selezionato + colonna totale
- Valori: somma di consuntivo (transactions_amount) + scadenze (outstanding_amount) + scaduto (pastdue_amount) per cella
- Riga saldo: saldo inizio, saldo fine, variazione per ogni mese
- Periodo default: 6 mesi passati + 6 mesi futuri

---

### FR-CASH-002: Grafico Combinato

**Priorita':** P0

**Given** un utente nella pagina cash flow
**When** la pagina viene caricata
**Then** visualizza un grafico con:
- Barre verdi (entrate) e rosse (uscite) per ogni mese
- Linea del saldo cumulativo: continua per il passato, tratteggiata per il futuro (LB-CF-10)
- Tooltip al hover con dettaglio del mese
- Dominio Y calcolato con arrotondamento ai milliari (LB-CF-09)

---

### FR-CASH-003: Aggregazione Dati (LB-CF-01)

**Priorita':** P0

**Given** dati da transactions, invoice_payments e budgets
**When** il cash flow viene calcolato per un mese
**Then** i valori vengono aggregati secondo LB-CF-01:
- `transactions_amount` da movimenti BOOKED
- `outstanding_amount` da scadenze aperte (solo mesi futuri/corrente)
- `pastdue_amount` da scadenze scadute non pagate
- `budget_amount` da budget manuali
e gli importi OUTFLOW vengono negati per la visualizzazione (LB-CF-03)

---

### FR-CASH-004: Gestione Budget (LB-CF-04)

**Priorita':** P1

**Given** un utente nella pagina cash flow con feature budget abilitata
**When** clicca su "Aggiungi previsione" nell'aside panel
**Then** si apre un form con: importo (solo interi positivi EUR), checkbox "Estendi" con numero mesi, 3 suggerimenti (LB-CF-05). Alla conferma:
- Se esiste un budget di livello opposto per lo stesso mese: viene eliminato (conflitto LB-CF-04)
- Se "Estendi" attivo: il budget viene replicato su N mesi (LB-CF-06)

---

### FR-CASH-005: Suggerimenti Budget (LB-CF-05)

**Priorita':** P1

**Given** l'utente apre il form budget per una categoria/mese
**When** il form viene mostrato
**Then** vengono proposti 3 suggerimenti:
1. Mese precedente (valore M-1)
2. Media ultimi 3 mesi (media M-1,M-2,M-3 diviso 3, ROUND_HALF_UP, 0 decimali)
3. Stesso mese anno precedente (valore M di Y-1)
L'utente puo' cliccare un suggerimento per popolare il campo importo

---

### FR-CASH-006: Importo Residuo Budget (LB-CF-07)

**Priorita':** P1

**Given** una cella della tabella con budget impostato
**When** l'aside panel viene aperto
**Then** mostra l'importo residuo calcolato come: budget - (consuntivo + scadenze + scaduto). Se negativo: badge "Over budget". Se positivo: "Rimanente: X EUR"

---

### FR-CASH-007: Aside Panel Dettaglio

**Priorita':** P0

**Given** un utente nella tabella cash flow
**When** clicca su una cella (intersezione categoria x mese)
**Then** si apre un pannello laterale destro con:
- Tab "Movimenti": lista movimenti per quella categoria e mese
- Tab "Scadenze": lista scadenze per quella categoria e mese
- Tab "Ricorrenze": ricorrenze attive per quella categoria
- Sezione budget con importo e residuo
- Link "Vedi tutti" che naviga a `/transactions/movements` con filtri applicati

---

### FR-CASH-008: Selezione Periodo (LB-CF-08)

**Priorita':** P0

**Given** un utente nella pagina cash flow
**When** modifica il periodo tramite il selettore
**Then** la tabella e il grafico si aggiornano. Il periodo deve essere minimo 3 mesi, massimo 12 mesi, con data minima 2020-01-01 e data massima fine anno corrente + 5 anni

---

### FR-CASH-009: Espansione/Collasso Categorie

**Priorita':** P1

**Given** una categoria con sottocategorie nella tabella
**When** l'utente clicca sulla freccia di espansione
**Then** le sottocategorie vengono mostrate/nascoste sotto la categoria padre. Lo stato di espansione e' mantenuto durante la sessione

---

### FR-CASH-010: Visibilita' Categorie

**Priorita':** P2

**Given** un utente nella pagina cash flow
**When** nasconde una categoria tramite il menu contestuale
**Then** la categoria non viene piu' mostrata nella tabella. La preferenza viene salvata in `localStorage`. L'utente puo' ripristinare la visibilita' dal menu "Personalizza"

---

### FR-CASH-011: Ordinamento Categorie

**Priorita':** P2

**Given** un utente nella pagina cash flow
**When** seleziona un ordinamento (alfabetico o per importo)
**Then** le categorie vengono riordinate secondo il criterio scelto

---

### FR-CASH-012: Export Cash Flow

**Priorita':** P1

**Given** un utente nella pagina cash flow con dati
**When** clicca "Esporta" e seleziona il formato (Excel)
**Then** viene scaricato un file XLSX con la stessa struttura della tabella: categorie per righe, mesi per colonne, totali

**[MIGLIORAMENTO]** Formati aggiuntivi: CSV, PDF con layout professionale

---

### FR-CASH-013: Saldo e Variazione (LB-CF-02)

**Priorita':** P0

**Given** dati cash flow per il periodo selezionato
**When** la tabella viene renderizzata
**Then** la sezione inferiore mostra: saldo inizio mese, saldo fine mese, variazione (fine - inizio) per ogni colonna. Il saldo di inizio mese N+1 coincide con il saldo di fine mese N

---

### FR-CASH-014: Filtro per Conto

**Priorita':** P1

**Given** un utente con piu' conti bancari
**When** seleziona/deseleziona conti dal multi-select
**Then** tutti i dati (tabella, grafico, aside panel) vengono ricalcolati filtrando solo i movimenti dei conti selezionati

---

## 11. Tabelle DB Coinvolte

| Tabella | Ruolo nel Modulo |
|---|---|
| `transactions` | Dati consuntivi (movimenti contabilizzati) |
| `invoice_payments` | Dati previsionali (scadenze aperte) |
| `budgets` | Previsioni manuali per categoria/mese |
| `cash_flow_entries` | Dati aggregati per mese (pre-calcolati) |
| `cash_flow_categories` | Dettaglio per categoria/mese (pre-calcolati) |
| `categories` | Categorie di classificazione |
| `subcategories` | Sottocategorie |
| `bank_accounts` | Conti per filtro e saldi |
| `recurring_transactions` | Ricorrenze per previsionale |
| `export_batches` | Tracciabilita' export |
