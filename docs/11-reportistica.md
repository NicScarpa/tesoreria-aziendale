# Reportistica e Dashboard — Analisi Funzionale

**Data analisi:** 10 febbraio 2026
**Modulo:** Reportistica e Dashboard
**URL dashboard cashflow:** `/cashflow`
**URL dashboard fatture:** `/invoices/dashboard`

---

## Panoramica

Sibill offre due dashboard principali e diverse funzionalita' di reportistica:

1. **Dashboard Cashflow** (`/cashflow`) — Vista principale con grafico flussi di cassa, tabella dettagliata per categoria, saldi bancari. E' anche la homepage dell'applicazione.

2. **Dashboard Fatture** (`/invoices/dashboard`) — Vista riepilogativa su ricavi, costi, IVA, top clienti e fornitori.

Oltre alle dashboard, il sistema offre funzionalita' di **export** (Excel per il cashflow, potenzialmente PDF e CSV per altri moduli).

---

## Interfaccia

### Dashboard Cashflow (Homepage)

**URL:** `/cashflow`
**Componenti:** Grafici SVG (183 elementi SVG osservati), tabelle, filtri

Layout:
1. **Barra filtri** — Periodo, conti, ordinamento
2. **Grafico combinato** — Barre (entrate/uscite) + linea (saldo)
3. **Tabella dettagliata** — Per categoria con espansione sottocategorie
4. **Pannello laterale** (on click) — Dettaglio per cella

### 🎨 PATTERN UI/UX — Grafico Combinato Barre+Linea

Il grafico cash flow usa un pattern di **dual visualization**:
- **Barre** (colorate per entrata/uscita) mostrano i flussi del mese
- **Linea** sovrapposta mostra l'andamento del saldo
- La linea si divide in **continua** (passato) e **tratteggiata** (futuro) al mese corrente
- Dimensioni: altezza 300px, colonna 77.5px, barra 16px, font tick 13px 🟢

### Dashboard Fatture

**URL:** `/invoices/dashboard`
**Componenti:** Grafici, KPI, tabelle ranking

Layout (dedotto dall'API):
1. **KPI principali** — Ricavi totali, Costi totali, Netto, IVA a debito/credito
2. **Grafico ricavi/costi** — Andamento mensile
3. **Top clienti** — Ranking per fatturato
4. **Top fornitori** — Ranking per costi
5. **Riepilogo IVA** — Debito e credito per periodo

---

## Entita' e Dati

### Fonti Dati per il Reporting

| Fonte | API | Tipo di Dati | Confidenza |
|---|---|---|---|
| Saldi bancari | `/api/v1/accounts/metadata` | Saldi aggregati real-time | 🟢 Alta |
| Flussi di cassa | `/api/v1/cashflow/chart` | Saldi inizio/fine mese | 🟢 Alta |
| Dettaglio cashflow | `/api/v1/cashflow/table` | Entrate/uscite per categoria/mese | 🟢 Alta |
| Riepilogo fatture | `/api/v1/documents-dashboard/summary` | Ricavi, costi, IVA, ranking | 🟢 Alta |
| Metadati transazioni | `/api/v1/transactions/metadata` | Totali, somme, non categorizzate | 🟢 Alta |
| Metadati documenti | `/api/v1/documents/metadata` | Conteggi per tipo documento | 🟢 Alta |
| Metadati controparti | `/api/v1/counterparts/metadata` | Conteggio controparti | 🟢 Alta |
| Metadati pagamenti | `/api/v1/payments/metadata` | Conteggio per stato | 🟢 Alta |

---

## Logiche di Business

### 📐 LB-REP-01: Dashboard Fatture — Riepilogo Ricavi e Costi

Confidenza: 🟢 Alta

L'endpoint `/api/v1/documents-dashboard/summary` restituisce:

```json
{
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
  "taxesSummary": { "data": [...], "totals": {...} },
  "customers": [...],
  "suppliers": [...]
}
```

📐 **FORMULE:**
```
Ricavi = somma fatture emesse (INVOICE, PARCEL) - note di credito emesse (CREDIT_NOTE)
Costi = somma fatture ricevute + note di debito ricevute
Netto = Ricavi - Costi
IVA a debito = IVA sulle fatture emesse
IVA a credito = IVA sulle fatture ricevute
```

### 📐 LB-REP-02: Top Clienti e Fornitori

Confidenza: 🟢 Alta

La dashboard fatture include il ranking di clienti e fornitori:

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
  "suppliers": [...]
}
```

📐 **FORMULA:**
```
Per ogni controparte (cliente o fornitore):
  amount = somma importi lordi dei documenti nel periodo
  amountPercentage = (amount / totale_ricavi_o_costi) * 100
  numberOfDocuments = conteggio documenti nel periodo
```

### 📐 LB-REP-03: Metriche Movimenti

Confidenza: 🟢 Alta

L'endpoint `/api/v1/transactions/metadata` fornisce KPI sui movimenti:

```json
{
  "total": 42,
  "totals": [{
    "currency": "EUR",
    "positive": {"currency": "EUR", "amount": "5645.30"},
    "negative": {"currency": "EUR", "amount": "-5181.79"}
  }],
  "totalsEur": {...},
  "totalUncategorised": 7,
  "totalsEurSucceeded": {...}
}
```

📐 **FORMULA:**
```
Totale entrate = somma movimenti positivi (contabilizzati)
Totale uscite = somma movimenti negativi (contabilizzati)
Non categorizzati = conteggio movimenti senza categoria assegnata
```

### 📐 LB-REP-04: Aggregazione Cash Flow

Confidenza: 🟢 Alta

Il cashflow aggrega 4 tipi di dati per ogni mese:
```
1. Consuntivo (transactionsAmount) — Movimenti bancari effettivi
2. Scadenze (outstandingAmount) — Scadenze aperte future
3. Scaduto (pastdueAmount) — Scadenze passate non pagate
4. Budget (budgetAmount) — Previsioni manuali

Totale mese = Consuntivo + Scadenze + Scaduto
Variazione = Saldo fine mese - Saldo inizio mese
```

### LB-REP-05: Export Cash Flow (Excel)

Confidenza: 🟢 Alta

La tabella cash flow supporta l'export in formato Excel:
- Tracking event: `CASHFLOW_EXPORTED` 🟢
- Messaggio errore: `cashflow.messages.failed_cashflow_export` 🟢
- L'export include probabilmente tutti i dati della tabella (categorie, sottocategorie, importi per mese, totali)

### LB-REP-06: Filtri Dashboard Fatture

Confidenza: 🟢 Alta

La dashboard fatture filtra per:
```
filter[company.id__eq]=UUID
filter[creationDate__gte]=2026-01-01        ← Inizio anno
filter[creationDate__lte]=2026-12-31        ← Fine anno
filter[documentType__in]=INVOICE,CREDIT_NOTE,DEBIT_NOTE,BILL,SELF_INVOICE,PARCEL
filter[status__notIn]=DRAFT,DISCARDED       ← Esclude bozze e scartati
filter[hiddenAt__empty]=true                ← Esclude documenti nascosti
```

Il periodo default e' l'**anno corrente** (1 gen — 31 dic). 🟢

---

## API Coinvolte

| Endpoint | Metodo | Scopo | Occorrenze | Rif. API |
|---|---|---|---|---|
| `/api/v1/cashflow/chart` | GET | Grafico cashflow (saldi) | 2 | §5 |
| `/api/v1/cashflow/table` | GET | Tabella cashflow (dettaglio categorie) | 4 | §5 |
| `/api/v1/documents-dashboard/summary` | GET | Riepilogo fatture (ricavi, costi, ranking) | 1 | §7 |
| `/api/v1/accounts/metadata` | GET | Saldi aggregati | 3 | §3 |
| `/api/v1/transactions/metadata` | GET | Totali transazioni | 1 | §4 |
| `/api/v1/documents/metadata` | GET | Conteggi documenti | 1 | §7 |
| `/api/v1/counterparts/metadata` | GET | Conteggio controparti | 1 | §8 |
| `/api/v1/payments/metadata` | GET | Conteggio pagamenti per stato | 29 | §9 |

---

## Filtri e Ricerca

### Dashboard Cashflow

| Filtro | Tipo | Descrizione | Confidenza |
|---|---|---|---|
| Periodo | Range date (preset/custom) | 3-12 mesi, default: -5/+6 dal mese corrente | 🟢 Alta |
| Conti | Multi-select | Filtra per conto bancario | 🟢 Alta |
| Categorie | Toggle visibilita' | Nasconde/mostra categorie | 🟢 Alta |
| Ordinamento | Select | Alfabetico / Per importo | 🟢 Alta |
| Espansione | Toggle | Mostra/nasconde sottocategorie | 🟢 Alta |

### Dashboard Fatture

| Filtro | Tipo | Descrizione | Confidenza |
|---|---|---|---|
| Periodo | Anno | Default: anno corrente | 🟢 Alta |
| Tipo documento | Include | INVOICE, CREDIT_NOTE, DEBIT_NOTE, etc. | 🟢 Alta |
| Stato | Exclude | Esclude DRAFT e DISCARDED | 🟢 Alta |
| Nascosti | Boolean | Esclude documenti nascosti | 🟢 Alta |

---

## Azioni Disponibili

| Azione | Descrizione | Tipo | Modulo | Confidenza |
|---|---|---|---|---|
| **Esporta cashflow** | Download Excel della tabella cashflow | Export | Cashflow | 🟢 Alta |
| **Filtra periodo** | Cambia intervallo temporale | Filter | Entrambi | 🟢 Alta |
| **Filtra conti** | Seleziona conti da visualizzare | Filter | Cashflow | 🟢 Alta |
| **Personalizza** | Gestione visibilita' categorie | Setting | Cashflow | 🟢 Alta |
| **Drill-down** | Click su cella → aside panel con dettagli | Navigate | Cashflow | 🟢 Alta |
| **Vedi tutti** | Da aside panel, naviga ai movimenti filtrati | Navigate | Cashflow | 🟢 Alta |

---

## Limitazioni Osservate

1. **Export limitato:** Solo l'export Excel del cashflow e' stato confermato. Non sono stati osservati export PDF o CSV per altri moduli. 🟡

2. **Dashboard fatture con dati reali:** La dashboard fatture mostra i dati dell'anno corrente, quindi richiede fatture presenti nel sistema. La quantita' e qualita' dei dati dipende dalle fatture importate. 🟢

3. **Nessun report personalizzabile:** Non sono stati osservati report personalizzabili o template di report. La reportistica sembra limitata alle due dashboard pre-configurate. 🟡

4. **Grafici non interattivi in modo avanzato:** I grafici sono basati su SVG (probabile Recharts), con tooltip ma senza funzionalita' avanzate come zoom o drill-down nel grafico stesso. Il drill-down avviene dalla tabella sottostante. 🟡

5. **Periodo fisso per fatture:** La dashboard fatture sembra filtrare solo per anno intero, senza possibilita' di selezionare periodi custom (trimestre, semestre). 🟡

---

## Note

- La reportistica di Sibill e' relativamente essenziale rispetto a strumenti di BI dedicati. Le due dashboard (cashflow e fatture) coprono le esigenze base di monitoraggio.
- Il pattern di endpoint `/metadata` e' usato estensivamente per fornire KPI rapidi senza scaricare tutti i dati. Questo e' un pattern efficiente per le dashboard.
- Il cashflow export Excel e' l'unico formato di export confermato. Per il gestionale target, sarebbe utile aggiungere export PDF e CSV.
- La dashboard fatture con ricavi/costi/IVA e ranking clienti/fornitori e' particolarmente utile per la gestione aziendale e potrebbe essere replicata nel gestionale.
- I dati di `totalsEurSucceeded` nel metadata transazioni suggeriscono che vengono conteggiati solo i movimenti con stato "succeeded" (contabilizzati), escludendo quelli in attesa.
