## Goal

Add `MemoryConfig.memory_max_pinned` (default 10, >= 1) so the pin limit
(REQ-006) has a validated, hot-reloadable configuration value.

## Scope

Modify `scripts/agent/config_dataclasses.py` only: add the field to
`MemoryConfig` and call its validator from `__post_init__`.

## Assumptions

- Default is 10; the validator enforces >= 1 (matches REQ-006 and the
  `validate_memory_retention_days` precedent).
- The validator function itself is added in `config_validators.py` (a separate
  target row); here it is imported and called, so both the import and the
  function name are marked (new).

## Design decisions

- Place the field directly after `memory_retention_days` and call the validator
  alongside the other `_v_mem_*` calls, matching the existing per-field layout.
- Reuse `_require_at_least(..., 1)` rather than a bespoke check, keeping a single
  validation primitive shared with the other memory validators.

## Alternatives considered

- A builder-level default instead of a dataclass default: rejected. The dataclass
  default keeps the field self-documenting and matches every other `MemoryConfig`
  field; the builder only threads an explicit value through.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. Add the field `memory_max_pinned: int = 10` to `MemoryConfig` (after
   `memory_retention_days`).
2. Import the new validator and call it in `MemoryConfig.__post_init__`.

### Method

- In `MemoryConfig`, add a comment + field:

  ```python
  # Max entries that may be pinned at once
  memory_max_pinned: int = 10
  ```

- Add an import:

  ```python
  from agent.services.config_validators import (
      validate_memory_max_pinned as _v_mem_mmp,
  )
  ```

  (`validate_memory_max_pinned` is (new); created in the `config_validators.py`
  target row.)

- In `__post_init__`, add `_v_mem_mmp(self)` after `_v_mem_rtd(self)`.

### Details

- The alias `_v_mem_mmp` follows the existing `_v_mem_<abbr>` convention
  (`_v_mem_rtd`, `_v_mem_met`).
- The new import belongs in the alphabetical `validate_memory_*` import block;
  ruff `I` enforces ordering.
- The field is plain `int`; no other dataclass changes.

## Compatibility considerations

Adding a field with a default cannot break existing `MemoryConfig()` construction.
`config_builders.py` builds the class by keyword, so the new positional-free
field does not shift any existing argument.

## Security considerations

N/A: this adds a configuration bound, not a new attack surface.

## Rollback considerations

Revert the commit; the field and import are purely additive.

## Validation plan

- `pytest tests/agent/test_config_dataclasses.py` exercises `MemoryConfig`.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`MemoryConfig.memory_max_pinned` defaults to 10, `MemoryConfig(memory_max_pinned=0)`
raises `ValueError`, and the validator runs inside `__post_init__`.

## Out of scope

The validator body (`config_validators.py`), the builder thread
(`config_builders.py`), the registry entry (`config_field_registry.py`), and the
`[memory]` TOML value (`config/agent.toml`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `MemoryConfig.memory_max_pinned` and call its validator in `__post_init__` | Pending | — | — | REQ-006 |
| 2 | Add/update config-validation tests | Pending | — | — | `test_config_dataclasses.py` |
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
- **Related target files**: scripts/agent/config_dataclasses.py
