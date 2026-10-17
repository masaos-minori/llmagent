## Goal

Add the cases that pin the new `requested_target` emission in `tests/agent/test_audit_log_format.py`:
the key appears when a caller supplies it, is absent when it is not, and record key ordering stays
deterministic (REQ-003).

## Scope

- Add a present-value case through `_build_audit_record`.
- Add an absent-key case through `_build_audit_record`.
- Add an end-to-end case through `_mcp_audit_log` that parses the emitted line and asserts the key.
- Leave every existing test unchanged.

## Assumptions

- The file's existing `_get_parsed` helper already calls `_mcp_audit_log` with a `MagicMock` logger and
  parses `logger.info` argument, so the end-to-end case needs no new fixture.
- The existing sorted-keys test reads the keys of a record built without optional fields, so it stays
  valid without modification.

## Design decisions

- Assert key presence and absence directly (`"requested_target" in parsed`) rather than comparing whole
  records, so the new key cannot silently appear in records that never asked for it.
- Reuse the pairing already documented for `canonical_target`: one case supplies both values and
  asserts both appear.

## Alternatives considered

- Extend the existing whole-record comparison tests: rejected — they would have to change their expected
  record shape for every optional field, which weakens the regression value of those tests.

## Implementation

### Target file

`tests/agent/test_audit_log_format.py`

### Procedure

1. Add a `requested_target` group to the MCP-format test class.
2. Add the three cases described in Scope.

### Method

Call `_build_audit_record` directly for the shape cases and `_mcp_audit_log` through the existing
`_get_parsed` helper for the serialized case.

### Details

- Present case: `requested_target="/repo/../private/x"` and `canonical_target="/repo/x"`; assert both
  keys are present with the supplied values.
- Absent case: build a record with no `requested_target` argument; assert `"requested_target" not in
  record` and that the always-present fields are still present.
- Serialized case: parse the emitted line and assert `list(parsed)` is sorted, which keeps the
  `OPT_SORT_KEYS` guarantee while the optional key is present.

## Compatibility considerations

- No existing assertion changes. The file's correlation and agent-side format tests are untouched.

## Security considerations

- The present-value case uses a path containing a traversal segment to record that the field carries the
  caller-supplied form verbatim and is not normalized here.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest -q tests/agent/test_audit_log_format.py`
- `uv run pytest -q tests/agent/`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`

## Completion criteria

- All three cases pass against the implementation from Plan row 1 (AC-002).
- The absent-key case fails if the emission becomes unconditional.
- All pre-existing tests in the file still pass.

## Out of scope

- Server-side emission tests for the file servers, which live in Plan row 7.
- Documenting the field, which lives in Plan row 17.
- Agent-side `tool_exec` record shape.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the present, absent, and serialized cases | Pending | — | — | REQ-003 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `tests/agent/test_audit_log_format.py`
