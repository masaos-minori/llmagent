## Title

Unused DTOs for RAG-003/RAG-004

### Context

Claim that DTOs exist for RAG-003/RAG-004 but are unused.

### Decision

**NOT FOUND.** No RAG-related DTOs exist in the codebase.

### Rationale

Searched for DTO patterns across the repo. Found three DTO files (`commands/models.py`, `memory/models.py`, `shared/models.py`) but none contain RAG-related types.

### Evidence

- `rg -n "RAG.*DTO\|dto.*rag" scripts/ tests/` returned no results
- Three DTO files found but none reference RAG:
  - `scripts/agent/commands/models.py` — slash-command handlers
  - `scripts/agent/memory/models.py` — memory layer
  - `scripts/agent/shared/models.py` — cross-cutting types

### Follow-up Actions

None required. The claim appears incorrect or refers to a different scope.
