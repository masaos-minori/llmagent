## Goal

Reroute `pin_ops._emit_event` through the shared resolver `resolve_memory_jsonl_dir()` (REQ-003) so `pin()`/`unpin()` append their `pin`/`unpin` change events to `memories.jsonl` on the main path instead of raising `KeyError('memory')` after the SQLite change is committed.

## Scope

- Modify only `_emit_event` in `scripts/agent/memory/pin_ops.py`.
- Change exactly the archive-path resolution line; preserve the surrounding SQLite-first flow and the M-07 append-failure propagation.

## Assumptions

- The shared resolver lives in `scripts/agent/memory/config_path.py` (created in the REQ-001 row) and returns a path string.
- `pin()`/`unpin()` remain SQLite-first: the SQLite change stands even if the archive append fails, and a real append failure re-raises so the caller can surface M-07.

## Design decisions

- **Swap only the path expression.** Replace `Path(cfg["memory"]["memory_jsonl_dir"]) / "memories.jsonl"` with `Path(resolve_memory_jsonl_dir()) / "memories.jsonl"`.
- **Remove the lazy `ConfigLoader` import** from inside `_emit_event`; the resolver now performs the load.

## Alternatives considered

- **Thread `AgentContext`/`ctx.cfg` into `pin()`/`unpin()`** — larger signature change across callers; rejected by the Plan's minimal-fix assumption.

## Implementation

### Target file
`scripts/agent/memory/pin_ops.py`

### Procedure
1. Open `scripts/agent/memory/pin_ops.py`. Locate `_emit_event` (line 62) and its body (lines 68-72).
2. Remove the local `from agent.memory.jsonl_store import JsonlMemoryStore` stays, but remove the `cfg = ConfigLoader().load("agent.toml")` line (line 70) and the lazy `ConfigLoader` import if present at module top.
3. Replace line 71:
   - From: `    store = JsonlMemoryStore(Path(cfg["memory"]["memory_jsonl_dir"]) / "memories.jsonl")`
   - To: `    store = JsonlMemoryStore(Path(resolve_memory_jsonl_dir()) / "memories.jsonl")`
4. Add the resolver import at the top of the module: `from agent.memory.config_path import resolve_memory_jsonl_dir`.
5. Delete the now-unused `cfg` local variable.

### Method
In-place substitution of the path expression; append-after-commit ordering and the re-raise of a failed append are untouched.

### Details
- After the change `_emit_event` reads:
  ```python
  def _emit_event(event: str, memory_id: str) -> None:
      from agent.memory.jsonl_store import JsonlMemoryStore
      store = JsonlMemoryStore(Path(resolve_memory_jsonl_dir()) / "memories.jsonl")
      store.append_event(event, memory_id)
  ```
- The docstring already notes it mirrors `write_ops._emit_delete_event`; keep that note.
- Do not alter `pin()` (line 36) / `unpin()` (line 49) or their call sites (lines 45, 58).

## Compatibility considerations
Low blast radius: only the internal path read changes; `pin()`/`unpin()` return values and callers are unaffected.

## Security considerations
N/A: no new privilege or injection surface; the path comes from the same config source as before.

## Rollback considerations
Revert this one-function edit (restore the nested `cfg["memory"]["memory_jsonl_dir"]` read and its `ConfigLoader` import).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `pin_ops.pin()`/`unpin()` | Unit: pin/unpin an existing id against the real loader; assert the event line lands under the isolated temp root | `uv run pytest tests/agent/memory/test_memory_store.py` | `memories.jsonl` contains the pin/unpin event; no `KeyError` |

## Completion criteria

- No code under `scripts/agent/memory/pin_ops.py` reads the nested `cfg["memory"]["memory_jsonl_dir"]`.
- `pin()`/`unpin()` append their event to the resolved archive path on the main path.
- SQLite-first ordering and M-07 re-raise preserved.

## Out of Scope

- Rerouting `write_ops._emit_delete_event` and `memory_data_ops._emit_prune_event` (separate rows).
- Changing the JSONL format or archive filename.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reroute `pin_ops._emit_event` through the resolver (REQ-003) | Completed | 20261020-073045 | 20261020-073045 | Preserve SQLite-first + M-07 re-raise |
| 2 | Add writer-level real-loader test in `test_memory_store.py` (REQ-006) | Completed | 20261020-073045 | 20261020-073045 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-073045 | 20261020-073045 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020-073045 | 20261020-073045 | N/A N/A: no docs/00_index.md task-scope mapping for scripts/agent/memory/pin_ops.py |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261019-165345_memcfg001_memory-event-writers-read-a-missing-config-key.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-205032_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-225902
- **Related target files**: `scripts/agent/memory/pin_ops.py`