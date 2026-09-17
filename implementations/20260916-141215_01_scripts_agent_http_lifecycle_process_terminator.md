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

`scripts/shared/mcp_config.py` (add `fields` field to `McpServerConfig`)
`scripts/agent/http_lifecycle.py` (merge `cfg.fields` into Popen kwargs in `_create_and_validate_proc`)

### Procedure

1. Add `fields: dict[str, Any] = field(default_factory=dict)` to `McpServerConfig` in `scripts/shared/mcp_config.py`.
2. In `scripts/agent/http_lifecycle.py`, locate `_create_and_validate_proc()` method.
3. After the existing `subprocess.Popen()` call, merge `cfg.fields` into the Popen kwargs before passing them.
4. Update the docstring of `_create_and_validate_proc()` to document the new behavior.

### Method

Current `McpServerConfig` class fields (in `scripts/shared/mcp_config.py`):
```python
class McpServerConfig:
    transport: TransportType
    url: str
    startup_mode: StartupMode = StartupMode.NONE
    ...
    env: dict[str, str] = field(default_factory=dict)
    key: str = field(default="", compare=False, repr=False)
    ...
```

Required update — add `fields` field after `env`:
```python
    fields: dict[str, Any] = field(default_factory=dict)
```

Current `_create_and_validate_proc()` method (approximate location in `http_lifecycle.py`):
```python
async def _create_and_validate_proc(
    self,
    server_key: str,
    cfg: McpServerConfig,
) -> tuple[subprocess.Popen[bytes], IO[bytes]]:
    ...
    proc = subprocess.Popen(
        cfg.cmd,
        stdout=subprocess.DEVNULL,
        stderr=stderr_fh,
        env=env,
        start_new_session=True,
    )
```

Required update — merge `cfg.fields` into Popen kwargs:
```python
    popen_kwargs: dict[str, Any] = {
        "stdout": subprocess.DEVNULL,
        "stderr": stderr_fh,
        "env": env,
        "start_new_session": True,
    }
    if cfg.fields:
        popen_kwargs.update(cfg.fields)
    proc = subprocess.Popen(cfg.cmd, **popen_kwargs)
```

### Details

The `fields` field should be added as a dataclass field on `McpServerConfig` after `env`. The merging logic in `_create_and_validate_proc()` should use `dict.update()` to avoid mutating the original `cfg.fields` dict. The `popen_kwargs` variable should be initialized as a regular dict before the merge to ensure it always exists.

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
| `scripts/shared/mcp_config.py` | Code quality | `uv run ruff check scripts/shared/mcp_config.py` | Clean |
| `scripts/agent/http_lifecycle.py` | Code quality | `uv run ruff check scripts/agent/http_lifecycle.py` | Clean |
| `scripts/shared/mcp_config.py` | Type checking | `uv run mypy scripts/shared/mcp_config.py` | Clean |
| `scripts/agent/http_lifecycle.py` | Type checking | `uv run mypy scripts/agent/http_lifecycle.py` | Clean |
| `tests/agent/test_http_lifecycle_integration.py` | Regression tests | `uv run pytest tests/agent/test_http_lifecycle_integration.py -v` | All pass |

## Completion criteria

- `McpServerConfig` has a `fields` field accepting additional keyword arguments for subprocess creation.
- `scripts/agent/http_lifecycle.py`'s `_create_and_validate_proc()` merges `cfg.fields` into Popen kwargs.
- `uv run ruff check scripts/shared/mcp_config.py scripts/agent/http_lifecycle.py` passes clean.
- `uv run mypy scripts/shared/mcp_config.py scripts/agent/http_lifecycle.py` passes clean.
- `uv run pytest tests/agent/test_http_lifecycle_integration.py -v` passes all tests.

## Out of scope

- Adding `fields` support to other lifecycle methods — handled in the next procedure document (REQ-002).
- Adding `fields` support to non-HTTP MCP servers — out of scope for this specific change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260917-124413 | 20260917-124413 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260917-124419 | 20260917-124419 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260917-124425 | 20260917-124425 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-124431 | 20260917-124431 |  |

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
- **Related target files**: scripts/shared/mcp_config.py, scripts/agent/http_lifecycle.py