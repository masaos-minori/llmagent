<!-- workitem: {"id": "20261102-192710", "generated_at": "2026-11-02T19:27:10Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261101-142029_toolarg001_tool-validation-fails-open-empty-schema.md", "target_file": "tests/agent/test_tool_runner.py", "target_kind": "test", "seq": 4} -->

## Goal

Migrate the three empty-schema registry-stub helpers in `tests/agent/test_tool_runner.py`
to a well-formed zero-argument schema so their tests keep passing after the validator
fails closed on missing/empty schemas (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Only the three helper bodies change; this file is also targeted by
  `plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md` and
  `plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md`,
  which add test functions only (compatible per the Plan's updated Step 8b overlap note);
  blockio001 defers its additions to this file until after this procedure.
- `tests/agent/test_tool_loop_guard_wiring.py` imports `_make_ctx` from this file; its
  injection-run failures are fixed by this migration — that file itself is not modified.

## Design decisions

- Fixture schema `{"type": "object", "properties": {}}` with `allow_extra_fields = True`
  preserves the previous pass behavior (Plan Design).

## Alternatives considered

N/A: fixture migration specified in the Plan.

## Implementation
### Target file
`tests/agent/test_tool_runner.py`

### Procedure
Replace `tool.input_schema = {}` with the zero-argument schema in the `_get` helpers of
`_default_runtime_tools`, `_runtime_tools` and `_write_registry`; reword the
`_write_registry` comment that describes the empty schema as the way validation is made
to pass.

### Method
- In each of the three helpers: `tool.input_schema = {}` →
  `tool.input_schema = {"type": "object", "properties": {}}`; keep
  `tool.allow_extra_fields = True`.
- Reword the two stub comments that describe an empty schema as the way validation
  passes: the one in `_runtime_tools._get` and the one in `_write_registry._get`
  (correction from Step 3a: the comment exists at both sites, not only in
  `_write_registry`).

### Details
- The 20 tests the Plan's failure-injection run flagged in this file all resolve their
  tools through these three helpers (verified 20261102: three single-line
  `tool.input_schema = {}` sites, each followed by `allow_extra_fields = True`).

## Compatibility considerations

Stub pass behavior is preserved; no test assertions change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| This file + dependent test file | Integration (regression) | `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_loop_guard_wiring.py` | Pass with migrated fixtures (AC-4) |
| Phase 1 gate | Regression | `uv run pytest tests/agent tests/integration` (Plan Phase 1) | No failure caused by an empty-schema stub |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (sequence in `rules/toolchain.md` section 7) | At least 90% |

## Completion criteria

- No `input_schema = {}` remains in this file (AC-4).
- `tests/agent/test_tool_runner.py` and `tests/agent/test_tool_loop_guard_wiring.py`
  pass with the stubs keeping their previous pass behavior.

## Out of Scope

- The validator code change (procedure seq 01) and the other fixture files
  (procedures seq 03, 05, 06).
- Test additions owned by blockio001 / inflightcancel001.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate the three helper stubs to `{"type": "object", "properties": {}}` and reword the `_write_registry` comment (REQ-004) | Completed | 20261102-195653 | 2026-11-02 | Plan Phase 1; lands before procedure seq 01's code change |
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
- **Related target files**: tests/agent/test_tool_runner.py
