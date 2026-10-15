## Goal

Assert the new `memory_max_pinned` field is accepted (not rejected as an unknown
key) in `test_removed_config_keys_rejected.py` (REQ-006).

## Scope

Modify `tests/agent/test_removed_config_keys_rejected.py` only: extend existing
unknown-key rejection tests.

## Assumptions

- `memory_max_pinned` must be accepted by the config loader, not rejected as an
  unknown key (REQ-006).
- All tests use sandbox config; none open a production DB.

## Design decisions

- Load a config containing `memory_max_pinned` and assert it is accepted while
  genuinely unknown keys are still rejected.

## Alternatives considered

- Adding a new test file: rejected. `test_removed_config_keys_rejected.py` already
  owns the unknown-key rejection coverage; extend it.

## Implementation

### Target file

`tests/agent/test_removed_config_keys_rejected.py`

### Procedure

1. Add an acceptance test for `memory_max_pinned`.

### Method

- Load a config that includes `memory_max_pinned` and assert the load succeeds
  and the value is present on `cfg.memory`.
- Keep the existing assertion that a truly unknown key is rejected, to guard
  against loosening validation too far.

### Details

- Keep assertions on trigger conditions rather than exact message strings
  (UNK-01).

## Compatibility considerations

Extends existing rejection tests; additive.

## Security considerations

N/A: test-only; sandbox config throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/agent/test_removed_config_keys_rejected.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts `memory_max_pinned` is accepted while unknown keys remain
rejected.

## Out of scope

The config field (`config_dataclasses.py`), the builder
(`config_builders.py`), the validator (`services/config_validators.py`), the
field registry (`services/config_field_registry.py`), and `config/agent.toml`
are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend new-field acceptance test | Pending | — | — | REQ-006 |
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
- **Related target files**: tests/agent/test_removed_config_keys_rejected.py
