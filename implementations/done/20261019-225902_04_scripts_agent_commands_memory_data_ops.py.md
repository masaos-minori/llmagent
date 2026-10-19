## Goal

Reroute `memory_data_ops._emit_prune_event` through the shared resolver `resolve_memory_jsonl_dir()` (REQ-004) so `memory_prune` appends one `delete` event per pruned id to `memories.jsonl` on the main path instead of raising `KeyError('memory')` after the SQLite change is committed.

## Scope

- Modify only `_emit_prune_event` in `scripts/agent/commands/memory_data_ops.py`.
- Change exactly the archive-path resolution line; preserve the surrounding SQLite-first flow and the M-07 append-failure propagation.

## Assumptions

- The shared resolver lives in `scripts/agent/memory/config_path.py` (created in the REQ-001 row) and returns a path string.
- `memory_prune` remains SQLite-first: the SQLite change stands even if the archive append fails, and a real append failure re-raises so the caller can surface M-07.

## Design decisions

- **Swap only the path expression.** Replace `Path(cfg["memory"]["memory_jsonl_dir"]) / "memories.jsonl"` with `Path(resolve_memory_jsonl_dir()) / "memories.jsonl"`.
- **Remove the lazy config/jsonl imports** from inside `_emit_prune_event`; the resolver now performs the load.
- **Within-layer import edge.** `agent.commands.memory_data_ops` importing from `agent.memory` is a within-layer edge that importlinter does not forbid (Plan Design). Keep the resolver import at the top of the module.

## Alternatives considered

- **Thread `AgentContext`/`ctx.cfg` into `memory_prune`** — larger signature change across callers; rejected by the Plan's minimal-fix assumption.

## Implementation

### Target file
`scripts/agent/commands/memory_data_ops.py`

### Procedure
1. Open `scripts/agent/commands/memory_data_ops.py`. Locate `_emit_prune_event` (line 27) and its body (lines 34-42).
2. Remove the local imports inside `_emit_prune_event`: `from pathlib import Path` (line 34), `from shared.config_loader import ConfigLoader` (line 36), and `from agent.memory.jsonl_store import JsonlMemoryStore` (line 38).
3. Replace line 41:
   - From: `    store = JsonlMemoryStore(Path(cfg["memory"]["memory_jsonl_dir"]) / "memories.jsonl")`
   - To: `    store = JsonlMemoryStore(Path(resolve_memory_jsonl_dir()) / "memories.jsonl")`
4. Add the resolver import at the top of the module (near the other `agent.memory` imports, e.g. after line 11): `from agent.memory.config_path import resolve_memory_jsonl_dir`.
5. Delete the now-unused `cfg` local variable.

### Method
In-place substitution of the path expression; append-after-commit ordering and the re-raise of a failed append are untouched.

### Details
- After the change `_emit_prune_event` reads:
  ```python
  def _emit_prune_event(memory_id: str) -> None:
      from agent.memory.jsonl_store import JsonlMemoryStore
      store = JsonlMemoryStore(Path(resolve_memory_jsonl_dir()) / "memories.jsonl")
      store.append_event("delete", memory_id)
  ```
- The docstring references REQ-005; update it to reflect the flat-key resolver (the stale `REQ-005` mention is a leftover from an earlier draft).
- Do not alter `memory_prune` (line 356) or its call site (line 401) beyond what this function requires.

## Compatibility considerations
Low blast radius: only the internal path read changes; `memory_prune`'s return value and callers are unaffected. The new import edge (`agent.commands` → `agent.memory`) is permitted by the layering contract.

## Security considerations
N/A: no new privilege or injection surface; the path comes from the same config source as before.

## Rollback considerations
Revert this one-function edit (restore the nested `cfg["memory"]["memory_jsonl_dir"]` read and its local imports).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `memory_data_ops.memory_prune` | Unit: prune ids against the real loader; assert one `delete` event per pruned id lands under the isolated temp root and the success line prints | `uv run pytest tests/agent/commands/test_memory_data_ops.py` | events present in `memories.jsonl`; no `KeyError` |

## Completion criteria

- No code under `scripts/agent/commands/memory_data_ops.py` reads the nested `cfg["memory"]["memory_jsonl_dir"]`.
- `memory_prune` appends one event per pruned id to the resolved archive path on the main path and reports success.
- SQLite-first ordering and M-07 re-raise preserved.

## Out of Scope

- Rerouting `write_ops._emit_delete_event` and `pin_ops._emit_event` (separate rows).
- Correcting the mocked test shape (separate row, REQ-005).
- Adding command-level end-to-end tests (separate row, REQ-007).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reroute `memory_data_ops._emit_prune_event` through the resolver (REQ-004) | Completed | 20261020 | 20261020 | Rerouted _emit_prune_event through resolve_memory_jsonl_dir(); removed local ConfigLoader/Path/jsonl imports |
| 2 | Add writer/prune real-loader tests (REQ-005, REQ-006) | Completed | 20261020 | 20261020 | Replaced stale nested-key mock test with TestMemoryPruneRealLoader (real resolver + temp-file SQLite + real JSONL append) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020 | 20261020 | ruff/mypy/lint-imports/bandit/ast-grep/generate_reference_table --check all clean; full suite 9591 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020 | 20261020 | N/A per Compatibility/Out of scope |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261019-165345_memcfg001_memory-event-writers-read-a-missing-config-key.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-205032_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-225902
- **Related target files**: `scripts/agent/commands/memory_data_ops.py`
