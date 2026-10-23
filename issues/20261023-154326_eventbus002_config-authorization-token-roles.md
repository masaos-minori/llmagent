# Fix EventBus configuration loading and enforce unambiguous token-role bindings

## Priority
High

## Summary
Pass the validated `consumer_authorization` and `topic_authorization` mappings through the file-loading path into `EventBusConfig`, and reject duplicate non-empty token values before principal maps are built.

## Background
Confirmed against HEAD (adversarial re-verification):
- `load_config()` in `scripts/eventbus/config.py` builds `EventBusConfig(...)` without `consumer_authorization` or `topic_authorization`, although both are listed in `_KNOWN_CONFIG_KEYS` and validated in `EventBusConfig.__post_init__`. A TOML value is accepted as a known key and then silently dropped. Dataclass-built configs in tests do not exercise this path.
- The defect is latent in the shipped configuration: `config/eventbus.toml` sets `auth_token` only; every per-role token is empty and no authorization table is present. It surfaces when an operator sets `consumer_token` and adds the mapping: `_populate_token_maps()` in `scripts/eventbus/auth.py` then raises `consumer_token is configured but consumer_authorization is missing`, because the loaded config has `consumer_authorization = None`.
- `_validate_cross_field()` (`_validate_token_combinations`, `_validate_deployment_mode`) has no duplicate-token check. In `_populate_token_maps()` a per-role token equal to an existing map key gets `existing.roles | {role}`. A `consumer_token` equal to `auth_token` therefore yields a principal with the control-plane roles plus CONSUMER, which contradicts the rule recorded in `auth.py` that the shared `auth_token` never holds the CONSUMER role (ADR-013 INV-02/INV-07). `admin_token` equal to another token silently overwrites that entry.
Aggregated from the memo's preserve-authorization-mappings item and the duplicate-token subset of its M-04.

## Problem
A valid TOML file loses its authorization mappings before principal generation, so a configured consumer token can fail startup because its required mapping disappears. Duplicate non-empty token values are not rejected, contradicting the documented one-role-per-token model.

## Reason for Change
Fail-closed authorization requires configuration ambiguity to be rejected before the server starts, and the production file-loading path must be the one tests exercise.

## Implementation Intent
Make `load_config()` the authoritative path: preserve validated mappings, normalize TOML arrays to the runtime collection types the authorization layer expects, and reject token-value collisions (naming the colliding fields, never the values) before token maps are built. Remove collision-driven union/overwrite behavior from token-map construction.

## Target Files or Areas
`scripts/eventbus/config.py`, `scripts/eventbus/auth.py`, `config/eventbus.toml` (documented example only, no secrets), `shared/config_loader.py`, `shared/config_utils.py` (`resolve_env_ref`), tests `tests/eventbus/test_eventbus_config.py`, `test_eventbus_auth.py`, `test_eventbus_consumer_authorization.py`, `test_admin_topics_authorization.py`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`.

## Required Changes
- Pass `consumer_authorization` and `topic_authorization` to `EventBusConfig` in `load_config()` and normalize their types.
- Require uniqueness across every non-empty token field, including the shared control-plane token and per-role tokens; report colliding field names without logging values.
- Remove role union and overwrite behavior from `_populate_token_maps()`.
- Keep missing and empty mapping semantics distinct: missing is invalid when required, empty remains deny-all.
- Add file-load-through-startup integration tests.

## Constraints
`${ENV:VAR}` token references must still resolve before validation. Token values must never appear in logs or error messages.

## Acceptance Criteria
- A valid TOML mapping appears in the generated consumer principal and a consumer token with a valid mapping starts successfully.
- A missing required mapping fails with an actionable message; an empty mapping remains deny-all.
- Any duplicate token value is rejected before startup and each accepted token has exactly the documented role set.

## Testing Expectations
Valid consumer and topic mappings from a real TOML file; missing mapping; empty mapping; environment-reference token values; every relevant pair of token fields with the same value; distinct-token configuration; startup through the normal application lifespan. Then ruff and mypy.

## Documentation Impact
Yes if token rules are documented: one role per token, token uniqueness, mapping semantics (missing versus empty), and the token distribution and rotation policy.

## Out of Scope
Runtime authorization updates through the admin API (the M-01 issue); schema validation and deployment gates (H-03).

## Dependencies
No open issue under `issues/` overlaps. Related memo tasks: M-01 (runtime authorization updates should use the same loader-built principals) and H-03 (startup preflight reuses this validation).

## Unresolved Questions
- Should two tokens with the same value be a hard configuration error in every deployment? Assumed yes by the fail-closed rule; the token distribution and rotation policy is not in the repository evidence reviewed. Needs confirmation.
- Should the rejection also cover `auth_token` versus `admin_token` (identical control-plane roles today, so currently harmless)? Assumed yes for uniformity.
- Is a TOML `topic_authorization` value stored as a list normalized to `set` (the dataclass annotation says `dict[str, set[str]]`) or kept as a list (the validators accept both)? Decide with the type annotation.

## AI Implementation Instruction
- Read the listed implementation, tests, and design documents before editing; keep changes minimal and do not rewrite unrelated files.
- Preserve the existing public contract unless this issue explicitly names a contract change; an unresolved owner decision is reported, not guessed.
- Do not resolve an implementation defect by changing documentation alone.
- Keep transaction, locking, authorization, durability and fail-closed boundaries explicit.
- Add or update automated tests for every acceptance criterion; do not implement out-of-scope items.

## Traceability
- **Workflow phase**: `issue-creator` (converted from `memo-issue.md`, task `H-02`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-154326
- **Related target files**: `scripts/eventbus/config.py`, `scripts/eventbus/auth.py`, `config/eventbus.toml`
