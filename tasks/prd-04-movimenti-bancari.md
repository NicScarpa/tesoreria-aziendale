# PRD-04 — Movimenti Bancari

**Versione:** 1.0
**Data:** 10 febbraio 2026
**Basato su:** RE Sibill (docs/04, docs/13), DB Schema (.tmp/db-schema.md)
**Stato:** Draft

---

## 1. Panoramica Modulo

Il modulo Movimenti Bancari gestisce la visualizzazione, categorizzazione e gestione dei movimenti bancari importati (via Open Banking o file). E' la base per la riconciliazione bancaria e il cash flow.

### 1.1 Obiettivi

- Visualizzare i movimenti con filtri avanzati (9+ filtri come in Sibill)
- Supportare la categorizzazione automatica (regole) e manuale
- Supportare lo split di categorizzazione (un movimento su piu' categorie)
- Gestire le regole di categorizzazione custom
- Tracciare le controparti e permettere l'associazione automatica

### 1.2 Tabelle DB coinvolte

| Tabella | Ruolo |
|---------|-------|
| `transactions` | Movimenti bancari |
| `categories` | Categorie di primo livello |
| `subcategories` | Sottocategorie (livello 2) |
| `categorization_rules` | Regole di categorizzazione automatica |
| `transaction_allocations` | Split categorizzazione |
| `counterparts` | Controparti (clienti/fornitori) |
| `attachments` | Allegati ai movimenti |
| `reconciliation_matches` | Match di riconciliazione (relazione) |

---

## 2. Tabella Movimenti Filtrata

### 2.1 Visualizzazione lista

La tabella movimenti presenta i seguenti campi per ogni riga:

| Campo UI | Campo DB | Tipo | Note |
|----------|----------|------|------|
| Data operazione | `transaction_date` | DATE | Ordinamento principale |
| Data valuta | `value_date` | DATE | Opzionale |
| Descrizione | `description` | TEXT | Troncato con tooltip |
| Importo | `amount` | NUMERIC(15,2) | Con segno, formattato con valuta |
| Direzione | `direction` | ENUM | INFLOW (verde) / OUTFLOW (rosso) |
| Categoria | `category_id` -> `categories.name` | FK | Con colore e icona sorgente |
| Sottocategoria | `subcategory_id` -> `subcategories.name` | FK | Opzionale |
| Controparte | `counterpart_name` o `counterpart_id` -> `counterparts.company_name` | VARCHAR/FK | Nome della controparte |
| Stato riconciliazione | via `reconciliation_matches` | Calcolato | Riconciliato / Non riconciliato / Suggerito |
| Verificato | `verified` | BOOLEAN | Checkbox |
| Conto | `bank_account_id` -> `bank_accounts.nickname` | FK | Nome conto |

### 2.2 Filtri

Basati su quelli osservati in Sibill (9+ filtri):

| # | Filtro | Campo DB / Logica | Tipo UI | Obbligatorio |
|---|--------|-------------------|---------|-------------|
| 1 | **Data range** | `transaction_date BETWEEN :start AND :end` | Date picker range | No (default: ultimi 30 giorni) |
| 2 | **Importo minimo** | `ABS(amount) >= :min` | Input numerico | No |
| 3 | **Importo massimo** | `ABS(amount) <= :max` | Input numerico | No |
| 4 | **Direzione** | `direction = :direction` | Select (INFLOW/OUTFLOW/tutti) | No |
| 5 | **Categoria** | `category_id = :cat_id` | Select con ricerca | No |
| 6 | **Stato riconciliazione** | JOIN `reconciliation_matches` | Select (Riconciliato/Non riconciliato/Suggerito) | No |
| 7 | **Conto bancario** | `bank_account_id IN (:ids)` | Multi-select | No |
| 8 | **Controparte** | `counterpart_id = :id` OR `counterpart_name ILIKE :name` | Autocomplete | No |
| 9 | **Testo libero** | Full-text search su `description`, `remittance_info`, `notes` | Input testo | No |
| 10 | **Stato transazione** | `status = :status` | Select (PENDING/BOOKED/REJECTED) | No |
| 11 | **Non categorizzati** | `category_id IS NULL` | Toggle | No |
| 12 | **Verificato** | `verified = :bool` | Toggle | No |

### 2.3 Ordinamento

Default: `-transaction_date, -created_at, -id` (come in Sibill)

Ordinamenti disponibili:
- Data operazione (ASC/DESC)
- Importo (ASC/DESC)
- Controparte (alfabetico)

### 2.4 Metadati aggregati

Endpoint separato per i totali (come `/transactions/metadata` di Sibill):

```json
{
  "total": 42,
  "totals_eur": {
    "positive": { "currency": "EUR", "amount": "5645.30" },
    "negative": { "currency": "EUR", "amount": "-5181.79" }
  },
  "total_uncategorised": 7
}
```

---

## 3. Dettaglio Movimento

### 3.1 Tutti i campi (da tabella `transactions`)

| Campo | Tipo DB | Editabile | Note |
|-------|---------|-----------|------|
| `id` | UUID PK | No | - |
| `company_id` | UUID FK | No | - |
| `bank_account_id` | UUID FK | No | Conto di appartenenza |
| `amount` | NUMERIC(15,2) | No | Positivo=entrata, negativo=uscita |
| `currency` | VARCHAR(3) | No | ISO 4217 |
| `direction` | `flow_direction` | No | Derivato dal segno di amount |
| `transaction_date` | DATE | No | Data operazione |
| `value_date` | DATE | No | Data valuta |
| `description` | TEXT | No | Descrizione dal provider |
| `remittance_info` | TEXT | No | Causale/riferimento |
| `transaction_type` | `transaction_type` | No | CREDIT_TRANSFER, DIRECT_DEBIT, etc. |
| `category_id` | UUID FK | **Si** | Categoria assegnata |
| `subcategory_id` | UUID FK | **Si** | Sottocategoria |
| `categorization_source` | ENUM | No (auto) | MANUAL, AUTOMATIC, RULE, IMPORT |
| `counterpart_id` | UUID FK | **Si** | Controparte associata |
| `counterpart_name` | VARCHAR(255) | No | Nome controparte dalla banca |
| `counterpart_iban` | VARCHAR(34) | No | IBAN controparte |
| `status` | `transaction_status` | No | PENDING, BOOKED, REJECTED |
| `verified` | BOOLEAN | **Si** | Checkbox verifica manuale |
| `notes` | TEXT | **Si** | Note utente |
| `hidden_at` | TIMESTAMPTZ | **Si** | Nascondimento |

### 3.2 Relazioni incluse

- **Conto bancario** (`bank_accounts`) con istituto
- **Categoria** e **sottocategoria**
- **Controparte** (dettaglio anagrafica)
- **Allocazioni** (`transaction_allocations`) per split categorizzazione
- **Riconciliazioni** (`reconciliation_matches`) con stato
- **Allegati** (`attachments`)
- **Pagamento** (`payment_orders`) se generato da un pagamento

---

## 4. Categorizzazione Automatica

### 4.1 Logica di applicazione

Basata sulla struttura osservata in Sibill (docs/13 sezione 11):

```pseudocode
function categorizzaTransazione(transaction):
    // 1. Recupera tutte le regole attive per l'azienda e la direzione
    rules = SELECT * FROM categorization_rules
            WHERE company_id = transaction.company_id
            AND direction = transaction.direction
            AND is_active = TRUE
            ORDER BY priority DESC

    // 2. Per ogni regola, verifica TUTTE le condizioni (AND)
    FOR EACH rule IN rules:
        match = TRUE

        FOR EACH condition IN rule.conditions:
            IF condition.type == 'ACCOUNT':
                IF transaction.bank_account_id != condition.value:
                    match = FALSE; BREAK

            ELIF condition.type == 'KEYWORDS':
                // Tutte le keywords devono essere presenti nella descrizione
                text = LOWER(transaction.description || ' ' || transaction.remittance_info)
                FOR EACH keyword IN condition.value:
                    IF keyword NOT IN text:
                        match = FALSE; BREAK

            ELIF condition.type == 'TRANSACTION_TYPE':
                IF transaction.transaction_type NOT IN condition.value:
                    match = FALSE; BREAK

        // 3. Se tutte le condizioni matchano, applica l'azione
        IF match:
            IF rule.action_type == 'SET_CATEGORY':
                transaction.category_id = rule.category_id
                transaction.subcategory_id = rule.subcategory_id
                transaction.categorization_source = 'RULE'
                RETURN  // Prima regola che matcha vince (priority)

    // 4. Se nessuna regola matcha, la transazione resta non categorizzata
```

### 4.2 Trigger della categorizzazione automatica

La categorizzazione automatica viene eseguita:

1. **All'importazione** di nuovi movimenti (sync Open Banking o import file)
2. **Alla creazione/modifica** di una regola (ri-applica a movimenti non categorizzati)
3. **Manualmente** su richiesta dell'utente ("Ricategorizza tutti")

---

## 5. Categorizzazione Manuale

### 5.1 Assegnazione categoria

L'utente puo' assegnare manualmente una categoria (e opzionalmente una sottocategoria) a un movimento. Questo sovrascrive qualsiasi categorizzazione automatica e imposta `categorization_source = 'MANUAL'`.

### 5.2 Creazione categoria al volo

Nel dialog di selezione categoria, l'utente puo' creare una nuova categoria o sottocategoria direttamente (come osservato in Sibill):

- **Nuova categoria**: nome (max 255 caratteri), colore (hex)
- **Nuova sottocategoria**: nome (max 255 caratteri), collegata alla categoria selezionata

---

## 6. Split Categorizzazione

### 6.1 Tabella `transaction_allocations`

Un movimento puo' essere diviso su piu' categorie tramite la tabella `transaction_allocations`:

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `id` | UUID PK | - |
| `transaction_id` | UUID FK | Movimento di riferimento |
| `category_id` | UUID FK | Categoria dell'allocazione |
| `subcategory_id` | UUID FK | Sottocategoria (opzionale) |
| `amount` | NUMERIC(15,2) | Importo allocato |
| `currency` | VARCHAR(3) | Valuta |
| `percentage` | NUMERIC(5,2) | Percentuale del totale (alternativa) |

### 6.2 Regole di split

```pseudocode
// Vincolo: la somma delle allocazioni deve essere uguale all'importo della transazione
ASSERT SUM(allocations.amount) == ABS(transaction.amount)

// Quando si crea uno split:
// 1. Si rimuove la categorizzazione diretta dalla transazione
transaction.category_id = NULL
transaction.subcategory_id = NULL
// 2. Si creano le allocazioni
INSERT INTO transaction_allocations (transaction_id, category_id, amount, ...)
// 3. La transazione viene considerata "categorizzata" se ha allocazioni
```

### 6.3 Visualizzazione split

Nella lista movimenti, un movimento con split mostra:
- Icona indicante lo split
- Tooltip/espansione con dettaglio allocazioni
- Nel dettaglio: lista completa con importo e percentuale per ogni allocazione

---

## 7. Regole di Categorizzazione Custom

### 7.1 CRUD Regole

Basate sulla tabella `categorization_rules`:

**Creazione regola:**

| Campo | Tipo | Obbligatorio | Note |
|-------|------|-------------|------|
| `name` | VARCHAR(255) | No | Nome descrittivo |
| `direction` | `flow_direction` | Si | INFLOW o OUTFLOW |
| `conditions` | JSONB | Si | Almeno 1 condizione |
| `action_type` | `rule_action_type` | Si | SET_CATEGORY |
| `category_id` | UUID FK | Si | Categoria destinazione |
| `subcategory_id` | UUID FK | No | Sottocategoria destinazione |
| `priority` | INTEGER | Si | Ordine di esecuzione |
| `is_active` | BOOLEAN | Si | DEFAULT TRUE |

### 7.2 Tipi di condizione (docs/13 sezione 3.7)

| Tipo | Campo `conditions` JSONB | Descrizione | Esempio |
|------|-------------------------|-------------|---------|
| `ACCOUNT` | `{"type": "ACCOUNT", "value": "uuid"}` | Filtra per conto bancario specifico | Solo movimenti dal conto UniCredit |
| `KEYWORDS` | `{"type": "KEYWORDS", "value": ["stipendio", "mensile"]}` | Parole chiave nella descrizione (AND tra keywords) | "stipendio" E "mensile" nella descrizione |
| `TRANSACTION_TYPE` | `{"type": "TRANSACTION_TYPE", "value": ["CREDIT_TRANSFER"]}` | Tipo di transazione | Solo bonifici |

Le condizioni all'interno di una regola sono in **AND** (tutte devono matchare).

### 7.3 Priorita'

Le regole vengono valutate in ordine di `priority` decrescente (valore piu' alto = valutata prima). La prima regola che matcha viene applicata. L'utente puo' riordinare le regole tramite drag & drop.

### 7.4 Test regola

Prima di salvare, l'utente puo' testare la regola per vedere quanti movimenti esistenti verrebbero categorizzati.

---

## 8. Eliminazione e Side-Effects

Basato su docs/13 sezione 11 (effetti collaterali eliminazione):

### 8.1 Eliminazione movimento

```pseudocode
function eliminaMovimento(transaction_id):
    transaction = GET transactions WHERE id = transaction_id

    // 1. Elimina riconciliazioni associate
    DELETE FROM reconciliation_matches WHERE transaction_id = transaction_id
    // Side-effect: le invoice_payments collegate tornano a UNPAID/PARTIALLY_PAID
    FOR EACH match IN deleted_matches:
        ricalcolaPagamentoScadenza(match.invoice_payment_id)

    // 2. Elimina allocazioni split
    DELETE FROM transaction_allocations WHERE transaction_id = transaction_id

    // 3. Elimina allegati
    DELETE FROM attachments WHERE entity_type = 'transactions' AND entity_id = transaction_id

    // 4. Elimina la transazione
    DELETE FROM transactions WHERE id = transaction_id

    // 5. Ricalcola saldi del conto
    ricalcolaSaldi(transaction.bank_account_id)

    // 6. Ricalcola cash flow per il mese della transazione
    ricalcolaCashFlow(transaction.company_id, transaction.transaction_date)

    // 7. Audit log
    INSERT INTO audit_log (action='DELETE', entity_type='transactions', entity_id=transaction_id, ...)
```

### 8.2 Eliminazione categoria

Come documentato in docs/13 sezione 7.1:

1. **Transazioni**: perdono la categorizzazione (`category_id = NULL`, `subcategory_id = NULL`)
2. **Fatture/documenti**: perdono la categorizzazione
3. **Sottocategorie**: tutte eliminate (CASCADE)
4. **Regole**: le `categorization_rules` che usano questa categoria vengono eliminate
5. **Budget**: i `budgets` associati vengono eliminati
6. **Ricorrenze**: le `recurring_transactions` perdono la categorizzazione
7. **Cash flow**: ricalcolo necessario per i mesi impattati

### 8.3 Eliminazione sottocategoria

Due opzioni per l'utente (come in Sibill):

- **"Rimuovi categorizzazione"** (`mark_uncategorised`): rimuove sia categoria che sottocategoria dalle entita' associate
- **"Assegna alla categoria padre"** (`parent_category`): mantiene la categoria padre, rimuove solo la sottocategoria

---

## 9. Controparte

### 9.1 Associazione automatica

Quando un movimento viene importato con `counterpart_name` e/o `counterpart_iban`:

```pseudocode
function associaControparte(transaction):
    // 1. Cerca per IBAN (match esatto)
    IF transaction.counterpart_iban IS NOT NULL:
        counterpart = SELECT FROM counterparts
                      WHERE company_id = transaction.company_id
                      AND bank_identifier = transaction.counterpart_iban
                      AND deleted_at IS NULL
        IF counterpart FOUND:
            transaction.counterpart_id = counterpart.id
            RETURN

    // 2. Cerca per nome (match fuzzy)
    IF transaction.counterpart_name IS NOT NULL:
        counterpart = SELECT FROM counterparts
                      WHERE company_id = transaction.company_id
                      AND company_name ILIKE '%' || transaction.counterpart_name || '%'
                      AND deleted_at IS NULL
                      LIMIT 1
        IF counterpart FOUND:
            transaction.counterpart_id = counterpart.id
            RETURN

    // 3. Se non trovata, crea controparte VIRTUAL
    new_counterpart = INSERT INTO counterparts (
        company_id, kind='VIRTUAL', identity_type='COMPANY',
        company_name=transaction.counterpart_name,
        bank_identifier=transaction.counterpart_iban
    )
    transaction.counterpart_id = new_counterpart.id
```

### 9.2 Merge controparti duplicate

Le controparti VIRTUAL create automaticamente possono essere fuse con controparti REAL:

```pseudocode
function mergeControparti(source_id, target_id):
    // 1. Aggiorna tutte le transazioni
    UPDATE transactions SET counterpart_id = target_id
    WHERE counterpart_id = source_id

    // 2. Aggiorna fatture
    UPDATE invoices SET counterpart_id = target_id
    WHERE counterpart_id = source_id

    // 3. Imposta parent (struttura gerarchica)
    UPDATE counterparts SET parent_id = target_id
    WHERE id = source_id

    // 4. Oppure elimina la controparte sorgente (soft delete)
    UPDATE counterparts SET deleted_at = NOW()
    WHERE id = source_id
```

---

## 10. API Endpoints

| Metodo | Path | Descrizione | Parametri principali |
|--------|------|-------------|---------------------|
| `GET` | `/api/v1/transactions` | Lista movimenti filtrata | company_id, filtri (sezione 2.2), sort, include, page |
| `GET` | `/api/v1/transactions/:id` | Dettaglio movimento | include=allocations,reconciliations,attachments |
| `GET` | `/api/v1/transactions/metadata` | Metadati aggregati (totali) | company_id, stessi filtri della lista |
| `PATCH` | `/api/v1/transactions/:id` | Modifica (categoria, note, verified) | Body: category_id, subcategory_id, notes, verified |
| `DELETE` | `/api/v1/transactions/:id` | Eliminazione con side-effects | - |
| `POST` | `/api/v1/transactions/:id/allocations` | Crea split categorizzazione | Body: allocations[] |
| `PUT` | `/api/v1/transactions/:id/allocations` | Aggiorna split (replace all) | Body: allocations[] |
| `DELETE` | `/api/v1/transactions/:id/allocations` | Rimuovi split | - |
| `POST` | `/api/v1/transactions/:id/attachments` | Carica allegato | Multipart: file |
| `GET` | `/api/v1/categorization-rules` | Lista regole | company_id, direction, is_active |
| `POST` | `/api/v1/categorization-rules` | Crea regola | Body: name, direction, conditions, action_type, category_id, ... |
| `PATCH` | `/api/v1/categorization-rules/:id` | Modifica regola | Body: parziale |
| `DELETE` | `/api/v1/categorization-rules/:id` | Elimina regola | - |
| `POST` | `/api/v1/categorization-rules/:id/test` | Testa regola | Restituisce conteggio movimenti che matchano |
| `POST` | `/api/v1/transactions/recategorize` | Ri-applica regole | company_id, direction (opz.), ricategorizza movimenti non categorizzati |

---

## 11. Functional Requirements

### FR-MOV-001: Visualizzazione lista movimenti con filtri

**Given** un utente autenticato con accesso a un'azienda
**When** accede alla pagina movimenti
**Then** vengono mostrati i movimenti del periodo default (ultimi 30 giorni), ordinati per data decrescente, con paginazione cursor-based (50 per pagina), e tutti i 12 filtri disponibili nella barra filtri

### FR-MOV-002: Filtro per testo libero

**Given** la lista movimenti e' visualizzata
**When** l'utente inserisce "stipendio" nel campo di ricerca testo
**Then** vengono mostrati solo i movimenti la cui `description`, `remittance_info` o `notes` contengono "stipendio" (case insensitive, full-text search)

### FR-MOV-003: Categorizzazione manuale

**Given** un movimento non categorizzato
**When** l'utente seleziona una categoria dal menu
**Then** `category_id` viene aggiornato, `categorization_source` viene impostato a `'MANUAL'`, il contatore `total_uncategorised` nei metadata diminuisce di 1

### FR-MOV-004: Categorizzazione automatica all'import

**Given** nuovi movimenti importati (sync Open Banking o import file)
**When** i movimenti vengono salvati in `transactions`
**Then** per ogni movimento, il sistema valuta le `categorization_rules` in ordine di priorita', la prima regola che matcha viene applicata con `categorization_source = 'RULE'`

### FR-MOV-005: Split categorizzazione

**Given** un movimento di EUR 1.000
**When** l'utente crea uno split con EUR 700 su "Stipendi" e EUR 300 su "Contributi"
**Then** vengono create 2 righe in `transaction_allocations`, la `category_id` sulla transazione viene rimossa, la somma delle allocazioni (700 + 300) corrisponde all'importo assoluto della transazione (1.000)

### FR-MOV-006: Creazione regola di categorizzazione

**Given** un utente con ruolo ADMIN o EDITOR
**When** crea una regola con condizioni: KEYWORDS=["stipendio"], TRANSACTION_TYPE=["CREDIT_TRANSFER"], direzione=INFLOW, azione=SET_CATEGORY "Stipendi"
**Then** la regola viene salvata in `categorization_rules`, tutti i movimenti INFLOW non categorizzati che contengono "stipendio" e sono di tipo CREDIT_TRANSFER vengono categorizzati automaticamente

### FR-MOV-007: Eliminazione movimento con side-effects

**Given** un movimento riconciliato con una scadenza
**When** l'utente elimina il movimento
**Then** la riconciliazione viene eliminata, la scadenza torna a stato UNPAID, il saldo del conto viene ricalcolato, il cash flow del mese viene ricalcolato, viene creato un audit_log

### FR-MOV-008: Verifica manuale

**Given** un movimento qualsiasi
**When** l'utente clicca la checkbox "Verificato"
**Then** `verified` viene impostato a TRUE, il movimento viene marcato visivamente come verificato nella lista

### FR-MOV-009: Associazione controparte automatica

**Given** un nuovo movimento importato con counterpart_iban = "IT60X0542811101000000123456"
**When** il movimento viene salvato
**Then** il sistema cerca una controparte con `bank_identifier` corrispondente; se trovata, associa `counterpart_id`; se non trovata, crea una controparte VIRTUAL con kind='VIRTUAL'

### FR-MOV-010: Merge controparti

**Given** una controparte VIRTUAL "MARIO ROSSI SRL" e una controparte REAL "Mario Rossi S.r.l."
**When** l'utente esegue il merge dalla VIRTUAL alla REAL
**Then** tutte le transazioni e fatture vengono riassociate alla controparte REAL, la controparte VIRTUAL viene eliminata (soft delete) o impostata come figlia (parent_id)

### FR-MOV-011: Metadati aggregati

**Given** la lista movimenti con filtri applicati
**When** i filtri cambiano
**Then** viene aggiornato il contatore totale movimenti, i totali entrate/uscite in EUR, e il conteggio movimenti non categorizzati, in una chiamata separata all'endpoint metadata

### FR-MOV-012: Creazione categoria al volo

**Given** l'utente sta categorizzando un movimento
**When** la categoria desiderata non esiste e l'utente digita un nuovo nome
**Then** viene creata una nuova categoria con il nome inserito (max 255 caratteri), un colore di default (#6b7280), e viene immediatamente assegnata al movimento
