## Goal

Delete the 6 direct POST execution route handlers from `github_server_pull_requests.py`. (`REQ-003`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The 6 routes (`list_pull_requests`, `get_pull_request`, `create_pull_request`, `search_pull_requests`, `update_pull_request`, `merge_pull_request`) call `svc.<method>(req)` via `_get_service` and bypass dispatch, idempotency/dedup, and audit; removing them removes only the HTTP surface, not tool availability (each tool is reachable via `/v1/call_tool` in `github_server.py`).
- No external deploy/ops/admin/CI/integration caller posts to these routes (recorded in Plan Risks / AC-6).
- The route-specific request/response models imported from `github_models` are consumed by the service/dispatch path, not deleted here (see `models.py` row).

## Design decisions
- Delete the `@router.post` decorators and their `async def` handler bodies together, so no dangling route registration or unused handler remains.
- Leave the module-level `router = APIRouter()` and imports intact unless the linter/mypy flags them as unused after handler removal.

## Alternatives considered
- Keeping the routes behind the dispatcher: out of scope — this Plan removes the parallel execution contract entirely.
- Moving these handlers into `github_server.py`'s `/v1/call_tool`: out of scope — `/v1/call_tool` already dispatches the same tools through the shared path.

## Implementation
### Target file
`scripts/mcp_servers/github/github_server_pull_requests.py`

### Procedure
1. Delete the 6 direct POST execution-route handlers and registrations at lines 33-134 (`/list_pull_requests`, `/get_pull_request`, `/create_pull_request`, `/search_pull_requests`, `/update_pull_request`, `/merge_pull_request`).
2. Confirm `github_server.py` still exposes these six tools solely through `/v1/call_tool`, so tool availability is preserved.
3. Remove now-unused imports (e.g. `time`, `ListPullRequestsResponse`, ...) only if the linter/mypy flags them and nothing else imports them.

### Method
Locate the handlers with `grep -n "@router.post\|async def" scripts/mcp_servers/github/github_server_pull_requests.py`; delete each `@router.post("/<route>", response_model=...)` decorator plus its `async def` handler body. Confirm no remaining `@router.post` execution route survives in this module.

### Details
- Each removed handler calls `svc.list_pull_requests(req)` etc. via `Depends(_get_service)` and never touches `_dispatch_*`, the idempotency/dedup path, or `_emit_call_tool_audit` — this is exactly the bypass this Plan removes.
- Availability is preserved because `github_server.py`'s `/v1/call_tool` (line 227) dispatches the same GitHubService methods through the shared path.

## Compatibility considerations
Breaking HTTP-surface removal. External callers must move to `/v1/call_tool`; no backward-compat shim (no-shim policy, `tools/check_compat_shims.py`).

## Security considerations
Route removal closes a second execution contract that bypassed availability gating, argument validation, dedup, and shared audit on the GitHub pull-request path.

## Rollback considerations
Revert the commit.

## Validation plan
- Route-inventory test for the GitHub app asserts no operation-specific execution route remains and `/v1/call_tool` is present (`AC-1`, `AC-5`).
- Existing GitHub `/v1/call_tool` tests still pass (availability preserved).
- `rg` over `deploy/`, `scripts/ops/`, `scripts/admin/`, `.github/workflows/`, `tests/integration/` finds no external caller of a removed route (`AC-6`).

## Completion criteria
- No `@router.post` execution route remains in `github_server_pull_requests.py`; only the tools reachable via `/v1/call_tool` remain.
- `/v1/call_tool` still dispatches GitHub pull-request tools.

## Out of Scope
- Any change to `/v1/call_tool` behavior, dispatch, or the idempotency-key enforcement (separate row / sibling Plan).
- Deleting route-specific response models that the service layer still imports (see `models.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` — remove the 6 direct POST execution routes from the GitHub pull-request router
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084338
- **Related target files**: `scripts/mcp_servers/github/github_server_pull_requests.py`, `tests/mcp_servers/github/test_server_pull_requests.py`

### Companion test files
- `tests/mcp_servers/github/test_server_pull_requests.py`
  - Procedure: remove or update the six route-level tests that post to the deleted pull-request routes.
  - Validation: targeted pytest passes after removal; route-inventory test covers the app.
