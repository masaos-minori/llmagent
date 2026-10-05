## Goal

Update `startup_mcp_starter.py` error handler to cover additional exception types after `retry_once_with_delay` preserves original exception types.

## Scope

- Modify `scripts/agent/startup_mcp_starter.py` line 88: update `except (OSError, RuntimeError) as e:` to handle broader exception types

## Assumptions

- The current handler catches `(OSError, RuntimeError)` because `RuntimeError` was previously raised by `retry_once_with_delay`
- After the retry helper change, callers may receive `TimeoutError`, `ConnectionRefusedError`, etc.

## Design decisions

- Broaden the exception handler to include common network-related exceptions: `TimeoutError`, `ConnectionRefusedError`, `ConnectionResetError`, `BrokenPipeError`
- Keep `OSError` in the handler since it covers many I/O errors including the above

## Alternatives considered

- Catching all `Exception` — too broad, masks unexpected errors
- Adding individual exception types one-by-one — fragile, requires constant updates

## Implementation
### Target file
`scripts/agent/startup_mcp_starter.py`

### Procedure
Broaden the exception handler to cover additional exception types that may now propagate from `retry_once_with_delay`.

### Method
1. Locate line 88 in `scripts/agent/startup_mcp_starter.py`
2. Change `except (OSError, RuntimeError) as e:` to `except (OSError, TimeoutError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as e:`

### Details
```python
# Before (line 88):
except (OSError, RuntimeError) as e:

# After:
except (OSError, TimeoutError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as e:
```

Note: `OSError` already covers `ConnectionRefusedError`, `ConnectionResetError`, and `BrokenPipeError` as subclasses. However, `TimeoutError` is not a subclass of `OSError` in Python 3.11+, so it must be listed separately. The explicit listing makes intent clear and avoids relying on inheritance relationships.

## Compatibility considerations

This change is backward-compatible — the handler now catches more exception types than before. No existing behavior is lost.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to `except (OSError, RuntimeError) as e:` if the retry helper change is reverted. This restores the previous narrow handling.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/startup_mcp_starter.py | Integration — verify error handling still works | uv run pytest tests/agent/test_startup_mcp_starter.py | Existing tests pass |

## Completion criteria

- [ ] Exception handler covers additional exception types (REQ-004)
- [ ] Existing tests pass after handler update

## Out of scope

- Modifying `retry_helper.py` (handled in separate document)
- Creating new test file (handled in separate document)

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Restored RuntimeError in the first-attempt except tuple (origin had removed it). Applied on top of origin/master. |
| 2 | Add or update tests per Validation plan | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261004-143000_rh001_retry_exception_type_masking.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182808_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-194143
- **Related target files**: scripts/agent/startup_mcp_starter.py