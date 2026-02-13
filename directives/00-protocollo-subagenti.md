# Protocollo di Pianificazione ed Esecuzione via Subagenti

## Principio

Ogni piano complesso DEVE essere strutturato come una lista di **task indipendenti**, ciascuno eseguibile da un subagente con contesto fresco. L'agente principale (tu) diventa un puro **orchestratore**: dispatcha task, raccoglie risultati, gestisce errori.

**Perché:** la finestra di contesto si satura durante l'esecuzione di piani complessi (context rot). Delegando a subagenti:
- Ogni task gira con **contesto fresco** → qualità costante
- Task indipendenti girano in **parallelo** → velocità
- Ogni task è **isolato** → un fallimento non corrompe gli altri
- Risultati salvati su **filesystem** → tracciabilità e riproducibilità

## Struttura obbligatoria di ogni task nel piano

Ogni task del piano DEVE avere questi 7 campi:

| Campo | Descrizione | Esempio |
|-------|-------------|---------|
| **ID** | Identificativo progressivo | `T1`, `T2`, `T3` |
| **Obiettivo** | Cosa deve fare il task (1-2 frasi) | "Estrarre tutti i file JS caricati dalla pagina principale e salvarli" |
| **Tipo subagente** | `general-purpose` \| `Explore` \| `Bash` | `general-purpose` |
| **Input** | Path esatti dei file necessari al subagente | `credenziali.env`, `directives/01-ricognizione.md` |
| **Output atteso** | Path esatti dei file da produrre o info da riportare | `assets/js-sources/*.js`, `.tmp/js-file-list.md` |
| **Contesto** | Snippet rilevanti, decisioni prese, vincoli specifici per il task | "La webapp è una SPA moderna, il login è a app.sibill.com" |
| **Vincoli** | Limitazioni del task | "Non mostrare credenziali in output", "Max 5 min timeout" |

## Regole di decomposizione

**Raggruppamento:** operazioni sequenziali inscindibili vanno in UN singolo task.
- Esempio: login → naviga alla pagina → estrai dati → salva = 1 task (perché la sessione deve essere mantenuta)

**Indipendenza:** se due task possono girare in parallelo senza dipendenze I/O → task separati.
- Esempio: "analizza JS file A" e "analizza JS file B" = 2 task paralleli

**Filesystem come bus di comunicazione:** i task comunicano tramite file su disco.
- Output di T1 salvato in `.tmp/t1-output.json`
- T3 che dipende da T1 legge `.tmp/t1-output.json` come input
- Usa `.tmp/` per intermedi, `docs/` per deliverable

**Granularità:** ogni task deve essere completabile in una singola sessione di subagente (indicativamente 5-15 tool calls). Se un task è troppo grande, scomponilo ulteriormente.

## Livello di contesto per i subagenti (Moderato)

**Includere nel prompt del subagente:**
- Obiettivo chiaro e specifico
- Contesto rilevante (estratti da docs, path chiave, decisioni architetturali)
- Vincoli espliciti
- Path di input e output

**NON includere:**
- L'intero contesto della sessione
- La storia delle conversazioni precedenti
- Task non correlati

Il subagente ha accesso a CLAUDE.md e alle direttive in `directives/` — può leggerli autonomamente se necessario. Non duplicare informazioni già presenti lì.

## Protocollo di esecuzione per l'orchestratore

Quando esegui un piano approvato:

1. **Leggi il piano** e identifica il grafo delle dipendenze tra task
2. **Lancia task indipendenti in parallelo** (max 3-5 contemporanei)
3. **Attendi i risultati** — non procedere finché i task in corso non completano
4. **Per task con dipendenze I/O:** lancia solo dopo che l'output del task predecessore è disponibile su disco
5. **Raccogli risultati** e produci un riepilogo conciso per l'utente
6. **Se un task fallisce:** analizza l'errore, correggi il prompt o gli input, rilancia. Se fallisce 2 volte, segnala all'utente

**Regola critica:** l'orchestratore NON esegue lavoro operativo. Non legge file di progetto, non naviga pagine, non analizza codice. Fa solo: dispatch, monitoraggio, raccolta risultati, riepilogo.

## Template del prompt per subagente

```
## Obiettivo
[1-2 frasi: cosa deve fare questo task]

## Contesto
[Informazioni rilevanti: architettura, decisioni prese, stato attuale]
[Riferimenti: "Leggi directives/04-logica-riconciliazione.md per le istruzioni dettagliate"]

## Input
[Lista di path esatti dei file da leggere]

## Output atteso
[Path esatti dei file da produrre O informazioni da riportare nel risultato]

## Vincoli
[Limitazioni specifiche: timeout, credenziali da non mostrare, formato output, ecc.]
```
