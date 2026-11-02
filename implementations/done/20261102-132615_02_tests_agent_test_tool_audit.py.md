# Skip-and-warn tests and the no-assert guard

## Goal

Add tests to `tests/agent/test_tool_audit.py` pinning the skip-and-warn behavior of the three
writers for `workflow_id` `None` and `""`, the preserved guard order, and a source-level guard that
`tool_audit.py` contains no `assert` statement (Plan REQ-003 / AC-1..AC-3).

## Scope

- New class `TestWorkflowIdSkipWarn` (new) appended after `TestAuditToolExecSnapshotDedup`.
- Reuse the module's `_make_ctx` helper (:63, sets `workflow_id = "wf-test-id"` — override the
  attribute per test) and `_make_cfg`.
- All pre-existing classes untouched: they are the AC-2 regression (non-empty `workflow_id`
  behavior).
- Batch note: maskargs001 earlier in the batch appends `TestAuditPreviewScrub` (new) to this same
  file; append order is that class first, then this one (recorded adjudication D3, append-only).

## Assumptions

- Verified 20261102: `_make_ctx` is a module-level function building a `MagicMock` ctx with
  `services_required.audit_logger = None` by default; caplog is used elsewhere in the module's
  style via the `caplog` fixture.
- Red-first (Plan Phase 1, AC-3): the skip tests fail with `AssertionError` against current code;
  the no-`ast.Assert` test fails until row 01 lands.
- Warning assertion: caplog at `logging.WARNING` on logger `agent.tool_audit`, exactly one record,
  message contains the writer name and the tool name, and does NOT contain argument values.

## Design decisions

- Parametrize (writer × missing-id) as one case list: `audit_approval` (tool `"read_text_file"`),
  `log_approval_decision` (an `ApprovalOutcome` with `tool_name="write_file"`), `audit_tool_exec`
  (tool `"read_text_file"`, non-empty `mcp_request_id` so the workflow check is reached) — each
  with `workflow_id` `None` and `""` (REQ-003 lists all six combinations).
- Order pin (REQ-002): `audit_tool_exec` called with empty `mcp_request_id` AND empty `source`
  and a missing `workflow_id` returns silently with NO warning — the early return precedes the
  workflow check; likewise a ctx with `audit_logger = None` logs no warning even with a missing id.

## Alternatives considered

- Per-writer test classes — rejected: one parametrized list keeps the six combinations uniform and
  the order-pin cases adjacent.

## Implementation
### Target file
`tests/agent/test_tool_audit.py`

### Procedure
Append `TestWorkflowIdSkipWarn` (new) at the end of the module.

### Method
- `test_missing_workflow_id_skips_with_warning` (new), parametrized over the six (writer, id)
  combinations: `ctx = _make_ctx()`; `ctx.services_required.audit_logger = MagicMock()`; set
  `ctx.workflow.workflow_id` to the missing value; `caplog.at_level(logging.WARNING,
  logger="agent.tool_audit")`; call the writer; assert no exception,
  `audit_logger.info.assert_not_called()`, and exactly one warning record containing both the
  writer name and the tool name.
- `test_no_warning_without_audit_logger` (new): missing id + `audit_logger = None` → no log record
  at WARNING level on `agent.tool_audit` (REQ-002 precedence).
- `test_early_return_precedes_workflow_check` (new): `audit_tool_exec` with empty `mcp_request_id`
  and empty `source` and missing id → no event, no warning (guard order, REQ-002).
- `test_no_assert_statements_in_source` (new): parse `Path("scripts/agent/tool_audit.py")` with
  `ast.parse`, walk for `ast.Assert`, assert none (AC-1 source pin; mirrors the bandit B101 claim).

### Details
- Import `logging`, `ast`, `pathlib.Path` following the module's existing import style; build
  `ApprovalOutcome(...)` from `agent.tool_models` with `risk_level`/`decision` values already used
  in this module's `TestLogApprovalDecision` cases.

## Compatibility considerations

- AC-2 regression modules (`test_audit_log_format.py`, `test_tool_approval_preflight.py`,
  `test_tool_runner.py`) run in the validation plan but are not edited here.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py` — new class red before row 01 lands (AC-3), green
  after.
- `uv run ruff format`, `uv run ruff check` on the touched file; coverage via
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- Six skip cases pass (no event, no exception, exactly one warning naming writer and tool); order
  and no-logger cases pass; the no-assert source test passes; all pre-existing tests unchanged.

## Out of Scope

- Implementation (row 01); docs (rows 03-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestWorkflowIdSkipWarn` (new) tests (red before row 01 lands) | Completed | 20261102-175110 | 20261102-180004 | Plan Phase 1 red-phase evidence: 6 skip cases + no-assert test fail (AssertionError), order pins green (Plan Phase 1, AC-3); ruff clean landed in batch 20261102-132615; red-first verified, all targets green |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261102-175530 | 20261102-180004 | green gate deferred to assertaudit001 row 01 implementation landing full suite 11348 passed/8 skipped; diff-cover 100%; ruff/mypy/bandit/lint-imports/check_module_size green; docs checkers green |

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
- **Requirement ID**: REQ-003 (unit tests for the three writers and the no-assert guard), REQ-002 (order pins)
- **Source issue**: issues/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141314_assertaudit001_audit-assert-risks-post-execution-crash.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132615
- **Related target files**: tests/agent/test_tool_audit.py