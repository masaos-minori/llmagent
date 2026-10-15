## Goal

Make `write_ops.delete()` remove the memory's `memory_links` rows in the same
transaction and append a `delete` change event after the SQLite write
(REQ-001, REQ-004).

## Scope

Modify `scripts/agent/memory/write_ops.py` only: extend `delete()` to clear
`memory_links` atomically and emit a `delete` event.

## Assumptions

- `memory_links` has `(src_id, dst_id)` both referencing `memories(memory_id)`; a
  deleted memory can appear in either column, so delete both (schema in
  `schema_sql.py`).
- SQLite foreign keys are OFF by default, so cascade cannot be relied on — delete
  the rows explicitly (REQ-004).
- Events are appended after the SQLite commit (SQLite-first); a failed append does
  NOT roll back the SQLite change and surfaces an error for the M-07 warning
  (REQ-001).
- `M-07` is a new message not yet defined in code; the emit is wired by the caller
  (`memory_data_ops.py`, a separate row).

## Design decisions

- Add the two `memory_links` deletes inside the existing transaction block so all
  four tables mutate in one commit.
- After the `with` block commits, append the `delete` event via a lazily
  constructed `JsonlMemoryStore`; on failure raise a clear exception rather than
  swallowing it, so the caller can print M-07 while the SQLite change stands.

## Alternatives considered

- Relying on `ON DELETE CASCADE`: rejected. SQLite leaves `PRAGMA foreign_keys`
  off, so cascade never fires; orphaned `memory_links` rows remain today.

## Implementation

### Target file

`scripts/agent/memory/write_ops.py`

### Procedure

1. Delete `memory_links` rows for `memory_id` in the same transaction.
2. Append a `delete` event after the commit.

### Method

- Inside `delete()`, within the existing `with ... as db:` block, after the
  `memories_vec` delete and before `db.commit()`, add:

  ```python
  db.execute("DELETE FROM memory_links WHERE src_id = ?", (memory_id,))
  db.execute("DELETE FROM memory_links WHERE dst_id = ?", (memory_id,))
  ```

- After the `with` block (i.e. after commit), when `deleted` is True, emit the
  event:

  ```python
  if deleted:
      _emit_delete_event(new)(memory_id)
  ```

- Add the helper:

  ```python
  def _emit_delete_event(new)(memory_id: str) -> None:
      """Append a 'delete' change event after the SQLite write (SQLite-first)."""
      from pathlib import Path

      from agent.memory.jsonl_store import JsonlMemoryStore
      from shared.config_loader import ConfigLoader

      cfg = ConfigLoader().load("agent.toml")
      store = JsonlMemoryStore(Path(cfg["memory"]["memory_jsonl_dir"]) / "memories.jsonl")
      store.append_event("delete", memory_id)
  ```

  (`append_event` is added in `jsonl_store.py`, row 1.)

### Details

- Keep the existing transaction shape (context-manager commit); the new deletes
  stay in that single transaction. Do not switch to `begin_immediate` unless the
  concurrency analysis requires it.
- `_emit_delete_event(new)` must not raise for a missing archive directory silently —
  propagate the error so M-07 fires. Decide (and document) how the sync append is
  serialized against the async `write()` path in `JsonlMemoryStore`.
- `append_event` opens `self._path` as a **file** (`self._path.open("a")`), so the
  store must be built with the archive *file* path, not the directory:
  `Path(cfg["memory"]["memory_jsonl_dir"]) / "memories.jsonl"` (matches
  `factory._build_jsonl_store`). Passing the raw directory raises `IsADirectoryError`.
- `now_iso` / event shape come from `jsonl_store.append_event`; do not duplicate
  the event schema here.

## Compatibility considerations

`delete()` still returns `bool`. It now also touches `memory_links` and appends a
JSONL line; tests that assert `memory_links` remains after delete, or that do not
expect a JSONL write, must be updated.

## Security considerations

N/A: deletion of link rows is bounded by `memory_id`; no new injection surface
(bound parameters throughout).

## Rollback considerations

Revert the commit; the deletes and event helper are additive.

## Validation plan

- `pytest tests/agent/memory/test_memory_store.py` covers the four-table delete
  and the delete event.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

After `delete(mid)` returns True, `memories`, `memories_fts`, `memories_vec`, and
`memory_links` (both columns) are empty for `mid`, and a `delete` event line exists
in the JSONL archive.

## Out of scope

The event-append primitive and reader (`jsonl_store.py`), the rebuild replay
(`import_ops.py`), and the caller that prints M-07 (`memory_data_ops.py`) are
separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `delete()` with atomic `memory_links` removal + delete event | Completed | 20261015-135752 | 20261015-135752 | REQ-001, REQ-004 delete() clears memories/memories_fts/memories_vec/memory_links in one txn + emits delete event after commit |
| 2 | Add/update four-table delete + event tests | Completed | 20261015-135752 | 20261015-135752 | `test_memory_store.py` 4 delete tests in test_memory_store.py; test_session_memory_boundary.py patched (_emit_delete_event spy + memory_links schema) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261015-135752 | 20261015-135752 | ruff/mypy(416)/lint-imports 6-0/bandit High:0/diff-cover 97%/MDQ-RAG 5-5; full suite only pre-existing eventbus acked failures |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/agent/memory/write_ops.py