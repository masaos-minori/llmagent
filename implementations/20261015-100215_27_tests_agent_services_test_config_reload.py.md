## Goal

Cover hot reload of `memory_max_pinned` in `test_config_reload.py` (REQ-006).

## Scope

Modify `tests/agent/services/test_config_reload.py` only: extend existing hot
reload tests.

## Assumptions

- `memory_max_pinned` hot-reloads without a process restart (REQ-006).
- The field is registered in `CONFIG_FIELD_REGISTRY` with `hot_reloadable=True`
  and a validator (REQ-006).
- All tests use sandbox config; none open a production DB.

## Design decisions

- Simulate a config change that updates `memory_max_pinned` and assert the loaded
  value reflects the change without a restart.

## Alternatives considered

- Adding a new test file: rejected. `test_config_reload.py` already owns the hot
  reload coverage; extend it.

## Implementation

### Target file

`tests/agent/services/test_config_reload.py`

### Procedure

1. Add a `memory_max_pinned` hot-reload test.

### Method

- Load config, apply a reload that changes `memory_max_pinned`, and assert the
  new value is reflected in `cfg.memory.memory_max_pinned`.

### Details

- Keep assertions on trigger conditions rather than exact message strings
  (UNK-01).

## Compatibility considerations

Extends existing reload tests; additive.

## Security considerations

N/A: test-only; sandbox config throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/agent/services/test_config_reload.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts `memory_max_pinned` hot-reloads without a restart.

## Out of scope

The config field (`config_dataclasses.py`), the builder
(`config_builders.py`), the validator (`services/config_validators.py`), the
field registry (`services/config_field_registry.py`), and `config/agent.toml`
are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend memory_max_pinned hot-reload test | Pending | — | — | REQ-006 |
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
- **Related target files**: tests/agent/services/test_config_reload.py
