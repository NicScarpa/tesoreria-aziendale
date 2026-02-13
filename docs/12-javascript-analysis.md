# Analisi JavaScript — Sibill

**Data analisi:** 10 febbraio 2026
**File analizzati:** 64 file JS in `assets/js-sources/`
**Bundle principale:** `index-N-OxfZQQ.js` (4,5 MB)

---

## 1. Inventario File JS

### 1.1 Categorizzazione

| Categoria | File | Dimensione totale |
|---|---|---|
| **Bundle principale** | 1 file | 4,5 MB |
| **Chunk pagina/componente** | 31 file | ~470 KB |
| **Vendor/Librerie terze parti** | 18 file | ~1,1 MB |
| **Moduli secondari** | 7 file | ~410 KB |
| **Icone SVG (componenti)** | 7 file | ~30 KB |

### 1.2 Dettaglio file per categoria

#### Bundle Principale
| File | Dimensione | Contenuto |
|---|---|---|
| `index-N-OxfZQQ.js` | 4,5 MB | Bundle React principale — contiene tutte le librerie core, routing, state management, componenti condivisi, API layer |

#### Chunk Pagina/Componente (Code Splitting Vite)
| File | Dimensione | Contenuto | Confidenza |
|---|---|---|---|
| `CashFlowPage--BaMgJEI.js` | 85 KB | Pagina cash flow completa: grafici, tabelle, budget, aside panel | 🟢 Alta |
| `CartesianChart-xVH2sHdv.js` | 292 KB | Libreria Recharts (chunk dedicato) | 🟢 Alta |
| `index-DR3wQGYQ.js` | 58 KB | Modulo significativo (react-virtuoso per liste virtualizzate) | 🟡 Media |
| `ReferenceLine-tIFjkUQe.js` | 29 KB | Componente ReferenceLine di Recharts | 🟢 Alta |
| `AddAccountingConsent-DQhKurMl.js` | 15 KB | Wizard consenso contabilità (SDI/Cassetto Fiscale) con MUI Stepper | 🟢 Alta |
| `CategorySearch-H5pZ_RC1.js` | 12 KB | Ricerca categorie con lista virtualizzata, CRUD categorie/sottocategorie | 🟢 Alta |
| `Line-Dqye7x_5.js` | 12 KB | Componente Line di Recharts | 🟢 Alta |
| `DeleteSubcategoryDialog-Z99Okfqh.js` | 9,3 KB | Dialog eliminazione categoria/sottocategoria con effetti collaterali | 🟢 Alta |
| `CashNavigationTabs-DVUea4A9.js` | 8,9 KB | Tab navigazione cash flow + filtri + API calls chart/table | 🟢 Alta |
| `CurrencyIcon-Cm3OVAso.js` | 8,4 KB | Icone valuta (SVG per diverse valute) | 🟢 Alta |
| `index-DT7u4BM2.js` | 8,1 KB | Core modules aggiuntivi | 🟡 Media |
| `OnboardingHeading-DRy2LcY9.js` | 7,9 KB | Layout onboarding con SVG decorativi + brand icons | 🟢 Alta |
| `gestione_tesoreria-CCDLfj4s.js` | 6,1 KB | Icone SVG (lucchetto, play, illustrazione tesoreria) per landing/empty state | 🟢 Alta |
| `EmptyState-BdglrTLA.js` | 5,4 KB | Componente stato vuoto con icona ricerca (SVG inline) | 🟢 Alta |
| `icon-arrow-expand-DeuJ6tiq.js` | 5,9 KB | Icona espansione | 🟢 Alta |
| `ListItem-1hx0FAb8.js` | 4,4 KB | Componente lista (wrapper MUI) | 🟢 Alta |
| `InvoiceCategoryTableCell-Bsu1jbDP.js` | 3,6 KB | Cella tabella fatture con categorizzazione | 🟢 Alta |
| `SubcategorySearch-BMvWduia.js` | 3 KB | Ricerca sottocategorie | 🟢 Alta |
| `categorization-utils-BD3ayecO.js` | 2,7 KB | Utility categorizzazione: regole, filtri, tracking | 🟢 Alta |
| `math-BhNrZZhy.js` | 2,6 KB | Funzioni matematiche (percentuali) + componenti categorizzazione transazione | 🟢 Alta |
| `icon-arrow-match-BZFHXmc0.js` | 2,7 KB | Icona match/freccia | 🟢 Alta |
| `Login-DLieno2m.js` | 2,2 KB | Pagina login con form email/password | 🟢 Alta |
| `CashSection-Dtvj5QpP.js` | 2 KB | Sezione cash flow: gestione stati vuoti, upsell, onboarding | 🟢 Alta |
| `CategoryEditableChip-D1TSOcb0.js` | 1,6 KB | Chip categoria editabile | 🟢 Alta |
| `AddAccountingAction-BdJNGAXU.js` | 1,6 KB | Azione aggiunta accounting (SDI/Cassetto Fiscale) | 🟢 Alta |
| `BankAccountFilter-DmD0iP_d.js` | 1,2 KB | Filtro conti bancari (dropdown multi-select) | 🟢 Alta |
| `index-D10DT0XY.js` | 1,1 KB | Modulo secondario | 🟡 Media |
| `CategoryChip-B_aD8aC5.js` | 611 B | Chip categoria (read-only) | 🟢 Alta |
| `CashFlowPage.module-vMBZTm_S.js` | 436 B | CSS Module per CashFlowPage | 🟢 Alta |
| `SplitLayout.module-CE1-MbOb.js` | 313 B | CSS Module per layout split | 🟢 Alta |

#### Utility
| File | Dimensione | Contenuto | Confidenza |
|---|---|---|---|
| `eachYearOfInterval-DZ7WlxUw.js` | 418 B | Utility date-fns (normalizzazione intervallo) | 🟢 Alta |
| `escapeRegExp-CcrdYU9b.js` | 306 B | Escape regex (wrapper lodash) | 🟢 Alta |
| `is-plan-event-enabled-DeNtQvA5.js` | 226 B | Feature flag per eventi piano | 🟢 Alta |
| `useConfirmationModal-BXiU4Nh6.js` | 194 B | Hook per modale di conferma | 🟢 Alta |
| `getYear-DN1hsmzw.js` | 150 B | Utility date-fns getYear | 🟢 Alta |
| `AddBankingAction-wIQlfJAD.js` | 396 B | Azione aggiunta connessione bancaria | 🟢 Alta |
| `CurrencyAddon-CKs8BsIB.js` | 320 B | Addon campo valuta | 🟢 Alta |
| `SplitAside-kAvfN_V6.js` | 855 B | Layout aside panel | 🟢 Alta |
| `ListItemIcon-fK9Y83hJ.js` | 837 B | Icona lista (wrapper MUI) | 🟢 Alta |
| `InfoIconTooltip-CQ9EHQxd.js` | 747 B | Tooltip informativo | 🟢 Alta |

#### Vendor / Terze Parti
| File | Dimensione | Servizio | Tipo |
|---|---|---|---|
| `fbevents.js` | 348 KB | Facebook Pixel | Analytics/Ads |
| `5811af70036899b09881.js` | 321 KB | Vendor bundle (date-fns, lodash, etc.) | Librerie |
| `modules.ddd41caee2adfc4aedb8.js` | 228 KB | Customer.io/Segment modules | Analytics |
| `js.js` | 111 KB | Segment Analytics SDK | Analytics |
| `401217558333388.js` | 110 KB | Facebook/Meta SDK | Ads |
| `collectedforms.js` | 75 KB | HubSpot Collected Forms | Marketing |
| `commons.59560acdd69ed701c941.js.gz.js` | 70 KB | Intercom commons bundle | Chat/Support |
| `banner.js` | 67 KB | Cookie banner (Iubenda o simile) | Compliance |
| `insight.min.js` | 52 KB | Segment Analytics (insight) | Analytics |
| `gist.min.js` | 33 KB | Gist in-app messaging | Messaging |
| `hotjar-2748974.js` | 15 KB | Hotjar (hjid: 2748974) | Heatmap |
| `fb.js` | 7,5 KB | Facebook SDK loader | Ads |
| `track-eu.js` | 6,6 KB | Tracking EU (Customer.io) | Marketing |
| `s8alsk5h.js` | 3,1 KB | Intercom (App ID: s8alsk5h) | Chat |
| `in-app-eu.js` | 3,1 KB | Customer.io in-app messaging EU | Marketing |
| `c2F0aXNtZXRlcg.dynamic.js.gz.js` | 2,9 KB | SatisMeter (base64: "satismeter") | NPS/Feedback |
| `aG90amFy.dynamic.js.gz.js` | 2,7 KB | Hotjar dynamic (base64: "hotjar") | Heatmap |
| `24972410.js` | 2 KB | HubSpot (Portal ID: 24972410) | CRM |
| `00b46d0899db90cd7140.js` | 4,4 KB | Customer.io site config (hash) | Marketing |

---

## 2. Stack Tecnologico Completo

### 2.1 Librerie Core

| Libreria | Versione | Uso | File | Confidenza |
|---|---|---|---|---|
| **React** | 18.x | UI framework | `index-N-OxfZQQ.js` | 🟢 Alta |
| **React DOM** | 18.x | Rendering | `index-N-OxfZQQ.js` | 🟢 Alta |
| **Vite** | - | Bundler (hash-based chunks, source maps) | Struttura file | 🟢 Alta |
| **TypeScript** | - | Type system (compilato in JS) | Pattern nel codice | 🟢 Alta |

### 2.2 UI Framework

| Libreria | Versione | Uso | Confidenza |
|---|---|---|---|
| **Material UI (MUI)** | 5.x+ | Componenti UI (Step, Stepper, Select, etc.) | 🟢 Alta |
| **React Aria** | - | Accessibilità (popover, overlay, modal) | 🟢 Alta |
| **Emotion** | - | CSS-in-JS (usato internamente da MUI) | 🟡 Media |
| **CSS Modules** | - | Styling componenti custom (pattern `_class_hash_1`) | 🟢 Alta |

### 2.3 State Management

| Libreria | Uso | Pattern | Confidenza |
|---|---|---|---|
| **Jotai** | State management principale | Atoms con localStorage persistence, atomFamily, atomWithStorage | 🟢 Alta |
| **nuqs** | URL state management | `useQueryState` per parametri URL (period, accountIds) | 🟡 Media |

> 🔵 **NOTA**: Sibill usa **Jotai** (non Redux/Zustand) come state manager. Gli atomi sono usati per: preferenze utente (periodo selezionato, filtri), stato UI (accordion espansi, sort order, visibility overrides), celle attive del cash flow. Molti atomi hanno persistenza in `localStorage` con pattern `atomWithStorage`.

### 2.4 Data Fetching

| Libreria | Uso | Pattern | Confidenza |
|---|---|---|---|
| **TanStack Query (React Query)** | Data fetching e caching | `useQuery`, `useMutation`, `useInfiniteQuery`, `queryClient.invalidateQueries` | 🟢 Alta |
| **Axios** | HTTP client | Importato come `E`/`Jt`/`S` — metodi `.get`, `.post`, `.patch`, `.delete` con params | 🟢 Alta |
| **jsonapi-serializer** | Serializzazione JSON:API | `serialize`/`deserialize` con relationships e include | 🟢 Alta |

### 2.5 Grafici

| Libreria | Uso | Confidenza |
|---|---|---|
| **Recharts** | Grafici cash flow | 🟢 Alta |

> 🔵 **NOTA**: Recharts è confermato dal chunk `CartesianChart-xVH2sHdv.js` (292 KB) e dai componenti usati in CashFlowPage: `ComposedChart`, `Bar`, `Line`, `XAxis`, `YAxis`, `CartesianGrid`, `Tooltip`, `ReferenceLine`, `ResponsiveContainer`. Il grafico del cash flow usa un **ComposedChart** con barre e linee sovrapposti.

### 2.6 Form e Validazione

| Libreria | Uso | Confidenza |
|---|---|---|
| **react-hook-form** | Gestione form | 🟢 Alta |
| **Zod** | Schema validation (via `@hookform/resolvers/zod`) | 🟢 Alta |

> Pattern tipico: `useForm({ resolver: zodResolver(schema) })` con `Controller` per integrazione MUI.

### 2.7 Date e Numeri

| Libreria | Uso | Confidenza |
|---|---|---|
| **date-fns** | Manipolazione date | 🟢 Alta |
| **BigNumber.js** (o `bignumber.js`) | Aritmetica monetaria ad alta precisione | 🟢 Alta |

> 🔵 **NOTA**: Gli importi monetari sono gestiti con BigNumber.js per evitare errori di arrotondamento floating-point. Pattern: `new St(amount)`, con metodi `.dividedBy()`, `.multipliedBy()`, `.toFixed()`, `.eq()`, `.isLessThan()`, `.abs()`, `.isZero()`, `.isNaN()`. Costanti di arrotondamento: `St.ROUND_CEIL`, `St.ROUND_HALF_UP`.

### 2.8 Internazionalizzazione

| Libreria | Uso | Confidenza |
|---|---|---|
| **i18next / react-i18next** | Traduzioni multilingua | 🟢 Alta |

> Pattern: `const {t} = useTranslation("namespace", {keyPrefix: "section"})`. Namespace trovati: `cashflow`, `transactions`, `auth`, `consents`, `categorization`, `documents`, `inputs`, `flows`, `empty_states`.

### 2.9 Routing

| Libreria | Uso | Confidenza |
|---|---|---|
| **React Router v6** | Client-side routing | 🟢 Alta |

> Le rotte sono definite nel bundle principale. Pattern di navigazione: `useNavigate()`, `buildLink()` per costruzione URL. Code splitting con `React.lazy()`.

### 2.10 Liste Virtualizzate

| Libreria | Uso | Confidenza |
|---|---|---|
| **react-virtuoso** | Virtualizzazione liste lunghe | 🟢 Alta |

> Usato in `CategorySearch` per la lista categorie e in altre liste con scroll infinito.

### 2.11 Scroll Sync

| Libreria | Uso | Confidenza |
|---|---|---|
| **Custom ScrollSync** | Sincronizzazione scroll tra pannelli | 🟢 Alta |

> Implementazione custom nel CashFlowPage per sincronizzare lo scroll orizzontale tra header, body e footer della tabella cash flow.

### 2.12 Monitoring e Error Tracking

| Libreria | Versione | Uso | Confidenza |
|---|---|---|---|
| **Sentry** | v10.38.0 | Error tracking (`captureException`) | 🟢 Alta |

### 2.13 Analytics

| Servizio | Uso | Confidenza |
|---|---|---|
| **Segment** | Hub analytics — `track(eventName, properties)` | 🟢 Alta |
| **Mixpanel** | Analytics (via Segment) | 🟡 Media |
| **HubSpot** | Marketing automation + collected forms | 🟢 Alta |
| **Hotjar** | Heatmap e session recording | 🟢 Alta |
| **Facebook Pixel** | Ads tracking | 🟢 Alta |
| **Customer.io** | Email marketing + in-app messaging EU | 🟢 Alta |
| **SatisMeter** | NPS surveys | 🟢 Alta |
| **Gist** | In-app messaging | 🟢 Alta |
| **Intercom** | Chat support | 🟢 Alta |

---

## 3. Architettura Componenti React

### 3.1 Struttura ad Albero

```
App (index-N-OxfZQQ.js)
├── Router (React Router v6)
│   ├── /login → Login-DLieno2m.js
│   ├── /cashflow → CashFlowPage--BaMgJEI.js
│   │   ├── CashNavigationTabs (tabs + filtri)
│   │   ├── ScrollSyncProvider (sync scroll orizzontale)
│   │   │   ├── Chart (Recharts ComposedChart)
│   │   │   ├── InitialBalanceRow
│   │   │   ├── BalanceChangeRow
│   │   │   ├── InflowSection (BudgetProvider)
│   │   │   │   ├── CategoryCard[] → SubcategoryRow[]
│   │   │   │   │   └── BudgetCell (editabile con suggerimenti)
│   │   │   │   └── AddCategoryButton
│   │   │   └── OutflowSection (BudgetProvider)
│   │   │       └── (stessa struttura)
│   │   └── AsidePanel (detail view con tabs)
│   │       ├── TransactionsTab
│   │       ├── ExpiringTab (outstanding)
│   │       └── ExpiredTab (pastdue)
│   ├── /cashflow/categories → (chunk separato)
│   ├── /transactions/* → (chunk separato)
│   ├── /accounts → (chunk separato)
│   ├── /outstanding/* → (chunk separato)
│   ├── /invoices/* → (chunk separato)
│   ├── /reconciliations → (chunk separato)
│   ├── /f24 → (chunk separato)
│   └── /settings/* → (chunk separato)
├── Providers globali
│   ├── QueryClientProvider (TanStack Query)
│   ├── Jotai Provider
│   ├── i18next Provider
│   └── ModalProvider (showModal pattern)
└── Servizi globali
    ├── Sentry (error tracking)
    ├── Segment (analytics)
    ├── Intercom (chat)
    └── Cookie/GDPR banner
```

### 3.2 Pattern Architetturali Ricorrenti

#### Context Pattern
- `CashflowBudgetsProvider` — gestisce dati budget, calcoli, handler
- `ScrollSyncProvider` — sincronizzazione scroll
- `CashflowDirectionProvider` — contesto inflow/outflow
- `SuggestionsProvider` — suggerimenti budget basati su storico

#### Custom Hooks
- `useConfirmationModal()` — modale conferma distruttiva
- `useCashflowBudgets()` — accesso a budget e handler
- `useAccountIds()` — account selezionati (Jotai + URL)
- `usePeriod()` — periodo selezionato (Jotai + URL)
- `useScrollSync()` — registrazione pannelli per scroll sync
- `useCollapsible()` — accordion con persistenza localStorage
- `useBudgetSuggestions()` — suggerimenti budget (mese precedente, media 3 mesi, anno precedente)

#### Atomic State (Jotai)
Pattern di persistenza con localStorage:
```
atomWithStorage("cashflow-sort-inflow", "alphabetical")
atomWithStorage("cashflow-visibility-overrides-inflow", {})
atomWithStorage("cashflow-accordion-expanded-inflow", false)
atomWithStorage("cashflow-include-budgets", false)
atomWithStorage("cashflow-include-overdue", false)
atomWithStorage("cashflow-include-pastdue", false)
atomWithStorage("cashflow-last-selected-period", defaultPeriod)
```

#### Modal Pattern
- `showModal({ component, props })` — modale dinamico globale
- Usato per: consensi bancari, budget prediction, eliminazione categorie, creazione sottocategorie

#### Data Test ID Pattern
- `useDataTestId(prefix)` che restituisce `(...parts) => prefix + parts.join("-")`
- Presente su quasi tutti i componenti interattivi

---

## 4. Pattern di Routing

### 4.1 Rotte Identificate dal JS

| Rotta | Nome interno | Lazy Loading |
|---|---|---|
| `/login` | `Login` | Si |
| `/cashflow` | `Cashflow` / `AppRoot` | Si |
| `/cashflow/categories` | `Categories` | Si |
| `/transactions/movements` | `Transactions` | Si |
| `/transactions/payments` | `Payments` | Si |
| `/transactions/rules` | `TransactionRules` | Si |
| `/reconciliations` | `Reconciliations` | Si |
| `/accounts` | `Accounts` | Si |
| `/outstanding` | `Outstanding` | Si |
| `/outstanding/recurrences/received` | `OutstandingRecurrences` | Si |
| `/outstanding/recurrences/issued` | `OutstandingRecurrencesIssued` | Si |
| `/outstanding/rules` | `OutstandingRules` | Si |
| `/invoices/dashboard` | `InvoicesDashboard` | Si |
| `/invoices/issued` | `InvoicesIssued` | Si |
| `/invoices/received` | `InvoicesReceived` | Si |
| `/invoices/bills` | `InvoicesBills` | Si |
| `/counterparts` | `Counterparts` | Si |
| `/invoices/profile/*` | `InvoicesProfile` | Si |
| `/invoices/info` | `InvoicesCreate` | Si |
| `/invoices/import` | `InvoicesImport` | Si |
| `/f24` | `F24` | Si |
| `/settings/team` | `SettingsTeam` | Si |
| `/referral` | `Referral` | Si |

### 4.2 Route Helpers

Il routing usa un pattern `buildLink()` per costruire URL:
```
Routes.Cashflow.buildLink()           → "/cashflow"
Routes.Transactions.buildLink()       → "/transactions/movements"
Routes.Outstanding.buildLink()        → "/outstanding"
Routes.OutstandingFlowsAll.buildLink() → "/outstanding" (con filtri expanded)
Routes.Categories.buildLink()         → "/cashflow/categories"
Routes.AppRoot.buildLink()            → "/cashflow" (root dell'app)
Routes.ResetPassword.buildLink()      → "/reset-password" (?)
```

---

## 5. API Layer

### 5.1 HTTP Client (Axios)

L'app usa Axios come HTTP client, importato nel bundle principale. Configurazione:
- Base URL: implicito (le chiamate usano path relativi come `/api/v1/...`)
- Content-Type: `application/vnd.api+json` (JSON:API)
- Cookie-based auth (cookie `_sibill_key`)

### 5.2 Pattern JSON:API

Serializzazione/deserializzazione con `jsonapi-serializer`:
```js
// Serializzazione
const payload = serializer.serialize(data, "resourceType", {
  relationships: ["company", "category", "subcategory"]
});

// Deserializzazione
const result = serializer.deserialize(response.data);
```

### 5.3 Query Builder Pattern

L'app implementa un pattern fluente per costruire query API:

```js
// Filtri
filter.eq("company.id", companyId)
filter.gte("date", startDate)
filter.lte("date", endDate)
filter.in("account.id", accountIds)
filter.empty("hiddenAt", true)

// Paginazione (cursor-based)
page.cursor(cursorValue)
page.size(100)

// Include relazioni
include(["category", "subcategory"])

// Ordinamento
sort([{sort: "name", direction: "asc"}])

// Composizione
buildParams(filter, include, sort, page)
```

### 5.4 API Endpoints dal JS

| Metodo | Endpoint | Usato in | Confidenza |
|---|---|---|---|
| `GET` | `/api/v1/cashflow/chart` | `CashNavigationTabs` | 🟢 Alta |
| `GET` | `/api/v1/cashflow/table` | `CashNavigationTabs` | 🟢 Alta |
| `GET` | `/api/v1/cashflow/table` (accept: xlsx) | `CashNavigationTabs` (export) | 🟢 Alta |
| `GET` | `/api/v1/budgets` | `CashFlowPage` | 🟢 Alta |
| `POST` | `/api/v1/budgets` | `CashFlowPage` (creazione budget) | 🟢 Alta |
| `PATCH` | `/api/v1/budgets/{id}` | `CashFlowPage` (modifica budget) | 🟢 Alta |
| `DELETE` | `/api/v1/budgets/{id}` | `CashFlowPage` (eliminazione budget) | 🟢 Alta |
| `GET` | `/api/v1/subcategories` | `DeleteSubcategoryDialog` | 🟢 Alta |
| `POST` | `/api/v1/subcategories` | `CategorySearch` (creazione) | 🟢 Alta |
| `PATCH` | `/api/v1/subcategories/{id}` | `CategorySearch` (rinomina) | 🟢 Alta |
| `DELETE` | `/api/v1/subcategories/{id}` | `DeleteSubcategoryDialog` | 🟢 Alta |

### 5.5 Parametri API Cash Flow

Parametri per `/api/v1/cashflow/chart` e `/api/v1/cashflow/table`:
- `timezone` — Timezone del browser (`Intl.DateTimeFormat().resolvedOptions().timeZone`)
- `from`/`to` — Intervallo date (ISO string)
- `includeBudgets` — Boolean, se includere budget previsionali
- `includeOverdue` — Boolean, se includere scaduti
- `includePastdue` — Boolean, se includere passato dovuto
- Filtri company e account IDs

---

## 6. Feature Flag e Configurazioni

### 6.1 Feature Flag Identificati

| Feature Flag | Tipo | Uso | File | Confidenza |
|---|---|---|---|---|
| `is-plan-event-enabled` | Piano/abbonamento | Controlla se eventi del piano sono abilitati. Default: `true`. Controlla proprietà `__default.enabled`. | `is-plan-event-enabled-DeNtQvA5.js` | 🟢 Alta |
| Budget feature | Piano/abbonamento | Il budget è gated: se il piano non lo supporta, viene mostrato upsell con link Calendly | `CashSection-Dtvj5QpP.js` | 🟢 Alta |
| Cash flow access | Piano/abbonamento | Accesso alla pagina cash flow condizionato dal piano | `CashSection-Dtvj5QpP.js` | 🟢 Alta |
| Outstanding features | Piano/abbonamento | Feature scadenzario controllate da hook `useIncludeOverdue`, `useIncludePastdue` | `CashNavigationTabs` | 🟡 Media |
| Aside expiring tab | Piano/condizione | Tab "Expiring" visibile solo se `includeOverdue` attivo E timePosition !== "past" | `CashFlowPage` | 🟢 Alta |
| Aside expired tab | Piano/condizione | Tab "Expired" visibile solo se `includePastdue` attivo E timePosition === "current" | `CashFlowPage` | 🟢 Alta |

### 6.2 URL Esterni Hardcoded

| URL | Uso | File |
|---|---|---|
| `https://calendly.com/cs--sibill/plan-upgrade` | Upsell — prenotazione upgrade piano | `CashSection-Dtvj5QpP.js` |
| `https://sibill.navattic.com/cashflow` | Demo interattiva cash flow | `CashSection-Dtvj5QpP.js` |
| `https://iampe.agenziaentrate.gov.it/sam/UI/Login?realm=/agenziaentrate` | Login Agenzia Entrate (Cassetto Fiscale) | `AddAccountingConsent-DQhKurMl.js` |
| `/static/documents/Sibill Tutorial - Cassetto Fiscale.pdf` | Tutorial autorizzazione SDI | `AddAccountingConsent-DQhKurMl.js` |

---

## 7. Integrazioni Identificate

### 7.1 Integrazione Cassetto Fiscale / SDI

**File:** `AddAccountingConsent-DQhKurMl.js`, `AddAccountingAction-BdJNGAXU.js`

Wizard a 3 step per autorizzare l'accesso al Cassetto Fiscale tramite SDICoop:
1. **Step 1:** Download PDF tutorial
2. **Step 2:** Login su portale Agenzia delle Entrate
3. **Step 3:** Completamento autorizzazione con alert di warning

**Flusso stato consent:**
```
Creating → Consent Screen (se userInfo disponibile) → Authorization → Authorized
```

**API:** Creazione consent tramite `institutionId`, autorizzazione tramite `consentId` + `userData`.

### 7.2 Integrazione Bancaria (Open Banking)

**File:** `AddBankingAction-wIQlfJAD.js`, `BankAccountFilter-DmD0iP_d.js`

- Modale per aggiunta connessione bancaria
- Filtro conti con nickname, nome istituto, saldo disponibile
- Stato: `"connected_waiting"` dopo prima connessione

### 7.3 Nessun WebSocket/SSE Identificato

Non sono stati trovati pattern WebSocket (`new WebSocket`), Server-Sent Events (`new EventSource`) o Socket.io nei file analizzati. L'app sembra usare solo polling HTTP standard. **Confidenza: 🟡 Media** (il bundle principale è troppo grande per una ricerca esaustiva).

---

## 8. Design System Tecnico

### 8.1 Palette Colori (dal JS)

| Variabile | Valore (stimato) | Uso |
|---|---|---|
| `colorForest600` | Verde scuro | Barre inflow (transazioni) |
| `colorForest700` | Verde più scuro | Barre inflow (chart loading) |
| `colorForest400` | Verde chiaro | Barre outstanding inflow |
| `colorForest800` | Verde molto scuro | Barre pastdue inflow |
| `colorLobster700` | Rosso | Barre outflow (transazioni) |
| `colorLobster500` | Rosso chiaro | Barre outstanding outflow |
| `#7a0c2e` | Bordeaux | Barre pastdue outflow (hardcoded) |
| `colorGrey200` | Grigio chiaro | Cursor tooltip chart |
| `colorGrey400` | Grigio | Grid lines |
| `colorGrey500` | Grigio medio | Tick labels |
| `colorGrey700` | Grigio scuro | Linea bilancio |
| `colorViolet100` | Viola chiaro | Background summary card |
| `#576CF6` | Blu/Viola | Icona ricerca (empty state) |

### 8.2 Dimensioni Costanti UI

| Costante | Valore | Uso |
|---|---|---|
| `ChartColumnWidth` | 77.5 px | Larghezza colonna grafico |
| `FirstColumnWidth` | 232 px | Larghezza prima colonna (label) |
| `LastColumnWidth` | 120 px | Larghezza ultima colonna (totale) |
| `LastColumnPaddingRightRatio` | 2.5 | Moltiplicatore padding |
| `Chart height` | 300 px | Altezza grafico cash flow |
| `StickyHeader z-index` | 20 | Z-index header sticky |
| `ChartTooltip z-index` | 80 | Z-index tooltip |
| `BudgetInputTooltip z-index` | 80 | Z-index input budget |
| `Aside z-index` | 1000 | Z-index pannello laterale |
| `Modal max-width` | 600 px | Larghezza massima modale consent |

---

## 9. Tabella Riassuntiva Tecnologie

| Categoria | Tecnologia | Confidenza |
|---|---|---|
| **Framework** | React 18 | 🟢 Alta |
| **Bundler** | Vite | 🟢 Alta |
| **Linguaggio** | TypeScript (compilato) | 🟢 Alta |
| **UI Library** | Material UI 5+ | 🟢 Alta |
| **Accessibilità** | React Aria | 🟢 Alta |
| **Styling** | CSS Modules + Emotion | 🟢 Alta |
| **Routing** | React Router v6 | 🟢 Alta |
| **State Management** | Jotai + nuqs (URL state) | 🟢 Alta |
| **Data Fetching** | TanStack Query (React Query) | 🟢 Alta |
| **HTTP Client** | Axios | 🟢 Alta |
| **API Format** | JSON:API (jsonapi-serializer) | 🟢 Alta |
| **Form Management** | react-hook-form + Zod | 🟢 Alta |
| **Grafici** | Recharts | 🟢 Alta |
| **Date** | date-fns | 🟢 Alta |
| **Aritmetica** | BigNumber.js | 🟢 Alta |
| **i18n** | i18next / react-i18next | 🟢 Alta |
| **Liste virtualizzate** | react-virtuoso | 🟢 Alta |
| **Error Tracking** | Sentry v10.38.0 | 🟢 Alta |
| **Analytics** | Segment (hub) | 🟢 Alta |
| **Chat** | Intercom | 🟢 Alta |
| **NPS** | SatisMeter | 🟢 Alta |
| **Heatmap** | Hotjar | 🟢 Alta |
| **Marketing** | HubSpot + Customer.io | 🟢 Alta |
| **Cookie Consent** | Banner dedicato | 🟡 Media |
| **Backend (ipotesi)** | Ruby on Rails | 🟡 Media |
