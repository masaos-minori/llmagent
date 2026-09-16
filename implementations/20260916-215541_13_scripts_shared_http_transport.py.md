## Goal

Rework `HttpTransport.call()`'s retry loop: increasing-exponential wait computed from `attempt` (not remaining attempts), sleep gated on `attempt < self._RETRY_MAX - 1`, and a `last_retryable_status` variable threaded into the exhaustion diagnostic. Replace the `HTTPStatusError` branch's raw-body `detail` string with the sanitized status-code/request-id form. Call the new redaction helper on `http_transport.py`'s module-level logger. Register the transport's auth token as a secret via `register_secret()`.

## Scope

- Modify `HttpTransport.call()` retry loop (lines 106-150).
- Modify `http_transport.py`'s module-level logger initialization (line 15).
- Modify `HttpTransport.__init__` to call `register_secret()` when an auth token is configured.

## Assumptions

- The corrected backoff formula is `2 ** attempt` for `attempt in {0, 1}` yielding delays `1, 2` (increasing exponential).
- Sleep should only occur when `attempt < self._RETRY_MAX - 1` (i.e., another attempt will follow).
- `e.response.headers.get("x-request-id", "")` safely extracts the request ID even when absent.
- The new `attach_redaction_filter()` helper exists (covered in previous row).

## Design decisions

- Use `last_retryable_status: int | None` variable set on every retryable-status branch iteration.
- Extract the exhaustion-diagnostic construction into a small private helper method rather than inlining more branches into `call()` (mitigates the cyclomatic complexity risk noted in the Plan's Risks section).
- Name the helper `_build_exhaustion_message()` per UNK-01 resolution.

## Alternatives considered

- Inlining the exhaustion diagnostic builder directly in the `else:` clause — rejected: increases cyclomatic complexity beyond grade C.
- Using a separate class for the diagnostic builder — rejected: over-engineers a simple string construction.

## Implementation

### Target file

`scripts/shared/http_transport.py`

### Procedure

1. Attach the redaction filter to `http_transport.py`'s module-level logger.
2. Register the auth token as a secret in `HttpTransport.__init__`.
3. Rework the retry loop: increasing-exponential wait, sleep gating, last retryable status tracking.
4. Replace the `HTTPStatusError` branch's raw-body detail with sanitized fields.
5. Thread `last_retryable_status` into the exhaustion diagnostic.

### Method

- **Step 1** (REQ-006): After line 15 (`logger = logging.getLogger(__name__)`):

```python
# Line 15 (unchanged):
logger = logging.getLogger(__name__)

# After line 15:
from shared.logger import attach_redaction_filter, register_secret  # REQ-006

# After the logger assignment:
attach_redaction_filter(logger)  # REQ-006
```

- **Step 2** (REQ-007): In `HttpTransport.__init__`, after setting `self._auth_token`:

```python
# After setting self._auth_token (around line 30):
if self._auth_token:
    register_secret(self._auth_token)  # REQ-007
```

- **Step 3** (REQ-001, REQ-002, REQ-003): Rework the retry loop:

```python
# Before (lines 106-150):
for attempt in range(self._RETRY_MAX):
    try:
        resp = await self._http.post(...)
        if resp.status_code in self._RETRYABLE_STATUS:
            wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
            logger.warning(...)
            await asyncio.sleep(wait_sec)
            continue
        ...
    except httpx.HTTPStatusError as e:
        last_exc = self._transport_error(
            name, "[HTTPStatusError]", f"status={e.response.status_code} response={e.response.text[:300]!r}",
            break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
            health_check=False,
        )
    ...
else:
    msg = f"[Retry exhausted] tool={name} url={self._base_url} after {self._RETRY_MAX} attempts: {last_exc}"
    logger.error(msg)
    raise TransportError(msg)

# After:
last_retryable_status: int | None = None
for attempt in range(self._RETRY_MAX):
    try:
        resp = await self._http.post(...)
        if resp.status_code in self._RETRYABLE_STATUS:
            last_retryable_status = resp.status_code  # REQ-003
            wait_sec = 2 ** attempt  # REQ-001: 1, 2 (increasing)
            logger.warning(...)
            if attempt < self._RETRY_MAX - 1:  # REQ-002: no sleep after final attempt
                await asyncio.sleep(wait_sec)
            continue
        ...
    except httpx.HTTPStatusError as e:
        req_id = e.response.headers.get("x-request-id", "")  # REQ-004/UNK-02
        detail = f"status={e.response.status_code} request_id={req_id!r}"  # REQ-004
        last_exc = self._transport_error(name, "[HTTPStatusError]", detail, ...)
        if e.response.status_code in self._RETRYABLE_STATUS:
            last_retryable_status = e.response.status_code  # REQ-003
    ...
else:
    # REQ-003/REQ-005: use last_retryable_status instead of last_exc for status info
    msg = self._build_exhaustion_message(name, last_retryable_status)
    logger.error(msg)
    raise TransportError(msg)
```

- **Step 4** (REQ-004/REQ-005): Add the exhaustion message builder:

```python
def _build_exhaustion_message(self, tool_name: str, last_retryable_status: int | None) -> str:
    """Build a safe retry-exhaustion diagnostic without exposing raw response bodies."""
    parts = [f"[Retry exhausted] tool={tool_name}"]
    if last_retryable_status is not None:
        parts.append(f"status={last_retryable_status}")
    return " ".join(parts) + f" after {self._RETRY_MAX} attempts"
```

### Details

**Step 1 — Attach redaction filter:**

After line 15 (`logger = logging.getLogger(__name__)`):

```python
from shared.logger import attach_redaction_filter, register_secret  # REQ-006

attach_redaction_filter(logger)  # REQ-006
```

**Step 2 — Register auth token as secret:**

In `HttpTransport.__init__`, after `self._auth_token = auth_token`:

```python
if self._auth_token:
    register_secret(self._auth_token)  # REQ-007
```

**Step 3 — Rework retry loop:**

Replace lines 106-150 as shown above. Key changes:
- `wait_sec = 2 ** attempt` (REQ-001: 1, 2 instead of 4, 2, 1)
- `if attempt < self._RETRY_MAX - 1: await asyncio.sleep(wait_sec)` (REQ-002: no sleep after final attempt)
- `last_retryable_status = resp.status_code` on retryable-status branches (REQ-003)
- `detail = f"status={e.response.status_code} request_id={req_id!r}"` (REQ-004)

**Step 4 — Add exhaustion message builder:**

Add after `_transport_error()` method:

```python
def _build_exhaustion_message(self, tool_name: str, last_retryable_status: int | None) -> str:
    """Build a safe retry-exhaustion diagnostic without exposing raw response bodies."""
    parts = [f"[Retry exhausted] tool={tool_name}"]
    if last_retryable_status is not None:
        parts.append(f"status={last_retryable_status}")
    return " ".join(parts) + f" after {self._RETRY_MAX} attempts"
```

## Compatibility considerations

- Backoff delay values change from `[4, 2, 1]` to `[1, 2]` — existing tests asserting these values must be updated (REQ-008).
- No sleep after the final attempt — existing test asserting 3 sleeps must be updated (REQ-008).
- Error messages no longer contain raw response body text — existing assertions checking for raw body fragments must be updated (REQ-004).
- Retry exhaustion now includes HTTP status code — existing assertions checking the exhaustion message format must be updated (REQ-005).
- Redaction filter attached to this module's logger — existing log-output assertions may need updating (REQ-006).

## Security considerations

- REQ-004 prevents raw MCP response bodies from reaching `ToolCallResult.output` — security improvement.
- REQ-006 applies secret redaction to previously-unprotected loggers — security improvement.
- REQ-007 registers the auth token as a secret so it can be redacted — security improvement.

## Rollback considerations

- Reverting removes the unified lifecycle handling but does not break existing behavior.
- Reverting the fail-closed check restores the pre-fix silent-pass behavior for unknown server keys.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_tool_executor.py -v`
- Verify backoff delays are `[1, 2]` (REQ-001/REQ-002/REQ-008).
- Verify no sleep after final attempt (REQ-002/REQ-008).
- Verify raw response body is not in error messages (REQ-004/REQ-010).
- Verify retry exhaustion includes HTTP status code (REQ-003/REQ-005/REQ-009).
- Verify redaction works on this module's log output (REQ-006/REQ-010).
- Static analysis: `uv run ruff check scripts/shared/http_transport.py`, `uv run mypy scripts/shared/http_transport.py`.

## Completion criteria

- Backoff delays increase: `[1, 2]` for `_RETRY_MAX=3`.
- No sleep after final attempt.
- Raw response body removed from error messages.
- Retry exhaustion reports HTTP status code safely.
- Redaction filter attached to module-level logger.
- Auth token registered as secret.
- All existing tests pass after updates.
- No new lint/type errors introduced.

## Out of scope

- Modifying `_RedactionFilter` itself — out of scope.
- Changing `Logger._configure_logger()` behavior — out of scope.
- Any change to `ToolCallResult`/`TransportErrorInfo` schema — confirmed unnecessary per Reference Files.
- Updating `docs/04_mcp_03_03_transport-and-health.md` — deferred to implementation phase per Documentation Impact.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Attach redaction filter; register auth token as secret | Pending | — | — | |
| 2 | Rework retry loop: increasing backoff, sleep gating, last status tracking | Pending | — | — | |
| 3 | Replace raw-body detail with sanitized fields; add exhaustion message builder | Pending | — | — | |
| 4 | Update test assertions for new behavior | Pending | — | — | See next row |
| 5 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 6 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260914-103224_mcpagent06_http-retry-backoff-safe-diagnostics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-124248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/shared/http_transport.py
