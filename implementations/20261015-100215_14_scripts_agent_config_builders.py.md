## Goal

Thread `memory_max_pinned` from the raw `[memory]` config dict into
`MemoryConfig` (REQ-006) so the new field is populated from `config/agent.toml`.

## Scope

Modify `scripts/agent/config_builders.py` only: read `memory_max_pinned` in
`_build_memory_config()` and pass it to `MemoryConfig(...)`.

## Assumptions

- The field defaults to 10 and is validated >= 1 downstream in
  `MemoryConfig.__post_init__`; the builder uses `_get_int` like the other memory
  integer fields.
- The `MemoryConfig` field itself is added in `config_dataclasses.py` (a separate
  target row); this document assumes it exists.

## Design decisions

- Read via `_get_or_default(cfg, "memory_max_pinned", _get_int, 10)` next to
  `memory_retention_days`, then pass it positionally by keyword into
  `MemoryConfig(...)`, matching the surrounding field-by-field pattern.

## Alternatives considered

- Reading the value lazily at access time: rejected. Every other memory field is
  built eagerly in `_build_memory_config()`, and eager keeps the builder the
  single place that maps TOML to `MemoryConfig`.

## Implementation

### Target file

`scripts/agent/config_builders.py`

### Procedure

1. Read `memory_max_pinned` in `_build_memory_config()`.
2. Pass `memory_max_pinned=...` into the `MemoryConfig(...)` call.

### Method

- After the `memory_retention_days` read, add:

  ```python
  memory_max_pinned = _get_or_default(
      cfg, "memory_max_pinned", _get_int, 10
  )
  ```

- Inside the `return MemoryConfig(...)` call, add the keyword
  `memory_max_pinned=memory_max_pinned` (e.g. after
  `memory_retention_days=memory_retention_days,`).

### Details

- `_get_int` is the same coercion helper used by `memory_retention_days`; it
  rejects wrong types per the type-coercion policy (`rules/coding.md`).
- Do not reorder existing keyword arguments beyond inserting the new one.

## Compatibility considerations

The builder already constructs `MemoryConfig` by keyword; adding one more keyword
is additive. If the key is absent from TOML, the default 10 applies.

## Security considerations

N/A: configuration parsing only.

## Rollback considerations

Revert the commit; the reads and keyword are additive.

## Validation plan

- `pytest tests/agent/test_config_builders.py` covers `_build_memory_config`.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`_build_memory_config()` returns a `MemoryConfig` whose `memory_max_pinned` equals
the TOML value (or 10 when absent).

## Out of scope

The field definition and validator (`config_dataclasses.py`), the validator body
(`config_validators.py`), the registry entry (`config_field_registry.py`), and the
TOML value (`config/agent.toml`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Thread `memory_max_pinned` through `_build_memory_config()` | Pending | — | — | REQ-006 |
| 2 | Add/update builder tests | Pending | — | — | `test_config_builders.py` |
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
- **Related target files**: scripts/agent/config_builders.py
