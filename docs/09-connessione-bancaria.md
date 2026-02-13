# Connessione Bancaria — Analisi Funzionale

**Data analisi:** 10 febbraio 2026
**Modulo:** Connessione Bancaria e Gestione Conti
**URL principale:** `/accounts`
**URL carte:** `/accounts/cards` (dedotto dalla navigazione)

---

## Panoramica

Il modulo Connessione Bancaria gestisce il collegamento tra Sibill e i conti bancari dell'azienda tramite **Open Banking (PSD2)**. Attraverso questo modulo l'utente autorizza Sibill ad accedere ai dati del conto (AISP) e potenzialmente a disporre pagamenti (PISP).

Il modulo gestisce:
- **Conti bancari** — Lista, saldi, dettagli dei conti collegati
- **Consensi Open Banking** — Autorizzazioni per l'accesso ai dati bancari
- **Istituzioni** — Catalogo delle banche supportate
- **Carte** — Carte di pagamento associate (sezione dedicata)
- **Sincronizzazione** — Importazione automatica dei movimenti

---

## Interfaccia

### Layout Principale

La pagina `/accounts` presenta:

1. **Barra dei saldi aggregati** (in alto)
   - Tab con 3 saldi:
     - Saldo totale (contabile): 12.093,43 EUR 🟢
     - Saldo disponibile: 10.190,17 EUR 🟢
     - Differenza: 1.903,26 EUR 🟢

2. **Tabella conti** — Lista dei conti collegati con:
   - Nome/nickname del conto
   - IBAN
   - Saldo contabile e disponibile
   - Stato della connessione
   - Data ultimo aggiornamento
   - Istituto bancario (logo e nome)

3. **Azioni** — Gestione conti (connetti, disconnetti, nascondi, modifica saldo)

### 🎨 PATTERN UI/UX — Saldi Multi-Tab

I saldi sono presentati con un pattern a tab nella parte superiore:
- **Saldo contabile** (current balance) — Saldo comprensivo di operazioni in attesa
- **Saldo disponibile** (available balance) — Saldo effettivamente utilizzabile
- **Differenza** — current - available (operazioni in attesa)

La differenza (1.903,26 EUR nell'account di test) rappresenta probabilmente bonifici in uscita gia' contabilizzati ma non ancora addebitati.

---

## Entita' e Dati

### Entita' Coinvolte

| Entita' | Ruolo nel Modulo | Rif. Data Model |
|---|---|---|
| `account` | Conto bancario collegato | §2.4 |
| `consent` | Consenso Open Banking | §2.5 |
| `institution` | Istituto bancario | §2.6 |
| `card` | Carta di pagamento | §3.6 |
| `user-bank-account` | Associazione utente-conto | §3.8 |

### Dettaglio Account (Conto Bancario)

Confidenza: 🟢 Alta

| Campo | Tipo | Descrizione |
|---|---|---|
| `nickname` | string | Nome del conto (spesso l'IBAN) |
| `currency` | string | Valuta (EUR) |
| `currentBalance` | dict `{currency, amount}` | Saldo contabile |
| `currentBalanceEur` | float | Saldo contabile in EUR |
| `availableBalance` | dict `{currency, amount}` | Saldo disponibile |
| `availableBalanceEur` | float | Saldo disponibile in EUR |
| `balanceDate` | datetime | Data ultimo aggiornamento saldo |
| `status` | string | Stato conto (es. "ACTIVE") |
| `identifiers` | list `[{type, value}]` | IBAN, BIC, etc. |
| `allowBalanceChange` | boolean | Permette modifica manuale saldo |
| `ignoreBalance` | boolean | Escludi da saldi aggregati |
| `creditLimit` | null/dict | Fido bancario |
| `creditLimitEur` | null/float | Fido in EUR |
| `hiddenAt` | null/datetime | Data nascondimento |
| `cashbackAgreedAt` | null/datetime | Accettazione cashback |
| `lastUpdatedAt` | datetime | Ultima sincronizzazione |

### Conti Osservati nell'Account di Test

| # | IBAN (parziale) | Tipo | Saldo Contabile | Saldo Disponibile |
|---|---|---|---|---|
| 1 | ...07084 64990 000000751821 | Conto corrente | ~ | ~ |
| 2 | ...07084 64990 000000982285 | Conto corrente | ~ | ~ |

**Totale:** 2 conti attivi, entrambi presso lo stesso istituto. 🟢

### Dettaglio Consent (Consenso Open Banking)

Confidenza: 🟢 Alta

| Campo | Tipo | Descrizione |
|---|---|---|
| `status` | string | AUTHORIZED, DISABLED, etc. |
| `purpose` | string | Scopo del consenso |
| `sourceId` | string | ID sorgente dal provider |
| `authorizedAt` | datetime | Data autorizzazione |
| `firstSyncAt` | datetime | Prima sincronizzazione |
| `lastRunAt` | datetime | Ultima esecuzione sync |
| `redirectUrl` | null/string | URL di redirect OAuth |
| `debug` | boolean | Flag debug |
| `userData` | list | Dati utente dal provider |
| `userInfo` | null/dict | Info utente aggiuntive |

### Dettaglio Institution (Istituto Bancario)

Confidenza: 🟢 Alta

| Campo | Tipo | Descrizione |
|---|---|---|
| `name` | string | Nome istituto (es. "Conto Sibill") |
| `fullName` | null/string | Nome completo |
| `source` | string | Provider Open Banking (es. "SWAN") |
| `types` | list | Tipi (es. ["BANKING"]) |
| `flags` | list | Flag operativi (5 osservati) |
| `hidden` | boolean | Nascosto dal catalogo |
| `iconUrl` | string | URL icona |
| `logoUrl` | string | URL logo |

---

## Logiche di Business

### LB-CB-01: Provider Open Banking — SWAN

Confidenza: 🟢 Alta

Sibill utilizza **SWAN** come provider Open Banking per la connessione ai conti bancari. Dalle API traces:
```
GET /api/v1/institutions?filter[source__eq]=SWAN&filter[types__contains]=BANKING
```

SWAN e' un provider europeo di Banking-as-a-Service che offre:
- Accesso AISP (Account Information Service Provider)
- Servizi PISP (Payment Initiation Service Provider)
- Conto proprio "Conto Sibill" (visibile nel catalogo istituzioni)

### LB-CB-02: Flusso di Connessione (Consent Flow)

Confidenza: 🟢 Alta (struttura) / 🟡 Media (dettagli)

```
Flusso di connessione bancaria:

1. L'utente sceglie l'istituto bancario dal catalogo
   → GET /api/v1/institutions

2. Il sistema crea un consent con redirect URL
   → POST /api/v1/consents (non catturato)

3. L'utente viene reindirizzato alla pagina della banca (OAuth2)
   → consent.redirectUrl = URL della banca

4. L'utente autorizza l'accesso nella pagina della banca
   → Redirect back a Sibill con token di autorizzazione

5. Il consent viene aggiornato a AUTHORIZED
   → consent.status = "AUTHORIZED"

6. Prima sincronizzazione dei dati
   → consent.firstSyncAt = timestamp
   → I conti bancari vengono creati/aggiornati
```

### LB-CB-03: Consent per Cassetto Fiscale (SDI)

Confidenza: 🟢 Alta

Oltre ai consensi bancari, esiste un consent specifico per il **Cassetto Fiscale / SDI** (fatturazione elettronica):

```
Wizard a 3 step:
  Step 1: Informazioni sul servizio
  Step 2: Checkbox di conferma utente (obbligatoria)
  Step 3: Conferma e autorizzazione

Validazione:
  - Pulsante conferma disabilitato finche':
    - step != 2
    - checkbox non selezionata
    - operazione back in corso
```

### LB-CB-04: Calcolo Saldi Aggregati

Confidenza: 🟢 Alta

```
GET /api/v1/accounts/metadata
  filter[company.id__eq]=UUID
  filter[ignoreBalance__eq]=false        ← Esclude conti con ignoreBalance=true
  filter[consent.status__neq]=DISABLED   ← Esclude conti con consent disabilitato

Risposta:
  balances_converted:
    count: 2                              ← Numero conti inclusi
    available: {currency: "EUR", amount: "10190.17"}  ← Saldo disponibile aggregato
    current: {currency: "EUR", amount: "12093.43"}    ← Saldo contabile aggregato
```

📐 **FORMULA:**
```
Saldo contabile aggregato = somma(account.currentBalanceEur)
                            per tutti i conti dove:
                            - ignoreBalance == false
                            - consent.status != DISABLED

Saldo disponibile aggregato = somma(account.availableBalanceEur)
                              con stessi filtri

Differenza = Saldo contabile - Saldo disponibile
```

### LB-CB-05: Gestione Multi-Conto

Confidenza: 🟢 Alta

Il sistema supporta **multi-conto** e **multi-banca**:
- Un'azienda puo' avere piu' conti presso la stessa banca
- Un'azienda puo' avere conti presso banche diverse
- Ogni conto e' collegato a un consent specifico
- Un consent puo' avere piu' conti (has_many accounts)
- I conti possono essere nascosti (`hiddenAt`) senza essere eliminati
- I conti possono essere esclusi dai saldi aggregati (`ignoreBalance=true`)

### LB-CB-06: Modifica Manuale Saldo

Confidenza: 🟢 Alta

Il flag `allowBalanceChange` indica se l'utente puo' modificare manualmente il saldo del conto. Questo e' utile per:
- Conti non collegati tramite Open Banking (importazione manuale)
- Correzioni temporanee in caso di ritardo nella sincronizzazione

### LB-CB-07: Fido Bancario

Confidenza: 🟢 Alta (struttura dati) / 🟡 Media (comportamento)

I conti supportano un campo `creditLimit` (fido bancario) che, se presente, potrebbe influenzare il calcolo del saldo disponibile effettivo:

```
Saldo disponibile effettivo = availableBalance + creditLimit (se presente)
```

### LB-CB-08: Frequenza Sincronizzazione

Confidenza: 🟡 Media

Dalla struttura del consent:
- `lastRunAt` — Indica l'ultima volta che il sistema ha sincronizzato i dati
- `firstSyncAt` — Indica quando e' avvenuta la prima sincronizzazione
- Il polling del consent (211 chiamate in sessione) suggerisce verifiche frequenti

La sincronizzazione e' probabilmente:
- **Automatica** — A intervalli regolari (probabilmente ogni 4-6 ore, standard PSD2)
- **Su richiesta** — L'utente puo' forzare un aggiornamento

### LB-CB-09: User-Bank-Account (Permessi)

Confidenza: 🟡 Media

L'entita' `user-bank-account` gestisce l'associazione tra utenti e conti bancari:
```
GET /api/v1/user-bank-accounts
  filter[bankAccount.company.id__eq]=UUID
  filter[source__eq]=...
  filter[status__in]=...
  filter[user.id__eq]=UUID
```

Questo suggerisce un sistema di **permessi per conto**: non tutti gli utenti di un'azienda possono vedere/operare su tutti i conti. 🟡

---

## API Coinvolte

| Endpoint | Metodo | Scopo | Occorrenze | Rif. API |
|---|---|---|---|---|
| `/api/v1/accounts` | GET | Lista conti bancari | 27 | §3 |
| `/api/v1/accounts/metadata` | GET | Saldi aggregati | 3 | §3 |
| `/api/v1/consents` | GET | Lista consensi Open Banking | 211 | §3 |
| `/api/v1/institutions` | GET | Catalogo banche supportate | 1 | §3 |
| `/api/v1/user-bank-accounts` | GET | Associazione utente-conto | 56 | §3 |
| `/api/v1/cards` | GET | Lista carte | 2 | §3 |

> 🔵 **NOTA**: L'endpoint `/api/v1/consents` ha il piu' alto numero di occorrenze (211) tra tutti gli endpoint osservati. Viene chiamato ad ogni navigazione di pagina per verificare lo stato dei consensi bancari. Questo e' fondamentale perche' i consensi PSD2 hanno una scadenza (tipicamente 90 giorni) e devono essere rinnovati.

---

## Filtri e Ricerca

| Filtro | Tipo | Descrizione | Confidenza |
|---|---|---|---|
| Company | UUID | Filtra per azienda (obbligatorio) | 🟢 Alta |
| Status consent | NotIn | Esclude consent con stato specifico | 🟢 Alta |
| Ignore balance | Boolean | Esclude conti ignorati dai saldi | 🟢 Alta |
| Tipo istituzione | Contains | Filtra per tipo (es. BANKING) | 🟢 Alta |
| Source | Eq | Filtra per provider (es. SWAN) | 🟢 Alta |
| Hidden | Empty | Filtra conti nascosti/visibili | 🟢 Alta |

---

## Azioni Disponibili

| Azione | Descrizione | Tipo | Confidenza |
|---|---|---|---|
| **Visualizza conti** | Lista conti con saldi | Read | 🟢 Alta |
| **Connetti banca** | Avvia flusso di connessione Open Banking | Create | 🟢 Alta |
| **Connetti Cassetto Fiscale** | Avvia consent per SDI | Create | 🟢 Alta |
| **Nascondi conto** | Nasconde un conto dalla vista (senza disconnettere) | Update | 🟢 Alta |
| **Ignora saldo** | Esclude un conto dai saldi aggregati | Update | 🟢 Alta |
| **Modifica saldo** | Modifica manuale del saldo (se `allowBalanceChange=true`) | Update | 🟢 Alta |
| **Visualizza carte** | Lista carte associate | Read | 🟡 Media |
| **Rinnova consenso** | Rinnova un consent scaduto | Update | 🟡 Media |
| **Disconnetti** | Revoca il consent bancario | Delete | 🟡 Media |

---

## Limitazioni Osservate

1. **Carte vuote:** Nessuna carta presente nell'account di test (`has_created_card: false`). L'entita' `card` non e' stata analizzata in dettaglio. 🟢

2. **Provider unico:** Solo SWAN e' stato osservato come provider Open Banking. Non e' chiaro se Sibill supporti altri provider (Tink, Plaid, etc.) o se SWAN sia l'unico. 🟡

3. **Endpoint di scrittura non catturati:** La creazione di consent e la connessione di nuovi conti non sono state eseguite durante l'analisi. 🟡

4. **Frequenza sync non confermata:** La frequenza esatta della sincronizzazione automatica non e' stata determinata. Lo standard PSD2 prevede un massimo di 4 richieste al giorno, ma il provider SWAN potrebbe avere limiti diversi. 🟡

5. **Scadenza consent:** Il periodo di validita' dei consent non e' stato osservato. Lo standard PSD2 prevede 90 giorni, dopo i quali l'utente deve ri-autorizzare. 🟡

---

## Note

- La connessione bancaria e' il fondamento di tutte le altre funzionalita' di Sibill. Senza conti collegati, il cashflow e i movimenti non hanno dati.
- L'alto numero di chiamate al consent (211) suggerisce che Sibill monitora attentamente lo stato dei consensi. Un consent scaduto o revocato impedirebbe l'importazione dei nuovi movimenti.
- SWAN come provider Open Banking e' una scelta strategica: offre sia AISP che PISP, permettendo sia la lettura dei movimenti che l'iniziazione di pagamenti tramite la stessa infrastruttura.
- Il "Conto Sibill" nel catalogo istituzioni suggerisce che Sibill offre anche un conto proprio tramite SWAN (Banking-as-a-Service), non solo l'accesso a conti di terze parti.
- La gestione dei permessi per conto (`user-bank-account`) e' fondamentale per aziende con piu' utenti che devono avere accesso solo a specifici conti.
