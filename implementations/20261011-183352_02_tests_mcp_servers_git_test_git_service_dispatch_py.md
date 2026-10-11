## Goal

Add a service-dispatch test asserting that a push command error surfaces as `GitServiceError("git_push failed: ...")` when invoked through `svc.git_push()`, covering `pipeline.run` Stage 6 (`repository_state.py`) wrapping a push `GitCommandError` into a tool-named `GitServiceError` (`REQ-003`).

## Scope

Additive only. One method is added to the existing dispatch test file. No production code (`scripts/mcp_servers/git/git_service.py`, `repository_state.py`) is touched.

## Assumptions

- `git_push` validates the branch/remote at dispatch (raising `ValueError` on rejection), then delegates to `_run_tool`, which routes writes to `WriteProtectionPipeline(state).run(...)`.
- Pipeline Stage 6 (`repository_state.py:385-391`) catches any op exception (including `git.exc.GitCommandError`) via its `except Exception` handler and re-raises `GitServiceError(f"{tool_name} failed: {e}")`. For the push path `tool_name == "git_push"`.
- Reaching Stage 6 requires a non-None `GitConfig`: `_push_op` asserts `self._config is not None` (`git_service.py:459`), and `format_push` → `_authorize_remote` raises `GitPolicyError("[DENIED] remote ...")` (a `GitServiceError` subclass, re-raised unchanged by Stage 6's `except GitServiceError: raise`) when the remote URL is not authorized. So the test MUST build the service with `allowed_repo_paths` including the test repo AND `allowed_remote_urls` including the mock remote's URL.
- A bare `GitService(allowed_repo_paths=[...], read_only=False, protected_branches=[], max_log_entries=50)` (no `_config`) cannot reach the op; it surfaces a `GitPolicyError("[DENIED] remote ...")` that does NOT match `"git_push failed"` and would test the wrong branch.
- `build_service(cfg: GitConfig) -> GitService` (`git_service.py:490`) injects `_config=cfg`; equivalently `GitService(..., _config=cfg)`.
- `TestWrapGitOp` models the `pytest.raises(GitServiceError, match="...failed")` assertion pattern (direct `_wrap_git_op` call only — not the push code path).

## Design decisions

- Build the service via `build_service(cfg)` where `cfg = GitConfig(allowed_repo_paths=[str(repo_dir)], read_only=False, allowed_remote_urls=[REMOTE_URL], protected_branches=[], allow_detached_head=True)`.
- Patch `RepositoryState.snapshot` to return a `RepositoryState` constructed directly with a MagicMock `_repo` whose `.git.push.side_effect = git.exc.GitCommandError(["git", "push"], 1)` and `.remotes = [origin_mock(url=REMOTE_URL)]`, plus scalar fields that pass Stage 3/5: `is_dirty=False`, `head_type="branch"`, `active_branch="feature/x"`, `untracked_file_count=0`, `protected_branch=False`, `ref_valid=True`. This makes Stage 6 execute `format_push` → `_authorize_remote` (passes) → `git.push` raises → wrapped as `GitServiceError("git_push failed: ...")`.
- Invoke `await svc.git_push({"repo_path": str(repo_dir), "remote": "origin", "branch": "feature/x"})` inside `with pytest.raises(GitServiceError, match="git_push failed")`.
- Use a valid, non-protected branch name ("feature/x") so dispatch-time validation passes.

## Alternatives considered

- Constructing a real temp repo and patching `git.Repo.git.push`: more setup and real git operations; a mocked `RepositoryState.snapshot` is deterministic and avoids network/git side effects.
- Relying on an existing helper like `_svc()`: it defaults `read_only=True` / empty allowlist, which blocks the write path before Stage 6. Build the service explicitly with the required config.

## Implementation

### Target file

`tests/mcp_servers/git/test_git_service_dispatch.py`

### Procedure

1. Import what the test needs at module level if not already present: `import git` and `from mcp_servers.git.git_models import GitConfig`; confirm `from mcp_servers.git.errors import GitServiceError` and `from mcp_servers.git.repository_state import RepositoryState` are present (they are).
2. Create a real empty directory for the test repo path: `repo_dir = tmp_path / "push_repo"; repo_dir.mkdir()`.
3. Build the mock repo state:
   - `mock_repo = MagicMock()`.
   - `mock_repo.git.push.side_effect = git.exc.GitCommandError(["git", "push"], 1)`.
   - Wire the remote so `_authorize_remote` resolves an authorized URL: set `mock_repo.remotes = [<MagicMock with .name = "origin", .url = REMOTE_URL>]`. Use a module-level `REMOTE_URL` constant consistent with `test_format_output.py` (e.g. `"https://example.com/repo.git"`); define it locally if this file has none.
   - Construct `state = RepositoryState(path=str(repo_dir), is_dirty=False, head_type="branch", active_branch="feature/x", untracked_file_count=0, protected_branch=False, ref_valid=True, _repo=mock_repo)`.
4. Build the service: `cfg = GitConfig(allowed_repo_paths=[str(repo_dir)], read_only=False, allowed_remote_urls=[REMOTE_URL], protected_branches=[], allow_detached_head=True)`; `svc = build_service(cfg)` (import `build_service` from `mcp_servers.git.git_service`).
5. Add the test method:
   ```python
   async def test_push_command_error_becomes_service_error(self, tmp_path) -> None:
       repo_dir = tmp_path / "push_repo"
       repo_dir.mkdir()
       mock_repo = MagicMock()
       mock_repo.git.push.side_effect = git.exc.GitCommandError(["git", "push"], 1)
       origin = MagicMock()
       origin.name = "origin"
       origin.url = REMOTE_URL
       mock_repo.remotes = [origin]
       state = RepositoryState(
           path=str(repo_dir), is_dirty=False, head_type="branch",
           active_branch="feature/x", untracked_file_count=0,
           protected_branch=False, ref_valid=True, _repo=mock_repo,
       )
       cfg = GitConfig(
           allowed_repo_paths=[str(repo_dir)], read_only=False,
           allowed_remote_urls=[REMOTE_URL], protected_branches=[],
           allow_detached_head=True,
       )
       svc = build_service(cfg)
       with (
           patch.object(RepositoryState, "snapshot", return_value=state),
           pytest.raises(GitServiceError, match="git_push failed"),
       ):
           await svc.git_push({"repo_path": str(repo_dir), "remote": "origin", "branch": "feature/x"})
   ```
6. Confirm `patch` is imported (`from unittest.mock import patch, MagicMock` — already present in the file).

### Method

Drive the real dispatch path (`svc.git_push` → `_run_tool` → pipeline) with a patched `RepositoryState.snapshot` so Stage 6 executes `format_push` against a mocked repo whose `.push` raises. Assert the wrapped `GitServiceError` names the tool.

### Details

- The mock remote URL in `cfg.allowed_remote_urls` MUST equal the URL wired onto `mock_repo.remotes[0].url`, or `_authorize_remote` raises `GitPolicyError("[DENIED] remote ...")` (re-raised unchanged by Stage 6) instead of reaching `.push()` — that would fail the assertion and test the wrong branch.
- `active_branch="feature/x"` must be a valid simple branch name (passes `_validate_ref_allowlist`) and must not appear in `protected_branches` (passes `_validate_protected`).
- `allow_detached_head=True` guards Stage 5 even though `head_type="branch"` (not detached); harmless and defensive.
- The assertion uses `match="git_push failed"` (regex partial match against `f"git_push failed: {e}"`).

## Compatibility considerations

Pure additive test change. No production code, no public/runtime interface change, no import-boundary contract change. Existing dispatch tests are unaffected.

## Security considerations

None beyond existing test-suite norms.

## Rollback considerations

Delete the added method to revert. No production impact; no other files changed.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `test_git_service_dispatch.py` (new + existing) | Unit | `uv run pytest tests/mcp_servers/git -q --timeout=60` | All pass |
| full suite | Regression | `uv run pytest tests -q --timeout=60` | All pass |
| static | format, lint, type, security, import boundary | `uv run ruff format`/`ruff check`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit scripts/mcp_servers/git`, `PYTHONPATH=scripts uv run lint-imports` | No new findings |

## Completion criteria

- The new test reaches `pipeline.run` Stage 6 and asserts `pytest.raises(GitServiceError, match="git_push failed")` around `await svc.git_push(...)`.

## Out of scope

- Production code (`git_service.py`, `repository_state.py`).
- `REQ-001`/`REQ-002` (formatter) — see `implementations/20261011-183352_01_tests_mcp_servers_git_test_format_output_py.md`.
- `REQ-004` (postcondition) — see `implementations/20261011-183352_03_tests_mcp_servers_git_test_repository_state_py.md`.
- Tests for non-push tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add push service-error test through `svc.git_push()` (REQ-003; AC-3) | Completed | 20261011-192815 | 20261011-192815 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261011-192815 | 20261011-192815 |  |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261011-192815 | 20261011-192815 | N/A: test-only N/A: test-only, no docs changed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (pipeline Stage 6 wraps a push `GitCommandError` into a tool-named `GitServiceError`)
- **Source issue**: `issues/20261008-150557_gitpusherr01_restore-push-error-path-test-coverage-in-the-git-mcp-tests.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261009-165555_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-183352
- **Related target files**: `tests/mcp_servers/git/test_git_service_dispatch.py`