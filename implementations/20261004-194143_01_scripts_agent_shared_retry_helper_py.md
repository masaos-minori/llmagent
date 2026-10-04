## Goal

Preserve the original exception type when `retry_once_with_delay` fails on second attempt, instead of always wrapping in `RuntimeError`.

## Scope

- Modify `scripts/agent/shared/retry_helper.py` line 59: replace `raise RuntimeError(masked_msg) from retry_err` with `raise retry_err`
- Update callers that currently catch `RuntimeError` specifically (e.g., `startup_mcp_starter.py:88`)

## Assumptions

- Callers that currently catch `RuntimeError` will need to broaden their exception handlers to catch the specific exception types they care about
- The `_mask_secrets()` call should remain on the logged message even though we no longer wrap the exception

## Design decisions

- Replace `raise RuntimeError(masked_msg) from retry_err` with `raise retry_err` — minimal change that preserves exception type information
- Keep the masking on the log line; the raw exception string will be included via `str(retry_err)` in the traceback

## Alternatives considered

- Wrapping in a custom exception class — adds complexity without clear benefit for this use case
- Adding an exception type parameter to the retry helper — over-engineering for a single caller pattern

## Implementation
### Target file
`scripts/agent/shared/retry_helper.py`

### Procedure
Replace the second-failure path to re-raise the original exception instead of wrapping it in `RuntimeError`.

### Method
1. Locate line 59 in `scripts/agent/shared/retry_helper.py`
2. Change `raise RuntimeError(masked_msg) from retry_err` to `raise retry_err`
3. Ensure the logging statement above still uses `_mask_secrets()` for sensitive data

### Details
```python
# Before (line 59):
raise RuntimeError(masked_msg) from retry_err

# After:
raise retry_err
```

The logging statement immediately before this line should retain its `_mask_secrets()` call to protect sensitive data in logs.

## Compatibility considerations

Callers that currently catch `RuntimeError` specifically must be updated to handle the broader set of possible exception types. For example, `startup_mcp_starter.py:88` catches `(OSError, RuntimeError)` — after this change, it may also receive `TimeoutError`, `ConnectionRefusedError`, etc.

## Security considerations

N/A: No security impact. The `_mask_secrets()` call remains on the log line.

## Rollback considerations

Revert to `raise RuntimeError(masked_msg) from retry_err` if callers cannot be updated simultaneously. This would restore the previous behavior but lose exception type preservation.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/shared/retry_helper.py | Unit test — verify exception type propagation | uv run pytest tests/agent/test_retry_helper.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] Original exception type is preserved through retry (REQ-001)
- [ ] Test verifies `TimeoutError` remains `TimeoutError` after retry failure (REQ-002)
- [ ] Test verifies `ConnectionRefusedError` remains `ConnectionRefusedError` after retry failure (REQ-003)
- [ ] Existing callers reviewed for compatibility (REQ-004)

## Out of scope

- Changing retry count or delay behavior
- Adding exponential backoff
- Modifying `startup_mcp_starter.py` (handled in separate document)
- Creating new test file (handled in separate document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261004-143000_rh001_retry_exception_type_masking.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182808_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-194143
- **Related target files**: scripts/agent/shared/retry_helper.py
