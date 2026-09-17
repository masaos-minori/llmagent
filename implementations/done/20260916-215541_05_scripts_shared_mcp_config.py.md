## Goal

Relax `_validate_auth_token` for disabled servers (REQ-004); add `required`/`failure_policy` role documentation (REQ-005); fix `get_effective_health_timeout()`'s zero-handling (REQ-006); correct the `health_timeout` conversion-error message (REQ-007); add per-mode required-field documentation (REQ-010).

## Scope

- Modify `McpServerConfig._validate_auth_token()` to skip non-empty auth_token requirement when `is_disabled`.
- Add docstring/field comments documenting `required` vs `failure_policy` roles (REQ-005).
- Fix `get_effective_health_timeout()` so `health_timeout=0` means "no timeout" consistently (REQ-006).
- Correct `_build_single_server()`'s `health_timeout` type-conversion error message (REQ-007).
- Add per-`StartupMode` required-field documentation (REQ-010).

## Assumptions

- `StartupMode.NONE`'s docstring states "no subprocess spawn, no health check; server is unusable" — requiring a connection secret for it is inconsistent.
- `httpx.Timeout(timeout=0)` interprets a numeric 0 as an immediate deadline, not "unbounded."
- `call_timeout_sec=0` already uses "0 = no timeout" convention (`http_transport.py:104`).

## Design decisions

- Use `self.is_disabled` property as the predicate for skipping auth_token validation.
- Change `get_effective_health_timeout()` to return `None` when `health_timeout == 0`, matching the "no timeout" convention.
- Rename the error message from "positive number or null" to "non-negative number or null" to accurately describe the accepted range.

## Alternatives considered

- Adding a new `HealthTimeoutZeroBehavior` enum — rejected: over-engineers a simple semantic fix.
- Using `-1` to mean "no timeout" — rejected: would break TOML config compatibility.
- Defining a separate `NO_TIMEOUT` sentinel value — rejected: adds complexity without benefit.

## Implementation

### Target file

`scripts/shared/mcp_config.py`

### Procedure

1. Relax `_validate_auth_token()` for disabled servers (REQ-004).
2. Add `required`/`failure_policy` role documentation (REQ-005).
3. Fix `get_effective_health_timeout()` zero-handling (REQ-006).
4. Correct `_build_single_server()`'s health_timeout error message (REQ-007).
5. Add per-`StartupMode` required-field documentation (REQ-010).

### Method

- **Step 1** (REQ-004): In `_validate_auth_token()`, add early-return for disabled servers:

```python
# Before (lines 177-184):
def _validate_auth_token(self, key_prefix: str) -> None:
    """Validate that auth_token is a non-empty str."""
    if not isinstance(self.auth_token, str):
        raise ValueError(
            f"{key_prefix}: auth_token must be str, got {type(self.auth_token).__name__}"
        )
    if not self.auth_token:
        raise ValueError(f"{key_prefix}: auth_token must not be empty")

# After:
def _validate_auth_token(self, key_prefix: str) -> None:
    """Validate that auth_token is a non-empty str, unless the server is disabled."""
    if not isinstance(self.auth_token, str):
        raise ValueError(
            f"{key_prefix}: auth_token must be str, got {type(self.auth_token).__name__}"
        )
    if not self.auth_token and not self.is_disabled:
        # Disabled servers do not require unused connection credentials (REQ-004)
        raise ValueError(f"{key_prefix}: auth_token must not be empty")
```

- **Step 2** (REQ-005): Add field-level documentation for `required` and `failure_policy`:

```python
# In McpServerConfig dataclass fields:
required: bool = True  # Startup criticality: FATAL vs WARNING escalation at discovery
failure_policy: FailurePolicy = FailurePolicy.FAIL_FAST  # Reserved: runtime call-failure behavior; currently single-valued (FAIL_FAST) with no branching
```

- **Step 3** (REQ-006): Fix `get_effective_health_timeout()`:

```python
# Before (lines 228-241):
def get_effective_health_timeout(cfg: McpServerConfig) -> float:
    """Return the effective health timeout for a given server config.

    Returns the configured ``health_timeout`` if set, otherwise falls back
    to the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a negative value.
    """
    if cfg.health_timeout is None:
        return 5.0
    if cfg.health_timeout < 0:
        raise ValueError(f"health_timeout must be >= 0, got {cfg.health_timeout}")
    return cfg.health_timeout

# After:
def get_effective_health_timeout(cfg: McpServerConfig) -> float | None:
    """Return the effective health timeout for a given server config.

    Returns None (no timeout) when health_timeout is 0, consistent with
    call_timeout_sec's "0 = no timeout" convention. Returns the configured
    health_timeout if set to a positive value, otherwise falls back to
    the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a negative value.
    """
    if cfg.health_timeout is None:
        return 5.0
    if cfg.health_timeout == 0:
        return None  # No timeout, consistent with call_timeout_sec=0 convention
    if cfg.health_timeout < 0:
        raise ValueError(f"health_timeout must be >= 0, got {cfg.health_timeout}")
    return cfg.health_timeout
```

- **Step 4** (REQ-007): Correct the error message:

```python
# Before (line 275-277):
raise ValueError(
    f"mcp_servers[{key!r}].health_timeout must be a positive number or null, "
    f"got {type(health_timeout_raw).__name__}"
)

# After:
raise ValueError(
    f"mcp_servers[{key!r}].health_timeout must be a non-negative number or null, "
    f"got {type(health_timeout_raw).__name__}"
)
```

- **Step 5** (REQ-010): Add per-StartupMode required-field documentation:

Add a class-level docstring/table after the `StartupMode` enum definition:

```python
class StartupMode(StrEnum):
    """MCP server startup lifecycle mode.

    Per-mode required fields:
    - NONE: none of url/cmd/auth_token (server is unusable)
    - PERSISTENT: url (enforced via HTTP-transport check)
    - SUBPROCESS: cmd (enforced) and url
    """
```

### Details

**Step 1 — REQ-004:** Replace lines 177-184 as shown above.

**Step 2 — REQ-005:** Update the `required` and `failure_policy` field definitions in `McpServerConfig` dataclass (around line 95-96).

**Step 3 — REQ-006:** Replace lines 228-241 as shown above. The return type changes from `float` to `float | None`.

**Step 4 — REQ-007:** Replace line 276 as shown above ("positive number" → "non-negative number").

**Step 5 — REQ-010:** Add the per-mode required-field table to `StartupMode`'s docstring (after line 41).

## Compatibility considerations

- `get_effective_health_timeout()` now returns `None` instead of `0` when `health_timeout=0`. Call sites must handle `None` (which `httpx.Timeout(None)` treats as "no timeout", matching the intended semantics).
- The two call sites (`mcp_tool_discovery.py:189`, `mcp_status.py:71-77`) are covered in subsequent rows.
- Disabled servers can now have an empty `auth_token` — this is the intended REQ-004 behavior.

## Security considerations

- REQ-004 improves security by not requiring credentials for disabled servers (reducing credential exposure surface).
- REQ-006 prevents near-instant health-check failures that could cause cascading issues.

## Rollback considerations

- Reverting REQ-004 restores the pre-fix auth_token requirement for disabled servers.
- Reverting REQ-006 restores the near-instant timeout behavior for `health_timeout=0`.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_mcp_config.py -v`
- Verify disabled-server auth_token exemption (REQ-004).
- Verify `health_timeout=0` returns `None` and does not cause immediate timeout (REQ-006).
- Verify corrected error message text (REQ-007).
- Verify per-mode required-field assertions (REQ-010).
- Static analysis: `uv run ruff check scripts/shared/mcp_config.py`, `uv run mypy scripts/shared/mcp_config.py`.

## Completion criteria

- `_validate_auth_token()` skips non-empty check for disabled servers.
- `get_effective_health_timeout()` returns `None` for `health_timeout=0`.
- Error message correctly says "non-negative number or null".
- Per-StartupMode required-field documentation added.
- All existing tests pass after adding regression tests.
- No new lint/type errors introduced.

## Out of scope

- Modifying `call_timeout_sec` semantics — already correct ("0 = no timeout").
- Modifying `startup_timeout_sec` semantics — intentionally different ("skip the health-check poll").
- Any change to `config/*.toml` server entries — no server currently uses `startup_mode = "none"`.
- Expanding `FailurePolicy` beyond `FAIL_FAST` — out of scope per Acceptance Criteria.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Relax _validate_auth_token; document required/failure_policy | Completed | 20260917-000000 | 20260917-000000 | Done |
| 2 | Fix health_timeout=0 handling; correct error message | Completed | 20260917-000000 | 20260917-000000 | Done |
| 3 | Add per-mode required-field documentation | Completed | 20260917-000000 | 20260917-000000 | Done |
| 4 | Add regression tests for REQ-004/006/007/010 | Completed | 20260917-000000 | 20260917-000000 | Existing test updated |
| 5 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-000000 | 20260917-000000 | All tests pass |
| 6 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-000000 | 20260917-000000 | Not in scope |


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
- **Requirement ID**: REQ-004, REQ-005, REQ-006, REQ-007, REQ-010
- **Source issue**: issues/20260914-103159_mcpagent05_mcp-lifecycle-invocation-gate-unification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-123229_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/shared/mcp_config.py
