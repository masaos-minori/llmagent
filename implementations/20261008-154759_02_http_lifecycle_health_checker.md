# Implementation Procedure: Add Bearer token to /health requests

## Goal

Add Bearer token authentication to `/health` requests in `http_lifecycle_health_checker.py` when the server has `auth_token` configured, implementing Option B of the `/health` authentication policy.

## Scope

- Modify `scripts/agent/http_lifecycle_health_checker.py`: add Bearer token to `verify_running_async()` and `startup_poll()` when `cfg.auth_token` is set.
- Related to: `REQ-002` (Bearer token on /health), `REQ-005` (do not weaken auth).

## Assumptions

- Option B (authenticate all endpoints) is the preferred `/health` authentication policy, consistent with ADR-007.
- The `cfg` object passed to `verify_running_async()` and `startup_poll()` has an `auth_token` attribute (from `McpServerConfig`).
- Only send Bearer token when `cfg.auth_token` is non-empty; existing callers without auth_token are unaffected.

## Design decisions

- Bearer token added via `headers["Authorization"] = f"Bearer {cfg.auth_token}"` in both `verify_running_async()` and `startup_poll()`.
- Token is only sent when `cfg.auth_token` is non-empty — no token sent for servers without `auth_token` configured.

## Alternatives considered

- Option A (exempt `/health` from auth): rejected — inconsistent with ADR-007 "authenticate all endpoints".
- Adding a separate parameter to `verify_running_async()` for headers: rejected — `cfg.auth_token` is already available on the config object, and adding a parameter would require changing all call sites.

## Implementation

### Target file

`scripts/agent/http_lifecycle_health_checker.py`

### Procedure

1. Modify `verify_running_async()` to include Bearer token in the request when `cfg.auth_token` is set.
2. Modify `startup_poll()` to pass the Bearer token through to `verify_running_async()`.

### Method

#### Step 1: Modify `verify_running_async()`

In `verify_running_async()` (lines 42-83), replace the current httpx.AsyncClient usage:

```python
@staticmethod
async def verify_running_async(
    server_key: str,
    cfg: object,
    *,
    url: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    **client_kwargs: Any,
) -> bool:
    """Verify that the server identified by *server_key* is reachable."""
    target_url = url or getattr(cfg, "health_url", _DEFAULT_HEALTH_URL)
    if target_url is None:
        target_url = _DEFAULT_HEALTH_URL
    # Build headers — add Bearer token if cfg has auth_token
    headers: dict[str, str] = {}
    auth_token = getattr(cfg, "auth_token", "")
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    try:
        async with httpx.AsyncClient(timeout=timeout, **client_kwargs) as client:
            response = await client.get(target_url, headers=headers)
            if response.status_code == 200:
                logger.debug("Health check passed at %s", target_url)
                return True
            logger.debug(
                "Health check returned status %d at %s",
                response.status_code,
                target_url,
            )
            return False
    except httpx.RequestError as exc:
        logger.debug("Health check failed at %s: %s", target_url, exc)
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unexpected error during health check: %s", exc)
        return False
```

Key changes:
1. Extract `auth_token` from `cfg` using `getattr(cfg, "auth_token", "")`.
2. If `auth_token` is non-empty, add `headers["Authorization"] = f"Bearer {auth_token}"`.
3. Pass `headers=headers` to `client.get()`.

#### Step 2: Modify `startup_poll()`

In `startup_poll()` (lines 85-137), the Bearer token is already handled by `verify_running_async()` since it delegates to that method. No additional changes needed here — the `cfg` object is passed through unchanged.

### Details

- **REQ-002**: Bearer token added via `headers["Authorization"] = f"Bearer {auth_token}"` when `cfg.auth_token` is non-empty. This applies to both `verify_running_async()` and `startup_poll()` (which delegates to `verify_running_async()`).
- **REQ-005**: Authentication is not weakened — Bearer token is sent when `auth_token` is configured; no fallback to unauthenticated access.
- **Risk mitigation**: Only send Bearer token when `cfg.auth_token` is non-empty; existing callers without auth_token are unaffected.

## Compatibility considerations

- The `auth_token` attribute is accessed via `getattr(cfg, "auth_token", "")`, which is safe even if `cfg` does not have this attribute (returns empty string, no header added).
- The `**client_kwargs` parameter is preserved — any existing caller passing custom kwargs will still work.
- No changes to the return type or signature of either method.

## Security considerations

- Bearer token is read from `cfg.auth_token` and sent only when non-empty. No token is sent for servers without `auth_token` configured.
- The token is not logged or persisted — it is used only as an HTTP header value.
- Authentication is not weakened to bypass the check (REQ-005 constraint).

## Rollback considerations

- The rollback is straightforward: revert the `headers` logic in `verify_running_async()` to the original `client.get(target_url)` call without headers.
- No database schema changes or configuration file changes are required.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_health_checker.py | Unit: mock 503 response with liveness=true/false, verify behavior | pytest | 503 handling tests pass |
| scripts/agent/http_lifecycle_health_checker.py | Integration: mock server with auth, verify Bearer token sent | pytest | Bearer token test passes |
| scripts/agent/startup_mcp_starter.py | Lint/type: ruff, mypy | ruff, mypy | No lint/type errors |

## Completion criteria

- [ ] `verify_running_async()` sends Bearer token when `cfg.auth_token` is non-empty.
- [ ] `verify_running_async()` does not send Bearer token when `cfg.auth_token` is empty or missing.
- [ ] `startup_poll()` correctly passes `cfg` to `verify_running_async()` (no changes needed — verified by checking the delegation).
- [ ] Integration test verifies Bearer token is sent on `/health` when `auth_token` is configured.
- [ ] ruff and mypy pass with no errors.

## Out of scope

- Health endpoint changes of unrelated servers.
- Circuit-breaker behavior.
- Changes to `scripts/agent/http_lifecycle.py` beyond what is needed for the `/health` auth policy.
- Documentation updates (ADR-004 Known Deviations, adr-index INV-09 status) — handled separately.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261008-184949 | 20261008-184949 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261008-185016 | 20261008-185016 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261008-185016 | 20261008-185016 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261008-185016 | 20261008-185016 |  |

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
- **Requirement ID**: REQ-002, REQ-005
- **Source issue**: issues/20261007-154014_mcpstart01_fix-mcp-subprocess-startup-and-health-check-handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-153840_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-154759
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py