# web_search_server.py broad except Exception in call_tool endpoint

## Priority
Medium

## Summary
The `call_tool` endpoint in `web_search_server.py` catches `Exception` broadly (line 293) and re-raises it after setting `error_type = "unexpected_error"`, which masks the actual exception type and makes debugging difficult.

## Background
The `call_tool` endpoint in `web_search_server.py` (lines 244-310) handles tool dispatch with specific exception handlers:

```python
except WebSearchUpstreamError as e:
    ...
    raise
except BrowserAuthorizationError:
    ...
    raise
except Exception:
    outcome = "error"
    error_type = "unexpected_error"
    latency_ms = (time.perf_counter() - t0) * 1000
    raise
```

The `finally` block (lines 298-310) always fires and logs the audit entry regardless of whether an exception was raised.

## Problem
The `except Exception` clause at line 293 catches ALL non-specific exceptions, including:
1. `RuntimeError` — could indicate configuration errors, missing dependencies, or unexpected state
2. `ValueError` — could indicate malformed input or data corruption
3. `TypeError` — could indicate type mismatches in the dispatch table
4. `ImportError` — could indicate missing dependencies
5. Any other unexpected exception

While the exception is re-raised (so the HTTP response is still correct), the `error_type` is always `"unexpected_error"` regardless of the actual exception type. This means:
1. The audit log loses information about the actual failure mode.
2. Monitoring/alerting systems cannot distinguish between different types of failures.
3. Debugging requires tracing through the stack trace rather than reading the audit log.

Additionally, the `finally` block always fires even when an exception is raised, which means the audit log records both the specific error type (from the `except` handler) AND the generic `"unexpected_error"` type (from the `finally` block). This creates duplicate/conflicting audit entries.

## Reason for Change
The broad `except Exception` clause masks the actual exception type, making it impossible to distinguish between different failure modes in the audit log. This reduces observability and makes debugging harder.

## Implementation Intent
Replace the broad `except Exception` with specific exception types that should be caught, or remove the catch entirely and let the exception propagate naturally. If catching is necessary, use a more specific exception type.

## Target Files or Areas
- `scripts/mcp_servers/web_search/web_search_server.py` — `call_tool` endpoint (lines 244-310)

## Required Changes
- Replace `except Exception:` with specific exception types (e.g., `except (RuntimeError, ValueError, TypeError):`)
- Or remove the catch entirely and let all exceptions propagate
- Ensure the audit log captures the actual exception type, not just `"unexpected_error"`

## Constraints
- Must not change the HTTP response behavior (exceptions should still result in appropriate HTTP status codes)
- Must preserve the audit logging behavior

## Acceptance Criteria
- Audit log captures the actual exception type, not just `"unexpected_error"`
- Specific exception types are handled differently in the audit log
- No silent swallowing of exceptions

## Testing Expectations
- Unit test: verify specific exception types are captured in audit log
- Integration test: verify audit log distinguishes between different failure modes
- Regression test: ensure existing exception handling behavior is preserved

## Documentation Impact
Update `call_tool` docstring to document the exception handling strategy.

## Out of Scope
- Changes to the audit log format itself
- Changes to how `WebSearchUpstreamError` subclasses are handled

## Dependencies
N/A: none

## Unresolved Questions
- Should the `finally` block skip audit logging when an exception is raised (since the specific handler already logged it)?
- Is there a risk of double-audit entries when both the `except` handler and `finally` block fire?

## AI Implementation Instruction
In `scripts/mcp_servers/web_search/web_search_server.py`, replace `except Exception:` with specific exception types in the `call_tool` endpoint. Do not modify any other MCP server's exception handling.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py
