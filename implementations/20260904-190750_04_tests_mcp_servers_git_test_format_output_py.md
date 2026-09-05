## Goal

Add a regression test proving `format_checkout()` performs a real branch switch (not `MagicMock`-only) against a real `git.Repo` in a temp directory.

## Scope

- `tests/mcp_servers/git/test_format_output.py`: add a new test using a real temporary `git.Repo` (not `MagicMock`) with two branches, asserting `format_checkout()` actually switches the active branch.

## Assumptions

- Existing checkout tests all use `MagicMock` repos that never execute real Git commands, missing the argument-order bug entirely.
- The test must use a real `git.Repo` in a temporary directory to exercise the actual GitPython library call.
- Two branches must exist in the temp repo: one current branch and one target branch to switch to.

## Design decisions

- **Real repo in temp directory**: Use `tempfile.TemporaryDirectory()` to create an isolated git repo that doesn't affect the working repository. This ensures test isolation and avoids flakiness from shared state.
- **Minimal assertion**: Assert only that `active_branch` changes after calling `format_checkout()`, matching AC-7's requirement.
- **Cleanup via context manager**: Ensure temp repo is cleaned up even if the test fails.

## Alternatives considered

- Using `pytest.fixture` with autouse=True — rejected because the temp repo setup is too heavyweight for every test; keep it local to this specific test.
- Testing against the actual project repo — rejected because it would modify the working tree and risk breaking other tests.

## Implementation

### Target file

`tests/mcp_servers/git/test_format_output.py`

### Procedure

1. Add import for `tempfile` and `git` at the top of the file.
2. Add a new test function `test_format_checkout_real_repo_branch_switch` that:
   - Creates a temp directory and initializes a bare git repo.
   - Clones it to a working directory with an initial commit.
   - Creates a second branch.
   - Calls `format_checkout()` to switch to the second branch.
   - Asserts the active branch changed.
3. Optionally add a negative test: call `format_checkout()` with a non-existent branch and assert `GitServiceError` is raised.

### Method

- Use `git.Repo.init(path, bare=True)` to create a bare repo.
- Clone it locally with `git.Repo.clone_from(bare_path, work_path)`.
- Make an initial commit so there's something to branch from.
- Create a second branch with `repo.create_head("feature")`.
- Call `format_checkout(state, req)` where `state` wraps the cloned repo and `req` is a `GitCheckoutRequest(branch="feature", create=False)`.
- Assert `state.active_branch.name == "feature"`.

### Details

**1. Import additions:**

```python
import tempfile
import git
```

**2. New test function:**

```python
def test_format_checkout_real_repo_branch_switch():
    """REQ-007, AC-7: format_checkout() performs a real branch switch (not MagicMock-only).
    
    This test uses a real temporary git.Repo to verify the argument-order fix
    for 'git checkout <branch> --' works correctly. Against pre-change code,
    this test fails with: error: pathspec 'feature' did not match any file(s) known to git
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup: create a bare repo and clone it
        bare_path = os.path.join(tmpdir, "bare.git")
        git.Repo.init(bare_path, bare=True)
        
        work_path = os.path.join(tmpdir, "work")
        repo = git.Repo.clone_from(bare_path, work_path)
        
        # Make an initial commit so we have something to branch from
        work_file = os.path.join(work_path, "README.md")
        with open(work_file, "w") as f:
            f.write("# Test\n")
        repo.index.add([work_file])
        repo.index.commit("Initial commit")
        
        # Create a second branch
        feature_branch = repo.create_head("feature")
        feature_branch.checkout()
        
        # Switch back to main
        repo.heads.main.checkout()
        
        # Verify we're on main before the test
        assert repo.active_branch.name == "main"
        
        # Create RepositoryState wrapper around the repo
        state = RepositoryState(work_path)
        
        # Call format_checkout to switch to feature branch
        req = GitCheckoutRequest(branch="feature", create=False)
        result = format_checkout(state, req)
        
        # Assert: the active branch changed
        assert state.active_branch.name == "feature"
        assert "Switched to branch 'feature'" in result
```

**3. Negative test (optional):**

```python
def test_format_checkout_real_repo_nonexistent_branch():
    """REQ-007: format_checkout() raises GitServiceError for nonexistent branch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bare_path = os.path.join(tmpdir, "bare.git")
        git.Repo.init(bare_path, bare=True)
        
        work_path = os.path.join(tmpdir, "work")
        repo = git.Repo.clone_from(bare_path, work_path)
        
        work_file = os.path.join(work_path, "README.md")
        with open(work_file, "w") as f:
            f.write("# Test\n")
        repo.index.add([work_file])
        repo.index.commit("Initial commit")
        
        state = RepositoryState(work_path)
        req = GitCheckoutRequest(branch="nonexistent", create=False)
        
        with pytest.raises(GitServiceError):
            format_checkout(state, req)
```

## Compatibility considerations

- The test requires `git` CLI to be available in the test environment (standard on most CI systems).
- Temp directory cleanup must occur even if the test fails — use `with tempfile.TemporaryDirectory()` context manager.
- The test should not depend on any existing branches or commits in the project repo.

## Security considerations

- Temp repo must be created in a secure location (use `tempfile.TemporaryDirectory()` which creates dirs with restricted permissions).
- No credentials or secrets are involved — this is a pure test of GitPython behavior.

## Rollback considerations

- If the test fails due to environmental issues (e.g., `git` not installed), skip it with `pytest.skip()` rather than removing it.
- If the test exposes unexpected behavior, investigate before reverting.

## Validation plan

- Run the specific test: `uv run pytest tests/mcp_servers/git/test_format_output.py::test_format_checkout_real_repo_branch_switch -v`
- The test fails against pre-change code with the pathspec error ("pathspec 'feature' did not match any file(s) known to git").
- The test passes after the argument-order fix in `format_output.py`.
- Full suite: `uv run pytest tests/mcp_servers/git/ -v` — no new failures.
- Static analysis: `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`, `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- New test using a real temporary `git.Repo` (not `MagicMock`) with two branches exists.
- Test asserts `format_checkout()` actually switches the active branch.
- Test fails against pre-change code with the pathspec error.
- Test passes after the argument-order fix.
- No new static analysis findings.

## Out of scope

- Unit-level postcondition/post-state/stage-recording tests — covered by companion document for `test_repository_state.py`.
- HTTP dispatch path bypass-proof tests — covered by companion document for `test_git_security_compliance.py`.
- Known Issue documentation entry — covered by companion document for `docs/00_governance_03_issue-and-uncertainty-management.md`.
- `format_pull()`/`format_push()` equivalent defect checks — out of scope per UNK-02 (documented but not implemented here).

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260902-144908_gitpipeline_enforce_complete_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-190750_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-190750
- **Related target files**: tests/mcp_servers/git/test_format_output.py
