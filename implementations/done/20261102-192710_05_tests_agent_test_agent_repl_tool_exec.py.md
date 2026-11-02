<!-- workitem: {"id": "20261102-192710", "generated_at": "2026-11-02T19:27:10Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261101-142029_toolarg001_tool-validation-fails-open-empty-schema.md", "target_file": "tests/agent/test_agent_repl_tool_exec.py", "target_kind": "test", "seq": 5} -->

## Goal

Migrate the empty-schema registry stub in `tests/agent/test_agent_repl_tool_exec.py` to
a well-formed zero-argument schema so its DAG-execution tests keep passing after the
validator fails closed (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Only the `_runtime_tools_for_dag` helper changes; the helper docstring's wording
  "Provides a permissive empty schema (so argument validation ...)" is reworded to
  describe the zero-argument schema (it currently states why validation passes).

## Design decisions

- Fixture schema `{"type": "object", "properties": {}}` with `allow_extra_fields = True`
  preserves the previous pass behavior (Plan Design).

## Alternatives considered

N/A: fixture migration specified in the Plan.

## Implementation
### Target file
`tests/agent/test_agent_repl_tool_exec.py`

### Procedure
Replace `tool.input_schema = {}` in `_runtime_tools_for_dag` with the zero-argument
schema and reword the helper docstring sentence.

### Method
- `tool.input_schema = {}` → `tool.input_schema = {"type": "object", "properties": {}}`;
  keep `tool.allow_extra_fields = True`.
- Reword only the docstring sentence that cites the empty schema as the reason
  validation passes; no assertion changes.

### Details
- The three injection-run failures this migration prevents are
  `test_dag_serial_tool_calls_overrides_dag`, `test_dag_write_executed_before_read` and
  `test_parallel_execution_without_side_effects`, all resolving tools through
  `_runtime_tools_for_dag`.

## Compatibility considerations

Stub pass behavior is preserved; no test assertions change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| This file | Integration (regression) | `uv run pytest tests/agent/test_agent_repl_tool_exec.py` | Pass with migrated fixture (AC-4) |
| Phase 1 gate | Regression | `uv run pytest tests/agent tests/integration` (Plan Phase 1) | No failure caused by an empty-schema stub |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (sequence in `rules/toolchain.md` section 7) | At least 90% |

## Completion criteria

- No `input_schema = {}` remains in this file (AC-4).
- The three DAG tests pass with the stub keeping its previous pass behavior.

## Out of Scope

- The validator code change (procedure seq 01) and the other fixture files
  (procedures seq 03, 04, 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate `_runtime_tools_for_dag` to `{"type": "object", "properties": {}}` and reword its docstring sentence (REQ-004) | Completed | 20261102-195711 | 2026-11-02 | Plan Phase 1; lands before procedure seq 01's code change |
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
- **Related target files**: tests/agent/test_agent_repl_tool_exec.py
