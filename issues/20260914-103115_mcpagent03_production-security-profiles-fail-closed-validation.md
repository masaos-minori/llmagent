# Unify production security profiles and fail-closed tool-safety validation

## Priority
High

## Summary
`production_config_validator.py` risks silently skipping safety-critical checks when the authoritative tool registry is unavailable (via a broad exception-to-`None` fallback) and may validate against an undefined or inconsistent set of supported security profiles; this issue requires an authoritative tool set for production validation and defines one canonical, enum-backed security-profile model so safety checks are never skipped due to ambiguity or registry failure.

## Background
`docs/adr/ADR-004-environment-failure-handling-policy.md` establishes fail-closed environment-failure handling as an architectural requirement — this issue applies that same fail-closed principle to production tool-safety validation specifically.

## Problem
Tool resolution in production validation currently has a broad exception-to-`None` fallback, meaning a registry import failure or other unexpected exception can silently disable authoritative-tool-set checking rather than failing the validation. Separately, the set of supported security profiles referenced across configuration comments, enum values, and validator inputs may not agree, so an unknown or unsupported profile could be silently accepted or misapplied instead of rejected.

## Reason for Change
Security-profile inconsistency and registry-unavailable validation skipping affect the same production safety decision. The validator cannot apply profile-specific guarantees if profiles are undefined or if the authoritative tool set is unavailable and silently ignored.

## Implementation Intent
Define one supported security-profile model and require an authoritative tool set for production validation. Safety-critical checks must never be skipped because of profile ambiguity or registry failure.

## Target Files or Areas
- `scripts/shared/production_config_validator.py`
- `scripts/shared/tool_registry.py`
- `scripts/agent/startup.py` and related `scripts/agent/startup_*.py` files (Unknown: source review cited `scripts/agent/startup/`, which does not exist as a directory — confirm the exact startup-pipeline file(s) that must inject the authoritative tool set before implementation)
- `tests/shared/test_production_config_validator.py`
- `scripts/shared/mcp_config.py`
- `scripts/agent/config_dataclasses.py`
- `docs/adr/ADR-004-environment-failure-handling-policy.md`

## Required Changes
- Remove the broad exception-to-`None` fallback from tool resolution.
- Inject the authoritative known-tool set into production validation from the startup pipeline.
- Convert registry initialization and duplicate-registration failures into validation errors.
- Catch only documented exception types where recovery is defined.
- Add tests for registry import failure, duplicate ownership, uninitialized registry, and explicit `known_tools` injection.
- Select the canonical set of supported security profiles.
- Remove unsupported profile documentation and parameters, or add the missing enum values and validation policies.
- Reject unknown profiles explicitly.
- Identify checks that always fail closed regardless of profile.
- Apply profile-specific error and warning behavior only where the design permits relaxation.
- Add parameterized tests for every supported and unsupported profile.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- Production validation cannot succeed without an authoritative tool set.
- Registry failures produce actionable validation errors.
- Duplicate registrations prevent startup.
- No security check is silently skipped because of an unexpected exception.
- Configuration comments, enum values, validator inputs, and runtime behavior list the same profiles.
- Unknown profiles fail during configuration construction.
- Safety-critical checks remain fail closed in every profile.
- Profile-specific tests prove the intended differences.

## Testing Expectations
Add or update automated tests for every modified behavior and failure path (see Acceptance Criteria and Required Changes' test items). Run unit tests, integration tests, static analysis, and type checks.

## Documentation Impact
Update `docs/adr/ADR-004-environment-failure-handling-policy.md` and the active known-issue inventory only after executable verification is available.

## Out of Scope
- Unrelated refactoring outside the design and implementation boundary described in this issue.

## Dependencies
Shares the startup pipeline with `mcpagent01` (MCP server availability/startup publication) for injecting the authoritative tool set — coordinate ordering to avoid duplicating startup-sequencing logic.

## Unresolved Questions
Exact file(s) among `scripts/agent/startup_*.py` that correspond to the source review's `scripts/agent/startup/` reference — confirm during implementation. Non-blocking.

## AI Implementation Instruction
Keep changes scoped to production validation's tool-resolution fallback and security-profile model; do not modify unrelated startup sequencing beyond what injecting the authoritative tool set requires. Confirm the exact startup file target (see Unresolved Questions) before editing rather than guessing. Verify that logs and tool results do not expose credentials, payloads, raw response bodies, or sensitive configuration.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-103115
- **Related target files**: scripts/shared/production_config_validator.py, scripts/shared/tool_registry.py, scripts/agent/startup.py, tests/shared/test_production_config_validator.py, scripts/shared/mcp_config.py, scripts/agent/config_dataclasses.py, docs/adr/ADR-004-environment-failure-handling-policy.md
