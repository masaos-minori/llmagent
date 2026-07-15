# Implementation: Add high-risk dry-run-failure-blocking tests to `tests/test_tool_approval_preflight.py`

Source plan: `plans/20260715-141245_plan.md` (Implementation step 4, dry-run portion)

## Goal

Add regression tests to the existing `TestCheckApprovalDryRun` class in
`tests/test_tool_approval_preflight.py` proving:
1. a dry-run result with `is_error=True` on a HIGH-risk tool denies the
   approval immediately (audited as `denied_dry_run_error`) without
   prompting the user.
2. a dry-run `RuntimeError` (unsupported/connection failure) on a
   HIGH-risk tool still falls back to the text preview and prompts —
   unchanged behavior, extending coverage of the existing
   `test_dry_run_exception_does_not_abort_approval` test (which only
   covers a MEDIUM-risk tool, `write_file`) to the HIGH-risk case.

This is the test counterpart to the `_build_preview_with_dry_run`/
`check_approval` changes described in
`20260715-154002_tool_approval.py.md`.

## Scope

**In scope**
- `tests/test_tool_approval_preflight.py`: add 2 new tests to
  `TestCheckApprovalDryRun` (currently lines 354-478).

**Out of scope**
- `tests/test_tool_approval_repos.py` (gitops scope tests) — covered by
  its own companion doc.
- `scripts/agent/tool_approval.py`, `scripts/agent/tool_exceptions.py` —
  covered by their own companion docs.

## Assumptions

1. `delete_file` is both HIGH-risk (per `_DEFAULT_APPROVAL_RISK_RULES` in
   `scripts/agent/config_builders.py`, line 69: `"delete_file": "high"`)
   and in the default dry-run tool set (`_DEFAULT_DRY_RUN_TOOLS`, line
   111), so it can be used as the HIGH-risk test tool without needing to
   override `approval_dry_run_tools` in `_make_cfg(...)` — the default
   `_make_cfg()` fixture already includes it.
2. `ToolCallResult` is already imported in this file (used by the
   existing dry-run tests at lines 358-363) — no new import needed for
   the `is_error=True` case.
3. `audit_approval` writes to `ctx.services_required.audit_logger` as a
   JSON string (existing pattern seen in
   `tests/test_tool_approval_repos.py`'s
   `test_fail_closed_empty_allowlist_denies_write`, which asserts
   `"denied_repo_allowlist" in logged`) — the new HIGH-risk-denied test
   follows the same pattern, asserting `"denied_dry_run_error" in
   logged`.
4. When denied at the dry-run-error branch, `check_approval()` returns
   `False` **before** reaching `_prompt_user_approval()` — the test
   must confirm no `asyncio.to_thread`/`input` call happens, by not
   patching `asyncio.to_thread` at all (if the implementation is wrong
   and falls through to the prompt, the test will hang or raise, making
   the regression visible) or by patching it with a mock that asserts
   `assert_not_awaited()`.

## Implementation

### Target file

`tests/test_tool_approval_preflight.py` (existing)

### Procedure

1. Add to `TestCheckApprovalDryRun` (after
   `test_dry_run_exception_does_not_abort_approval`, before
   `test_dry_run_for_create_directory`):
   ```python
   @pytest.mark.asyncio
   async def test_high_risk_dry_run_error_denies_without_prompt(self) -> None:
       """Explicit dry-run error on a HIGH-risk tool denies immediately, no prompt."""
       cfg = _make_cfg()
       ctx = _make_ctx(cfg=cfg)
       audit = MagicMock()
       ctx.services_required.audit_logger = audit
       ctx.services_required.tools = MagicMock()
       ctx.services_required.tools.execute = AsyncMock(
           return_value=ToolCallResult(
               output="permission denied",
               is_error=True,
               request_id="",
               server_key="",
           )
       )
       prompt_mock = AsyncMock()
       with patch("asyncio.to_thread", new=prompt_mock):
           result = await check_approval(
               ctx, "delete_file", {"path": "/tmp/f.txt"}
           )

       assert result is False
       prompt_mock.assert_not_awaited()
       logged = audit.info.call_args[0][0]
       assert "denied_dry_run_error" in logged

   @pytest.mark.asyncio
   async def test_high_risk_dry_run_exception_still_falls_back(self) -> None:
       """dry_run raising RuntimeError for a HIGH-risk tool still falls back to prompt."""
       cfg = _make_cfg()
       ctx = _make_ctx(cfg=cfg)
       ctx.services_required.tools = MagicMock()
       ctx.services_required.tools.execute = AsyncMock(
           side_effect=RuntimeError("mcp connection error")
       )

       with (
           patch("builtins.print"),
           patch("asyncio.to_thread", new=AsyncMock(return_value="yes")),
       ):
           result = await check_approval(
               ctx, "delete_file", {"path": "/tmp/f.txt"}
           )

       assert result is True  # unchanged fallback-to-preview behavior
   ```
2. Confirm `_make_ctx`'s default `ctx.services_required.audit_logger =
   None` (line 103 of this file) is overridden with a `MagicMock()` in
   the first new test, matching the existing pattern used in
   `tests/test_tool_approval_repos.py`.

### Method

Two additive tests inside the existing `TestCheckApprovalDryRun` class;
reuses the `_make_cfg`/`_make_ctx` fixtures and `ToolCallResult` already
imported in this file. No changes to any other test class.

### Details

- `test_high_risk_dry_run_error_denies_without_prompt` asserts three
  things: the boolean result, that the prompt mechanism was never
  invoked (`prompt_mock.assert_not_awaited()`), and the specific audit
  decision string `denied_dry_run_error` — matching the audit-decision
  naming convention established in the plan's Design §3.
- `test_high_risk_dry_run_exception_still_falls_back` mirrors the
  existing `test_dry_run_exception_does_not_abort_approval` test exactly
  but swaps `write_file` (MEDIUM) for `delete_file` (HIGH), to close the
  coverage gap the plan's Risk #3 identifies (the fallback path must
  remain HIGH-risk-safe, not just MEDIUM-risk-safe).
- Do not remove or alter
  `test_dry_run_exception_does_not_abort_approval` — it remains valid
  and continues to cover the MEDIUM-risk case.

## Validation plan

```bash
uv run ruff format tests/test_tool_approval_preflight.py
uv run ruff check tests/test_tool_approval_preflight.py
uv run mypy tests/test_tool_approval_preflight.py
uv run pytest tests/test_tool_approval_preflight.py -v
uv run pytest tests/test_tool_approval_preflight.py::TestCheckApprovalDryRun -v
```

Expected: 0 lint errors, no new mypy errors; both new tests pass, all
pre-existing tests in `TestCheckApprovalDryRun` and the rest of the file
continue to pass unchanged.

## Note on prior implementation document with the same target file name

`implementations/done/20260622-130400_test_tool_approval_preflight.md`
exists for the same target file
(`tests/test_tool_approval_preflight.py`) but addresses a **different,
unrelated change**: adding tests for `check_approval()`'s user-input
parsing edge cases (empty input, whitespace handling) and
`audit_logger`-is-`None`/audit-logger-raises boundary conditions in
`TestCheckApproval`. It does not touch `TestCheckApprovalDryRun`, dry-run
error handling, or risk-level-conditioned blocking at all. It was not
treated as a match; this document was created fresh, targeting a
different test class within the same file.
