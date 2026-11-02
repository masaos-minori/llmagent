<!-- workitem: {"id": "20261102-192710", "generated_at": "2026-11-02T19:27:10Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261101-142029_toolarg001_tool-validation-fails-open-empty-schema.md", "target_file": "tests/agent/test_tool_preparation.py", "target_kind": "test", "seq": 3} -->

## Goal

Migrate the empty-schema registry stub in `tests/agent/test_tool_preparation.py` to a
well-formed zero-argument schema (REQ-004: fixtures keep their pass behavior), and add
the preparation-level rejection test showing `prepare_tool_calls()` rejects an
empty-schema tool with kind `schema` (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Fixture migration (Plan Phase 1) lands before the validator change in procedure
  seq 01 (Plan Phase 2), so this file shows no failures during Phase 1.
- The failure tuple `failures[0]` does not carry `kind` as a separate field; the
  `schema` kind is observable through the failure text (`_reject` puts
  `validation.reason` into it), the same pattern as the existing
  `test_registry_none_rejects_with_configuration_kind` asserts on text (verified 20261102).

## Design decisions

- Fixture schema `{"type": "object", "properties": {}}` with `allow_extra_fields` kept
  at `True` preserves the previous pass behavior (no required fields; extra-field check
  skipped; jsonschema accepts any property) (Plan Design).

## Alternatives considered

N/A: test-fixture migration specified in the Plan; no design decision of its own.

## Implementation
### Target file
`tests/agent/test_tool_preparation.py`

### Procedure
Replace `input_schema = {}` in `TestPrepareToolCallsBatchOrdering._valid_registry` with
the zero-argument schema, then add one empty-schema rejection test class/function.

### Method
- In `_valid_registry`: `runtime_tool.input_schema = {}` →
  `runtime_tool.input_schema = {"type": "object", "properties": {}}`;
  `runtime_tool.allow_extra_fields = True` stays.
- Add `test_empty_schema_rejected_with_schema_kind` (new) following the shape of
  `TestPrepareToolCallsConfigurationErrors.test_registry_none_rejects_with_configuration_kind`:
  `_make_ctx()`, a `MagicMock` runtime tool with `input_schema = {}` and
  `allow_extra_fields = True` returned by `runtime_tools.get`, one `_tc(...)` call.

### Details
- `_valid_registry` currently sets `input_schema = {}` and feeds
  `test_mixed_valid_invalid_batch_preserves_order` and
  `test_approval_never_called_for_failed_prep_call` — the two tests the Plan's
  failure-injection run showed would fail without this migration.
- New-test assertions (AC-5): `prepared == []`, `len(failures) == 1`, `is_error is True`,
  and the failure text contains the tool name and "input schema" (the rejection reason
  from AC-1, i.e. the `schema`-kind `_reject`).
- Other stubs in this file already use non-empty schemas
  (`TestPrepareToolCallsSchemaViolation`, `TestPrepareToolCallsHappyPath`) — do not touch them.

## Compatibility considerations

Only the stub's schema value and one new test change; existing assertions stay valid.

## Security considerations

N/A: test-only change; it locks in the fail-closed contract asserted elsewhere.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| This file | Unit | `uv run pytest tests/agent/test_tool_preparation.py` | All pass; the new call fails with the `schema`-kind reason (AC-5) |
| Batch-ordering tests during Phase 1 | Regression | `uv run pytest tests/agent tests/integration` (Plan Phase 1 gate) | Pass with the migrated stub while the validator is still lenient |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (sequence in `rules/toolchain.md` section 7) | At least 90% |

## Completion criteria

- No `input_schema = {}` remains in the fixture helpers; `_valid_registry`-based tests
  pass unchanged (AC-4). The new rejection test intentionally supplies an empty schema.
- The new test yields one failure whose text names the tool and "input schema" and
  `prepared == []` (AC-5).

## Out of Scope

- The validator code change (procedure seq 01).
- Fixture files of procedures seq 04-06.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate `_valid_registry` to `{"type": "object", "properties": {}}` (REQ-004) | Completed | 20261102-195545 | 2026-11-02 | Plan Phase 1; lands before procedure seq 01's code change |
| 2 | Add `test_empty_schema_rejected_with_schema_kind` (new) asserting kind `schema` (REQ-005) | Completed | 20261102-195554 | 2026-11-02 | Rejection test red until procedure seq 01 code landed, then green (allowed red in batch order 03-06 then 01) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-02 | 2026-11-02 | Batch full-suite run passed: 11369 passed / 8 skipped; diff-cover 100% |

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
- **Requirement ID**: `REQ-004` (fixture schema migration), `REQ-005` (preparation-level rejection test)
- **Source issue**: issues/20261003-180328_toolarg001_tool-validation-fails-open-empty-schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142029_toolarg001_tool-validation-fails-open-empty-schema.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-192710
- **Related target files**: tests/agent/test_tool_preparation.py
