# Implementation Procedure: DOC-005 Update GIT-001 and GIT-002 entries in Known Issues doc

## Goal

Update `GIT-001` and `GIT-002` Known Issue entries from `Status: open` to `Status: resolved` in `docs/04_mcp_90_inconsistencies_and_known_issues.md`, revise their `Observed Implementation`/`Resolution Notes` fields to describe current confirmed behavior, citing responsible functions and test names.

## Scope

- Update `GIT-001` entry (DOC-005 REQ-001, REQ-002)
- Update `GIT-002` entry (DOC-005 REQ-003, REQ-004)

## Assumptions

- The plan's claim that `_check_dirty_worktree()`/`_check_detached_head()` are implemented is correct (verified in this cycle)
- The plan's claim that postcondition checks exist in `format_checkout()`/`format_pull()`/`format_push()` is correct (verified in this cycle)
- Test names cited in the plan exist and pass (confirmed at implementation time)

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

- For `GIT-001`: The plan's Background section confirms `_check_dirty_worktree()` (git_service.py:64-71) returns `(False, "[DENIED] worktree has uncommitted changes")` when dirty; `_check_detached_head()` (git_service.py:73-80) returns `(False, "[DENIED] repository is in a detached HEAD state")` when detached and `allow_detached_head` is False. These are called in `git_checkout()` (lines 248-253) and `git_pull()` (lines 280-285) before proceeding with write operations.
- For `GIT-002`: The plan's Background section confirms `format_checkout()` (format_output.py:135-141) verifies resulting branch/detached-HEAD state; `format_pull()` (format_output.py:156-159) checks for unresolved merge conflicts; `format_push()` (format_output.py:169-173) scans for push-rejection markers. All raise `GitServiceError` on mismatch.

### Details

#### GIT-001 update (current content at lines 136-155):

Current `Observed Implementation`: `git_checkout` calls `git reset --hard` unconditionally; `git_pull` calls `git pull` without checking for uncommitted changes first.

New `Observed Implementation`: Both `git_checkout` and `git_pull` call `_check_dirty_worktree(repo)` and `_check_detached_head(repo)` before proceeding with write operations (unless `dry_run` is set), returning the guard's error if either check fails. Current code: `scripts/mcp_servers/git/git_service.py::git_checkout()` (lines 248-253) and `git_pull()` (lines 280-285). `_check_dirty_worktree()` (git_security.py:64-71) returns `(False, "[DENIED] worktree has uncommitted changes")` when dirty; `_check_detached_head()` (git_security.py:73-80) returns `(False, "[DENIED] repository is in a detached HEAD state")` when detached and `allow_detached_head` is False.

New `Resolution Notes`: Guards implemented in `git_checkout()`/`git_pull()` via `_check_dirty_worktree()`/`_check_detached_head()` (Verified by test, `tests/mcp_servers/git/test_git_security_compliance.py::test_git_checkout_dirty_worktree_denied`, `test_git_pull_dirty_worktree_denied`, `test_git_checkout_detached_head_denied`, `test_git_pull_detached_head_denied`).

#### GIT-002 update (current content at lines 158-177):

Current `Observed Implementation`: `git_checkout` returns success after calling `git checkout` without verifying the branch actually changed; `git_pull` returns success after `git pull` without verifying the remote refs updated.

New `Observed Implementation`: `format_checkout()` (format_output.py:135-141) verifies the resulting branch/detached-HEAD state and raises `GitServiceError` on mismatch; `format_pull()` (format_output.py:156-159) checks for unresolved merge conflicts and raises on detection; `format_push()` (format_output.py:169-173) scans for push-rejection markers and raises if found. The issue's Observed Implementation claim ("returns success ... without verifying the branch actually changed" / "returns success ... without verifying the remote refs updated") predates this change.

New `Resolution Notes`: Postcondition verification implemented in `format_checkout()`/`format_pull()`/`format_push()` (Verified by test, `tests/mcp_servers/git/test_format_output.py::test_checkout_postcondition_failure_wrong_branch`, `test_checkout_postcondition_failure_detached_head`, `test_pull_postcondition_failure_unresolved_conflicts`, `test_push_postcondition_failure_rejection_marker_in_output`).

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Not required — documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Not required — documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Not applicable |

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
