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
- Out of scope: any individual `git_*` handler method's own per-tool validation
  (`_validate_ref`, `_validate_protected`, dry-run handling in `git_checkout`/
  `git_pull`/`git_push`) — these already call `_run_tool()` correctly and need no
  change; `get_dispatch_table()` (lines 412-423, already correctly maps all 10 tools,
  confirmed unchanged); `WriteProtectionPipeline` internals
  (`scripts/mcp_servers/git/repository_state.py`, `gitauth`/`gitpipeline`/`gitdryrun`'s
  scope).

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
- The 5 write-tool handler methods' behavior (`git_add`/`git_commit`/`git_checkout`/
  `git_pull`/`git_push`) is byte-for-byte unchanged — same pipeline construction, same
  stages, same return shape.
- `get_dispatch_table()` (lines 412-423) needs no change — it already maps all 10
  tool names to their respective handler methods; only what happens *inside*
  `_run_tool()` changes.

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

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py -v` — this file's
  own procedure document adds the read-only-bypass-vs-write-pipeline unit tests
  (`REQ-003`, `REQ-004`); this document's implementation must make those tests pass.
- `uv run pytest tests/mcp_servers/git/ -v` (full suite) — no new failures, especially
  the existing write-tool pipeline tests in `test_git_security_compliance.py`
  (dirty-worktree/detached-HEAD denial tests for checkout/pull/push must still pass
  unchanged).
- `uv run mypy scripts/mcp_servers/git/`, `uv run ruff check scripts/mcp_servers/git/`.

## Completion criteria
- `GIT_READ_TOOLS` calls to `_run_tool()` do not construct a `WriteProtectionPipeline`
  and are not rejected by dirty-worktree/detached-HEAD checks (AC-3).
- `GIT_WRITE_TOOLS` calls continue through `WriteProtectionPipeline` with identical
  behavior to today (AC-2).
- Full git-mcp test suite passes with no regressions.

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
| 1 | Import `GIT_READ_TOOLS` and branch `_run_tool()` on read vs. write (Procedure steps 1-2) | Pending | — | — | |
| 2 | Confirm `_wrap_git_op()` return shape matches caller expectations (Procedure step 3) | Pending | — | — | |
| 3 | Run validation plan (unit tests, full suite, static checks) | Pending | — | — | |
| 4 | Update `docs/04_mcp_04_05_git.md`, if in scope per Documentation Impact | Pending | — | — | |

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
