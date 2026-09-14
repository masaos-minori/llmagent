# Normalize EventBus configuration validation and role-token policy

## Priority
Medium

## Summary
EventBus's cross-field configuration validation, administrator-token semantics, supported per-role token combinations, and unauthorized-response format are currently handled inconsistently within `scripts/eventbus/config.py` and `auth.py`; this issue separates field-level from cross-field validation, defines the administrator role's scope (or removes `admin_token` if unneeded), and centralizes authentication-failure handling into one documented response contract.

## Background
`docs/00_governance_03_issue-and-uncertainty-management.md` `CI-001` ("EventBus process reads configuration directly instead of using ConfigLoader") concerns a related but distinct gap — this issue's scope is the internal structure/policy of EventBus's own configuration validation and token handling, not the ConfigLoader-migration question `CI-001` tracks.

## Problem
Cross-field validation currently runs inside the per-key type-validation loop rather than as a separate pass, making validation error handling harder to reason about and test in isolation. Whether an administrator role exists (and which endpoints it may access) is not clearly defined, and `admin_token` may be present without a corresponding role. Required tokens are validated against what appears to be an arbitrary subset of enabled capabilities rather than a rule tied to which capabilities are actually enabled, and authentication-failure handling is not centralized to one documented HTTP 401 response format.

## Reason for Change
Cross-field validation, administrator-token semantics, supported token combinations, and unauthorized responses are one configuration and authentication contract.

## Implementation Intent
Make every accepted configuration meaningful, fail closed on invalid security settings, and use one error contract — separate from (but coordinated with) `CI-001`'s broader ConfigLoader-migration question.

## Target Files or Areas
- `scripts/eventbus/config.py`
- `tests/eventbus/test_eventbus_config.py`
- `scripts/eventbus/auth.py`
- `config/eventbus.toml`
- `scripts/eventbus/app.py`
- `tests/eventbus/test_eventbus_auth.py`

## Required Changes
- Move cross-field validation outside the per-key type-validation loop.
- Separate field validation from cross-field policy validation.
- Add focused tests for each validation error.
- Define whether an administrator role exists and which endpoints it may access.
- Remove `admin_token` if no administrator role is required.
- Validate required tokens based on enabled capabilities rather than an arbitrary subset.
- Document valid token combinations.
- Centralize authentication failure handling.
- Return one documented HTTP 401 response format.
- Add the appropriate authentication challenge header if required by the API contract.
- Ensure one audit record per failure.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- Each cross-field rule is evaluated once per configuration load.
- Validation behavior is unchanged except for clearer control flow.
- Tests cover missing, empty, wrong-type, unknown, and inconsistent values.
- Every configured token maps to a defined principal role.
- Publisher-only and monitoring-only deployments are either supported or explicitly rejected for documented reasons.
- Configuration tests cover all supported combinations.
- Missing and invalid credentials return the same documented response schema.
- Authentication failures are not processed twice.
- Tests cover every public endpoint.

## Testing Expectations
Add or update unit, integration, and regression tests for all affected boundaries (see Acceptance Criteria). Run the relevant test suites, static analysis, and type checks.

## Documentation Impact
Update active design documents and the known-issue inventory only after implementation evidence is available; note the relationship between this issue's scope and `CI-001` if both remain open.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
Coordinates with `eventbus02` (principal-based authentication) on the unified HTTP 401 response contract — implement in either order but reconcile the response format if both change it. Related to `CI-001`, which this issue does not resolve.

## Unresolved Questions
Whether an administrator role is actually required for EventBus's current operational model, or whether `admin_token` should simply be removed — resolve during this issue's own Required Changes, not before filing it. Non-blocking.

## AI Implementation Instruction
Keep changes scoped to configuration validation structure and token/role policy; do not perform the `CI-001` ConfigLoader migration as part of this issue. Confirm that failure paths do not expose credentials, tokens, payloads, or sensitive configuration. If `eventbus02` has already changed the HTTP 401 response contract, align with it rather than introducing a second format.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102535
- **Related target files**: scripts/eventbus/config.py, tests/eventbus/test_eventbus_config.py, scripts/eventbus/auth.py, config/eventbus.toml, scripts/eventbus/app.py, tests/eventbus/test_eventbus_auth.py
