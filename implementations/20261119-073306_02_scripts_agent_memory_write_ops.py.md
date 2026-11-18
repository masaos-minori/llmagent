## Goal

Route `write_ops._emit_delete_event` through the shared `_emit_change_event` emitter, removing its inline `JsonlMemoryStore` construction and late import (`REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit.

## Assumptions

- The sibling document adds `_emit_change_event(event, memory_id)` to `jsonl_store.py`.
- After routing through the emitter, the top-level `from agent.memory.config_path import resolve_memory_jsonl_dir` (write_ops.py:10) and `from pathlib import Path` (write_ops.py:5) become unused (their only usage is the removed inline construction at L145), so both must be removed to keep ruff clean.

## Design decisions

- Replace the late import and inline body of `_emit_delete_event` with a single call to the shared emitter, keeping the late-import style to preserve the existing import discipline and minimize blast radius.

## Alternatives considered

- Moving the import to module level: rejected; the callers currently late-import to avoid import cost, and the plan removes the inline construction rather than restructuring imports beyond what is needed.

## Implementation
### Target file
`scripts/agent/memory/write_ops.py`
### Procedure
Replace the inline `JsonlMemoryStore` construction + late import in `_emit_delete_event` with a call to the shared emitter, then remove the now-unused imports.
### Method
1. In `scripts/agent/memory/write_ops.py`, `_emit_delete_event` (L137-147), replace the late import line (L143):
   ```python
   from agent.memory.jsonl_store import JsonlMemoryStore
   ```
   with:
   ```python
   from agent.memory.jsonl_store import _emit_change_event
   ```
2. Replace the two body lines (L145-146):
   ```python
   store = JsonlMemoryStore(Path(resolve_memory_jsonl_dir()) / "memories.jsonl")
   store.append_event("delete", memory_id)
   ```
   with a single call:
   ```python
   _emit_change_event("delete", memory_id)
   ```
3. Remove the now-unused top-level import at L10:
   ```python
   from agent.memory.config_path import resolve_memory_jsonl_dir
   ```
4. Remove the now-unused top-level import at L5:
   ```python
   from pathlib import Path
   ```
   Confirm `Path` and `resolve_memory_jsonl_dir` are not referenced elsewhere in the file before removing.
### Details

- Preserve the docstring and SQLite-first ordering: the emit call stays after the SQLite commit (write_ops.py:133 calls `_emit_delete_event` after `db.commit()`).
- Preserve error propagation: `_emit_change_event` performs no try/except, so an append failure still propagates to the caller (REQ-003).
- Do not change `write_ops.delete`'s SQLite transaction boundaries (out of scope).

## Compatibility considerations

N/A: private helper reorganization; no public signature or behavior change. The delete event still records `{"event": "delete", "memory_id", "at"}` via the shared emitter (REQ-004).

## Security considerations

N/A: no change to query construction, binding, or side-effect semantics beyond the existing append primitive.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/write_ops.py` | Integration: delete emits one event after SQLite commit | `uv run pytest tests/agent/memory/ (delete handler tests)` | all pass |
| `scripts/agent/memory/write_ops.py` | Static: format, lint, type | `uv run ruff check` / `uv run mypy` on the touched files | clean (no unused imports) |

## Completion criteria

- `write_ops._emit_delete_event` no longer imports `JsonlMemoryStore` or constructs the archive path; it calls the shared emitter (`REQ-002`).
- `Path` and `resolve_memory_jsonl_dir` imports removed if unused elsewhere; ruff reports no F401 (`REQ-002`).
- SQLite-first ordering and error propagation preserved (`REQ-003`).
- ruff check and mypy are clean on the touched file (`REQ-001`–`REQ-004`).

## Out of Scope

- Changing what data the change event records.
- Refactoring the JSONL read path or `iter_records`.
- Any change to the SQLite transaction boundaries in `write_ops.delete`.
- Touching `pin_ops._emit_event` (handled by its own sibling document) or `memory_data_ops._emit_prune_event` (out of scope for this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route `_emit_delete_event` through the shared emitter; remove unused imports (`scripts/agent/memory/write_ops.py`, REQ-002) | Pending | — | — | |
| 2 | Verify SQLite-first + error propagation; run ruff/mypy/tests (`scripts/agent/memory/write_ops.py`, REQ-002, REQ-003) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261118-224741_dupevt001_shared-change-event-helper.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-002801_dupevt001_shared-change-event-helper.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-073306
- **Related target files**: `scripts/agent/memory/write_ops.py`
