# Implementation: MemoryDeleteStore Protocol — DB API Doc + Known Issues

## Goal

Add extensibility rationale to `06_shared_05_db_api_and_operations.md` §3 (MemoryDeleteStore section); resolve DESIGN-01 in `06_shared_90_inconsistencies_and_known_issues.md`.

## Scope

- `docs/06_shared_05_db_api_and_operations.md` — add extensibility note to MemoryDeleteStore section
- `docs/06_shared_90_inconsistencies_and_known_issues.md` — resolve DESIGN-01

## Assumptions

1. The Protocol/implementation split exists purely for future extensibility — no non-SQLite backend is planned.
2. `06_shared_05` §3 contains the MemoryDeleteStore section (not §4 as the plan states).

## Current State

### MemoryDeleteStore section (`06_shared_05:160-173`)

```markdown
### `MemoryDeleteStore` / `SQLiteMemoryDeleteStore`

```python
from db.store import MemoryDeleteStore, SQLiteMemoryDeleteStore, MemoryDeleteResult

store = SQLiteMemoryDeleteStore(db)
result: MemoryDeleteResult = store.delete_memories_before(older_than_days=30)
# result.deleted — count of deleted entries
```

- Atomically deletes from `memories`, `memories_fts`, `memories_vec`
- `maintenance.py::prune_old_memories()` delegates to this class
- See [06_shared_90 DESIGN-01](06_shared_90_inconsistencies_and_known_issues.md) for responsibility boundary

---
```

**Gap:** No explanation of WHY there is a Protocol/implementation split. Developer may wonder if non-SQLite backends are planned.

### DESIGN-01 (`06_shared_90:58-66`)

```markdown
### DESIGN-01: Responsibility boundary between `MemoryDeleteStore` and `SQLiteMemoryDeleteStore`

- **Type:** Needs confirmation
- **Impact scope:** `db/store.py::MemoryDeleteStore` (Protocol), `db/store.py::SQLiteMemoryDeleteStore` (implementation)
- **Statement A:** `MemoryDeleteStore` is a `Protocol` defining `delete_memories_before(older_than_days)`.
- **Statement B:** `SQLiteMemoryDeleteStore` implements this protocol for SQLite (deletes from `memories`, `memories_fts`, `memories_vec` atomically).
- **Current safe interpretation:** The Protocol/implementation split allows future non-SQLite backends. For current SQLite-only deployments, use `SQLiteMemoryDeleteStore` directly.
- **Recommended action:** Document that `MemoryDeleteStore` protocol exists for extensibility, not because non-SQLite backends are planned.
- **Notes for AI reference:** Do not confuse `SQLiteMemoryDeleteStore` (cross-table delete) with `MemoryStore.delete()` (single-entry delete).

---
```

**Gap:** Type is "Needs confirmation" — should be resolved. Recommended action is to document extensibility rationale.

## Proposed Changes

### 1. `06_shared_05_db_api_and_operations.md` after line 172

Add extensibility note before the `---` separator:

```markdown
- Atomically deletes from `memories`, `memories_fts`, `memories_vec`
- `maintenance.py::prune_old_memories()` delegates to this class
- **Extensibility rationale:** `MemoryDeleteStore` is a Protocol (structural type) that exists to preserve the option of a non-SQLite backend in the future. Today, `SQLiteMemoryDeleteStore` is the sole implementation. No non-SQLite backend is currently planned.
- See [06_shared_90 DESIGN-01](06_shared_90_inconsistencies_and_known_issues.md) for responsibility boundary
```

### 2. `06_shared_90_inconsistencies_and_known_issues.md` DESIGN-01

Replace lines 58-66:

```markdown
### DESIGN-01: Responsibility boundary between `MemoryDeleteStore` and `SQLiteMemoryDeleteStore` (RESOLVED)

- **Type:** Design decision (resolved)
- **Impact scope:** `db/store_protocols.py::MemoryDeleteStore` (Protocol), `db/store_impl.py::SQLiteMemoryDeleteStore` (implementation), `db/store.py` (re-export stub)
- **Description:** `MemoryDeleteStore` is a `Protocol` defining `delete_memories_before(older_than_days)`. `SQLiteMemoryDeleteStore` implements this protocol for SQLite. The Protocol/implementation split preserves the option of a non-SQLite backend in the future. No non-SQLite backend is currently planned.
- **Current safe interpretation:** Use `SQLiteMemoryDeleteStore` directly for all current use cases. The Protocol type is available for type annotations if dependency injection is needed later.
- **Recommended action:** Complete. Extensibility rationale documented in [06_shared_05](06_shared_05_db_api_and_operations.md).
- **Notes for AI reference:** Do not confuse `SQLiteMemoryDeleteStore` (cross-table delete) with `MemoryStore.delete()` (single-entry delete).
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Manual review | Read updated sections | Extensibility rationale is clear, DESIGN-01 marked resolved |
| Cross-reference | Check DESIGN-01 link in 06_shared_05 | Points to resolved issue with current interpretation |
