# Fix Log — MVP Generation Pipeline

## Come usare questo file

Dopo ogni sessione di fix, aggiungi una voce con:
- Data e prompt eseguito
- Cosa è stato cambiato (file + descrizione breve)
- Risultato del test (✅ successo / ⚠️ parziale / ❌ fallito)
- Ipotesi aggiornate e prossima azione

---

## Sessioni di fix

### FIX-01 — 2026-04-21 — Bug critici bloccanti (generazione non completa)

**Commit:** da aggiungere dopo push  
**Branch:** `claude/fix-mvp-generation-wlmy6`

#### Modifiche apportate

| File | Modifica |
|------|----------|
| `AI_agents/graph/graph.py` | `route_after_integration_check()`: separato errori critici (design/backend/frontend) da non critici (backlog/publish). Prima qualsiasi errore bloccava il pipeline. |
| `AI_agents/graph/graph.py` | `get_app()`: rimosso `interrupt_before=["backend_agent"]` che fermava il graph dopo design senza mai riprendere. |
| `orchestrator-ui/backend/orchestrator.py` | `_map_event_to_step_info()`: riscritto — la presenza del node_name nell'evento è il segnale di completamento, non `"completed_steps"` nel data (che con stream_mode="updates" non è affidabile). |
| `orchestrator-ui/backend/orchestrator.py` | Loop di streaming: `final_state` ora viene aggiornato per qualsiasi node output, non solo quelli con chiave `"errors"`. |
| `orchestrator-ui/backend/orchestrator.py` | Check errori finale: usa stessa logica critico/non-critico del graph router. |
| `orchestrator-ui/backend/orchestrator.py` | `run_generation` + `_run_generation_internal`: introdotto `ctx` dict condiviso per esporre `project` e `generation_attempt` al wrapper di timeout. Prima erano sempre `None`/`1` nel wrapper, rendendo i log di errore da timeout inutili. |

#### Bug risolti in questa sessione
- **BUG A**: Error routing troppo aggressivo — backlog_agent fallito bloccava devops+publish
- **BUG C**: `interrupt_before` in `get_app()` senza resume handler — graph si fermava dopo design
- **BUG D**: `final_state` tracking parziale — veniva aggiornato solo su nodi con chiave `"errors"`
- **BUG E**: `_map_event_to_step_info()` restituiva sempre `None` — zero notifiche di progresso
- **BUG F**: `generation_attempt` disallineato — il wrapper di timeout usava sempre valore 1

#### Risultato test
⬜ Da testare (push non ancora avvenuto)

#### Ipotesi post-fix
Il pipeline dovrebbe ora terminare anche se backlog o publish falliscono.
I progress update via WebSocket dovrebbero arrivare al frontend.
Il resume dovrebbe loggare l'attempt corretto.

#### Prossima azione se FIX-01 non basta
→ Procedere con **FIX-02**: robustezza JSON nei backend/frontend agents (chunked generation o prompt ridotto)

---

## Bug noti non ancora affrontati

| ID | Descrizione | Priorità | Fix previsto |
|----|-------------|----------|--------------|
| BUG-B | JSON truncation/parse failure in backend_node e frontend_node per output troppo grandi | ALTA | FIX-02 |
| BUG-G | Race condition WebSocket: messaggi early droppati perché WS non ancora connessa | MEDIA | FIX-03 o FIX-05 |
| WS-1  | WebSocket problematico su Render free tier (proxy HTTP può killare la connessione) | MEDIA | FIX-05 (migrazione SSE) |

---

## Architettura attuale (quick reference)

```
POST /api/generation/start
  → run_generation (asyncio.wait_for, 30 min timeout)
    → _run_generation_internal
      → langgraph_app.astream(initial_state, stream_mode="updates")
        → knowledge_retrieval (stub)
        → design_node (Deep Agents)
        → [backend_node, frontend_node, backlog_node] in parallel (Send API)
        → integration_check (stub)
        → route_after_integration_check (CRITICAL errors only)
        → devops_node
        → publish_node
      → per ogni evento: persist artifacts + broadcast WebSocket progress
```

## Lezioni apprese

1. Con `stream_mode="updates"`, la presenza del `node_name` nell'evento è sufficiente a sapere che il nodo è completato. Non bisogna controllare campi interni.
2. `interrupt_before` richiede un handler di resume esplicito. Se non c'è, il graph si ferma silenziosamente.
3. Le variabili locali in `run_generation` (wrapper di timeout) non vengono mai popolate dalla coroutine interna — serve un oggetto mutable condiviso.
4. Qualsiasi agente non-critico che fallisce non deve bloccare devops/publish.
