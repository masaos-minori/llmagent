## Goal

Remove the 9 direct POST execution routes and `GET /list_allowed_directories` from `read_server.py`; keep `/health`, `/v1/tools`, `/v1/call_tool`. (`REQ-001`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The 9 routes call `_service.*` directly and bypass dispatch, idempotency/dedup, and audit; removing them removes only the HTTP surface, not tool availability (each tool is reachable via `/v1/call_tool`).
- No external deploy/ops/admin/CI/integration caller posts to these routes (recorded in Plan Risks / AC-6).
- Read-only keyless `/v1/call_tool` stays allowed and documented elsewhere; this file change does not touch it.

## Design decisions
- Delete the `@app.post` decorators and their handler functions together, so no dangling route registration or unused handler remains.
- `/list_allowed_directories` disposition is recorded as a Needs-confirmation item for the maintainer (path-disclosure risk); the procedure marks the decision rather than inventing one.

## Alternatives considered
- Keeping the routes behind the dispatcher: out of scope — this Plan removes the parallel execution contract entirely.
- Removing `/list_allowed_directories` unconditionally: rejected until the maintainer decides; it is a sensitive diagnostic that resolves allowlist paths.

## Implementation
### Target file
`scripts/mcp_servers/file/read_server.py`

### Procedure
1. Delete the 9 direct POST execution-route handlers and registrations at lines 140-274 (`/list_directory`, `/list_directory_with_sizes`, `/directory_tree`, `/read_text_file`, `/read_media_file`, `/read_multiple_files`, `/search_files`, `/grep_files`, `/get_file_info`).
2. Decide and record the disposition of `GET /list_allowed_directories` at line 278 (keep-as-diagnostic or remove); apply the recorded decision.
3. Keep `/health` (line 284), `/v1/tools` (line 317), `/v1/call_tool` (line 332) unchanged.
4. Remove now-unused route-specific imports/response-model names if the linter/mypy flags them and nothing else imports them.

### Method
Locate the route block with `grep -n "@app.post\|@app.get" scripts/mcp_servers/file/read_server.py`; delete each `@app.post("/<route>", response_model=...)` decorator plus its `async def` handler body; handle line 278 per the recorded decision. Confirm no remaining `@app.post` execution route survives.

### Details
- Each removed handler calls `_service.<method>(req)` directly and never touches `_dispatch_*`, the idempotency/dedup path, or `_emit_call_tool_audit` — this is exactly the bypass this Plan removes.
- Availability is preserved because `github_server.py`-style `/v1/call_tool` dispatches the same tools through the shared path; verify the file-read tools still resolve via `/v1/call_tool` in the existing read tests that do not post to a removed route.

## Compatibility considerations
Breaking HTTP-surface removal. External callers must move to `/v1/call_tool`; no backward-compat shim (no-shim policy, `tools/check_compat_shims.py`).

## Security considerations
`/list_allowed_directories` resolves and returns allowlist paths; its disposition (AC-4) is a path-disclosure decision for the maintainer.

## Rollback considerations
Revert the commit.

## Validation plan
- Route-inventory test for the file-read app asserts no operation-specific execution route remains and `/v1/call_tool` is present (`AC-1`, `AC-5`).
- Existing file-read `/v1/call_tool` tests still pass (availability preserved).
- `rg` over `deploy/`, `scripts/ops/`, `scripts/admin/`, `.github/workflows/`, `tests/integration/` finds no external caller of a removed route (`AC-6`).

## Completion criteria
- No `@app.post` execution route remains in `read_server.py`; only `/health`, `/v1/tools`, `/v1/call_tool` (plus the recorded `/list_allowed_directories` disposition) remain.
- `/v1/call_tool` still dispatches file-read tools.
- `/list_allowed_directories` decision is recorded (`AC-4`).

## Out of Scope
- Any change to `/v1/call_tool` behavior, dispatch, or the idempotency-key enforcement (separate rows / sibling Plan).
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
- **Requirement ID**: `REQ-001` — remove the 9 direct POST execution routes and decide `/list_allowed_directories`
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084338
- **Related target files**: `scripts/mcp_servers/file/read_server.py`
