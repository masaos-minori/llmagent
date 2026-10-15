## Goal

Cover the `hot_reloadable=True` classification of `memory_max_pinned` in
`test_config_reload_classification.py` (REQ-006).

## Scope

Modify `tests/agent/services/test_config_reload_classification.py` only: extend
existing classification tests.

## Assumptions

- `memory_max_pinned` is classified as `hot_reloadable=True` in
  `CONFIG_FIELD_REGISTRY` (REQ-006).
- All tests use sandbox config; none open a production DB.

## Design decisions

- Assert the registry entry for `memory_max_pinned` carries `hot_reloadable=True`
  and a validator reference.

## Alternatives considered

- Adding a new test file: rejected. `test_config_reload_classification.py` already
  owns the registry-classification coverage; extend it.

## Implementation

### Target file

`tests/agent/services/test_config_reload_classification.py`

### Procedure

1. Add a `memory_max_pinned` classification test.

### Method

- Look up `memory_max_pinned` in `CONFIG_FIELD_REGISTRY` and assert
  `hot_reloadable is True` and a validator is registered.

### Details

- Keep assertions on trigger conditions rather than exact message strings
  (UNK-01).

## Compatibility considerations

Extends existing classification tests; additive.

## Security considerations

N/A: test-only; sandbox config throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/agent/services/test_config_reload_classification.py` (sandbox
  config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts `memory_max_pinned` is classified `hot_reloadable=True` with a
validator.

## Out of scope

The config field (`config_dataclasses.py`), the builder
(`config_builders.py`), the validator (`services/config_validators.py`), the
field registry (`services/config_field_registry.py`), and `config/agent.toml`
are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend hot_reloadable classification test | Pending | — | — | REQ-006 |
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
- **Related target files**: tests/agent/services/test_config_reload_classification.py
