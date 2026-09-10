## Goal

Register the new authentication middleware on the FastAPI app in `scripts/eventbus/app.py`, replacing the existing warning message about missing authentication with actual enforcement.

## Scope

- Modify `scripts/eventbus/app.py`:
  - Register `@app.middleware("http")` for Bearer-token authentication
  - Remove the existing warning log message about missing authentication (line 64-68)
  - Wire the middleware to use the token from `EventBusConfig.auth_token`
- No other file modifications beyond what's listed in the Plan's Implementation Target Files.

## Assumptions

- `scripts/eventbus/auth.py` will be created first (REQ-002) with `verify_bearer_token()`, `require_role()`, and related helpers.
- `EventBusConfig` will have an `auth_token` attribute after `REQ-005`'s `load_config()` hardening adds the key.
- The middleware pattern mirrors `scripts/mcp_servers/server.py::attach_auth_middleware()` exactly.

## Design decisions

- **Middleware placement**: Register `@app.middleware("http")` immediately after `app = FastAPI(lifespan=lifespan)` (line 109), before any route handlers.
- **Token source**: Read from `request.app.state.config.auth_token` (set during lifespan initialization).
- **Fail-closed behavior**: Empty/missing `auth_token` causes 500 error (not 401), preventing silent unauthenticated operation.

## Alternatives considered

- Per-route authentication dependencies: Would require adding `Depends(require_role(...))` to every route handler; middleware approach simpler and consistent with MCP server precedent.
- Separate auth middleware class: Unnecessary complexity; function-based middleware sufficient.

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

Modify `scripts/eventbus/app.py` to register the authentication middleware and remove the existing warning message.

### Method

1. Import the authentication middleware helper from `scripts/eventbus/auth.py`.
2. After `app = FastAPI(lifespan=lifespan)` (line 109), call the middleware registration function.
3. Replace the existing warning log message (lines 64-68) with the actual authentication check.
4. Update the lifespan function to validate `auth_token` presence before starting.

### Details

```python
# scripts/eventbus/app.py — changes only

# After existing imports, add:
from eventbus.auth import attach_auth_middleware  # noqa: PLC0415 — new module, REQ-002

# In lifespan() function, replace lines 64-68:
# OLD:
#     if _is_public_host(app.state.config.host):
#         logger.warning(
#             "eventbus bound to public address %s:%d without authentication",
#             app.state.config.host,
#             app.state.config.port,
#         )
# NEW:
#     if _is_public_host(app.state.config.host):
#         logger.warning(
#             "eventbus bound to public address %s:%d without loopback-only protection",
#             app.state.config.host,
#             app.state.config.port,
#         )

# After app = FastAPI(lifespan=lifespan) (line 109):
#     # Authentication middleware — mirrors scripts/mcp_servers/server.py::attach_auth_middleware()
#     try:
#         attach_auth_middleware(app, app.state.config.auth_token)
#     except ValueError:
#         # auth_token not configured — fail closed at startup
#         logger.error("auth_token not configured in config/eventbus.toml")
#         sys.exit(1)
```

## Compatibility considerations

- The middleware must be registered after `app.state.config` is initialized (during lifespan startup), so the token is available.
- The `attach_auth_middleware()` function signature must match the MCP server precedent: `(app: _FastAPIApp, token: str) -> None`.

## Security considerations

- **Startup validation**: `auth_token` must be validated at startup (before the middleware runs) — an empty/missing token must cause `sys.exit(1)`, not silently start unauthenticated.
- **No secret logging**: The middleware must never log the token value; only log that authentication failed.
- **Loopback warning update**: The existing warning about missing authentication should be updated to reference loopback-only protection instead, since authentication now exists.

## Rollback considerations

- Rolling back this change means removing the middleware registration and restoring the original warning message.
- The original warning message (`scripts/eventbus/config.py` line 53) references the absence of authentication — this becomes accurate again after rollback.

## Validation plan

- Integration test: Send requests to each route without a Bearer token → expect 401.
- Integration test: Send requests with an invalid Bearer token → expect 401.
- Integration test: Send requests with a valid Bearer token → expect success.
- Startup validation: Start EventBus without `auth_token` in config → expect 500 error or exit.
- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v`.

## Completion criteria

- [ ] Middleware registered in `scripts/eventbus/app.py`
- [ ] Existing warning message replaced with loopback-only reference
- [ ] Startup validation for missing `auth_token` present
- [ ] All auth tests passing (unauthenticated → 401, authenticated → success)
- [ ] No cross-layer imports (verified via `PYTHONPATH=scripts uv run lint-imports`)

## Out of scope

- Modifying route handlers (covered by separate implementation procedures).
- Adding monitoring-specific health/metrics endpoints.
- Token rotation infrastructure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register authentication middleware | Pending | — | — | |
| 2 | Replace existing warning message | Pending | — | — | |
| 3 | Add startup validation for auth_token | Pending | — | — | |
| 4 | Add or update tests per Validation plan | Pending | — | — | |
| 5 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: scripts/eventbus/app.py
