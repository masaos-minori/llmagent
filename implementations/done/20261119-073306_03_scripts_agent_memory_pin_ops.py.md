## Goal

Route `pin_ops._emit_event` through the shared `_emit_change_event` emitter, removing its inline `JsonlMemoryStore` construction and late import (`REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit.

## Assumptions

- The sibling document adds `_emit_change_event(event, memory_id)` to `jsonl_store.py`.
- After routing through the emitter, the top-level `from agent.memory.config_path import resolve_memory_jsonl_dir` (pin_ops.py:11) and `from pathlib import Path` (pin_ops.py:7) become unused (their only usage is the removed inline construction at L71), so both must be removed to keep ruff clean.

## Design decisions

- Replace the late import and inline body of `_emit_event` with a single call to the shared emitter, keeping the late-import style to preserve the existing import discipline and minimize blast radius.

## Alternatives considered

- Moving the import to module level: rejected; the caller currently late-imports to avoid import cost, and the plan removes the inline construction rather than restructuring imports beyond what is needed.

## Implementation
### Target file
`scripts/agent/memory/pin_ops.py`
### Procedure
Replace the inline `JsonlMemoryStore` construction + late import in `_emit_event` with a call to the shared emitter, then remove the now-unused imports.
### Method
1. In `scripts/agent/memory/pin_ops.py`, `_emit_event` (L63-73), replace the late import line (L69):
   ```python
   from agent.memory.jsonl_store import JsonlMemoryStore
   ```
   with:
   ```python
   from agent.memory.jsonl_store import _emit_change_event
   ```
2. Replace the two body lines (L71-72):
   ```python
   store = JsonlMemoryStore(Path(resolve_memory_jsonl_dir()) / "memories.jsonl")
   store.append_event(event, memory_id)
   ```
   with a single call:
   ```python
   _emit_change_event(event, memory_id)
   ```
3. Remove the now-unused top-level import at L11:
   ```python
   from agent.memory.config_path import resolve_memory_jsonl_dir
   ```
4. Remove the now-unused top-level import at L7:
   ```python
   from pathlib import Path
   ```
   Confirm `Path` and `resolve_memory_jsonl_dir` are not referenced elsewhere in the file before removing.
### Details

- Preserve the docstring (including the "Mirrors `write_ops._emit_delete_event`" note, which remains accurate since both now delegate to the same shared emitter).
- Preserve SQLite-first ordering: `_emit_event` is called on the main path after `_set_pinned` (pin_ops.py:59); the emit call stays there.
- Preserve error propagation: `_emit_change_event` performs no try/except, so an append failure still propagates to the caller (REQ-003).

## Compatibility considerations

N/A: private helper reorganization; no public signature or behavior change. Events still record `{"event", "memory_id", "at"}` via the shared emitter (REQ-004).

## Security considerations

N/A: no change to query construction, binding, or side-effect semantics beyond the existing append primitive.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/pin_ops.py` | Integration: pin/unpin emit one event after SQLite write | `uv run pytest tests/agent/memory/ (pin/unpin handler tests)` | all pass |
| `scripts/agent/memory/pin_ops.py` | Static: format, lint, type | `uv run ruff check` / `uv run mypy` on the touched files | clean (no unused imports) |

## Completion criteria

- `pin_ops._emit_event` no longer imports `JsonlMemoryStore` or constructs the archive path; it calls the shared emitter (`REQ-002`).
- `Path` and `resolve_memory_jsonl_dir` imports removed if unused elsewhere; ruff reports no F401 (`REQ-002`).
- SQLite-first ordering and error propagation preserved (`REQ-003`).
- ruff check and mypy are clean on the touched file (`REQ-001`–`REQ-004`).

## Out of Scope

- Changing what data the change event records.
- Refactoring the JSONL read path or `iter_records`.
- Touching `write_ops._emit_delete_event` (handled by its own sibling document) or `memory_data_ops._emit_prune_event` (out of scope for this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route `_emit_event` through the shared emitter; remove unused imports (`scripts/agent/memory/pin_ops.py`, REQ-002) | Completed | 20261119-110657 | 20261119-110657 | STEP 1: implemented shared emitter + routing; STEP 2: ruff/mypy/lint-imports/bandit/full-suite/diff-cover all pass |
| 2 | Verify SQLite-first + error propagation; run ruff/mypy/tests (`scripts/agent/memory/pin_ops.py`, REQ-002, REQ-003) | Completed | 20261119-110657 | 20261119-110657 | STEP 1: implemented shared emitter + routing; STEP 2: ruff/mypy/lint-imports/bandit/full-suite/diff-cover all pass |

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
- **Related target files**: `scripts/agent/memory/pin_ops.py`
