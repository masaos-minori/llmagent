## Goal

Add `fields` parameter support to `ShutdownCoordinator.shutdown_all()`'s process termination logic — specifically, wire through the `fields` argument from the MCP server config into `ProcessTerminator.terminate_with_timeout()` for the shutdown path.

## Scope

- Add `fields` parameter to `shutdown_all()` method signature.
- Pass `fields` to `terminate_with_timeout()` call within `shutdown_all()`.
- Update docstring to document the new parameter.

## Assumptions

- The `shutdown_all()` method currently exists in `scripts/agent/http_lifecycle_shutdown_coordinator.py`.
- The `fields` field is available on the MCP server config object.
- `ProcessTerminator.terminate_with_timeout()` accepts additional keyword arguments via `**kwargs`.

## Design decisions

- Add `fields` as an optional positional parameter to match existing `shutdown_all()` signature style.
- Use `**kwargs` pattern to pass any extra fields to `terminate_with_timeout()` rather than hardcoding specific keys.
- Do not change the default behavior — `fields` defaults to empty dict `{}`.

## Alternatives considered

- Adding `fields` only to specific shutdown scenarios — rejected because the Plan's intent is to add general `fields` support for all shutdown paths.

## Implementation
### Target file

`scripts/agent/http_lifecycle_shutdown_coordinator.py`

### Procedure

1. Locate the `shutdown_all()` method in `ShutdownCoordinator`.
2. Add `fields: dict[str, Any] | None = None` parameter to the method signature.
3. Convert the positional timeout argument to a keyword argument and merge `fields` into the terminate kwargs before calling `terminate_with_timeout()`.
4. Update the docstring to document the new parameter.

### Method

Current `shutdown_all()` method signature (in `http_lifecycle_shutdown_coordinator.py`):
```python
async def shutdown_all(
    self,
    manager: HttpServerLifecycleManager,
    terminator: ProcessTerminator | None = None,
) -> None:
    """Gracefully shut down every managed server."""
```

Inside the loop body:
```python
await terminator.terminate_with_timeout(proc, server_key, _SHUTDOWN_TIMEOUT_SEC)
```

Required update — add `fields` parameter and convert timeout to keyword arg:
```python
async def shutdown_all(
    self,
    manager: HttpServerLifecycleManager,
    terminator: ProcessTerminator | None = None,
    fields: dict[str, Any] | None = None,
) -> None:
    """Gracefully shut down every managed server.
    
    Args:
        manager: The lifecycle manager owning the processes.
        terminator: Optional terminator instance; falls back to manager's.
        fields: Additional keyword arguments to pass to each
            ``terminate_with_timeout()`` call. If None, defaults to
            an empty dict.
    """
```

Inside the loop body (after `terminator = terminator or manager._process_terminator`):
```python
# Merge fields into terminate kwargs
terminate_kwargs: dict[str, Any] = {
    "timeout": _SHUTDOWN_TIMEOUT_SEC,
}
if fields:
    terminate_kwargs.update(fields)
await terminator.terminate_with_timeout(proc, server_key, **terminate_kwargs)
```

### Details

The `fields` parameter should be added as the last parameter in the method signature. The merging logic should use `dict.update()` to avoid mutating the original `fields` dict. The `terminate_kwargs` variable should be initialized before the merge to ensure it always exists. The `timeout` key must be set first so that `fields` can override it if desired.

## Compatibility considerations

- Adding an optional parameter with a default value maintains backward compatibility.
- Existing callers that don't pass `fields` will continue to work unchanged.
- The `**kwargs` pattern means any valid `terminate_with_timeout` kwarg can be passed through without code changes.

## Security considerations

- No security impact — `fields` passes through to `terminate_with_timeout()` which already validates its arguments.
- The `**kwargs` pattern does not introduce new attack surfaces since `terminate_with_timeout()` itself validates input.

## Rollback considerations

- If the `fields` parameter causes issues, simply remove it from the signature and the merge logic. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | Code quality | `uv run ruff check scripts/agent/http_lifecycle_shutdown_coordinator.py` | Clean |
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | Type checking | `uv run mypy scripts/agent/http_lifecycle_shutdown_coordinator.py` | Clean |
| `tests/agent/test_http_lifecycle_shutdown_coordinator.py` | Regression tests | `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -v` | All pass |

## Completion criteria

- `scripts/agent/http_lifecycle_shutdown_coordinator.py`'s `shutdown_all()` method accepts a `fields` parameter.
- `uv run ruff check scripts/agent/http_lifecycle_shutdown_coordinator.py` passes clean.
- `uv run mypy scripts/agent/http_lifecycle_shutdown_coordinator.py` passes clean.
- `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -v` passes all tests.

## Out of scope

- Adding `fields` support to health checker startup — handled in the next procedure document (REQ-003).
- Adding `fields` support to non-HTTP lifecycle methods — out of scope for this specific change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260917-124924 | 20260917-124924 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260917-124930 | 20260917-124930 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260917-124936 | 20260917-124936 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-124942 | 20260917-124942 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260915-102515_refactor_http_lifecycle_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-141215_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-141215
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py