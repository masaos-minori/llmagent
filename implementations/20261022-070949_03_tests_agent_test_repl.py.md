## Goal

Update every mock `StartupOrchestrator.run()` return value in `tests/agent/test_repl.py` from a 3-tuple to a 2-tuple so the mocks match the collapsed contract that `repl.py` now unpacks (REQ-006). Leaving any mock as a 3-tuple would raise `ValueError: too many values to unpack` when `repl.run()` unpacks it.

## Scope

In-scope: `tests/agent/test_repl.py` only — the six `MockStartup.return_value.run = AsyncMock(return_value=(...))` sites.

Out-of-scope: `startup.py`, `repl.py`, and `test_startup_rollback.py` (sibling documents).

## Assumptions

- All six sites drive `await repl.run()`, which unpacks the return value, so all six must be 2-tuples.
- The line-1381 mock carries `[fake_proc]`; dropping the third element leaves `fake_proc` still used via `fake_proc.poll.return_value = None` and `fake_proc.terminate.assert_not_called()`, so no unused-variable results.

## Design decisions

- Shrink each mock return from a 3-tuple to a 2-tuple by removing the trailing `, <third>` element, preserving the first two `MagicMock()`/`cmds, orchestrator` positions that `repl.run()` binds.

## Alternatives considered

- Rewriting these tests to assign `repl._cmds`/`repl._orchestrator` directly instead of mocking `run()`: rejected — out of scope; the minimal change is arity reduction, which keeps every existing assertion valid.

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

Replace the trailing third element of each of the six mock returns with a 2-tuple. Do this at exactly these six locations:

1. Line 724 — `(cmds, orchestrator, [])` → `(cmds, orchestrator)`
2. Line 762 — `(MagicMock(), MagicMock(), [])` → `(MagicMock(), MagicMock())`
3. Line 799 — `(MagicMock(), MagicMock(), [])` → `(MagicMock(), MagicMock())`
4. Line 1381 — `(MagicMock(), MagicMock(), [fake_proc])` → `(MagicMock(), MagicMock())`
5. Line 1455 — `(MagicMock(), MagicMock(), [])` → `(MagicMock(), MagicMock())`
6. Line 1484 — `(MagicMock(), MagicMock(), [])` → `(MagicMock(), MagicMock())`

### Method

Six targeted edits; no new symbols, no import changes.

### Details

The plan's original inventory listed only lines 1381, 1455, 1484; adversarial verification found three additional 3-tuple mocks at lines 724, 762, 799 that also flow through `repl.run()` and must be updated or the corresponding tests raise on unpack. Each edit removes only the trailing `, <third>` element; the leading two tuple positions are unchanged.

## Compatibility considerations

N/A: test-only change; the production contract is updated by the sibling `startup.py` / `repl.py` documents.

## Security considerations

N/A: no security impact.

## Rollback considerations

Revert the commit (or reverse the six edits above).

## Validation plan

- `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_repl.py tests/agent/test_startup_mcp_lifecycle.py` then the full `tests/agent/` suite — the six sites must no longer raise on unpack, and `TestAgentREPLRunSubprocessTermination` still asserts `.terminate()` is not called on success and shutdown routes through `lifecycle.shutdown_all()` on failure (T-002).
- `ruff check` / `mypy` / `bandit` on `tests/agent/test_repl.py`.

## Completion criteria

- All six mock `run()` returns are 2-tuples; no 3-tuple mock of `StartupOrchestrator.run()` remains in the file.
- Target suite green; `ruff`/`mypy`/`bandit` pass.

## Out of Scope

`startup.py`, `repl.py`, `test_startup_rollback.py` (sibling documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This file IS the test target; no separate test addition. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-006
- **Source issue**: `issues/20261021-220228_star001_clarify-mcp-subprocess-termination-ownership-and-remove-unused-spawned-subprocess-list-return.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-231352_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-070949
- **Related target files**: `tests/agent/test_repl.py`
