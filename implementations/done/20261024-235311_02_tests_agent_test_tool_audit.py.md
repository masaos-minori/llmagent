## Goal
- Add regression tests that pin the `args_preview` cap behavior for both audit writers (`REQ-005`: multi-KB value, exactly-at-cap, cap+1, mask-plus-truncation).

## Scope
- Add test cases to `tests/agent/test_tool_audit.py`; existing tests stay unchanged.

## Assumptions
- Existing helpers: `_make_cfg()`, `_make_ctx()` (ctx is a `MagicMock` with `services_required.audit_logger = None` by default) and the `TestAuditToolExec` pattern `ctx.services_required.audit_logger = MagicMock()` then `audit_logger.info.call_args[0][0]` (read 2026-10-24). `audit_approval` is already imported in this file.
- `audit_approval()` requires workflow context (`ctx.workflow.workflow_id`), which `_make_ctx()` provides.
- The constant `AUDIT_ARGS_PREVIEW_MAX_CHARS` comes from row `01` (`scripts/agent/tool_audit.py`); these tests import it and therefore fail at import until row `01` lands, which is the intended Plan Phase 1 "failing first" state.
- Boundary construction: the serialized length of the container, not of one value, is measured, so build the at-cap case by sizing one string value from `len(_json_dumps(base))`.

## Design decisions
- Parse the logged JSON line with the `json` module already imported and assert on `args_preview` directly.
- One parametrized boundary test over both writers avoids duplicating the three cases.

## Alternatives considered
N/A: single test-file addition following the existing class-per-function layout.

## Implementation
### Target file
`tests/agent/test_tool_audit.py`

### Procedure
1. Add the test class `TestArgsPreviewBound` (new) after `TestAuditToolExec`; import `AUDIT_ARGS_PREVIEW_MAX_CHARS` from `agent.tool_audit` and `dumps` from `shared.json_utils` in the existing import style.
2. Add a small helper that runs either writer (`audit_approval` or `audit_tool_exec`) against a ctx with a `MagicMock` audit logger and returns the parsed `args_preview`.
3. Cases, each for both writers: (a) multi-KB value returns the envelope with `len(preview) <= AUDIT_ARGS_PREVIEW_MAX_CHARS` and `truncated is True` and no original top-level key; (b) serialized length exactly at the cap is unchanged with no `truncated` key; (c) cap+1 returns the envelope.
4. Add the mask-plus-truncation case: configure `masked_fields` with a key, send a large container containing that key, assert `"***"` is in the preview prefix, the raw secret is absent, and `truncated is True`.

### Method
- Use deterministic filler (`"x" * n`); derive `n` from the measured base length rather than hard-coding the cap-dependent number.

### Details
- Annotate every test `-> None` as the file does; keep comments in English.

## Compatibility considerations
N/A: test-only addition.

## Security considerations
N/A: tests use dummy secret strings only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before row `01`: `uv run pytest tests/agent/test_tool_audit.py -q` fails on import of the new constant.
- After row `01`: the file passes, with `tests/agent/test_tool_approval_preflight.py` and `tests/agent/test_audit_log_format.py` unchanged and green.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/agent/test_tool_audit.py` on the file.

## Completion criteria
- The new class covers envelope, at-cap, cap+1, and mask-plus-truncation for both writers and passes with row `01`; no existing test changed.

## Out of Scope
- Tests of masking behavior itself, and `tool_approval.py` preview behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestArgsPreviewBound` (new) with the helper and cases | Completed | — | 20261025-002449 |  |
| 2 | Run the tests before and after row `01` | Completed | — | 20261025-002449 |  |
| 3 | Run ruff and mypy on the file | Completed | — | 20261025-002449 |  |

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
- **Requirement ID**: `REQ-005` (regression tests for the cap and boundary cases)
- **Source issue**: `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-221315_args-preview-is-written-to-the-audit-log-unbounded.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235311
- **Related target files**: `tests/agent/test_tool_audit.py`