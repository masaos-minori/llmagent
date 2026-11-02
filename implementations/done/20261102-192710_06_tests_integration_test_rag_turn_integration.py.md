<!-- workitem: {"id": "20261102-192710", "generated_at": "2026-11-02T19:27:10Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261101-142029_toolarg001_tool-validation-fails-open-empty-schema.md", "target_file": "tests/integration/test_rag_turn_integration.py", "target_kind": "test", "seq": 6} -->

## Goal

Migrate the empty-schema registry stub in `tests/integration/test_rag_turn_integration.py`
to a well-formed zero-argument schema so the F-series tests keep passing after the
validator fails closed (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Only the `_default_runtime_tools._get` body changes; its docstring describes the
  fail-closed preparation phase and does not cite the empty schema, so no rewording is
  required (verified 20261102).

## Design decisions

- Fixture schema `{"type": "object", "properties": {}}` with `allow_extra_fields = True`
  preserves the previous pass behavior (Plan Design).

## Alternatives considered

N/A: fixture migration specified in the Plan.

## Implementation
### Target file
`tests/integration/test_rag_turn_integration.py`

### Procedure
Replace `tool.input_schema = {}` in `_default_runtime_tools._get` with the
zero-argument schema.

### Method
- `tool.input_schema = {}` → `tool.input_schema = {"type": "object", "properties": {}}`;
  keep `tool.allow_extra_fields = True`. No assertion changes.

### Details
- The five injection-run failures this migration prevents are the five async tests
  `test_f01_rag_empty_result_turn_continues` through `test_f05_mixed_success_and_timeout_in_same_round`,
  all resolving tools through `_default_runtime_tools`.

## Compatibility considerations

Stub pass behavior is preserved; no test assertions change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| This file | Integration (regression) | `uv run pytest tests/integration/test_rag_turn_integration.py` | Pass with migrated fixture (AC-4) |
| Phase 1 gate | Regression | `uv run pytest tests/agent tests/integration` (Plan Phase 1) | No failure caused by an empty-schema stub |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (sequence in `rules/toolchain.md` section 7) | At least 90% |

## Completion criteria

- No `input_schema = {}` remains in this file (AC-4).
- The five async tests named in Details pass with the stub keeping its previous pass
  behavior.

## Out of Scope

- The validator code change (procedure seq 01) and the other fixture files
  (procedures seq 03, 04, 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate `_default_runtime_tools._get` to `{"type": "object", "properties": {}}` (REQ-004) | Completed | 20261102-195726 | 2026-11-02 | Plan Phase 1; lands before procedure seq 01's code change |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-02 | 2026-11-02 | Batch full-suite run passed: 11369 passed / 8 skipped; diff-cover 100% |

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
- **Requirement ID**: `REQ-004` (fixture schema migration)
- **Source issue**: issues/20261003-180328_toolarg001_tool-validation-fails-open-empty-schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142029_toolarg001_tool-validation-fails-open-empty-schema.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-192710
- **Related target files**: tests/integration/test_rag_turn_integration.py
