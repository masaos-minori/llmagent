# Implementation Procedure: tests/agent/test_tool_approval_preflight.py

## Goal

Add a default-names audit case to `TestAuditApproval`: an approval audit event built with a
default-constructed `ToolConfig` masks the real payload key `content` on the audit path,
extending coverage from the `["secret"]` fixtures to the shipped default.

## Scope

In scope:
- One new test `test_default_masked_fields_applied_to_args` (new) and a new `ToolConfig`
  import in `tests/agent/test_tool_approval_preflight.py`.

Out of scope:
- Existing audit tests `test_masked_fields_applied_to_args` (`:417`) and
  `test_masked_fields_applied_to_nested_args` (`:432`) — untouched.
- Code defaults (procedures 01-02), config (procedure 03), pin (procedure 04), formatter
  tests (procedure 05), docs (procedure 07).

## Assumptions

- Assumption: `_make_cfg` hardcodes `masked_fields: []` in its builder defaults (verified at
  `:53`), so — as in procedure 05 — the default path is expressed by replacing the tool
  section with a directly constructed `ToolConfig()` on the test context rather than
  extending the helper (which would flip behavior of every existing consumer).
- Assumption: `_audit_approval` (imported alias of `agent.tool_audit.audit_approval`) masks
  via `ctx.cfg.tool.masked_fields` — verified at `scripts/agent/tool_audit.py:157`
  (`mask_args(args, ctx.cfg.tool.masked_fields)`); `ctx.cfg` is the real `AgentConfig`
  object attached to the `MagicMock` context (`_make_ctx` at `:79-89`), so assigning
  `ctx.cfg.tool = ToolConfig()` is a legal attribute swap on the dataclass.
- Assumption: the test fails (red) against the current `["file_content"]` default — expected
  per plan Phase 1 — and goes green once procedures 01-02 land.

## Design decisions

- Decision: use `write_file` with a top-level `content` argument — the canonical masked
  shape on the audit path; the nested `edits` shape is already covered behaviorally by
  procedure 05 and structurally by `test_masked_fields_applied_to_nested_args`.
- Decision: assert value-absence (`"s3cr3t" not in payload`) plus `***` presence and path
  visibility, mirroring the existing nested test's assertion pattern (`:448-452`) rather
  than re-parsing the JSON event.

## Alternatives considered

- Alternative: parameterize the two existing `["secret"]` tests over both fixture and
  default lists. Rejected: the frozen plan asks for a sibling case, not a refactor of
  passing tests; keeping the fixtures preserves the explicit-list regression coverage.
- Alternative: exercise the full `check_approval` flow instead of `_audit_approval`
  directly. Rejected: approval flow is covered by other classes in this file; the unit
  here is the audit masking path with default settings.

## Implementation

### Target file

`tests/agent/test_tool_approval_preflight.py`

### Procedure

1. Add `ToolConfig` to the existing import line `from agent.config_dataclasses import
   AgentConfig` (`:16`).
2. Insert the new test inside `TestAuditApproval` (class at `:394`), directly after
   `test_masked_fields_applied_to_nested_args` (ends around `:452`).

### Method

New import (edit of existing line at `:16`):

```python
from agent.config_dataclasses import AgentConfig, ToolConfig
```

New test, inserted after `test_masked_fields_applied_to_nested_args`:

```python
    def test_default_masked_fields_applied_to_args(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool = ToolConfig()  # default settings: shipped masked_fields
        audit = MagicMock()
        ctx.services_required.audit_logger = audit
        _audit_approval(
            ctx,
            "write_file",
            "medium",
            {"path": "/tmp/f", "content": "s3cr3t"},
            "approved",
        )
        payload: str = audit.info.call_args[0][0]
        assert "s3cr3t" not in payload
        assert "***" in payload
        assert "/tmp/f" in payload
```

No existing tests change.

### Details

- The `"/tmp/f" in payload` assertion documents the intended asymmetry: the path stays
  visible for review while the payload value is masked (REQ-001 semantics).
- Run in plan Phase 1, before procedures 01-02: red against the current default, green
  after.
- The approval preview path stays unmasked by design (see `agent_08_03` docs bullet,
  procedure 07); this test targets the audit sink only.

## Compatibility considerations

- No fixture or helper changes; all existing cases in `TestAuditApproval` keep passing
  (AC-6).
- Until procedures 01-02 land, this file has one failing test by design; the plan Phase 2
  gate command includes this file and must run after all of 01-04.

## Security considerations

- Regression guard for the audit sink specifically: proves the shipped default actually
  masks `content` in serialized audit payloads (REQ-001, REQ-005).
- Sentinel value only (`s3cr3t`); no real secrets.

## Rollback considerations

- Rollback: delete the new test and revert the import line; independent of the other
  procedures' reverts (this file's existing tests pass against either default).
- No data or fixture migration.

## Validation plan

1. Phase 1 (before code change): `uv run pytest tests/agent/test_tool_approval_preflight.py
   -q` shows the new test failing against the current default (expected red).
2. After procedures 01-02: same command is fully green.
3. Full gate: `uv run pytest tests/agent -q` and `uv run mypy scripts/ tests/ --strict`.

## Completion criteria

- `test_default_masked_fields_applied_to_args` (new) passes against the new default.
- Payload asserts hold: sentinel absent, `***` present, path visible.
- The two existing `["secret"]` audit tests still pass unchanged.

## Out of Scope

- Existing audit/approval tests in this file.
- Formatter default tests (procedure 05) and builder pin (procedure 04).
- Code and config changes (procedures 01-03).

## Execution Status

- [ ] Completed
- [ ] Partial — Blocked by: (state explicitly, including partial deploy state)

## Traceability

- Plan: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- Plan section: Implementation Target Files — row 6 of 7
  (`tests/agent/test_tool_approval_preflight.py`); Tests section; Implementation steps Phase
  1
- Requirements: REQ-005
- Acceptance criteria: AC-1, AC-3
- Procedure file:
  `implementations/20261025-004008_06_tests_agent_test_tool_approval_preflight.py.md`
- Validation commands: `uv run pytest tests/agent/test_tool_approval_preflight.py -q`;
  `uv run pytest tests/agent -q`
