# Gateway denial end-to-end audit tests

## Goal

Add gateway-driven regression tests to `tests/agent/test_repository_gateway.py`: a write denied by
`check_preflight()` inside a real `RepositoryGateway`, executed through `execute_one_tool_call()`,
produces exactly one `tool_exec` audit record with `error_type="denied"` (Plan REQ-003 / AC-3),
plus the no-`workflow_id` companion test gated on assertaudit001 (Plan REQ-004 / AC-4).

## Scope

- New class `TestDenialAuditEndToEnd` (new) appended after `TestWritePolicy`.
- Existing tests untouched — `test_write_tool_blocked_by_policy` (the pre-existing denial-result
  behavior) is the regression that `_denied_result()` and the `gateway.policy_denied` log line stay
  unchanged (REQ-003).
- Extend the module's `_make_ctx` (:25-35) per test (never mutate the shared helper):
  `workflow_id=None` today and `services_required` has no `audit_logger` — the new tests set
  `ctx.workflow.workflow_id = "wf-test"`, `ctx.services_required.audit_logger = MagicMock()`,
  `ctx.session = SimpleNamespace(session_id=None)`, and pin `ctx.cfg.tool.masked_fields = []`,
  `ctx.cfg.approval.approval_resource_keys = {}` on the `MagicMock` cfg.

## Assumptions

- Verified 20261102: the gateway denial path is `check_preflight` raising `PolicyViolationError`
  → `logger.warning("gateway.policy_denied tool=%r reason=%s", ...)` (`repository_gateway.py:104`)
  → `_denied_result` with `error_type="denied"`, `request_id=""`, `source` unset; the runner's
  `audit_tool_exec` call site (`tool_runner.py:281-290`) passes `result.error_type` and
  `source=result.source` — this is the wiring the test must traverse end-to-end.
- Red-first (Plan Phase 1): the denial-audit test sees zero records until row 01 lands.
- REQ-004 test is written only after assertaudit001's procedure document has been implemented
  (batch step 4 before step 5); before that the old assert would raise `AssertionError`.

## Design decisions

- Exercise the real pipeline (`execute_one_tool_call` with a real `RepositoryGateway` on
  `ctx.services_required.gateway`) rather than calling `audit_tool_exec` directly — REQ-003's claim
  is about the gateway→runner wiring, and it pins the `"denied"` literal agreement between
  `_denied_result` and row 01's constant (Plan Design).
- Assert `executor.execute` is never awaited (denial semantics preserved) and exactly one
  `audit_logger.info` call whose parsed JSON has `error_type == "denied"`.

## Alternatives considered

- Assert only on the audit record — rejected: REQ-003 also requires the unchanged
  `gateway.policy_denied` log line, so caplog on logger `agent.repository_gateway` is part of the
  same test.

## Implementation
### Target file
`tests/agent/test_repository_gateway.py`

### Procedure
Append `TestDenialAuditEndToEnd` (new) at the end of the module.

### Method
- `test_denied_write_produces_one_tool_exec_record` (new): build ctx as in Scope; real
  `RepositoryGateway` (module's `_make_gateway` helper) wired to `ctx.services_required.gateway`
  with an `AsyncMock` executor; classify patched to `OperationType.WRITE` and
  `check_preflight` patched to raise `PolicyViolationError("deny", "blocked")` (the existing
  `TestWritePolicy` pattern); run `execute_one_tool_call` (import from `agent.tool_runner`) with a
  `PreparedToolCall` for `write_file`; then assert: `executor.execute.await_count == 0`;
  `audit_logger.info.assert_called_once()` with parsed record `event == "tool_exec"`,
  `error_type == "denied"`, `is_error` true; exactly one caplog WARNING on logger
  `agent.repository_gateway` containing `gateway.policy_denied`.
- `test_denied_without_workflow_id_skips_quietly` (new): same setup with
  `ctx.workflow.workflow_id = None`; assert no exception, `audit_logger.info.assert_not_called()`.
  Add only after assertaudit001 is implemented (REQ-004 gate).

### Details
- `ctx.turn` already carries `current_turn_id="turn-1"`; `_idempotency_key` needs the ctx turn/
  session fields the helper already provides plus the added `session` namespace.
- Import `execute_one_tool_call` and `PreparedToolCall` following the module's import style;
  `json` for parsing the logged record.

## Compatibility considerations

- `tests/agent/test_tool_runner.py` runs unchanged in the validation plan (shared harness).
- `_make_ctx` stays `workflow_id=None` for pre-existing tests — mutations are per-test only.

## Security considerations

- N/A: tests only; they pin audit completeness for policy denials.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_repository_gateway.py tests/agent/test_tool_runner.py` — denial
  test red before row 01 lands, then green; `test_tool_runner.py` unchanged.
- `uv run ruff format`, `uv run ruff check` on the touched file; coverage via
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- Exactly one `tool_exec` denial record for the gateway-denied write; executor not awaited; the
  `gateway.policy_denied` warning still logged once; the REQ-004 test (once gated-in) shows no
  event and no exception; all pre-existing tests pass unchanged.

## Out of Scope

- Unit-level audit behavior (row 02); `_denied_result` itself (unchanged by the Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestDenialAuditEndToEnd` (new) denial test (red before row 01 lands) | Pending | — | — | Plan Phase 1 |
| 2 | Add the no-`workflow_id` test | Pending | — | — | Gated: only after assertaudit001 is implemented (REQ-004) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (gateway denial audited end-to-end), REQ-004 (denial without workflow_id, gated on assertaudit001)
- **Source issue**: issues/20261003-180330_toolaudit001_audit-drops-denied-gateway-tool-calls.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141718_toolaudit001_audit-drops-denied-gateway-tool-calls.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132702
- **Related target files**: tests/agent/test_repository_gateway.py
