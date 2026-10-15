## Goal

Cover `_build_memory_config()` honoring `memory_max_pinned` in
`test_config_builders.py` (REQ-006).

## Scope

Modify `tests/agent/test_config_builders.py` only: extend existing builder tests.

## Assumptions

- `_build_memory_config()` reads `memory_max_pinned` from the raw dict and sets it
  on the resulting `MemoryConfig` (REQ-006).
- All tests use sandbox config; none open a production DB.

## Design decisions

- Build a raw dict containing `memory_max_pinned` and assert the built
  `MemoryConfig` carries the value.

## Alternatives considered

- Adding a new test file: rejected. `test_config_builders.py` already owns the
  builder coverage; extend it.

## Implementation

### Target file

`tests/agent/test_config_builders.py`

### Procedure

1. Add a `memory_max_pinned` passthrough test.

### Method

- Provide a raw dict with `memory_max_pinned = 25` and assert the built
  `MemoryConfig.memory_max_pinned == 25`.
- Optionally assert the default (10) when the key is absent.

### Details

- Keep assertions on trigger conditions rather than exact message strings
  (UNK-01).

## Compatibility considerations

Extends existing builder tests; additive.

## Security considerations

N/A: test-only; sandbox config throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/agent/test_config_builders.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts `_build_memory_config()` honors `memory_max_pinned` from the raw
dict.

## Out of scope

The config field (`config_dataclasses.py`), the validator
(`services/config_validators.py`), the field registry
(`services/config_field_registry.py`), and `config/agent.toml` are separate
target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend _build_memory_config memory_max_pinned test | Pending | — | — | REQ-006 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: tests/agent/test_config_builders.py
