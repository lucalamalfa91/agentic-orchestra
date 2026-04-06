---
paths: ["orchestrator-ui/frontend/**"]
---
# Frontend Development Rules

- Reuse existing Tailwind classes and component patterns — do not invent new ones
- New screen → create in `src/screens/{ScreenName}/` with index.tsx
- New API call → add to the appropriate hook in `src/hooks/`
- TypeScript: strict types mandatory, no `any`
- Do not add new npm dependencies without checking if existing ones cover the need
- All API base URL must use the existing API client, not raw fetch()
