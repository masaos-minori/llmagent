## Goal

Add a single synchronous, module-level change-event emitter to `scripts/agent/memory/jsonl_store.py` that resolves the archive path via `resolve_memory_jsonl_dir()` and appends an event, so both `write_ops._emit_delete_event` and `pin_ops._emit_event` delegate to it (`REQ-001`, `REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit.

## Assumptions

- `append_event(event, memory_id)` (jsonl_store.py:72) is the sync primitive the emitter delegates to; it is a method on `JsonlMemoryStore`.
- `resolve_memory_jsonl_dir()` (config_path.py:11) is the single archive-path resolver both callers already use; importing it does not create a cycle (config_path.py imports nothing from the memory package at module level).
- The emitter stays a private module-level function (UNK-01 option a), preserving the Path A (no public interface change) classification.

## Design decisions

- Add a module-level function `_emit_change_event` (new) that constructs a `JsonlMemoryStore` at the resolved archive path and calls `append_event(event, memory_id)`. Keep the `resolve_memory_jsonl_dir()` import as a late import inside the function to preserve the existing lazy-import discipline of the change-event writers and avoid any new top-level import in this module.
- Place the function directly after the existing module-level helper `_entry_from_dict` (jsonl_store.py:34-47) and before the `JsonlMemoryStore` class, so it sits with the other module-level helpers.

## Alternatives considered

- Making the emitter a method on `JsonlMemoryStore` (UNK-01 option b): rejected as primary because it widens the public/interface surface and could reclassify this as Path B; the module-level function keeps the change private and removes both copies with one definition.

## Implementation
### Target file
`scripts/agent/memory/jsonl_store.py`
### Procedure
Add a synchronous module-level emitter that resolves the archive path and appends an event.
### Method
1. In `scripts/agent/memory/jsonl_store.py`, insert a module-level function after `_entry_from_dict` (L34-47) and before `class JsonlMemoryStore:` (L50):
   ```python
   def _emit_change_event(event: str, memory_id: str) -> None:
       """Append a change event to the JSONL archive after the SQLite write (SQLite-first).

       Shared by ``write_ops._emit_delete_event`` and ``pin_ops._emit_event``.
       Resolves the archive path via ``resolve_memory_jsonl_dir()`` and appends
       synchronously; a failed append propagates so the caller can surface M-07.
       """
       from agent.memory.config_path import resolve_memory_jsonl_dir

       store = JsonlMemoryStore(Path(resolve_memory_jsonl_dir()) / "memories.jsonl")
       store.append_event(event, memory_id)
   ```
2. Do not change `JsonlMemoryStore.append_event` or any other member.
### Details

- Preserve the exact archive path construction `Path(resolve_memory_jsonl_dir()) / "memories.jsonl"` (REQ-004).
- Preserve synchronous behavior and error propagation: the function performs no try/except, so an append failure propagates to the caller (REQ-003).
- The event name ("delete"/"pin"/"unpin"/"unpin") is passed through by each caller unchanged (out of scope: what data the event records).

## Compatibility considerations

N/A: purely additive private module-level function; no public signature or behavior change. The `None`-means-unvalidated contract is unrelated here.

## Security considerations

N/A: no change to query construction, binding, or side-effect semantics beyond the existing append primitive.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/jsonl_store.py` | Unit: shared emitter resolves archive path and appends | `uv run pytest tests/agent/memory/test_jsonl_store.py` | all pass |
| `scripts/agent/memory/jsonl_store.py` | Static: format, lint, type | `uv run ruff check` / `uv run mypy` on the touched files | clean |

## Completion criteria

- Exactly one implementation resolves the archive path and appends an event among the in-scope writers (`REQ-001` / single source of truth).
- The emitter stays synchronous and preserves SQLite-first ordering and error propagation (`REQ-003`).
- The archive filename and its resolution via `resolve_memory_jsonl_dir()` are unchanged (`REQ-004`).
- ruff check and mypy are clean on the touched file (`REQ-001`–`REQ-004`).

## Out of Scope

- Changing what data the change event records (`{"event", "memory_id", "at"}`).
- Refactoring the JSONL read path or `iter_records`.
- Any change to the SQLite transaction boundaries in `write_ops.delete`.
- Touching a third near-identical copy in `scripts/agent/commands/memory_data_ops.py::_emit_prune_event` (out of scope for this Plan; the frozen target table lists only jsonl_store.py, write_ops.py, pin_ops.py).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add synchronous shared emitter to jsonl_store.py (`scripts/agent/memory/jsonl_store.py`, REQ-001, REQ-003, REQ-004) | Completed | 20261119-110657 | 20261119-110657 | STEP 1: implemented shared emitter + routing; STEP 2: ruff/mypy/lint-imports/bandit/full-suite/diff-cover all pass |
| 2 | Verify single implementation + sync/error propagation; run ruff/mypy/tests (`scripts/agent/memory/jsonl_store.py`, REQ-001–REQ-004) | Completed | 20261119-110657 | 20261119-110657 | STEP 1: implemented shared emitter + routing; STEP 2: ruff/mypy/lint-imports/bandit/full-suite/diff-cover all pass |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261118-224741_dupevt001_shared-change-event-helper.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-002801_dupevt001_shared-change-event-helper.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-073306
- **Related target files**: `scripts/agent/memory/jsonl_store.py`
