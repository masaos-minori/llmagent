## Goal

Only remove tracking entries after confirmed process termination, preventing orphaned processes when shutdown fails.

## Implementation outcome

Deviation from procedure: no code change was performed. Origin/master already ships
this change in commit `10308ed7` (`manager.cleanup_server_key()` moved into the try
block after successful termination, tracking entry retained on failure). Validated
against current source: `tests/agent/test_http_lifecycle_shutdown_coordinator.py`
passes (2 passed). Accepting the upstream implementation and closing the workflow.

## Scope

- Modify `scripts/agent/http_lifecycle_shutdown_coordinator.py`: move `cleanup_server_key()` inside the try block so it only executes after successful termination
- Update warning log message to indicate tracking entry is kept on failure

## Assumptions

- `terminate_with_timeout()` raises an exception on failure rather than returning a status code
- The tracking entry removal is safe to defer until after successful termination

## Design decisions

- Move `manager.cleanup_server_key(server_key)` from the except block into the try block, after the termination call
- Keep the tracking entry intact on failure so subsequent cleanup attempts can target the process

## Alternatives considered

- Adding a return value to `terminate_with_timeout()` indicating success/failure — changes public API
- Using a flag variable to track termination status — more complex, harder to reason about

## Implementation
### Target file
`scripts/agent/http_lifecycle_shutdown_coordinator.py`

### Procedure
Move the `cleanup_server_key()` call inside the try block so it only executes after successful termination. On failure, keep the tracking entry intact so subsequent cleanup attempts can target the process.

### Method
1. Locate lines 97-111 in `scripts/agent/http_lifecycle_shutdown_coordinator.py`
2. Move `manager.cleanup_server_key(server_key)` from line 111 (except block) to after line 97 (try block, after termination)
3. Update the warning log message in the except block to indicate tracking entry is kept

### Details
```python
# Before (lines 97-111):
try:
    await manager.terminate_with_timeout(server_key, timeout)
except Exception as e:
    logger.warning(f"Failed to terminate {server_key}: {e}")
    manager.cleanup_server_key(server_key)

# After:
try:
    await manager.terminate_with_timeout(server_key, timeout)
    manager.cleanup_server_key(server_key)
except Exception as e:
    logger.warning(f"Failed to terminate {server_key}: {e} — tracking entry retained for retry")
```

The key change is moving `cleanup_server_key()` from the except block into the try block, after the termination call. This ensures tracking data is only removed after confirmed process termination.

## Compatibility considerations

Callers that expect tracking entry to be removed even on failure may need updates. However, keeping the tracking entry is generally safer — it allows subsequent cleanup attempts to find and target the process.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to the original placement of `cleanup_server_key()` in the except block if callers depend on immediate tracking removal. This would restore the previous behavior but reintroduce orphaned process risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Unit test — verify cleanup ordering | uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] Tracking data is removed only after confirmed process termination (REQ-001)
- [ ] Failed termination leaves tracking entry intact for retry (REQ-002)
- [ ] All new tests pass when run individually

## Out of scope

- Changes to `ProcessTerminator.terminate_with_timeout()` itself
- Changes to `cleanup_server_key()` implementation
- Creating new test file (handled in separate document)

## execution Status

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261004-143001_sc002_tracking_data_cleanup_on_failure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-194347
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py
