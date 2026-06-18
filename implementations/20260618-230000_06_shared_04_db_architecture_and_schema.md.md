# Implementation: MemoryDeleteStore Protocol — DB Architecture Doc

## Goal

Update `docs/06_shared_04_db_architecture_and_schema.md` §2 to show three-file split (`store_protocols.py`, `store_impl.py`, `store.py`).

## Scope

- `docs/06_shared_04_db_architecture_and_schema.md` — update directory listing in §2

## Assumptions

1. The three-file layout is stable and final (confirmed by reading `scripts/db/store.py` which is a re-export stub).
2. No code changes needed — this is documentation-only.

## Current State

### §2 Directory listing (`06_shared_04:16-23`)

```markdown
db/
├── helper.py          SQLiteHelper — connection lifecycle, PRAGMA, vec extension
├── create_schema.py   DDL creation (rag + session schemas; idempotent)
├── store.py           Protocol definitions + SQLite implementations
├── maintenance.py     WAL checkpoint, VACUUM, purge, rotate, recover
├── tool_results.py    ToolResultStore — full tool result storage
└── workflow_schema.py workflow.sqlite DDL initialization
```

**Gap:** Shows single `store.py` with "Protocol definitions + SQLite implementations" — does not reflect actual three-file split.

### Actual files (`scripts/db/`)

| File | Content |
|---|---|
| `store_protocols.py` | `VectorStore`, `DocumentStore`, `SessionStore`, `MemoryDeleteStore` Protocols + embedding helpers |
| `store_impl.py` | `SQLiteVectorStore`, `SQLiteDocumentStore`, `SQLiteSessionStore`, `SQLiteMemoryDeleteStore` implementations |
| `store.py` | Re-export stub (imports from both, provides backward-compatible `from db.store import ...`) |

## Proposed Changes

### `06_shared_04_db_architecture_and_schema.md` §2 directory listing

Replace the existing listing:

```markdown
db/
├── helper.py              SQLiteHelper — connection lifecycle, PRAGMA, vec extension
├── create_schema.py       DDL creation (rag + session schemas; idempotent)
├── store_protocols.py     Protocol definitions + embedding helpers
├── store_impl.py          SQLite implementations of all protocols
├── store.py               Re-export stub (backward-compatible imports from db.store)
├── maintenance.py         WAL checkpoint, VACUUM, purge, rotate, recover
├── tool_results.py        ToolResultStore — full tool result storage
└── workflow_schema.py     workflow.sqlite DDL initialization
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Manual review | Compare listing to `scripts/db/` files | All 10 files listed, descriptions accurate |
