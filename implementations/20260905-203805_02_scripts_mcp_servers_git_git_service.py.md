## Goal
Split `GitService._run_tool()` so read-only tools (`GIT_READ_TOOLS`) execute directly
against a validated repo, bypassing `WriteProtectionPipeline`'s write-only precondition/
postcondition stages (`REQ-003`), while write tools (`GIT_WRITE_TOOLS`) continue through
the pipeline exactly as today (`REQ-004`), and confirm `_git_tool_availability()`'s
`read_only`-gating (`REQ-005`) is unaffected by this change (it lives in
`scripts/mcp_servers/git/git_server.py`, not this file — this document only confirms
no dependency on this file's change).

## Scope
- In scope: `_run_tool()` (lines 213-237) — branch on whether `tool_name` is in
  `GIT_READ_TOOLS` vs `GIT_WRITE_TOOLS` before deciding whether to construct a
  `WriteProtectionPipeline`.
- **In scope (added 2026-09-06, code-implementation cycle, per user decision — see
  "Added scope: rejection signaling contract fix" below)**: every "[DENIED] ..." /
  validation-failure early-return site in this file (`_validate_repo()`'s
  `error_message` check in `_run_tool()`, `_run_tool()`'s own pipeline-rejection
  branch, and each handler method's own `_validate_ref()`/`_validate_protected()`
  early returns) — convert from `return err` to `raise ValueError(err)`.
- Out of scope: any individual `git_*` handler method's own per-tool validation
  logic itself (`_validate_ref`, `_validate_protected`, dry-run handling in
  `git_checkout`/`git_pull`/`git_push`) — only *how a failure is signaled* changes
  (return → raise), not the validation logic itself; `get_dispatch_table()` (lines
  412-423, already correctly maps all 10 tools, confirmed unchanged);
  `WriteProtectionPipeline` internals (`scripts/mcp_servers/git/repository_state.py`,
  `gitauth`/`gitpipeline`/`gitdryrun`'s scope) — `PipelineResult.ok`/
  `.rejection_message`'s own fields are unchanged, only how `_run_tool()` reads them
  changes; `scripts/mcp_servers/dispatch.py` (shared infra, unchanged — this fix
  works entirely within its existing `except ValueError` handling, already used by
  every other MCP server in this codebase for policy/validation rejections, e.g.
  `scripts/mcp_servers/shell/shell_service.py`'s `ShellValidationError(ValueError)`).

### Added scope: rejection signaling contract fix (BLOCKING finding from sibling file)
`implementations/20260905-203805_01_..._git_server.py.md`'s Step 3a adversarial
verification (code-implementation cycle, 2026-09-06) found that this Plan's
`git_server.py` document cannot switch `call_tool()` to
`dispatch_tool()`/`GitService.get_dispatch_table()` without a live regression: every
"[DENIED] ..." string this file's methods currently `return` (rather than raise) is
wrapped by `dispatch_tool()` as `DispatchResult(output=<string>, is_error=False)` —
a policy-rejected write reported as a 200 "success". The user selected fixing this
file's contract (raise `ValueError` for every rejection, since `dispatch_tool()`
already converts a raised `ValueError` into `DispatchResult(is_error=True, ...)` —
no change to shared `dispatch.py` needed) over the alternative (a `shell-mcp`-style
raised+typed-exception-with-dedicated-HTTP-status design, which would itself change
this Plan's response-shape compatibility guarantee).

Sites requiring `return err` → `raise ValueError(err)` (verified against current
source, 2026-09-06):
- `_run_tool()` line 226-227: `if result.error_message: return result.error_message`
- `_run_tool()` line 236-237: `return pipeline_result.rejection_message` (the `if
  pipeline_result.ok: return pipeline_result.output` line above it is unchanged)
- `git_log()` lines 256-257, `git_diff()` lines 272-273, `git_show()` lines 292-293
  (each a single `_validate_ref()` early return)
- `git_checkout()` lines 331-332 (`_validate_ref`) and 334-335 (`_validate_protected`)
- `git_pull()` lines 360-361 (`_validate_ref` branch), 363-364 (`_validate_protected`),
  366-367 (`_validate_ref` remote) — line numbers per current source, three checks
- `git_push()` — same three-check shape as `git_pull()`, own line numbers
- **`_checkout_op()`/`_pull_op()`/`_push_op()`'s inline `if not req.dry_run: if
  state.is_dirty: return "[DENIED]..."` / `if state.is_detached_head...: return
  "[DENIED]..."` (each op closure, e.g. `git_checkout()` lines 344-349) are
  EXCLUDED from this conversion — do not raise here.** These closures run as
  `WriteProtectionPipeline.run()`'s Stage 6 `op()` callable
  (`repository_state.py`'s `run()`), which wraps any non-`GitServiceError`
  exception from `op()` into a re-raised `GitServiceError` (Stage 6's own
  try/except) — `git_server.py` has a registered `@app.exception_handler(
  GitServiceError)` returning **HTTP 500**, not this fix's intended 200+
  `is_error=True` shape. Raising `ValueError` here would be silently wrong if this
  code were ever reached. It is provably unreachable today regardless (Stage 5's
  `RepositoryState.verify_preconditions()` already performs the identical
  dirty/detached check and rejects via a normal `PipelineResult.reject(...)` return
  *before* Stage 6/this closure ever runs) — leave it as `return "[DENIED]...")`
  unchanged; removing this dead code is a separate, out-of-scope cleanup.

This changes `GitService`'s own public method contract: existing direct-unit-test
callers (`tests/mcp_servers/git/test_git_security_compliance.py`'s
`TestGitSecurityCompliance` class, e.g. `test_git_checkout_protected_branch`,
`test_git_push_protected_branch`, `test_git_pull_protected_branch`,
`test_git_pull_unsafe_remote`, `test_git_show_unsafe_ref`,
`test_git_checkout_dirty_worktree_denied`, `test_git_pull_dirty_worktree_denied`,
`test_git_checkout_detached_head_denied`, `test_git_pull_detached_head_denied`, and
the parametrized `test_write_tools_reject_shipped_protected_branches`) currently
assert `"[DENIED]" in result` against a returned string — each must change to
`with pytest.raises(ValueError, match=...` instead. This file
(`test_git_security_compliance.py`) is itself this Plan's own target-file row 5
(`implementations/20260905-203805_05_..._test_git_security_compliance.py.md`) — the
required update is in-scope there, not a new additional-target-file discovery.

## Assumptions
- `GIT_READ_TOOLS` (`git_status`/`git_log`/`git_diff`/`git_branch`/`git_show`) and
  `GIT_WRITE_TOOLS` (`git_add`/`git_commit`/`git_checkout`/`git_pull`/`git_push`) from
  `scripts/shared/tool_constants.py` are the authoritative classification — confirmed
  present and matching this Plan's Requirements text.
- None of the 5 read-only handler methods (`git_status`/`git_log`/`git_diff`/
  `git_branch`/`git_show`, lines 241-296) pass a non-empty `active_ref` to `_run_tool()`
  today (confirmed: none of their calls set `active_ref=`) — so the read-only branch
  does not need to handle `active_ref`-dependent postcondition logic, only the
  write-tool branch does.

## Design decisions
- Branch inside `_run_tool()` itself (one shared entry point all 10 handler methods already call) rather than adding a second method (`_run_read_only_tool()`) — keeps one call site per handler method unchanged, and keeps the read/write split in exactly one place.
- For the read-only branch, reuse the existing `_wrap_git_op()` helper (lines 205-211) for error wrapping, matching the same `GitServiceError` conversion `WriteProtectionPipeline.run()`'s Stage 6 already does for the write branch — so error-handling behavior stays consistent across both branches, only the precondition/postcondition stages differ.
- Do not change `WriteProtectionPipeline`'s own `run()` signature or internals (`scripts/mcp_servers/git/repository_state.py`) — the branch happens entirely in `_run_tool()`, before `WriteProtectionPipeline` is even constructed for read-only tools.

## Alternatives considered
- Pass a `skip_write_checks: bool` flag into `WriteProtectionPipeline.run()` and branch inside it: rejected — would require modifying `repository_state.py`, out of scope per this Plan's Reference Files (`gitauth`/`gitpipeline`/`gitdryrun` own that file's internals) and would entangle this Plan's dispatch-unification concern with pipeline-internal changes.
- Add per-tool `if tool_name in GIT_READ_TOOLS: ...` branches inside each of the 5 read-only handler methods individually: rejected — duplicates the same branch 5 times instead of once in the shared `_run_tool()`.

## Implementation
### Target file
`scripts/mcp_servers/git/git_service.py`

### Procedure
1. Import `GIT_READ_TOOLS` from `scripts/shared/tool_constants.py` alongside the
   existing import (confirm current import list at the top of the file; `GIT_WRITE_TOOLS`
   equivalent is not currently imported into this file either — check whether either
   constant is already imported before adding).
2. In `_run_tool()` (lines 213-237), after building `state = RepositoryState.snapshot(...)`
   (lines 228-232), branch:
   - If `tool_name in GIT_READ_TOOLS`: call `self._wrap_git_op(tool_name, lambda: op(state.repo, state))` directly and return its result — no `WriteProtectionPipeline` construction, no precondition/postcondition checks.
   - Else (write tool): keep the existing `pipeline = WriteProtectionPipeline(state); pipeline_result = pipeline.run(tool_name, lambda: op(state.repo, state)); ...` logic (lines 233-237) exactly as-is.
3. Confirm `_wrap_git_op()`'s return type (`str`, same as `op()`'s return type) matches
   what `_run_tool()`'s callers already expect (each `git_*` handler method returns
   `_run_tool()`'s return value directly) — no caller-side change needed if so.
4. **(Added scope)** Convert every "[DENIED] ..." early-return site listed in "Added
   scope: rejection signaling contract fix" above from `return err` to
   `raise ValueError(err)`: `_run_tool()`'s `_validate_repo()`-error branch and
   pipeline-rejection branch; `git_log`/`git_diff`/`git_show`'s single `_validate_ref`
   early return each; `git_checkout`/`git_pull`/`git_push`'s `_validate_ref`/
   `_validate_protected` early returns; and `_checkout_op`/`_pull_op`/`_push_op`'s
   inline dirty/detached-HEAD checks. Re-run `rg '"\[DENIED\]'` against this file
   after editing to confirm no `return "[DENIED]...")` site remains unconverted.

### Method
`_run_tool()` currently unconditionally does: validate repo → snapshot state → wrap in
`WriteProtectionPipeline` → run pipeline (Stage 3 authorization, Stage 5 precondition,
Stage 6 execution, Stage 7 postcondition) → return `.output` or `.rejection_message`.
The read-only branch skips straight from "snapshot state" to "execute `op()` via
`_wrap_git_op()`", skipping Stage 3/5/7 entirely — those stages exist specifically to
gate write operations (protected-branch authorization, dirty-worktree/detached-HEAD
preconditions, dirty-worktree postconditions), none of which apply to a read.

### Details
- `op` (the `Callable[[git.Repo, RepositoryState], str]` each handler method passes in,
  e.g. `lambda repo, _state: format_status(repo)` for `git_status`) is invoked
  identically in both branches — same call signature `op(state.repo, state)` — only the
  wrapping around it differs (pipeline stages vs. direct `_wrap_git_op()`).
- `_validate_repo()` (called at line 225, before the branch) is unchanged — both
  read-only and write tools go through the same repo-path/read-only-gating validation
  before this method's branch point (a different check from `_git_tool_availability()`
  in `git_server.py`). Today, only write tools (`git_checkout`/`git_pull`/`git_push`)
  reach `_run_tool()` via the live `/v1/call_tool` path; read-only tools have never been
  exercised through this method via HTTP before this Plan lands (made reachable for the
  first time by `git_server.py`'s own procedure document, `REQ-002`). Confirm during
  implementation that `_validate_repo()`'s existing checks encode no write-only
  assumption that would misbehave for a read-only call; treat any such finding
  surfaced by the new read-only HTTP tests
  (`tests/mcp_servers/git/test_git_security_compliance.py`'s procedure document) as an
  in-scope fix per the Plan's own Risk section, not a deferred follow-up.
- `active_ref` defaults to `""` for all 5 read-only handler methods' calls (per
  Assumptions above) — the read-only branch does not need to thread `active_ref`
  anywhere, since it skips the postcondition stage that would have used it.

## Compatibility considerations
- The 5 write-tool handler methods' *validation logic and pipeline construction* are
  unchanged — same stages, same conditions. **Superseded by the Added scope above**:
  the *signaling shape* of a rejection changes from `return "[DENIED]..."` to
  `raise ValueError("[DENIED]...")`, an intentional, in-scope contract change (see
  "Added scope: rejection signaling contract fix") — existing direct-unit-test
  callers must be updated accordingly (this Plan's own `test_git_security_
  compliance.py` target-file row).
- `get_dispatch_table()` (lines 412-423) needs no change — it already maps all 10
  tool names to their respective handler methods; only what happens *inside*
  `_run_tool()` and each handler's early-validation sites changes.

## Security considerations
- Read-only tools bypassing `WriteProtectionPipeline` is the intended behavior change
  (`REQ-003`) — confirm the branch condition is `tool_name in GIT_READ_TOOLS`
  (allowlist), not `tool_name not in GIT_WRITE_TOOLS` (denylist), so an unrecognized
  future tool name defaults to the safer (pipeline-wrapped) path rather than silently
  bypassing write protection.
- `_validate_repo()` and `_git_tool_availability()`'s (in `git_server.py`)
  `allowed_repo_paths`/`read_only` gating both still run before either branch —
  this change only affects what happens once a tool call is already authorized to
  reach `_run_tool()`.

## Rollback considerations
- Single-method branch change; revertible via `git revert` alone.
- If `_validate_repo()` is found to encode write-only assumptions that break for
  read-only tools in a way that requires modifying `_validate_repo()` itself, this
  stays within this same target file (`git_service.py`) — not an additional-target-file
  discovery, since `_validate_repo()` is defined in this file too.
- The Added-scope rejection-signaling change is revertible together with this file's
  commit; it must land in the same commit as `test_git_security_compliance.py`'s
  updated `TestGitSecurityCompliance` assertions (row 5) — reverting one without the
  other breaks that test class.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py -v` — this file's
  own procedure document adds the read-only-bypass-vs-write-pipeline unit tests
  (`REQ-003`, `REQ-004`); this document's implementation must make those tests pass.
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` — the
  `TestGitSecurityCompliance` class's rejection tests must be updated (row 5) to
  expect a raised `ValueError` instead of a returned string, and pass against this
  change.
- `uv run pytest tests/mcp_servers/git/ -v` (full suite) — no new failures, especially
  the existing write-tool pipeline tests in `test_git_security_compliance.py`
  (dirty-worktree/detached-HEAD denial tests for checkout/pull/push must still pass,
  once updated to the raise-based contract).
- `uv run mypy scripts/mcp_servers/git/`, `uv run ruff check scripts/mcp_servers/git/`.

## Completion criteria
- `GIT_READ_TOOLS` calls to `_run_tool()` do not construct a `WriteProtectionPipeline`
  and are not rejected by dirty-worktree/detached-HEAD checks (AC-3).
- `GIT_WRITE_TOOLS` calls continue through `WriteProtectionPipeline` with identical
  validation behavior to today (AC-2), signaled via a raised `ValueError` instead of
  a returned string on rejection.
- No "[DENIED] ..." string is `return`ed by this file on a rejection path — confirmed
  via `rg '"\[DENIED\]' scripts/mcp_servers/git/git_service.py` showing only `raise
  ValueError(...)` call sites.
- Full git-mcp test suite passes with no regressions (post-update to
  `test_git_security_compliance.py`).

## Out of scope
- `WriteProtectionPipeline`'s internal stage logic (`gitauth`/`gitpipeline`/
  `gitdryrun`'s Plans).
- `call_tool()`'s dispatch-call replacement — `scripts/mcp_servers/git/git_server.py`'s
  own procedure document (`REQ-002`, `REQ-006`).
- `docs/04_mcp_04_05_git.md` update — deferred to implementation time per the Plan's
  Documentation Impact section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import `GIT_READ_TOOLS` and branch `_run_tool()` on read vs. write (Procedure steps 1-2) | Completed | 20260906-092000 | 20260906-095500 | Implemented as specified |
| 2 | Confirm `_wrap_git_op()` return shape matches caller expectations (Procedure step 3) | Completed | 20260906-092000 | 20260906-095500 | No caller-side change needed; `str` return preserved |
| 3 | Convert every "[DENIED] ..." early-return site to `raise ValueError(err)` (Procedure step 4, Added scope) | Completed | 20260906-092000 | 20260906-095500 | All sites converted except `_checkout_op`/`_pull_op`/`_push_op`'s inline dirty/detached checks — excluded (see doc's "Added scope" note: raising there would be miscaught as `GitServiceError`→HTTP 500 by `WriteProtectionPipeline.run()`'s Stage 6 try/except; provably unreachable dead code, left as-is). Also required updating existing rejection-assertion tests broken by this contract change in `tests/mcp_servers/git/test_git_security_compliance.py` (this Plan's row 5), `tests/mcp_servers/git/test_mcp_git.py` and `tests/mcp_servers/git/test_git_service_dispatch.py` (this Plan's row 4 and row 3 respectively) — all updated from `assert "[DENIED]" in result` to `pytest.raises(ValueError, ...)` |
| 4 | Run validation plan (unit tests, full suite, static checks) | Completed | 20260906-095500 | 20260906-101500 | `tests/mcp_servers/git/`: 238/238 passed. ruff format/check, mypy (`scripts/`), lint-imports, bandit: pass (pre-existing unrelated findings unchanged vs. baseline). Full suite (`--deselect` the known unrelated `test_keyboard_interrupt_breaks_loop` bug): 6309 passed/575 failed/14 skipped/3 errors — zero failures under `tests/mcp_servers/git/` |
| 5 | Update `docs/04_mcp_04_05_git.md`, if in scope per Documentation Impact | Completed | 20260906-101500 | 20260906-101500 | N/A: `docs/00_index.md`'s Document References by Task table has no row naming `docs/04_mcp_04_05_git.md` at all; this file matches the generic "MCP server implementation" row instead, whose reference docs (`04_mcp_02_01_endpoints-and-transport.md`, `04_mcp_03_01_dispatch-and-routing.md`) contain no claim about `git_service.py`/`_run_tool()`/`GIT_READ_TOOLS` requiring correction (confirmed via `rg`) |

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
- **Requirement ID**: `REQ-002` (make `_run_tool()` reachable for all 10 tools via unified dispatch), `REQ-003` (read-only tools bypass `WriteProtectionPipeline`), `REQ-004` (write tools continue through it unchanged), `REQ-005` (confirm no dependency on `read_only`-gating, which lives in `git_server.py`)
- **Source issue**: issues/20260902-144910_gitdispatch_unify_git_mcp_tool_dispatch_and_write_protection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191458_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-203805
- **Related target files**: scripts/mcp_servers/git/git_service.py
