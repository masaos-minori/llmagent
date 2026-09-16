# Normalize configuration isolation, schema validation, and loader contracts

## Priority
Medium

## Summary
Process-level configuration file restrictions (`restrict_to()`), loader default documentation, exception contracts, duplicated validation-result types, and inconsistent Agent/RAG configuration shapes currently all bear on the same configuration-authority boundary; this issue requires `restrict_to()` initialization before production config loading, corrects loader documentation, unifies the duplicated result type, and defines one canonical configuration shape validated against one root schema.

## Background
N/A: covered by Summary — this is a direct code-level finding across the shared config loader/validator path, not derived from a prior design decision document.

## Problem
Process-level `restrict_to()` initialization is not confirmed mandatory before production configuration loading, and the allowed-file set may be broadenable after initialization, weakening the process-isolation guarantee it exists to provide. `load_all()`'s strict-default behavior may not match its documentation. `ConfigValidationResult` appears to be defined more than once, and Agent/RAG configuration validators may consume differently-shaped (nested vs. flat) configuration with valid keys derived inconsistently (mixed dataclass introspection and manual additions) rather than from one root schema.

## Reason for Change
Process file restrictions, loader defaults, exception contracts, duplicated validation result types, and inconsistent configuration shapes all affect the same configuration authority boundary.

## Implementation Intent
Require immutable process-level configuration ownership and validate one canonical root configuration shape with one result and exception contract.

## Target Files or Areas
- `scripts/shared/config_loader.py`
- `scripts/shared/config_errors.py`
- `scripts/shared/config_validator.py`
- `scripts/shared/production_config_validator.py`
- `scripts/agent/config_dataclasses.py`
- `tests/shared/test_config_loader.py`
- `tests/shared/test_production_config_validator.py`

## Required Changes
- Require process-level `restrict_to()` initialization before production configuration loading.
- Reject later changes to the allowed-file set, except an explicitly test-only reset mechanism.
- Correct the `load_all()` strict-default documentation.
- Document all loader exception types, including configuration-policy permission failures.
- Unify duplicated `ConfigValidationResult` definitions.
- Define one canonical nested or flat shape for Agent and RAG configuration.
- Derive valid keys from one root schema rather than mixed dataclass introspection and manual additions.
- Add integration tests using the actual production configuration shape.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- Production configuration cannot be loaded before process restrictions are established.
- The restriction set cannot be broadened after initialization.
- Loader documentation matches actual defaults and exception types.
- RAG and production validators consume the same canonical configuration shape.
- Unknown keys are rejected at the correct namespace level.

## Testing Expectations
Add or update automated tests for every modified behavior and failure path (see Acceptance Criteria and Required Changes' test items), including integration tests using the actual production configuration shape. Run unit tests, integration tests, static analysis, and type checks.

## Documentation Impact
Update ADRs and the active known-issue inventory only after executable verification is available.

## Out of Scope
- Unrelated refactoring outside the design and implementation boundary described in this issue.

## Dependencies
Related to `mcpagent03` (production security profiles) via `production_config_validator.py`, but independently implementable — coordinate if both touch the same validation entry point in the same session.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Keep changes scoped to configuration loading/validation/isolation contracts; do not rewrite unrelated Agent or RAG business logic beyond what one canonical configuration shape requires. Coordinate with `mcpagent03` if both are implemented in the same session, since both touch `production_config_validator.py`. Verify that logs and tool results do not expose credentials, payloads, raw response bodies, or sensitive configuration.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-103255
- **Related target files**: scripts/shared/config_loader.py, scripts/shared/config_errors.py, scripts/shared/config_validator.py, scripts/shared/production_config_validator.py, scripts/agent/config_dataclasses.py, tests/shared/test_config_loader.py, tests/shared/test_production_config_validator.py
