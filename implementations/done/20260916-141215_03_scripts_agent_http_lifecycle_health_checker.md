## Goal

Add `fields` parameter support to `HealthChecker.startup_poll()`'s HTTP request logic — specifically, wire through the `fields` argument from the MCP server config into `httpx.AsyncClient()` for the health check path.

## Scope

- Add `fields` parameter to `startup_poll()` method signature.
- Pass `fields` to `httpx.AsyncClient()` call within `startup_poll()`.
- Update docstring to document the new parameter.

## Assumptions

- The `startup_poll()` method currently exists in `scripts/agent/http_lifecycle_health_checker.py`.
- The `fields` field is available on the MCP server config object.
- `httpx.AsyncClient()` accepts additional keyword arguments via `**kwargs`.

## Design decisions

- Add `fields` as an optional positional parameter to match existing `startup_poll()` signature style.
- Use `**kwargs` pattern to pass any extra fields to `AsyncClient()` rather than hardcoding specific keys.
- Do not change the default behavior — `fields` defaults to empty dict `{}`.

## Alternatives considered

- Adding `fields` only to specific health check scenarios — rejected because the Plan's intent is to add general `fields` support for all health check paths.

## Implementation
### Target file

`scripts/agent/http_lifecycle_health_checker.py`

### Procedure

1. Locate the `startup_poll()` method in `HealthChecker`.
2. Add `fields: dict[str, Any] | None = None` parameter to the method signature.
3. Inside the method, merge `fields` into the AsyncClient kwargs before calling `httpx.AsyncClient()`.
4. Update the docstring to document the new parameter.

### Method

Current `startup_poll()` method signature (approximate location in `http_lifecycle_health_checker.py`):
```python
@staticmethod
async def startup_poll(
    server_key: str,
    cfg: object,
    *,
    max_retries: int = _STARTUP_MAX_RETRIES,
    interval: float = _STARTUP_INTERVAL,
    url: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> bool:
    """Poll until the server becomes healthy or *max_retries* expires."""
```

Required update:
```python
@staticmethod
async def startup_poll(
    server_key: str,
    cfg: object,
    *,
    max_retries: int = _STARTUP_MAX_RETRIES,
    interval: float = _STARTUP_INTERVAL,
    url: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    fields: dict[str, Any] | None = None,
) -> bool:
    """Poll until the server becomes healthy or *max_retries* expires.
    
    Args:
        server_key: Unique identifier for the server.
        cfg: Configuration object with health_url attribute.
        max_retries: Maximum number of retry attempts.
        interval: Time between retries in seconds.
        url: Optional override URL for the health check endpoint.
        timeout: Timeout for individual health check requests.
        fields: Additional keyword arguments to pass to
            ``httpx.AsyncClient()``. If None, defaults to an
            empty dict.
    """
```

Inside the method (before `async with httpx.AsyncClient(timeout=timeout)`):
```python
# Merge fields into client kwargs
client_kwargs: dict[str, Any] = {"timeout": timeout}
if fields:
    client_kwargs.update(fields)
async with httpx.AsyncClient(**client_kwargs) as client:
```

### Details

The `fields` parameter should be added as the last parameter in the method signature. The merging logic should use `dict.update()` to avoid mutating the original `fields` dict. The `client_kwargs` variable should be initialized before the merge to ensure it always exists.

## Compatibility considerations

- Adding an optional parameter with a default value maintains backward compatibility.
- Existing callers that don't pass `fields` will continue to work unchanged.
- The `**kwargs` pattern means any valid `AsyncClient` kwarg can be passed through without code changes.

## Security considerations

- No security impact — `fields` passes through to `AsyncClient()` which already validates its arguments.
- The `**kwargs` pattern does not introduce new attack surfaces since `AsyncClient()` itself validates input.

## Rollback considerations

- If the `fields` parameter causes issues, simply remove it from the signature and the merge logic. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle_health_checker.py` | Code quality | `uv run ruff check scripts/agent/http_lifecycle_health_checker.py` | Clean |
| `scripts/agent/http_lifecycle_health_checker.py` | Type checking | `uv run mypy scripts/agent/http_lifecycle_health_checker.py` | Clean |
| `tests/agent/test_http_lifecycle_health_checker.py` | Regression tests | `uv run pytest tests/agent/test_http_lifecycle_health_checker.py -v` | All pass |

## Completion criteria

- `scripts/agent/http_lifecycle_health_checker.py`'s `startup_poll()` method accepts a `fields` parameter.
- `uv run ruff check scripts/agent/http_lifecycle_health_checker.py` passes clean.
- `uv run mypy scripts/agent/http_lifecycle_health_checker.py` passes clean.
- `uv run pytest tests/agent/test_http_lifecycle_health_checker.py -v` passes all tests.

## Out of scope

- Adding `fields` support to shutdown coordinator — handled in the previous procedure document (REQ-002).
- Adding `fields` support to process terminator — handled in the previous procedure document (REQ-001).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260917-125316 | 20260917-125316 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260917-125322 | 20260917-125322 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260917-125329 | 20260917-125329 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-125336 | 20260917-125336 |  |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260915-102515_refactor_http_lifecycle_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-141215_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-141215
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py