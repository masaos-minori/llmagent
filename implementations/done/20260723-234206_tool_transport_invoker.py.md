## Goal

Wrap `ensure_ready()` call in `ToolTransportInvoker.invoke()` with try-except to catch `ServerCooldownError` and display meaningful cooldown message instead of letting it propagate silently.

## Scope

**In-Scope**:
- Add try-except for `ServerCooldownError` around `ensure_ready()` call in `invoke()` method

**Out-of-Scope**:
- Modifying `tool_executor.py` (already catches `RuntimeError` which includes `ServerCooldownError`)
- Changing `_COOLDOWN_SECONDS` duration
- Adding new configuration options

## Assumptions

1. The existing code at `tool_transport_invoker.py:192` (`await self._lifecycle.ensure_ready(server_key)`) correctly invokes the lifecycle check.
2. `ServerCooldownError(RuntimeError)` will be caught by existing `except (OSError, RuntimeError)` handlers in `tool_executor.py`.

## Design decisions

- **Use `try-except ServerCooldownError` specifically**: More precise than catching generic `RuntimeError` — only catches cooldown-related errors, not unrelated runtime errors.
- **Log warning + return error result**: Consistent with existing error handling pattern in this method (see `_transport_missing_msg` path).
- **Set `error_type="transport"`**: Matches the error type used in other transport-level failures in this method.

## Alternatives considered

- **Catch generic `RuntimeError`**: Would work but would also catch unrelated runtime errors. Chose specific exception type for precision.
- **Return sentinel value instead of raising**: Would require changing all callers. Raised exception approach chosen because it makes failure explicit at call site.
- **Add new method like `ensure_ready_or_cooldown()`**: Would add API surface. Chose minimal change — just wrap existing call.

## Implementation

### Target file

`scripts/shared/tool_transport_invoker.py`

### Procedure

1. **Import `ServerCooldownError` (~line 1)**
   - [ ] Add import near top of file alongside other imports from factory module:
     ```python
     from scripts.agent.factory import AgentContext, ServerCooldownError
     ```
   - [ ] Note: Verify current import statement from factory module exists and append `ServerCooldownError` to existing import

2. **Wrap `ensure_ready()` call with try-except (~lines 191-192)**
   - [ ] Change lines 191-192 from:
     ```python
     if self._lifecycle is not None:
         await self._lifecycle.ensure_ready(server_key)
     ```
     To:
     ```python
     if self._lifecycle is not None:
         try:
             await self._lifecycle.ensure_ready(server_key)
         except ServerCooldownError as e:
             msg = str(e)
             logger.warning(msg)
             return self._error_result(server_key, msg, error_type="transport")
     ```

### Method

- Read-only analysis of current source code structure
- Identify insertion points for import and try-except block
- Determine correct variable access paths

### Details

- Insertion point for import: Top of file, alongside existing imports from `scripts.agent.factory`
- Insertion point for try-except: After line 191, wrapping line 192
- Variable access: `self._lifecycle.ensure_ready(server_key)` — same as current code
- Error message format: `str(e)` uses the message set in `ServerCooldownError` constructor
- No new variables needed — `msg` reuses local variable name consistent with other error paths

## Compatibility considerations

- No API surface changes — only adds internal state tracking
- Existing behavior unchanged for non-cooldown cases
- Exception hierarchy preserved — subclasses of `RuntimeError` are caught by existing handlers in `tool_executor.py`

## Security considerations

- No security impact — only adds error message formatting
- No sensitive data exposure

## Rollback considerations

- Simple additions — easy to revert by removing the try-except block and restoring original code
- No state changes or side effects

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `ruff format scripts/ && ruff check scripts/ --fix && ruff check scripts/` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Architecture | `lint-imports` | 0 violations |
| Security | `bandit -r scripts/ -c pyproject.toml` | no HIGH unaddressed |
| Tests | `pytest` | all pass |
| Coverage | `diff-cover coverage.xml --compare-branch=main` | ≥ 90% on changed lines |
| Pre-commit | `pre-commit run --all-files` | pass |

## Out of scope

- Unit tests for the new exception handling (separate test creation task)
- Changes to tool_executor.py (covered in separate document)
- Integration testing with actual MCP subprocess failures

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-225955_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-234206
- Related target files: scripts/shared/tool_transport_invoker.py
