## Goal

Register `memory_max_pinned` in `CONFIG_FIELD_REGISTRY` under the `memory`
section with `hot_reloadable=True` and its validator reference (REQ-006).

## Scope

Modify `scripts/agent/services/config_field_registry.py` only: add one
`ConfigFieldRegistry` entry to the Memory section.

## Assumptions

- `hot_reloadable=True` (REQ-006: hot-reloadable without restart).
- The `ConfigFieldRegistry` constructor is `ConfigFieldRegistry(name, section,
  hot_reloadable)` as shown by the existing memory entries.
- The validator name string is `"validate_memory_max_pinned"` (the function added
  in `config_validators.py`, row 15).

## Design decisions

- Insert `ConfigFieldRegistry("memory_max_pinned", "memory", True)` among the
  existing Memory-section entries (after `memory_retention_days`), keeping the
  section grouped.

## Alternatives considered

- Marking it `hot_reloadable=False`: rejected. REQ-006 requires hot reload; the
  pin limit must take effect without a restart.

## Implementation

### Target file

`scripts/agent/services/config_field_registry.py`

### Procedure

1. Add the `ConfigFieldRegistry` entry in the Memory section.

### Method

After `ConfigFieldRegistry("memory_retention_days", "memory", True)`, add:

```python
ConfigFieldRegistry("memory_max_pinned", "memory", True),
```

### Details

- The third positional argument is `hot_reloadable`; `True` matches
  `memory_retention_days`.
- The entry is added to `_CONFIG_ENTRIES` (which `CONFIG_FIELD_REGISTRY` is built
  from); do not edit the derived dict literal.
- Keep alphabetical/section grouping consistent with siblings.

## Compatibility considerations

Adding a registry entry does not change any existing entry's behavior. The
reload-classification test (`test_config_reload_classification.py`, row 28)
asserts `hot_reloadable=True` for this key.

## Security considerations

N/A: registry metadata only.

## Rollback considerations

Revert the commit; the entry is additive.

## Validation plan

- `pytest tests/agent/services/test_config_reload_classification.py` asserts the
  `hot_reloadable=True` classification.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`registry_for("memory")` includes an entry named `memory_max_pinned` with
`hot_reloadable == True`.

## Out of scope

The field definition (`config_dataclasses.py`), the validator
(`config_validators.py`), the builder (`config_builders.py`), and the TOML value
(`config/agent.toml`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register `memory_max_pinned` (hot_reloadable=True) | Pending | — | — | REQ-006 |
| 2 | Add/update reload-classification tests | Pending | — | — | `test_config_reload_classification.py` |
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
- **Related target files**: scripts/agent/services/config_field_registry.py
