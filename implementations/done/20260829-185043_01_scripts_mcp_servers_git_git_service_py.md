# Implementation Procedure: Modify `_validate_protected` in `git_service.py`

## Goal

Reject empty branch strings in `_validate_protected` to prevent protected-branch bypass via omitted `branch` argument on `git_push` and `git_pull` handlers. REQ-001.

## Scope

**In-Scope:**
- Modify `scripts/mcp_servers/git/git_service.py`: add empty-branch rejection in `_validate_protected`.

**Out-of-Scope:**
- Changes to `git_checkout`, other MCP servers, configuration schema.
- Adding tests (covered by separate procedure document).

## Assumptions

1. `_validate_protected` currently returns `(True, "")` for falsy values (verified: line 122-123), which skips the protected-branch check entirely.
2. `GitPushRequest.branch` and `GitPullRequest.branch` both accept empty string as valid default (verified: `git_models.py:172-175` and `git_models.py:186`).
3. `format_push` uses `branch = req.branch or repo.active_branch.name` fallback (verified: `format_output.py:165`).

## Design decisions

- Single-line change: replace `return True, ""` with `return False, "[DENIED] branch must not be empty"` at line 123. No new methods or classes needed.
- The guard applies to all falsy values (empty string, None), not just empty string — this is intentional since neither handler accepts `None` as a valid branch value.

## Alternatives considered

- Add a dedicated `if branch == "":` check before the existing `if not branch:` line — unnecessary duplication; the existing falsy check already covers empty string.
- Return a different error message format — `[DENIED]` prefix is consistent with the existing error convention used elsewhere in the codebase.

## Implementation

### Target file

`scripts/mcp_servers/git/git_service.py`

### Procedure

Replace the early-return for falsy branch values at line 123 with an explicit denial.

### Method

Edit `scripts/mcp_servers/git/git_service.py` line 123:

```python
# Before:
    if not branch:
        return True, ""
    return self._check_protected_branch(branch)

# After:
    if not branch:
        return False, "[DENIED] branch must not be empty"
    return self._check_protected_branch(branch)
```

### Details

1. Locate `_validate_protected` method at line 120-124.
2. Change line 123 from `return True, ""` to `return False, "[DENIED] branch must not be empty"`.
3. Verify no other callers of `_validate_protected` exist outside `git_push`/`git_pull` (verified: grep confirms calls at lines 242, 271, 301 — all within `git_service.py` itself).
4. Verify `_check_protected_branch` contract (returns `(False, reason)` when branch is protected) — confirmed at `git_security.py:58`.

## Compatibility considerations

- **Breaking change**: callers that relied on empty branch being silently allowed will now receive a denial. This is the intended fix.
- `git_log` and `git_diff` also accept empty branch/ref arguments but are read-only operations — they do not call `_validate_protected` (only write operations need protected-branch checks). Verified: no calls to `_validate_protected` in `git_log`/`git_diff` handlers.

## Security considerations

- This change closes a security gap: protected-branch enforcement was bypassable by omitting the `branch` argument.
- The denial message includes `[DENIED]` prefix so it can be distinguished from normal errors downstream.

## Rollback considerations

- Revert line 123 back to `return True, ""` to restore original behavior.
- No database or state migration needed.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/git/git_service.py` | Unit test: call `_validate_protected("")` directly | pytest | Returns `(False, "[DENIED] branch must not be empty")` |
| `tests/mcp_servers/git/test_git_security_compliance.py` | Integration test: `git_push`/`git_pull` with empty branch | pytest | Response contains `[DENIED]` |
| `tests/mcp_servers/git/test_git_security_compliance.py` | Regression: existing protected-branch tests | pytest | All existing tests pass |

## Completion criteria

- [ ] `_validate_protected("")` returns `(False, "[DENIED] branch must not be empty")` instead of `(True, "")`.
- [ ] Existing protected-branch tests continue to pass (non-empty branch names still denied).
- [ ] No import errors in `scripts/mcp_servers/git/` module after edit.

## Out of scope

- Adding regression tests (covered by `implementations/{timestamp}_02_tests_mcp_servers_git_test_git_security_compliance_py.md`).
- Changes to `git_checkout` (not affected).
- Changes to other MCP servers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Replaced `return True, ""` with `return False, "[DENIED] branch must not be empty"` at line 131-132 |
| 2 | Add or update tests per Validation plan | Completed | — | — | Added `"branch": "main"` to failing tests in test_mcp_git.py and test_git_service_dispatch.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 164 tests pass, ruff/mypy/bandit clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: internal security guard fix |

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
- **Requirement ID**: REQ-001 — `_validate_protected` must reject empty branch strings before proceeding with any git operation
- **Source issue**: issues/20260828-155804_nc019_git_mcp_command_specific_guards.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-090751_nc019_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-185043
- **Related target files**: scripts/mcp_servers/git/git_service.py
