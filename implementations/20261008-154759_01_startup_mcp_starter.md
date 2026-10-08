# Implementation Procedure: Fix MCP subprocess startup and health check handling

## Goal

Implement the decision matrix for MCP server startup and health check behavior per ADR-004 Group 7: `required=false` servers that fail must be disabled without aborting the Agent, and the `/health` authentication policy must be resolved consistently between Agent and servers.

## Scope

- Modify `scripts/agent/startup_mcp_starter.py`: add `cfg.required` branching in `start_servers()` and `verify_health()`, add Bearer token support, parse 503 body for degraded-but-live detection.
- Related to: `REQ-001` (required=false server disable), `REQ-002` (Bearer token on /health), `REQ-003` (503 body parsing), `REQ-004` (required=true aborts startup).

## Assumptions

- Option B (authenticate all endpoints) is the preferred `/health` authentication policy, consistent with ADR-007.
- The 503 body structure follows `make_health_response()` in `health_response.py`: `{"liveness": True/False, "status": "degraded", "ready": False}`.
- `McpServerConfig.required` defaults to `True` (line 104 of mcp_config.py), so only explicitly set `required=false` servers are affected.
- The existing `is_disabled` property on `McpServerConfig` (line 110) is sufficient for disabling a server — no new property needed.

## Design decisions

- Decision matrix per ADR-004 Group 7: 2-axis (required/not + down/degraded) determines outcome.
- Bearer token sent on `/health` requests when `cfg.auth_token` is non-empty (Option B).
- 503 body parsed defensively: if body is not valid JSON or lacks `liveness` field, treat as down.

## Alternatives considered

- Option A (exempt `/health` from auth): rejected — inconsistent with ADR-007 "authenticate all endpoints".
- Raising a new exception type for degraded-but-live: rejected — existing `RuntimeError` raised for non-200 is sufficient; the caller can inspect status code and body.

## Implementation

### Target file

`scripts/agent/startup_mcp_starter.py`

### Procedure

1. Add `disable_server(server_key, cfg)` helper method to `McpServerStarter`.
2. Modify `start_servers()` to check `cfg.required` after subprocess start failure.
3. Modify `verify_health()` to add Bearer token, parse 503 body, apply decision matrix.

### Method

#### Step 1: Add `disable_server` helper

Add a new async method to `McpServerStarter`:

```python
async def disable_server(self, server_key: str, cfg: McpServerConfig) -> None:
    """Disable a non-required server: mark is_disabled, remove from routing."""
    logger.warning(
        "Disabling MCP server %r (required=false, startup failed)",
        server_key,
    )
    # Mark the server as disabled
    cfg.startup_mode = StartupMode.NONE
    # Remove from routing by clearing tool_names
    cfg.tool_names = []
```

This uses the existing `is_disabled` property (line 110 of mcp_config.py) which returns `True` when `startup_mode == StartupMode.NONE`.

#### Step 2: Modify `start_servers()`

After the retry logic in `start_servers()` (around line 110), add decision matrix logic:

```python
# After the retry block (line ~110), before returning:
if result is not None:
    last_startup_time = result
else:
    # Subprocess start failed — apply decision matrix
    if not cfg.required:
        # required=false: disable server and continue
        await self.disable_server(key, cfg)
        continue
    else:
        # required=true: raise FATAL (existing behavior preserved)
        raise RuntimeError(
            f"MCP subprocess {key!r} failed to start after retry"
        )
```

The key change: after `result is None` (subprocess start failure), check `cfg.required` instead of silently continuing. For `required=false`, call `disable_server()` and `continue` to the next server. For `required=true`, raise an error (preserving existing behavior).

#### Step 3: Modify `verify_health()`

In `verify_health()` (lines 114-151), replace the current logic:

```python
async def verify_health(self) -> None:
    """Verify health of all MCP subprocess servers after startup."""
    ctx = self._ctx
    if ctx.services_required.tools is None:
        raise RuntimeError("tools service not initialized")
    if ctx.services_required.lifecycle is None:
        raise RuntimeError("lifecycle service not initialized")

    subprocess_servers = [
        (key, cfg)
        for key, cfg in ctx.cfg.mcp.mcp_servers.items()
        if cfg.startup_mode == StartupMode.SUBPROCESS
        and cfg.transport == TransportType.HTTP
    ]

    for server_key, cfg in subprocess_servers:
        if self._shutdown_event is not None and self._shutdown_event.is_set():
            from agent.startup import StartupInterrupted
            raise StartupInterrupted(
                f"shutdown requested before health check for {server_key!r}"
            )
        url = cfg.url.rstrip("/") + "/health"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Add Bearer token if server has auth_token
                headers = {}
                if cfg.auth_token:
                    headers["Authorization"] = f"Bearer {cfg.auth_token}"
                resp = await client.get(url, headers=headers)
                if resp.status_code != httpx.codes.OK:
                    # Parse 503 body for degraded-but-live detection
                    if resp.status_code == 503:
                        try:
                            body = resp.json()
                            liveness = body.get("liveness", False)
                            if liveness:
                                logger.info(
                                    "Post-startup health check: %r is degraded but live",
                                    server_key,
                                )
                                continue
                        except Exception:
                            pass  # Not valid JSON — treat as down
                    raise RuntimeError(f"HTTP {resp.status_code}")
                logger.info("Post-startup health check passed for %r", server_key)
        except Exception:  # noqa: BLE001
            # Use retry helper instead of inline retry
            await retry_once_with_delay(
                lambda: self._verify_single_health(server_key, cfg),
                delay=RETRY_DELAY_SEC,
                shutdown_event=self._shutdown_event,
                interrupt_msg=f"shutdown requested during post-startup health check retry delay for {server_key!r}",
                fatal_prefix=f"{OutputTag.FATAL} MCP subprocess {server_key!r} failed post-startup health check:",
            )
```

Key changes:
1. Add Bearer token to the request when `cfg.auth_token` is set.
2. On 503, parse the JSON body — if `liveness=true`, log INFO and continue (degraded-but-live).
3. If body parsing fails or `liveness=false`, raise RuntimeError (treat as down).

### Details

- **REQ-001**: `disable_server()` sets `startup_mode = StartupMode.NONE`, which makes `is_disabled` return True. The `tool_names` list is cleared so the server's tools are removed from routing.
- **REQ-002**: Bearer token added via `headers["Authorization"] = f"Bearer {cfg.auth_token}"` when `cfg.auth_token` is non-empty.
- **REQ-003**: 503 body parsed with `resp.json()`, checking `body.get("liveness", False)`. If `liveness=true`, continue. If parsing fails, treat as down.
- **REQ-004**: `required=true` servers still raise RuntimeError on startup failure (existing behavior preserved).
- **REQ-005**: Authentication is not weakened — Bearer token is sent when `auth_token` is configured; no fallback to unauthenticated access.

## Compatibility considerations

- The `disable_server()` method modifies `cfg.startup_mode` and `cfg.tool_names` in-place. This is consistent with how other parts of the codebase handle server disabling (e.g., `mcp_tool_discovery.py` line 305 checks `cfg.is_disabled`).
- The Bearer token header is only added when `cfg.auth_token` is non-empty, so existing callers without auth_token are unaffected.
- The 503 body parsing assumes the standard `make_health_response()` structure. Servers using a different health response format may need separate handling.

## Security considerations

- Bearer token is read from `cfg.auth_token` and sent only when non-empty. No token is sent for servers without `auth_token` configured.
- The token is not logged or persisted — it is used only as an HTTP header value.
- Authentication is not weakened to bypass the check (REQ-005 constraint).

## Rollback considerations

- If the decision matrix causes unexpected behavior, the rollback is straightforward: revert the `cfg.required` check in `start_servers()` and the Bearer token/503 parsing in `verify_health()`.
- The `disable_server()` method is additive — removing it does not affect existing behavior since it was never called before.
- No database schema changes or configuration file changes are required.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/startup_mcp_starter.py | Unit: mock subprocess failure, verify `required=false` continues, `required=true` aborts | pytest | All decision matrix tests pass |
| scripts/agent/http_lifecycle_health_checker.py | Unit: mock 503 response with liveness=true/false, verify behavior | pytest | 503 handling tests pass |
| scripts/agent/http_lifecycle_health_checker.py | Integration: mock server with auth, verify Bearer token sent | pytest | Bearer token test passes |
| scripts/agent/startup_mcp_starter.py | Lint/type: ruff, mypy | ruff, mypy | No lint/type errors |

## Completion criteria

- [ ] `disable_server()` method exists and correctly sets `startup_mode = StartupMode.NONE` and clears `tool_names`.
- [ ] `start_servers()` checks `cfg.required` after subprocess start failure: `required=false` → disable and continue; `required=true` → raise error.
- [ ] `verify_health()` sends Bearer token when `cfg.auth_token` is set.
- [ ] `verify_health()` parses 503 body: `liveness=true` → continue; `liveness=false` or parse failure → raise error.
- [ ] Unit tests cover all four decision matrix outcomes: `required=false`+down, `required=true`+down, 503+liveness=true, 503+liveness=false.
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
| 2 | Add or update tests per Validation plan | Completed | 20261008-185008 | 20261008-185008 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261008-185008 | 20261008-185008 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261008-185008 | 20261008-185008 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20261007-154014_mcpstart01_fix-mcp-subprocess-startup-and-health-check-handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-153840_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-154759
- **Related target files**: scripts/agent/startup_mcp_starter.py