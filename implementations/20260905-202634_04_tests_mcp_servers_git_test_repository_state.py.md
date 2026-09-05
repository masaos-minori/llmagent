## Goal
Add unit tests for `verify_preconditions()`'s new `dry_run`/`allow_detached_head`
parameters (`REQ-001` through `REQ-004`; `AC-1`, `AC-2`, `AC-5`), covering the 2x2
matrix of `dry_run` x `allow_detached_head` against a dirty and a detached-HEAD
repository state.

## Scope
- In scope: new test cases in this file exercising `RepositoryState.verify_preconditions()`
  directly, against real `working_repo`-style fixtures made dirty or detached.
- Out of scope: `POST /v1/call_tool` `TestClient`-level tests (separate target file,
  `test_git_security_compliance.py`); the production code under test (separate target
  files).

## Assumptions
- `verify_preconditions()`'s new parameters default to `False` (per the
  `repository_state.py` sibling document's Design decisions) — existing calls at
  lines 180 (`TestGuardDelegation`) and 279 (`TestPipelineOrdering`) that pass only
  `"checkout"` continue to pass unchanged; this document adds new test cases rather
  than modifying those two.
- A "dirty" state is produced by writing an uncommitted change to a file already
  tracked in `working_repo`; a "detached HEAD" state is produced by checking out a
  commit SHA directly (`repo.git.checkout(repo.head.commit.hexsha)`), matching how a
  real detached-HEAD state arises — consistent with this file's existing convention of
  using real `git.Repo` fixtures rather than mocks in `TestGuardDelegation`/
  `TestPipelineOrdering`/`TestGuardIntegration`.

## Design decisions
- New test class `TestVerifyPreconditionsDryRunAndDetachedHead`, placed after the
  existing `TestPipelineOrdering` class (before `TestGuardIntegration`) since it tests
  the same `verify_preconditions()` surface those two classes already touch.
- Use real repo-state fixtures (dirty via an uncommitted write, detached via
  `git checkout <sha>`), not mocks — matching this file's existing style for
  `RepositoryState`-level tests (`working_repo` fixture, direct `git.Repo` operations)
  rather than introducing a new mocking pattern only for this row.
- Parametrize over the 2x2 `dry_run` x `allow_detached_head` matrix per state (dirty,
  detached) using `pytest.mark.parametrize`, matching the Plan's Tests section
  wording ("parametrized unit tests ... covering the 2x2 matrix").

## Alternatives considered
- Mocking `RepositoryState.snapshot()` (as `test_git_security_compliance.py`'s
  `TestGitSecurityCompliance` class already does for `GitService`-level tests):
  rejected for this file — this file's existing `RepositoryState`-level tests
  (`TestGuardDelegation`, `TestPipelineOrdering`, `TestGuardIntegration`) all use real
  `working_repo`/`bare_repo` fixtures; mocking here would be inconsistent with the
  file's established convention and would test the mock's return value, not the real
  `is_dirty`/`is_detached_head` properties this row's logic reads.

## Implementation
### Target file
`tests/mcp_servers/git/test_repository_state.py`

### Procedure
1. Add two new fixtures (or extend `working_repo` via a helper) producing (a) a dirty
   working tree and (b) a detached HEAD, both built on top of the existing
   `working_repo` fixture.
2. Add a new class `TestVerifyPreconditionsDryRunAndDetachedHead` with parametrized
   tests covering: dirty + dry_run=True (allowed), dirty + dry_run=False (denied,
   regardless of allow_detached_head), detached + dry_run=True (allowed), detached +
   dry_run=False + allow_detached_head=False (denied), detached + dry_run=False +
   allow_detached_head=True (allowed).
3. Assert both the boolean result and, for denied cases, the expected `[DENIED]`
   message substring (matching this file's existing assertion style, e.g. line
   181-182's `assert ok is True` / `assert err == ""`).

### Method
Direct test-code addition. Read `working_repo`'s fixture definition (lines 28-39,
already read) and `TestPipelineOrdering`'s existing `verify_preconditions("checkout")`
call (line 279) as the pattern to extend, not replace.

### Details
```python
@pytest.fixture()
def dirty_repo(working_repo: str) -> str:
    Path(working_repo, "README.md").write_text("# test\nuncommitted change\n")
    return working_repo


@pytest.fixture()
def detached_repo(working_repo: str) -> str:
    repo = git.Repo(working_repo)
    repo.git.checkout(repo.head.commit.hexsha)
    return working_repo


class TestVerifyPreconditionsDryRunAndDetachedHead:
    def test_dirty_worktree_dry_run_true_is_allowed(self, dirty_repo: str) -> None:
        state = RepositoryState.snapshot(dirty_repo)
        ok, err = state.verify_preconditions("checkout", dry_run=True)
        assert ok is True
        assert err == ""

    @pytest.mark.parametrize("allow_detached_head", [False, True])
    def test_dirty_worktree_dry_run_false_is_denied(
        self, dirty_repo: str, allow_detached_head: bool
    ) -> None:
        state = RepositoryState.snapshot(dirty_repo)
        ok, err = state.verify_preconditions(
            "checkout", dry_run=False, allow_detached_head=allow_detached_head
        )
        assert ok is False
        assert "dirty worktree" in err

    def test_detached_head_dry_run_true_is_allowed(self, detached_repo: str) -> None:
        state = RepositoryState.snapshot(detached_repo)
        ok, err = state.verify_preconditions("checkout", dry_run=True)
        assert ok is True
        assert err == ""

    def test_detached_head_dry_run_false_allow_false_is_denied(
        self, detached_repo: str
    ) -> None:
        state = RepositoryState.snapshot(detached_repo)
        ok, err = state.verify_preconditions(
            "checkout", dry_run=False, allow_detached_head=False
        )
        assert ok is False
        assert "detached HEAD" in err

    def test_detached_head_dry_run_false_allow_true_is_allowed(
        self, detached_repo: str
    ) -> None:
        state = RepositoryState.snapshot(detached_repo)
        ok, err = state.verify_preconditions(
            "checkout", dry_run=False, allow_detached_head=True
        )
        assert ok is True
        assert err == ""
```
Confirm `RepositoryState.snapshot()`'s exact fixture-refresh semantics (does it
recompute `is_dirty`/`is_detached_head` from the live repo each call, or cache from
construction?) by reading its definition immediately before writing these tests, since
the fixtures above rely on the snapshot reflecting the just-mutated repo state.

## Compatibility considerations
- Purely additive test file change; existing tests (`TestGuardDelegation`,
  `TestPipelineOrdering`) are unmodified and continue to pass unchanged because the
  production code's new parameters default to today's behavior.

## Security considerations
- N/A: test-only change, no production code path affected.

## Rollback considerations
- Test-only, additive; revertible independently via `git checkout` of this one file
  with no effect on production behavior.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` — new tests pass
  once the sibling `repository_state.py` document's change lands; confirm each new
  test fails against the pre-change code (still unconditionally rejecting dirty/
  detached regardless of `dry_run`) and passes after, per the Plan's Tests section.
- `uv run pytest tests/mcp_servers/git/ -v` — full suite, no new failures.
- `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`
  (test files are covered by the same lint/type commands per `rules/toolchain.md`).

## Completion criteria
- The 2x2 `dry_run` x `allow_detached_head` matrix is covered for both a dirty and a
  detached-HEAD repository state, with each new test failing pre-change and passing
  post-change.

## Out of scope
- `POST /v1/call_tool` HTTP-level tests — `test_git_security_compliance.py` sibling
  document.
- Production code changes — `repository_state.py`/`git_server.py` sibling documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `dirty_repo`/`detached_repo` fixtures and `TestVerifyPreconditionsDryRunAndDetachedHead` with the 2x2 matrix tests | Pending | — | — | |
| 2 | Confirm each new test fails pre-change and passes post-change | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test file, no doc impact |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004 (test coverage for the
  dry_run/allow_detached_head matrix)
- **Source issue**: issues/20260902-144909_gitdryrun_align_detached_head_and_dry_run_with_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191122_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-202634
- **Related target files**: tests/mcp_servers/git/test_repository_state.py
