## Goal

Enumerate `LifecycleProtocol`'s permitted exceptions as a named, importable tuple/type in `scripts/shared/tool_lifecycle.py`, covering `ServerCooldownError` and the `(OSError, RuntimeError)` set already used by `ToolExecutor`, with a docstring stating this is the closed set any `ensure_ready()` implementation may raise to be normalized into a `ToolCallResult`.

## Scope

- Add a constant tuple of permitted exception types to `tool_lifecycle.py`
- Update `LifecycleProtocol.ensure_ready()` docstring to reference the new constant
- No other files are modified in this row

## Assumptions

- The two exception types currently handled (`ServerCooldownError` and `(OSError, RuntimeError)`) are sufficient for all currently-read call paths; UNK-01's resolution during implementation will widen the tuple if a new type is found.
- `ServerCooldownError` subclasses `RuntimeError`, so including both covers the union.
- The constant will be a module-level `frozenset[type[Exception]]` or `tuple[type[Exception], ...]` for immutability.

## Design decisions

- Use `tuple[type[Exception], ...]` (not `set` or `frozenset`) for the exception-set constant, since tuples are hashable and can be used in `isinstance` checks via `__subclasscheck__` patterns.
- Name the constant `_PERMITTED_LIFECYCLE_EXCEPTIONS` (private prefix) since it is an internal contract, not a public API.
- Place the constant before `LifecycleProtocol` so callers can import it without circular dependencies.

## Alternatives considered

- Using a `@property` on `LifecycleProtocol` — rejected: adds unnecessary indirection for a simple constant.
- Defining a new `LifecycleException` base class — rejected: would require changing existing exception hierarchies and is out of scope.
- Using `typing.Protocol` with a `permitted_exceptions` attribute — rejected: over-engineers a simple constant.

## Implementation

### Target file

`scripts/shared/tool_lifecycle.py`

### Procedure

Add a module-level constant enumerating the closed set of permitted lifecycle exceptions, and update `LifecycleProtocol.ensure_ready()`'s docstring to reference it.

### Method

1. Define `_PERMITTED_LIFECYCLE_EXCEPTIONS: tuple[type[Exception], ...] = (ServerCooldownError, OSError, RuntimeError)` after the `ServerCooldownError` definition.
2. Add a docstring sentence to `LifecycleProtocol.ensure_ready()` stating: "May raise only exceptions listed in `_PERMITTED_LIFECYCLE_EXCEPTIONS`."

### Details

```python
# After ServerCooldownError class definition (line 10), add:

_PERMITTED_LIFECYCLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    ServerCooldownError,
    OSError,
    RuntimeError,
)

# In LifecycleProtocol.ensure_ready() docstring, add:

async def ensure_ready(self, server_key: str) -> None:
    """Ensure the MCP server identified by server_key is ready to accept calls.

    May raise only exceptions listed in _PERMITTED_LIFECYCLE_EXCEPTIONS.
    """
    ...
```

## Compatibility considerations

- Existing code that catches `ServerCooldownError` or `(OSError, RuntimeError)` individually continues to work unchanged.
- Callers can now check `isinstance(e, _PERMITTED_LIFECYCLE_EXCEPTIONS)` for uniform handling.
- No public API change — the constant is private (underscore-prefixed).

## Security considerations

- No security impact. This is a behavioral contract clarification, not a security boundary change.

## Rollback considerations

- Reverting this change removes the explicit exception-contract documentation but does not break existing behavior.
- If UNK-01 reveals additional exception types during implementation, the constant can be widened without breaking existing callers.

## Validation plan

- Unit: import `_PERMITTED_LIFECYCLE_EXCEPTIONS` from `shared.tool_lifecycle` and assert it contains exactly `(ServerCooldownError, OSError, RuntimeError)`.
- Regression: run `uv run pytest tests/shared/test_tool_executor.py tests/shared/test_tool_transport_invoker.py -v` to confirm no regression.
- Static analysis: `uv run ruff check scripts/shared/tool_lifecycle.py`, `uv run mypy scripts/shared/tool_lifecycle.py`.

## Completion criteria

- `_PERMITTED_LIFECYCLE_EXCEPTIONS` is defined as a `tuple[type[Exception], ...]` containing `(ServerCooldownError, OSError, RuntimeError)`.
- `LifecycleProtocol.ensure_ready()` docstring references `_PERMITTED_LIFECYCLE_EXCEPTIONS`.
- All existing tests continue to pass.
- No new lint/type errors introduced.

## Out of scope

- Changing which exceptions are caught in `invoke()` or `_ensure_lifecycle_ready()` — covered by REQ-002 (next row).
- Adding new exception types beyond the three confirmed ones — left to implementation-phase discovery (UNK-01).
- Modifying `docs/*.md` — deferred to REQ-011 (later phase).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add _PERMITTED_LIFECYCLE_EXCEPTIONS constant and update LifecycleProtocol docstring | Pending | — | — | |
| 2 | Add unit test for the constant | Pending | — | — | |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
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
- **Source issue**: issues/20260914-103159_mcpagent05_mcp-lifecycle-invocation-gate-unification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-123229_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/shared/tool_lifecycle.py
