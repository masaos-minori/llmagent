# Denial-audit unit tests

## Goal

Add unit tests to `tests/agent/test_tool_audit.py` proving `audit_tool_exec` audits a
`error_type="denied"` call with empty ids, keeps the no-op for other empty-identity calls, and
pins the default `source` field (Plan REQ-001 / AC-1, REQ-002 / AC-2).

## Scope

- New class `TestDeniedResultAudit` (new) appended after the classes added earlier in the batch
  (maskargs001's `TestAuditPreviewScrub` (new), assertaudit001's `TestWorkflowIdSkipWarn` (new) — append-only
  order, adjudication D3).
- Reuse `_make_ctx` (:63) and `_make_cfg`; no existing test edited.

## Assumptions

- Verified 20261102: the early return at `tool_audit.py:173` drops denied calls
  (`request_id=""`, `source=""` from `_denied_result`); the event's `source` field defaults to
  `"agent"` when the argument is empty (:192).
- Red-first (Plan Phase 1): the denial test fails (no record) until row 01 lands; the no-op test
  passes before and after (it pins behavior that must NOT change).

## Design decisions

- Assert the full field contract of the one written record (`event == "tool_exec"`,
  `error_type == "denied"`, `is_error` true, `mcp_request_id` empty, `source == "agent"`) by
  parsing the logged JSON — mirrors AC-1 instead of substring checks.

## Alternatives considered

- Parametrize denial/no-op into `TestAuditToolExec` — rejected: keeps this Plan's new contract
  class separable in a file already shared by three plans this batch.

## Implementation
### Target file
`tests/agent/test_tool_audit.py`

### Procedure
Append `TestDeniedResultAudit` (new) at the end of the module.

### Method
- `test_denied_result_is_audited` (new): ctx with `audit_logger = MagicMock()`; call
  `audit_tool_exec(ctx, "write_file", {"path": "/tmp/x"}, True, "", "denied", source="")`;
  assert `info` called once; parse `json.loads(call_args[0][0])`; assert the AC-1 field values.
- `test_empty_identity_non_denied_still_skipped` (new), parametrized `error_type` `""` and
  `"tool"`: same empty ids → `info.assert_not_called()` (REQ-002).
- `test_denied_record_keeps_full_field_set` (new): assert no new keys appear in the record — the
  parsed JSON keys equal those of a non-denied `tool_exec` record built the same way (no schema
  change, REQ-001).

### Details
- `import json` if not already present at module level; follow existing ctx-argument style.

## Compatibility considerations

- All pre-existing tests in this module and `tests/agent/test_tool_approval_preflight.py` pass
  unchanged (AC-2).

## Security considerations

- N/A: tests only; they pin the audit completeness contract.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py` — denial test red before row 01 lands.
- `uv run ruff format`, `uv run ruff check` on the touched file; coverage via
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- Denial call writes exactly one matching record; non-denied empty-identity calls write nothing;
  field set unchanged; all pre-existing tests green.

## Out of Scope

- Gateway end-to-end test (row 03); the `workflow_id` skip test (row 03, gated on assertaudit001).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestDeniedResultAudit` (new) tests (denial case red before row 01 lands) | Pending | — | — | Plan Phase 1 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (denied call audited), REQ-002 (no-op preserved)
- **Source issue**: issues/20261003-180330_toolaudit001_audit-drops-denied-gateway-tool-calls.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141718_toolaudit001_audit-drops-denied-gateway-tool-calls.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132702
- **Related target files**: tests/agent/test_tool_audit.py
