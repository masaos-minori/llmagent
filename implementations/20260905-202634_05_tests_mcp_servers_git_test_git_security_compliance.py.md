## Goal
Add `POST /v1/call_tool` `TestClient` tests proving (a) Stage 3 (authorization) stays
active during dry-run against a protected branch, and (b) a dry-run request against a
dirty/detached-HEAD repository is not rejected by Stage 5 and performs no mutation
(`REQ-006`, `REQ-009`; `AC-3`, `AC-4`, `AC-6`).

## Scope
- In scope: new tests in this file exercising the real, unmocked live
  `POST /v1/call_tool` route end-to-end against real temporary git repositories (not
  `RepositoryState.snapshot` mocks), for `git_checkout` (primary coverage) and
  `git_pull`/`git_push` (same pattern, against a local bare-repo remote).
- Out of scope: `RepositoryState`-level unit tests (separate target file,
  `test_repository_state.py`); production code (separate target-file documents).

## Assumptions
- Per this Plan's revalidated Repository Evidence (see `plans/20260904-191122_plan.md`,
  Implementation Target Files, this row): this file already contains extensive
  `TestClient`/`/v1/call_tool` usage (`TestHTTPSiblingPathRejection`,
  `TestPostConditionBypassPrevention`, `TestCompletePipelineCoverage`), added by a
  commit after this Plan was authored — but none of it exercises
  `dry_run`/`allow_detached_head`/detached-HEAD; that gap is what this document
  closes.
- The file's existing `TestPostConditionBypassPrevention`/`TestCompletePipelineCoverage`
  classes monkeypatch `RepositoryState.snapshot` to a `MagicMock` with
  `verify_preconditions` stubbed directly — that pattern is unsuitable for this row's
  tests specifically, because it would bypass the exact method (`verify_preconditions()`)
  this Plan fixes, defeating the purpose of a regression test for `REQ-006`/`REQ-009`.
  This document's new tests must exercise the real `verify_preconditions()` via a real
  repo, not a mocked snapshot.
- `_cfg.allowed_repo_paths` defaults to `[]` (deny-all); the file's existing
  `TestHTTPSiblingPathRejection` class already establishes the pattern (lines
  505-520) of `git_server._cfg.allowed_repo_paths = [...]` inside a `try`/`finally`
  that restores the original value — this document's new tests must follow the same
  pattern with a real temp-repo path, or requests will be rejected before ever
  reaching Stage 5, producing a false-pass test (the same latent looseness observed
  in some of this file's existing tests, e.g. `TestPostConditionBypassPrevention`'s
  loose `is_error is True or "failed" in ...` assertions, which this document's new
  tests must not repeat).

## Design decisions
- New test class `TestDryRunAndDetachedHeadLivePath`, placed after
  `TestCompletePipelineCoverage` (end of file), using a `client` fixture identical to
  the existing pattern (`TestClient(app)` from `scripts.mcp_servers.git.git_server`).
- Build real temporary git repos (via `tmp_path`, mirroring
  `test_repository_state.py`'s `working_repo`/`dirty_repo`/`detached_repo` fixtures —
  do not duplicate a second definition of the same fixtures; either import/reuse via a
  shared conftest if one is introduced, or redefine locally scoped to this class if a
  shared conftest is out of scope for this Plan) rather than mocking
  `RepositoryState.snapshot`, so the real `verify_preconditions()` logic executes.
- Set `git_server._cfg.allowed_repo_paths = [str(repo_dir)]` and restore in
  `finally`, per the file's own established pattern — do not leave global `_cfg`
  mutated across tests.
- Use branch `"develop"` for the non-protected-branch dry-run tests (not in
  `["main", "master", "release"]`) and branch `"main"` for the Stage-3-active-during-
  dry-run test — matching this file's existing branch-name conventions.
- Assert on specific `[DENIED]`/success substrings and, for the non-mutation claim,
  assert the repo's actual git state (e.g. `git.Repo(repo_dir).is_dirty()` still
  `True`, `HEAD` still detached) is unchanged after the call — not merely
  `is_error is False`, avoiding this file's existing loose-assertion pattern.

## Alternatives considered
- Reusing `TestPostConditionBypassPrevention`'s mocked-`RepositoryState.snapshot`
  pattern: rejected — mocking `verify_preconditions()`'s return value would make these
  new tests pass regardless of whether the actual bug (this Plan's target) is fixed,
  providing no real regression coverage for `REQ-006`/`REQ-009`.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure
1. Add (or reuse, if a shared fixture module is introduced) real-repo fixtures for a
   dirty working tree and a detached HEAD, following `test_repository_state.py`'s
   `dirty_repo`/`detached_repo` fixtures (sibling document).
2. Add `TestDryRunAndDetachedHeadLivePath` with:
   - `test_dry_run_checkout_skips_dirty_and_detached_precondition`: POST
     `git_checkout` with `dry_run=True` against a dirty+detached real repo on a
     non-protected branch; assert not rejected at Stage 5 and the repo's dirty/
     detached state is unchanged after the call (no mutation).
   - `test_dry_run_checkout_protected_branch_still_denied`: POST `git_checkout` with
     `dry_run=True`, `branch="main"` (protected); assert `[DENIED]` and "protected
     branch" in the response (Stage 3 stays active during dry-run).
   - `test_non_dry_run_detached_head_denied_then_allowed`: POST `git_checkout` with
     `dry_run=False` against a detached-HEAD repo, once with
     `_cfg.allow_detached_head=False` (denied) and once with `True` (allowed),
     mirroring `test_repository_state.py`'s matrix but via the live route.
   - `test_dry_run_pull_and_push_skip_dirty_and_detached_precondition`: same
     dry-run/no-mutation assertion for `git_pull`/`git_push`, using a local bare repo
     as the `origin` remote (`git.Repo.init(str(tmp_path / "remote"), bare=True)`,
     added via `repo.create_remote("origin", remote_path)`) so `git_pull`/`git_push`
     have a real remote to target without needing network access.
3. Set `git_server._cfg.allowed_repo_paths = [str(repo_dir)]` in each test (or a
   fixture), restoring the original value in `finally`.

### Method
Direct test-code addition, following the file's established `TestClient`/`_cfg`
mutation-restoration pattern (lines 505-520). Read `WriteProtectionPipeline.run()`'s
exact Stage 5 call signature (sibling `repository_state.py` document) immediately
before writing these tests, to confirm the `dry_run`/`allow_detached_head` argument
order this document's live-path assertions depend on.

### Details
```python
class TestDryRunAndDetachedHeadLivePath:
    @pytest.fixture
    def client(self):
        from scripts.mcp_servers.git.git_server import app
        return TestClient(app)

    def test_dry_run_checkout_skips_dirty_and_detached_precondition(
        self, client, tmp_path
    ):
        from scripts.mcp_servers.git import git_server

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        repo = git.Repo.init(str(repo_dir))
        (repo_dir / "README.md").write_text("# test")
        repo.index.add(["README.md"])
        repo.index.commit("initial")
        repo.git.checkout(repo.head.commit.hexsha)  # detached
        (repo_dir / "README.md").write_text("# test\nuncommitted\n")  # dirty

        original = git_server._cfg.allowed_repo_paths
        try:
            git_server._cfg.allowed_repo_paths = [str(repo_dir)]
            response = client.post("/v1/call_tool", json={
                "name": "git_checkout",
                "args": {"repo_path": str(repo_dir), "branch": "develop", "dry_run": True},
            })
        finally:
            git_server._cfg.allowed_repo_paths = original

        body = response.json()
        assert body.get("is_error") is not True
        assert "[DENIED]" not in str(body.get("result", ""))
        assert git.Repo(str(repo_dir)).is_dirty()  # unchanged: still dirty, no mutation
```
(The remaining three tests in Procedure above follow the same real-repo,
`_cfg`-restore-in-`finally` shape — protected-branch and detached-head-denied/allowed
variants swap `branch`/`dry_run`/`_cfg.allow_detached_head`; the pull/push variant
additionally creates a bare-repo remote per Procedure step 2's fourth bullet.)

## Compatibility considerations
- Purely additive test file change; existing classes/tests in this file are
  unmodified.
- New tests mutate module-level `git_server._cfg.allowed_repo_paths` (and, for the
  detached-head-allowed case, `_cfg.allow_detached_head`) — each test MUST restore
  the original value in `finally`, matching this file's own established convention
  (lines 505-520, 536-551, etc.), to avoid leaking state into later tests in the same
  session (`pytest-randomly` is active per this suite's plugin list, so test order is
  not fixed — leaked config state would produce order-dependent failures).

## Security considerations
- These tests exercise the real authorization/precondition pipeline end-to-end
  (unmocked) specifically to prove Stage 3 is not bypassed during dry-run (`AC-4`) and
  that dry-run performs no actual mutation (`AC-3`) — this is itself the security
  property `REQ-005`/`REQ-009` require, verified here rather than assumed.

## Rollback considerations
- Test-only, additive; revertible independently via `git checkout` of this one file
  with no effect on production behavior. Any test that fails to restore
  `_cfg.allowed_repo_paths` in `finally` would leak state into later tests — verify
  this explicitly during review before considering this document's Step 1 complete.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` — new
  tests pass once the sibling `repository_state.py`/`git_server.py` documents' changes
  land; confirm each new test fails against the pre-change code (Stage 5 rejects the
  dirty/detached dry-run request identically to a real one) and passes after.
- `uv run pytest tests/mcp_servers/git/ -v` — full suite, no new failures, and no
  order-dependent failures under `pytest-randomly` (run at least twice with different
  `-p randomly` seeds to confirm no `_cfg` leakage).
- `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`.

## Completion criteria
- A dry-run `git_checkout`/`git_pull`/`git_push` request against a dirty/detached-HEAD
  repository, routed through the real `/v1/call_tool` endpoint, is not rejected by
  Stage 5 and performs no mutation to the repository or a local bare-repo remote.
- A dry-run request against a protected branch is still denied (Stage 3 active).
- A non-dry-run detached-HEAD request is denied when `allow_detached_head=False` and
  allowed when `True`, via the live route.

## Out of scope
- `RepositoryState`-level unit tests — `test_repository_state.py` sibling document.
- Production code changes — `repository_state.py`/`git_server.py` sibling documents.
- Fixing the existing, looser assertions in `TestPostConditionBypassPrevention`/
  `TestCompletePipelineCoverage` — out of this Plan's scope; noted only as a
  pattern this document's new tests must not repeat.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestDryRunAndDetachedHeadLivePath` with the four real-repo, `TestClient`-based tests | Pending | — | — | |
| 2 | Confirm each new test fails pre-change and passes post-change; run suite twice under different random seeds to check for `_cfg` leakage | Pending | — | — | |
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
- **Requirement ID**: REQ-006 (live-path threading verified end-to-end), REQ-009
  (dry-run non-mutation verified end-to-end)
- **Source issue**: issues/20260902-144909_gitdryrun_align_detached_head_and_dry_run_with_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191122_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-202634
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py
