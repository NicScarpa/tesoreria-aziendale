# Edge Cases e Criteri di Qualità

## Edge Cases e situazioni da gestire

Durante il reverse engineering, gestisci questi scenari:

- **Sessione scaduta durante raccolta dati**: ri-autenticati automaticamente usando le credenziali da `credenziali.env`, riprendi da dove eri.
- **Rate limiting API**: se le richieste vengono limitate, riduci la frequenza. Documenta i limiti osservati nella direttiva corrispondente.
- **Contenuto caricato dinamicamente (lazy loading, infinite scroll)**: scrolla fino a caricare tutto prima di catturare. Verifica con il network monitor che non ci siano ulteriori chiamate pendenti.
- **Feature gated/nascoste**: cerca nel JavaScript riferimenti a funzionalità non visibili nell'UI (feature flag, controlli su ruoli utente, menu condizionali). Documentale anche se non accessibili.
- **Websocket/SSE**: se Sibill usa comunicazione real-time (notifiche, aggiornamenti live), documentala separatamente — endpoint, formato messaggi, eventi.
- **Paginazione API**: segui TUTTE le pagine per avere dataset completi. Non fermarti alla prima pagina.
- **Multi-tenant/multi-company**: documenta come l'app gestisce il contesto aziendale (header custom, URL parametrizzato, parametro in query string, cookie).
- **Errori di rete intermittenti**: se una chiamata fallisce, ritenta una volta. Se fallisce di nuovo, logga l'errore e prosegui con le altre sezioni.

## Criteri di qualità — Verifica completezza

Prima di considerare completata ogni fase, verifica:

1. **Copertura**: ogni sezione/pagina dell'app è stata visitata e documentata?
2. **Profondità API**: per ogni azione UI, la chiamata API corrispondente è catturata con request E response completi?
3. **Riproducibilità**: un analista che NON ha accesso a Sibill potrebbe ricostruire le funzionalità dalla sola documentazione?
4. **UI/UX**: per ogni pagina, i pattern di design, layout e interazione sono documentati in modo sufficientemente dettagliato da essere replicati nel gestionale?
5. **Confidenza**: ogni affermazione sulla logica di business ha un livello di confidenza assegnato?
6. **Formati bancari**: tutti i formati di import/export sono stati scaricati e documentati con schema e campi?
7. **Offline-ready**: i materiali raccolti (screenshot, API traces, JS, report) sono sufficienti per continuare l'analisi senza accesso a Sibill?
