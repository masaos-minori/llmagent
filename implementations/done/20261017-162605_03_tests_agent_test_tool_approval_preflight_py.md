# Implementation Procedure — `tests/agent/test_tool_approval_preflight.py`

## Goal

Add regression coverage for enabling dry-run previews for GitHub mutation tools
(`REQ-004`, `REQ-005`).

## Scope

Modify only `tests/agent/test_tool_approval_preflight.py`. Under the existing
`TestCheckApprovalDryRun` class (lines 447–568, which already exercises the dry-run flow
with a mocked `tools.execute`), append:
- a GitHub dry-run test asserting `check_approval(ctx, "github_create_issue", {...})` awaits
  `tools.execute` with `{**args, "dry_run": True}` and appends dry-run text to the preview
  (REQ-005);
- a read-only GitHub tool test asserting `github_get_issue` does not trigger dry-run
  (REQ-004).
Depends on the code changes in `scripts/agent/tool_approval.py` (row 1) and
`scripts/agent/constants.py` (row 2).

## Assumptions

- The existing `TestCheckApprovalDryRun` harness mocks `ctx.services_required.tools.execute`
  as an `AsyncMock` and drives `check_approval(...)`. See existing
  `test_dry_run_result_appended_to_preview` (line 449) and the non-capable-tool assertion
  at line 511 (`execute.assert_not_awaited()`).
- Rows 1–2 make GitHub mutation tools pass both dry-run gates, so
  `check_approval(ctx, "github_create_issue", ...)` now reaches `tools.execute(dry_run=True)`.

## Design decisions

- Mirror the existing `test_dry_run_result_appended_to_preview` setup (same mock wiring,
  same `check_approval` call shape) but use a GitHub tool name and args.
- Assert `ctx.services_required.tools.execute.assert_awaited_once()` with
  `{**args, "dry_run": True}`, and that the returned preview contains the dry-run text.
- For the read-only case, assert `execute.assert_not_awaited()` (or that the tool is
  auto-approved and never reaches the gate), mirroring the existing non-capable-tool test.

## Alternatives considered

- Asserting exact call args vs. call presence: assert call presence plus the `dry_run=True`
  kwarg (the essential property); keep preview-content assertions lightweight to avoid
  brittleness.

## Implementation

### Target file

`tests/agent/test_tool_approval_preflight.py`

### Procedure

1. In `TestCheckApprovalDryRun`, add `test_github_tool_triggers_dry_run` (new):
   - Wire `ctx.services_required.tools.execute = AsyncMock(...)` as in the existing test.
   - Call `await check_approval(ctx, "github_create_issue", {...})`.
   - Assert `ctx.services_required.tools.execute.assert_awaited_once()` with
     `{**args, "dry_run": True}`.
   - Assert the returned preview includes the dry-run output (not static text only)
     (REQ-001, REQ-005).
2. Add `test_readonly_github_tool_does_not_trigger_dry_run` (new):
   - Use a read-only GitHub tool (e.g. `github_get_issue`).
   - Assert `ctx.services_required.tools.execute.assert_not_awaited()` (REQ-004).
3. Confirm existing `test_dry_run_result_appended_to_preview` /
   `test_dry_run_for_create_directory` still pass (REQ-003).

### Method

Append test methods to `TestCheckApprovalDryRun`; reuse the existing mock wiring and
fixtures.

### Details

- Match the arg dict shape used by neighboring tests so the mock and call path are
  representative.
- Ensure the read-only tool genuinely lacks a `dry_run` field (it does; confirmed via
  `github_models_*.py`).

## Compatibility considerations

N/A: test-only change.

## Security considerations

The tests encode a safety property (GitHub writes still gated by approval; dry-run is
preview-only). Keep args free of real secrets.

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run the preflight tests; all pass.
- Command: `uv run pytest tests/agent/test_tool_approval_preflight.py -q`.

## Completion criteria

The GitHub dry-run test asserts `tools.execute` awaited with `dry_run=True` and the preview
includes dry-run output; the read-only GitHub tool does not trigger dry-run; existing
default-tool regressions pass.

## Out of scope

`scripts/agent/tool_approval.py` (separate row), `scripts/agent/constants.py` (separate
row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_tool_approval_preflight.py | Completed | 20261018-120816 | 20261018-120816 | Two tests added under TestCheckApprovalDryRun; aligns with rows 1–2 (tool_approval.py/constants.py). |
| 2 | Add or update tests per Validation plan | Completed | 20261018-120816 | 20261018-120816 | test_github_tool_triggers_dry_run (REQ-005) and test_readonly_github_tool_does_not_trigger_dry_run (REQ-004). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261018-120816 | 20261018-120816 | ruff/mypy/bandit-high/lint-imports clean; 9109 passed, 0 failed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261018-120816 | 20261018-120816 | N/A: test-only change. |

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
- **Requirement ID**: `REQ-004` (read-only GitHub tool no dry-run), `REQ-005` (GitHub
  dry-run execution regression)
- **Source issue**: `issues/done/20261017-123420_dryrun01_enable-approval-dry-run-previews-for-github-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-152556_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162605
- **Related target files**: `tests/agent/test_tool_approval_preflight.py`
