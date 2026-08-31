# Implementation Procedure: DOC-005 Update GIT-001 and GIT-002 entries in Known Issues doc

## Goal

Update `GIT-001` and `GIT-002` Known Issue entries from `Status: open` to `Status: resolved` in `docs/04_mcp_90_inconsistencies_and_known_issues.md`, revise their `Observed Implementation`/`Resolution Notes` fields to describe current confirmed behavior, citing responsible functions and test names.

## Scope

- Update `GIT-001` entry (DOC-005 REQ-001, REQ-002)
- Update `GIT-002` entry (DOC-005 REQ-003, REQ-004)

## Assumptions

- **Corrected during Step 3 adversarial verification (this cycle)**: the plan's
  claim that `git_checkout()`/`git_pull()` call standalone
  `_check_dirty_worktree()`/`_check_detached_head()` functions is stale. Direct
  source inspection (`rg -n "_check_dirty_worktree|_check_detached_head"
  scripts/mcp_servers/git/*.py`) finds no such call from `git_service.py`;
  `git_checkout()`/`git_pull()` (`scripts/mcp_servers/git/git_service.py`) now
  check `state.is_dirty` / `state.is_detached_head` directly inline, where
  `state` is a `RepositoryState` (`scripts/mcp_servers/git/repository_state.py`)
  snapshot passed in by `_run_tool()`. The guard's *outcome* the Plan describes
  (reject dirty worktree / detached HEAD before write operations) is still
  correct and confirmed by test — only the specific function names/call path
  changed since the Plan was written (repository was refactored to introduce
  `RepositoryState` after this Plan/procedure's Background was drafted). The
  doc update below is written against the corrected, current mechanism.
- The plan's claim that postcondition checks exist in
  `format_checkout()`/`format_pull()`/`format_push()` is correct (re-confirmed
  in this cycle by direct read of `scripts/mcp_servers/git/format_output.py` —
  these three functions still exist with the same postcondition-check
  behavior, now taking a `state: RepositoryState` parameter instead of a raw
  `repo`).
- Test names cited in the plan exist and pass (re-confirmed in this cycle: `uv
  run pytest tests/mcp_servers/git/test_git_security_compliance.py -k
  "dirty_worktree_denied or detached_head_denied"` → 4 passed; `uv run pytest
  tests/mcp_servers/git/test_format_output.py -k "postcondition_failure"` → 4
  passed).
- **Out-of-scope observation (not acted on)**: `repository_state.py` contains
  unused, dead-code duplicates of the dirty-worktree/detached-head checks
  (underscore-prefixed `_check_dirty_worktree()`/`_check_detached_head()`,
  confirmed via `rg` to have zero callers in `scripts/` or `tests/`) alongside
  a "backward-compat" `check_dirty_worktree()`/`check_detached_head()` pair
  that also isn't the active call path (`git_service.py` uses the
  `is_dirty`/`is_detached_head` properties directly). This is a code-cleanup
  matter outside this documentation-only procedure's scope — noted here for
  visibility, not fixed.

## Design decisions

- Change `Status: open` to `Status: resolved` for both entries — the plan's adversarial verification confirms the guards are implemented.
- Rewrite `Observed Implementation` to describe current behavior (not pre-fix state) — cite actual function names.
- Add `Resolution Notes` citing the specific functions and test names that verify the fix.

## Alternatives considered

- Leave status as `open` and add a note that it was re-evaluated — rejected because the plan's evidence shows the gap is actually closed.
- Merge both entries into one — rejected because they track separate concerns (pre-condition vs post-condition).

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure

#### Phase 1: Preparation

1. Re-confirm current implementation by reading `scripts/mcp_servers/git/git_service.py::git_checkout()`/`git_pull()` and `format_output.py::format_checkout()`/`format_pull()`/`format_push()` in full (REQ-002, REQ-004)
2. Check `tests/mcp_servers/git/` for tests covering these checks so `Resolution Notes` can cite real test names (REQ-008)

#### Phase 2: Core Logic Implementation

3. Update `GIT-001` entry: change `Status: open` to `Status: resolved`, rewrite `Observed Implementation` to describe current implementation (`_check_dirty_worktree()`/`_check_detached_head()`), add `Resolution Notes` citing test names (REQ-001, REQ-002)
4. Update `GIT-002` entry: change `Status: open` to `Status: resolved`, rewrite `Observed Implementation` to describe current implementation (`format_checkout()`/`format_pull()`/`format_push()`), add `Resolution Notes` citing test names (REQ-003, REQ-004)

#### Phase 3: Deployment & Verification

5. Manual verification — re-read all three affected files to confirm edits are accurate and consistent (AC-001 through AC-005)

### Method

- For `GIT-001` (**corrected during Step 3 adversarial verification**): current
  source (`scripts/mcp_servers/git/git_service.py`) shows `git_checkout()`'s
  `_checkout_op` closure and `git_pull()`'s `_pull_op` closure each check
  `state.is_dirty` (returns `"[DENIED] worktree has uncommitted changes (dirty
  worktree)"`) and `state.is_detached_head and not self._allow_detached_head`
  (returns `"[DENIED] repository is in a detached HEAD state"`) before
  proceeding, where `state` is a `RepositoryState`
  (`scripts/mcp_servers/git/repository_state.py`) snapshot. This differs from
  the plan's Background (which describes standalone `_check_dirty_worktree()`/
  `_check_detached_head()` calls) — the outcome is identical, the mechanism
  changed.
- For `GIT-002`: re-confirmed current source: `format_checkout()`
  (`scripts/mcp_servers/git/format_output.py`) verifies resulting
  branch/detached-HEAD state; `format_pull()` checks for unresolved merge
  conflicts; `format_push()` scans for push-rejection markers. All raise
  `GitServiceError` on mismatch, matching the plan's Background.

### Details

#### GIT-001 update:

Current `Observed Implementation`: `git_checkout` calls `git reset --hard` unconditionally; `git_pull` calls `git pull` without checking for uncommitted changes first.

New `Observed Implementation` (**corrected to match current source, not the
plan's original function-name claim**): Both `git_checkout` and `git_pull`
(`scripts/mcp_servers/git/git_service.py`) check the current `RepositoryState`
snapshot before proceeding with write operations (unless `dry_run` is set):
they reject with `"[DENIED] worktree has uncommitted changes (dirty
worktree)"` when `state.is_dirty` is true, and with `"[DENIED] repository is
in a detached HEAD state"` when `state.is_detached_head` is true and detached
HEAD is not explicitly allowed. `RepositoryState.is_dirty`/`is_detached_head`
(`scripts/mcp_servers/git/repository_state.py`) are captured from a single
`git.Repo` snapshot per operation.

New `Resolution Notes`: Guards implemented in `git_checkout()`/`git_pull()` via `RepositoryState.is_dirty`/`is_detached_head` (Verified by test, `tests/mcp_servers/git/test_git_security_compliance.py::test_git_checkout_dirty_worktree_denied`, `test_git_pull_dirty_worktree_denied`, `test_git_checkout_detached_head_denied`, `test_git_pull_detached_head_denied` — re-run in this cycle, all 4 pass).

#### GIT-002 update:

Current `Observed Implementation`: `git_checkout` returns success after calling `git checkout` without verifying the branch actually changed; `git_pull` returns success after `git pull` without verifying the remote refs updated.

New `Observed Implementation`: `format_checkout()` (`scripts/mcp_servers/git/format_output.py`) verifies the resulting branch/detached-HEAD state and raises `GitServiceError` on mismatch; `format_pull()` checks for unresolved merge conflicts and raises on detection; `format_push()` scans for push-rejection markers and raises if found. The issue's Observed Implementation claim ("returns success ... without verifying the branch actually changed" / "returns success ... without verifying the remote refs updated") predates this change.

New `Resolution Notes`: Postcondition verification implemented in `format_checkout()`/`format_pull()`/`format_push()` (Verified by test, `tests/mcp_servers/git/test_format_output.py::test_checkout_postcondition_failure_wrong_branch`, `test_checkout_postcondition_failure_detached_head`, `test_pull_postcondition_failure_unresolved_conflicts`, `test_push_postcondition_failure_rejection_marker_in_output` — re-run in this cycle, all 4 pass).

## Compatibility considerations

- No source-code compatibility impact — documentation-only change.
- Other documents referencing `GIT-001`/`GIT-002` as open may become inconsistent (e.g., ADR-012, security policy doc) — those are addressed separately in DOC-005 target rows 2 and 3.

## Security considerations

- Low risk: documentation correction only. Incorrectly marking these as resolved could mislead future reviewers, but the adversarial verification in this cycle confirms the guards are actually implemented.

## Rollback considerations

- Simple revert: restore previous `Status: open` text and original `Observed Implementation`/`Resolution Notes` fields. No operational impact since no code changes are involved.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_90_inconsistencies_and_known_issues.md` | Manual review: verify GIT-001/GIT-002 Status=resolved, Resolution Notes cite actual functions | Manual read | Entries match current code behavior |

## Completion criteria

- GIT-001 Status = `resolved`, Observed Implementation describes current `_check_dirty_worktree()`/`_check_detached_head()` behavior, Resolution Notes cites test names (REQ-001, REQ-002)
- GIT-002 Status = `resolved`, Observed Implementation describes current `format_checkout()`/`format_pull()`/`format_push()` behavior, Resolution Notes cites test names (REQ-003, REQ-004)

## Out of scope

- Updating ADR-012's Known Deviations section (separate target file row)
- Updating security policy doc's Git MCP bullet (separate target file row)
- Changing ADR-012's Status field (owner decision tied to NC-019)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260831-110338 | 20260831-110338 | Corrected during Step 3 adversarial verification: `git_checkout()`/`git_pull()` no longer call standalone `_check_dirty_worktree()`/`_check_detached_head()` (stale, refactored to `RepositoryState.is_dirty`/`is_detached_head` inline checks) — doc text updated to match current source, not the plan's original claim. Re-ran cited tests (8 total, all pass). Updated GIT-001/GIT-002 to `Status: resolved` with corrected `Observed Implementation`/`Resolution Notes`. |
| 2 | Add or update tests per Validation plan | Completed | 20260831-110338 | 20260831-110338 | Not required — documentation-only change; existing tests re-run to confirm citations accurate |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260831-110338 | 20260831-110338 | Not required — documentation-only change; ran `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_consistency.py --domain mcp` instead — see Notes on Step 4 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260831-110338 | 20260831-110338 | This document's Target file *is* the documentation edit. `check_docs_structure.py` initially flagged the edit pushing the file past the 16384-byte size limit (16594 bytes; confirmed via pre-edit `git show HEAD:...`/`git stash` comparison that this was newly introduced, not pre-existing) — trimmed `Observed Implementation` wording for both entries to 16291 bytes, resolving it. Remaining `missing '## Keywords' section` finding is confirmed pre-existing (present before this edit too) and left as-is, out of scope. |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260828-161729_doc005_git001_git002_stale_open_status.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-121751_doc005_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-201308
- **Related target files**: docs/04_mcp_90_inconsistencies_and_known_issues.md
