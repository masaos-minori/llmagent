## Goal

Reroute `write_ops._emit_delete_event` through the shared resolver `resolve_memory_jsonl_dir()` (REQ-002) so `delete()` appends its `delete` change event to `memories.jsonl` on the main path instead of raising `KeyError('memory')` after the SQLite change is committed.

## Scope

- Modify only `_emit_delete_event` in `scripts/agent/memory/write_ops.py`.
- Change exactly the archive-path resolution line; preserve the surrounding SQLite-first flow and the M-07 append-failure propagation.

## Assumptions

- The shared resolver lives in `scripts/agent/memory/config_path.py` (created in the sibling row for REQ-001) and returns a path string.
- `delete()` remains SQLite-first: the SQLite change stands even if the archive append fails, and a real append failure re-raises so the caller can surface M-07.

## Design decisions

- **Swap only the path expression.** Replace `Path(cfg["memory"]["memory_jsonl_dir"]) / "memories.jsonl"` with `Path(resolve_memory_jsonl_dir()) / "memories.jsonl"`. Everything else in the function is unchanged.
- **Keep the lazy `ConfigLoader` import removed, not added.** The resolver now owns config loading; this function no longer needs `from shared.config_loader import ConfigLoader`.

## Alternatives considered

- **Thread `AgentContext`/`ctx.cfg` into `delete()`** — larger signature change across callers; rejected by the Plan's minimal-fix assumption. Keep the local config load inside the resolver only.

## Implementation

### Target file
`scripts/agent/memory/write_ops.py`

### Procedure
1. Open `scripts/agent/memory/write_ops.py`. Locate `_emit_delete_event` (line 137) and its body (lines 143-147).
2. Remove the local `from shared.config_loader import ConfigLoader` import inside `_emit_delete_event` (line 143) — the resolver now performs the load.
3. Replace line 146:
   - From: `    store = JsonlMemoryStore(Path(cfg["memory"]["memory_jsonl_dir"]) / "memories.jsonl")`
   - To: `    store = JsonlMemoryStore(Path(resolve_memory_jsonl_dir()) / "memories.jsonl")`
4. Add the resolver import at the top of the module (top-level, alongside the other `agent.memory` imports): `from agent.memory.config_path import resolve_memory_jsonl_dir`.
5. Delete the now-unused `cfg` local variable and its `ConfigLoader().load(...)` line.

### Method
In-place substitution of the path expression; the append-after-commit ordering and the re-raise of a failed append are untouched.

### Details
- After the change `_emit_delete_event` reads:
  ```python
  def _emit_delete_event(memory_id: str) -> None:
      from agent.memory.jsonl_store import JsonlMemoryStore
      store = JsonlMemoryStore(Path(resolve_memory_jsonl_dir()) / "memories.jsonl")
      store.append_event("delete", memory_id)
  ```
- `resolve_memory_jsonl_dir()` returns the flat-key path (builder default when unset), matching `ctx.cfg.memory.memory_jsonl_dir`.
- Do not alter `delete()` (line 111) or the emit call site (line 133) beyond what this function requires.

## Compatibility considerations
Low blast radius: only the internal path read changes; `delete()`'s return value and callers are unaffected. The resolver is imported from the new `config_path` module.

## Security considerations
N/A: no new privilege or injection surface; the path comes from the same config source as before.

## Rollback considerations
Revert this one-function edit (restore the nested `cfg["memory"]["memory_jsonl_dir"]` read and the local `ConfigLoader` import).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `write_ops.delete()` | Unit: delete an existing id against the real loader; assert a `delete` event line lands under the isolated temp root and the success path completes | `uv run pytest tests/agent/memory/test_memory_store.py` | `memories.jsonl` contains the delete event; no `KeyError` |

## Completion criteria

- No code under `scripts/agent/memory/write_ops.py` reads the nested `cfg["memory"]["memory_jsonl_dir"]`.
- `delete()` appends its `delete` event to the resolved archive path on the main path and prints its success line.
- SQLite-first ordering and M-07 re-raise preserved.

## Out of Scope

- Rerouting `pin_ops._emit_event` and `memory_data_ops._emit_prune_event` (separate rows).
- Changing the JSONL format or archive filename.
- Adding command-level end-to-end tests (separate row, REQ-007).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reroute `write_ops._emit_delete_event` through the resolver (REQ-002) | Completed | 20261020-071920 | 20261020-071920 | Preserve SQLite-first + M-07 re-raise |
| 2 | Add writer-level real-loader test in `test_memory_store.py` (REQ-006) | Completed | 20261020-071920 | 20261020-071920 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-071920 | 20261020-071920 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020-071920 | 20261020-071920 | N/A N/A: no docs/00_index.md task-scope mapping for scripts/agent/memory/write_ops.py |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261019-165345_memcfg001_memory-event-writers-read-a-missing-config-key.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-205032_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-225902
- **Related target files**: `scripts/agent/memory/write_ops.py`