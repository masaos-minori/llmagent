## Goal

Add `__post_init__` to `DiagnosticsConfig` so a malformed `[diagnostics]` section fails startup or reload with a typed error instead of silently weakening protection (`REQ-002`, `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The three validators (`validate_diagnostics_encryption_key`(new), `validate_diagnostics_retention_days`(new), `validate_diagnostics_sensitive_fields`(new)) are added by `scripts/agent/services/config_validators.py` (its own row); this file only imports and calls them.
- An empty `encryption_key` is valid (opt-in encryption); validation rejects a *non-empty* key that is not a valid Fernet key.
- `retention_days` validation enforces an **int type**; the `<= 0 disables purge` runtime semantic is preserved (not rejected at load time) per `UNK-03`.
- Construction of `DiagnosticsConfig` elsewhere (e.g. `config_section_builders.py` via `_build_model`) will now run `__post_init__`; valid production defaults (`encryption_key = ""`, integer `retention_days`) pass.

## Design decisions
- **Call validators in `__post_init__` vs. in `_build_model`.** Put validation in `__post_init__` so it fires on *every* construction, not only through the config-build path. `_build_model` wraps the resulting `ValueError` in `ConfigReloadValidationError`, so a bad value still surfaces as a reload/startup error.
- **Alias imports (`as _v_diag_*`) mirroring the existing `_v_app_*`/`_v_mem_*` pattern.** Keeps import style consistent and avoids name clashes.

## Alternatives considered
- **Validate inside `_build_diagnostics_config` only.** Rejected: a `DiagnosticsConfig` built outside the builder (tests, future callers) would skip validation. `__post_init__` guarantees it.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`
### Procedure
1. Import the three new validators with aliases, one `from agent.services.config_validators import (...)` block each, placed after the LLM group (after `validate_llm_temperature as _v_llm_temp`).
2. Add `__post_init__` to `DiagnosticsConfig`.
### Method
- **Imports** — add after line 61 (end of the LLM group):
  ```python
  from agent.services.config_validators import (
      validate_diagnostics_encryption_key as _v_diag_key,
  )
  from agent.services.config_validators import (
      validate_diagnostics_retention_days as _v_diag_retention,
  )
  from agent.services.config_validators import (
      validate_diagnostics_sensitive_fields as _v_diag_fields,
  )
  ```
- **`DiagnosticsConfig.__post_init__`** — add after the `sensitive_fields` field (after line 342), before the class closes:
  ```python
      def __post_init__(self) -> None:
          """Validate diagnostics configuration fields after initialization."""
          _v_diag_key(self)
          _v_diag_retention(self)
          _v_diag_fields(self)
  ```
### Details
- The three validators raise `ValueError` on a bad value; `_build_model` in `config_section_builders.py` catches `ValueError` and re-raises as `ConfigReloadValidationError`, so the error propagates to the caller as a typed reload failure (`AC-3`).
- `retention_days` must remain an `int`; the validator rejects wrong types but allows `<= 0` (purge disabled), preserving the documented runtime semantic.

### Companion test files
- `tests/agent/test_config_dataclasses.py`
  - Procedure: update `DiagnosticsConfig` assertions for the new validated fields / `__post_init__` (assert a non-Fernet key, wrong-typed `retention_days`, and non-frozenset `sensitive_fields` each raise `ValueError` on construction).
  - Validation: `uv run pytest tests/agent/test_config_dataclasses.py` passes.

## Compatibility considerations
Adding `__post_init__` makes `DiagnosticsConfig` construction stricter. Any code constructing it with an invalid key or wrong-typed `retention_days` will now raise. Production defaults are valid, so no caller breakage is expected.

## Security considerations
This is the type-validation half of the fail-closed design: a malformed `[diagnostics]` section can no longer silently disable encryption or bypass the type-coercion policy via a wrong-typed `retention_days`.

## Rollback considerations
Revert the commit (`N/A: revert the commit`).

## Validation plan
- Unit: a non-Fernet `encryption_key` when set raises; wrong-typed `retention_days` raises; non-frozenset/non-string `sensitive_fields` raises; valid defaults construct cleanly.
- Command: `uv run pytest tests/agent/test_config_dataclasses.py`.

## Completion criteria
- `DiagnosticsConfig.__post_init__` calls all three validators.
- Invalid values raise `ValueError` at construction; valid defaults do not.

## Out of Scope
- Defining the validators themselves (`scripts/agent/services/config_validators.py`).
- Routing construction through the validators (`scripts/agent/config_section_builders.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion covers this |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261111-163701_diagstore002_diagnostic-store-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261114-161816_diagstore002_diagnostic-store-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-170132
- **Related target files**: `scripts/agent/config_dataclasses.py`, `tests/agent/test_config_dataclasses.py`
