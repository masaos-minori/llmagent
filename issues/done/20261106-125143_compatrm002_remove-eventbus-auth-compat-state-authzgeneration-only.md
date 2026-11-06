# Remove the EventBus authentication compatibility state and standardize generation-based authorization

## Priority
High

## Summary
Remove `_TOKEN_PRINCIPAL_MAP`, `principal_map()`, and the old token-map population entry point so that `AuthzGeneration` is the only authentication and authorization state exposed to production code and tests. Production alias removal, test-helper redesign, authentication-test updates, function renaming, documentation correction, and removed-name protection are one issue because they must be made atomically.

## Background
Initiative issue H-2 of `memo-issue.md`. Verified 2026-11-06: `_TOKEN_PRINCIPAL_MAP` appears in about 11 files and `_populate_token_maps` in about 12 files under `scripts/`, `tests/`, `tools/`, and `docs/`; `principal_map` is defined in `tests/eventbus/eventbus_helpers.py`. `_TOKEN_PRINCIPAL_MAP` is an explicitly identified compatibility alias for `AuthzGeneration.principals`; production principal resolution and several tests still reference or mutate it, and the helper `principal_map()` can fall back to it when no generation is available.

## Problem
Two apparent sources of truth for principal state weaken the immutable-generation design, let tests bypass the publication boundary, and make atomic authorization updates harder to reason about.

## Reason for Change
A single published, complete, immutable generation is the design intent; the alias contradicts it and is the kind of compatibility surface the initiative removes.

## Implementation Intent
Make one published `AuthzGeneration` the complete and exclusive source of authentication and authorization state: every reader observes either the previous complete generation or the next complete generation, and no caller reads or mutates a parallel module-level principal dictionary.

## Target Files or Areas
`scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/config.py`, `tests/eventbus/eventbus_helpers.py`, the EventBus authentication and authorization tests, any authentication design document that describes the compatibility alias, and every reference to `_TOKEN_PRINCIPAL_MAP`, `_populate_token_maps`, and `principal_map`.

## Required Changes
- Delete `_TOKEN_PRINCIPAL_MAP` from `eventbus/auth.py`; change `resolve_principal()` to read `current_generation().principals`; remove compatibility-alias rebinding from `publish_generation()`.
- Rename `_populate_token_maps()` to a name that reflects generation construction and publication (for example `build_and_publish_generation()`); keep no alias for the old name.
- Delete `principal_map()` from `tests/eventbus/eventbus_helpers.py`; replace direct global-dictionary mutation with explicit `AuthzGeneration` construction and publication; make test setup and teardown restore a complete generation; remove tests that assert object identity between `generation.principals` and `_TOKEN_PRINCIPAL_MAP`.
- Update authentication and authorization documentation.
- Add removed-name checks for `_TOKEN_PRINCIPAL_MAP`, `principal_map`, and `_populate_token_maps` (the checker configuration itself is finalized in the policy-enforcement issue).

## Constraints
- `current_generation()` fails closed when no valid generation has been published.
- A failed generation construction does not replace the current valid generation.
- Publication stays atomic; readers never observe an empty or partially built principal map.
- Authorization decisions use roles, consumer IDs, and topic bindings from the same generation snapshot.
- Raw bearer tokens never appear in logs or assertion messages.

The common policy of the initiative applies:

Common policy (shared by all four issues of this initiative):

1. Support only the current database schema, API, import path, and authentication model.
2. Do not provide automatic database migration, version stamping, compatibility aliases, re-export facades, or deprecated call signatures.
3. Reject incompatible existing databases before mutation.
4. Do not automatically delete an incompatible database.
5. Permit an operator to archive an incompatible database and recreate it manually.
6. Preserve rotation, archive validation, and supported corruption recovery: they protect current data and are not backward-compatibility features.
7. Prevent deleted symbols, modules, imports, and specifications from being reintroduced through CI and pre-commit checks.

## Acceptance Criteria
- [ ] `_TOKEN_PRINCIPAL_MAP`, `principal_map()`, and `_populate_token_maps` have no definition or reference.
- [ ] All authentication readers obtain principal state from `current_generation()`, and `publish_generation()` publishes one complete immutable generation.
- [ ] Tests do not mutate a global principal dictionary.
- [ ] A failed rebuild leaves the previous generation active, and concurrent readers never observe a partial generation.
- [ ] Duplicate-token validation stays fail closed; consumer ID and topic authorization stay enforced.
- [ ] Raw bearer tokens are excluded from logs.
- [ ] The compatibility checker rejects reintroduction of the removed names.

## Testing Expectations
Valid-token and invalid-token tests; duplicate-token rejection; one-role-per-token behavior; consumer ID and topic authorization; failed generation reconstruction; concurrent readers during generation replacement; an audit-log test for token leakage; the full EventBus authentication and authorization test suite.

## Documentation Impact
Yes: the authentication design documents that describe the compatibility alias (state that `AuthzGeneration` is the only source of authentication state). Use `docs/00_index.md` "Document References by Task" to find them.

## Out of Scope
Changing the EventBus role model, token storage or distribution, adding token refresh protocols, and preserving aliases for external callers.

## Dependencies
Can run in parallel with `issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md`. Complete before the policy-enforcement issue `issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md`.

## Unresolved Questions
- The final name of the renamed generation-building function (`build_and_publish_generation()` is a suggestion).

## AI Implementation Instruction
Make the production and test changes in one change so no intermediate state has two sources of truth. Keep the publication boundary atomic and never log raw tokens.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-125143
- **Related target files**: `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/config.py`, `tests/eventbus/eventbus_helpers.py`

## Adversarial Validation

Validated against current source on 2026-11-07.

- `_TOKEN_PRINCIPAL_MAP` is referenced in 11 files and `_populate_token_maps` in 12 files under `scripts/`, `tests/`, `tools/`, `docs/` (excl. `done/`). — Evidence: `Operationally observed` (rg) — Confidence: High
- `principal_map()` is defined in `tests/eventbus/eventbus_helpers.py`; `AuthzGeneration` and `current_generation()` live in `scripts/eventbus/auth.py`. — Evidence: `Explicit in code` — Confidence: High
- Framed correctly as one atomic change: production alias removal, test-helper redesign, authentication-test updates, function rename, documentation correction, and removed-name protection must land together or an intermediate state has two sources of truth.
- No factual conflict found. The only Unresolved Question (final name of the renamed generation-building function) is appropriately left open.

Verdict: accepted as filed.

## Content Analysis

- Type: implementation (removes production compat alias `_TOKEN_PRINCIPAL_MAP`, redesigns the test helper, renames the generation-building function).
- Pipeline path: issue -> plan -> implementation procedure -> code. Owner: engineer.
- Scope: `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/config.py`, `tests/eventbus/eventbus_helpers.py`.
- Dependency: second of the four (initiative H-2); parallel with `001`/`003`; must land atomically with `004`'s removed-name protection.
- Open item before planning: final name of the renamed generation-building function.
