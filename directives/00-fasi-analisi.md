# Fasi di analisi — Reverse Engineering Sibill

## Fase 1 — Ricognizione tecnica (Playwright)

1. Effettua il **login** alla webapp usando le credenziali da `credenziali.env`.
2. Ispeziona il DOM della pagina principale per identificare il framework frontend (React/Vue/Angular), librerie UI, versioni.
3. Estrai la **lista completa dei file JavaScript** caricati (bundle principali, chunk). Salva i sorgenti in `assets/js-sources/`.
4. Abilita il **monitoring delle richieste di rete** e naviga le sezioni principali per catturare tutte le chiamate API.
5. Ispeziona **cookie e storage** (localStorage, sessionStorage) per capire gestione sessione/token.
6. Identifica il **flusso di autenticazione**: tipo (JWT, session, OAuth2), endpoint di login/refresh, durata token.
7. Cattura **screenshot** di ogni pagina/sezione principale e salvali in `assets/screenshots/`.
8. Salva un **HAR completo** della sessione di navigazione in `assets/har/`.

## Fase 2 — Mappatura dell'applicazione e cattura UI/UX (Playwright)

9. Naviga sistematicamente **tutte le pagine/schermate** accessibili, cattura URL, titolo e screenshot per ciascuna.
10. Documenta il **flusso di navigazione** completo con un diagramma Mermaid (menu, sottomenu, pagine).
11. Per ogni sezione, identifica i **componenti UI** principali: tabelle, form, filtri, modal, wizard.
12. Per ogni pagina, estrai i **campi dei form** presenti: nomi, tipi, validazioni, valori di default, opzioni dei select/dropdown.
13. Mappa le **azioni disponibili** per ogni sezione: CRUD, export, import, filtri, ordinamento.

**Cattura UI/UX (PRIORITA ALTA — materiale per analisi offline):**

14. Per ogni pagina/sezione, cattura screenshot ad alta risoluzione in **stati diversi**: vuoto, con dati, in loading, con errori, con filtri applicati.
15. Documenta il **design system**: palette colori (hex), tipografia (font family, size, weight), spacing, componenti ricorrenti (card, tabelle, badge, toast, modal, tooltip).
16. Mappa il **sistema di navigazione**: menu principale, breadcrumb, tab, sidebar — cattura come l'utente si orienta nell'app.
17. Per ogni form: cattura layout, ordine dei campi, label, placeholder, messaggi di validazione, stati (vuoto, compilato, errore, disabled, focus).
18. Documenta i **pattern di interazione con i dati**: come vengono presentate tabelle con molti dati (paginazione/infinite scroll/virtual scroll), filtri (inline/sidebar/modal), ordinamento, selezione multipla, azioni batch, drill-down.
19. Cattura le **transizioni e feedback**: loading states, skeleton screens, toast notifications, progress bar, animazioni di conferma, empty states ("nessun risultato").
20. Identifica le **soluzioni di data visualization**: tipi di grafici usati, librerie (Chart.js, D3, Recharts), interattività (tooltip, zoom, drill-down, time range selector).

## Fase 3 — Cattura completa delle API (PRIORITA MASSIMA)

Questa fase è la più critica per le SPA moderne. L'obiettivo è intercettare e documentare OGNI chiamata API.

21. Con network monitoring attivo, naviga **ogni sezione** dell'applicazione e cattura tutte le chiamate. Per ogni endpoint documentare:
    - URL completo e metodo HTTP
    - Headers (specialmente Authorization, Content-Type)
    - Query parameters e request body
    - Response body (JSON) con struttura completa
    - Status code
    - Azione UI che triggera la chiamata

22. Identifica i **pattern API**: base URL, versioning, paginazione, filtri, ordinamento, gestione errori.
23. Mappa le **entità del modello dati** a partire dalle risposte JSON: campi, tipi, relazioni (ID di riferimento).
24. Identifica le **API di lookup/autocomplete** — spesso rivelano entità e relazioni non visibili nell'UI.
25. Genera un **diagramma ER** basato sulle entità osservate nelle risposte API.
26. Salva tutte le API traces in `assets/api-traces/` in formato JSON strutturato.

## Fase 4 — Analisi funzionale per modulo

Per ogni modulo, esegui un'analisi approfondita usando Playwright per navigare, inserire dati di test e catturare il comportamento.

**4A — Cash Flow e Previsioni:**
27. Come vengono calcolate le previsioni di cassa (input, algoritmo, orizzonte temporale).
28. Gestione dello scostamento previsto vs. consuntivo.
29. Fonti dati per le previsioni: scadenze, ricorrenze, pattern storici.
30. Granularità temporale: giornaliera, settimanale, mensile.

**4B — Riconciliazione Bancaria:**
31. Algoritmo di matching automatico: regole, pesi, soglie di tolleranza.
32. Gestione matching 1:1, 1:N, N:1, N:M.
33. Regole di riconciliazione personalizzabili: come vengono definite, priorità, eccezioni.
34. Flusso di riconciliazione manuale: interfaccia, suggerimenti, conferma.
35. Gestione delle partite aperte e chiusura parziale.

**4C — Gestione Scadenze e Pagamenti:**
36. Struttura dello scadenzario: campi, stati, workflow.
37. Tipi di disposizione supportati: bonifico SEPA, RiBa, SDD, F24, altro.
38. Flusso di creazione e approvazione pagamento.
39. Generazione file di pagamento: formato XML SEPA, tracciato CBI, altro.
40. Gestione di pagamenti multipli/massivi.

**4D — Connessione Bancaria:**
41. Metodo di connessione: API PSD2 (Open Banking), flussi CBI, import manuale.
42. Frequenza e modalità di sincronizzazione movimenti.
43. Formato dati movimenti bancari importati: campi, categorizzazione, metadati.
44. Gestione multi-banca e multi-conto.

**4E — Reportistica e Dashboard:**
45. Tipi di report disponibili e formati di export (PDF, Excel, CSV).
46. Dashboard: KPI mostrati, metriche, grafici, filtri.
47. Scarica almeno un esempio per ogni tipo di report/export in `assets/reports/`.

## Fase 5 — Analisi dei formati di integrazione (PRIORITA ALTA)

Questi formati sono fondamentali per il gestionale target.

48. Cattura esempi di **file di import** accettati dall'applicazione (movimenti bancari, scadenze, anagrafiche).
49. Cattura esempi di **file di export** generati (disposizioni di pagamento, report, estratti).
50. Per ogni formato, documenta: tipo file (XML, CSV, CBI), schema/struttura, campi obbligatori/opzionali, validazioni.
51. Se disponibili, analizza i **template di import** forniti dall'applicazione.
52. Documenta i **flussi CBI e SEPA XML** con particolare attenzione a: pain.001 (bonifici), pain.008 (SDD), camt.053 (estratto conto), camt.054 (notifica).

## Fase 6 — Analisi JavaScript e logica client-side (Playwright)

53. Estrai tutti i **file JavaScript** (bundle principali). Se minificati/bundled, usa source map se disponibili o beautify con `execution/beautify_js.py`.
54. Analizza il codice JS per identificare: calcoli eseguiti lato client, validazioni, trasformazioni dati, logica di business.
55. Cerca **costanti e configurazioni** hardcoded nel JS: limiti, soglie, URL di servizi, feature flag.
56. Identifica le **librerie di terze parti** usate e le loro versioni (React, Axios, date-fns, ecc.).

## Fase 7 — Analisi UI/UX approfondita (Playwright)

Questa fase approfondisce gli aspetti di design e usabilità catturati nella Fase 2, analizzandoli per la reimplementazione.

57. Documenta il **responsive design**: breakpoint CSS, come cambiano layout e navigazione su mobile/tablet/desktop. Cattura screenshot a diverse viewport width (375px, 768px, 1024px, 1440px).
58. Analizza l'**accessibilità**: uso di aria-label, ruoli ARIA, contrasto colori, keyboard navigation, focus management nei modal/drawer.
59. Identifica i **pattern di error handling UX**: come vengono mostrati errori di rete, errori di validazione inline, timeout, sessione scaduta, permessi mancanti. Cattura screenshot di ogni stato di errore.
60. Documenta i **micro-interaction pattern**: hover states, click feedback, drag & drop, shortcut da tastiera, selezione multipla con Shift/Ctrl.
61. Analizza la **gerarchia informativa**: come viene organizzata l'informazione più importante, progressive disclosure, informazioni on-demand (tooltip, expandable sections, drawer laterali).
62. Identifica i **pattern di workflow UX**: wizard multi-step, conferme distruttive (modal "sei sicuro?"), undo/redo, salvataggio automatico, draft.
63. Documenta i **pattern di filtro e ricerca**: ricerca globale vs. per sezione, filtri salvabili, filtri combinati, autocompletamento, ricerca fuzzy.
64. Per ogni pattern UI/UX rilevante, segnala con PATTERN UI/UX e documenta: componente, comportamento, contesto d'uso, perché funziona.

## Fase 8 — Verifica e validazione (Playwright + Python)

65. Crea un **set di dati di test** con valori noti per ogni modulo.
66. Usa Playwright per **inserire i dati di test** e catturare i risultati.
67. Per ogni logica dedotta, assegna un **livello di confidenza**:
    - Alta — Logica confermata da API response, JS client, o verifica con dati noti
    - Media — Logica coerente con i risultati ma non direttamente osservabile
    - Bassa — Logica ipotetica, necessita ulteriori verifiche
68. Confronta i risultati con calcoli manuali dove possibile.
