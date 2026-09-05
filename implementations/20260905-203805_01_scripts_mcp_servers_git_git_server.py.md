## Goal
Make `POST /v1/call_tool` dispatch every one of the 10 advertised git tools through
`GitService.get_dispatch_table()` instead of its own inline 3-tool `handlers` dict
(`REQ-002`: unify canonical dispatch), and remove the now-fully-unreachable
`GitMCPServer.dispatch()` / `_dispatch_git_tool()` alternative (`REQ-006`).

## Scope
- In scope: `call_tool()`'s inline `handlers` dict (lines 257-264) and the
  `pipeline.run(req.name, handler)` call immediately after it; deleting
  `_dispatch_git_tool()` and `GitMCPServer.dispatch()`.
- Out of scope: `GitService._run_tool()`'s read-only bypass logic (`REQ-003`/`REQ-004`,
  implemented in `scripts/mcp_servers/git/git_service.py` — see its own procedure
  document); `WriteProtectionPipeline` internals (`gitauth`/`gitpipeline`/`gitdryrun`'s
  scope); tool names, arguments, or read-only output format (`REQ-009`).

## Assumptions
- `GitService.get_dispatch_table()` already returns correctly-typed handlers for all
  10 `git_*` methods (confirmed: `scripts/mcp_servers/git/git_service.py` lines
  241-411 define one method per tool, each calling `self._run_tool(...)`).
- `dispatch_tool()` (`scripts/mcp_servers/dispatch.py`) already returns a
  `DispatchResult` shape compatible with what `call_tool()` needs to build a
  `CallToolResponse` — this document's Method section confirms the exact field
  mapping.

## Design decisions
- Replace the inline `handlers` dict with a single `dispatch_tool(_service.get_dispatch_table(), req.name, args)` call, reusing the existing `_dispatch_git_tool()` helper's pattern rather than inlining `dispatch_tool()` a second time — one call site, not two.
- Keep `call_tool()`'s pre-dispatch logic (availability check, path validation, `pre_state`/`post_state` snapshotting, audit logging) unchanged; only the dispatch step itself changes, per `REQ-009`'s "no behavior change beyond what unifying dispatch requires".
- Delete `_dispatch_git_tool()` and `GitMCPServer.dispatch()` in the same change as the `handlers` dict replacement, not a follow-up — leaving them in place after `call_tool()` no longer needs its own `WriteProtectionPipeline`-wrapping call would create a second, subtly different dispatch path (`REQ-006`).

## Alternatives considered
- Hand-port the 7 missing tools' request construction directly into `call_tool()`'s `handlers` dict: rejected — duplicates logic `GitService`'s methods already have correctly (Plan's Design section).
- Keep both `handlers` and `get_dispatch_table()` dispatch paths and manually keep them in sync: rejected — this is the exact drift this Plan exists to eliminate.

## Implementation
### Target file
`scripts/mcp_servers/git/git_server.py`

### Procedure
1. In `call_tool()` (currently lines 185-288), after building `pre_state` (line 254-256)
   and before the existing post-processing (post-snapshot, audit log, response), replace
   the `handlers` dict block (lines 257-264) and the `pipeline = WriteProtectionPipeline(pre_state); result = pipeline.run(req.name, handler)` block (lines 265-266) with a single
   dispatch call through `GitService.get_dispatch_table()`.
2. Confirm the replacement produces a `result` object exposing the same `.ok` /
   `.output` / rejection-message shape the current code already reads at lines
   267-288 (`post_state = ...`, `result.ok`, `result.output`) — if `dispatch_tool()`'s
   `DispatchResult` shape differs, adapt the read sites, not `DispatchResult` itself
   (it is shared infrastructure in `scripts/mcp_servers/dispatch.py`, out of scope
   here).
3. Remove `_dispatch_git_tool()` (lines 150-152) and `GitMCPServer.dispatch()`
   (lines 355-357) once step 1 lands — re-run `rg '\.dispatch\('` and
   `rg '_dispatch_git_tool'` immediately before deleting, per the Plan's own Risk
   mitigation, to reconfirm no caller was added since this document's Step 3a
   revalidation (both confirmed zero external callers as of this cycle).
4. Confirm `handlers`' now-unused `Callable` import (line 25) and the now-unused
   `format_checkout`/`format_pull`/`format_push` import (line 36) — remove only if
   step 1-3 leaves them genuinely unused (`GitMCPServer._format_checkout`/
   `_format_pull`/`_format_push`, lines 320-353, currently the only callers of those
   three format functions; confirm whether those static methods themselves become
   dead code once `handlers` is removed, and remove them together if so — do not
   leave a newly-dead private method behind).

### Method
`call_tool()`'s existing flow (availability check → arg validation → path resolution
→ `pre_state` snapshot) is unchanged. Only the dispatch step changes: instead of
building a 3-entry `handlers` dict and manually instantiating
`WriteProtectionPipeline`, delegate to `GitService.get_dispatch_table()` (via
`dispatch_tool()`), which already runs each tool's method — and, once
`scripts/mcp_servers/git/git_service.py`'s own procedure document lands `REQ-003`'s
read-only bypass — applies `WriteProtectionPipeline` only to `GIT_WRITE_TOOLS`.

### Details
- `_service` (the module-level `GitService` instance `call_tool()` already has
  access to via `_dispatch_git_tool()`) is the same instance `.get_dispatch_table()`
  is called on.
- The unknown-tool case (`handlers.get(req.name)` returning `None` today, line
  262-264) must still surface as `CallToolResponse(result=f"Unknown tool: {req.name}", is_error=True)` — confirm `dispatch_tool()` / `GitService.get_dispatch_table()`
  already reject unregistered tool names this way (or adapt the read site to
  preserve this response shape); this is `REQ-005`/`AC-4`'s existing
  unknown-tool-rejection behavior, which this change must not regress.
- `pre_state` is currently passed into each `handlers` lambda directly (e.g.
  `GitMCPServer._format_checkout(pre_state, req)`); `GitService`'s own `_run_tool()`
  builds its own `RepositoryState.snapshot()` internally rather than accepting one
  from the caller — confirm whether `call_tool()`'s separately-built `pre_state`
  (used again at line 267 for `post_state`, and audit logging) becomes redundant
  with `GitService._run_tool()`'s internal snapshot, or whether both are still
  needed (one for `call_tool()`'s audit/response bookkeeping, one internal to
  `GitService`) — this is a Non-blocking evidence gap noted here for the
  implementer to resolve at implementation time; it does not block writing this
  procedure, since either resolution stays within this file's dispatch-call
  replacement scope.

## Compatibility considerations
- `GET /v1/tools`' `_annotate_tool()`/`_git_tool_availability()` behavior (REQ-005,
  AC-4) is untouched by this file's change — same function, same gating logic.
- Response shape (`CallToolResponse(result=..., is_error=...)`) must stay identical
  for existing callers of the 3 currently-working tools (`git_checkout`/`git_pull`/
  `git_push`) — this is a refactor of *how* the result is produced, not a change to
  its shape.

## Security considerations
- `_git_tool_availability()`'s `allowed_repo_paths`/`read_only` gating (REQ-005) runs
  before dispatch and is unchanged — the 7 newly-reachable tools inherit the same
  gating already applied to the 3 currently-reachable ones.
- Removing `GitMCPServer.dispatch()`/`_dispatch_git_tool()` eliminates the only other
  code path capable of invoking git operations outside `call_tool()`'s own
  audit-logging/path-validation wrapper (REQ-006) — confirmed zero external callers
  via `rg '\.dispatch\('` and `rg '_dispatch_git_tool'` this cycle.

## Rollback considerations
- Single-file, mechanical dispatch-call replacement; revertible via `git revert` of
  this file's commit alone — no schema, config, or cross-service state changes.
- If `dispatch_tool()`'s `DispatchResult` shape proves incompatible in a way that
  requires changing shared `scripts/mcp_servers/dispatch.py`, stop and report
  `Blocked: additional target file discovered — scripts/mcp_servers/dispatch.py`
  rather than modifying it under this document's scope.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py tests/mcp_servers/git/test_mcp_git.py tests/mcp_servers/git/test_tools_endpoint.py -v` —
  existing checkout/pull/push HTTP tests must keep passing (no response-shape
  regression); `test_tools_endpoint.py`'s existing `read_only`/`allowed_repo_paths`
  gating tests must keep passing (REQ-005/AC-4).
- `uv run pytest tests/mcp_servers/git/ -v` (full suite) — no new failures.
- `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`,
  `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- `call_tool()` dispatches through `GitService.get_dispatch_table()` for all 10 tool
  names; none of the 10 return `"Unknown tool"` (AC-1).
- `GitMCPServer.dispatch()` and `_dispatch_git_tool()` no longer exist in this file
  (AC-5), confirmed by `rg` finding zero remaining references.
- Existing checkout/pull/push tests and `test_tools_endpoint.py` pass unchanged.

## Out of scope
- `WriteProtectionPipeline`'s internal precondition/postcondition logic
  (`gitauth`/`gitpipeline`/`gitdryrun`'s Plans).
- The read-only-vs-write split inside `_run_tool()` — that is
  `scripts/mcp_servers/git/git_service.py`'s own procedure document (`REQ-003`,
  `REQ-004`).
- `docs/04_mcp_04_05_git.md` update — deferred to implementation time per the
  Plan's Documentation Impact section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace `handlers` dict with `GitService.get_dispatch_table()` dispatch (Procedure steps 1-2) | Pending | — | — | |
| 2 | Remove `_dispatch_git_tool()`/`GitMCPServer.dispatch()` after re-confirming zero callers (Procedure step 3) | Pending | — | — | |
| 3 | Remove now-dead `_format_checkout`/`_format_pull`/`_format_push` and unused imports, if confirmed dead (Procedure step 4) | Pending | — | — | |
| 4 | Run validation plan (existing tests + full suite + static checks) | Pending | — | — | |
| 5 | Update `docs/04_mcp_04_05_git.md`, if in scope per Documentation Impact | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (route `call_tool()` through `GitService.get_dispatch_table()`), `REQ-006` (remove the unreachable `GitMCPServer.dispatch()`/`_dispatch_git_tool()` alternative)
- **Source issue**: issues/20260902-144910_gitdispatch_unify_git_mcp_tool_dispatch_and_write_protection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191458_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-203805
- **Related target files**: scripts/mcp_servers/git/git_server.py
