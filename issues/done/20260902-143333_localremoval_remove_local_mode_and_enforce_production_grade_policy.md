# Remove Local mode and enforce one Production-grade runtime policy

## Priority
High

## Summary
Remove `SecurityProfile.LOCAL` as a supported runtime profile and make the current
Production-grade validation, security, and failure behavior mandatory for every normal
startup, so security behavior is no longer derived from a selectable profile at all.

## Background
ADR-004 (`docs/adr/ADR-004-environment-failure-handling-policy.md`) already requires that
environment names not change Fail-Fast conditions or weaken safety/integrity guarantees
(Decision Group 1), and several narrower sub-tasks toward this goal are already complete:
`required_in_local`/`required_in_production` were unified into a single `required` field
(`issues/done/20260831-173019_adr004_01_mcp_config_failure_model_alignment.md`, superseded and
implemented by `plans/done/20260831-230938_plan.md`), `shell_sandbox_backend="none"`
enforcement is now unconditional
(`issues/done/20260831-192510_adr004_07_shell_mcp_sandbox_production_only_enforcement.md`), and
stale local/dev-mode wording was removed from several Specifications
(`issues/done/20260831-173019_adr004_03_related_docs_local_mode_language.md`,
`issues/done/20260831-185650_adr004_04_remaining_local_dev_mode_language_in_specs.md`). This
issue is the remaining, larger step those did not attempt: `SecurityProfile.LOCAL` and
`security_profile` itself still exist in code (confirmed: `scripts/shared/mcp_config.py`) and
ADR-004's current Decision retains a two-profile model that requires outcome parity between
profiles, rather than removing the profile concept entirely.

## Problem
Retaining `SecurityProfile.LOCAL` and `security_profile`-branching code after establishing
that both profiles must produce identical outcomes leaves dormant paths that could be
reactivated accidentally through configuration drift, environment variables, or later code
changes — the two-profile model is harder to keep in permanent lockstep than a single
unconditional policy.

## Reason for Change
The target architecture has one security posture: safety and integrity failures fail closed,
required-component failures stop startup, and optional-availability failures disable only the
affected capability — none of this needs to be derived from a selectable profile.

## Implementation Intent
Make Production-grade behavior the unconditional default and only supported behavior: remove
`SecurityProfile.LOCAL` and all Local-only conditions, helpers, defaults, imports, environment
overrides, and CLI overrides; remove `security_profile` after migration (or, if a transitional
release is required, accept only `production` and reject every other value); decide and
implement one final `failure_policy` model rather than a declared-but-partially-used field
(tracked as an open sign-off item by `plans/done/20260901-102432_plan.md`'s REQ-003); make
Production configuration validation, tool-definition strictness, routing-drift strictness, and
security lockdown unconditional; require explicit `allowed_tools`, complete tool safety tiers,
approved Shell MCP sandboxing, and explicit resource/command/workflow allowlists; remove
Local-only configuration keys; reject retired profile keys as invalid configuration rather than
silently ignoring them; preserve per-process configuration ownership and
`ConfigLoader.restrict_to()` isolation.

## Target Files or Areas
- `scripts/shared/mcp_config.py`
- `scripts/shared/production_config_validator.py`
- `scripts/shared/config_loader.py`
- `scripts/shared/tool_routing_validation.py`
- `scripts/shared/runtime_tool_registry.py`
- `scripts/agent/startup.py`
- `scripts/agent/config_builders.py`
- `scripts/agent/config_dataclasses.py`
- `scripts/agent/services/mcp_tool_discovery.py`
- `scripts/agent/tool_policy.py`
- `config/agent.toml`
- `config/*_mcp_server.toml`
- Tests covering configuration, startup, routing, discovery, authentication, and tool visibility

Confirm the exact file list with repository-wide searches before editing — this issue's file
list was not re-verified against current source line-by-line at filing time.

## Required Changes
- Search the repository for `SecurityProfile`, `security_profile`, `is_production`, `is_local`, `failure_policy`, `local mode`/`local profile`, `fail-open`, `warn only`, `security_lockdown_enabled`, `tool_definitions_strict`, `routing_drift_strict` before editing; do not remove unrelated uses of "local" (local Git repository, local branch, local filesystem, local RAG, local database, local process, localhost).
- Remove `SecurityProfile.LOCAL` and all Local-only conditions, helpers, defaults, imports, environment overrides, and CLI overrides.
- Remove or restrict `security_profile` to accept only `production`.
- Resolve `failure_policy`'s final fate (implement fully or remove) per the sign-off this issue depends on (see Dependencies) rather than leaving it declared-but-unused.
- Make Production configuration validation, tool-definition strictness, routing-drift strictness, and security lockdown run unconditionally, or remove their switches and preserve the strict behavior directly.
- Remove Local-only configuration keys from files, dataclasses, builders, validators, schemas, environment mappings, examples, and tests; reject retired profile keys as invalid configuration.
- Preserve per-process configuration ownership and `ConfigLoader.restrict_to()` isolation.

## Constraints
- Do not weaken existing allowlists, authentication, approval, routing, workflow, database-integrity, or audit controls.
- Do not create a shared configuration file; preserve `config/agent.toml`, pipeline TOMLs, Event Bus configuration, workflow definitions, and each MCP server's own TOML file.
- Keep configuration-isolation enforcement active for every process.
- Do not leave compatibility aliases that silently restore Local behavior.
- Network binding is handled by a separate follow-up issue (`loopbackonly`, filed alongside this issue) — keep this issue focused on runtime policy and configuration behavior.
- This issue proposes removing a currently-retained architectural concept (`SecurityProfile.LOCAL`) that ADR-004's current Decision does not itself call for removing — see Unresolved Questions.

## Acceptance Criteria
- Local mode cannot be selected through TOML, environment variables, CLI arguments, defaults, or test-only startup paths.
- Every normal startup applies Production-grade validation.
- No Local-only warning, authentication-optional, sandbox-relaxation, or degraded-startup branch remains.
- `required_in_local`/`required_in_production` remain absent from active configuration or code (already true; verify no regression).
- Missing or unknown tool safety tiers, duplicate ownership, routing drift, tool-definition drift, invalid workflow definitions, and database-schema mismatches fail startup.
- Retired profile keys produce clear configuration errors.
- Per-process configuration isolation remains unchanged.
- Existing security and startup tests pass, and new Production-only regression tests are added.

## Testing Expectations
Add focused tests for retired key rejection and removal of Local profile selection; startup
tests for required/optional MCP failures; tests proving optional disabled tools are excluded
from LLM visibility; strict validation tests for tool tiers, ownership, routing, workflow
definitions, authentication, and database schemas. Run the affected unit tests first, then the
complete startup, configuration, routing, discovery, approval, and MCP regression suites.

## Documentation Impact
Update ADR-004, configuration reference, startup documentation, MCP failure policy, security
architecture, and Known Issues in the same change — this is a larger revision than the prior
local/dev-language cleanup issues, since it changes ADR-004's own two-profile Decision, not
just downstream Specifications. Consider whether this warrants a new, superseding ADR rather
than an in-place ADR-004 revision (see `adrprodonly`, filed alongside this issue).

## Out of Scope
- Loopback-only HTTP enforcement and deployment exposure removal (`loopbackonly`).
- Consolidating process-specific configuration files.
- Replacing HTTP transport with stdio or another transport.
- Broad refactoring unrelated to removal of runtime profiles.

## Dependencies
- `issues/done/20260831-173019_adr004_01_mcp_config_failure_model_alignment.md`, `issues/done/20260831-192510_adr004_07_shell_mcp_sandbox_production_only_enforcement.md`, `issues/done/20260831-173019_adr004_03_related_docs_local_mode_language.md`, `issues/done/20260831-185650_adr004_04_remaining_local_dev_mode_language_in_specs.md` — already-completed narrower steps this issue builds on.
- `plans/done/20260901-102432_plan.md` REQ-003 — the `failure_policy` sign-off gate this issue's `failure_policy` resolution depends on.
- `adrprodonly` (filed alongside this issue) — the ADR-level decision of whether to supersede ADR-004 should likely be resolved before or alongside this issue's code changes.

## Unresolved Questions
Whether removing `SecurityProfile.LOCAL` entirely is the intended direction, or whether
ADR-004's current two-profile-with-parity model is the deliberately chosen design — ADR-004's
Decision does not itself call for removing the profile concept, only for equal outcomes across
it. This is an architecture-owner decision, not one this issue's filing resolves; do not
implement removal until that sign-off is obtained.

## AI Implementation Instruction
Do not begin removal until the Unresolved Questions sign-off is obtained. Read all target
files in full before editing; confirm current behavior from code and tests, not only from
design documents. Implement in a sequence that keeps startup valid after each commit:
introduce unconditional validation first, migrate configuration, update callers and tests,
then delete retired profile fields and branches last. Do not broaden scope when an unrelated
inconsistency is found; report it as a dependency or separate issue.
