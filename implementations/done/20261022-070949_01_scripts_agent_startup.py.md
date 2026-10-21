## Goal

Collapse `StartupOrchestrator.run()`'s return tuple from three elements to two `(CommandRegistry, Orchestrator)` and replace the misleading "caller terminates the subprocesses" comment with a statement that `lifecycle.shutdown_all()` owns termination (REQ-001, REQ-003). Zero runtime behavioral delta.

## Scope

In-scope: `scripts/agent/startup.py` only — the `run()` annotation, the `run()` docstring, the line-88 comment, and the `run()` return statement. The `self._spawned_subprocesses = await self._start_servers()` assignment is preserved unchanged (REQ-004).

Out-of-scope: everything handled by the sibling documents for `repl.py`, `test_repl.py`, and `test_startup_rollback.py`. `McpServerStarter.start_servers()`, `ResourceShutdownCoordinator`, and `lifecycle` are untouched.

## Assumptions

- `StartupOrchestrator` is internal, not a public/library API (ASM-002); changing `run()` arity is internal plumbing.
- The `_spawned_subprocesses` field stays populated for rollback bookkeeping and its existing field-based tests (ASM-003).
- `McpServerStarter.start_servers()` keeps returning the list so the preserved field stays populated (ASM-001).

## Design decisions

- Collapse the tuple to `(self._cmds, self._orchestrator)` while keeping `self._spawned_subprocesses` assigned — no behavioral delta, rollback bookkeeping intact.
- Replace the dead comment with an explicit lifecycle-ownership note so termination responsibility is documented at its single real owner instead of implying a nonexistent caller contract.

## Alternatives considered

- Dropping `McpServerStarter.start_servers()`'s return too: rejected — it would additionally require deleting the append in `_start_http_subprocess_once` and updating `test_startup_mcp_lifecycle.py` (ASM-001), expanding blast radius.

## Implementation

### Target file

`scripts/agent/startup.py`

### Procedure

1. Change the `run()` return annotation (line 67) to the 2-tuple.
2. Update the `run()` docstring (line 68) to drop the third element.
3. Replace the comment at line 88 with a lifecycle-ownership statement.
4. Change the return statement (line 94) to the 2-tuple.
5. Leave the `self._spawned_subprocesses = await self._start_servers()` assignment (line 73) untouched.

### Method

Edit the four in-place locations inside `run()`; no new symbols, no import added or removed.

### Details

- Line 67 — annotation:
  `async def run(self) -> tuple[CommandRegistry, Orchestrator, list[subprocess.Popen]]:`
  →
  `async def run(self) -> tuple[CommandRegistry, Orchestrator]:`
- Line 68 — docstring: `...; return (cmds, orchestrator, spawned_subprocesses).` → `...; return (cmds, orchestrator).`
- Line 88 — comment: `# Pass subprocess list to caller for termination` → `# Termination is owned exclusively by lifecycle.shutdown_all() above; run() no longer returns the spawned-subprocess list.`
- Line 94 — return: `return self._cmds, self._orchestrator, self._spawned_subprocesses` → `return self._cmds, self._orchestrator`
- Line 73 unchanged: `self._spawned_subprocesses = await self._start_servers()`

## Compatibility considerations

N/A: single production caller (`repl.py`) is updated by the sibling document; `StartupOrchestrator` is not a public/library API.

## Security considerations

N/A: pure return-value arity reduction; no security impact.

## Rollback considerations

Revert the commit (or reverse the four edits above).

## Validation plan

- `ruff check scripts/agent/startup.py` — passes, no F401 (`import subprocess` is still referenced by the preserved `_spawned_subprocesses` field type hint and stringified annotations).
- `mypy scripts/agent/startup.py` — confirms the 2-tuple annotation and return.
- `bandit scripts/agent/startup.py` — clean.
- `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_repl.py tests/agent/test_startup_mcp_lifecycle.py` then the full `tests/agent/` suite.

## Completion criteria

- `run()` annotation and return expose exactly two elements; no `list[subprocess.Popen]` is returned (AC-001).
- No comment asserts caller termination (AC-003).
- `_spawned_subprocesses` is still assigned (AC-004 / T-003).
- Target suite green; `ruff`/`mypy`/`bandit` pass.

## Out of Scope

`repl.py`, `test_repl.py`, `test_startup_rollback.py` (sibling documents); `McpServerStarter`, `resource_shutdown_coordinator.py`, `lifecycle`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261022-075154 | 20261022-075154 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261022-075154 | 20261022-075154 | Handled by the sibling `test_repl.py` / `test_startup_rollback.py` documents. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261022-075154 | 20261022-075154 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261022-075154 | 20261022-075154 | N/A |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: `issues/20261021-220228_star001_clarify-mcp-subprocess-termination-ownership-and-remove-unused-spawned-subprocess-list-return.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-231352_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-070949
- **Related target files**: `scripts/agent/startup.py`