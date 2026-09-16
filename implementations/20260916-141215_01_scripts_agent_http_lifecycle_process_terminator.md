## Goal

Add `fields` parameter support to `HttpServerLifecycleManager.start()`'s subprocess creation logic — specifically, wire through the `fields` argument from the MCP server config into `subprocess.Popen()` for the HTTP-based MCP servers.

## Scope

- Add `fields` parameter to `start()` method signature.
- Pass `fields` to `subprocess.Popen()` call within `start()`.
- Update docstring to document the new parameter.

## Assumptions

- The `start()` method currently exists in `scripts/agent/http_lifecycle.py`.
- The `fields` field is available on the MCP server config object.
- `subprocess.Popen()` accepts additional keyword arguments via `**kwargs`.

## Design decisions

- Add `fields` as an optional positional parameter to match existing `start()` signature style.
- Use `**kwargs` pattern to pass any extra fields to `Popen()` rather than hardcoding specific keys.
- Do not change the default behavior — `fields` defaults to empty dict `{}`.

## Alternatives considered

- Adding `fields` only to specific server types — rejected because the Plan's intent is to add general `fields` support for all HTTP-based MCP servers.

## Implementation
### Target file

`scripts/agent/http_lifecycle_process_terminator.py`

### Procedure

1. Locate the `start()` method in `HttpServerLifecycleManager`.
2. Add `fields: dict[str, Any] | None = None` parameter to the method signature.
3. Inside the method, merge `fields` into the Popen kwargs before calling `subprocess.Popen()`.
4. Update the docstring to document the new parameter.

### Method

Current `start()` method signature (approximate location in `http_lifecycle.py`):
```python
async def start(self, server_key: str, command: list[str], ...) -> None:
    ...
    proc = subprocess.Popen(command, ...)
```

Required update:
```python
async def start(
    self,
    server_key: str,
    command: list[str],
    ...,
    fields: dict[str, Any] | None = None,
) -> None:
    """Start an HTTP-based MCP server subprocess.
    
    Args:
        server_key: Unique identifier for the server.
        command: Command to execute for the MCP server.
        fields: Additional keyword arguments to pass to subprocess.Popen().
            If None, defaults to an empty dict.
    """
    ...
    popen_kwargs: dict[str, Any] = {}
    if fields:
        popen_kwargs.update(fields)
    proc = subprocess.Popen(command, **popen_kwargs)
```

### Details

The `fields` parameter should be added as the last parameter in the method signature. The merging logic should use `dict.update()` to avoid mutating the original `fields` dict. The `popen_kwargs` variable should be initialized before the merge to ensure it always exists.

## Compatibility considerations

- Adding an optional parameter with a default value maintains backward compatibility.
- Existing callers that don't pass `fields` will continue to work unchanged.
- The `**kwargs` pattern means any valid `Popen` kwarg can be passed through without code changes.

## Security considerations

- No security impact — `fields` passes through to `Popen()` which already validates its arguments.
- The `**kwargs` pattern does not introduce new attack surfaces since `Popen()` itself validates input.

## Rollback considerations

- If the `fields` parameter causes issues, simply remove it from the signature and the merge logic. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle_process_terminator.py` | Code quality | `uv run ruff check scripts/agent/http_lifecycle_process_terminator.py` | Clean |
| `scripts/agent/http_lifecycle_process_terminator.py` | Type checking | `uv run mypy scripts/agent/http_lifecycle_process_terminator.py` | Clean |
| `tests/agent/test_http_lifecycle_process_terminator.py` | Regression tests | `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py -v` | All pass |

## Completion criteria

- `scripts/agent/http_lifecycle_process_terminator.py`'s `start()` method accepts a `fields` parameter.
- `uv run ruff check scripts/agent/http_lifecycle_process_terminator.py` passes clean.
- `uv run mypy scripts/agent/http_lifecycle_process_terminator.py` passes clean.
- `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py -v` passes all tests.

## Out of scope

- Adding `fields` support to other lifecycle methods — handled in the next procedure document (REQ-002).
- Adding `fields` support to non-HTTP MCP servers — out of scope for this specific change.

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
- **Source issue**: issues/20260915-102515_refactor_http_lifecycle_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-141215_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-141215
- **Related target files**: scripts/agent/http_lifecycle_process_terminator.py
