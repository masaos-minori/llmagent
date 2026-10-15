## Goal

Add `validate_memory_max_pinned` (>= 1) following the `validate_memory_*`
pattern, enforcing the pin-limit lower bound (REQ-006).

## Scope

Modify `scripts/agent/services/config_validators.py` only: add one validator
function.

## Assumptions

- The contract is "at least 1" (REQ-006), matching
  `validate_memory_retention_days` which uses `_require_at_least(..., 1)`.
- The function receives a `MemoryConfig` instance (typed under `TYPE_CHECKING`),
  consistent with the sibling validators.

## Design decisions

- Implement as a thin wrapper: `_require_at_least("memory_max_pinned", cfg.memory_max_pinned, 1)`.
- Place it immediately after `validate_memory_retention_days`, keeping the
  memory validators grouped.

## Alternatives considered

- Inlining the check in `config_dataclasses.py` `__post_init__`: rejected. The
  project extracts each field check into `config_validators.py` so the dataclass
  stays a thin holder; follow the established extraction.

## Implementation

### Target file

`scripts/agent/services/config_validators.py`

### Procedure

1. Add `validate_memory_max_pinned(cfg: MemoryConfig) -> None` after
   `validate_memory_retention_days`.

### Method

```python
def validate_memory_max_pinned(cfg: MemoryConfig) -> None:
    """Validate that memory_max_pinned is at least 1."""
    _require_at_least("memory_max_pinned", cfg.memory_max_pinned, 1)
```

### Details

- Uses the existing `_require_at_least` helper (already imported in this module).
- `MemoryConfig` is referenced under `TYPE_CHECKING`; no runtime import needed.
- Keep the two-blank-line separation between functions.

## Compatibility considerations

Purely additive function; no existing caller changes. `config_dataclasses.py`
(row 13) adds the call site.

## Security considerations

N/A: bounds a configuration value.

## Rollback considerations

Revert the commit; the function is additive.

## Validation plan

- `pytest tests/agent/test_config_dataclasses.py` triggers the validator via
  `MemoryConfig.__post_init__`.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`MemoryConfig(memory_max_pinned=0)` raises `ValueError` mentioning
`memory_max_pinned`; a value of 1 passes.

## Out of scope

The field definition (`config_dataclasses.py`), the builder
(`config_builders.py`), the registry entry (`config_field_registry.py`), and the
TOML value (`config/agent.toml`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `validate_memory_max_pinned` | Pending | — | — | REQ-006 |
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
- **Related target files**: scripts/agent/services/config_validators.py
