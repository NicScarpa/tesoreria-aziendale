# PRD-11: UI Design System e Pattern di Interfaccia

**Versione:** 1.0
**Data:** 10 febbraio 2026
**Basato su:** RE Sibill — docs/12-javascript-analysis.md (design system tecnico), docs/13-regole-business.md (costanti UI), docs/01-app-map.md (componenti osservati)
**Stack target:** Next.js 14+, shadcn/ui (Radix UI), Tailwind CSS, TanStack Table, react-hook-form + Zod, Recharts

---

## 1. Design Tokens

### 1.1 Palette Colori

Basata sui pattern osservati in Sibill (variabili `colorForest`, `colorLobster`, `colorViolet`, `colorGrey`) e adattata per il gestionale.

#### Colori Primari

| Token | Hex | Uso | Riferimento Sibill |
|-------|-----|-----|-------------------|
| `--primary-50` | `#eff6ff` | Background hover leggero | - |
| `--primary-100` | `#dbeafe` | Background selezionato | - |
| `--primary-500` | `#3b82f6` | Azione primaria, link | - |
| `--primary-600` | `#2563eb` | Azione primaria hover | - |
| `--primary-700` | `#1d4ed8` | Focus ring | - |
| `--primary-900` | `#1e3a5f` | Testo heading principale | - |

#### Colori Semantici

| Token | Hex | Uso | Riferimento Sibill |
|-------|-----|-----|-------------------|
| `--success-400` | `#4ade80` | Inflow (entrate) — barre outstanding | `colorForest400` |
| `--success-600` | `#16a34a` | Inflow (entrate) — barre transazioni | `colorForest600` |
| `--success-700` | `#15803d` | Inflow — barre chart loading | `colorForest700` |
| `--success-800` | `#166534` | Inflow — pastdue | `colorForest800` |
| `--error-500` | `#ef4444` | Outflow (uscite) — barre outstanding | `colorLobster500` |
| `--error-700` | `#b91c1c` | Outflow (uscite) — barre transazioni | `colorLobster700` |
| `--error-900` | `#7a0c2e` | Outflow — pastdue | Hardcoded in Sibill |
| `--warning-500` | `#f59e0b` | Avvisi, badge attenzione | - |
| `--info-100` | `#ede9fe` | Background card riepilogo | `colorViolet100` |
| `--info-500` | `#576CF6` | Icona ricerca, accent secondario | Hardcoded in Sibill |

#### Colori Neutri

| Token | Hex | Uso | Riferimento Sibill |
|-------|-----|-----|-------------------|
| `--grey-50` | `#f9fafb` | Background pagina | - |
| `--grey-100` | `#f3f4f6` | Background card | - |
| `--grey-200` | `#e5e7eb` | Cursor tooltip, divider | `colorGrey200` |
| `--grey-300` | `#d1d5db` | Border input | - |
| `--grey-400` | `#9ca3af` | Grid lines grafici | `colorGrey400` |
| `--grey-500` | `#6b7280` | Tick labels, testo secondario | `colorGrey500` |
| `--grey-700` | `#374151` | Linea bilancio, testo primario | `colorGrey700` |
| `--grey-900` | `#111827` | Testo heading | - |

### 1.2 Tipografia

| Token | Valore | Uso | Riferimento Sibill |
|-------|--------|-----|-------------------|
| `--font-sans` | `"Public Sans", "Inter", system-ui, sans-serif` | Font principale | Sibill usa Public Sans (Google Fonts) |
| `--font-mono` | `"JetBrains Mono", "Fira Code", monospace` | Importi, IBAN, codici | - |
| `--text-xs` | `0.75rem / 1rem` (12px) | Label minori, badge | - |
| `--text-sm` | `0.875rem / 1.25rem` (14px) | Body, tabelle, input | - |
| `--text-base` | `1rem / 1.5rem` (16px) | Paragrafi | - |
| `--text-lg` | `1.125rem / 1.75rem` (18px) | Titoli sezione | - |
| `--text-xl` | `1.25rem / 1.75rem` (20px) | Heading pagina | - |
| `--text-2xl` | `1.5rem / 2rem` (24px) | Titolo principale | - |
| `--text-3xl` | `1.875rem / 2.25rem` (30px) | KPI grandi (saldo, totale) | - |
| `--font-tick` | `13px` | Etichette assi grafici | Confermato in Sibill |
| `--font-weight-normal` | `400` | Body | - |
| `--font-weight-medium` | `500` | Label, badge | - |
| `--font-weight-semibold` | `600` | Heading, importi | - |
| `--font-weight-bold` | `700` | KPI, totali | - |

### 1.3 Spacing Scale

Basata su multipli di 4px (standard Tailwind):

| Token | Valore | Uso |
|-------|--------|-----|
| `--space-1` | `4px` | Padding minimo, gap icona-testo |
| `--space-2` | `8px` | Padding interno chip/badge |
| `--space-3` | `12px` | Gap tra elementi form |
| `--space-4` | `16px` | Padding card, gap colonne |
| `--space-5` | `20px` | Padding sezione |
| `--space-6` | `24px` | Margin tra sezioni |
| `--space-8` | `32px` | Padding container principale |

### 1.4 Border Radius

| Token | Valore | Uso |
|-------|--------|-----|
| `--radius-sm` | `4px` | Input, badge, chip |
| `--radius-md` | `6px` | Card, button |
| `--radius-lg` | `8px` | Modal, dialog |
| `--radius-xl` | `12px` | Card grandi, container |
| `--radius-full` | `9999px` | Avatar, badge circolare |

### 1.5 Shadows

| Token | Valore | Uso |
|-------|--------|-----|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Card, dropdown |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.07)` | Modal, popover |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Dialog, drawer |

### 1.6 Z-Index Scale

| Token | Valore | Uso | Riferimento Sibill |
|-------|--------|-----|-------------------|
| `--z-header` | `10` | Header sticky | - |
| `--z-sticky` | `20` | Sticky header tabella | Confermato |
| `--z-dropdown` | `50` | Dropdown, popover | - |
| `--z-tooltip` | `80` | Tooltip grafici, budget input | Confermato |
| `--z-modal` | `100` | Modal, dialog | - |
| `--z-aside` | `1000` | Pannello laterale | Confermato |

---

## 2. Mapping MUI --> shadcn/ui

Per ogni componente MUI usato in Sibill, il corrispondente shadcn/ui o la strategia di implementazione.

| Componente MUI (Sibill) | shadcn/ui equivalente | Note |
|--------------------------|----------------------|------|
| `<Button>` | `<Button>` | Varianti: default, destructive, outline, secondary, ghost, link |
| `<TextField>` / `<Input>` | `<Input>` | Con `<Label>` e messaggio errore |
| `<Select>` / `<MenuItem>` | `<Select>` | Basato su Radix Select |
| `<Autocomplete>` | `<Combobox>` (cmdk) | Ricerca con suggerimenti |
| `<Dialog>` / `<Modal>` | `<Dialog>` | Max-width: 600px (consent), 480px (budget) |
| `<Stepper>` / `<Step>` | Custom `<Stepper>` | Wizard step — da implementare custom |
| `<Checkbox>` | `<Checkbox>` | Basato su Radix Checkbox |
| `<Switch>` | `<Switch>` | Basato su Radix Switch |
| `<Tabs>` / `<Tab>` | `<Tabs>` | Navigazione tab (Cashflow/Categorie, Movimenti/Pagamenti/Regole) |
| `<Table>` | TanStack Table + `<Table>` | Headless per logica, shadcn per rendering |
| `<Chip>` | `<Badge>` | CategoryChip con colore personalizzato |
| `<Tooltip>` | `<Tooltip>` | Basato su Radix Tooltip |
| `<Popover>` | `<Popover>` | Ricerca categorie, filtri |
| `<Drawer>` / `<Aside>` | `<Sheet>` | Pannello laterale dettaglio (z-index 1000) |
| `<Accordion>` | `<Collapsible>` o `<Accordion>` | Categorie espandibili con persistenza localStorage |
| `<CircularProgress>` | `<Spinner>` (custom) | Loading states |
| `<Skeleton>` | `<Skeleton>` | Placeholder caricamento |
| `<Snackbar>` / `<Alert>` | `<Toast>` (sonner) | Notifiche: successo, errore, info |
| `<DatePicker>` | `<Calendar>` + `<Popover>` | Selezione periodo cash flow |
| `<ListItem>` / `<List>` | Custom con `<div>` | Lista con virtualizzazione (react-virtuoso) |
| React Aria Overlays | Radix Primitives | Accessibilita' nativa in shadcn/ui |

### Componenti da implementare custom

| Componente | Descrizione | Pattern Sibill |
|-----------|-------------|----------------|
| `<CategoryChip>` | Badge con colore categoria + indicatore auto (icona robot) | `CategoryChip-B_aD8aC5.js` |
| `<CurrencyInput>` | Input numerico con formattazione locale, solo positivi, max decimali | Budget input con `onlyPositive`, `maxDecimalPlaces` |
| `<ScrollSyncProvider>` | Sincronizzazione scroll orizzontale tra pannelli | Custom in Sibill per tabella cash flow |
| `<BankAccountFilter>` | Dropdown multi-select con IBAN, nome, saldo | `BankAccountFilter-DmD0iP_d.js` |
| `<EmptyState>` | Stato vuoto con icona + CTA | `EmptyState-BdglrTLA.js` |

---

## 3. Layout System

### 3.1 Struttura Base

```
+--------------------------------------------------+
|                  Header (sticky)                  |
+--------+-----------------------------------------+
|        |                                         |
| Sidebar|           Main Content                  |
| (240px)|                                         |
|        |                                         |
| - Logo |  +----------------------------------+   |
| - Menu |  |  Page Header (titolo + azioni)   |   |
| - User |  +----------------------------------+   |
|        |  |                                  |   |
|        |  |  Page Content                    |   |
|        |  |  (tabelle, grafici, form)        |   |
|        |  |                                  |   |
|        |  +----------------------------------+   |
|        |                                         |
+--------+-----------------------------------------+
```

### 3.2 Sidebar

| Proprieta' | Valore |
|-----------|--------|
| Larghezza desktop | 240px (expanded), 64px (collapsed) |
| Larghezza mobile | Overlay full-width (drawer) |
| Background | `--grey-900` o `white` con bordo |
| Voci menu | Icona + label, con badge (es. "Novita'" per F24) |
| Active state | Background `--primary-50`, bordo sinistro `--primary-500` |
| Sezioni | Come Sibill: Cashflow, Transazioni, Scadenzario, Fatture, F24, Settings |

### 3.3 Responsive Breakpoints

| Breakpoint | Valore | Layout |
|-----------|--------|--------|
| `sm` | 640px | Mobile — sidebar hidden (hamburger), tabella stacked |
| `md` | 768px | Tablet — sidebar collapsed (icone), tabella responsive |
| `lg` | 1024px | Desktop — sidebar expanded, layout completo |
| `xl` | 1280px | Desktop large — aside panel visibile senza sovrapposizione |
| `2xl` | 1536px | Desktop wide — spazi maggiori, grafici piu' larghi |

---

## 4. Pattern Tabelle (DataTable)

Basato su **TanStack Table** per la logica e **shadcn/ui Table** per il rendering. Pattern osservati nella pagina Movimenti di Sibill (212 righe, 9 filtri).

### 4.1 Struttura

```
+-----------------------------------------------------+
| Toolbar                                              |
| [Ricerca]  [Filtro 1] [Filtro 2]  ... [Scarica]    |
+-----------------------------------------------------+
| Header riga (sticky)                                 |
| [ ] | Data | Descrizione | Importo | Categoria | V  |
+-----------------------------------------------------+
| [ ] | 10/02 | Bonifico SEPA... | -1.500,00 | Gest..| |
| [ ] | 09/02 | Incasso POS...   | +2.340,00 | Inc..| |
| ...                                                  |
+-----------------------------------------------------+
| Footer: Totale: 212 movimenti | < 1 2 3 ... 5 >    |
+-----------------------------------------------------+
```

### 4.2 Feature della tabella

| Feature | Implementazione | Riferimento Sibill |
|---------|----------------|-------------------|
| **Filtri combinati** | Toolbar con dropdown (shadcn Select/Combobox) | 9 filtri nella pagina Movimenti |
| **Ricerca testo** | Input con debounce 300ms, cerca in descrizione e note | `filter[search]` |
| **Ordinamento** | Click su header → asc/desc/none, indicatore freccia | `sort=-date,-createdAt,-id` |
| **Paginazione** | Cursor-based, bottoni Prev/Next, page size selector (20/50/100) | `page[size]=50, page[cursor]=...` |
| **Selezione righe** | Checkbox per riga, select all, azioni batch | Checkbox "Verificato" |
| **Azioni batch** | Toolbar contestuale (categorizza, verifica, esporta) | [MIGLIORAMENTO] |
| **Export** | Pulsante "Scarica" → XLSX/CSV con stessi filtri | Content negotiation |
| **Colonne responsive** | Colonne nascoste su mobile, priorita' per importo e data | - |
| **Sticky header** | z-index 20, background opaco | Confermato in Sibill |
| **Virtual scroll** | react-virtuoso per dataset > 100 righe | Confermato in Sibill |

### 4.3 Pattern Filtri

| Tipo filtro | Componente | Esempio |
|-------------|-----------|---------|
| Testo libero | `<Input>` con icona search | Ricerca movimenti |
| Range date | `<DateRangePicker>` (Calendar + Popover) | Data operazione |
| Multi-select | `<Combobox>` con badge selezionati | Conti, Categorie |
| Range numerico | Due `<Input>` type=number (Min / Max) | Importo |
| Select singolo | `<Select>` | Status, Tipo, Visibilita' |

---

## 5. Pattern Form

### 5.1 Stack Form

- **react-hook-form** per gestione stato form
- **Zod** per schema validation (via `@hookform/resolvers/zod`)
- **shadcn/ui** per componenti (`Input`, `Select`, `Checkbox`, `Label`)
- Pattern: `useForm({ resolver: zodResolver(schema) })` con `Controller` per componenti custom

### 5.2 Layout Form

```
+------------------------------------------+
| Titolo Form                              |
+------------------------------------------+
| Label campo 1 *                          |
| [________________________________]       |
| Messaggio errore (rosso)                 |
|                                          |
| Label campo 2                            |
| [________________________________]       |
| Helper text (grigio)                     |
|                                          |
| Label campo 3 *        Label campo 4    |
| [_________________]    [________________]|
|                                          |
| +--------------------------------------+ |
| | Sezione espandibile (Collapsible)    | |
| | Label campo 5                        | |
| | [____________________________]       | |
| +--------------------------------------+ |
|                                          |
| [Annulla]                    [Salva]     |
+------------------------------------------+
```

### 5.3 Validazione Inline

| Stato | Stile | Trigger |
|-------|-------|---------|
| **Default** | Border `--grey-300` | - |
| **Focus** | Border `--primary-500`, ring 2px | Focus |
| **Errore** | Border `--error-500`, messaggio rosso sotto il campo | onBlur o onSubmit |
| **Successo** | Border `--success-500` (opzionale) | Dopo validazione positiva |
| **Disabled** | Background `--grey-100`, opacity 0.6 | Condizione logica |

### 5.4 Validazioni Osservate in Sibill

| Campo | Schema Zod | Contesto |
|-------|-----------|----------|
| Email login | `z.string().min(1).email()` | Normalizzata a lowercase |
| Password login | `z.string().min(1)` | - |
| Nome categoria | `z.string().min(1).max(255)` | Max 255 caratteri |
| Nome sottocategoria | `z.string().min(1).max(255)` | Max 255 caratteri |
| Colore categoria | `z.string()` | Formato hex |
| Budget amount | `z.refine(isNumeric)` | Solo positivi, 0 decimali |
| Budget months (extend) | `z.refine(months > 0)` | Obbligatorio se extend attivo |

---

## 6. Pattern Grafici (Recharts)

### 6.1 Grafico Cash Flow — ComposedChart

Il grafico principale di Sibill e' un `ComposedChart` con barre sovrapposte e linea del bilancio.

```
Struttura:
- ComposedChart (Recharts)
  - CartesianGrid (linee grigie)
  - XAxis (mesi: "feb 26", "mar 26", ...)
  - YAxis (importi EUR, dominio arrotondato ai migliaia)
  - Bar: inflow transactions (verde --success-600)
  - Bar: inflow outstanding (verde chiaro --success-400)
  - Bar: inflow pastdue (verde scuro --success-800)
  - Bar: outflow transactions (rosso --error-700)
  - Bar: outflow outstanding (rosso chiaro --error-500)
  - Bar: outflow pastdue (bordeaux --error-900)
  - Line: bilancio passato (continua, grigio --grey-700, stroke 2px)
  - Line: bilancio futuro (tratteggiata strokeDasharray=4, grigio --grey-700)
  - ReferenceLine: zero (asse orizzontale)
  - Tooltip: custom con dettaglio mese
  - ResponsiveContainer
```

### 6.2 Costanti Grafiche

| Costante | Valore | Uso |
|----------|--------|-----|
| `ChartColumnWidth` | `77.5px` | Larghezza colonna barra |
| `ChartHeight` | `300px` | Altezza area grafico |
| `FirstColumnWidth` | `232px` | Colonna label a sinistra |
| `LastColumnWidth` | `120px` | Colonna totale a destra |
| `BarSize` | `16px` | Larghezza singola barra |
| `LineStrokeWidth` | `2px` | Spessore linea bilancio |
| `FontSizeTick` | `13px` | Font size etichette assi |

### 6.3 Tipi di Grafico Utilizzati

| Tipo | Libreria | Contesto | Pattern |
|------|---------|----------|---------|
| **ComposedChart** (Bar + Line) | Recharts | Cash flow principale | Barre = transazioni, linea = bilancio |
| **BarChart** | Recharts | Dashboard fatture (ricavi/costi per mese) | Ipotizzato dalla pagina |
| **PieChart** / **DonutChart** | Recharts | Top clienti/fornitori | Ipotizzato dalla dashboard fatture |
| **LineChart** | Recharts | Trend temporali | Per analisi periodi |

### 6.4 Interattivita'

| Feature | Implementazione |
|---------|----------------|
| **Tooltip** | Custom con dettaglio: mese, importi inflow/outflow, bilancio, budget |
| **Click su barra** | Apre aside panel con dettaglio transazioni del mese/categoria |
| **Responsive** | `ResponsiveContainer` adatta alla larghezza del container |
| **Separazione past/future** | Linea continua (passato) + tratteggiata (futuro), punto di incontro = mese corrente |
| **Dominio Y** | Arrotondamento automatico ai migliaia (min/max + padding 1000) |

---

## 7. Empty States, Loading States, Error States

### 7.1 Empty States

| Stato | Componente | Contenuto | Azione |
|-------|-----------|-----------|--------|
| **Nessun dato** | `EmptyState` | Icona ricerca + "Nessun risultato trovato" | Suggerimento: modifica filtri |
| **Primo accesso senza conti** | `EmptyState` + CTA | Illustrazione tesoreria + "Connetti il tuo conto bancario" | Pulsante "Connetti banca" |
| **Modulo non attivo** | `EmptyState` | Illustrazione + "Modulo non attivo — Contattare l'amministratore per l'abilitazione" | Link a impostazioni aziendali |
| **Lista vuota** | `EmptyState` | Icona specifica + "Nessun [elemento] presente" | Pulsante "Crea il primo" |

### 7.2 Loading States

| Stato | Componente | Pattern |
|-------|-----------|---------|
| **Caricamento pagina** | `Skeleton` | Struttura grigia della pagina (tabella, grafico, card) |
| **Caricamento tabella** | `Skeleton` righe | 5-10 righe skeleton con colonne proporzionali |
| **Caricamento grafico** | `Skeleton` + barre grigie | Barre grigie placeholder + "Caricamento..." |
| **Azione in corso** | `Spinner` + testo | Pulsante con spinner: "Salvataggio..." |
| **Invio form** | Pulsante disabled + spinner | Previene doppio submit |

### 7.3 Error States

| Stato | Componente | Pattern |
|-------|-----------|---------|
| **Errore di rete** | `Toast` errore | "Errore di connessione. Riprova." con pulsante retry |
| **Errore validazione** | Inline sotto il campo | Testo rosso con icona alert |
| **Errore server (500)** | `Toast` errore | "Si e' verificato un errore. Riprova piu' tardi." |
| **Sessione scaduta** | Redirect automatico | Redirect a /login con `?rd=` per tornare alla pagina |
| **Permesso negato (403)** | Pagina dedicata | "Non hai i permessi per accedere a questa sezione" |
| **Pagina non trovata (404)** | Pagina dedicata | "Pagina non trovata" con link alla home |

### 7.4 Toast Notifications (Sonner)

Basati sui messaggi i18n osservati in Sibill:

| Tipo | Durata | Esempio |
|------|--------|---------|
| **Successo** | 3 secondi | "Categoria eliminata con successo" |
| **Errore** | 5 secondi (non auto-dismiss) | "Errore nel salvataggio del budget" |
| **Info** | 3 secondi | "Export in corso..." |
| **Warning** | 5 secondi | "Il budget della sottocategoria sovrascrivera' il budget della categoria" |

---

## 8. Responsive Design

### 8.1 Breakpoint e Adattamenti

| Breakpoint | Sidebar | Tabella | Grafico | Aside Panel |
|-----------|---------|---------|---------|-------------|
| `< 640px` (mobile) | Hidden (hamburger menu) | Stacked cards | Scroll orizzontale | Full-screen overlay |
| `640-768px` (tablet portrait) | Collapsed (icone) | Colonne ridotte | Responsive container | Overlay 80% width |
| `768-1024px` (tablet landscape) | Collapsed | Tutte le colonne, font ridotto | Full width | Overlay 50% width |
| `1024-1280px` (desktop) | Expanded 240px | Full | Full | Overlay 400px |
| `> 1280px` (desktop large) | Expanded 240px | Full + spazi | Full | Inline 400px (no overlay) |

### 8.2 Adattamenti Specifici

**Tabella movimenti su mobile:**
- Le colonne "Categoria", "Verificato" sono nascoste
- La riga diventa card: Data + Descrizione sopra, Importo a destra
- Filtri in un drawer (pulsante "Filtri" con badge conteggio filtri attivi)

**Cash flow su mobile:**
- Il grafico ha scroll orizzontale
- La tabella categorie sotto il grafico ha scroll orizzontale
- L'aside panel diventa full-screen

---

## 9. Accessibility (WCAG 2.1 AA)

### 9.1 Requisiti Minimi

| Requisito | Standard | Implementazione |
|-----------|---------|-----------------|
| **Contrasto colori** | WCAG 2.1 AA (4.5:1 testo, 3:1 UI) | Verificare tutti i token colore con tool di contrasto |
| **Keyboard navigation** | Tutti gli elementi interattivi raggiungibili da tastiera | Radix UI lo gestisce nativamente (focus trap in modal) |
| **Focus visible** | Ring 2px `--primary-700` su tutti gli elementi focusabili | Tailwind `focus-visible:ring-2` |
| **Screen reader** | Aria-label su tutti gli elementi non testuali | shadcn/ui include aria-* di default |
| **Form labels** | Ogni input ha un `<label>` associato | `<Label htmlFor=...>` obbligatorio |
| **Error messages** | Collegati al campo con `aria-describedby` | react-hook-form + shadcn pattern |
| **Skip navigation** | Link "Vai al contenuto" come primo elemento | Nascosto visivamente, visibile su focus |
| **Alt text** | Tutti i grafici hanno descrizione testuale alternativa | `aria-label` su `<ResponsiveContainer>` |
| **Reduced motion** | Animazioni rispettano `prefers-reduced-motion` | Tailwind `motion-reduce:` |

### 9.2 Pattern Accessibilita' da Sibill

Sibill usa **React Aria** per gestire accessibilita' in popover, overlay e modal. Il gestionale beneficia di **Radix UI** (base di shadcn/ui) che offre gli stessi pattern:

| Pattern | React Aria (Sibill) | Radix UI (Gestionale) |
|---------|--------------------|-----------------------|
| Modal focus trap | `useOverlay` | `<Dialog>` nativo |
| Combobox | Custom | `<Combobox>` con cmdk |
| Tooltip | `useTooltip` | `<Tooltip>` |
| Menu | Custom | `<DropdownMenu>` |
| Select | Custom | `<Select>` |

### 9.3 Testing Accessibilita'

| Tool | Uso |
|------|-----|
| **axe-core** (jest-axe) | Test automatici componenti |
| **Lighthouse** | Audit accessibilita' pagina |
| **Keyboard testing** | Tab attraverso tutti gli elementi interattivi |
| **Screen reader** | VoiceOver (macOS) / NVDA (Windows) per verifica manuale |
