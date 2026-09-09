# Implementation Procedure: Create Unit Tests for Config Resolution

## Goal

Create unit tests for `resolve_rag_config()` covering priority ordering, defaults, and validation error propagation, ensuring the extracted function behaves identically to the original.

## Scope

- Create `tests/rag/test_config_resolution.py` with comprehensive unit tests
- Cover: CLI args > env vars > YAML config > defaults priority ordering
- Cover: default values when no overrides provided
- Cover: validation error propagation (exceptions raised for invalid configs)

## Assumptions

- `resolve_rag_config()` exists in `scripts/rag/config_resolution.py` (created by Phase 2).
- The function depends only on `RagConfigImpl`, `RagConfig`, and standard library modules.
- No other file imports `resolve_rag_config` directly from `pipeline.py` (confirmed by grep).

## Design decisions

1. **Test the function directly**, not through `RagPipeline` — isolates config resolution logic.
2. **Use `pytest` fixtures** for common test setup (e.g., mock YAML configs, environment variables).
3. **Test priority ordering explicitly** — verify that higher-priority sources override lower ones.

## Alternatives considered

- Testing through `RagPipeline.__init__`: rejected because it couples config resolution tests to pipeline construction.
- Property-based testing: rejected because the config resolution logic has clear discrete cases (priority ordering, defaults, errors).

## Implementation

### Target file

`tests/rag/test_config_resolution.py`

### Procedure

1. Create `tests/rag/test_config_resolution.py` with module docstring referencing `config_resolution.py` as the source.
2. Write test class(es) covering:
   - **Priority ordering**: CLI args > env vars > YAML config > defaults
   - **Defaults**: when no overrides provided, returns expected defaults
   - **Validation errors**: exceptions raised for invalid configs
   - **Edge cases**: empty configs, partial overrides, conflicting values across layers
3. Ensure ≥80% branch coverage for `config_resolution.py`.

### Method

Standard unit test creation: define test functions/classes, use `pytest` fixtures for setup, assert expected behavior.

### Details

- Priority order: CLI args (highest) → env vars → YAML config → defaults (lowest)
- Each layer can override the previous one
- Validation errors propagate as exceptions (not silently ignored)
- Default values come from `RagConfig` dataclass defaults

## Compatibility considerations

- Tests must validate that `resolve_rag_config()` behaves identically to the original (before extraction).

## Security considerations

- Test file changes have no security impact.

## Rollback considerations

- Revert: delete `test_config_resolution.py`.
- Trivial rollback.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/config_resolution.py` | Unit | `uv run pytest tests/rag/test_config_resolution.py -v` | Priority ordering, defaults, and validation-error propagation all pass |

## Completion criteria

- `tests/rag/test_config_resolution.py` passes with ≥80% branch coverage.
- Priority ordering verified: CLI > env > YAML > defaults.
- Defaults verified: correct values when no overrides.
- Validation errors verified: exceptions raised for invalid configs.

## Out of scope

- Integration tests for `RagPipeline` (covered separately).
- Performance benchmarks.
- Testing config hot-reload (out of scope for this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/rag/test_config_resolution.py` | Pending | — | — | |
| 2 | Run validation sequence | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-008 — unit tests for `resolve_rag_config()`, ≥80% branch coverage
- **Source issue**: issues/20260908-105318_refactor_rag_pipeline_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-165531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-165531
- **Related target files**: tests/rag/test_config_resolution.py
