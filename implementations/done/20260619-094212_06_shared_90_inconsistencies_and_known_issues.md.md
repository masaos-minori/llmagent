# Implementation: Resolve DESIGN-01 in known-issues Doc

## Goal

Mark DESIGN-01 in `docs/06_shared_90_inconsistencies_and_known_issues.md` as RESOLVED and add a reference to the updated documentation so the known-issues file reflects the current state.

## Scope

- `docs/06_shared_90_inconsistencies_and_known_issues.md` — update DESIGN-01 entry (lines 58–67)

Out of scope:
- Code changes
- Other DESIGN-* entries

## Assumptions

1. DESIGN-01 is currently "Needs confirmation" (line 60) and the Recommended action says to document the extensibility rationale.
2. After steps 1 and 2 are complete:
   - `06_shared_04` shows the three-file split
   - `06_shared_05` §4 has the extensibility sentence
3. The RESOLVED pattern to follow is the CONFIG-01 pattern (line 12–15): change Type to "Document inconsistency (resolved)", update the statement, remove the "Recommended action" line, add resolution description.
4. The `Impact scope` must be updated from `db/store.py::MemoryDeleteStore` (single file) to reflect the three-file split (`db/store_protocols.py::MemoryDeleteStore`).

## Implementation

### Target file

`docs/06_shared_90_inconsistencies_and_known_issues.md`

### Procedure

1. Change the heading suffix from nothing to `(RESOLVED)`.
2. Change Type from "Needs confirmation" to "Document inconsistency (resolved)".
3. Update Impact scope to reference `db/store_protocols.py`.
4. Replace the "Recommended action" line with a resolution description.

### Method

In-place block replacement of lines 58–67. Follow the CONFIG-01 RESOLVED pattern exactly.

### Details

**Current (lines 58–67):**
```markdown
### DESIGN-01: Responsibility boundary between `MemoryDeleteStore` and `SQLiteMemoryDeleteStore`

- **Type:** Needs confirmation
- **Impact scope:** `db/store.py::MemoryDeleteStore` (Protocol), `db/store.py::SQLiteMemoryDeleteStore` (implementation)
- **Statement A:** `MemoryDeleteStore` is a `Protocol` defining `delete_memories_before(older_than_days)`.
- **Statement B:** `SQLiteMemoryDeleteStore` implements this protocol for SQLite (deletes from `memories`, `memories_fts`, `memories_vec` atomically).
- **Current safe interpretation:** The Protocol/implementation split allows future non-SQLite backends. For current SQLite-only deployments, use `SQLiteMemoryDeleteStore` directly.
- **Recommended action:** Document that `MemoryDeleteStore` protocol exists for extensibility, not because non-SQLite backends are planned.
- **Notes for AI reference:** Do not confuse `SQLiteMemoryDeleteStore` (cross-table delete) with `MemoryStore.delete()` (single-entry delete).
```

**Replace with:**
```markdown
### DESIGN-01: Responsibility boundary between `MemoryDeleteStore` and `SQLiteMemoryDeleteStore` (RESOLVED)

- **Type:** Document inconsistency (resolved)
- **Impact scope:** `db/store_protocols.py::MemoryDeleteStore` (Protocol), `db/store_impl.py::SQLiteMemoryDeleteStore` (implementation)
- **Statement A:** `MemoryDeleteStore` is a `Protocol` defining `delete_memories_before(older_than_days)`.
- **Statement B:** `SQLiteMemoryDeleteStore` implements this protocol for SQLite (deletes from `memories`, `memories_fts`, `memories_vec` atomically).
- **Current safe interpretation:** The Protocol/implementation split allows future non-SQLite backends. For current SQLite-only deployments, use `SQLiteMemoryDeleteStore` directly.
- **Resolution:** Extensibility rationale documented in [06_shared_05 §4 MemoryDeleteStore](06_shared_05_db_api_and_operations.md). Directory listing updated in [06_shared_04](06_shared_04_db_architecture_and_schema.md).
- **Notes for AI reference:** Do not confuse `SQLiteMemoryDeleteStore` (cross-table delete) with `MemoryStore.delete()` (single-entry delete).
```

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-commit | `pre-commit run --all-files` | pass |
| Manual review | Read DESIGN-01 entry | status is clearly RESOLVED with links to updated docs |
| Link check | Open linked sections in 06_shared_04 and 06_shared_05 | content exists at linked anchors |
