## Goal

Convert the characterization lock in `test_empty_command_raises_before_spawn`
(`tests/agent/test_http_lifecycle.py`) from asserting the leak to asserting the fixed
behavior (handle closed, registry cleared), matching the sibling cleanup tests
(REQ-002).

## Scope

Modify only `test_empty_command_raises_before_spawn` in `tests/agent/test_http_lifecycle.py`.
No source file change (that is covered by the sibling procedure for
`scripts/agent/http_lifecycle_subprocess_launcher.py`).

## Assumptions

- The test drives the empty-command path via `await mgr.start("test", cfg)` with
  `open_log` patched; the real `forget` runs unmocked but is a safe no-op pop.
- The sibling cleanup tests (`test_command_validation_failure_closes_stderr_and_raises`,
  `test_popen_failure_closes_stderr_and_reraises`) already assert
  `stderr_fh.close.assert_called_once()` + `"test" not in mgr._stderr_files`.

## Design decisions

- Replace the two leak-locking assertions with assertions of the fixed behavior,
  mirroring the sibling cleanup tests exactly.
- Keep the short-circuit assertions (`mock_validate.assert_not_called()`,
  `mock_popen.assert_not_called()`, correct `reason`/`server_key`, and the
  `_http_procs`/`_http_pgids` absence checks) intact so the test still pins the
  empty-command guard firing before validation/Popen.
- Update the docstring to describe the fixed behavior.

## Alternatives considered

N/A: single-test Path A change; no fixture or helper changes needed.

## Implementation
### Target file

`tests/agent/test_http_lifecycle.py`

### Procedure

In `test_empty_command_raises_before_spawn`, replace the two leak assertions with
fixed-behavior assertions and update the method docstring.

### Method

1. Change `stderr_fh.close.assert_not_called()` to
   `stderr_fh.close.assert_called_once()`.
2. Change `assert mgr._stderr_files.get("test") is stderr_fh` to
   `assert "test" not in mgr._stderr_files`.
3. Update the docstring to describe the closed-handle / cleared-registry behavior.

### Details

Before:

```python
        """An empty cmd is a startup failure raised before command validation or Popen.

        The stderr handle opened for the attempt is left open and its tracking entry is
        left in place on this path; the lock records that as current behavior.
        """
```

After:

```python
        """An empty cmd is a startup failure raised before command validation or Popen.

        The stderr handle opened for the attempt is closed and its tracking entry is
        dropped on this path, matching the other failure branches.
        """
```

Before:

```python
        stderr_fh.close.assert_not_called()
        assert mgr._stderr_files.get("test") is stderr_fh
```

After:

```python
        stderr_fh.close.assert_called_once()
        assert "test" not in mgr._stderr_files
```

Keep every other assertion in the test unchanged:
`exc_info.value.failure.reason == "Empty command configuration"`,
`exc_info.value.failure.server_key == "test"`, `mock_validate.assert_not_called()`,
`mock_popen.assert_not_called()`, `assert "test" not in mgr._http_procs`,
`assert "test" not in mgr._http_pgids`.

## Compatibility considerations

The sibling cleanup tests already assert the same fixed behavior, so this test now
converges with them. No other test in the file is affected.

## Security considerations

N/A: no auth, secret, or credential-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy (Unit) | Tool / Command | Expected Outcome |
|---|---|---|---|
| `test_empty_command_raises_before_spawn` | Regression: handle closed once, registry entry removed, short-circuit assertions hold | `uv run pytest tests/agent/test_http_lifecycle.py` | All pass, including sibling cleanup tests |

## Completion criteria

- `test_empty_command_raises_before_spawn` asserts `stderr_fh.close.assert_called_once()`
  and `assert "test" not in mgr._stderr_files`.
- The short-circuit assertions still hold.
- The full suite in `tests/agent/test_http_lifecycle.py` passes.

## Out of Scope

Any change to the success path, the non-empty value-error path, the `Popen`-failure
cleanup, or `Popen`/pipe/`getpgid` handling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the characterization test per Implementation > Procedure/Method/Details | Completed | 20261030-092017 | 20261030-092017 |  |
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
- **Requirement ID**: `REQ-002` (characterization test asserts the fixed behavior: handle closed, registry cleared)
- **Source issue**: issues/20261029-220634_lifecyc001_empty-cmd-stderr-leak.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-001217_lifecyc001_empty-cmd-stderr-leak.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-072145
- **Related target files**: tests/agent/test_http_lifecycle.py