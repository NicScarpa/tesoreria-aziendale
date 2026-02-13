# Regole di Business — Estratte dal JavaScript

**Data analisi:** 10 febbraio 2026
**Fonte:** File JavaScript in `assets/js-sources/`
**Metodologia:** Analisi statica del codice client-side (minificato ma leggibile)

---

## 1. Validazioni Client-Side

### 1.1 Login

**File:** `Login-DLieno2m.js`

| Campo | Validazione | Schema Zod | Confidenza |
|---|---|---|---|
| `username` (email) | Obbligatorio, formato email | `z.string().min(1).email()` | 🟢 Alta |
| `password` | Obbligatorio, almeno 1 carattere | `z.string().min(1)` | 🟢 Alta |

**Regole aggiuntive:**
- L'email viene forzata a **lowercase** prima dell'invio: `onChange: n => field.onChange(n.toLowerCase())` 🟢
- Errore 401 → messaggio `"error_wrong_credentials"` 🟢
- Altri errori → messaggio `"error_login_failed"` 🟢
- Redirect dopo login: parametro `?rd=` nella URL, oppure `AppRoot` (= `/cashflow`) 🟢
- Campo nascosto `cc-num` con `aria-hidden` e `inert` — probabilmente anti-autofill browser 🟡

### 1.2 Categorie e Sottocategorie

**File:** `categorization-utils-BD3ayecO.js`, `DeleteSubcategoryDialog-Z99Okfqh.js`, `CategorySearch-H5pZ_RC1.js`

| Campo | Validazione | Valore | Confidenza |
|---|---|---|---|
| Nome categoria | Lunghezza massima | **255 caratteri** | 🟢 Alta |
| Nome sottocategoria | Obbligatorio + lunghezza | `z.string().min(1).max(255)` | 🟢 Alta |
| Colore categoria | Obbligatorio | `z.string()` (formato hex) | 🟢 Alta |
| Ricerca categorie | Filtro regex | `new RegExp(escapeRegExp(query), "i")` — case insensitive | 🟢 Alta |

### 1.3 Budget / Previsioni

**File:** `CashFlowPage--BaMgJEI.js`

| Campo | Validazione | Valore | Confidenza |
|---|---|---|---|
| `budget.amount` | Opzionale, se presente deve essere numerico valido | `z.refine(isNumeric)` — verifica `isNaN` e valore non vuoto | 🟢 Alta |
| `budget.currency` | Stringa | Sempre `"EUR"` | 🟢 Alta |
| `extend` (checkbox) | Se attivo, `amount` diventa obbligatorio | Refine: `!extend \|\| (isNumeric(amount) && !isEmpty(amount))` | 🟢 Alta |
| `months` (estensione) | Se extend attivo, deve essere > 0 | Refine: `!extend \|\| months > 0` | 🟢 Alta |

**Regole input budget:**
- Solo valori positivi (`onlyPositive: true`) 🟢
- Massimo 0 decimali (`maxDecimalPlaces: 0`) — i budget sono in numeri interi 🟢
- Input con formattazione locale dei numeri (separatore migliaia) 🟢
- Rimozione punti (`.`) dall'input: `value.replaceAll(".", "")` 🟢

### 1.4 Consenso Accounting (SDI)

**File:** `AddAccountingConsent-DQhKurMl.js`

| Regola | Dettaglio | Confidenza |
|---|---|---|
| Pulsante conferma | Disabilitato finché: step !== 2 O checkbox non selezionata O operazione back in corso | 🟢 Alta |
| Checkbox conferma utente | Obbligatoria prima dell'autorizzazione SDI | 🟢 Alta |
| Step wizard | 3 step sequenziali, non si può saltare avanti | 🟢 Alta |

---

## 2. Costanti e Limiti

### 2.1 Limiti Generali

| Costante | Valore | Contesto | File | Confidenza |
|---|---|---|---|---|
| **Max lunghezza nome categoria** | 255 caratteri | Categorie e sottocategorie | `categorization-utils-BD3ayecO.js` | 🟢 Alta |
| **Pagina API (page size)** | 100 | Paginazione cursor-based per tutte le liste | `CashFlowPage--BaMgJEI.js` | 🟢 Alta |
| **Valuta predefinita** | `"EUR"` | Cash flow, budget, formattazione | `CashFlowPage--BaMgJEI.js` | 🟢 Alta |
| **Data minima periodo** | Gennaio 2020 | Selezione periodo cash flow | `CashNavigationTabs-DVUea4A9.js` | 🟢 Alta |
| **Data massima periodo** | Fine anno + 5 anni da oggi | Selezione periodo cash flow | `CashNavigationTabs-DVUea4A9.js` | 🟢 Alta |
| **Range mesi custom** | Min 3, Max 12 mesi | Se start > end-2 o start < end-11, viene ricalcolato | `CashNavigationTabs-DVUea4A9.js` | 🟢 Alta |
| **StaleTime query** | 30.000 ms (30 sec) | Cache sottocategorie | `DeleteSubcategoryDialog-Z99Okfqh.js` | 🟢 Alta |
| **StaleTime cashflow table** | 500 ms | Cache tabella cashflow | `CashNavigationTabs-DVUea4A9.js` | 🟢 Alta |
| **Modale max width** | 600 px | Consent, eliminazione, budget modal | Vari file | 🟢 Alta |
| **Modale budget max width** | 480 px | Modale budget/previsioni | `CashFlowPage--BaMgJEI.js` | 🟢 Alta |

### 2.2 Costanti Grafiche Cash Flow

| Costante | Valore | Uso | Confidenza |
|---|---|---|---|
| `ChartColumnWidth` | 77.5 px | Larghezza colonna barra nel grafico | 🟢 Alta |
| `Chart height` | 300 px | Altezza area grafico | 🟢 Alta |
| `FirstColumnWidth` | 232 px | Colonna label a sinistra | 🟢 Alta |
| `LastColumnWidth` | 120 px | Colonna totale a destra | 🟢 Alta |
| `Font size tick` | 13 px | Font size etichette assi | 🟢 Alta |
| `Bar size` | 16 px | Larghezza barre nel grafico | 🟢 Alta |
| `Line stroke width` | 2 px | Spessore linea bilancio | 🟢 Alta |

---

## 3. Enum e Stati delle Entità

### 3.1 Direzione Flusso (Cash Flow)

**File:** `CashFlowPage--BaMgJEI.js`

```
Direction:
  - INFLOW   → Entrate
  - OUTFLOW  → Uscite
```
Confidenza: 🟢 Alta

### 3.2 Livello Budget

**File:** `CashFlowPage--BaMgJEI.js`

```
BudgetLevel:
  - CATEGORY      → Budget a livello categoria
  - SUBCATEGORY   → Budget a livello sottocategoria
```
Confidenza: 🟢 Alta

### 3.3 Posizione Temporale

**File:** `CashFlowPage--BaMgJEI.js`

```
TimePosition:
  - "past"    → Periodo passato (prima del mese corrente)
  - "current" → Mese corrente
  - "future"  → Periodo futuro (dopo il mese corrente)
```
Determinata da: confronto tra mese/anno dell'item e data odierna.
Confidenza: 🟢 Alta

### 3.4 Tipo di Riga Cash Flow

**File:** `CashFlowPage--BaMgJEI.js`

```
RowType:
  - "header"                     → Riga totale (somma di tutte le categorie)
  - "category"                   → Categoria senza sottocategorie
  - "category-with-subcategories" → Categoria con sottocategorie espanse
  - "subcategory"                → Sottocategoria
```
Confidenza: 🟢 Alta

### 3.5 Suggerimenti Budget

**File:** `CashFlowPage--BaMgJEI.js`

```
SuggestionKey:
  - "prevMonthBudget"          → Valore del mese precedente
  - "lastPeriodAverageBudget"  → Media ultimi 3 mesi
  - "prevYearBudget"           → Stesso mese dell'anno precedente
```
Confidenza: 🟢 Alta

### 3.6 Opzioni di Ordinamento Cash Flow

```
SortOption:
  - "alphabetical"  → Ordine alfabetico per nome categoria
  - "amount-desc"   → Ordine per importo decrescente
```
Confidenza: 🟢 Alta

### 3.7 Tipo Condizione Regola (Categorizzazione)

**File:** `categorization-utils-BD3ayecO.js`

```
RuleConditionType:
  - Account          → Filtro per conto bancario
  - Keywords         → Filtro per parole chiave nella descrizione
  - TransactionType  → Filtro per tipo transazione
```
Confidenza: 🟢 Alta

### 3.8 Tipo Azione Regola

```
RuleActionType:
  - SetCategory  → Assegna categoria + sottocategoria
```
Confidenza: 🟢 Alta

### 3.9 Sorgente Categorizzazione

**File:** `math-BhNrZZhy.js`, `CashFlowPage--BaMgJEI.js`

```
CategorizationSource:
  - Automatic  → Categorizzata automaticamente (mostra icona robot 🤖)
  - (altro)    → Manuale o non specificata
```
Confidenza: 🟢 Alta

### 3.10 Stato Consent Bancario

**File:** `AddAccountingConsent-DQhKurMl.js`

```
ConsentStatus:
  - Authorized  → Consenso autorizzato
  - (altro)     → In attesa o in corso
```
Confidenza: 🟡 Media

### 3.11 Stato Pagamento (Scadenzario)

**File:** `CashFlowPage--BaMgJEI.js`

```
PaymentStatus:
  - ToPay  → Da pagare (usato nei filtri aside)
```
Confidenza: 🟢 Alta

### 3.12 Stato Transazione

**File:** `CashFlowPage--BaMgJEI.js`

```
TransactionStatus:
  - Booked  → Transazione contabilizzata
```
Confidenza: 🟡 Media

### 3.13 Tipo Documento (Fatture)

**File:** `DeleteSubcategoryDialog-Z99Okfqh.js`

```
DocumentType:
  - Invoice       → Fattura
  - CreditNote    → Nota di credito
  - DebitNote     → Nota di debito
  - Parcel        → Parcella
  - SelfInvoice   → Autofattura
  - Bill          → Corrispettivo
  - Other         → Altro (escluso dai filtri standard)
```
Confidenza: 🟢 Alta

---

## 4. Logiche di Calcolo Client-Side

### 4.1 📐 Calcolo Percentuale (Budget vs Actual)

**File:** `math-BhNrZZhy.js`

```pseudocode
function percentuale(actual, budget):
    bigBudget = BigNumber(budget)
    if bigBudget.isZero():
        return BigNumber(0)
    result = BigNumber(actual) / bigBudget * 100
    if result.isNaN():
        return BigNumber(0)
    return result
```

**Uso:** Mostrato come badge percentuale nella UI (es. "75%") con arrotondamento `ROUND_CEIL`.
Confidenza: 🟢 Alta

### 4.2 📐 Calcolo Percentuale di Importo

**File:** `math-BhNrZZhy.js`

```pseudocode
function percentualeImporto(percentuale, importo):
    return BigNumber(percentuale || "0") / 100 * BigNumber(importo).abs()
```
Confidenza: 🟢 Alta

### 4.3 📐 Calcolo Importo Residuo Budget

**File:** `CashFlowPage--BaMgJEI.js`

```pseudocode
function importoResiduo(actualAmount, outstandingAmount, budgetAmount, pastdueAmount):
    amounts = [outstandingAmount, actualAmount, pastdueAmount].filter(nonNull)
    totalUsed = amounts.reduce(sum, budgetAmount)
    diff = diff(Money(0, "EUR"), totalUsed)
    return max(diff, null)
```

**Uso:** Mostrato come "Rimanente" o "Over budget" nell'aside panel.
Confidenza: 🟢 Alta

### 4.4 📐 Suggerimenti Budget

**File:** `CashFlowPage--BaMgJEI.js`

```pseudocode
function suggerimentiBudget(month, year, direction, categoryId, subcategoryId):
    // Dati storici dalla tabella cashflow
    data = cashflowData.filter(direction, categoryId, subcategoryId)

    // 1. Mese precedente
    prevMonth = getMonthData(data, month-1, year)

    // 2. Media ultimi 3 mesi
    m1 = getMonthData(data, month-1, year)
    m2 = getMonthData(data, month-2, year)
    m3 = getMonthData(data, month-3, year)
    validMonths = [m1, m2, m3].filter(nonNull)
    avg = sum(validMonths) / 3   // Arrotondamento: ROUND_HALF_UP, 0 decimali

    // 3. Stesso mese anno precedente
    prevYear = getMonthData(data, month, year-1)

    return { prevMonth, lastPeriodAverage: avg, prevYear }
```
Confidenza: 🟢 Alta

### 4.5 📐 Aggregazione Dati Cash Flow

**File:** `CashFlowPage--BaMgJEI.js`

```pseudocode
function aggregaCashFlow(balanceData, tableData, budgets):
    result = []
    for each month/year in balanceData:
        entry = {
            balance: { start, end },
            transactions: { inflow: 0, outflow: 0 },
            budgets: { inflow: 0, outflow: 0 },
            outstanding: { inflow: 0, outflow: 0 },
            pastdue: { inflow: 0, outflow: 0 }
        }

        // Aggrega tableData per mese
        for each row in tableData where month/year match:
            if row.is_inflow:
                entry.transactions.inflow += row.transactionsAmount
                entry.outstanding.inflow += row.outstandingAmount
                entry.pastdue.inflow += row.pastdueAmount
            else:
                entry.transactions.outflow += row.transactionsAmount
                entry.outstanding.outflow += row.outstandingAmount
                entry.pastdue.outflow += row.pastdueAmount

        // Aggrega budgets per mese
        for each budget where month/year match:
            if budget.direction == INFLOW:
                entry.budgets.inflow += budget.amount
            else:
                entry.budgets.outflow += budget.amount

        result.push(entry)
    return result
```
Confidenza: 🟢 Alta

### 4.6 📐 Calcolo Variazione Bilancio

```pseudocode
balanceChange = balance.end - balance.start
```
Per mese e per totale (somma di tutti i mesi).
Confidenza: 🟢 Alta

### 4.7 📐 Calcolo Punti Linea Bilancio (Grafico)

**File:** `CashFlowPage--BaMgJEI.js`

```pseudocode
function calcolaLineBilancio(data):
    points = data.map(month => {
        balance: month.balance.start
        month, year
    })

    // Aggiunge punto finale (balance.end dell'ultimo mese)
    lastMonth = data.last()
    nextMonthDate = addMonths(Date(lastMonth.year, lastMonth.month-1, 1), 1)
    points.push({
        balance: lastMonth.balance.end,
        month: nextMonthDate.month,
        year: nextMonthDate.year
    })

    // Separa in past e future per linea continua/tratteggiata
    for each point:
        if timePosition != "future": pastBalance = point.balance
        if timePosition != "past": futureBalance = point.balance

    return points
```

> 🔵 **NOTA**: La linea del bilancio nel grafico è divisa in due serie: linea continua per il passato e linea tratteggiata (`strokeDasharray: 4`) per il futuro. Il punto dove le due linee si incontrano è il mese corrente.

Confidenza: 🟢 Alta

### 4.8 📐 Calcolo Dominio Y del Grafico

```pseudocode
function calcolaDominioY(data):
    min = 0, max = 0
    for each month in data:
        values = [
            balance.start, balance.end,
            budgets.inflow, budgets.outflow,
            transactions.inflow + outstanding.inflow + pastdue.inflow,
            transactions.outflow + outstanding.outflow + pastdue.outflow
        ]
        min = Math.min(min, ...values)
        max = Math.max(max, ...values)

    // Arrotondamento ai milliari
    yMin = min - (1000 + min % 1000)
    yMax = max + (1000 - max % 1000)
    return [yMin, yMax]
```
Confidenza: 🟢 Alta

### 4.9 📐 Inversione Segno per Outflow

**File:** `CashFlowPage--BaMgJEI.js`

```pseudocode
function invertiSegno(money, isOutflow):
    if isOutflow:
        return negate(money)  // Inverte il segno
    return money

// Usato per: tutti gli importi outflow nel grafico e nella tabella
// Gli importi vengono negati per la visualizzazione
```

> 🟡 **ATTENZIONE**: Gli importi outflow vengono NEGATI lato client per la visualizzazione. Il server restituisce importi positivi per entrambe le direzioni. La negazione avviene nella funzione `pt(money, isOutflow)`.

Confidenza: 🟢 Alta

---

## 5. Messaggi di Errore e Contesto

### 5.1 Messaggi Login

| Chiave i18n | Contesto | Trigger |
|---|---|---|
| `auth.login.error_wrong_credentials` | Credenziali errate | HTTP 401 |
| `auth.login.error_login_failed` | Errore generico login | Qualsiasi altro errore HTTP |

### 5.2 Messaggi Cash Flow

| Chiave i18n | Contesto |
|---|---|
| `cashflow.messages.failed_budget_edit` | Errore modifica budget |
| `cashflow.messages.success_forecasts_delete` | Successo eliminazione previsioni |
| `cashflow.messages.failed_forecasts_delete` | Errore eliminazione previsioni |
| `cashflow.messages.failed_cashflow_export` | Errore export Excel |
| `cashflow.aside.prediction_modal.error_message` | Errore nel modal previsioni |
| `cashflow.chart.no_data` | Nessun dato nel grafico |
| `cashflow.chart.loading` | Caricamento grafico |

### 5.3 Messaggi Categorie

| Chiave i18n | Contesto |
|---|---|
| `transactions.edit_modal.messages.failed` | Errore cambio categoria transazione |
| `categorization.delete_category_dialog.messages.operation_completed` | Successo eliminazione categoria |
| `categorization.delete_category_dialog.messages.operation_failed` | Errore eliminazione categoria |
| `categorization.delete_subcategory_dialog.messages.operation_completed` | Successo eliminazione sottocategoria |
| `categorization.delete_subcategory_dialog.messages.operation_failed` | Errore eliminazione sottocategoria |
| `categorization.create_subcategory_dialog.messages.operation_failed` | Errore creazione sottocategoria |
| `categorization.category_search_popover.creation_failed` | Errore creazione categoria |

### 5.4 Messaggi Consent

| Chiave i18n | Contesto |
|---|---|
| `consents.add_account.error` | Errore creazione consent bancario |

---

## 6. Tracking Events (Analytics)

**File:** `CashFlowPage--BaMgJEI.js`, `categorization-utils-BD3ayecO.js`

| Evento | Trigger | Confidenza |
|---|---|---|
| `TRANSACTION_CATEGORY_ASSIGNED` | Prima categorizzazione di una transazione | 🟢 |
| `TRANSACTION_CATEGORY_EDITED` | Modifica categoria di una transazione | 🟢 |
| `TRANSACTION_SUBCATEGORY_ASSIGNED` | Prima assegnazione sottocategoria | 🟢 |
| `TRANSACTION_SUBCATEGORY_EDITED` | Modifica sottocategoria | 🟢 |
| `SUBCATEGORY_CREATED` | Creazione nuova sottocategoria | 🟢 |
| `SUBCATEGORY_DELETED` | Eliminazione sottocategoria | 🟢 |
| `BUDGET_VALUE_INSERTED` | Inserimento nuovo valore budget | 🟢 |
| `BUDGET_VALUE_UPDATED` | Modifica valore budget | 🟢 |
| `BUDGET_VALUE_SEQUENCE_DELETED` | Eliminazione sequenza budget | 🟢 |
| `BUDGET_VALUE_MADE_RECURRENT` | Budget esteso su più mesi | 🟢 |
| `CASHFLOW_VIEW_UTILISED` | Qualsiasi interazione con la vista cashflow | 🟢 |
| `CASHFLOW_EXPORTED` | Export Excel del cashflow | 🟢 |
| `CASHFLOW_SUBCATEGORIES_EXPANDED` | Espansione tutte le sottocategorie | 🟢 |
| `CASHFLOW_SUBCATEGORIES_COLLAPSED` | Collasso tutte le sottocategorie | 🟢 |
| `CASHFLOW_CATEGORIES_SORTED` | Cambio ordinamento categorie | 🟢 |
| `CASHFLOW_DISPLAY_CATEGORY_CLICKED` | Click su "mostra categoria" | 🟢 |
| `CASHFLOW_DISPLAY_SUBCATEGORY_CLICKED` | Click su "mostra sottocategoria" | 🟢 |
| `CASHFLOW_EDIT_CATEGORY_CLICKED` | Click su modifica categoria | 🟢 |
| `CASHFLOW_EDIT_SUBCATEGORY_CLICKED` | Click su modifica sottocategoria | 🟢 |
| `CASHFLOW_DELETE_CATEGORY_BUDGET_CLICKED` | Click su elimina budget categoria | 🟢 |
| `CASHFLOW_DELETE_SUBCATEGORY_BUDGET_CLICKED` | Click su elimina budget sottocategoria | 🟢 |
| `CASHFLOW_CATEGORY_HIDDEN` | Categoria nascosta | 🟢 |
| `CASHFLOW_SUBCATEGORY_HIDDEN` | Sottocategoria nascosta | 🟢 |
| `CASHFLOW_VIEW_ALL_ITEMS_CLICKED` | Click su "vedi tutti" nell'aside | 🟢 |
| `RIGHT_SIDEBAR_TAB_CLICKED` | Cambio tab nell'aside panel | 🟢 |
| `FLOWS_CATEGORY_ASSIGNED` | Categorizzazione da panel flows | 🟢 |
| `FLOWS_CATEGORY_EDITED` | Modifica categoria da panel flows | 🟢 |
| `FLOWS_SUBCATEGORY_ASSIGNED` | Sottocategoria da panel flows | 🟢 |
| `FLOWS_SUBCATEGORY_EDITED` | Modifica sottocategoria da panel flows | 🟢 |

---

## 7. Effetti Collaterali Eliminazione

### 7.1 Eliminazione Categoria

**File:** `DeleteSubcategoryDialog-Z99Okfqh.js`

Quando si elimina una **categoria**, vengono impattati:
1. ✅ **Transazioni** — Le transazioni con questa categoria perdono la categorizzazione
2. ✅ **Fatture** (Invoice, CreditNote, DebitNote, Parcel, SelfInvoice) — Perdono la categorizzazione
3. ✅ **Corrispettivi** (Bill) — Perdono la categorizzazione
4. ✅ **Sottocategorie** — Tutte le sottocategorie vengono eliminate
5. ✅ **Regole** — Le regole che usano questa categoria vengono eliminate
6. ✅ **Budget** — I budget associati vengono eliminati
7. ✅ **Ricorrenze** — Le ricorrenze con questa categoria perdono la categorizzazione

**UI:** Mostra conteggio per transazioni, fatture e corrispettivi. Richiede checkbox di conferma.

### 7.2 Eliminazione Sottocategoria

Stessi effetti della categoria, più:
- Opzione **"Rimuovi categorizzazione"** → `mark_uncategorised`
- Opzione **"Assegna alla categoria padre"** → `parent_category`
- Le opzioni vengono mostrate separatamente per transazioni, fatture e corrispettivi

### 7.3 Eliminazione Previsioni Budget

Per categorie e sottocategorie, è possibile eliminare solo i budget **futuri** (mese corrente e successivi). La conferma mostra il numero di mesi rimanenti.

---

## 8. Pattern di Upsell e Gating

### 8.1 Cash Flow Access

**File:** `CashSection-Dtvj5QpP.js`

```pseudocode
if NOT hasCashflowFeature():
    show UpsellPage:
        - Titolo: "upsell.title"
        - Box 1: Illustrazione + link Calendly per upgrade
          → window.open("https://calendly.com/cs--sibill/plan-upgrade")
        - Box 2: Demo interattiva
          → window.open("https://sibill.navattic.com/cashflow")
    return

if isTrialUser() AND noConsents:
    redirect to AppRoot

if hasConsents AND connectionState == "first_connection":
    show EmptyState with:
        - AddBankingAction (connetti banca)
        - AddAccountingAction (connetti Cassetto Fiscale)
```
Confidenza: 🟢 Alta

### 8.2 Budget Feature Gating

I budget nel cash flow sono condizionati da una feature del piano. Se il piano non li supporta:
- Il campo budget non viene mostrato nelle celle
- L'header non mostra i totali budget
- L'aside panel non mostra il pulsante "Aggiungi previsione"

Confidenza: 🟢 Alta

---

## 9. Gestione Visibilità Categorie

**File:** `CashFlowPage--BaMgJEI.js`

Il sistema di visibilità usa un pattern di **override** su localStorage:

```pseudocode
// Storage key: "cashflow-visibility-overrides-{direction}"
// Formato: { "categoryId": "hidden" | "shown", "categoryId:subcategoryId": "hidden" | "shown" }

// Default: tutte le categorie sono visibili
// "shown" = override per mostrare una categoria che altrimenti sarebbe nascosta
// "hidden" = override per nascondere una categoria
// assenza = comportamento default (visibile)
```

**Azioni:**
- `hideCategory(catId, subCatId)` → aggiunge override "hidden"
- `showCategory(catId, subCatId)` → aggiunge override "shown"
- Le categorie "shown" permettono di aggiungere categorie alla vista dalla lista

Confidenza: 🟢 Alta

---

## 10. Formattazione Numeri e Date

### 10.1 Importi

**Pattern:** `formatCurrency(money)` → formattazione locale con separatore migliaia e simbolo valuta.

**Logica:** Se il valore è finito e diverso da 0, viene formattato. Altrimenti viene mostrato il fallback (`"-"`). Il segno può essere incluso tramite flag `sign`.

### 10.2 Date

**Pattern:** date-fns `format()` con formati:
- `"dd/MM/yy"` — Date nelle tabelle (es. "10/02/26")
- `"MMM yy"` — Header colonne cash flow (es. "feb 26")
- `"MMMM yyyy"` — Modale budget (es. "febbraio 2026")
- `"MMMM yy"` — Tooltip (es. "febbraio 26")
- `"MMMM"` — Nome mese (es. "febbraio")
- `"yyyy"` — Anno

**Capitalizzazione:** La prima lettera del mese viene capitalizzata con `capitalize()` per la visualizzazione.

### 10.3 Periodo Default

```pseudocode
defaultPeriod = "startDate/endDate"
// dove:
startDate = startOfMonth(subMonths(today, 5))   // 5 mesi fa
endDate = endOfMonth(addMonths(today, 6))         // 6 mesi avanti
// Formato: "YYYY-MM-DD/YYYY-MM-DD"
```
Confidenza: 🟢 Alta

---

## 11. Regole di Categorizzazione Automatica

**File:** `categorization-utils-BD3ayecO.js`

Le regole di categorizzazione automatica hanno la struttura:

```pseudocode
Rule:
  conditions:
    - type: Account     → filtra per ID conto bancario
    - type: Keywords    → filtra per parole chiave nella descrizione
    - type: TransactionType → filtra per tipo transazione (bonifico, SDD, etc.)
  actions:
    - type: SetCategory → { category_id, subcategory_id }
```

**Estrazione dati dalla regola:**
- `extractCategory(rule)` → `{ categoryId, subcategoryId }` dalla prima azione SetCategory
- `extractAccount(rule)` → primo account ID dalla condizione Account
- `extractKeywords(rule)` → lista parole chiave dalla condizione Keywords
- `extractTransactionTypes(rule)` → lista tipi transazione dalla condizione TransactionType

**Direzione transazione:**
- Il parametro URL `direction` determina se filtrare per `Inflow` o `Outflow`

Confidenza: 🟢 Alta

---

## 12. Gestione Budget Multi-livello

**File:** `CashFlowPage--BaMgJEI.js`

### 12.1 Conflitti Budget Categoria vs Sottocategoria

Quando si inserisce un budget a livello **categoria** e esistono già budget a livello **sottocategoria** (o viceversa), la logica è:

```pseudocode
function handleBudgetChangeWithCleanup(change):
    // 1. Trova budget esistenti di livello opposto
    conflictingBudgets = budgets.filter(
        b.level != targetLevel
        AND b.month == change.month
        AND b.year == change.year
        AND b.direction == change.direction
        AND b.category.id == change.categoryId
    )

    // 2. Se il budget corrente è uno dei conflicting, reset budgetId
    if conflictingBudgets.includes(change.item.budgetId) AND hasValue:
        change.item.budgetId = null

    // 3. Elimina budget conflicting
    if conflictingBudgets.length > 0:
        delete(conflictingBudgets.map(b => b.id))

    // 4. Crea/aggiorna il budget target
    upsertBudget(change)
```

### 12.2 Estensione Budget su Più Mesi

```pseudocode
function extendBudget(data, startMonth, endMonth, startYear, endYear):
    // Per ogni mese nell'intervallo:
    for each month in range(start, end):
        // Elimina budget di livello opposto
        existingOpposite = findBudgets(oppositeLevel, month, year)
        delete(existingOpposite)

        // Se esiste budget stesso livello, aggiorna se diverso
        existing = findBudget(sameLevel, month, year)
        if existing AND existing.amount != data.amount:
            update(existing.id, amount)

        // Se non esiste, crea
        if NOT existing:
            create(newBudget)
```
Confidenza: 🟢 Alta

### 12.3 Warning Budget

Due warning vengono mostrati nell'input budget:
1. **Sottocategoria con budget categoria padre:** "Il budget della sottocategoria sovrascriverà il budget della categoria"
2. **Categoria con budget sottocategorie:** "Il budget della categoria sovrascriverà i budget delle sottocategorie"

Confidenza: 🟢 Alta

---

## 13. Pattern di Azione nell'Eliminazione Sottocategoria

**File:** `DeleteSubcategoryDialog-Z99Okfqh.js`

Quando si elimina una sottocategoria con transazioni/fatture/corrispettivi associati, l'utente può scegliere per ciascun tipo:

| Azione | Valore | Effetto |
|---|---|---|
| (nessuna selezione) | `""` | Blocca il pulsante conferma |
| Rimuovi categorizzazione | `"mark_uncategorised"` | Rimuove categoria e sottocategoria |
| Assegna alla categoria padre | `"parent_category"` | Mantiene la categoria, rimuove la sottocategoria |

Il pulsante conferma è disabilitato se:
- La checkbox di conferma non è selezionata, OPPURE
- Ci sono transazioni > 0 e nessuna azione selezionata, OPPURE
- Ci sono fatture > 0 e nessuna azione selezionata, OPPURE
- Ci sono corrispettivi > 0 e nessuna azione selezionata

Confidenza: 🟢 Alta
