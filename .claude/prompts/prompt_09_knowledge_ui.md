# Prompt 09 — Knowledge Sources UI

You are working on `lucalamalfa91/agentic-orchestra` (React + TypeScript).
Check `.claude/context/migration_status.md` before starting.

## Task: Add Knowledge Sources management screen

Users configure here what context the Knowledge Agent uses.
All source types are supported: web URL, file upload, API endpoint.

## Files to create

### `orchestrator-ui/frontend/src/screens/KnowledgeSources/types.ts`
TypeScript types:
- `KnowledgeSourceType`: `"web" | "file" | "api"`
- `KnowledgeSource`: id, name, source_type, last_indexed_at, status
- `WebSourceConfig`: url, selectors?, crawl_depth, max_pages
- `FileSourceConfig`: file_names (after upload)
- `ApiSourceConfig`: endpoint_url, auth_header, auth_value

### `orchestrator-ui/frontend/src/screens/KnowledgeSources/useKnowledgeSources.ts`
Custom hook:
- `useSources()` — fetches `GET /api/knowledge/sources`, returns list + loading
- `useAddSource()` — calls `POST /api/knowledge/sources`
- `useDeleteSource()` — calls `DELETE /api/knowledge/sources/{id}`
- `useIndexSource()` — calls `POST /api/knowledge/index/{id}`,
  then polls `GET /api/knowledge/index/{id}/status` every 2s until done

### `orchestrator-ui/frontend/src/screens/KnowledgeSources/KnowledgeSourceCard.tsx`
Card component showing:
- Source name + type badge (Web / File / API)
- Last indexed date (or "Never indexed")
- Status indicator: idle / indexing (spinner) / error
- "Re-index" button → triggers `useIndexSource`
- "Delete" button with confirmation dialog

### `orchestrator-ui/frontend/src/screens/KnowledgeSources/AddSourceModal.tsx`
Modal with:
- Source type selector (Web URL / Local Files / API Endpoint)
- Dynamic form based on type:
  - **Web**: URL input, crawl depth slider (1–5), max pages input,
    optional CSS selector for content
  - **File**: drag-and-drop upload (.pdf .md .txt .docx),
    shows file list before submitting
  - **API**: endpoint URL, auth header name + value
    (note in UI: "stored encrypted")
- "Save & Index" button → save then trigger indexing
- "Save only" button → save without indexing now

### `orchestrator-ui/frontend/src/screens/KnowledgeSources/KnowledgeSourcesScreen.tsx`
Main screen:
- Header: "Knowledge Sources" + "Add Source" button
- Grid of `KnowledgeSourceCard` components
- Empty state: "No sources yet — add one to give agents context"
  with Add Source button

### Integration
- Add "Knowledge" entry to existing sidebar/nav
- On the MVP creation screen, show:
  "Context sources active: N" with link to knowledge sources screen
  (if N = 0, show a subtle warning that no context is configured)

Reuse existing Tailwind classes and component patterns.
Do NOT invent new design tokens or styles.
Write complete TypeScript + React code for all files.
When done, update `.claude/context/migration_status.md` marking Prompt 09 complete.
