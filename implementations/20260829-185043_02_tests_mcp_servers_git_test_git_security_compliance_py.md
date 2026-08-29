# Implementation Procedure: Add regression tests for empty-branch bypass

## Goal

Add regression tests for `git_push` and `git_pull` with empty `branch` argument, verifying that both return `[DENIED]` responses after the `_validate_protected` fix. REQ-002, REQ-003.

## Scope

**In-Scope:**
- Add two test methods to `tests/mcp_servers/git/test_git_security_compliance.py`:
  - Test `git_push` with empty `branch` → `[DENIED]` response.
  - Test `git_pull` with empty `branch` → `[DENIED]` response.

**Out-of-Scope:**
- Modifying `scripts/mcp_servers/git/git_service.py` (covered by separate procedure document).
- Changes to `git_checkout`, other MCP servers, configuration schema.

## Assumptions

1. The existing test file `tests/mcp_servers/git/test_git_security_compliance.py` already has test infrastructure (fixtures, helpers) for git-mcp handlers.
2. Tests use `pytest` and follow the project's test conventions (verified: existing tests in the file use `pytest` fixtures).
3. The denial message format is `[DENIED] branch must not be empty` (from the companion procedure document).

## Design decisions

- Two separate test methods, one per handler (`git_push`, `git_pull`), to keep each assertion focused and independently runnable.
- Use `assert "[DENIED]" in result` rather than exact string matching — allows the error message text to evolve without breaking the test.

## Alternatives considered

- Single parametrized test covering both handlers — would reduce duplication but makes it harder to identify which handler fails; separate methods are clearer for debugging.
- Testing via mock request objects vs. end-to-end handler invocation — mock approach is sufficient since `_validate_protected` is called directly on the service instance before any git operations execute.

## Implementation

### Target file

`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure

Append two test methods to the existing test class in the file.

### Method

1. Read the existing test file to find the appropriate test class name and fixture setup.
2. Add the following two test methods to the same class:

```python
    def test_git_push_with_empty_branch_returns_denied(self):
        """git_push with empty branch argument must return [DENIED] (REQ-002)."""
        # Arrange
        req = GitPushRequest(
            repo_path=self.repo_path,
            remote="origin",
            branch="",  # Empty branch — the bypass scenario
        )
        # Act
        result = self.service.git_push(req)
        # Assert
        assert "[DENIED]" in result
        assert "branch must not be empty" in result.lower()

    def test_git_pull_with_empty_branch_returns_denied(self):
        """git_pull with empty branch argument must return [DENIED] (REQ-003)."""
        # Arrange
        req = GitPullRequest(
            repo_path=self.repo_path,
            remote="origin",
            branch="",  # Empty branch — the bypass scenario
        )
        # Act
        result = self.service.git_pull(req)
        # Assert
        assert "[DENIED]" in result
        assert "branch must not be empty" in result.lower()
```

3. Run the new tests: `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v`.

### Details

1. Locate the existing test class in `test_git_security_compliance.py` (likely named `TestGitSecurityCompliance` or similar based on naming convention).
2. Verify the class has `self.repo_path` fixture available (check existing test methods for pattern).
3. Import `GitPushRequest` and `GitPullRequest` from `scripts.mcp_servers.git.git_models` if not already imported.
4. If the service instance variable name differs from `self.service`, adjust accordingly (verify from existing test methods).

## Compatibility considerations

- These tests depend on the fix in `git_service.py` being applied first (empty branch must now return denial). Running these tests against the unpatched code will fail.
- No backward compatibility concerns — the tests verify the new security behavior.

## Security considerations

- These tests validate a security guard — they should be added to CI to prevent regression of this bypass.
- The denial message includes `[DENIED]` prefix so downstream consumers can programmatically detect denials.

## Rollback considerations

- Remove the two test methods to revert test coverage changes.
- No database or state migration needed.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/git/test_git_security_compliance.py` | New tests pass with patched `git_service.py` | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py::test_git_push_with_empty_branch_returns_denied -v` | Test passes |
| `tests/mcp_servers/git/test_git_security_compliance.py` | New tests pass with patched `git_service.py` | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py::test_git_pull_with_empty_branch_returns_denied -v` | Test passes |
| `tests/mcp_servers/git/test_git_security_compliance.py` | Regression: all existing tests still pass | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | All tests pass |

## Completion criteria

- [ ] `test_git_push_with_empty_branch_returns_denied` passes when `_validate_protected` returns `(False, "[DENIED] ...")`.
- [ ] `test_git_pull_with_empty_branch_returns_denied` passes when `_validate_protected` returns `(False, "[DENIED] ...")`.
- [ ] Both tests fail when `_validate_protected` returns `(True, "")` (confirms the test actually validates the fix).
- [ ] Existing protected-branch tests continue to pass.

## Out of scope

- Modifying `scripts/mcp_servers/git/git_service.py` (covered by `implementations/{timestamp}_01_scripts_mcp_servers_git_git_service_py.md`).
- Changes to `git_checkout` (not affected).
- Changes to other MCP servers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This step |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: internal security guard fix |

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
- **Requirement ID**: REQ-002, REQ-003 — `git_push`/`git_pull` with empty `branch` argument must return a denial message containing `[DENIED]` and indicating branch is required
- **Source issue**: issues/20260828-155804_nc019_git_mcp_command_specific_guards.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-090751_nc019_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-185043
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py
