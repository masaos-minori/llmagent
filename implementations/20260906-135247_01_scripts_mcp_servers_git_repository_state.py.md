## Goal
Remove the confirmed-dead duplicate service/dispatch/formatter/tool-handler/guard
method surface from `RepositoryState` and `WriteProtectionPipeline`, now that Phase 0
(`gitauth`, `gitpipeline`, `gitdryrun`) has landed and confirmed each named
placeholder's functional replacement is real (REQ-002, REQ-003 — remove the
confirmed-dead surface once re-confirmed against current code).

## Scope
- In scope: delete the two duplicate method blocks below from
  `scripts/mcp_servers/git/repository_state.py`; no other file's content changes as
  part of this document (the accompanying test-file change is tracked in the sibling
  document `implementations/20260906-135247_02_tests_mcp_servers_git_test_repository_state.py.md`).
- Out of scope: `PipelineStage`/`PipelineResult` (lines 437-501), `WriteProtectionPipeline`'s
  real 9-stage `run()` and its helpers (`__init__`, `state`, `record_stage`, `stages`,
  `all_stages_succeeded`, `last_failed_stage`, lines 515-627), `RepositoryState`'s real
  guard-delegation methods (`verify_authorization`, `verify_preconditions`,
  `verify_postcondition`, `audit`, `structured_result`, `check_dirty_worktree`,
  `check_detached_head`, `validate_protected`, `validate_ref`, lines 139-238), and the
  module-level helpers (`_normalize_branch_name`, `_is_protected_branch`, `_is_safe_ref`,
  `_validate_ref`, `_resolve_remote_url`, `_redact_remote_url`, lines 801-880) — all
  confirmed live this cycle (see Method below).

## Assumptions
- Line numbers below reflect the file's state as re-read this cycle (2026-09-06,
  880 lines total) — re-confirm immediately before deletion in case an intervening
  change (e.g. a concurrent session) shifted them again.
- `tests/mcp_servers/git/test_repository_state.py`'s `TestBackwardCompatShims` class
  (the only test coupling to this dead surface) is removed by the sibling document
  above; this document assumes that removal happens in the same implementation cycle,
  not independently, since removing this file's methods first would otherwise break
  test collection.

## Design decisions
- Delete both duplicate blocks in full rather than partially trim them — every method
  in both blocks was confirmed to have zero production callers (see Method), so a
  partial removal would leave an arbitrary, unexplained subset of a duplicate surface.
- Do not attempt to consolidate or "merge" the two blocks into one shared
  implementation — the class-appropriate replacements (`RepositoryState`'s real
  guard-delegation methods and `WriteProtectionPipeline`'s real `run()`) already exist
  and cover the responsibilities the dead surface's names suggested; there is nothing
  to merge, only to delete.

## Alternatives considered
- Deprecate with a warning instead of deleting: rejected — REQ-004 only retains a
  compatibility shim when a verified caller and removal plan exist; this surface has
  zero external (production) callers and this Plan's REQ-002/REQ-003 is exactly its
  scoped removal plan.
- Remove only the three placeholders the originating issue named
  (`verify_authorization`/`_is_protected_branch`/`verify_postcondition`): rejected —
  those three were already superseded by `gitauth`/`gitpipeline`'s real logic before
  this Plan's authoring; the Plan's own Design section grounds the broader ~74-method
  scope in the issue's own Implementation Intent wording, not only the 3 examples.

## Implementation
### Target file
`scripts/mcp_servers/git/repository_state.py`

### Procedure
1. Re-run the zero-caller confirmation immediately before editing (Design decisions'
   Assumption note): `rg -n "RepositoryState\.|WriteProtectionPipeline\."
   scripts/mcp_servers/` and `rg -n "\.open_repo\(|\.wrap_git_op\(|\.run_tool\("
   scripts/ tests/` — expect only `RepositoryState.snapshot(...)` call sites in
   `git_server.py`/`git_service.py`/`format_output.py`, and zero remaining matches for
   the trio once the sibling test document's removal has landed.
2. Delete the `RepositoryState` duplicate block: `open_repo`, `wrap_git_op`, `run_tool`,
   `get_dispatch_table`, `build_service`, `get_dispatch_table_factory`,
   `format_checkout`, `format_pull`, `format_push`, `format_add`, `format_commit`,
   `format_status`, `format_log`, `format_diff`, `format_branch`, `format_show`,
   `git_status`, `git_log`, `git_diff`, `git_branch`, `git_show`, `git_add`,
   `git_commit`, `git_checkout`, `git_pull`, `git_push`, `_check_repo_path`,
   `_check_write`, `_is_safe_ref`, `_check_protected_branch`, `_validate_ref`,
   `_validate_protected`, `_wrap_git_op`, `_open_repo`, `_allow_detached_head`,
   `_protected_branches`, `_read_only`, `_max_log_entries`, `_allowed_repo_paths`
   (currently lines 240-435 inclusive, immediately after `validate_ref` and before
   `class PipelineStage`).
3. Delete the `WriteProtectionPipeline` duplicate block: `get_dispatch_table`,
   `build_service`, `format_checkout`, `format_pull`, `format_push`, `format_add`,
   `format_commit`, `format_status`, `format_log`, `format_diff`, `format_branch`,
   `format_show`, `git_status`, `git_log`, `git_diff`, `git_branch`, `git_show`,
   `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push`,
   `_check_repo_path`, `_check_write`, `_is_safe_ref`, `_check_protected_branch`,
   `_validate_ref`, `_validate_protected`, `_wrap_git_op`, `_open_repo`,
   `_allow_detached_head`, `_protected_branches`, `_read_only`, `_max_log_entries`,
   `_allowed_repo_paths` (currently lines 629-789 inclusive, immediately after
   `last_failed_stage` and before the module's `__all__` block).
4. Confirm no blank-line/whitespace artifacts remain at either deletion site (each
   class should end cleanly at its last remaining real method).

### Method
Zero-caller confirmation performed this cycle (2026-09-06):
- `rg -n "RepositoryState\.|WriteProtectionPipeline\." scripts/mcp_servers/git/*.py`
  outside `repository_state.py` itself returns only `RepositoryState.snapshot(...)` in
  `git_server.py` (lines 243, 247), `format_output.py` (line 152), and `git_service.py`
  (line 234) — no other attribute access on either class from production code.
- Every method name in both duplicate blocks was checked (as a class of names, not
  individually re-verified per name beyond this class-level sweep, per
  `rules/ai-execution.md` Adversarial Verification's "stop once checked once against a
  concrete source") against `scripts/mcp_servers/` and `tests/mcp_servers/git/` for any
  `.methodname(` call where the receiver is a `RepositoryState`/`WriteProtectionPipeline`
  instance (as opposed to `GitService`, which independently defines its own same-named
  real methods in `git_service.py` — a distinct class, out of scope here).
- The only such match was `tests/mcp_servers/git/test_repository_state.py`'s
  `TestBackwardCompatShims` class (`state.open_repo(...)`, `state.wrap_git_op(...)`,
  `state.run_tool(...)`, lines 234/243/252) — tracked by the sibling document (seq 02).
- `run_tool` (part of the dead block) only calls `self.open_repo`/`self.wrap_git_op`
  internally (lines 264-265) — the trio is self-contained with no other internal
  caller either.

### Details
No behavior change to any live code path: `GitService` (in `git_service.py`) — the
sole production caller reachable from `POST /v1/call_tool` — never calls any method in
either deleted block; it defines and uses its own identically-named real methods.
`RepositoryState.snapshot()`, the real guard-delegation methods, and
`WriteProtectionPipeline.run()`'s real 9-stage pipeline are untouched.

## Compatibility considerations
No public API surface is removed from a caller's perspective: nothing outside this
file and its sibling test document references any deleted method (confirmed via
Method above). `GitService`'s independent, real implementations of the same-named
methods (`_check_write`, `_validate_ref`, `_validate_protected`, `_wrap_git_op`,
`_open_repo`, `git_status`, etc. in `git_service.py`) are a separate class and are
unaffected.

## Security considerations
Several deleted methods returned permissive/fixed placeholder values that could be
mistaken for active security behavior if ever called (`_check_write()` → `True, ""`;
`_protected_branches()` → `[]`; `_allow_detached_head()` → `False`). Removing them
eliminates the risk of a future change accidentally wiring one of these dead,
silently-permissive methods into a live path instead of `GitService`'s real
equivalent or `RepositoryState`'s real guard-delegation methods.

## Rollback considerations
Revert via `git checkout` on this file alone if `uv run pytest tests/mcp_servers/git/`
regresses after this change and the sibling test-file removal — low risk, since Method
above confirms zero production callers before deletion; no data migration, no config
change, and no other file's runtime behavior depends on this file's deleted methods.

## Validation plan
- `uv run vulture scripts/mcp_servers/git/ --min-confidence 80` before and after: the
  deleted method names must no longer appear (because they no longer exist), and no
  new dead-code finding should appear elsewhere in the same run.
- `uv run pytest tests/mcp_servers/git/ -v` (full suite, run together with the sibling
  test-file document's removal in the same cycle): no failures — this is the
  regression proof that the removed methods truly had zero callers.
- `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`,
  `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`,
  `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- Both duplicate blocks (RepositoryState lines 240-435; WriteProtectionPipeline lines
  629-789, current-at-time-of-writing line numbers — re-confirm before editing per
  Assumptions) no longer exist in the file.
- `rg` for any of the deleted method names within `scripts/mcp_servers/git/repository_state.py`
  returns no matches.
- `uv run vulture scripts/mcp_servers/git/ --min-confidence 80` reports no finding for
  any deleted name (they no longer exist to be flagged).
- Validation plan's full command set passes with no new failure.

## Out of scope
- The accompanying test-file change (`tests/mcp_servers/git/test_repository_state.py`)
  — tracked in the sibling document, seq 02, since a document may modify only one file
  (see `templates/implementation-procedure.md` Notes on filling sections).
- ADR-012 / Known Issues / `docs/00_security_02...` / `docs/04_mcp_04_05_git.md`
  corrections — tracked in seq 03-06 of this same Plan.
- Any further dead-code discovery beyond the two blocks catalogued here — if one is
  found during implementation, treat it as this Plan's own new evidence per
  `rules/workflow-lifecycle.md` (correct the Plan, do not silently expand this
  document's scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-06 | 2026-09-06 | Duplicate blocks already removed; file reduced from 880 to 527 lines |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-06 | 2026-09-06 | Sibling doc seq 02 removed TestBackwardCompatShims |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-06 | 2026-09-06 | ruff clean; mypy clean; bandit low-only (pre-existing); fixed F401 unused imports |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-06 | 2026-09-06 | No documentation update needed: Compatibility considerations state "No public API surface is removed from a caller's perspective"; Out of scope explicitly tracks ADR-012/Known Issues/docs corrections in seq 03-06 |

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
- **Requirement ID**: REQ-002 (remove empty service/dispatch/formatter/tool-handler methods), REQ-003 (remove duplicate guard helpers)
- **Source issue**: issues/20260902-144914_gitcleanup_remove_placeholders_and_align_docs_with_verified_implementation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192746_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-135247
- **Related target files**: scripts/mcp_servers/git/repository_state.py
