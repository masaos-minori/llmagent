## Goal

Implement the Agent-only control plane: authenticate with a dedicated control Bearer token and serve `GET /v1/call_state/{key}` and `POST /v1/call_state/{key}/reconcile` from the dedup ledger, with the reconciler registry seam and operator-review responses.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the new module only. `dispatch.py` stays untouched (24,573 B of the 24,576 B gate). Wiring into each server is row 10.

## Assumptions

- Verified: each server module calls `attach_auth_middleware(app, token)` at import time, while uvicorn imports the app string only after `run_http` has run (and the base-class tests use non-importable `app_module` strings), so `run_http` cannot attach to the app object. Design: `run_http` calls `configure_control` (new) and `attach_auth_middleware` calls `attach_control_api(app)`; both are small additions in row 10 (Plan corrected in this cycle).
- The control middleware is registered after the tool-auth middleware, so it is outermost: control paths are authenticated and served entirely there and never reach the tool-auth middleware; tool paths are untouched (ADR-017 INV-03 preserved).
- The module opens its own `DedupStore` handle from the validated `[dedup]` config (no access to private `dispatch` globals).

## Design decisions

- `CONTROL_PATH_PREFIX = '/v1/call_state/'`; `configure_control(token, dedup_config, server_name)` stores state and opens the store only when the token is non-empty and a config exists; an empty token logs one warning naming the server.
- `attach_control_api(app)` registers an HTTP middleware: for a control path it compares `Authorization` with `Bearer <control token>` via `hmac.compare_digest`; empty or missing token returns 401 (fail closed); the tool token therefore fails on control paths.
- GET: `call_state_view` to `CallStateResponse` (404 `unknown_key` for an absent key). POST reconcile: completed gives `reused_completed` (no mutation); pending with a live lease gives `refused`/`lease_live` (409); exhausted attempts gives `refused`/`attempts_exhausted` with operator review; otherwise consult the registered `Reconciler` for the tool: `evidence_found` (new)/`no_evidence` (new) call `reconcile_execution` (row moves to interrupted) and record the evidence digest, `ambiguous`/`unverifiable`/reconciler error give `operator_review` with no row change; no reconciler registered gives `reconcile_execution` plus `operator_review`.
- `register_reconciler(tool_name, reconciler)` is the registration seam; per-tool reconcilers belong to other issues.

## Alternatives considered

Rejected: a FastAPI `APIRouter` with `Depends` (routes would still sit behind the tool-auth middleware, which rejects the control token).

## Implementation
### Target file
`scripts/mcp_servers/control_api.py` (new)

### Procedure
1. Create the module with the prefix constant, module state, `configure_control` (new), `register_reconciler` (new), and the handler helpers.
2. Implement `attach_control_api` (new) with the control-path middleware, key validation (`^[A-Za-z0-9._:-]{1,256}$`, else 422), and `X-Request-Id`.
3. Implement the reconcile decision flow above, appending evidence through `append_reconcile_evidence`.

### Method
Handlers are plain functions returning the Pydantic models from row 08; the middleware turns them into `JSONResponse` with `model_dump()`. Store errors map to 503 `store_unavailable` (new); unexpected exceptions return a fixed message and are logged by class name only.

### Details
- Never read or echo the request body; reconcile takes no payload.
- Reconciler exceptions are caught, logged by class name, and reported as `reconciler_failed` (new) with operator review.
- A completed row is never re-executed or mutated by any control path.

## Compatibility considerations

New paths only; every existing path and the tool-auth middleware behave as before. An unconfigured server answers control paths with 401.

## Security considerations

Separate control token, constant-time compare, fail closed on empty token, structured responses only, exact-match key lookup, loopback binding unchanged; no raw arguments, credentials, signed URLs, exceptions, or paths in any response or log.

## Rollback considerations

Revert the commit; the middleware disappears with the module and control paths return 404.

## Validation plan

- `uv run pytest tests/mcp_servers/test_call_state_api.py tests/mcp_servers/test_mcp_server_base.py tests/mcp_servers/test_require_auth_token.py`
- `uv run python tools/check_module_size.py --top 5`

## Completion criteria

- Both endpoints work with the control token, reject the tool token and an empty token, follow the reconcile decision flow, and the new module has no import of `server.py`.

## Out of Scope

Per-tool reconciler implementations, the Agent client, and server wiring (row 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-144718 | 20261123-144718 | control_api.py created (prefix constant, module state, configure_control, register_reconciler, key pattern, X-Request-Id, no request-body reads); /reconcile suffix is parsed before key validation so the key stays the lookup key |
| 2 | Add or update tests per Validation plan | Completed | 20261123-144718 | 20261123-144718 | covered by row 29 tests/mcp_servers/test_call_state_api.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-144718 | 20261123-144718 | ruff, mypy, lint-imports, bandit (-ll: no new medium/high from this file), module-size gate (12,461 B) pass; 19 control tests plus the base and auth tests green |

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
- **Requirement ID**: `REQ-001` (control endpoints and response shape), `REQ-002` (separate control Bearer authorization), `REQ-004` (reconciler contract)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/mcp_servers/control_api.py`
