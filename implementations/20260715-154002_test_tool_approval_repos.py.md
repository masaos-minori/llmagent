# Implementation: Add `gitops_push_blocked` scope-parity tests to `tests/test_tool_approval_repos.py`

Source plan: `plans/20260715-141245_plan.md` (Implementation step 4, gitops/allowlist portion)

## Goal

Add regression tests to `tests/test_tool_approval_repos.py` proving the
new `_GITOPS_BLOCKABLE_TOOLS` constant (see
`20260715-154002_tool_approval.py.md`) blocks exactly the same 7
repo/PR-mutating GitHub tools as today, and explicitly does **not**
block `github_create_issue`/`github_add_issue_comment` — documenting the
intentional scope split from plan Assumption 4 / UNK-03 as an executable
test rather than only a code comment.

## Scope

**In scope**
- `tests/test_tool_approval_repos.py`: extend the existing
  `TestGitopsGuards` class with:
  - a parametrized/loop test asserting `gitops_push_blocked=True` blocks
    `github_push_files`, `github_create_or_update_file`,
    `github_delete_file`, `github_merge_pull_request`,
    `github_create_branch`, `github_create_pull_request`,
    `github_update_pull_request`.
  - a test asserting `gitops_push_blocked=True` does **not** block
    `github_create_issue` and `github_add_issue_comment` (these proceed
    to the normal risk/prompt flow instead of being denied at the
    gitops guard).

**Out of scope**
- `tests/test_tool_approval_preflight.py` (dry-run failure tests) —
  covered by its own companion doc.
- Any change to `scripts/agent/tool_approval.py` itself — covered by
  `20260715-154002_tool_approval.py.md`.

## Assumptions

1. The existing `TestGitopsGuards` class (lines 156-196 of the current
   file) already has one representative case
   (`test_github_push_blocked_when_flag_set`, using
   `github_push_files`) and one negative case
   (`test_non_github_tool_not_blocked_by_gitops`, using
   `read_text_file`). New tests add coverage for the *other 6* tools in
   the mutation set and the explicit issue-tools exclusion, rather than
   duplicating the existing single-tool case.
2. `_make_cfg(gitops_push_blocked=True)` and `_make_ctx(cfg)` (defined at
   lines 21 and 95 of this file) are reused unchanged — no new fixture
   is needed.
3. For the two issue tools, `check_approval()` must not short-circuit at
   the gitops guard, but it will still proceed into the normal
   risk-classification/prompt path. Per `_DEFAULT_APPROVAL_RISK_RULES` in
   `scripts/agent/config_builders.py` (line 79),
   `github_create_issue` classifies as `"medium"` risk, so the test must
   patch `agent.tool_approval._prompt_user_approval` (as the existing
   `test_github_push_blocked_false_does_not_block_by_flag` test already
   does at line 173-174) to avoid blocking on real stdin input, and
   assert the call reaches the prompt (i.e. returns `True` when the
   patched prompt returns `True`) rather than being denied before that
   point.
4. `github_add_issue_comment` is not present in
   `_DEFAULT_APPROVAL_RISK_RULES`; confirm its risk falls through to
   `classify_risk()`'s constants-based fallback (Priority 3 in
   `tool_policy.classify_risk`) — since it is in `WRITE_TOOLS`... actually
   it is a GitHub tool, not in `shared.tool_constants.WRITE_TOOLS`
   (which only covers filesystem tools), so it falls through to the
   final default `RiskLevel.MEDIUM` (Priority 4). Either way it is not
   `RiskLevel.NONE`, so the test must patch `_prompt_user_approval` the
   same way as `github_create_issue`.

## Implementation

### Target file

`tests/test_tool_approval_repos.py` (existing)

### Procedure

1. Add to `TestGitopsGuards` (after
   `test_non_github_tool_not_blocked_by_gitops`, before
   `test_allowed_repos_rejects_unlisted_repo`):
   ```python
   @pytest.mark.asyncio
   @pytest.mark.parametrize(
       "tool_name",
       [
           "github_push_files",
           "github_create_or_update_file",
           "github_delete_file",
           "github_merge_pull_request",
           "github_create_branch",
           "github_create_pull_request",
           "github_update_pull_request",
       ],
   )
   async def test_gitops_blocks_all_mutation_tools(self, tool_name: str) -> None:
       """gitops_push_blocked=True denies every repo/PR-mutating GitHub tool."""
       cfg = _make_cfg(gitops_push_blocked=True)
       ctx = _make_ctx(cfg)
       result = await check_approval(ctx, tool_name, {})
       assert result is False

   @pytest.mark.asyncio
   @pytest.mark.parametrize(
       "tool_name", ["github_create_issue", "github_add_issue_comment"]
   )
   async def test_gitops_does_not_block_issue_tools(self, tool_name: str) -> None:
       """gitops_push_blocked=True does not block issue-tracker mutations."""
       cfg = _make_cfg(gitops_push_blocked=True)
       ctx = _make_ctx(cfg)
       with patch(
           "agent.tool_approval._prompt_user_approval", AsyncMock(return_value=True)
       ):
           result = await check_approval(ctx, tool_name, {})
       assert result is True
   ```
2. Confirm `pytest.mark.parametrize` usage is consistent with any
   existing parametrized tests elsewhere in the `tests/` tree (if this
   file has none yet, this introduces the pattern locally — acceptable,
   `pytest` config already supports it via the existing `pyproject.toml`
   `[tool.pytest.ini_options]` asyncio mode).

### Method

Two small parametrized test additions inside the existing
`TestGitopsGuards` class; no new fixtures, no changes to `_make_cfg`/
`_make_ctx`.

### Details

- Keep test names descriptive and specific
  (`test_gitops_blocks_all_mutation_tools`,
  `test_gitops_does_not_block_issue_tools`) to make CI failures
  self-explanatory if the scope split is ever changed unintentionally.
- Do not add a docstring claiming this is exhaustive proof of "security
  intent" — per plan Risk #2, the scope split is a product/security
  decision flagged for reviewer sign-off, not a settled fact; the test
  docstrings should describe current behavior only.

## Validation plan

```bash
uv run ruff format tests/test_tool_approval_repos.py
uv run ruff check tests/test_tool_approval_repos.py
uv run mypy tests/test_tool_approval_repos.py
uv run pytest tests/test_tool_approval_repos.py -v
```

Expected: 0 lint errors, no new mypy errors; 9 new parametrized test
cases pass (7 blocked + 2 not-blocked), plus all pre-existing tests in
this file continue to pass unchanged.

## Note on prior implementation documents

No existing document under `implementations/` or `implementations/done/`
targets `test_tool_approval_repos.py` (confirmed via `find implementations
-iname "*test_tool_approval_repos*"` — no results). This is a new
implementation item with no prior overlap to reconcile.
