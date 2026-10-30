## Goal

Remove the two tests in `tests/agent/test_startup_rollback.py` that assert on the
dead `self._spawned_subprocesses` field of `StartupOrchestrator`, so no test in the
repo references the field (REQ-002).

## Scope

Modify only `tests/agent/test_startup_rollback.py`: delete the dead-state assertion in
`test_rollback_no_op_when_no_subprocess_started` and delete the entire
`test_run_populates_spawned_subprocesses_on_exception_path` method. No source file
change (that is covered by the sibling procedure for
`scripts/agent/startup.py`).

## Assumptions

- The deleted assertions encode only the dead field's value, not a production rollback
  contract: rollback is validated by sibling assertions on
  `lifecycle.shutdown_all()` (verified in Step 3a).
- `import subprocess` stays used after the edits (still referenced by other tests'
  `MagicMock(spec=subprocess.Popen)`); no import cleanup needed.
- Deleting a test here removes a dead-state lock, not a behavior contract.

## Design decisions

- Keep `mock_lifecycle.shutdown_all.assert_awaited_once()` in
  `test_rollback_no_op_when_no_subprocess_started`; it validates the real rollback
  path that the removed assertion did not.
- Delete `test_run_populates_spawned_subprocesses_on_exception_path` wholesale: its
  sole purpose was asserting the dead field becomes populated.

## Alternatives considered

N/A: test-only Path A change; leaving either assertion would re-lock the dead field
into the suite.

## Implementation
### Target file

`tests/agent/test_startup_rollback.py`

### Procedure

1. In `test_rollback_no_op_when_no_subprocess_started`, delete the dead-state
   assertion line, keeping the `shutdown_all` assertion above it.
2. Delete the entire `test_run_populates_spawned_subprocesses_on_exception_path`
   method (decorator through final assertion).

### Method

In `test_rollback_no_op_when_no_subprocess_started`, remove only the last assertion
line, leaving the preceding `assert_awaited_once()` call. Locate
`test_run_populates_spawned_subprocesses_on_exception_path` by its name and delete from
its `@pytest.mark.asyncio` decorator through its trailing blank line before the next
test.

### Details

Delete this line (current line 236), the last line of
`test_rollback_no_op_when_no_subprocess_started`:

```python
        assert orch._spawned_subprocesses == []
```

leaving:

```python
        mock_lifecycle.shutdown_all.assert_awaited_once()
```

Delete the whole method `test_run_populates_spawned_subprocesses_on_exception_path`
(current lines 238-256, i.e. its `@pytest.mark.asyncio` decorator through the final
`assert orch._spawned_subprocesses == fake_procs` and the following blank line):

```python
    @pytest.mark.asyncio
    async def test_run_populates_spawned_subprocesses_on_exception_path(self) -> None:
        """Regression: _spawned_subprocesses must be populated even when run() raises."""
        orch, mock_lifecycle = _make_rollback_startup()
        fake_procs = [
            MagicMock(spec=subprocess.Popen),
            MagicMock(spec=subprocess.Popen),
        ]
        orch._start_servers = AsyncMock(return_value=fake_procs)
        orch._check_services = AsyncMock(
            side_effect=RuntimeError("health check failed")
        )
        orch._setup_prompt = AsyncMock()
        mock_lifecycle.shutdown_all.side_effect = OSError("shutdown failed")

        with pytest.raises(RuntimeError, match="health check failed"):
            await orch.run()

        assert orch._spawned_subprocesses == fake_procs
```

## Compatibility considerations

`test_run_returns_cmds_and_orchestrator_on_success` still asserts `run()` returns
exactly `(cmds, orchestrator)`; removing the sibling dead-state test does not affect it.

## Security considerations

N/A: no auth, secret, or credential-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy (Unit) | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_startup_rollback.py` | Regression: suite passes after the two edits | `uv run pytest tests/agent/test_startup_rollback.py` | All tests pass; no assertion references `_spawned_subprocesses` |
| Repo-wide | Confirm no remaining reader of the field on `StartupOrchestrator` | `rg -n "_spawned_subprocesses" tests/ scripts/` | Only `McpServerStarter` references remain (different class) |

## Completion criteria

- `test_rollback_no_op_when_no_subprocess_started` no longer asserts on
  `_spawned_subprocesses` and still calls
  `mock_lifecycle.shutdown_all.assert_awaited_once()`.
- `test_run_populates_spawned_subprocesses_on_exception_path` no longer exists.
- `rg -n "_spawned_subprocesses" tests/agent/test_startup_rollback.py` returns no
  matches.
- The full `tests/agent/test_startup_rollback.py` suite passes.

## Out of Scope

The field removal in `scripts/agent/startup.py` (sibling procedure); any change to
`McpServerStarter._spawned_subprocesses`; rollback / `lifecycle.shutdown_all()`
behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the dead-state tests described in Implementation > Procedure/Method/Details | Completed | 20261030-092017 | 20261030-092017 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-092017 | 20261030-092017 |  |

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
- **Requirement ID**: `REQ-002` (remove the two tests that assert on the dead `self._spawned_subprocesses` field)
- **Source issue**: issues/20261029-220719_startorch001_dead-spawned-subprocesses.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-065511_startorch001_dead-spawned-subprocesses.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-073124
- **Related target files**: tests/agent/test_startup_rollback.py