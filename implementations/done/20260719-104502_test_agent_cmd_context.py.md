Source plan: `plans/20260719-093757_plan.md` ("Add `/diff` slash command to review files the agent
wrote/edited this session"), Implementation step 3.

No existing implementations doc (under `implementations/` or `implementations/done/`) targets
`tests/test_agent_cmd_context.py` by this exact name; the only near-match is
`implementations/20260708-172107_test_agent_cmd_context_m4.py.md`, which is for a **different** file,
`tests/test_agent_cmd_context_m4.py` (an `_m4`-suffixed file from an earlier cycle, confirmed by its own
title). Grepped it for `_cmd_diff`/`"/diff"`/`git_diff` — zero matches. Flagged as checked, not a
genuine overlap; no doc covers adding `/diff` test cases to `tests/test_agent_cmd_context.py` itself.

## Goal

Add test coverage for the new `_cmd_diff` method (see paired doc
`implementations/20260719-104343_cmd_context.py.md`) to `tests/test_agent_cmd_context.py`, covering: no
touched files, a real diff for one touched path, a touched path with no matching hunk, a touched path
outside any git repository, and a denied/error `git_diff` response — matching this test file's existing
`_FakeCmd(_ContextMixin)` / `_make_ctx()` conventions plus this codebase's established
`unittest.mock`-based GitPython-mocking pattern (`tests/test_mcp_git.py`).

## Scope

**In scope**
- Add a new `TestCmdDiff` class (and any small new helper functions/fixtures it needs) to
  `tests/test_agent_cmd_context.py`, exercising `_cmd_diff` per the plan's Implementation step 3
  scenarios (a)-(e).

**Out of scope**
- Implementing `_cmd_diff` itself (paired `cmd_context.py` doc) or the `CommandDef` entry (paired
  `command_defs_list.py` doc).
- `tests/test_command_def_sync.py` — unaffected; that suite validates `_COMMANDS`/handler-name
  consistency generically and needs no `/diff`-specific edit (same reasoning already used by the two
  sibling `/session`-help-string docs for this same suite).

## Assumptions

1. Current file state (re-verified by direct read of `tests/test_agent_cmd_context.py`): the harness is
   `_FakeCmd(_ContextMixin)` at lines 20-22 (`self._ctx = ctx` only — no `_out` override, so `_out`
   defaults to the class-level `CliOutputPort()` from `MixinBase`, and `capsys` captures its
   `print(...)` calls) and `_make_ctx() -> MagicMock` at lines 25-46, which returns a bare `MagicMock()`
   with specific attributes pre-set (`ctx.conv.history = []`, `ctx.services_required.hist_mgr = None`,
   etc.). No test in this file today exercises anything `async`, so this doc introduces the file's
   first `@pytest.mark.asyncio` test class.
2. `pytest-asyncio` is a project dependency (`pyproject.toml:51`: `"pytest-asyncio>=0.23"`) with
   `asyncio_mode = "auto"` configured (`pyproject.toml:108`, `[tool.pytest.ini_options]`) — re-verified
   directly. This means `@pytest.mark.asyncio` decorators are not strictly required for `async def
   test_*` functions to run, but the codebase's own convention (verified in `tests/test_cmd_mdq.py` and
   `tests/test_mcp_git.py`, both using `@pytest.mark.asyncio` explicitly on every async test) is to add
   the marker anyway for clarity/explicitness; this doc follows that convention.
3. **Correction, carried over from the paired `cmd_context.py` doc's Assumption 6**: the plan's own text
   suggests mocking `ctx.services_required.tools.execute = AsyncMock(...)`, matching `tests/
   test_cmd_mdq.py`'s convention (its `_Ctx` stub defines a `services_required` property that returns
   `self.services`, so setting `ctx.services_required.tools.execute` there also affects
   `ctx.services.tools.execute` since both names resolve to the same underlying object). However, this
   test file's own `_make_ctx()` returns a **bare `MagicMock()`**, not a custom stub class with a real
   `services_required` property — on a plain `MagicMock`, `ctx.services` and `ctx.services_required` are
   two *independent* auto-created child mocks (no relationship between them). Since the paired
   `cmd_context.py` doc specifies `_cmd_diff` reads `ctx.services`/`ctx.services.tools.execute` directly
   (matching `cmd_mdq.py`'s actual verified production-code pattern, not `services_required`), tests in
   this doc must set `ctx.services.tools.execute = AsyncMock(...)` (and, for the "tools not available"
   case, `ctx.services = None` or `ctx.services.tools = None`) — **not** `ctx.services_required....`,
   since that would silently mock an unrelated attribute path that `_cmd_diff` never reads, causing the
   test to pass for the wrong reason (or fail to stub the real call site).
4. `ToolCallResult` (`scripts/shared/transport_dto.py:7-15`) requires `output`, `is_error`, `request_id`,
   `server_key` (no defaults on the latter two); `source`/`error_type` default to `""`. Tests construct
   it as `ToolCallResult(output=..., is_error=..., request_id="", server_key="")`, or — matching `tests/
   test_cmd_mdq.py`'s own lighter-weight convention — use `mcp_servers.dispatch.DispatchResult(output=...,
   is_error=...)`, which is duck-type-compatible since `_cmd_diff` only reads `.output`/`.is_error`.
   This doc uses `ToolCallResult` for realism (it is the actual type `ctx.services.tools.execute`
   returns per `shared/tool_executor.py`'s `ToolExecutor` contract, not independently re-read line-by-
   line here beyond the paired doc's Assumption 7), but either is acceptable at implementation time.
5. GitPython (`git.Repo`) construction inside `_cmd_diff`'s `_group_paths_by_repo` helper (paired doc,
   Procedure step 4) is the natural mock point for controlling repo-detection outcomes without touching
   the real filesystem — mirroring `tests/test_mcp_git.py`'s own established pattern of mocking a
   `git.Repo`-like object (there via `patch.object(svc, "_open_repo", return_value=mock_repo)`; here via
   `patch("agent.commands.cmd_context.git.Repo")` since `_cmd_diff`'s helper constructs `git.Repo(...)`
   directly rather than going through a dedicated `_open_repo`-style indirection point).

## Implementation

### Target file

`tests/test_agent_cmd_context.py`.

### Procedure

1. Add imports: `from unittest.mock import AsyncMock` (alongside the existing `MagicMock, patch` import
   at line 9) and `from shared.transport_dto import ToolCallResult`. Add `import git` only if the test
   needs to reference `git.InvalidGitRepositoryError` directly as a `side_effect` (it will).
2. Add a new section near the end of the file (after `TestCollectContextStateWorkflow`, the current
   last class ending around line 530) with a `# ── /diff ──` header comment, matching this file's
   existing section-comment style (e.g. `# ── _cmd_undo ──` at line 69).
3. Add helper(s) local to this section as needed, e.g. a `_write_tool_call_msg(path: str, fn: str =
   "write_file") -> dict` that returns
   `{"role": "assistant", "content": None, "tool_calls": [{"id": "1", "type": "function", "function":
   {"name": fn, "arguments": json.dumps({"path": path})}}]}` (add `import json` to the test file's
   top-level imports if not already present — re-check at implementation time; not currently imported
   per the file's current import block, lines 1-15).
4. Add `class TestCmdDiff:` with the following test methods (mapping directly to the plan's
   Implementation step 3 (a)-(e)):
   - `test_no_touched_files_prints_nothing_to_show` (async): `ctx = _make_ctx()` with
     `ctx.conv.history = []` (default); `cmd = _FakeCmd(ctx)`; `await cmd._cmd_diff()`; assert
     `capsys.readouterr().out` contains `"No files written or edited"`; assert
     `ctx.services.tools.execute` was **not** called (since there is nothing to diff).
   - `test_one_touched_path_with_real_diff_prints_hunk` (async): history has one
     `_write_tool_call_msg("/repo/a.py")`; patch `agent.commands.cmd_context.git.Repo` so constructing
     it returns a `MagicMock(working_tree_dir="/repo")` (no exception raised); set
     `ctx.services.tools.execute = AsyncMock(return_value=ToolCallResult(output="diff --git a/a.py
     b/a.py\n@@ -1 +1 @@\n-old\n+new\n", is_error=False, request_id="", server_key=""))`; assert the
     printed output contains the touched path and the hunk body (`"-old"`, `"+new"`); assert
     `ctx.services.tools.execute.assert_called_once_with("git_diff", {"repo_path": "/repo", "commit":
     ""})`.
   - `test_touched_path_with_no_matching_hunk_prints_no_diff_notice` (async): same setup as above but
     `git_diff`'s returned diff text has a `diff --git a/other.py b/other.py` header only (no header
     for the touched `a.py`); assert output contains `"a.py"` and `"no working-tree diff"`.
   - `test_touched_path_outside_git_repo_prints_skipped_notice_and_completes` (async): history has two
     touched paths — one inside a repo (as in the real-diff case above) and one for which
     `git.Repo(...)` raises `git.InvalidGitRepositoryError` (patch with `side_effect=` a list/dict
     keyed by path, or two separate `patch` contexts, whichever is simplest to express); assert the
     command does not raise, output contains `"not inside a git repository (skipped)"` for the
     outside-repo path, and still contains the real diff/hunk for the in-repo path (verifies both
     buckets are processed in the same run, per the plan's explicit acceptance criterion).
   - `test_git_diff_denied_prints_per_repo_denial_and_completes` (async): one touched path inside a
     repo; `ctx.services.tools.execute = AsyncMock(return_value=ToolCallResult(output="[DENIED]
     repo_path '/repo' is not in allowed_repo_paths", is_error=True, request_id="", server_key=""))`;
     assert output contains `"git diff unavailable"` and the repo path, and that the command completes
     without raising.
   - `test_tools_not_available_prints_message` (async, additional case beyond the plan's lettered list,
     covering the paired doc's `ctx.services is None` branch): one touched path in history,
     `ctx.services = None`; assert output contains `"not available"` and the command does not raise.
   - `test_path_with_space_matches_correct_hunk` (async, per the plan's own Risks section, which
     explicitly calls for "a dedicated test for a path containing a space"): touched path
     `"/repo/my file.py"`; `git_diff` output contains `diff --git a/my file.py b/my file.py\n@@ ...`;
     assert the space-containing path's hunk is correctly matched and printed (not silently treated as
     "no working-tree diff").

### Method

Pure additive test-writing; no change to existing test classes/fixtures. Follows this file's existing
`_FakeCmd`/`_make_ctx` harness plus `unittest.mock.patch`/`AsyncMock`, consistent with
`tests/test_cmd_mdq.py` and `tests/test_mcp_git.py`'s established async/GitPython-mocking conventions.

### Details

- Every new test method takes `capsys: Any` (matching this file's existing type-annotation style for
  that fixture, e.g. `cmd_context.py:163` `def test_undo_with_no_user_message_prints_nothing(self,
  capsys: Any) -> None:` — re-verified) and is declared `async def`, decorated `@pytest.mark.asyncio`.
- `ctx.conv.history` entries must be plain dicts matching `LLMMessage`'s shape (per the paired doc's
  Assumption 4): `role`, optional `content`, and `tool_calls: list[dict]` with each entry shaped as
  `{"id": ..., "type": "function", "function": {"name": ..., "arguments": <json str>}}` — this doc's
  `_write_tool_call_msg` helper (Procedure step 3) is the single place that constructs this shape so
  every test method stays terse.
- Patch target for GitPython must be the name as imported into `cmd_context.py` (i.e.
  `"agent.commands.cmd_context.git.Repo"`, since the paired doc's Procedure step 1 adds `import git`
  to that module) — not `"git.Repo"` directly, per standard `unittest.mock` patch-where-used guidance.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format tests/test_agent_cmd_context.py && uv run ruff check tests/test_agent_cmd_context.py` | 0 errors |
| Type check | `uv run mypy tests/test_agent_cmd_context.py` | 0 new errors vs. baseline (if `tests/` is in mypy's scope — confirm via existing baseline; not otherwise a new requirement introduced by this doc) |
| New test class present | `rg -n "class TestCmdDiff" tests/test_agent_cmd_context.py` | 1 match |
| Targeted run | `uv run pytest tests/test_agent_cmd_context.py -k TestCmdDiff -v` | all new `/diff` tests pass |
| Full file | `uv run pytest tests/test_agent_cmd_context.py -v` | all pass, no regressions in existing classes |
| Registry sync (unaffected) | `uv run pytest tests/test_command_def_sync.py -v` | passes unchanged |
| Coverage on changed lines | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on `_cmd_diff` and its helpers, covered by the 7 new test methods above |
| Full suite | `uv run pytest -v` | no new failures vs. pre-change baseline |
