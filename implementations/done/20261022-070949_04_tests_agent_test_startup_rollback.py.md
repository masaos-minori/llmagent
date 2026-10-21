## Goal

Update `test_run_returns_spawned_subprocesses_on_success` in `tests/agent/test_startup_rollback.py` to the 2-tuple contract returned by the collapsed `StartupOrchestrator.run()`: assert the two-element shape and drop the third-value assertion (REQ-006, T-001).

## Scope

In-scope: `tests/agent/test_startup_rollback.py` only — the single `test_run_returns_spawned_subprocesses_on_success` method (lines 223-238).

Out-of-scope: `startup.py`, `repl.py`, `test_repl.py` (sibling documents). The `_spawned_subprocesses` field assertions elsewhere (e.g. `_spawned_subprocesses == []` and `== fake_procs`) remain valid because the field is preserved (T-003) and are NOT touched here.

## Assumptions

- `subprocess` stays imported and used at module level (`MagicMock(spec=subprocess.Popen)` at lines 227-228), so the import is retained.
- `fake_procs` is still passed as `orch._start_servers`'s `return_value`, so it is not left unused even after the third-value assertion is removed.

## Design decisions

- Bind the result and assert it equals `(orch._cmds, orch._orchestrator)` with length 2, replacing the old `cmds, orchestrator, spawned = ...` unpacking and `assert spawned == fake_procs`.
- Rename the test to reflect that it now verifies the 2-tuple shape rather than a returned subprocess list (the old name is now inaccurate).

## Alternatives considered

- Keeping the old method name `test_run_returns_spawned_subprocesses_on_success`: rejected — the method no longer asserts anything about spawned processes, so the name would mislead future readers.

## Implementation

### Target file

`tests/agent/test_startup_rollback.py`

### Procedure

1. Rename the method `test_run_returns_spawned_subprocesses_on_success` → `test_run_returns_cmds_and_orchestrator_on_success` (new).
2. Update the docstring.
3. Replace the 3-way unpacking and the third-value assertion with a 2-tuple assertion.

### Method

Edit the method body at lines 223-238; no new symbols, no import change.

### Details

Replace lines 223-238:

```python
    async def test_run_returns_spawned_subprocesses_on_success(self) -> None:
        """Assert run()'s third return value equals the real spawned-process list."""
        orch, mock_lifecycle = _make_rollback_startup()
        fake_procs = [
            MagicMock(spec=subprocess.Popen),
            MagicMock(spec=subprocess.Popen),
        ]
        orch._start_servers = AsyncMock(return_value=fake_procs)
        orch._check_services = AsyncMock()
        orch._setup_prompt = AsyncMock()
        orch._cmds = MagicMock()
        orch._orchestrator = MagicMock()

        cmds, orchestrator, spawned = await orch.run()

        assert spawned == fake_procs
```

with:

```python
    async def test_run_returns_cmds_and_orchestrator_on_success(self) -> None:
        """Assert run() returns exactly (cmds, orchestrator); no subprocess list."""
        orch, mock_lifecycle = _make_rollback_startup()
        fake_procs = [
            MagicMock(spec=subprocess.Popen),
            MagicMock(spec=subprocess.Popen),
        ]
        orch._start_servers = AsyncMock(return_value=fake_procs)
        orch._check_services = AsyncMock()
        orch._setup_prompt = AsyncMock()
        orch._cmds = MagicMock()
        orch._orchestrator = MagicMock()

        result = await orch.run()

        assert result == (orch._cmds, orch._orchestrator)
        assert len(result) == 2
```

## Compatibility considerations

N/A: test-only change; the production contract is updated by the sibling `startup.py` / `repl.py` documents.

## Security considerations

N/A: no security impact.

## Rollback considerations

Revert the commit (or reverse the edits above).

## Validation plan

- `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_repl.py tests/agent/test_startup_mcp_lifecycle.py` then the full `tests/agent/` suite — the renamed test passes and all rollback/shutdown assertions still hold (T-001, T-003, T-004).
- `ruff check` / `mypy` / `bandit` on `tests/agent/test_startup_rollback.py`.

## Completion criteria

- `test_run_returns_cmds_and_orchestrator_on_success` asserts the 2-tuple shape; the old `spawned` third-value assertion is gone.
- Field-based assertions (`_spawned_subprocesses`) remain intact and pass.
- Target suite green; `ruff`/`mypy`/`bandit` pass.

## Out of Scope

`startup.py`, `repl.py`, `test_repl.py` (sibling documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261022-075154 | 20261022-075154 | stale-detector flagged the renamed-away old method name (expected post-rename); new name marked (new). |
| 2 | Add or update tests per Validation plan | Completed | 20261022-075154 | 20261022-075154 | This file IS the test target; no separate test addition. stale-detector flagged the renamed-away old method name (expected post-rename); new name marked (new). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261022-075154 | 20261022-075154 | stale-detector flagged the renamed-away old method name (expected post-rename); new name marked (new). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261022-075154 | 20261022-075154 | N/A stale-detector flagged the renamed-away old method name (expected post-rename); new name marked (new). |

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
- **Related target files**: `tests/agent/test_startup_rollback.py`