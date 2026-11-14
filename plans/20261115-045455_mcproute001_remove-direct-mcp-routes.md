# Plan: Remove direct MCP execution routes and require idempotency keys for side effects

## Goal
Replace the operation-specific POST execution routes that coexist with `/v1/call_tool` on every MCP FastAPI server with the single `/v1/call_tool` path, and reject keyless side-effecting `/v1/call_tool` requests before dispatch, so every accepted side effect goes through the shared availability gating, argument validation, dedup, and audit path.

## Priority
High

## Scope
- **In-Scope**:
  - Remove the operation-specific POST execution routes from `scripts/mcp_servers/file/{read,write,delete}_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, and the four GitHub router modules under `scripts/mcp_servers/github/`.
  - Keep only `/v1/tools`, `/v1/call_tool`, `/health`, and explicitly approved non-execution diagnostics on every server.
  - Decide and record the disposition of `GET /list_allowed_directories`.
  - Add a shared request-boundary check that rejects a side-effecting tool with an empty `X-Idempotency-Key` before dispatch.
  - Keep keyless read-only calls only if documented and tested.
  - Remove direct-route request/response models after confirming `/v1/call_tool` handlers do not reuse them.
  - Add a route-inventory test per MCP FastAPI app so reintroduction fails.
  - Update server module docstrings and the MCP API reference.
  - Migrate callers: the only current callers of the removed routes are the server definitions themselves and the route-level tests below — no external deploy/ops/admin/CI/integration caller exists.
- **Out-of-Scope**:
  - Redefining the dedup store ownership or retry classes (`plans/20261110-230633_adrrev008_mcp-dedup-ownership.md`).
  - Making WRITE_DANGEROUS tools leave an audit record (`plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md`) — out of scope here.
  - Changing the content of any tool's behavior behind `/v1/call_tool`.
  - Changing disabled-tool rejection semantics.
  - Introducing backward-compatibility shims (`tools/check_compat_shims.py`).
- **Dependencies**:
  - **Depends on**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md` | phase all | the idempotency-key requirement must consume the canonical side-effect tool set that this issue defines; route removal is independent of it.
  - Shares the `scripts/shared/tool_constants.py` routing-authority comment cleanup with `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`; assign the single edit to one of the two (recorded in Assumptions).

## Background
Source: `memo-issue.md` (Issue B), re-verified against current source on 2026-11-15.

- `Explicit in code`: `scripts/mcp_servers/file/read_server.py` registers 9 direct POST execution routes (`/list_directory`, `/list_directory_with_sizes`, `/directory_tree`, `/read_text_file`, `/read_media_file`, `/read_multiple_files`, `/search_files`, `/grep_files`, `/get_file_info`) plus `GET /list_allowed_directories`; `write_server.py` 4 (`/write_file`, `/edit_file`, `/create_directory`, `/move_file`); `delete_server.py` 2 (`/delete_file`, `/delete_directory`); `shell_server.py` 1 (`/shell_run`); `rag_pipeline_server.py` 2 (`/rag_run_pipeline`, `/rag_debug_pipeline`). Each keeps `/health`, `/v1/tools`, `/v1/call_tool`. (checked in Step 2/3)
- `Explicit in code`: the GitHub package registers 21 direct POST execution routes across four router modules — `github_server_file.py` (4), `github_server_issues.py` (5), `github_server_pull_requests.py` (6), `github_server_repository.py` (6). `github_server.py` itself registers only `/v1/call_tool`. (checked in Step 2/3)
- `Confirmed by repository evidence`: the direct routes call service methods directly (`_service.write_file(req)` etc.) and never touch `_dispatch_*`, the idempotency/dedup path, or `_emit_call_tool_audit`. `/v1/call_tool` runs `req.validate_args()`, `_dispatch_*` with `idempotency_key`, and `_emit_call_tool_audit`. (checked in Step 2/3)
- `Confirmed by repository evidence`: `extract_request_context()` in `scripts/mcp_servers/server.py` returns `idempotency_key = ""` when `X-Idempotency-Key` is absent, so a keyless side-effecting `/v1/call_tool` executes today. (checked in Step 2/3)
- `Confirmed by repository evidence`: no repository caller outside the server definitions and the route-level tests posts to any removed route. `rg` over `deploy/`, `scripts/ops/`, `scripts/admin/`, `.github/workflows/`, `tests/integration/` finds none. (checked in Step 2/3)
- `Needs confirmation`: which route-specific request/response models are unreused by `/v1/call_tool` and can be deleted (resolved during implementation by diffing against the dispatch handlers).

## Problem
Direct routes are a second execution contract that skips availability gating, argument validation, dedup, and shared audit. Separately, a keyless side-effecting `/v1/call_tool` always executes (empty idempotency key), so retried or duplicated requests can repeat side effects. Changing only the dispatcher cannot fix the keyless problem while the direct routes remain a parallel path.

## Reason for Change
These routes are a security and reliability bypass on the write, delete, shell, GitHub, and RAG paths. The change is also a breaking API removal, and benefits from being decided before further MCP work builds on `/v1/call_tool`.

## Implementation Intent
- Treat `/v1/call_tool` as the single execution path for every MCP server.
- Enforce the idempotency-key requirement at the shared request boundary (before dispatch) rather than inside `dispatch_tool()`, so read-only tools may stay keyless if the contract says so.
- Make the set of keyed tools come from the single side-effect classification defined by the sibling issue `sideeffect001`, not from a second list.
- Add a route-inventory test per MCP app so reintroduction fails.

## Requirements
- `REQ-001`: Remove the 9 direct POST execution routes and `GET /list_allowed_directories` disposition from `scripts/mcp_servers/file/read_server.py`; keep `/health`, `/v1/tools`, `/v1/call_tool`.
- `REQ-002`: Remove the direct POST execution routes from `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`.
- `REQ-003`: Remove the 21 direct POST execution routes from the four GitHub router modules `scripts/mcp_servers/github/github_server_{file,issues,pull_requests,repository}.py`.
- `REQ-004`: Add a shared request-boundary check rejecting a side-effecting tool with an empty `X-Idempotency-Key` before dispatch (status 400 or 422).
- `REQ-005`: Delete direct-route request/response models that `/v1/call_tool` handlers do not reuse.
- `REQ-006`: Migrate remaining callers; confirm no external deploy/ops/admin/CI/integration caller still uses a removed route.
- `REQ-007`: Add a route-inventory test for every MCP FastAPI app so reintroduction fails.
- `REQ-008`: Update server module docstrings and `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` to remove the direct-route contract and document the idempotency-key requirement and retained non-execution endpoints.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified`; `issue-to-plan` Step 8's Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/file/read_server.py` | Modify | Delete the 9 direct POST execution route handlers and their route registrations; keep `/health`, `/v1/tools`, `/v1/call_tool`, decide `/list_allowed_directories`. | REQ-001 | 9 `@app.post` handlers at lines 140-274 + `GET /list_allowed_directories` line 278; each calls `_service.*` directly, bypassing dispatch (checked in Step 2/3) | route-inventory test (REQ-007); existing file read tests that post to these routes | Verified |
| `scripts/mcp_servers/file/write_server.py` | Modify | Delete the 4 direct POST execution route handlers (`/write_file`, `/edit_file`, `/create_directory`, `/move_file`). | REQ-002 | `@app.post` handlers at lines 130-188 call `_service.*` directly (checked in Step 2/3) | route-inventory test (REQ-007) | Verified |
| `scripts/mcp_servers/file/delete_server.py` | Modify | Delete the 2 direct POST execution route handlers (`/delete_file`, `/delete_directory`). | REQ-002 | `@app.post` handlers at lines 131-156 (checked in Step 2/3) | route-inventory test (REQ-007) | Verified |
| `scripts/mcp_servers/shell/shell_server.py` | Modify | Delete the `/shell_run` direct POST execution route handler. | REQ-002 | `@app.post("/shell_run")` at line 143 calls `_service` directly (checked in Step 2/3) | `tests/mcp_servers/shell/test_shell_server_endpoints.py` (posts `/shell_run`) | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify | Delete the `/rag_run_pipeline` and `/rag_debug_pipeline` direct POST execution route handlers. | REQ-002 | `@app.post` handlers at lines 182-210 (checked in Step 2/3) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | Verified |
| `scripts/mcp_servers/github/github_server_file.py` | Modify | Delete the 4 direct POST execution route handlers. | REQ-003 | `@router.post` at lines 29-110 (checked in Step 2/3) | `tests/mcp_servers/github/test_server_file.py` | Verified |
| `scripts/mcp_servers/github/github_server_issues.py` | Modify | Delete the 5 direct POST execution route handlers. | REQ-003 | `@router.post` at lines 31-115 (checked in Step 2/3) | `tests/mcp_servers/github/test_server_issues.py` | Verified |
| `scripts/mcp_servers/github/github_server_pull_requests.py` | Modify | Delete the 6 direct POST execution route handlers. | REQ-003 | `@router.post` at lines 33-160 (checked in Step 2/3) | `tests/mcp_servers/github/test_server_pull_requests.py` | Verified |
| `scripts/mcp_servers/github/github_server_repository.py` | Modify | Delete the 6 direct POST execution route handlers. | REQ-003 | `@router.post` at lines 33-160 (checked in Step 2/3) | `tests/mcp_servers/github/test_server_repository.py` | Verified |
| `scripts/mcp_servers/server.py` | Modify | Add the shared request-boundary idempotency-key enforcement for side-effecting tools (candidate boundary where `extract_request_context` lives). | REQ-004 | `extract_request_context()` returns `idempotency_key=""` when header absent (lines 151-166) (checked in Step 2/3) | tests for keyless keyless side-effect rejection (REQ-007) | Verified |
| `scripts/mcp_servers/models.py` | Verify/Modify | Confirm whether `/v1/call_tool` handlers reuse direct-route request/response models; delete unreused ones. | REQ-005 | `CallToolRequest`/`CallToolResponse` are shared (lines 15/40); route-specific models resolved during implementation | REQ-005 | Verified |
| `tests/mcp_servers/shell/test_shell_server_endpoints.py` | Modify | Update or remove tests that post to the removed `/shell_run` route. | REQ-006 | `client.post("/shell_run", ...)` at lines 73/86/94 (checked in Step 2/3) | this file | Verified |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | Modify | Update or remove tests that post to the removed RAG routes. | REQ-006 | route-level posts to `/rag_run_pipeline`/`/rag_debug_pipeline` (checked in Step 2/3) | this file | Verified |
| `tests/mcp_servers/github/test_server_file.py` | Modify | Update or remove tests that post to the removed GitHub file routes. | REQ-006 | `client.post("/get_file_contents", ...)` etc. (checked in Step 2/3) | this file | Verified |
| `tests/mcp_servers/github/test_server_issues.py` | Modify | Update or remove tests that post to the removed GitHub issue routes. | REQ-006 | route-level posts (checked in Step 2/3) | this file | Verified |
| `tests/mcp_servers/github/test_server_pull_requests.py` | Modify | Update or remove tests that post to the removed GitHub pull-request routes. | REQ-006 | route-level posts (checked in Step 2/3) | this file | Verified |
| `tests/mcp_servers/github/test_server_repository.py` | Modify | Update or remove tests that post to the removed GitHub repository routes. | REQ-006 | route-level posts (checked in Step 2/3) | this file | Verified |
| `tests/mcp_servers/conftest.py` or a shared route-inventory helper | Create | Provide the route-inventory assertion reused by one test per app. | REQ-007 | no route-inventory test exists today (checked in Step 2/3) | new per-app tests (REQ-007) | Verified |
| `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` | Modify | Remove the direct-route contract; document the `/v1/call_tool`-only execution path and the idempotency-key requirement. | REQ-008 | current API reference under `docs/22_mcp/` (checked in Step 2/3) | N/A | Verified |

Rules:
- One row per file. No directory, glob pattern, component/module name, file group, or vague phrase appears as a row.
- Test, configuration, schema, migration, deployment, or documentation files are their own rows, not folded into the source file they accompany.
- `Validation Status` is `Verified` for every row before freeze. Every path was confirmed to exist via `rg`/`ls` in Step 2/3.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/dispatch.py` | The shared dispatch/dedup path the removed routes bypass; confirms what `/v1/call_tool` gains over the direct routes. | REQ-001..003 |
| `scripts/mcp_servers/audit.py` | `_emit_call_tool_audit` / `_audit_log` signatures used by the shared boundary check (REQ-004). | REQ-004 |
| `scripts/shared/tool_constants.py` | The side-effect tool classification and the contradictory routing-authority comment shared with `rtregistry001`. | REQ-004, Scope |
| `issues/20261111-163800_sideeffect001_side-effect-classification-central.md` | Defines the canonical side-effect tool set the key requirement must consume. | REQ-004 |
| `scripts/mcp_servers/file/read_server.py` (for `/list_allowed_directories` decision) | Sensitive diagnostic returning resolved allowlist paths; read to record its disposition. | REQ-001 |

## Acceptance Criteria
- `AC-1`: No MCP FastAPI app registers an operation-specific execution POST route. (`REQ-001`, `REQ-002`, `REQ-003`)
- `AC-2`: A keyless side-effecting `/v1/call_tool` request is rejected before execution with status 400 or 422. (`REQ-004`)
- `AC-3`: Every accepted side effect passes availability gating, argument validation, common dispatch, dedup, and audit. (`REQ-004`)
- `AC-4`: The `/list_allowed_directories` path-disclosure question has an explicit recorded decision. (`REQ-001`)
- `AC-5`: Route-inventory tests fail if an operation-specific route is reintroduced. (`REQ-007`)
- `AC-6`: No repository caller still uses a removed route (`rg` check recorded). (`REQ-006`)
- `AC-7`: Direct-route request/response models are removed only after confirming `/v1/call_tool` handlers do not reuse them. (`REQ-005`)

## Tests
- Route-inventory tests for each MCP FastAPI app asserting only `/v1/tools`, `/v1/call_tool`, `/health` (and approved diagnostics) are registered. (`REQ-007`, `AC-1`, `AC-5`)
- Tests for keyless side-effecting (rejected), keyed side-effecting (dispatched + deduped), and keyless read-only (documented) requests at `/v1/call_tool`. (`REQ-004`, `AC-2`, `AC-3`)
- Update or remove the route-level tests under `tests/mcp_servers/{shell,rag_pipeline,github}/` that post to removed routes. (`REQ-006`, `AC-6`)
- Regression coverage so a reintroduced direct route fails CI via the route-inventory test. (`REQ-007`)

## Documentation Impact
Update `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` (identified via `docs/00_index.md` → MCP task mapping) to remove the direct-route contract and document the `/v1/call_tool`-only execution path, the idempotency-key requirement, the retained non-execution endpoints, and the `/list_allowed_directories` decision. Do not add literal ports or per-route catalogs (`skills/DESIGN.md` Docs content policy). Run `uv run python tools/generate_reference_table.py --check` if guarded blocks drift. (`REQ-008`)

## Assumptions
- The route removal is a breaking change with no transition period, per the no-shim policy (`tools/check_compat_shims.py`).
- Keyless read-only `/v1/call_tool` calls remain allowed and are documented/tested; the maintainer decides otherwise (UNK-02).
- The `scripts/shared/tool_constants.py` routing-authority comment cleanup is assigned to this Plan or to `rtregistry001`, not both (recorded in Dependencies); the edit lands once.
- The GitHub router modules' direct routes map 1:1 to the tools also reachable via `/v1/call_tool` in `github_server.py`; removing them does not remove tool availability.
- Overlaps: `plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md` covers `/v1/call_tool` audit only (not these routes) and `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md` does not touch routes; both are compatible, not conflicting.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | Where the shared request boundary lives: `scripts/mcp_servers/server.py` (where `extract_request_context` already lives) vs a FastAPI middleware applied to all apps vs `models.py`. | Design trade-off (shared across independent FastAPI apps). | Prefer the shared helper in `server.py` if it is invoked by every app's `/v1/call_tool`; else a common middleware. Record choice in Design. | False |
| `UNK-02` | Whether keyless read-only `/v1/call_tool` calls stay allowed (documented/tested) or require a key. | Maintainer policy decision. | Default: allow keyless read-only, documented and tested (`AC-3`). | False |
| `UNK-03` | Rejection status code (400 vs 422) for a keyless side-effecting request. | Maintainer preference. | Choose 422 (validation error) unless the owner prefers 400. | False |
| `UNK-04` | Disposition of `GET /list_allowed_directories`: keep (sensitive diagnostic, resolves allowlist paths) or remove. | Maintainer decision on path disclosure. | Record explicit decision; if kept, mark it as the sole retained non-execution diagnostic. | False |
| `UNK-05` | Which direct-route request/response models are unreused by `/v1/call_tool` handlers. | Resolved during implementation by diffing route handlers against dispatch handlers. | Delete only confirmed-unused models; keep shared `CallToolRequest`/`CallToolResponse`. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/file/read_server.py` | Modify | file-mcp server callers; removes public HTTP surface | 2 | shared (single-server) | not applicable (rsynced) |
| `scripts/mcp_servers/file/write_server.py` | Modify | file-write-mcp server callers; removes public HTTP surface | 3 | shared (single-server) | not applicable (rsynced) |
| `scripts/mcp_servers/file/delete_server.py` | Modify | file-delete-mcp server callers; removes public HTTP surface | 2 | shared (single-server) | not applicable (rsynced) |
| `scripts/mcp_servers/shell/shell_server.py` | Modify | shell-mcp server callers; removes public HTTP surface | 2 | shared (single-server) | not applicable (rsynced) |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify | rag-mcp server callers; removes public HTTP surface | 2 | shared (single-server) | not applicable (rsynced) |
| `scripts/mcp_servers/github/github_server_{file,issues,pull_requests,repository}.py` | Modify | github-mcp server callers; removes public HTTP surface | 5 | shared (single-server) | not applicable (rsynced) |
| `scripts/mcp_servers/server.py` | Modify | every MCP app if boundary is shared | 8 | shared (cross-server) | not applicable (rsynced) |
| `scripts/mcp_servers/models.py` | Modify/Verify | request model consumers | 1 | shared (single-server) | not applicable (rsynced) |
| `tests/mcp_servers/{shell,rag_pipeline,github}/*` | Modify | test suite for affected servers | 6 | shared (test suite) | not applicable (rsynced) |
| `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` | Modify | API consumers reading the reference | 1 | N/A | N/A |

## Design
Path B: affects > 3 files and changes a public/runtime HTTP interface (breaking removal of routes).

- **Route removal**: delete the `@app.post`/`@router.post` execution-route decorators and their handler functions from the nine target files. Keep `/health`, `/v1/tools`, `/v1/call_tool`. For the GitHub routers, the 21 exec routes live only in the four `github_server_*` router modules; `github_server.py` already exposes those tools solely through `/v1/call_tool`, so removal preserves tool availability. (Step 3)
- **Shared request boundary (REQ-004)**: the enforcement must run before dispatch on every app. Candidate is a shared helper in `server.py` (co-located with `extract_request_context`), invoked by each app's `/v1/call_tool` handler, or a FastAPI middleware registered on every app. The set of "side-effecting tools" must come from the canonical classification in `tool_constants.py` (once `sideeffect001` defines it), not a second list. Until then, the plan records the requirement and defers the exact set to that issue (UNK-05 resolution happens at implementation). (Step 3)
- **Model cleanup (REQ-005)**: `CallToolRequest`/`CallToolResponse` in `models.py` are shared and stay. Route-specific request/response models (e.g. `WriteFileRequest`, `ShellRunRequest`, GitHub route models) are deleted only after confirming the dispatch handlers build their own request models rather than importing the route ones. (Step 3)
- **Blast radius**: the removed routes are HTTP-surface only; service methods are unchanged, so in-process callers (if any) are unaffected. The only external references are the seven route-level test files, all listed as targets. (Step 3)
- **Complexity baseline**: `radon cc` shows `dispatch_tool` at complexity F (44); route handlers themselves are thin, so removal lowers complexity. (Step 5)

## Implementation steps
Each step cites the exact file path(s) it touches by referencing rows of `Implementation Target Files` above.

1. **Phase 1: Remove direct execution routes**
   - [ ] Delete the 9 direct POST execution routes and decide `/list_allowed_directories` in `scripts/mcp_servers/file/read_server.py`. [`scripts/mcp_servers/file/read_server.py`] (REQ-001)
   - [ ] Delete the 4 write, 2 delete, 1 shell, 2 RAG direct routes. [`scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`] (REQ-002)
   - [ ] Delete the 21 direct routes across the four GitHub router modules. [`scripts/mcp_servers/github/github_server_file.py`, `scripts/mcp_servers/github/github_server_issues.py`, `scripts/mcp_servers/github/github_server_pull_requests.py`, `scripts/mcp_servers/github/github_server_repository.py`] (REQ-003)
2. **Phase 2: Shared idempotency-key enforcement**
   - [ ] Add the shared request-boundary check rejecting keyless side-effecting tools before dispatch. [`scripts/mcp_servers/server.py`] (REQ-004)
   - [ ] Confirm shared vs route-specific models; delete unreused direct-route models. [`scripts/mcp_servers/models.py`] (REQ-005)
3. **Phase 3: Callers and tests**
   - [ ] Confirm no external caller uses a removed route; update/remove the seven route-level tests. [`tests/mcp_servers/{shell,rag_pipeline,github}/*`] (REQ-006)
   - [ ] Add a route-inventory test per MCP FastAPI app. [`tests/mcp_servers/conftest.py` or shared helper + one test per app] (REQ-007)
4. **Phase 4: Documentation**
   - [ ] Update `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` for the `/v1/call_tool`-only path and idempotency-key requirement. [`docs/22_mcp/mcp_02_01_endpoints-and-transport.md`] (REQ-008)
5. **Phase 5: Validation suite**
   - [ ] Run the full validation sequence (`rules/toolchain.md`): ruff, mypy, import-linter, bandit, targeted pytest, and `uv run python tools/check_docs_consistency.py --domain mcp`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/**/*_server.py` | Integration: no exec route registered; `/v1/call_tool` still works | route-inventory tests; targeted pytest | Pass |
| `scripts/mcp_servers/server.py` | Unit: keyless side-effect rejected, keyed dispatched, keyless read allowed | targeted pytest | Pass |
| `tests/mcp_servers/{shell,rag_pipeline,github}/*` | Regression: removed-route tests updated/removed | targeted pytest | Pass |
| `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` | Doc consistency | `uv run python tools/check_docs_consistency.py --domain mcp` | Pass |

## Risks
- **Risk**: Removing a route that some external caller depends on breaks production. → **Mitigation**: `rg` over `deploy/`, `scripts/ops/`, `scripts/admin/`, `.github/workflows/`, `tests/integration/` found no external caller (recorded in Step 2/3); `AC-6` re-runs the `rg` check at completion.
- **Risk**: The shared boundary in `server.py` is not actually on the request path of every app. → **Mitigation**: verify each app's `/v1/call_tool` invokes the shared helper, or use a common middleware; covered by the keyless-rejection test per app (`AC-2`).
- **Risk**: Deleting a request/response model that `/v1/call_tool` imports breaks dispatch. → **Mitigation**: `AC-7` requires confirming reuse before deletion; mypy catches stray imports.
- **Risk**: The key-enforcement cannot reference the canonical side-effect set until `sideeffect001` lands. → **Mitigation**: record `UNK-05`; route removal (Phases 1) proceeds independently; key enforcement (Phase 2) sequences after `sideeffect001`.
- **Risk**: Breaking change to the MCP HTTP surface conflicts with the no-shim policy. → **Mitigation**: no shims added; `tools/check_compat_shims.py` in the validation suite.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove direct execution routes (file, shell, RAG, GitHub) | Pending | — | — | REQ-001/002/003 |
| 2 | Shared idempotency-key enforcement + model cleanup | Pending | — | — | REQ-004/005 |
| 3 | Caller migration + route-inventory tests | Pending | — | — | REQ-006/007 |
| 4 | Documentation update | Pending | — | — | REQ-008 |
| 5 | Validation suite | Pending | — | — | rules/toolchain.md |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-045455
- **Related target files**: `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/github/github_server_file.py`, `scripts/mcp_servers/github/github_server_issues.py`, `scripts/mcp_servers/github/github_server_pull_requests.py`, `scripts/mcp_servers/github/github_server_repository.py`, `scripts/mcp_servers/server.py`, `scripts/mcp_servers/models.py`, `tests/mcp_servers/shell/test_shell_server_endpoints.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`, `tests/mcp_servers/github/test_server_file.py`, `tests/mcp_servers/github/test_server_issues.py`, `tests/mcp_servers/github/test_server_pull_requests.py`, `tests/mcp_servers/github/test_server_repository.py`, `docs/22_mcp/mcp_02_01_endpoints-and-transport.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; remove direct routes | `scripts/mcp_servers/file/read_server.py` | Phase 1 | AC-1, AC-4 | route-inventory test | Confirmed by repository evidence |
| REQ-002 | Required Changes; remove direct routes | `scripts/mcp_servers/file/write_server.py`, `delete_server.py`, `shell/shell_server.py`, `rag_pipeline/rag_pipeline_server.py` | Phase 1 | AC-1 | route-inventory test | Confirmed by repository evidence |
| REQ-003 | Strongly implied by code (21 routes, 4 routers) | `scripts/mcp_servers/github/github_server_{file,issues,pull_requests,repository}.py` | Phase 1 | AC-1 | route-inventory test | Confirmed by repository evidence |
| REQ-004 | Implementation Intent; Required Changes (key enforcement) | `scripts/mcp_servers/server.py` | Phase 2 | AC-2, AC-3 | keyless/keyed tests | Needs confirmation (boundary choice UNK-01) |
| REQ-005 | AI Implementation Instruction; remove unused models | `scripts/mcp_servers/models.py` | Phase 2 | AC-7 | mypy | Confirmed by repository evidence |
| REQ-006 | Required Changes; migrate callers | `tests/mcp_servers/{shell,rag_pipeline,github}/*` | Phase 3 | AC-6 | rg check; targeted pytest | Confirmed by repository evidence |
| REQ-007 | Required Changes; route-inventory tests | new shared helper + per-app tests | Phase 3 | AC-5 | route-inventory tests | Confirmed by repository evidence |
| REQ-008 | Documentation Impact | `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` | Phase 4 | N/A: doc-only | check_docs_consistency | Confirmed by repository evidence |
