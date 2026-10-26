# _audit_log_safe swallows SystemExit and KeyboardInterrupt in git-mcp

## Priority
High

## Summary
The `_audit_log_safe` wrapper in `git_server.py` catches all exceptions including `SystemExit` and `KeyboardInterrupt`, which can mask fatal signals during audit logging.

## Background
All MCP servers use `_audit_log` from `mcp_servers.audit` to record operation outcomes. The git-mcp server wraps this in `_audit_log_safe` (line 163 of `git_server.py`) to prevent audit failures from masking the original response. However, the broad `except Exception` clause does not exclude `SystemExit` or `KeyboardInterrupt`.

## Problem
When `_audit_log` raises `SystemExit` or `KeyboardInterrupt` inside `_audit_log_safe`, these exceptions are caught by the `except Exception` block (line 168), incremented into `_audit_failure_count`, and logged as a generic error. The original signal is lost — the process continues running when it should terminate.

This is particularly dangerous because:
1. `SystemExit` may be raised by the security posture gate or other shutdown paths.
2. `KeyboardInterrupt` may be raised by uvicorn during graceful shutdown.
3. Both are caught silently, incrementing `_audit_failure_count` (a mutable global at line 160) instead of propagating.

## Reason for Change
A silent swallow of `SystemExit`/`KeyboardInterrupt` during audit logging can cause the server to continue operating after a shutdown signal, leading to resource leaks, orphaned connections, and inconsistent state.

## Implementation Intent
Replace the broad `except Exception` in `_audit_log_safe` with explicit exception types that should be caught (e.g., `OSError`, `IOError`, `RuntimeError`). Allow `SystemExit` and `KeyboardInterrupt` to propagate.

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py` — `_audit_log_safe` function (lines 163-170)

## Required Changes
- Replace `except Exception:` with `except (OSError, IOError, RuntimeError):` in `_audit_log_safe`
- Ensure `SystemExit` and `KeyboardInterrupt` propagate through `_audit_log_safe`
- Verify no other MCP server has the same pattern

## Constraints
- Must not change the fail-closed semantics of audit logging (audit failure must never mask the original response)
- Must preserve `_audit_failure_count` tracking for recoverable errors

## Acceptance Criteria
- `SystemExit` raised by `_audit_log` propagates through `_audit_log_safe`
- `KeyboardInterrupt` raised by `_audit_log` propagates through `_audit_log_safe`
- Recoverable errors (OSError, IOError, RuntimeError) are still caught and logged
- `_audit_failure_count` is still incremented for recoverable errors

## Testing Expectations
- Unit test: verify `_audit_log_safe` propagates `SystemExit`
- Unit test: verify `_audit_log_safe` propagates `KeyboardInterrupt`
- Unit test: verify `_audit_log_safe` catches `OSError` and increments `_audit_failure_count`

## Documentation Impact
Update `_audit_log_safe` docstring to document which exceptions are caught vs propagated.

## Out of Scope
- Changes to `_audit_log` itself
- Changes to `_audit_failure_count` synchronization

## Dependencies
N/A: none

## Unresolved Questions
- Should `_audit_failure_count` be a thread-safe counter?
- Does any other MCP server have the same pattern?

## AI Implementation Instruction
Modify `_audit_log_safe` in `scripts/mcp_servers/git/git_server.py` to replace `except Exception:` with `except (OSError, IOError, RuntimeError):`. Do not modify any other MCP server's audit logic.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/git/git_server.py
