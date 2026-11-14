## Goal

Ensure a rejected `DiagnosticsConfig` value surfaces from the config-build path as `ConfigReloadValidationError` (`REQ-002`, `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_build_model` (`scripts/agent/config_section_builders.py`, lines 106-116) wraps any `ValueError` from `model(**fields)` in `ConfigReloadValidationError`.
- `DiagnosticsConfig.__post_init__` (added by the `config_dataclasses.py` row) calls the three validators, which raise `ValueError` on a bad value.
- Therefore constructing `DiagnosticsConfig` through `_build_model` automatically runs the validators and translates failures into `ConfigReloadValidationError`.

## Design decisions
- **Rely on the existing `_build_model` wrapper rather than adding an explicit validator call.** `_build_diagnostics_config` already calls `_build_model(DiagnosticsConfig, ...)` (lines 330-335); adding `__post_init__` (config_dataclasses row) is what activates validation. No new wrapper or duplicate call is needed — this keeps every builder reporting rejections identically.

## Alternatives considered
- **Call the validators explicitly inside `_build_diagnostics_config`.** Rejected: `_build_model` already constructs the dataclass (running `__post_init__`) and wraps the error; an explicit call would duplicate validation and diverge from the other builders' pattern.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`
### Procedure
- Confirm `_build_diagnostics_config` (lines 322-335) constructs `DiagnosticsConfig` exclusively through `_build_model` (lines 330-335). **No body edit is required** once `DiagnosticsConfig.__post_init__` (config_dataclasses row) exists: a bad `encryption_key`, wrong-typed `retention_days`, or invalid `sensitive_fields` raises `ValueError` during `model(**fields)`, which `_build_model` converts to `ConfigReloadValidationError`.
- If a future refactor ever builds `DiagnosticsConfig` outside `_build_model`, route it through `_build_model` so the translation is preserved.
### Method
- No change to lines 322-335. Verify at implementation time that `_build_model` remains the single construction path (grep for `DiagnosticsConfig(` in this file must show only the `_build_model(...)` call).

### Companion test files
N/A.

## Compatibility considerations
None: no behavioral change to the build path other than newly-active validation that was previously absent.

## Security considerations
A malformed `[diagnostics]` table now fails config reload with a named `ConfigReloadValidationError` instead of silently building a weakly-configured `DiagnosticsConfig`.

## Rollback considerations
Revert the commit (`N/A: revert the commit`).

## Validation plan
- Integration: a malformed `[diagnostics]` table (non-Fernet key when set) raises `ConfigReloadValidationError` through the reload path; valid tables build cleanly.
- Command: config-build tests (see the config_dataclasses row) plus `uv run pytest` on the config-build test suite.

## Completion criteria
- `_build_diagnostics_config` constructs `DiagnosticsConfig` only via `_build_model`.
- A rejected value raises `ConfigReloadValidationError`.

## Out of Scope
- Defining the validators (`scripts/agent/services/config_validators.py`).
- Adding `__post_init__` to `DiagnosticsConfig` (`scripts/agent/config_dataclasses.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | No body edit required |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Related target files**: `scripts/agent/config_section_builders.py`
