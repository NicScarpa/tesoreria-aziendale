# Cash Flow e Previsioni — Analisi Funzionale

**Data analisi:** 10 febbraio 2026
**Modulo:** Cash Flow e Previsioni
**URL principale:** `/cashflow`
**URL categorie:** `/cashflow/categories`

---

## Panoramica

Il modulo Cash Flow e' la **dashboard principale** di Sibill. Dopo il login, l'utente viene reindirizzato a `/cashflow`. Il modulo offre una visione consolidata dei flussi di cassa aziendali, combinando dati consuntivi (movimenti bancari) e previsionali (scadenze, budget, ricorrenze) in un'unica vista temporale.

Lo scopo principale e': monitorare la posizione di cassa attuale, prevedere i flussi futuri, e confrontare previsioni con consuntivi per identificare scostamenti.

---

## Interfaccia

### Layout Principale

La pagina `/cashflow` e' organizzata in tre aree principali:

1. **Barra di navigazione temporale** (in alto)
   - Selettore di periodo con preset: ultimi 6 mesi + prossimi 6 mesi (default)
   - Possibilita' di selezionare periodi custom (min 3 mesi, max 12 mesi) 🟢
   - Range assoluto: da Gennaio 2020 a fine anno corrente + 5 anni 🟢
   - Filtro per conti bancari (multi-select)

2. **Grafico a barre e linea** (area centrale, altezza 300px)
   - Barre verticali: entrate (positive) e uscite (negative) per mese
   - Linea sovrapposta: andamento del saldo di bilancio
   - La linea e' **continua per il passato** e **tratteggiata per il futuro** (`strokeDasharray: 4`) 🟢
   - Larghezza colonna: 77.5px, larghezza barra: 16px, spessore linea: 2px 🟢

3. **Tabella dettagliata** (area inferiore)
   - Colonna label a sinistra (232px) con categorie espandibili
   - Colonne mensili al centro
   - Colonna totale a destra (120px)
   - Righe raggruppate per: Entrate totali → categorie → sottocategorie, Uscite totali → categorie → sottocategorie
   - Riga bilancio (saldo inizio/fine mese, variazione)

### 🎨 PATTERN UI/UX — Tabella Cash Flow

La tabella cash flow usa un pattern di **espansione gerarchica**:
- **Header row**: totale entrate/uscite (grassetto, sfondo colorato)
- **Category row**: categoria senza sottocategorie (click per espandere)
- **Category-with-subcategories**: categoria con sottocategorie (freccia espansione)
- **Subcategory row**: sottocategoria (indentata)

Le categorie possono essere nascoste/mostrate individualmente. La visibilita' e' salvata in `localStorage` con chiave `cashflow-visibility-overrides-{direction}`. 🟢

### Aside Panel (Pannello Laterale Destro)

Quando l'utente clicca su una cella della tabella, si apre un pannello laterale a destra che mostra:
- Dettaglio dei movimenti/scadenze per quella categoria e mese
- Budget impostato (se presente)
- Importo residuo o over-budget
- Pulsante "Vedi tutti" per navigare ai movimenti filtrati
- Tab per switchare tra movimenti, scadenze e ricorrenze

---

## Entita' e Dati

### Entita' Coinvolte

| Entita' | Ruolo nel Modulo | Rif. Data Model |
|---|---|---|
| `account` | Fonte dati: saldi bancari | §2.4 |
| `transaction` | Movimenti consuntivi (entrate/uscite) | §3.4 |
| `category` / `subcategory` | Classificazione dei flussi | §2.8, §2.9 |
| `document` / `flow` | Scadenze future (outstanding) | §2.10, §3.3 |
| `recurrence` | Pagamenti/incassi ricorrenti | §3.7 |
| Budget (non entita' JSON:API) | Previsioni manuali | Gestito client-side/API custom |

### Dati Osservati nell'Account di Test

- **2 conti bancari** attivi (WEISS S.R.L.)
- **Saldo contabile totale:** 12.093,43 EUR 🟢
- **Saldo disponibile totale:** 10.190,17 EUR 🟢
- **42 transazioni** nel periodo osservato 🟢
- **Entrate totali:** 5.645,30 EUR 🟢
- **Uscite totali:** -5.181,79 EUR 🟢
- **7 transazioni non categorizzate** 🟢

---

## Logiche di Business

### 📐 LB-CF-01: Aggregazione Dati Cash Flow

Il grafico e la tabella combinano dati da tre fonti distinte. Confidenza: 🟢 Alta

```
Per ogni mese nel periodo selezionato:
  1. CONSUNTIVO (transactionsAmount)
     = somma dei movimenti bancari contabilizzati (status: Booked)
     Separati in: entrate (is_inflow=true) e uscite (is_inflow=false)

  2. PREVISIONALE - Scadenze (outstandingAmount)
     = somma delle scadenze aperte (flow) non ancora pagate
     Solo per mesi futuri o mese corrente

  3. PREVISIONALE - Scaduto (pastdueAmount)
     = somma delle scadenze scadute non pagate
     Riportato nei mesi passati

  4. BUDGET (budgetAmount)
     = importo manuale impostato dall'utente per categoria/sottocategoria
```

**Fonti API:**
- `/api/v1/cashflow/chart` → dati per il grafico (saldi inizio/fine mese)
- `/api/v1/cashflow/table` → dati per la tabella (dettaglio per categoria/mese)

### 📐 LB-CF-02: Calcolo Saldo e Variazione

Confidenza: 🟢 Alta

```
Per ogni mese:
  saldo_inizio = balance.start (dal chart API)
  saldo_fine   = balance.end   (dal chart API)
  variazione   = saldo_fine - saldo_inizio

Per il totale (riga "Variazione bilancio"):
  variazione_totale = somma(variazione per ogni mese)
```

Il saldo di inizio mese coincide con il saldo di fine del mese precedente.

### 📐 LB-CF-03: Inversione Segno per Uscite

Confidenza: 🟢 Alta

Il server restituisce **importi positivi** per entrambe le direzioni. La negazione avviene **lato client**:
```
if direction == OUTFLOW:
    importo_visualizzato = -importo_server
```

Questo vale per: tabella, grafico, aside panel.

### 📐 LB-CF-04: Gestione Budget / Previsioni

Confidenza: 🟢 Alta

Il sistema di budget permette di inserire previsioni manuali per categoria o sottocategoria:

**Livelli budget:**
- `CATEGORY` — budget a livello categoria (applica a tutte le sottocategorie)
- `SUBCATEGORY` — budget a livello sottocategoria (override del budget categoria)

**Conflitti:**
- Se si inserisce un budget a livello **sottocategoria** quando esiste un budget **categoria**, il budget categoria viene eliminato per quel mese
- E viceversa
- Warning mostrati all'utente prima della sovrascrittura 🟢

**Validazione input budget:**
- Solo valori positivi (`onlyPositive: true`) 🟢
- Solo numeri interi (0 decimali) 🟢
- Valuta fissa: EUR 🟢

### 📐 LB-CF-05: Suggerimenti Budget

Confidenza: 🟢 Alta

Quando l'utente crea un budget, il sistema suggerisce 3 valori:

```
1. "Mese precedente" → valore del budget/consuntivo del mese M-1
2. "Media ultimi 3 mesi" → media(M-1, M-2, M-3)
   Arrotondamento: ROUND_HALF_UP, 0 decimali
   Se meno di 3 mesi hanno dati, divide comunque per 3
3. "Stesso mese anno precedente" → valore del mese M dell'anno Y-1
```

### 📐 LB-CF-06: Estensione Budget su Piu' Mesi

Confidenza: 🟢 Alta

L'utente puo' estendere un budget su piu' mesi con la checkbox "Estendi":
```
Per ogni mese nell'intervallo [mese_corrente, mese_corrente + N]:
  1. Elimina budget di livello opposto (se presente)
  2. Se esiste budget stesso livello con importo diverso: aggiorna
  3. Se non esiste: crea nuovo budget
```

Validazione: se "Estendi" attivo, il numero di mesi deve essere > 0. 🟢

### 📐 LB-CF-07: Importo Residuo Budget

Confidenza: 🟢 Alta

```
importo_residuo = budget - (consuntivo + scadenze_aperte + scaduto)
Se importo_residuo < 0: mostra "Over budget"
Se importo_residuo > 0: mostra "Rimanente: X EUR"
```

### 📐 LB-CF-08: Periodo Default

Confidenza: 🟢 Alta

```
data_inizio = primo giorno del mese, 5 mesi fa
data_fine   = ultimo giorno del mese, 6 mesi avanti
Formato: "YYYY-MM-DD/YYYY-MM-DD"
```

Esempio: se oggi e' 10/02/2026, il periodo default e' Set 2025 — Ago 2026.

### 📐 LB-CF-09: Calcolo Dominio Y del Grafico

Confidenza: 🟢 Alta

```
Per determinare il range dell'asse Y:
  y_min = min(0, tutti i saldi, tutti i budget, tutti i totali entrate+scadenze)
  y_max = max(0, tutti i saldi, tutti i budget, tutti i totali uscite+scadenze)

  y_min_arrotondato = y_min - (1000 + y_min % 1000)
  y_max_arrotondato = y_max + (1000 - y_max % 1000)
```

### LB-CF-10: Separazione Passato/Futuro nel Grafico

Confidenza: 🟢 Alta

La determinazione passato/presente/futuro avviene per mese:
```
if mese/anno < mese_corrente/anno_corrente: "past"
if mese/anno == mese_corrente/anno_corrente: "current"
if mese/anno > mese_corrente/anno_corrente: "future"
```

La linea del bilancio usa:
- **Linea continua** per punti "past" e "current"
- **Linea tratteggiata** per punti "future"
- Il punto di giunzione e' il mese corrente

---

## API Coinvolte

| Endpoint | Metodo | Scopo | Rif. API |
|---|---|---|---|
| `/api/v1/cashflow/chart` | GET | Dati grafico (saldi mese per mese) | §5 |
| `/api/v1/cashflow/table` | GET | Dati tabella (dettaglio per categoria) | §5 |
| `/api/v1/categories` | GET | Lista categorie con sottocategorie | §6 |
| `/api/v1/accounts` | GET | Lista conti bancari | §3 |
| `/api/v1/accounts/metadata` | GET | Saldi aggregati | §3 |
| `/api/v1/transactions` | GET | Movimenti (per aside panel) | §4 |
| `/api/v1/transactions/metadata` | GET | Totali transazioni | §4 |

### Parametri Chiave

**cashflow/chart:**
```
filter[company.id__eq]=UUID
timezone=Europe/Rome
from=2025-08-31T22:00:00.000Z
to=2026-08-31T21:59:59.999Z
includeBudgets=false
includeOverdue=false
includePastdue=false
```

**cashflow/table:**
```
filter[company.id__eq]=UUID
filter[date__gte]=2025-08-31T22:00:00.000Z
filter[date__lte]=2026-08-31T21:59:59.999Z
filter[hiddenAt__empty]=true
timezone=Europe/Rome
includeBudgets=false
includeOverdue=false
includePastdue=false
```

> 🔵 **NOTA**: I parametri `includeBudgets`, `includeOverdue`, `includePastdue` sono flag opzionali. Quando attivati, le risposte API includono rispettivamente i dati budget, le scadenze aperte e gli importi scaduti. Questo suggerisce che il piano TRIAL potrebbe non avere accesso a tutte queste funzionalita'.

---

## Filtri e Ricerca

| Filtro | Tipo | Comportamento | Confidenza |
|---|---|---|---|
| Periodo | Range temporale | Min 3 mesi, Max 12 mesi, preset o custom | 🟢 Alta |
| Conti | Multi-select | Filtra per uno o piu' conti bancari | 🟢 Alta |
| Direzione | Toggle | Entrate / Uscite (tab separate in tabella) | 🟢 Alta |
| Categorie visibili | Override individuale | Nasconde/mostra categorie dalla tabella | 🟢 Alta |
| Ordinamento categorie | Select | Alfabetico / Per importo decrescente | 🟢 Alta |

### Gestione Visibilita' Categorie

Pattern di override su `localStorage`:
```
Chiave: "cashflow-visibility-overrides-{inflow|outflow}"
Formato: { "categoryId": "hidden"|"shown", "categoryId:subcategoryId": "hidden"|"shown" }
Default: tutte visibili
```

---

## Azioni Disponibili

| Azione | Descrizione | Tipo | Confidenza |
|---|---|---|---|
| **Aggiungi previsione** | Inserisce un budget per categoria/sottocategoria/mese | Create | 🟢 Alta |
| **Modifica previsione** | Modifica un budget esistente | Update | 🟢 Alta |
| **Elimina previsioni** | Elimina budget futuri per una categoria | Delete | 🟢 Alta |
| **Estendi previsione** | Propaga un budget su N mesi successivi | Bulk Create | 🟢 Alta |
| **Esporta** | Download Excel del cashflow | Export | 🟢 Alta |
| **Personalizza** | Gestione visibilita' categorie | UI Setting | 🟢 Alta |
| **Filtra periodo** | Cambia intervallo temporale visualizzato | Filter | 🟢 Alta |
| **Filtra conti** | Seleziona conti da includere | Filter | 🟢 Alta |
| **Espandi/collassa** | Mostra/nasconde sottocategorie | UI Toggle | 🟢 Alta |
| **Ordina categorie** | Ordine alfabetico o per importo | Sort | 🟢 Alta |

---

## Limitazioni Osservate

1. **Piano TRIAL:** L'accesso al modulo cash flow e' soggetto a feature gating. Se la feature `cashflow` non e' abilitata nel piano, viene mostrata una pagina di upsell con:
   - Link a Calendly per upgrade: `https://calendly.com/cs--sibill/plan-upgrade` 🟢
   - Demo interattiva Navattic: `https://sibill.navattic.com/cashflow` 🟢

2. **Budget condizionato:** La funzionalita' budget e' gated da una feature separata del piano. Se non disponibile, i campi budget non vengono visualizzati. 🟢

3. **Empty state:** Se l'utente ha consents ma e' alla "prima connessione", viene mostrato un empty state con azioni per connettere la banca o il Cassetto Fiscale. 🟢

4. **Parametri previsionale:** I flag `includeBudgets`, `includeOverdue`, `includePastdue` suggeriscono che i dati previsionali potrebbero non essere disponibili per tutti i piani. 🟡

5. **Valuta unica:** I budget sono supportati solo in EUR. Non c'e' gestione multi-valuta nei budget. 🟢

---

## Note

- Il modulo cash flow e' il piu' ricco dal punto di vista della logica client-side. La maggior parte dei calcoli (aggregazione, inversione segno, suggerimenti, dominio grafico) avviene nel browser.
- La cache del cashflow table ha staleTime di soli 500ms, il che indica che i dati vengono rinfrescati molto frequentemente.
- La libreria grafica usata sembra essere **Recharts** (basata su SVG, con componenti come `BarChart`, `Line`, `Tooltip`).
- I tracking events sono molto granulari (21 eventi solo per il cashflow), suggerendo che il team prodotto monitora attentamente l'utilizzo di questa sezione.
- Le date nelle API usano il **fuso orario UTC con offset per Europe/Rome** (es. `2025-08-31T22:00:00.000Z` = 1 settembre 2025 ore 00:00 CEST).
