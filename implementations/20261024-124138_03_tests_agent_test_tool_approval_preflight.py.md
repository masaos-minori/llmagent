## Goal

Add the audit-path test (`T-2`) that a sensitive value nested inside a tool-argument container does
not appear in the serialized `tool_approval` audit payload (`REQ-002`, `REQ-004`, `AC-2`).

## Scope

- `tests/agent/test_tool_approval_preflight.py`: one new test inside the existing `TestAuditApproval`
  class (`:394-430`).
- No change to `_make_cfg()` (`:44`), `_make_ctx()` (`:79`), the `_audit_approval` import (`:23`), or
  any existing test in the class.

## Assumptions

- The audit sink stays a `MagicMock` assigned to `ctx.services_required.audit_logger`, and the payload
  stays one JSON line produced by `audit_logger.info(_json_dumps(dataclasses.asdict(evt)))`
  (`scripts/agent/tool_audit.py:63`).
- `audit_approval()` keeps calling `mask_args(args, cfg.security.masked_fields)` at
  `scripts/agent/tool_audit.py:46` and writing the result as `args_preview` at `:58`.

### Procedure-local findings

- The Plan cites the existing audit masking test at `:384-397`. Measured: `TestAuditApproval` starts at
  `:394`, its local `_make_ctx` helper is at `:412`, and `test_masked_fields_applied_to_args` is at
  `:417-430`. The procedures use the measured anchors; the correction is recorded in
  `plans/20261023-072425_plan.md`.
- The Plan's `T-2` sample uses only a dict-nested value. The test here also nests through a list,
  because `REQ-002` names `edits`-shaped args explicitly.

## Design decisions

- Assert on the serialized payload string, not on the in-memory dict. `AC-2` is a statement about what
  lands in the audit log, and the serialization is where a nested leak would survive.
- Assert both halves of `AC-2`: the sensitive literal is absent, and the masked path is present as
  `"***"`. Asserting only absence would also pass if the key were dropped, which `mask_args` must not
  do.
- Reuse the existing `_make_cfg(masked_fields=[...])` / `_make_ctx(cfg=cfg)` / `MagicMock` sink pattern
  from `test_masked_fields_applied_to_args` (`:417-430`) instead of a new fixture.

## Alternatives considered

- Asserting on `ctx.services_required.audit_logger` call kwargs after patching
  `scripts/agent/tool_audit.py`'s serialization: rejected. It couples the test to a private helper and
  would not detect a leak introduced by serialization itself.
- Adding the case to `tests/agent/test_tool_audit.py`: rejected. The Plan row assigns this coverage to
  the preflight file's existing audit/approval fixture area, and `test_tool_audit.py` is a read-only
  regression anchor for this Plan (`Reference Files`).
- Nested value only in a dict: rejected as sufficient. The verified defect is nesting through a list as
  well, so the case covers a dict inside a list inside the argument dict.

## Implementation

### Target file

`tests/agent/test_tool_approval_preflight.py` — append inside `TestAuditApproval` after
`test_masked_fields_applied_to_args` (`:417-430`).

### Procedure

1. Build `cfg = _make_cfg(masked_fields=["secret"])` and `ctx = _make_ctx(cfg=cfg)`.
2. Assign `ctx.services_required.audit_logger = MagicMock()`.
3. Call `_audit_approval(ctx, "write_file", "medium", args, "approved")` with
   `args = {"path": "/tmp/f", "payload": {"secret": "s3cr3t"}, "edits": [{"secret": "nested-list-secret"}]}`.
4. Read the payload from `audit.info.call_args[0][0]` (the same access the existing test uses at
   `:429-430`).
5. Assert neither secret literal appears in the payload, and that the payload contains `"***"`.

### Method

- The assertion set mirrors `AC-2`: `s3cr3t` and `nested-list-secret` absent, `"***"` present, and
  `args_preview` still contains the non-sensitive keys (`path`, `payload`, `edits`) so the shape is
  preserved.

### Details

- Name the test `test_masked_fields_applied_to_nested_args` (new).
- Keep the argument shape tool-real: `path` plus a nested container, matching the `write_file` /
  `edits` schemas in `scripts/mcp_servers/file/write_tools.py:31` and `:73`.
- Do not assert a specific JSON key order.

## Compatibility considerations

- `test_masked_fields_applied_to_args` (`:417-430`) must pass with zero edits (`AC-3`).
- The event shape is unchanged: `dataclasses.asdict(evt)` remains one JSON line, so
  `tests/agent/test_tool_audit.py` keeps passing unmodified.
- `_make_cfg()`'s default `masked_fields` is `[]` (`:53`); the new test passes the list explicitly and
  does not change the helper's default.
- Tests must not touch `/opt/llm` (`tests/conftest.py` isolation guard).

## Security considerations

- This is the regression guard for the leak the Plan fixes: before the change, a value nested under a
  configured key reaches the audit log in clear text.
- Payload assertions use synthetic literals so the test file itself introduces no real secret.

## Rollback considerations

- Deleting the appended test reverts this row; no helper or fixture is shared with other rows.

## Validation plan

- `uv run pytest tests/agent/test_tool_approval_preflight.py -v` — the new test plus all pre-existing
  tests in the file pass.
- Targeted single test: `uv run pytest tests/agent/test_tool_approval_preflight.py -k
  test_masked_fields_applied_to_nested_args -v`.
- `uv run pytest tests/agent -q` — `test_tool_audit.py`, `test_config_builders.py`, and
  `test_agent_integration.py` keep passing (`AC-8`).
- Mutation intent (manual): removing the list branch or the dict recursion in `_mask_value` (new) must
  make this test fail.

## Completion criteria

- `AC-2`: the serialized `tool_approval` payload contains no nested sensitive value and shows `"***"` at
  the masked path.
- `AC-3`: `test_masked_fields_applied_to_args` passes with zero edits.
- `AC-8`: the agent suite reports no new failure.

## Out of Scope

- Unit-level nesting coverage (`T-1`), owned by
  `implementations/20261024-124138_02_tests_agent_test_tool_result_formatter.py.md`.
- Any change to `scripts/agent/tool_audit.py` or the `args_preview` field type; bounding that field's
  size is filed as
  `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`.
- The plan-mode blocked notice path (`scripts/agent/tool_approval.py:222`), whose behavior is unchanged.


## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append `test_masked_fields_applied_to_nested_args` (new) to `TestAuditApproval` | Pending | — | — | Reuses `_make_cfg` / `_make_ctx` / `MagicMock` |
| 2 | Run the targeted file and the agent suite | Pending | — | — | Requires `_01` to be implemented |
| 3 | Confirm the existing masking test is byte-identical | Pending | — | — | `AC-3` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | N/A: no work item was created by this row |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-004`
- **Source issue**: `issues/20261021-093421_tool005-masked-args-not-applied-to-previews-or-nesting.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-072425_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-124138
- **Related target files**: `tests/agent/test_tool_approval_preflight.py`
