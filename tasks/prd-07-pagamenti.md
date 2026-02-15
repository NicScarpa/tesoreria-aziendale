# PRD-07 — Pagamenti e Disposizioni

**Versione:** 1.0
**Data:** 10 febbraio 2026
**Basato su:** RE Sibill (docs/04, docs/08, docs/10, docs/13), DB Schema (.tmp/db-schema.md)
**Stato:** Draft

---

## 1. Panoramica Modulo

Il modulo Pagamenti gestisce il ciclo di vita completo delle **disposizioni di pagamento** verso fornitori e terzi: dalla creazione alla esecuzione, passando per l'approvazione. Supporta pagamenti singoli, bulk, e diversi strumenti di pagamento (bonifici SEPA, RiBa, SDD, F24).

### 1.1 Obiettivi

- Gestire il ciclo di vita del pagamento con state machine definita (8 stati)
- Supportare la creazione di pagamenti da scadenze, manuali e da fattura
- Supportare pagamenti bulk (batch) con raggruppamento
- Gestire il retry automatico/manuale dei pagamenti falliti
- Eseguire pagamenti via PISP (Open Banking) dove supportato
- **[MIGLIORAMENTO]** Generare file SEPA XML pain.001 per bonifici
- **[MIGLIORAMENTO]** Generare file RiBa per incassi
- **[MIGLIORAMENTO]** Gestire pagamenti F24 con tracciato dedicato
- Implementare workflow di approvazione con soglie importo

### 1.2 Tabelle DB coinvolte

| Tabella | Ruolo |
|---------|-------|
| `payment_orders` | Disposizioni di pagamento |
| `bank_accounts` | Conti di addebito |
| `counterparts` | Beneficiari |
| `invoice_payments` | Scadenze collegate ai pagamenti |
| `invoices` | Fatture collegate |
| `transactions` | Transazioni generate dai pagamenti |
| `bank_connections` | Consensi per PISP |
| `attachments` | Allegati ai pagamenti |
| `export_batches` | Batch di generazione file (pain.001, RiBa) |
| `audit_log` | Log operazioni |
| `notifications` | Notifiche stato pagamento |

---

## 2. Ciclo di Vita del Pagamento

### 2.1 State Machine

Basata su docs/08 (5 stati osservati) + stati aggiuntivi dal DB schema:

```mermaid
stateDiagram-v2
    [*] --> DRAFT: Creazione bozza
    DRAFT --> PENDING: Utente invia per approvazione
    DRAFT --> CANCELLED: Utente annulla bozza

    PENDING --> APPROVED: Approvatore autorizza
    PENDING --> DRAFT: Approvatore respinge (torna in bozza)
    PENDING --> CANCELLED: Utente annulla

    APPROVED --> ACCEPTED: Provider accetta la disposizione
    APPROVED --> FAILED: Errore invio al provider
    APPROVED --> CANCELLED: Utente annulla prima dell'invio

    ACCEPTED --> SUCCEEDED: Pagamento eseguito con successo
    ACCEPTED --> FAILED: Provider segnala errore
    ACCEPTED --> TIMEOUT: Nessuna risposta dal provider

    FAILED --> DRAFT: Retry (nuova bozza con dati copiati)
    TIMEOUT --> DRAFT: Retry (nuova bozza con dati copiati)

    SUCCEEDED --> [*]
    CANCELLED --> [*]

    note right of PENDING: Attesa approvazione<br/>(opzionale: bypass<br/>per importi sotto soglia)
    note right of ACCEPTED: In elaborazione<br/>dalla banca
    note right of SUCCEEDED: Genera transazione<br/>sul conto
```

### 2.2 Stati (da enum `payment_order_status`)

| Stato | Descrizione | Azioni possibili | Chi puo' agire |
|-------|-------------|-----------------|----------------|
| `DRAFT` | Bozza, non ancora inviata | Modifica, Invia, Annulla | Creatore, ADMIN |
| `PENDING` | In attesa di approvazione | Approva, Respingi, Annulla | Approvatore (ADMIN/OWNER) |
| `APPROVED` | Approvato, pronto per esecuzione | Esegui (automatico), Annulla | Sistema, ADMIN |
| `ACCEPTED` | Accettato dal provider/banca | Attendi esito | Sistema |
| `SUCCEEDED` | Eseguito con successo | Visualizza | Tutti |
| `FAILED` | Fallito | Retry, Visualizza errore | Creatore, ADMIN |
| `TIMEOUT` | Timeout senza risposta | Retry, Verifica manuale | Creatore, ADMIN |
| `CANCELLED` | Annullato | Visualizza | Tutti |

### 2.3 Transizioni di stato

```pseudocode
function transizioneStato(payment_id, new_status, user_id):
    payment = GET payment_orders WHERE id = payment_id
    old_status = payment.status

    // Validazione transizioni consentite
    allowed = {
        'DRAFT':     ['PENDING', 'CANCELLED'],
        'PENDING':   ['APPROVED', 'DRAFT', 'CANCELLED'],
        'APPROVED':  ['ACCEPTED', 'FAILED', 'CANCELLED'],
        'ACCEPTED':  ['SUCCEEDED', 'FAILED', 'TIMEOUT'],
        'FAILED':    ['DRAFT'],    // Retry
        'TIMEOUT':   ['DRAFT'],    // Retry
        'SUCCEEDED': [],           // Stato finale
        'CANCELLED': []            // Stato finale
    }

    IF new_status NOT IN allowed[old_status]:
        RAISE "Transizione non consentita: {old_status} -> {new_status}"

    // Esegui transizione
    payment.status = new_status
    payment.updated_at = NOW()

    // Side-effects per stato
    SWITCH new_status:
        CASE 'APPROVED':
            payment.approved_by = user_id
            payment.approved_at = NOW()
            // Se PISP disponibile, avvia esecuzione automatica
            IF payment.bank_account.bank_connection.purpose IN ('PISP', 'BOTH'):
                QUEUE eseguiPagamentoPISP(payment.id)

        CASE 'ACCEPTED':
            // Provider ha accettato, attendi conferma
            NOTIFY user PAYMENT_ACCEPTED (opzionale)

        CASE 'SUCCEEDED':
            payment.executed_at = NOW()
            // Genera transazione sul conto
            creaTransazioneDaPagamento(payment)
            // Aggiorna scadenze collegate
            aggiornaScadenzeCollegate(payment)
            NOTIFY user PAYMENT_SUCCEEDED

        CASE 'FAILED':
            payment.retry_count += 1
            payment.last_error = error_message
            NOTIFY user PAYMENT_FAILED

        CASE 'TIMEOUT':
            NOTIFY user PAYMENT_FAILED

        CASE 'CANCELLED':
            // Nessun side-effect specifico

    // Audit log
    INSERT INTO audit_log (
        action=CASE new_status
            WHEN 'APPROVED' THEN 'PAYMENT_APPROVE'
            WHEN 'SUCCEEDED' THEN 'PAYMENT_EXECUTE'
            WHEN 'CANCELLED' THEN 'PAYMENT_CANCEL'
            ELSE 'UPDATE',
        entity_type='payment_orders', entity_id=payment.id,
        user_id=user_id,
        old_values={status: old_status},
        new_values={status: new_status}
    )
```

---

## 3. Creazione Pagamento

### 3.1 Da scadenza (invoice_payment)

Il modo piu' comune: l'utente seleziona una scadenza e crea un pagamento per essa.

```pseudocode
function creaPagamentoDaScadenza(invoice_payment_id, bank_account_id, user_id):
    ip = GET invoice_payments WHERE id = invoice_payment_id
    invoice = GET invoices WHERE id = ip.invoice_id
    counterpart = GET counterparts WHERE id = invoice.counterpart_id

    payment = INSERT INTO payment_orders (
        company_id = ip.company_id,
        bank_account_id = bank_account_id,
        counterpart_id = counterpart.id,
        payment_type = determina_tipo_pagamento(ip, counterpart),
        amount = ip.amount - ip.paid_amount,  // Importo residuo
        currency = ip.currency,
        description = "Pagamento fattura {invoice.number}",
        reference = "Fatt. {invoice.number} del {invoice.creation_date}",
        beneficiary_name = counterpart.company_name,
        beneficiary_iban = counterpart.bank_identifier,
        beneficiary_bic = counterpart.bic,  // Se disponibile
        execution_date = ip.due_date,
        status = 'DRAFT',
        created_by = user_id
    )

    RETURN payment
```

### 3.2 Manuale

L'utente compila tutti i campi manualmente.

**Campi obbligatori** (da tabella `payment_orders`):

| Campo | Tipo DB | Vincoli | Note |
|-------|---------|---------|------|
| `company_id` | UUID FK | NOT NULL | Auto dal contesto |
| `bank_account_id` | UUID FK | NOT NULL | Conto di addebito |
| `payment_type` | `payment_order_type` | NOT NULL | Tipo pagamento |
| `amount` | NUMERIC(15,2) | NOT NULL, > 0 | Importo |
| `currency` | VARCHAR(3) | NOT NULL, DEFAULT 'EUR' | Valuta |
| `beneficiary_name` | VARCHAR(255) | NOT NULL per SEPA | Nome beneficiario |
| `beneficiary_iban` | VARCHAR(34) | NOT NULL per SEPA | IBAN beneficiario |
| `status` | `payment_order_status` | NOT NULL, DEFAULT 'DRAFT' | Stato iniziale |

**Campi opzionali:**

| Campo | Tipo DB | Note |
|-------|---------|------|
| `counterpart_id` | UUID FK | Controparte selezionata |
| `parent_id` | UUID FK | Pagamento padre (per bulk) |
| `description` | TEXT | Descrizione interna |
| `reference` | VARCHAR(140) | Causale SEPA (max 140 caratteri) |
| `beneficiary_bic` | VARCHAR(11) | BIC beneficiario |
| `execution_date` | DATE | Data esecuzione richiesta |
| `metadata` | JSONB | Dati extra (es. sezioni F24) |

### 3.3 Da fattura

Come "Da scadenza" ma con creazione automatica di una scadenza se la fattura non ne ha:

```pseudocode
function creaPagamentoDaFattura(invoice_id, bank_account_id, user_id):
    invoice = GET invoices WHERE id = invoice_id

    // Cerca scadenza non pagata
    ip = SELECT * FROM invoice_payments
         WHERE invoice_id = invoice_id
         AND payment_status IN ('UNPAID', 'PARTIALLY_PAID')
         ORDER BY due_date ASC
         LIMIT 1

    IF ip IS NULL:
        // Crea scadenza per l'importo lordo della fattura
        ip = INSERT INTO invoice_payments (
            company_id = invoice.company_id,
            invoice_id = invoice.id,
            due_date = invoice.creation_date + 30,  // Default 30 giorni
            amount = invoice.gross_amount,
            direction = CASE invoice.direction
                WHEN 'RECEIVED' THEN 'OUTFLOW'
                WHEN 'ISSUED' THEN 'INFLOW'
        )

    RETURN creaPagamentoDaScadenza(ip.id, bank_account_id, user_id)
```

---

## 4. Pagamenti Bulk

### 4.1 Creazione batch

L'utente seleziona piu' scadenze e genera un batch di pagamenti.

```pseudocode
function creaPagamentoBulk(invoice_payment_ids[], bank_account_id, user_id):
    // 1. Crea il pagamento padre (container)
    parent = INSERT INTO payment_orders (
        company_id,
        bank_account_id,
        payment_type = 'SEPA_CREDIT_TRANSFER',
        amount = SUM(scadenze.importi_residui),
        currency = 'EUR',
        description = "Pagamento bulk - {COUNT(invoice_payment_ids)} disposizioni",
        status = 'DRAFT',
        created_by = user_id
    )

    // 2. Crea i pagamenti figli
    FOR EACH ip_id IN invoice_payment_ids:
        child = creaPagamentoDaScadenza(ip_id, bank_account_id, user_id)
        child.parent_id = parent.id
        UPDATE payment_orders SET parent_id = parent.id WHERE id = child.id

    RETURN parent
```

### 4.2 Struttura gerarchica

Come osservato in Sibill (docs/08, LB-PAG-02):

```
payment_orders (parent - tipo SEPA_CREDIT_TRANSFER)
    ├── payment_orders (figlio 1 - Fatt. 123, EUR 1.000)
    ├── payment_orders (figlio 2 - Fatt. 456, EUR 2.500)
    └── payment_orders (figlio 3 - Fatt. 789, EUR 800)
```

Il parent aggrega l'importo totale. I figli contengono i dettagli dei singoli beneficiari. La transizione di stato del parent propaga ai figli.

---

## 5. Retry Pagamenti Falliti

### 5.1 Retry manuale

```pseudocode
function retryPagamento(payment_id, user_id):
    original = GET payment_orders WHERE id = payment_id

    IF original.status NOT IN ('FAILED', 'TIMEOUT'):
        RAISE "Solo pagamenti FAILED o TIMEOUT possono essere ripetuti"

    // Crea nuova bozza con dati copiati dall'originale
    new_payment = INSERT INTO payment_orders (
        ...copia tutti i campi da original...,
        status = 'DRAFT',
        retry_count = 0,
        last_error = NULL,
        executed_at = NULL,
        approved_by = NULL,
        approved_at = NULL,
        provider_payment_id = NULL,
        transaction_id = NULL,
        created_by = user_id,
        // Mantieni collegamento all'originale per tracciabilita'
        metadata = {retry_of: original.id, original_error: original.last_error}
    )

    // Audit log
    INSERT INTO audit_log (action='CREATE', description='Retry di pagamento fallito {original.id}')

    RETURN new_payment
```

### 5.2 Retry automatico (configurabile)

```pseudocode
// Job periodico per retry automatico
function jobRetryAutomatico():
    // Trova pagamenti FAILED con retry_count < max_retries
    failed = SELECT * FROM payment_orders
             WHERE status IN ('FAILED', 'TIMEOUT')
             AND retry_count < 3  // Max 3 tentativi
             AND updated_at < NOW() - INTERVAL '1 hour'  // Attendi 1h tra retry

    FOR EACH payment IN failed:
        // Re-invia al provider
        payment.status = 'APPROVED'
        payment.retry_count += 1
        QUEUE eseguiPagamentoPISP(payment.id)
```

---

## 6. [MIGLIORAMENTO] PISP + pain.001

Sibill esegue i pagamenti esclusivamente via PISP (API SWAN). Il gestionale supporta **entrambi** i canali: PISP per banche Open Banking e generazione file SEPA XML per banche tradizionali.

### 6.1 Esecuzione via PISP

```pseudocode
function eseguiPagamentoPISP(payment_id):
    payment = GET payment_orders WHERE id = payment_id
    connection = GET bank_connections
                 WHERE id = payment.bank_account.bank_connection_id
                 AND purpose IN ('PISP', 'BOTH')
                 AND status = 'AUTHORIZED'

    IF connection IS NULL:
        RAISE "Nessun consenso PISP attivo per questo conto"

    // Invia al provider Open Banking
    result = PROVIDER.initiate_payment({
        debtor_iban: payment.bank_account.iban,
        creditor_name: payment.beneficiary_name,
        creditor_iban: payment.beneficiary_iban,
        amount: payment.amount,
        currency: payment.currency,
        reference: payment.reference,
        execution_date: payment.execution_date
    })

    payment.provider_payment_id = result.payment_id
    payment.status = 'ACCEPTED'

    // Il provider inviera' webhook per SUCCEEDED o FAILED
```

### 6.2 Generazione file SEPA XML pain.001

Per banche non supportate da Open Banking, il sistema genera un file XML conforme allo standard ISO 20022 pain.001.001.03.

```pseudocode
function generaPain001(payment_ids[], company_id):
    payments = SELECT * FROM payment_orders
               WHERE id IN (payment_ids)
               AND payment_type = 'SEPA_CREDIT_TRANSFER'
               AND status = 'APPROVED'

    company = GET companies WHERE id = company_id

    // Struttura pain.001
    xml = {
        Document: {
            CstmrCdtTrfInitn: {
                // Group Header
                GrpHdr: {
                    MsgId: generate_unique_id(),         // ID univoco messaggio
                    CreDtTm: NOW().toISO8601(),          // Data/ora creazione
                    NbOfTxs: payments.count,             // Numero transazioni
                    CtrlSum: SUM(payments.amount),       // Somma controllo
                    InitgPty: {
                        Nm: company.name,                // Nome iniziatore
                        Id: { OrgId: { Othr: { Id: company.vat_number } } }
                    }
                },
                // Payment Information (uno per conto di addebito)
                PmtInf: payments.GROUP_BY(bank_account_id).MAP(group => {
                    PmtInfId: generate_unique_id(),
                    PmtMtd: "TRF",                      // Transfer
                    NbOfTxs: group.count,
                    CtrlSum: SUM(group.amount),
                    PmtTpInf: {
                        SvcLvl: { Cd: "SEPA" }           // SEPA Credit Transfer
                    },
                    ReqdExctnDt: group[0].execution_date, // Data esecuzione
                    Dbtr: {
                        Nm: company.name                  // Debitore
                    },
                    DbtrAcct: {
                        Id: { IBAN: group[0].bank_account.iban }
                    },
                    DbtrAgt: {
                        FinInstnId: { BIC: group[0].bank_account.bic }
                    },
                    // Credit Transfer Transaction Information
                    CdtTrfTxInf: group.MAP(payment => {
                        PmtId: {
                            EndToEndId: payment.id       // ID end-to-end
                        },
                        Amt: {
                            InstdAmt: { Ccy: payment.currency, value: payment.amount }
                        },
                        CdtrAgt: {
                            FinInstnId: { BIC: payment.beneficiary_bic }
                        },
                        Cdtr: {
                            Nm: payment.beneficiary_name  // Creditore
                        },
                        CdtrAcct: {
                            Id: { IBAN: payment.beneficiary_iban }
                        },
                        RmtInf: {
                            Ustrd: payment.reference      // Causale (max 140 char)
                        }
                    })
                })
            }
        }
    }

    // Salva file
    filename = "pain001_{company.vat_number}_{date}.xml"
    file_url = STORAGE.upload(xml.toXMLString(), filename)

    // Traccia export
    INSERT INTO export_batches (
        company_id, user_id, format='SEPA_PAIN_001',
        entity_type='payment_orders',
        status='COMPLETED',
        file_url=file_url,
        total_records=payments.count
    )

    // Aggiorna stato pagamenti
    UPDATE payment_orders SET status = 'ACCEPTED'
    WHERE id IN (payment_ids)

    RETURN file_url
```

### 6.3 Campi obbligatori pain.001

| Campo XML | Campo DB | Obbligatorio | Max length |
|-----------|----------|-------------|-----------|
| `MsgId` | Auto-generato | Si | 35 |
| `CreDtTm` | NOW() | Si | - |
| `NbOfTxs` | COUNT | Si | 15 |
| `CtrlSum` | SUM(amount) | Si | 18+2 dec |
| `InitgPty/Nm` | `companies.name` | Si | 70 |
| `PmtMtd` | "TRF" | Si | 3 |
| `ReqdExctnDt` | `execution_date` | Si | date |
| `Dbtr/Nm` | `companies.name` | Si | 70 |
| `DbtrAcct/IBAN` | `bank_accounts.iban` | Si | 34 |
| `EndToEndId` | `payment_orders.id` | Si | 35 |
| `InstdAmt` | `amount` + `currency` | Si | 18+2 dec |
| `Cdtr/Nm` | `beneficiary_name` | Si | 70 |
| `CdtrAcct/IBAN` | `beneficiary_iban` | Si | 34 |
| `RmtInf/Ustrd` | `reference` | No | 140 |

---

## 7. [MIGLIORAMENTO] Tracciato RiBa

Per la gestione degli incassi tramite Ricevuta Bancaria.

### 7.1 Struttura record RiBa

Il tracciato RiBa CBI e' composto da record a lunghezza fissa (120 caratteri):

| Record | Tipo | Descrizione |
|--------|------|-------------|
| **IB** | Header | Intestazione flusso |
| **14** | Testata | Dati mittente e codice SIA |
| **20** | Dati debitore | Nome, indirizzo, CAB/ABI |
| **30** | Dati banca | Banca domiciliataria |
| **40** | Dati aggiuntivi | Descrizione, riferimenti |
| **50** | Riferimento creditore | Dati del creditore |
| **51** | Importo | Importo e scadenza |
| **70** | Info aggiuntive | Note |
| **EF** | Coda | Totali di controllo |

### 7.2 Generazione file RiBa

```pseudocode
function generaFileRiBa(payment_ids[], company_id):
    payments = SELECT * FROM payment_orders
               WHERE id IN (payment_ids)
               AND payment_type = 'RIBA'
               AND status = 'APPROVED'

    company = GET companies WHERE id = company_id

    records = []
    records.APPEND(recordIB(company))  // Header

    FOR EACH payment IN payments:
        records.APPEND(record14(payment, company))  // Testata
        records.APPEND(record20(payment))            // Debitore
        records.APPEND(record30(payment))            // Banca
        records.APPEND(record40(payment))            // Aggiuntivi
        records.APPEND(record50(company))            // Creditore
        records.APPEND(record51(payment))            // Importo
        records.APPEND(record70(payment))            // Info

    records.APPEND(recordEF(payments))  // Coda

    filename = "riba_{company.vat_number}_{date}.txt"
    file_url = STORAGE.upload(records.JOIN("\n"), filename)

    INSERT INTO export_batches (
        company_id, format='CBI', entity_type='payment_orders',
        status='COMPLETED', file_url=file_url,
        total_records=payments.count
    )

    RETURN file_url
```

---

## 8. [MIGLIORAMENTO] F24

### 8.1 Gestione pagamento F24

Il pagamento F24 richiede dati specifici diversi da un bonifico SEPA.

```pseudocode
// Struttura metadata JSONB per F24
f24_metadata = {
    "tipo_f24": "ORDINARIO",  // ORDINARIO, SEMPLIFICATO, ACCISE
    "sezioni": [
        {
            "tipo": "ERARIO",
            "righe": [
                {
                    "codice_tributo": "6001",    // Versamento IVA gennaio
                    "anno_riferimento": "2026",
                    "importo_debito": 5000.00,
                    "importo_credito": 0
                }
            ]
        },
        {
            "tipo": "INPS",
            "righe": [
                {
                    "codice_sede": "1234",
                    "causale": "DM10",
                    "matricola": "1234567890",
                    "periodo_da": "01/2026",
                    "periodo_a": "01/2026",
                    "importo_debito": 3000.00
                }
            ]
        },
        {
            "tipo": "REGIONI",
            "righe": []
        },
        {
            "tipo": "IMU",
            "righe": []
        }
    ],
    "totale_debito": 8000.00,
    "totale_credito": 0,
    "saldo": 8000.00
}
```

### 8.2 Creazione pagamento F24

```pseudocode
function creaPagamentoF24(f24_data, bank_account_id, user_id):
    // Validazione
    IF f24_data.saldo <= 0:
        RAISE "Il saldo F24 deve essere positivo"

    payment = INSERT INTO payment_orders (
        company_id,
        bank_account_id,
        payment_type = 'F24',
        amount = f24_data.saldo,
        currency = 'EUR',
        description = "Pagamento F24 - {f24_data.tipo_f24}",
        execution_date = f24_data.data_versamento,
        status = 'DRAFT',
        metadata = f24_data,
        created_by = user_id
    )

    RETURN payment
```

---

## 9. Workflow Approvazione

### 9.1 Regole di approvazione

```pseudocode
function richiedeApprovazione(payment):
    // Regole di base (configurabili per azienda)
    config = GET company_settings(payment.company_id)

    // 1. Sotto soglia minima: nessuna approvazione necessaria
    IF payment.amount <= config.approval_threshold_low:  // es. EUR 500
        RETURN FALSE  // Bypass approvazione, va diretto in APPROVED

    // 2. Sopra soglia alta: doppia approvazione
    IF payment.amount >= config.approval_threshold_high:  // es. EUR 10.000
        RETURN 'DOUBLE_APPROVAL'

    // 3. Zona intermedia: singola approvazione
    RETURN 'SINGLE_APPROVAL'
```

### 9.2 Chi puo' approvare

| Ruolo | Puo' creare | Puo' approvare | Puo' eseguire |
|-------|-------------|---------------|---------------|
| VIEWER | No | No | No |
| EDITOR | Si (DRAFT) | No | No |
| ADMIN | Si | Si | Si |
| OWNER | Si | Si | Si |

### 9.3 Doppia approvazione

Per importi sopra la soglia alta:

```pseudocode
function approva(payment_id, user_id):
    payment = GET payment_orders WHERE id = payment_id
    user_role = GET user_companies WHERE user_id AND company_id

    IF user_role NOT IN ('ADMIN', 'OWNER'):
        RAISE "Permesso negato"

    IF payment.approved_by == user_id:
        RAISE "La seconda approvazione deve essere di un utente diverso"

    IF richiedeApprovazione(payment) == 'DOUBLE_APPROVAL':
        IF payment.approved_by IS NULL:
            // Prima approvazione
            payment.approved_by = user_id
            payment.approved_at = NOW()
            payment.metadata.first_approval = {user_id, timestamp: NOW()}
            // Resta in PENDING per seconda approvazione
        ELSE:
            // Seconda approvazione
            payment.metadata.second_approval = {user_id, timestamp: NOW()}
            payment.status = 'APPROVED'
    ELSE:
        // Singola approvazione
        payment.approved_by = user_id
        payment.approved_at = NOW()
        payment.status = 'APPROVED'
```

---

## 10. Notifiche

### 10.1 Notifiche automatiche

| Evento | Tipo notifica | Destinatari | Canali |
|--------|--------------|-------------|--------|
| Pagamento SUCCEEDED | `PAYMENT_SUCCEEDED` | Creatore + Admin | In-app, email |
| Pagamento FAILED | `PAYMENT_FAILED` | Creatore + Admin | In-app, email |
| Pagamento in TIMEOUT | `PAYMENT_FAILED` | Creatore + Admin | In-app, email |
| In attesa di approvazione | (custom) | Approvatori | In-app, email |
| Scadenza imminente | (custom) | Admin | In-app |

### 10.2 Polling TIMEOUT

Come osservato in Sibill (docs/08, LB-PAG-05), il frontend esegue polling per verificare pagamenti in TIMEOUT:

```pseudocode
// Chiamata ad ogni navigazione di pagina
function checkTimeoutPayments(company_id):
    result = GET /api/v1/payment-orders/metadata
             ?company_id=:company_id
             &status=TIMEOUT

    IF result.total > 0:
        // Mostra badge/notifica nell'UI
        showBadge("payments", result.total)
```

---

## 11. Side-Effects del Pagamento SUCCEEDED

```pseudocode
function onPaymentSucceeded(payment):
    // 1. Genera transazione sul conto
    tx = INSERT INTO transactions (
        company_id = payment.company_id,
        bank_account_id = payment.bank_account_id,
        amount = -payment.amount,  // Negativo = uscita
        currency = payment.currency,
        direction = 'OUTFLOW',
        transaction_date = DATE(payment.executed_at),
        description = payment.description,
        remittance_info = payment.reference,
        transaction_type = CASE payment.payment_type
            WHEN 'SEPA_CREDIT_TRANSFER' THEN 'CREDIT_TRANSFER'
            WHEN 'SEPA_DIRECT_DEBIT' THEN 'DIRECT_DEBIT'
            ELSE 'OTHER',
        counterpart_id = payment.counterpart_id,
        counterpart_name = payment.beneficiary_name,
        counterpart_iban = payment.beneficiary_iban,
        status = 'BOOKED',
        provider_transaction_id = payment.provider_payment_id
    )

    // 2. Collega la transazione al pagamento
    payment.transaction_id = tx.id

    // 3. Aggiorna saldo del conto
    account = GET bank_accounts WHERE id = payment.bank_account_id
    account.current_balance -= payment.amount
    account.available_balance -= payment.amount
    account.balance_date = NOW()

    // 4. Trigger riconciliazione automatica per la nuova transazione
    QUEUE riconciliazioneAutomatica(tx.id)

    // 5. Ricalcola cash flow
    ricalcolaCashFlow(payment.company_id, tx.transaction_date)
```

---

## 12. API Endpoints

| Metodo | Path | Descrizione | Parametri principali |
|--------|------|-------------|---------------------|
| `GET` | `/api/v1/payment-orders` | Lista pagamenti | company_id, status, payment_type, sort, include, page |
| `GET` | `/api/v1/payment-orders/:id` | Dettaglio pagamento | include=bankAccount,counterpart,attachments,transaction,parent,children |
| `POST` | `/api/v1/payment-orders` | Creazione pagamento | Body: bank_account_id, payment_type, amount, beneficiary_*, ... |
| `POST` | `/api/v1/payment-orders/bulk` | Creazione batch | Body: invoice_payment_ids[], bank_account_id |
| `PATCH` | `/api/v1/payment-orders/:id` | Modifica bozza | Body: campi modificabili (solo se DRAFT) |
| `POST` | `/api/v1/payment-orders/:id/submit` | Invia per approvazione | DRAFT -> PENDING (o APPROVED se bypass) |
| `POST` | `/api/v1/payment-orders/:id/approve` | Approva pagamento | PENDING -> APPROVED |
| `POST` | `/api/v1/payment-orders/:id/reject` | Respingi (torna bozza) | PENDING -> DRAFT, con motivo |
| `POST` | `/api/v1/payment-orders/:id/cancel` | Annulla pagamento | -> CANCELLED |
| `POST` | `/api/v1/payment-orders/:id/retry` | Retry pagamento fallito | FAILED/TIMEOUT -> nuova DRAFT |
| `POST` | `/api/v1/payment-orders/:id/execute` | Esegui via PISP | APPROVED -> ACCEPTED |
| `POST` | `/api/v1/payment-orders/validate-iban` | Validazione IBAN | Body: iban |
| `GET` | `/api/v1/payment-orders/metadata` | Conteggio per stato | company_id, status |
| `POST` | `/api/v1/payment-orders/export/pain001` | [MIGLIORAMENTO] Genera pain.001 | Body: payment_ids[] |
| `POST` | `/api/v1/payment-orders/export/riba` | [MIGLIORAMENTO] Genera RiBa | Body: payment_ids[] |

---

## 13. Functional Requirements

### FR-PAG-001: Creazione pagamento da scadenza

**Given** una scadenza OUTFLOW con `payment_status = UNPAID` e importo EUR 1.000
**When** l'utente seleziona la scadenza e clicca "Crea pagamento"
**Then** viene creato un `payment_orders` con `status = DRAFT`, `amount = 1000.00`, `payment_type = SEPA_CREDIT_TRANSFER`, i dati del beneficiario precompilati dalla controparte della fattura

### FR-PAG-002: Pagamento bulk da scadenze multiple

**Given** 5 scadenze OUTFLOW selezionate con importi diversi
**When** l'utente clicca "Paga selezionate"
**Then** viene creato un `payment_orders` padre con `amount = somma degli importi` e 5 `payment_orders` figli, ciascuno con `parent_id` impostato al padre

### FR-PAG-003: Workflow approvazione singola

**Given** un pagamento in DRAFT di EUR 2.000 (sotto soglia doppia approvazione)
**When** l'utente EDITOR invia il pagamento (submit)
**Then** lo status diventa PENDING; quando un utente ADMIN approva, lo status diventa APPROVED e l'esecuzione viene avviata

### FR-PAG-004: Workflow doppia approvazione

**Given** un pagamento in PENDING di EUR 50.000 (sopra soglia alta)
**When** un primo ADMIN approva il pagamento
**Then** il pagamento resta in PENDING con prima approvazione registrata; quando un secondo ADMIN (diverso dal primo) approva, lo status diventa APPROVED

### FR-PAG-005: Esecuzione via PISP

**Given** un pagamento APPROVED per un conto con consent PISP attivo
**When** il sistema avvia l'esecuzione
**Then** il pagamento viene inviato al provider Open Banking, lo status diventa ACCEPTED, al completamento diventa SUCCEEDED con transazione generata sul conto

### FR-PAG-006: Retry pagamento fallito

**Given** un pagamento con `status = FAILED` e `retry_count = 1`
**When** l'utente clicca "Riprova"
**Then** viene creata una nuova bozza con i dati copiati dall'originale, `metadata.retry_of` riferisce al pagamento originale, il pagamento originale resta in stato FAILED per storico

### FR-PAG-007: [MIGLIORAMENTO] Generazione pain.001

**Given** 3 pagamenti APPROVED di tipo SEPA_CREDIT_TRANSFER
**When** l'utente esporta come file SEPA
**Then** viene generato un file XML pain.001.001.03 conforme allo standard ISO 20022, con GroupHeader contenente NbOfTxs=3 e CtrlSum=somma importi, e 3 CdtTrfTxInf con i dettagli dei beneficiari; il file viene salvato in `export_batches`

### FR-PAG-008: Validazione IBAN beneficiario

**Given** un utente che compila l'IBAN del beneficiario
**When** inserisce "IT60X0542811101000000123456"
**Then** il sistema verifica: lunghezza 27 (per Italia), paese IT, check digit valido, ABI e CAB estratti, BIC derivato; se valido mostra conferma verde, se non valido mostra errore

### FR-PAG-009: Transazione generata da pagamento SUCCEEDED

**Given** un pagamento ACCEPTED che riceve conferma SUCCEEDED dal provider
**When** lo status diventa SUCCEEDED
**Then** viene creata una `transactions` con amount negativo (uscita), collegata al pagamento via `transaction_id`, il saldo del conto viene decrementato, il cash flow viene ricalcolato

### FR-PAG-010: Annullamento pagamento

**Given** un pagamento in stato DRAFT o PENDING
**When** l'utente annulla il pagamento
**Then** lo status diventa CANCELLED, nessuna transazione viene generata, le scadenze collegate non vengono modificate, viene creato un audit_log con action PAYMENT_CANCEL

### FR-PAG-011: Notifica pagamento TIMEOUT

**Given** un pagamento in stato ACCEPTED da piu' di X ore senza risposta
**When** il sistema lo marca come TIMEOUT
**Then** viene creata una notifica `PAYMENT_FAILED` per il creatore e gli admin, il frontend mostra un badge con il conteggio dei pagamenti in TIMEOUT

### FR-PAG-012: [MIGLIORAMENTO] Generazione RiBa

**Given** 2 pagamenti APPROVED di tipo RIBA con i dati dei debitori
**When** l'utente esporta come file RiBa
**Then** viene generato un file in formato CBI RiBa con header IB, record 14-70 per ogni disposizione, e coda EF con totali di controllo

### FR-PAG-013: [MIGLIORAMENTO] Pagamento F24

**Given** un utente che compila i dati F24 (sezione Erario con codice tributo 6001, importo EUR 5.000)
**When** crea il pagamento F24
**Then** viene creato un `payment_orders` con `payment_type = 'F24'`, `metadata` contenente le sezioni F24 compilate, `amount = saldo F24`

### FR-PAG-014: Bypass approvazione per importi sotto soglia

**Given** una configurazione aziendale con `approval_threshold_low = 500`
**When** un utente crea e invia un pagamento di EUR 200
**Then** il pagamento passa direttamente da DRAFT ad APPROVED, senza passare per PENDING

### FR-PAG-015: Causale SEPA con limite 140 caratteri

**Given** un utente che compila la causale di un bonifico SEPA
**When** inserisce un testo di 150 caratteri
**Then** il sistema mostra un errore di validazione indicando il limite di 140 caratteri (campo `reference` in `payment_orders`)
