# Implementation Procedure

## Goal

Add the rejection, destination-protection, and schema-validation tests for the
git-mcp write-tool surface to `tests/mcp_servers/git/test_git_service_dispatch.py`
(`tests/mcp_servers/git/test_git_service_dispatch.py`). These lock the new
allow-list ref validation (`REQ-001`), the destination-based protected-branch
decision and the allowed escape from a protected branch (`REQ-002`, `REQ-003`),
and the now-required `branch` field (`REQ-004`) before the core logic changes are
in place. Driven by `REQ-001`, `REQ-002`, `REQ-004`; Tests 1, 2, 3.

## Scope

Modifies only `tests/mcp_servers/git/test_git_service_dispatch.py`. Cross-file
effects are dependencies, not targets:

- `scripts/mcp_servers/git/git_service.py` — provides the `_validate_ref_allowlist()`
  / `_validate_remote()` helpers this test calls directly (own document,
  `implementations/..._git_service.py.md`).
- `scripts/mcp_servers/git/git_models.py` — `GitPullRequest`/`GitPushRequest`
  `branch` becomes required (`REQ-004`); the schema test constructs these models
  directly.
- `scripts/mcp_servers/git/repository_state.py` — new `verify_authorization()`
  signature; the integration test exercises Stage 3 through the real pipeline.
- `tests/mcp_servers/git/test_repository_state.py` — owns the pipeline-input test
  (Test 4); own document.

## Assumptions

- The allow-list helper `_validate_ref_allowlist(ref)` returns `(ok, message)` and
  lives in `git_service.py` (created in the git_service row); the test calls it
  via the service instance without needing a repo.
- `_validate_remote(remote)` validates the remote against a conservative
  `[A-Za-z0-9._-]+` pattern; the test calls it the same way.
- `GitService` accepts `protected_branches` in its constructor (as the existing
  `_svc()` helper already threads constructor args), so the integration test can
  configure a protected list on a real temporary repository.
- Existing dispatch tests pass `branch` explicitly, so making `branch` required
  does not break them inside this file.

## Design decisions

- **Direct-helper unit test for the reject set (Test 1).** Because the
  allow-list helper is created in the git_service row, Test 1 asserts on
  `svc._validate_ref_allowlist(...)` / `svc._validate_remote(...)` return tuples
  rather than driving a full dispatch. This keeps Test 1 a pure unit test that
  does not require a repository.
- **Dispatch-level "before any GitPython call" proof (Test 2).** The rejection is
  proven to happen before any GitPython call by patching
  `RepositoryState.snapshot` with a `side_effect` that raises; a rejection that
  still surfaces as a `ValueError` can only have come from the pre-snapshot
  validator.
- **Schema test lives here, not in `test_git_models.py`.** `test_git_models.py`
  is not a frozen implementation-target row, so the `branch`-required schema test
  (Test 3) is added to this file and constructs the Pydantic models directly.
- **Escape test uses a real temporary repository.** Checkout away from a protected
  branch (`REQ-003`) is verified against a live repo so the postcondition and the
  destination comparison run for real.

## Alternatives considered

- **Drive Test 1 through the full `git_push` dispatch instead of the helper.**
  Rejected: a full dispatch needs a mocked `RepositoryState` snapshot and remote
  wiring for every parametrized form; calling the helper directly is a cleaner
  unit test and still proves the reject set.
- **Put Test 3 in `test_git_models.py`.** Rejected: that file is not a frozen
  target row, and this document MUST NOT instruct modification of a second file.

## Implementation

### Target file

`tests/mcp_servers/git/test_git_service_dispatch.py`

### Procedure

1. Add an allow-list rejection unit test (Test 1; `REQ-001`).
2. Add a dispatch-level rejection + destination-protection integration test
   (Test 2; `REQ-001`, `REQ-002`, `REQ-003`).
3. Add a `branch`-required schema test (Test 3; `REQ-004`).

### Method

#### Step 1 — Allow-list rejection unit test (Test 1; `REQ-001`)

Add class `TestWriteRefAllowlist`. Parametrize the rejected forms and assert the
helper rejects each; assert plain simple names pass.

```python
class TestWriteRefAllowlist:
    """REQ-001: allow-list validator rejects force-push / refspec forms."""

    @pytest.mark.parametrize(
        "bad",
        [
            "+main",
            "feature:main",
            "HEAD:main",
            "refs/heads/main",
            "main~1",
            "main..",
            "a b",
            "a\\b",
            "a@{1}",
            "[x]",
            "\0",
            "HEAD",
        ],
    )
    def test_rejected_branch_forms(self, bad) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, msg = svc._validate_ref_allowlist(bad)
        assert ok is False
        assert msg.startswith("[DENIED]")

    @pytest.mark.parametrize("good", ["main", "feature/x", "develop-1", "a.b"])
    def test_simple_names_pass(self, good) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, msg = svc._validate_ref_allowlist(good)
        assert ok is True
        assert msg == ""

    @pytest.mark.parametrize("bad", ["../evil", "a:b", "HEAD", "has space"])
    def test_rejected_remote_forms(self, bad) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, msg = svc._validate_remote(bad)
        assert ok is False
        assert msg.startswith("[DENIED]")

    @pytest.mark.parametrize("good", ["origin", "remote-1", "upstream"])
    def test_valid_remote_forms(self, good) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, msg = svc._validate_remote(good)
        assert ok is True
        assert msg == ""
```

#### Step 2 — Dispatch-level rejection + destination protection (Test 2; `REQ-001`, `REQ-002`, `REQ-003`)

Add two classes.

`TestGitPushRefRejectionBeforeGit`: each malicious form is rejected before any
GitPython call, proven by making `snapshot()` raise if reached.

```python
class TestGitPushRefRejectionBeforeGit:
    """REQ-001: malicious push refspec forms rejected before any GitPython call."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "bad",
        ["+main", "feature:main", "HEAD:main", "refs/heads/main", "main~1"],
    )
    async def test_rejected_before_snapshot(self, bad) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)

        def _no_snapshot(*_a, **_k):
            raise AssertionError("snapshot() must not be reached for a bad ref")

        with (
            patch.object(RepositoryState, "snapshot", side_effect=_no_snapshot),
            pytest.raises(ValueError, match="\\[DENIED\\]"),
        ):
            await svc.git_push(
                {"repo_path": "/opt/repos/proj", "branch": bad, "remote": "origin"}
            )
```

`TestDestinationBasedProtection`: against a real temporary repository with HEAD on
`main` (configured protected), checkout to an unprotected branch succeeds
(`REQ-003`), while a push onto the protected branch is rejected at dispatch
(`REQ-002`).

```python
class TestDestinationBasedProtection:
    """REQ-002/REQ-003: protected-branch decision is evaluated against the destination."""

    @pytest.mark.asyncio
    async def test_checkout_from_protected_succeeds(self, tmp_path) -> None:
        import pathlib

        repo_dir = pathlib.Path(str(tmp_path))
        # init a repo with an initial commit on main
        repo = git.Repo.init(repo_dir)
        (repo_dir / "f.txt").write_text("x")
        repo.index.add(["f.txt"])
        repo.index.commit("init")
        repo.create_branch("develop")
        svc = GitService(
            allowed_repo_paths=[str(repo_dir)],
            read_only=False,
            protected_branches=["main"],
            max_log_entries=50,
        )
        result = await svc.git_checkout(
            {"repo_path": str(repo_dir), "branch": "develop"}
        )
        assert "develop" in result  # switched away from protected main

    @pytest.mark.asyncio
    async def test_push_to_protected_rejected_at_dispatch(self, tmp_path) -> None:
        import pathlib

        repo_dir = pathlib.Path(str(tmp_path))
        repo = git.Repo.init(repo_dir)
        (repo_dir / "f.txt").write_text("x")
        repo.index.add(["f.txt"])
        repo.index.commit("init")
        svc = GitService(
            allowed_repo_paths=[str(repo_dir)],
            read_only=False,
            protected_branches=["main"],
            max_log_entries=50,
        )
        with pytest.raises(ValueError, match="protected branch"):
            await svc.git_push(
                {"repo_path": str(repo_dir), "branch": "main", "remote": "origin"}
            )
```

Note: the exact `format_*` output strings returned by a real checkout may vary;
assert on a stable substring (e.g. the target branch name) or on success rather
than an exact message. Adjust to whatever `format_checkout` returns once the core
logic lands.

#### Step 3 — `branch`-required schema test (Test 3; `REQ-004`)

Add class `TestGitPullPushBranchRequired`. Construct the models without `branch`
and assert a Pydantic `ValidationError`; assert a model with `branch` constructs.

```python
class TestGitPullPushBranchRequired:
    """REQ-004: git_pull/git_push require a non-empty branch."""

    def test_pull_requires_branch(self) -> None:
        with pytest.raises(ValidationError):
            GitPullRequest(repo_path="/x")

    def test_push_requires_branch(self) -> None:
        with pytest.raises(ValidationError):
            GitPushRequest(repo_path="/x")

    def test_pull_accepts_branch(self) -> None:
        req = GitPullRequest(repo_path="/x", branch="main")
        assert req.branch == "main"

    def test_push_accepts_branch(self) -> None:
        req = GitPushRequest(repo_path="/x", branch="main")
        assert req.branch == "main"
```

Import `from pydantic import ValidationError` and
`from mcp_servers.git.git_models import GitPullRequest, GitPushRequest` at the top
of the file.

### Details

- Keep the existing `_svc()` helper; it already forwards constructor args, so the
  integration test can build a `GitService` with `protected_branches` directly
  (or extend `_svc` with an optional `protected_branches` parameter).
- The dispatch-level rejection tests rely on the pre-snapshot ordering that the
  current handlers already follow (`_validate_ref`/`_validate_protected` run before
  `_run_tool`); the new allow-list helper replaces `_validate_ref` on the write
  paths (git_service row).
- No existing test in this file breaks from `branch` becoming required: every
  `git_pull`/`git_checkout` call site passes `branch` explicitly. Guard removal
  (`RepoValidationResult`) does not touch this file either. If running the full
  suite surfaces breakage in non-frozen files (`test_git_models.py`,
  `test_mcp_git.py`), that is an additional-target-file discovery — see below.

## Compatibility considerations

- The schema test assumes `GitPullRequest`/`GitPushRequest` declare `branch` as a
  required field (`Field(...)`). If a model still defaults `branch=""`, Test 3
  fails until `git_models.py` is updated (`REQ-004`, own document).
- Making `branch` required will break callers elsewhere that omit it
  (`test_git_models.py`, and any test constructing `GitPullRequest`/`GitPushRequest`
  with `branch=""`). Those files are not frozen rows; updating them is out of scope
  for this document and surfaces as additional-target-file discovery during the
  full-suite run (Step 3 of the toolchain).

## Security considerations

- The "before any GitPython call" proof (Step 2) is the key security assertion:
  a malicious refspec must be rejected by the validator, never forwarded to
  GitPython where `+main` could reach `git push -- <form>`. Do not weaken it by
  allowing `snapshot()` to run before the rejection.
- Fail-closed: the integration push-to-protected test asserts a rejection even
  though the pre-pipeline `_validate_protected()` and Stage 3 both cover it; keep
  both layers tested.

## Rollback considerations

- Revert the single commit touching `test_git_service_dispatch.py`. The added
  classes are self-contained; reverting restores the prior characterization suite
  unchanged.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| Allow-list reject set | Unit | `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py::TestWriteRefAllowlist -v` | all malformed forms rejected; simple names/remotes pass |
| Dispatch-level rejection | Unit (patched snapshot) | `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py::TestGitPushRefRejectionBeforeGit -v` | rejection raised; `snapshot()` never reached |
| Destination protection + escape | Integration (temp repo) | `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py::TestDestinationBasedProtection -v` | checkout FROM protected succeeds; push INTO protected rejected |
| Schema `branch` required | Unit | `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py::TestGitPullPushBranchRequired -v` | missing `branch` raises `ValidationError` |
| Whole git-mcp module | Full suite | `uv run pytest tests/mcp_servers/git/ -v` | no new failures |
| Toolchain | Static/type/security | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | clean per `rules/toolchain.md` |

## Completion criteria

- Every one of `+main`, `feature:main`, `HEAD:main`, `refs/heads/main`, `main~1`,
  `main..`, `a b`, `a\b`, `a@{1}`, `[x]`, `\0`, `HEAD` is rejected by the
  allow-list validator; plain `main`/`feature/x`-style names pass.
- Malicious push forms are rejected at dispatch before any `snapshot()`/GitPython
  call.
- With HEAD on a protected branch, checkout to an unprotected branch succeeds and
  a push onto the protected branch is rejected.
- `GitPullRequest`/`GitPushRequest` without `branch` fail Pydantic validation;
  with `branch` they construct.
- Full git-mcp suite and toolchain pass with no new failures.

## Out of scope

- Implementing the allow-list validator itself — `git_service.py`, own document.
- The pipeline-input re-check test (Test 4) — `test_repository_state.py`, own
  document.
- Snapshot-count (Test 5) and error-message (Test 6) tests — covered by the
  `git_service.py` / `repository_state.py` documents.
- Updating non-frozen test files broken by `branch`-required or guard removal
  (`test_git_models.py`, `test_mcp_git.py`) — additional-target-file discovery if
  the full-suite run requires it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add allow-list rejection unit tests (Test 1) | Pending | — | — | REQ-001 |
| 2 | Add dispatch-level rejection + destination-protection integration tests (Test 2) | Pending | — | — | REQ-001/002/003 |
| 3 | Add branch-required schema test (Test 3) | Pending | — | — | REQ-004 |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (allow-list ref validation for write `branch`/`remote`), `REQ-002` (route protected-branch decision to destination), `REQ-004` (make `branch` required in `git_pull`/`git_push`)
- **Source issue**: `issues/20261007-153840_gitref01_fix-git-mcp-ref-validation-and-protected-branch-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261007-162035_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261007-170610
- **Related target files**: `tests/mcp_servers/git/test_git_service_dispatch.py`
