## Goal

Add a shared request-boundary check that rejects a side-effecting tool called through `/v1/call_tool` with an empty `X-Idempotency-Key` before dispatch. (`REQ-004`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Every MCP app (`read`, `write`, `delete`, `shell`, `rag_pipeline`, `github`, `git`, `web_search`, `cicd`, `mdq`) builds its own `FastAPI` instance but calls the shared `attach_auth_middleware()` in `scripts/mcp_servers/server.py` — so a middleware-based boundary check can be added in `server.py` alone and applies to all apps without editing any app module.
- The set of "side-effecting tools" is defined by the sibling issue `sideeffect001` (`issues/20261111-163800_sideeffect001_side-effect-classification-central.md`) and the canonical classification in `scripts/shared/tool_constants.py`. That set does not exist yet, so the exact tool list is deferred to `sideeffect001`; this procedure implements the boundary mechanism and records the dependency.
- Keyless read-only `/v1/call_tool` calls stay allowed (UNK-02); the check rejects only side-effecting tools.
- The current behavior under test: `extract_request_context()` returns `idempotency_key = ""` when `X-Idempotency-Key` is absent (server.py lines 163-166), so a keyless side-effecting call currently executes.
- Rejection status code (400 vs 422) is a maintainer preference (UNK-03); default 422 (validation error).

## Design decisions
- **Boundary location (UNK-01)**: prefer a FastAPI middleware registered inside the shared `attach_auth_middleware()` in `server.py`. Verified evidence: all 10 apps call `attach_auth_middleware()` once after `app = FastAPI(...)`, so registering the idempotency middleware there covers every app from a single edited file. The alternative — a shared helper in `server.py` invoked by each app's `/v1/call_tool` handler — would require editing the handler bodies in the app modules (`git_server.py`, `web_search_server.py`, `cicd_server.py`, `mdq_server.py`, `github_server.py`, etc.), which are NOT in this Plan's Implementation Target Files; that path would be an additional-target-file discovery, so it is rejected in favor of the middleware.
- **Side-effect set source**: the middleware must consult the canonical side-effect tool set from `tool_constants.py`/`sideeffect001`, never a second hardcoded list. Until `sideeffect001` lands, the procedure records the requirement and defers the concrete set (recorded below as a Needs-confirmation caveat).

## Alternatives considered
- Per-handler shared helper in `server.py`: rejected because it forces edits to unlisted app modules (additional-target-file discovery).
- A per-app middleware call in each app module: rejected because it duplicates the registration across 10 files instead of using the existing shared `attach_auth_middleware()` hook.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. Add a FastAPI middleware (registered alongside `attach_auth_middleware`, or as a second `@app.middleware("http")` in that function) that, for `POST /v1/call_tool` requests, rejects the call when the tool is side-effecting and the resolved `idempotency_key` is empty.
2. Resolve the idempotency key from the same headers/state the rest of the stack uses (`x-idempotency-key` header, falling back to `request.state.idempotency_key`), matching `extract_request_context()`.
3. Consult the canonical side-effect tool set from `tool_constants.py` (once `sideeffect001` defines it) to decide whether a given tool name is side-effecting; do not introduce a second list.
4. Return the chosen rejection status (default 422) before dispatch; leave read-only and non-`/v1/call_tool` paths untouched.

### Method
- Inspect `attach_auth_middleware()` (server.py lines 95-136) as the single shared middleware-registration hook every app calls; add the idempotency enforcement there or as a companion middleware in the same module.
- Read `dispatch.py` to confirm how `idempotency_key` flows to dedup, and `audit.py` (`_emit_call_tool_audit`/`_audit_log`) for the audit path the boundary feeds into.
- Read `tool_constants.py` and `sideeffect001` for the canonical side-effect set; if `sideeffect001` has not landed, gate the concrete set behind that definition and record the dependency.

### Details
- The middleware must read and replay the request body (or use FastAPI's request state) so downstream handlers still see the original body.
- The check must run before dispatch but after auth middleware, so an unauthorized request is still rejected by the existing bearer check first.
- Because the side-effect set is not yet canonical, the middleware as implemented here must not silently allow or deny based on an unverified list; the Needs-confirmation caveat below governs this.

## Compatibility considerations
Breaking HTTP-surface behavior: keyless side-effecting `/v1/call_tool` requests now fail instead of executing. External callers must supply `X-Idempotency-Key` for side effects. No backward-compat shim (no-shim policy, `tools/check_compat_shims.py`).

## Security considerations
Closes the gap where a keyless side-effecting `/v1/call_tool` always executed, bypassing availability gating, argument validation, dedup, and shared audit. The key requirement must consume the canonical side-effect set, not a second list.

## Rollback considerations
Revert the commit.

## Validation plan
- Test that a keyless side-effecting `/v1/call_tool` is rejected with the chosen status before execution (`AC-2`).
- Test that a keyed side-effecting `/v1/call_tool` is dispatched and deduped (`AC-3`).
- Test that keyless read-only `/v1/call_tool` remains allowed (`AC-3`, UNK-02).
- Confirm the middleware is active on every app (all 10 call `attach_auth_middleware()`).
- `uv run python tools/stale_detector.py` clean before hand-off.

## Completion criteria
- A keyless side-effecting `/v1/call_tool` is rejected before dispatch with status 400 or 422 (`AC-2`).
- Every accepted side effect passes availability gating, argument validation, common dispatch, dedup, and audit (`AC-3`).
- The side-effect set consulted is the canonical one from `sideeffect001`/`tool_constants.py`, not a second list.

## Out of Scope
- Removing direct execution routes (separate rows, REQ-001/002/003).
- Making WRITE_DANGEROUS tools leave an audit record (`adrrev011`, out of scope here).
- Deleting route-specific request/response models (see `models.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-122326 | 20261115-122326 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261115-122326 | 20261115-122326 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-122326 | 20261115-122326 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-122326 | 20261115-122326 | STEP:4:N/A docs endpoint update is REQ-008 (procedure 19); this boundary is middleware-level, no per-app doc change |

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
- **Requirement ID**: `REQ-004` — reject keyless side-effecting `/v1/call_tool` before dispatch at the shared request boundary
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084338
- **Related target files**: `scripts/mcp_servers/server.py`