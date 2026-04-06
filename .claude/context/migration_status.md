# Migration Status — Last updated: 2026-04-06

## Completed steps
- [ ] Prompt 01 — Analysis
- [ ] Prompt 02 — LangGraph state schema
- [ ] Prompt 03 — LangGraph graph + parallelismo
- [ ] Prompt 04 — Knowledge Agent (RAG generico)
- [ ] Prompt 05 — MCP Servers
- [ ] Prompt 06 — Backend FastAPI integration
- [ ] Prompt 07 — Agent nodes reali (design + altri)
- [ ] Prompt 08 — Checkpoint + human-in-the-loop
- [ ] Prompt 09 — UI Knowledge Sources
- [ ] Prompt 10 — Testing

## Current step
**Prompt 01 — Analysis**
Working on: nessun file ancora, solo analisi
Blocker: nessuno

## Decisions made
- LangGraph invece di CrewAI: controllo deterministico del flusso
- pgvector invece di Qdrant: già presente Postgres, riduce infra
- MCP servers come processi separati su porte 8001-8003
- Multilingual embeddings: paraphrase-multilingual-mpnet-base-v2
- interrupt_before=["backend_agent"] per human-in-the-loop sul design

## Files created by this migration
(nessuno ancora)

## Next action
Eseguire Prompt 01: leggere il repo e produrre l'analisi del flusso
attuale prima di scrivere codice.
