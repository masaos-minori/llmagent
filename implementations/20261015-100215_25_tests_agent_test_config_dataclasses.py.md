## Goal

Cover `MemoryConfig.memory_max_pinned` validation in `test_config_dataclasses.py`:
the default (10) and the `>= 1` rejection (REQ-006).

## Scope

Modify `tests/agent/test_config_dataclasses.py` only: extend existing
MemoryConfig validation tests.

## Assumptions

- `memory_max_pinned` defaults to 10 and must be at least 1 (REQ-006).
- The validator `validate_memory_max_pinned` is called from `MemoryConfig.__post_init__`
  (REQ-006).
- All tests use sandbox config; none open a production DB.

## Design decisions

- Construct `MemoryConfig` with and without the field and assert the default and
  the rejection path.

## Alternatives considered

- Adding a new test file: rejected. `test_config_dataclasses.py` already owns the
  MemoryConfig coverage; extend it.

## Implementation

### Target file

`tests/agent/test_config_dataclasses.py`

### Procedure

1. Add a default-value test.
2. Add a `>= 1` rejection test.

### Method

- Default: construct `MemoryConfig` without `memory_max_pinned` and assert it
  equals 10.
- Rejection: construct `MemoryConfig` with `memory_max_pinned = 0` (or negative)
  and assert the validator raises.

### Details

- Assert on the trigger condition (exception raised) rather than an exact
  message string (UNK-01).

## Compatibility considerations

Extends existing config-dataclass tests; additive.

## Security considerations

N/A: test-only; sandbox config throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/agent/test_config_dataclasses.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts `memory_max_pinned` defaults to 10 and rejects values below 1.

## Out of scope

The config field (`config_dataclasses.py`), the builder
(`config_builders.py`), the validator (`services/config_validators.py`), the
field registry (`services/config_field_registry.py`), and `config/agent.toml`
are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend memory_max_pinned validation tests | Pending | — | — | REQ-006 |
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
- **Related target files**: tests/agent/test_config_dataclasses.py
