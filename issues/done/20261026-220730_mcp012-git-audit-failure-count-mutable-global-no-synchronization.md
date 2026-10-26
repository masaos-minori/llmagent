# _audit_failure_count mutable global without synchronization

## Priority
Medium

## Summary
The `_audit_failure_count` variable in `git_server.py` is a mutable global integer that is incremented without thread-safe synchronization, creating a race condition under concurrent requests.

## Background
The `_audit_failure_count` variable at line 160 of `git_server.py`:

```python
_audit_failure_count: int = 0
```

It is incremented in `_audit_log_safe` at line 169:

```python
except Exception:  # noqa: BLE001 — audit failure must never propagate
    _audit_failure_count += 1
    logger.error("audit_log failed: %s", kwargs.get("action", "unknown"))
```

And read in the health endpoint at line 363:

```python
"audit_failure_count": _audit_failure_count,
```

## Problem
The `_audit_failure_count += 1` operation is not atomic in Python. Under concurrent requests, multiple threads can read the same value, increment it, and write back the same result — losing increments. This is a classic TOCTOU (time-of-check-time-of-use) race condition.

For example:
1. Thread A reads `_audit_failure_count = 5`
2. Thread B reads `_audit_failure_count = 5`
3. Thread A writes `_audit_failure_count = 6`
4. Thread B writes `_audit_failure_count = 6` (should be 7)

The health endpoint then reports `6` instead of `7`, making monitoring unreliable.

Additionally, the variable is accessed from both the async handler (via `_audit_log_safe`) and the health endpoint without any synchronization, which means:
1. The health endpoint may see stale values due to Python's GIL not guaranteeing atomicity of compound operations.
2. The variable is not thread-safe even under CPython's GIL because `+=` involves a read-modify-write cycle.

## Reason for Change
A non-thread-safe counter makes monitoring unreliable and can lead to under-reporting of audit failures under concurrent load.

## Implementation Intent
Replace the mutable global integer with a thread-safe counter. Options include:
1. Use `threading.Lock` to protect the increment operation.
2. Use `atomicwrites` or `ctypes.c_int` for atomic operations.
3. Use `asyncio.Lock` if the server is single-threaded (uvicorn workers are single-threaded per worker).

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py` — `_audit_failure_count` (line 160), `_audit_log_safe` (line 169), health endpoint (line 363)

## Required Changes
- Replace `_audit_failure_count` with a thread-safe counter
- Protect the increment operation with a lock or use an atomic operation
- Document the synchronization strategy in a comment

## Constraints
- Must not change the existing counter semantics (increment on audit failure)
- Must preserve the health endpoint's ability to read the counter

## Acceptance Criteria
- Counter increments are not lost under concurrent load
- Health endpoint reads the correct counter value
- No performance regression from synchronization overhead

## Testing Expectations
- Concurrency test: verify counter increments are not lost under concurrent load
- Unit test: verify thread-safe increment operation
- Regression test: ensure existing counter behavior is preserved

## Documentation Impact
Document the synchronization strategy in a comment near `_audit_failure_count`.

## Out of Scope
- Changes to the audit log format itself
- Changes to how audit failures are detected

## Dependencies
N/A: none

## Unresolved Questions
- Is uvicorn running in single-worker mode (which would eliminate the need for thread safety)?
- Are there other MCP servers with the same pattern?

## AI Implementation Instruction
In `scripts/mcp_servers/git/git_server.py`, replace `_audit_failure_count` with a thread-safe counter. Do not modify any other MCP server's counter logic.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/git/git_server.py
