## Goal
Make `RepositoryState.verify_preconditions()` (`REQ-001`) actually accept and evaluate
`dry_run` and `allow_detached_head`, so the method's own docstring and error message
(which already claim this behavior) become true, and `WriteProtectionPipeline.run()`'s
Stage 5 call site is updated to pass both values through.

## Scope
- In scope: `verify_preconditions()`'s signature and body (`REQ-001` through
  `REQ-004`), `run()`'s Stage 5 call site (`REQ-005`), the docstring/error-text
  correction (`REQ-007`), and confirming no dry-run code path mutates anything
  (`REQ-009`, verification only — no new logic).
- Out of scope: Stage 3 (`verify_authorization()` — `gitauth`'s Plan), Stage 7 /
  `record_stage()` (`gitpipeline`'s Plan), `git_server.py`'s call site (separate
  target file, `implementations/20260905-202634_02_...git_server.py.md`),
  `config/git_mcp_server.toml` (separate target file), test files (separate target
  files).

## Assumptions
- `allow_detached_head`'s scope applies uniformly to `git_checkout`/`git_pull`/
  `git_push` (`REQ-004`), per the Plan's Design decision — not narrowed to checkout
  only.
- `git_server.py`'s call site (this document's sibling target-file document) supplies
  the actual, non-default `dry_run`/`allow_detached_head` argument values at the call
  site this document updates; this document defines the parameters and their
  (defaulted) signature, it does not itself thread the live-path values.

## Design decisions
- Add `dry_run: bool = False` and `allow_detached_head: bool = False` as *defaulted*
  parameters to `verify_preconditions()` and to `run()`'s new parameters (default =
  current, always-reject behavior) — required per a finding made while writing the
  sibling `git_server.py` document: `run()` has a second caller,
  `scripts/mcp_servers/git/git_service.py:234`
  (`pipeline.run(tool_name, lambda: op(state.repo, state))`, the dead-code path the
  Plan's Reference Files section explicitly marks "not modified"). Non-defaulted
  parameters would raise `TypeError` at that call site the moment `run()`'s signature
  changed, which would force an out-of-scope edit to `git_service.py` (a Reference
  File) or an additional-target-file discovery — neither of which this row's scope
  permits. Defaulting both to `False` preserves `git_service.py`'s exact current
  (buggy-but-unchanged, dead-code) behavior with zero edits there, while
  `git_server.py`'s live-path call site (sibling document) still passes explicit,
  non-default values.
- Skip both the dirty-worktree and detached-HEAD checks together when `dry_run=True`
  (not just detached-HEAD) — matches the existing docstring's claim ("guards apply
  only to write commands when dry_run is False") and `REQ-002`'s wording exactly.
- When `dry_run=False`, only the detached-HEAD check is conditional on
  `allow_detached_head`; the dirty-worktree check remains unconditional (no
  `allow_dirty_worktree` setting exists or is requested by the Plan) — `REQ-003` only
  scopes detached-HEAD to the new parameter.
- Delegate to the file's own existing `check_dirty_worktree()` (line 209) and
  `check_detached_head(allow_detached_head)` (line 215) methods rather than
  re-inlining the `is_dirty`/`is_detached_head` checks a second time inside
  `verify_preconditions()` — both methods already implement exactly this row's
  required logic (`check_detached_head` already takes an `allow_detached_head`
  parameter and applies the same `is_detached_head and not allow_detached_head`
  condition `REQ-003`/`REQ-004` need) and are already covered by
  `TestGuardDelegation` tests. Found during this document's investigation; avoids
  duplicating logic that already exists one method away.

## Alternatives considered
- Required (non-defaulted) parameters, forcing every call site to state both
  explicitly: initially preferred for its stronger guarantee against a future call
  site silently omitting `allow_detached_head`, but rejected once investigation
  (sibling `git_server.py` document) found `run()`'s second caller,
  `git_service.py:234`, is out of this row's scope (Reference File) — see Design
  decisions above. Defaulted parameters are the only option that does not require
  touching that file.
- Updating `git_service.py` itself to pass the new parameters explicitly, keeping
  `run()`'s parameters required: rejected — `git_service.py` is a Reference File in
  this Plan ("not modified, dead-code path"), and this Plan's Design section scopes
  its change narrowly to Stage 5's live path; expanding scope to a second file would
  require Plan amendment, not a unilateral decision at the implementation-procedure
  stage.

## Implementation
### Target file
`scripts/mcp_servers/git/repository_state.py`

### Procedure
1. Change `verify_preconditions(self, command: str)` (line 144) to
   `verify_preconditions(self, command: str, dry_run: bool = False, allow_detached_head: bool = False)`
   — defaulted per Design decisions above, so `git_service.py:234`'s existing call
   (unmodified, Reference File) keeps working unchanged.
2. Update the docstring (lines 145-149) to state the actual, now-implemented
   behavior: guards are skipped entirely when `dry_run` is `True`; when `dry_run` is
   `False`, the detached-HEAD guard is skipped only when `allow_detached_head` is
   `True`.
3. In the body (lines 150-160): if `dry_run` is `True`, return `(True, "")`
   immediately (skip both the `is_dirty` and `is_detached_head` checks). Otherwise,
   keep the `is_dirty` check unconditional; gate the `is_detached_head` check on `not
   allow_detached_head`.
4. Correct the detached-HEAD error message (line 158) only if its wording changes as
   a result of the above (the existing text already correctly directs the operator to
   `allow_detached_head=true in git_mcp_server.toml` — confirm it still reads
   correctly with the new parameter in place; no textual change is required unless
   review finds the wording stale).
5. Update `WriteProtectionPipeline.run()`'s Stage 5 call site (line 563,
   `ok, msg = self._state.verify_preconditions(tool_name)`) to
   `ok, msg = self._state.verify_preconditions(tool_name, dry_run, allow_detached_head)`.
   This requires `run()`'s own signature (starting line 547) to accept
   `dry_run: bool = False` and `allow_detached_head: bool = False` as new, defaulted
   parameters (see Design decisions — `git_service.py:234`'s existing call passes
   neither, and must keep working via the defaults) — `git_server.py`'s call site
   (this Plan's sibling target-file document) is the one that supplies concrete,
   non-default values from the live path.

### Method
Direct code edit (no codemod/AST tooling needed — a single method signature, a single
docstring, and one call site). Read the current file around lines 140-165 (method) and
540-570 (`run()`) immediately before editing to confirm no further drift since this
document's revalidation (line numbers in this document are current as of
2026-09-05; re-check if this document is executed in a later session).

### Details
- `verify_preconditions()`'s new signature:
  `def verify_preconditions(self, command: str, dry_run: bool = False, allow_detached_head: bool = False) -> tuple[bool, str]:`
- Body logic, delegating to the existing `check_dirty_worktree()`/`check_detached_head()`
  helpers (see Design decisions):
  ```python
  if dry_run:
      return True, ""
  ok, msg = self.check_dirty_worktree()
  if not ok:
      return ok, msg
  return self.check_detached_head(allow_detached_head)
  ```
- `run()`'s new signature adds `dry_run: bool = False` and
  `allow_detached_head: bool = False` parameters (placement: after `op`, before
  `requested_branch`, to keep the two boolean flags adjacent and match the order
  `verify_preconditions()` now takes them). Defaults preserve `git_service.py:234`'s
  existing call unchanged.

## Compatibility considerations
- `run()` has two existing callers: `git_server.py:266` (target file, sibling
  document — passes explicit new values) and `git_service.py:234` (Reference File,
  dead-code path, "not modified" per the Plan) — defaulted parameters (see Design
  decisions) keep the latter working with zero changes.
  `tests/mcp_servers/git/test_repository_state.py` (sibling target-file document)
  calls `verify_preconditions()` directly at lines 180 and 279 with the old
  one-argument form — defaults mean those calls continue to work unchanged too, though
  that document should still add explicit-argument test cases for the new
  dry_run/allow_detached_head matrix per its own scope.
- No public API surface outside this module changes; `verify_preconditions`/`run` are
  internal to the git-mcp server.

## Security considerations
- The dirty-worktree check remains unconditional outside `dry_run` — this change does
  not introduce a new way to bypass it.
- Stage 3 (`verify_authorization()`) is untouched — authorization still runs before
  Stage 5 regardless of `dry_run`, per `REQ-005`; this document's edit does not touch
  `verify_authorization()` or its call site (line 557).
- `allow_detached_head` defaults to `False` at the `GitConfig` level (unchanged by
  this document) — the new parameter does not change the fail-closed default.

## Rollback considerations
- Single-file, single-method change with no schema/data migration — revertible via
  `git checkout` of this one file if the sibling `git_server.py`/test changes are
  reverted in the same rollback (defaulted parameters mean this file's own revert is
  not itself breaking for `git_service.py`'s untouched call site, but leaving
  `git_server.py`'s sibling change in place while reverting this file would strip the
  new parameters `git_server.py` passes — revert together to avoid that mismatch).

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` — new
  `dry_run`/`allow_detached_head` matrix tests (tracked in that document) must pass
  against this change.
- `uv run pytest tests/mcp_servers/git/ -v` — full git-mcp suite, no new failures
  (defaulted parameters mean existing calls to `run()`/`verify_preconditions()`
  elsewhere in the suite, and `git_service.py:234`'s dead-code call, keep working
  unchanged with no `TypeError`).
- `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`,
  `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`,
  `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- `verify_preconditions()` accepts `dry_run` and `allow_detached_head`; returns
  `(True, "")` unconditionally when `dry_run=True`; rejects detached HEAD only when
  `allow_detached_head=False` and `dry_run=False`; dirty-worktree rejection is
  unconditional outside `dry_run=True`.
- `run()`'s Stage 5 call site passes both values through from its own new parameters.
- Docstring/error text describe only this now-implemented behavior.
- All existing and new tests in `tests/mcp_servers/git/` pass; no new lint/type/security
  findings.

## Out of scope
- `git_server.py`'s call site providing concrete `dry_run`/`allow_detached_head`
  values into `run()` — separate target-file document.
- `config/git_mcp_server.toml` documentation — separate target-file document.
- Stage 3 / Stage 7 changes — `gitauth`/`gitpipeline` Plans, not this one.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `dry_run`/`allow_detached_head` params to `verify_preconditions()`; implement skip/permit logic; correct docstring/error text; update `run()`'s signature and Stage 5 call site | Pending | — | — | |
| 2 | Add or update tests per Validation plan (tracked in the `test_repository_state.py` sibling document) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A here — doc update deferred per Plan's Documentation Impact |

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
- **Requirement ID**: REQ-001 (add parameters), REQ-002 (skip on dry_run), REQ-003
  (reject detached HEAD unless allowed), REQ-004 (uniform scope — this file's change
  is scope-agnostic, applied by callers), REQ-005 (Stage 3 unaffected), REQ-007
  (docstring/error-text correction), REQ-009 (verify non-mutation, no new logic)
- **Source issue**: issues/20260902-144909_gitdryrun_align_detached_head_and_dry_run_with_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191122_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-202634
- **Related target files**: scripts/mcp_servers/git/repository_state.py
