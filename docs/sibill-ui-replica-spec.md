# Sibill UI Replica Spec (Live + Local Diff)

Data audit: 2026-02-11
Target live verificato: `https://app.sibill.com` (sessione autenticata, pagine reali)
Repo analizzato: `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend`

## 1) Scope verificato live
Pagine live campionate con stile computato:
- `/cashflow`
- `/transactions/movements`
- `/transactions/payments`
- `/invoices/issued`
- `/settings/team`

Stati UI campionati:
- Layout dashboard completo (sidebar + contenuto + banner)
- Bottoni, tab, input, select, table header/body
- Badge/chip di categoria
- Modal conferma logout
- Modal form “Invita utente”
- Dropdown/listbox MUI in tabella movimenti
- Date range picker (popover grande con preset + calendario)

## 2) Design Tokens live (estratti da CSS vars reali)

### 2.1 Font e tipografia base
- Font famiglia principale: `"Public Sans", sans-serif`
- Body base:
  - `font-size: 13px`
  - `font-weight: 500`
  - `line-height: 19.5px`
  - `color: #1a1a1a`
  - `background: #ffffff`

Scala che ricorre più spesso nelle pagine live:
- `12px` (filtri, chip, table meta)
- `13px` (base app)
- `14px` (bottoni medium, form controls)
- `18px` (titoli modal)

Pesi più frequenti:
- `500` (default)
- `400` (input/option)
- `600` (CTA, titoli secondari)

### 2.2 Colori/radius/shadow (root vars live)

```json
{
  "--color-orange-200": "#fff2d9",
  "--color-forest-500": "#8cbabc",
  "--color-pink-300": "#ffe3e9",
  "--color-pink-500": "#ffc0ce",
  "--color-forest-700": "#338589",
  "--color-grey-200": "#f2f2f2",
  "--color-orange-600": "#ffcd66",
  "--color-orange-800": "#e37c30",
  "--color-lemon-300": "#f9f7c9",
  "--color-teal-400": "#b2e5e7",
  "--color-violet-600": "#6672ff",
  "--color-berry-400": "#c8b9df",
  "--color-pink-400": "#ffd5df",
  "--color-grey-600": "#817f7d",
  "--color-grey-100": "#f9f9f9",
  "--shadow-md": "0px 2px 8px 0px rgb(0 0 0 / 16%)",
  "--color-green-100": "#e5f7f0",
  "--color-lemon-400": "#f5f1a5",
  "--color-lobster-400": "#fdcbcb",
  "--color-lobster-800": "#f75251",
  "--color-berry-700": "#9173c0",
  "--color-pink-800": "#f9567c",
  "--color-teal-800": "#00a7b0",
  "--color-lemon-200": "#fbf9db",
  "--color-green-500": "#8cddba",
  "--color-violet-400": "#c0c8ff",
  "--color-grey-500": "#aba8a4",
  "--color-lobster-600": "#fa9797",
  "--color-lemon-600": "#ebe34b",
  "--color-sea-200": "#ccdfee",
  "--color-teal-600": "#66cad0",
  "--shadow-sm": "0px 2px 4px 0px rgb(0 0 0 / 20%)",
  "--color-sea-400": "#99bedd",
  "--color-sea-100": "#e5eff6",
  "--border-radius-md": "16px",
  "--shadow-lg": "0px 2px 16px 0px rgb(0 0 0 / 16%)",
  "--color-lobster-500": "#fbb1b1",
  "--color-forest-200": "#d9e8e9",
  "--color-berry-800": "#7550b0",
  "--color-lobster-200": "#fee5e5",
  "--color-forest-100": "#e5f0f0",
  "--color-lobster-100": "#feeeee",
  "--border-radius-xs": "4px",
  "--color-violet-500": "#969eff",
  "--color-pink-100": "#fff1f4",
  "--color-orange-300": "#fec",
  "--color-lemon-700": "#e0d500",
  "--color-berry-600": "#ac96d0",
  "--color-berry-200": "#e3dcef",
  "--color-forest-600": "#66a3a6",
  "--color-sea-600": "#669ecb",
  "--color-green-600": "#66d1a3",
  "--color-berry-100": "#e4e4e4",
  "--color-violet-300": "#d9deff",
  "--color-orange-700": "#ffab00",
  "--color-teal-700": "#33b9c0",
  "--color-orange-500": "#ffd98c",
  "--color-berry-300": "#d6cae7",
  "--color-berry-500": "#baa7d7",
  "--color-grey-800": "#1a1a1a",
  "--color-orange-400": "#ffe6b2",
  "--color-pink-600": "#ffabbe",
  "--color-violet-100": "#f5f6ff",
  "--color-pink-200": "#ffeaef",
  "--color-lobster-900": "#ea0b0b",
  "--color-sea-300": "#b2cee5",
  "--color-grey-300": "#e5e4e3",
  "--color-green-800": "#00b365",
  "--color-grey-700": "#535353",
  "--color-green-400": "#b2e8d1",
  "--border-radius-sm": "8px",
  "--color-forest-800": "#00666b",
  "--color-pink-700": "#ff7393",
  "--border-radius-full": "50%",
  "--color-violet-200": "#e5e9ff",
  "--color-orange-100": "#fff7e5",
  "--color-teal-300": "#ccedef",
  "--color-sea-800": "#005da9",
  "--color-green-200": "#d9f4e8",
  "--color-grey-400": "#d7d4d1",
  "--color-green-300": "#ccf0e0",
  "--color-teal-200": "#d9f2f3",
  "--color-sea-500": "#80aed4",
  "--color-forest-300": "#cce0e1",
  "--color-green-700": "#33c284",
  "--border-radius-xl": "40px",
  "--color-teal-500": "#8cd7db",
  "--color-lobster-300": "#fddcdc",
  "--color-forest-400": "#b2d1d3",
  "--color-lemon-500": "#f1eb81",
  "--color-lobster-700": "#f97574",
  "--border-radius-lg": "32px",
  "--color-sea-700": "#337dba",
  "--color-teal-100": "#e5f6f7"
}
```

### 2.3 Palette dominante osservata in pagina
Ricorrenza più alta:
- testo: `#1a1a1a`
- bg: `#ffffff`, `#f9f9f9`
- border neutro: `#817f7d`, `#e5e4e3`
- brand primario: `#6672ff`
- CTA dark: `#1a1a1a`

## 3) Layout live (misure)

Dashboard root (`1440x900` viewport):
- rail sinistra: `88px` fissa (`_container_ieaeu_1`)
- contenuto destra: `1352px` (`_dashboardPage_de77x_6`)
- header area contenuto: `height 96px`, padding `16px 24px`
- content area: `1352x804`

Nota: esiste un pannello submenu `280px` (`_submenu_17xzt_22`) con bordo destro `1px solid #f2f2f2` (gestione via stato/hover).

## 4) Component Specs live (computed)

### 4.1 Button
Primary CTA (es. “Aggiungi metodo di pagamento”, “Invita”, “Esporta small dark”):
- bg `#1a1a1a`
- text `#ffffff`
- border `none`
- radius `8px`
- font `14px/600` (oppure `12px/600` nella variante small h32)
- padding medium `0 16px`

Outlined:
- bg `transparent`
- text `#1a1a1a`
- border `1px solid #1a1a1a`
- radius `8px`

Filter/trigger controls:
- bg `#ffffff`
- border `1px solid #817f7d`
- radius `8px`
- font `12px/500`
- h tipica `32px`

### 4.2 Tabs
Esempio tab attiva (`Cashflow`, `Movimenti`, `Pagamenti`, `Emesse`):
- altezza `48px`
- attiva: bg `#6672ff`, text bianco
- inattiva: trasparente, text `#1a1a1a`
- padding tipico `13px 24px`
- radius segmentata (es. prima tab `8px 0 0 8px`)

### 4.3 Input e combobox
Input text standard (modal/team):
- size `197x38`
- border `1px solid #817f7d` (focus `#6672ff`)
- radius `8px`
- font `14px/400`
- padding `7px 12px`

Combobox/Select trigger:
- size `~197x38`
- border `1px solid #817f7d`
- radius `8px`
- font `14px/400`
- padding `8px 12px`

### 4.4 Table
Team table:
- `th`: bg `#f9f9f9`, text `#817f7d`, `12px/600`, padding `10px 16px`
- `td`: text `#1a1a1a`, `13px/500`, padding `16px`

Movimenti/Invoices table (dense):
- header operativo con filtri inline
- row/cell font spesso `12px/500`
- cell padding osservato `0 12px 0 24px` in colonne operative

### 4.5 Badge/Chip
Categoria pill tipica:
- radius `40px`
- altezza `32px`
- padding `0 12px`
- font `12px/500`
- esempi colore:
  - Incassi: bg `#8cd7db`
  - Non categorizzata: bg `#e5e4e3`
  - Gestione: bg `#c0c8ff`
  - Imposte e tasse: bg `#ffc0ce`
  - Personale: bg `#ffd98c`

### 4.6 Modal: conferma logout
Overlay:
- full viewport
- bg `rgba(0,0,0,0.25)`
- z-index `1300`

Dialog:
- size `600x196`
- bg `#ffffff`
- radius `16px`
- shadow `0 2px 16px rgba(0,0,0,0.16)`
- padding container `24px 0`
- gap verticale `24px`

Titolo:
- `18px/600`
- padding `24px`

Footer actions:
- justify-end, gap `12px`
- padding `0 24px`

Bottoni:
- Cancel outlined: h `38`, radius `8`, `14px/600`
- Confirm success green: bg `#00b365`, h `38`, radius `8`, `14px/600`

### 4.7 Modal: “Invita utente”
Overlay: come sopra (`rgba(0,0,0,0.25)`, z-index `1300`)

Dialog:
- size `458x659`
- bg white
- radius `16px`
- shadow `0 2px 16px rgba(0,0,0,0.16)`
- gap `24px`
- padding `24px 0`

Titolo:
- `18px/600`
- padding `24px`

Input form:
- `197x38`
- radius `8px`
- border default `#817f7d`, focus `#6672ff`
- `14px/400`

Action bar:
- Cancel outlined + Invita dark filled
- h `38`, radius `8`, `14px/600`

### 4.8 Dropdown/listbox (MUI autocomplete)
Popper:
- class `MuiAutocomplete-popper`
- z-index `1300`

Paper:
- bg `#fff`
- radius `8px`
- shadow `0 0 2px rgba(171,168,164,.24), 0 20px 40px -4px rgba(171,168,164,.24)`
- overflow-y auto

Option:
- h `32`
- padding `6px 16px`
- font `13px/500`

### 4.9 Date range picker
Popper grande:
- class `MuiPopper-root css-1xdhyk6`
- rect `890x432`
- z-index `2000`

Paper:
- class include `_paper_139kq_89`
- bg white
- radius `8px`
- shadow `-20px 20px 40px -4px rgba(145,158,171,.24), 0 0 2px rgba(145,158,171,.24)`

Preset list item selezionato:
- class `_item_1nw8i_13 _sameRange_1nw8i_23`
- bg `#f5f6ff`
- padding `12px 24px`
- font base `13px/500`
- label preset `14px/600`

Day button:
- size `40x40`
- shape circle (`50%`)
- variant ghost
- font `14px/600`
- day fuori mese text `#817f7d`

### 4.10 Iconografia
Distribuzione live:
- dimensioni prevalenti SVG: `20x20`, `24x24`
- stroke width computato tipico: `1px`
- colore icone prevalente: `#1a1a1a`, con accenti brand `#6672ff`

## 5) Confronto con codice locale (gap principali)

### 5.1 Typography e font
Locale:
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/app/layout.tsx` usa `Geist` e `Geist Mono`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/app/globals.css` delega a token shadcn generici

Live Sibill:
- `Public Sans` unico font UI
- base `13px/500`

Gap: alto. Da solo cambia totalmente percezione della UI.

### 5.2 Token system
Locale:
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/app/globals.css` usa token OKLCH generici shadcn (primary/secondary/muted)
- non contiene palette Sibill (`--color-violet-*`, `--color-grey-*`, ecc)

Live:
- design system ampio con token cromatici business-specific
- radius canonici 4/8/16/32/40
- shadow canoniche sm/md/lg specifiche

Gap: critico.

### 5.3 Component primitives
Locale (shadcn/radix default) vs Live (custom mix + MUI in parti tabellari):
- Button locale (`/components/ui/button.tsx`): `rounded-md`, h9/h8/h10 standard shadcn
- Input locale (`/components/ui/input.tsx`): dimensioni e focus ring diversi
- Dialog locale (`/components/ui/dialog.tsx`): overlay `bg-black/50`, max width shadcn
- Popover/dropdown locale (`/components/ui/popover.tsx`, `/components/ui/dropdown-menu.tsx`): shadow/radius/padding non allineati
- Calendar locale (`/components/ui/calendar.tsx`): `react-day-picker`, non coincide con date range picker live

Gap: critico su quasi tutti i componenti base.

### 5.4 Layout
Locale:
- sidebar classica `w-64` in `/components/layout/sidebar.tsx`
- header semplice con titolo testuale in `/components/layout/header.tsx`
- shell `/app/(dashboard)/layout.tsx` con `p-6` standard

Live:
- rail da `88px` + submenu `280px`
- struttura nav molto più ricca, badge, sezioni multiple, supporto/impostazioni integrati
- top bar e content spacing diversi

Gap: critico.

### 5.5 Status chips e palette semantica
Locale:
- mapping tailwind standard (es. `bg-blue-100`, `bg-green-100`, `bg-purple-100`) in `/types/payment.ts`, `/types/report.ts`, `/types/integration.ts`, `/types/cash-flow.ts`, `/types/dashboard.ts`

Live:
- chip con palette proprietaria pastel (`teal/pink/orange/violet/grey`), radius 40, altezza 32, font 12/500

Gap: alto.

### 5.6 Auth UI
Locale:
- card centrate shadcn (`/app/(auth)/login/page.tsx`, `/register/page.tsx`, `/forgot-password/page.tsx`)
- look totalmente diverso dal login live Sibill

Gap: alto.

## 6) Specifica operativa per coding agent (replica visiva 1:1)

### 6.1 Ordine consigliato
1. Sostituire font + token globali
2. Rifare primitives UI core (button/input/select/dialog/popover/table/chip)
3. Rifare shell layout dashboard (rail + submenu + content)
4. Rifinire pagine chiave (movimenti/pagamenti/fatture/team/cashflow)
5. QA visuale con diff screenshot

### 6.2 Hard requirements (non negoziabili)
- Font globale: `Public Sans`
- Base typography: `13px / 500 / 19.5px`
- Radius canonico: `4, 8, 16, 40`
- Overlay modal: `rgba(0,0,0,0.25)`
- Modal card: white + `16px` radius + shadow `0 2px 16px rgba(0,0,0,.16)`
- Primary button: bg `#1a1a1a`, text white, radius `8px`
- Brand active/tab: `#6672ff`
- Chip: h `32`, radius `40`, font `12/500`
- Dropdown paper: radius `8`, shadow MUI-like (vedi sopra)

### 6.3 File locali da toccare per primi
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/app/layout.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/app/globals.css`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/ui/button.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/ui/input.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/ui/select.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/ui/dialog.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/ui/alert-dialog.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/ui/dropdown-menu.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/ui/popover.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/ui/table.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/ui/badge.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/layout/sidebar.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/components/layout/header.tsx`
- `/Users/nicolascarpa/Desktop/Progetti/sibill-re/frontend/src/app/(dashboard)/layout.tsx`

### 6.4 QA checklist finale
- Pixel check su: tab h48, button h32/h38, chip h32, modal radius16
- Color check su: text `#1a1a1a`, primary violet `#6672ff`, border neutral `#817f7d`
- Overlay check: 25% black
- Cross-page consistency check: Movimenti, Pagamenti, Emesse, Team, Cashflow
- Screenshot diff desktop 1440x900 + mobile

---

Questo documento contiene i valori necessari per una replica visiva ad alta fedeltà; per una copia effettivamente “identica”, il coding agent deve applicare i token live a tutte le primitives e poi rifinire pagina per pagina con screenshot diff.
