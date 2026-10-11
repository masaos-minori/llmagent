## Goal

Add two tests to `TestFormatPush` in `tests/mcp_servers/git/test_format_output.py` that pin the push error path: a mocked `git.push` raising `git.exc.GitCommandError` must propagate unchanged out of `format_push` (`REQ-001`), and a successful push whose output merely contains rejection-like text must be returned unchanged (`REQ-002`).

## Scope

Additive only. Two methods are added inside the existing `TestFormatPush` class. No other file is modified. No production code (`scripts/mcp_servers/git/format_output.py`) is touched.

## Assumptions

- `format_push` calls `state._repo.git.push(req.remote, "--", branch)` directly (`format_output.py:232`) and returns `result or f"Pushed..."` (`233`) with no result-text matching; a `git.exc.GitCommandError` raised by `.push()` therefore propagates unchanged out of `format_push`.
- A successful push whose output merely contains rejection-like text is intentionally returned as-is (`REQ-002` intended behavior, owner-confirmed via `UNK-01` in the Plan).
- The existing helpers `_make_state`, `_mock_remote`, `_authorized_cfg` drive a mocked repo. `_authorized_cfg(REMOTE_URL)` authorizes the default mock remote URL, and `_mock_remote(mock_repo, "origin")` wires `mock_repo.remotes` so `_authorize_remote` passes before `.push()` is reached.
- `git` is not imported at module level in this file (only imported inline in `TestRealRepoRegression`); the new tests must `import git` to reference `git.exc.GitCommandError`.

## Design decisions

- Place both tests inside `TestFormatPush` to reuse its fixtures and stay colocated with `test_real_push_with_result`.
- Model `test_push_command_error_propagates` on `test_real_push_with_result`: build a `MagicMock` repo, set `mock_repo.git.push.side_effect = git.exc.GitCommandError(["git", "push"], 1)`, wire `_mock_remote(mock_repo, "origin")`, build state via `_make_state(_repo=mock_repo)`, authorize via `_authorized_cfg(REMOTE_URL)`, then assert `pytest.raises(git.exc.GitCommandError)` around the `format_push` call.
- Model `test_push_rejection_text_returned_unchanged` on `test_real_push_with_result`: set `mock_repo.git.push.return_value` to a synthetic string containing a rejection marker (e.g. `"remote: ![rejected] 'main' -> 'main' (non-fast-forward)"`), then assert `format_push` returns that exact string unchanged.
- Assert `REQ-001` directly on `format_push` (unit boundary), not through the service — the formatter's direct re-raise is the behavior under test.

## Alternatives considered

- Asserting the re-raise through `svc.git_push` instead of `format_push`: rejected — that path adds pipeline wrapping and would test `REQ-003`, not the formatter's direct re-raise. Keep `REQ-001` at the formatter boundary.
- Using a real temp repo for `REQ-001`: rejected — forcing a real push to fail is brittle; a mocked `side_effect` is deterministic.

## Implementation

### Target file

`tests/mcp_servers/git/test_format_output.py`

### Procedure

1. Ensure `import git` is available in the test (add a module-level `import git` if none exists; do not remove the existing inline import in `TestRealRepoRegression`).
2. Add `TestFormatPush::test_push_command_error_propagates`:
   - Build `mock_repo = MagicMock()`.
   - Set `mock_repo.git.push.side_effect = git.exc.GitCommandError(["git", "push"], 1)`.
   - Call `_mock_remote(mock_repo, "origin")`.
   - Build `state = _make_state(_repo=mock_repo)`.
   - Build `req = GitPushRequest(repo_path=REPO_PATH, remote="origin", branch="main", dry_run=False)`.
   - Assert `with pytest.raises(git.exc.GitCommandError): format_push(state, req, cfg=_authorized_cfg(REMOTE_URL))`.
3. Add `TestFormatPush::test_push_rejection_text_returned_unchanged`:
   - Build `mock_repo = MagicMock()`.
   - Set `mock_repo.git.push.return_value = "<synthetic rejection-like string>"`.
   - Call `_mock_remote(mock_repo, "origin")`.
   - Build `state = _make_state(_repo=mock_repo)`.
   - Build `req = GitPushRequest(repo_path=REPO_PATH, remote="origin", branch="main", dry_run=False)`.
   - Assign `result = format_push(state, req, cfg=_authorized_cfg(REMOTE_URL))`.
   - Assert `result == "<the same synthetic string>"`.

### Method

Model both tests on the existing `test_real_push_with_result` (fixture usage, `_authorized_cfg`, `_mock_remote`, `_make_state(_repo=...)`). Keep assertions at the formatter boundary.

### Details

- The rejection-like string in `REQ-002` MUST be synthetic and contain no real credential or URL — use a `remote:` line only.
- Use branch `"main"` (valid, non-protected) so no dispatch-time validation intervenes — this test is unit-level on `format_push`, which does not validate the branch.
- `GitCommandError` is constructed as `git.exc.GitCommandError(["git", "push"], 1)` (args + returncode), matching the pattern used elsewhere in the suite.

## Compatibility considerations

Pure additive test change. No production code, no public/runtime interface change, no import-boundary (`import-linter`) contract change. Existing tests are unaffected.

## Security considerations

None beyond existing test-suite norms. The `REQ-002` rejection string is synthetic (no real remote URL or credential).

## Rollback considerations

Delete the two added methods to revert. No production impact; no other files changed.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `test_format_output.py` (new + existing) | Unit | `uv run pytest tests/mcp_servers/git -q --timeout=60` | All pass |
| full suite | Regression | `uv run pytest tests -q --timeout=60` | All pass |
| static | format, lint, type, security, import boundary | `uv run ruff format`/`ruff check`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit scripts/mcp_servers/git`, `PYTHONPATH=scripts uv run lint-imports` | No new findings |

## Completion criteria

- `TestFormatPush::test_push_command_error_propagates` exists and `pytest.raises(git.exc.GitCommandError)` fires from within `format_push`.
- `TestFormatPush::test_push_rejection_text_returned_unchanged` exists and asserts the exact rejection-like string is returned unchanged by `format_push`.

## Out of scope

- Production code (`scripts/mcp_servers/git/format_output.py`).
- `REQ-003` (service-dispatch error wrapping) — see `implementations/20261011-183352_02_tests_mcp_servers_git_test_git_service_dispatch_py.md`.
- `REQ-004` (postcondition) — see `implementations/20261011-183352_03_tests_mcp_servers_git_test_repository_state_py.md`.
- Tests for non-push tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestFormatPush::test_push_command_error_propagates` (REQ-001; AC-1) | Completed | 20261011-190824 | 20261011-190824 |  |
| 2 | Add `TestFormatPush::test_push_rejection_text_returned_unchanged` (REQ-002; AC-2) | Completed | 20261011-190824 | 20261011-190824 | UNK-01 resolved |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261011-190824 | 20261011-190824 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261011-190824 | 20261011-190824 | N/A: test-only N/A: test-only, no docs changed |

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
- **Requirement ID**: `REQ-001`/`REQ-002` (formatter re-raises a pushed `GitCommandError`; formatter returns rejection-like output unchanged)
- **Source issue**: `issues/20261008-150557_gitpusherr01_restore-push-error-path-test-coverage-in-the-git-mcp-tests.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261009-165555_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-183352
- **Related target files**: `tests/mcp_servers/git/test_format_output.py`