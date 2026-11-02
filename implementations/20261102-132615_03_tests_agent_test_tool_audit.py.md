# Audit-writer scrub tests

## Goal

Add tests to `tests/agent/test_tool_audit.py` proving both audit writers persist scrubbed
`args_preview` — including inside the oversized `truncated` envelope — for a secret embedded under
an unlisted key (Plan REQ-003 / AC-3).

## Scope

- New class `TestAuditPreviewScrub` (new) appended after `TestAuditToolExecSnapshotDedup`.
- Existing classes (`TestLogApprovalDecision`, `TestAuditApprovalInv11`, `TestAuditToolExec`,
  `TestArgsPreviewBound`, `TestWriteRoundExec`, `TestAuditToolExecSnapshotDedup`) untouched: they
  are the AC-6 regression, including the `truncated`-envelope shape test.
- Reuse the module's `_make_ctx` helper (:63) and its `AgentConfig` mock style.

## Assumptions

- Verified 20261102: `audit_tool_exec` calls `mask_args` then `_bounded_preview`
  (`tool_audit.py:28-37`); `audit_approval` masks the same way (:60); oversized payloads become
  `{"preview": serialized[:1500], "truncated": True}`; `_make_ctx` returns a `MagicMock` with
  `cfg.tool.masked_fields` controllable.
- Red-first (Plan Phase 1): these fail until row 01 lands.
- Batch note: assertaudit001 also appends a class to this file later in the batch; this class is
  added first and nothing here is edited by that plan (recorded overlap adjudication D3,
  append-only).

## Design decisions

- Parametrize over both writers with the same secret-carrying args dict — one source of truth for
  "both sinks scrub" (REQ-003 names both explicitly).
- For the envelope case assert on the serialized `preview` string field: the truncation slice must
  still be free of the secret even when the secret lands inside the first 1500 chars.

## Alternatives considered

- Extend `TestAuditToolExec`'s cases — rejected: keeps the AC-3 new-contract class separable from
  the pre-existing writer behavior pins (AC-6).

## Implementation
### Target file
`tests/agent/test_tool_audit.py`

### Procedure
Append `TestAuditPreviewScrub` (new) at the end of the module.

### Method
- `test_writers_scrub_free_form_secret` (new), parametrized over `audit_approval` and
  `audit_tool_exec`: ctx with `masked_fields=[]` and a `MagicMock` audit logger; args
  `{"command": "curl -H 'Authorization: Bearer abc1234567890' https://x"}` (a secret under an
  unlisted key); call the writer; capture the logged JSON (`audit_logger.info.call_args[0][0]`)
  and assert the secret substring is absent while `tool_exec`/`tool_approval` markers remain.
- `test_scrubbed_inside_truncated_envelope` (new): args whose serialized masked form exceeds
  `AUDIT_ARGS_PREVIEW_MAX_CHARS` (pad with filler dict entries) and still contain
  `token=abc12345678`; assert the logged preview contains `"truncated"` and contains no `abc12345678`.
- `test_masked_fields_still_star` (new): `masked_fields=["content"]` round-trip keeps `"***"`
  exactly through both writers (REQ-002 at the sink level).

### Details
- Follow the existing call style of `TestAuditToolExec` (`ctx.services_required.audit_logger =
  MagicMock()` then `audit_logger.info.assert_called_once()`).

## Compatibility considerations

- `tests/agent/test_audit_log_format.py` must keep passing unchanged (reference file).
- No interaction with assertaudit001's later additions to this file beyond append order.

## Security considerations

- N/A: tests only; they pin the persisted-row contract.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py` — red for the new class until row 01 lands.
- `uv run pytest tests/agent/test_audit_log_format.py` unchanged.
- `uv run ruff format`, `uv run ruff check` on the touched file; coverage via
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- Both writers' logged previews contain no secret substring for the parametrized args, plain or
  truncated; all pre-existing tests in the module pass unchanged.

## Out of Scope

- `mask_args` unit behavior (row 02); runner/REPL sinks (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestAuditPreviewScrub` (new) tests (red before row 01 lands) | Pending | — | — | Plan Phase 1 |
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
- **Requirement ID**: REQ-003 (persisted args_preview scrubbed, incl. truncated envelope)
- **Source issue**: issues/20261003-180335_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140856_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132615
- **Related target files**: tests/agent/test_tool_audit.py
