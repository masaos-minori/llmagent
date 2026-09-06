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
- ~~`dispatch_tool()` (`scripts/mcp_servers/dispatch.py`) already returns a
  `DispatchResult` shape compatible with what `call_tool()` needs to build a
  `CallToolResponse` — this document's Method section confirms the exact field
  mapping.~~ **DISCONFIRMED (Step 3a, code-implementation cycle, 2026-09-06)** —
  see "Step 3a finding: is_error fidelity regression" below.

### Step 3a finding: is_error fidelity regression (BLOCKING)
Adversarial verification against current source (`scripts/mcp_servers/dispatch.py`,
`scripts/mcp_servers/git/git_service.py`) disconfirms this document's core
Assumption and Design:
- `dispatch_tool()` (`scripts/mcp_servers/dispatch.py:40-67`) wraps ANY non-exception
  string return from a dispatch-table handler as `DispatchResult(output=result,
  is_error=False)` unconditionally — it only sets `is_error=True` when the handler
  raises `ValueError`, or `output=f"Unknown tool: {name}"` for a missing handler.
  It has no way to distinguish a successful op from a policy-rejected one when both
  return a plain `str`.
- `GitService._run_tool()` (`git_service.py:213-237`, unchanged by this Plan's own
  `git_service.py` procedure document, whose Compatibility considerations state the
  5 write-tool handlers stay "byte-for-byte unchanged") returns
  `pipeline_result.output` on success OR `pipeline_result.rejection_message` on a
  Stage-3/5/7 pipeline rejection — both as a **plain `str`**, with no boolean/
  exception signal. `PipelineResult.ok`/`.rejection_message` (`repository_state.py`)
  is discarded before the string ever leaves `_run_tool()`.
- Today (pre-this-Plan), `call_tool()` never calls `GitService.git_checkout`/
  `git_pull`/`git_push` at all — it builds its own local `WriteProtectionPipeline(
  pre_state)` directly (current lines 265-267) and reads `.ok`/`.output` from the
  returned `PipelineResult` itself, which is why `is_error` is accurate today for a
  Stage-3/5/7 rejection (`[DENIED] ... protected branch` / `dirty worktree` /
  `detached HEAD` etc.) via the live `/v1/call_tool` route.
- Switching to `dispatch_tool(_service.get_dispatch_table(), req.name, args)` as this
  document's Design/Procedure literally specifies would make **every** Stage-3/5/7
  rejection of `git_checkout`/`git_pull`/`git_push` come back as `is_error=False`
  (a policy-denied write silently reported as a 200 "success") — a live-tested,
  concrete regression: `tests/mcp_servers/git/test_git_security_compliance.py`'s
  `TestPostConditionBypassPrevention`, `TestHTTPSiblingPathRejection`, and this
  session's own new `TestDryRunAndDetachedHeadLivePath::
  test_dry_run_checkout_protected_branch_still_denied` /
  `test_non_dry_run_detached_head_denied_then_allowed` (added in this Plan's sibling
  `gitdryrun` Plan, already landed) all assert `is_error is True` for exactly this
  case via the live route, and would start failing.
- This directly contradicts this Plan's own Compatibility considerations
  ("Response shape... must stay identical for existing callers of the 3
  currently-working tools") and `REQ-009` ("no behavior change beyond what unifying
  dispatch requires") — the codebase's only other precedent for policy-denial
  signaling through `dispatch_tool()` (`scripts/mcp_servers/shell/shell_server.py`)
  uses a **raised, typed exception** (`ShellAuthorizationError`/
  `ShellValidationError`) caught by a dedicated `@app.exception_handler`, returning a
  distinct HTTP status (403/422) — not a same-shape `CallToolResponse` with
  `is_error=True` at HTTP 200. Adopting that precedent here would itself be an HTTP
  contract change (200+is_error=True → 403/422), which is a different, but equally
  real, behavior change this Plan's own Compatibility considerations forbid.
- **Resolution is out of this document's sole scope**: fixing this requires
  `GitService`/`_run_tool()` (`git_service.py`, this Plan's own sibling target file,
  `implementations/20260905-203805_02_..._git_service.py.md`) to expose a
  structured ok/rejection signal that this file's `call_tool()` can read — a change
  neither this document nor `git_service.py`'s own procedure document currently
  describes or scopes. This is a Plan-level design gap, not a stale line number or
  symbol reference this cycle's Step 3a/3b correction tolerance is meant to absorb.

**Reported as `Blocked: Plan-level design gap — dispatch_tool()/GitService._run_tool()
cannot preserve is_error fidelity for policy-rejected checkout/pull/push without a
coordinated, not-yet-scoped change to git_service.py's return contract` per this
cycle's Step 3a. Not implemented this cycle.**

### Step 3a second finding: dry_run/allow_detached_head not threaded to Stage 5 (BLOCKING, resolved)
Further verification (same cycle) found `GitService._run_tool()`'s
`pipeline.run(tool_name, lambda: op(state.repo, state))` call never passes
`dry_run`/`allow_detached_head` — both silently default to `False` regardless of
the actual request. Confirmed by direct execution: `git_checkout(dry_run=True)`
against a dirty repo is rejected (`[DENIED] worktree has uncommitted changes`) —
the entire `gitdryrun` feature (Stage 5 skip on `dry_run=True`) would silently
break the moment `call_tool()` routes through `GitService` for the first time.
This is a pre-existing latent bug (unreachable via HTTP before this Plan, since
`call_tool()` never called `GitService.git_checkout`/`git_pull`/`git_push`), not
something introduced this session — but activating it live is a direct,
foreseeable consequence of this file's own change, so it must be fixed together.
Also found (same root cause, still unresolved — separate, deeper issue, out of
this fix's minimal scope per user decision): `git_add` (no `dry_run`) against a
dirty repo is *also* rejected by the same always-`dry_run=False` Stage 5 check,
which is arguably wrong for `git_add` regardless of `dry_run` (its whole purpose
is to act on a dirty worktree) — this is a separate design question (should
`GIT_READ_TOOLS`-style Stage-5 bypass extend to `git_add`/`git_commit`?) not
resolved by this fix; flagged here as a known follow-up, not blocking this Plan.

**Resolution (user-approved, minimal scope)**: thread `dry_run`/`allow_detached_head`
through `_run_tool()` to `pipeline.run()`, sourced from each write-tool handler's
own `req.dry_run` / `self._allow_detached_head` — implemented in `git_service.py`
(this Plan's own target file, already archived as
`implementations/done/20260905-203805_02_..._git_service.py.md`; this additional,
narrowly-scoped correction is recorded here since it was discovered during this
file's cycle, not reopened as a new document).

### Step 3a re-verification: unblocked (2026-09-06, later cycle)
`git_service.py`'s own procedure document (`implementations/done/20260905-203805_02_
..._git_service.py.md`) has since landed (commit `23bd6a71d`) with exactly the
coordinated fix this finding called for: `_run_tool()` and every handler method's
early-validation site now `raise ValueError(...)` on a policy/validation rejection
instead of returning it as a plain string. `dispatch_tool()` already converts a
raised `ValueError` into `DispatchResult(is_error=True, output=str(e))` (confirmed,
`scripts/mcp_servers/dispatch.py:40-67`, unchanged) — so this document's original
Design (`dispatch_tool(_service.get_dispatch_table(), req.name, args)`) is now
correct as originally written; no further design change needed in this file.
Re-verified via `rg` against current `git_service.py` (2026-09-06): zero remaining
`return "[DENIED]` sites outside the two provably-dead op-closure lines (see that
document's own finding). Proceeding with the original Design/Procedure below.

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
| 1 | Replace `handlers` dict with `GitService.get_dispatch_table()` dispatch (Procedure steps 1-2) | Completed | 20260906-091500 | 20260906-104500 | Unblocked once `git_service.py`'s contract fix (commit `23bd6a71d`) landed. Also required an additional coordinated fix (Step 3a second finding, user-approved): threaded `dry_run`/`allow_detached_head` through `GitService._run_tool()` to `pipeline.run()`, which was previously always calling it with `dry_run=False`, silently breaking the `gitdryrun` feature the moment dispatch routed through `GitService` |
| 2 | Remove `_dispatch_git_tool()`/`GitMCPServer.dispatch()` after re-confirming zero callers (Procedure step 3) | Completed | 20260906-091500 | 20260906-104500 | `rg '_dispatch_git_tool'` / `rg '\.dispatch\('` reconfirmed zero external callers; both removed |
| 3 | Remove now-dead `_format_checkout`/`_format_pull`/`_format_push` and unused imports, if confirmed dead (Procedure step 4) | Completed | 20260906-091500 | 20260906-104500 | Confirmed dead via `rg` (zero remaining callers after Step 1); removed together with `Callable`/`format_checkout`/`format_pull`/`format_push`/`GitCheckoutRequest`/`GitPullRequest`/`GitPushRequest`/`WriteProtectionPipeline`/`ToolArgs`/`DispatchResult` imports (ruff F401-confirmed unused) |
| 4 | Run validation plan (existing tests + full suite + static checks) | Completed | 20260906-104500 | 20260906-110000 | `tests/mcp_servers/git/`: 238/238 passed (after fixing 3 of this session's own new dry-run/detached-head live-path tests: `_service`'s internal `_allowed_repo_paths`/`_read_only`/`_allow_detached_head` copies, frozen at module-import time from `_cfg`, are no longer kept in sync by patching `_cfg` alone now that dispatch routes through `_service` — test-only fix, patch both; and one test needed an explicit `branch` arg since `GitService.git_pull`/`git_push` require a non-empty branch, unlike the old `format_pull`/`format_push` path). ruff format/check, mypy (`scripts/`), lint-imports, bandit: pass (pre-existing unrelated findings unchanged). Full suite (`--deselect` the known unrelated `test_keyboard_interrupt_breaks_loop` bug): 6309 passed/575 failed/14 skipped/3 errors — zero failures under `tests/mcp_servers/git/` |
| 5 | Update `docs/04_mcp_04_05_git.md`, if in scope per Documentation Impact | Completed | 20260906-110000 | 20260906-110000 | N/A: `docs/00_index.md` has no row naming `docs/04_mcp_04_05_git.md`; this file matches the generic "MCP server implementation" row, whose reference docs contain no claim needing correction (same finding as `git_service.py`'s own document) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `dispatch_tool()`/`GitService._run_tool()` cannot preserve `is_error` fidelity for a policy-rejected `git_checkout`/`git_pull`/`git_push` via the live route without a coordinated, not-yet-scoped change to `git_service.py`'s return contract (see Step 3a finding) | Yes | 20260906-104500 |
| 2 | `GitService._run_tool()` never threaded `dry_run`/`allow_detached_head` to `pipeline.run()`, which would have silently broken the `gitdryrun` feature once dispatch routed through `GitService` (Step 3a second finding) | Yes | 20260906-104500 |

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
