# Implementation Procedure: Remove git_push stdout postcondition check

## Goal

Remove the git_push stdout-rejection branch in `verify_postcondition()` (`scripts/mcp_servers/git/repository_state.py`; REQ-008). Rely on git exit-code failures (which surface as `GitServiceError` execution failures) instead of the ineffective stdout marker check.

## Scope

- Modify `scripts/mcp_servers/git/repository_state.py`:
  - Lines 216-219: remove the `elif tool_name == "git_push"` branch that checks `"rejected"/"error" in result.lower()`.

## Assumptions

- GitPython raises `git.exc.GitError` on non-zero push exit code — confirmed by GitPython documentation and the existing `_wrap_git_op` error wrapping.
- The pipeline's Stage 6 execution already wraps `git.exc.GitError` as `GitServiceError` (via `_wrap_git_op` in `git_service.py`).
- The removed check was ineffective because git reports push results on stderr, not stdout.

## Design decisions

- **Remove the branch entirely**: The stdout check is ineffective (git reports push results on stderr) and redundant (GitPython raises on non-zero exit). Removing it simplifies the code and eliminates a false sense of protection.

## Alternatives considered

- Moving the check to stderr parsing: rejected because GitPython already handles this via `git.exc.GitError` on non-zero exit.
- Keeping the check as a belt-and-suspenders approach: rejected because it creates a false sense of protection and the plan explicitly calls it out as ineffective.

## Implementation
### Target file
`scripts/mcp_servers/git/repository_state.py`

### Procedure
1. Remove the git_push stdout-rejection branch in `verify_postcondition()` (REQ-008).

### Method
Edit `scripts/mcp_servers/git/repository_state.py`:
- Lines 216-219: Remove the `elif tool_name == "git_push"` branch that checks `"rejected"/"error" in result.lower()`.

### Details
- GitPython raises `git.exc.GitError` on non-zero push exit code — confirmed by GitPython documentation and the existing `_wrap_git_op` error wrapping.
- The pipeline's Stage 6 execution already wraps `git.exc.GitError` as `GitServiceError` (via `_wrap_git_op` in `git_service.py`).
- The removed check was ineffective because git reports push results on stderr, not stdout.

## Compatibility considerations

- The removed branch only affects `git_push` postcondition verification.
- Push failures will now be handled by GitPython's exit-code mechanism — same outcome, different path.

## Security considerations

- No security impact: this removes a dead code path, not a security check.

## Rollback considerations

- Revert the branch removal — acceptable because it's a small, bounded change.

## Validation plan

- **Static check**: `rg 'rejected.*result\.lower' scripts/mcp_servers/git/repository_state.py` should return 0 after the change.
- **Type check**: `uv run mypy scripts/mcp_servers/git/repository_state.py` — confirm clean.
- **Existing tests**: `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py` — confirm no regressions.

## Completion criteria

- The `git_push` stdout-rejection branch is removed from `verify_postcondition()`.
- Push failures are driven by git exit code (GitPython raises `git.exc.GitError`).
- One audit record is produced for push failures (via the exactly-one-record invariant in `git_server.py`).

## Out of scope

- Modifying `format_output.py` (removes `_rejection_markers` — covered in its own document).
- Modifying `git_service.py` (removes `[DENIED]` returns — covered in its own document).
- Modifying `dispatch.py` (kept generic per plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove git_push stdout-rejection branch in `verify_postcondition()` (`scripts/mcp_servers/git/repository_state.py`) | Pending | — | — | REQ-008 |
| 2 | Run validation sequence (ruff, mypy, pytest) | Pending | — | — | REQ-008 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261007-153904_gitaudit01_fix-git-mcp-audit-records-and-policy-rejection-error-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261007-191952_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-110318
- **Related target files**: scripts/mcp_servers/git/repository_state.py
