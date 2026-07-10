---
title: "Agent Data Layer"
category: agent
tags:
  - agent
  - agent
  - data-layer
  - database
  - sqlite
related:
  - 05_agent_00_document-guide.md
---

# Agent Data Layer

Pattern for DB Access

`SQLiteHelper` (used everywhere in agent/RAG layers):

```python
with SQLiteHelper().open(write_mode=True, row_factory=True) as db:
    db.execute(...)
```

- `write_mode=True` → enables WAL mode + foreign keys
- `row_factory=True` → enables column name access (`row["column"]`)
- Opened per-query (not connection pool); DB_PATH and SQLITE_VEC_SO are lazily initialized

---

## FTS5 Index (`chu

nks_fts`)

The `chunks_fts` FTS5 virtual table in `rag.sqlite` is synchronized by triggers:
- `chunks_ai` (after INSERT): insert into `chunks_fts(COALESCE(normalized_content, content))`
- `chunks_au` (after UPDATE): delete + re-insert
- `chunks_ad` (after DELETE): delete from `chunks_fts`

`/db rag rebuild-fts` drops and recreates the FTS5 index from `chunks` data.
Use when `SELECT COUNT(*) FROM chunks_fts` ≠ `SELECT COUNT(*) FROM chunks`.

---

## Workflow SQLite 

(`workflow.sqlite`)

Managed by `agent/workflow/state_store.py`.

| Table | Contents |
|---|---|
| `tasks` | One row per turn attempt; status: `pending → running → [pending_approval →] completed \| halted \| failed` |
| `attempts` | Retry attempts within a task; status: `running \| completed \| failed` |
| `processed_events` | Idempotency enforcement; prevents duplicate stage execution |
| `approvals` | Approval gates; status: `pending → approved \| rejected` |
| `artifacts` | URIs produced by stage callbacks |

Used when `config/workflows/default.json` exists. Falls back to direct execution otherwise.

---

## Non-Message Pers

istence Boundaries

| Store | Role | Visible to LLM | Contents |
|---|---|---|---|
| `messages` | Conversation flow history (authoritative) | yes | Message sequence passed to LLM; large outputs stored as summaries only |
| `session_diagnostics` | Diagnostic-only events | no | LLM transport errors, guard hints; written by `DiagnosticStore.save()` |
| `workflow.artifacts` | Workflow artifact references | no | URIs produced by workflow stage callbacks; stored in `workflow.sqlite` |
| `audit.log` | Operational trace | no | JSON-lines audit events (`turn_start`, `turn_end`, MCP calls); see [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration_and_operations.md) |

Using `messages` for anything other than LLM-visible conversation flow is prohibited — diagnostic,
artifact, and audit data belong in the non-message stores above.

---

## Related Documents

- `agent`
- `data-layer`
- `database`

## Keywords

agent
data-layer
database
sqlite
