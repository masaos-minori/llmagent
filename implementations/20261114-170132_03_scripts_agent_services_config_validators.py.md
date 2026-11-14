## Goal

Add three validators to `config_validators.py` — `validate_diagnostics_encryption_key`, `validate_diagnostics_retention_days`, `validate_diagnostics_sensitive_fields` — following the existing `validate_<field>(cfg) -> None` pattern, so `DiagnosticsConfig` construction fails with a `ValueError` on a bad value (`REQ-002`, `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `DiagnosticsConfig` (fields `encryption_key: str`, `retention_days: int`, `sensitive_fields: frozenset[str]`) is defined in `scripts/agent/config_dataclasses.py` (its own row) and imported under `TYPE_CHECKING` here for the `cfg:` hints.
- **Interpretation note (caveat):** `REQ-002` says "positive-int `retention_days`", but the Plan's Assumptions, `UNK-03`, and Out-of-Scope all state validation enforces an **int type** and does *not* reject `<= 0` (the "disable purge" semantic is preserved). This procedure implements type-only validation. If maintainer intent is to reject `<= 0` at load, that is a scope change to the Plan, not this workflow.
- An empty `encryption_key` (`""`) is valid; only a non-empty invalid Fernet key is rejected.
- `cryptography` is already a project dependency (used by `diagnostic_store.py`); importing `Fernet` here adds no new dep.

## Design decisions
- **Mirror `validate_memory_retention_days` (line 170).** Same signature `def validate_<field>(cfg: <Config>) -> None:`, raising `ValueError`. Kept next to the memory group for locality.
- **`Fernet` imported at runtime; `DiagnosticsConfig` under `TYPE_CHECKING`.** Preserves the module's no-circular-import contract (`config_dataclasses` imports these validators at runtime).

## Alternatives considered
- **Use `_require_positive` for `retention_days`.** Rejected: `_require_positive` rejects `<= 0`, which would break the preserved "disable purge" semantic. Type-only check is intended.

## Implementation
### Target file
`scripts/agent/services/config_validators.py`
### Procedure
1. Add `DiagnosticsConfig` to the `if TYPE_CHECKING:` import block.
2. Add a runtime `from cryptography.fernet import Fernet` import.
3. Add the three validators after `validate_memory_max_pinned` (line 177).
### Method
- **`TYPE_CHECKING` import** (lines 15-21) — add `DiagnosticsConfig`:
  ```python
  if TYPE_CHECKING:
      from agent.config_dataclasses import (
          ApprovalConfig,
          DiagnosticsConfig,
          LLMConfig,
          MemoryConfig,
          ToolConfig,
      )
  ```
- **Runtime import** — add after line 13 (`from typing import ...`):
  ```python
  from cryptography.fernet import Fernet
  ```
- **Validators** — insert after line 177 (`validate_memory_max_pinned`), before `validate_approval_risk_rules`:
  ```python
  def validate_diagnostics_encryption_key(cfg: DiagnosticsConfig) -> None:
      """Validate encryption_key is a valid Fernet key when configured (empty = disabled)."""
      key = cfg.encryption_key
      if not key:
          return
      try:
          Fernet(key.encode("utf-8"))
      except (ValueError, TypeError) as exc:
          raise ValueError(f"encryption_key is not a valid Fernet key: {exc}") from exc

  def validate_diagnostics_retention_days(cfg: DiagnosticsConfig) -> None:
      """Validate retention_days is an int (<= 0 disables purge; preserved per UNK-03)."""
      if isinstance(cfg.retention_days, bool) or not isinstance(cfg.retention_days, int):
          raise ValueError(
              f"retention_days must be an int, got {type(cfg.retention_days).__name__}"
          )

  def validate_diagnostics_sensitive_fields(cfg: DiagnosticsConfig) -> None:
      """Validate sensitive_fields is a frozenset of strings."""
      fields = cfg.sensitive_fields
      if not isinstance(fields, frozenset) or not all(
          isinstance(field, str) for field in fields
      ):
          raise ValueError("sensitive_fields must be a frozenset of strings")
  ```
### Details
- Each raises `ValueError`; `config_section_builders.py::_build_model` wraps it in `ConfigReloadValidationError`, so a malformed `[diagnostics]` table fails startup/reload (`AC-3`).
- `Fernet(key.encode("utf-8"))` raises `ValueError` for a malformed base64 key; the `try/except` normalizes any exception type to `ValueError`.

### Companion test files
N/A: diagnostics validation tests are added to `tests/agent/test_config_dataclasses.py` (the config-validation test home, companion of `config_dataclasses.py`) per the Plan's Tests section.

## Compatibility considerations
Adding validators changes nothing at runtime until `DiagnosticsConfig.__post_init__` calls them (that wiring is `config_dataclasses.py`'s row). This file only defines functions.

## Security considerations
These are the type-validation controls for the fail-closed design: a wrong-typed `retention_days` or a malformed `encryption_key` is now rejected at config build instead of silently degrading protection.

## Rollback considerations
Revert the commit (`N/A: revert the commit`).

## Validation plan
- Unit: each validator accepts a good value and rejects a bad one (non-Fernet key when set, wrong-typed `retention_days`, non-frozenset/non-string `sensitive_fields`); empty key passes.
- Command: `uv run pytest tests/agent/test_config_dataclasses.py`.

## Completion criteria
- Three validators exist with the `validate_<field>(cfg) -> None` signature.
- Each rejects its bad value with `ValueError`; valid values pass.

## Out of Scope
- Calling the validators from `DiagnosticsConfig.__post_init__` (`scripts/agent/config_dataclasses.py`).
- Routing construction through the validators (`scripts/agent/config_section_builders.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | See Companion test files |
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
- **Related target files**: `scripts/agent/services/config_validators.py`
