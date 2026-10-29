# Add generation, optimistic concurrency, and TTL semantics to runtime EventBus authorization

## Priority
Medium

## Summary
Give every effective runtime change to EventBus consumer and topic authorization a unique generation, reject stale concurrent updates with an expected-generation check, support optional TTL for temporary grants that expires through an atomic generation update, and make the loss of runtime overrides at restart explicit and auditable, while keeping fail-closed, one-generation publication.

## Background
Source: `memo-issue.md` item M-03 (original task M-05), re-verified against current source on 2026-10-29.
- Runtime updates are atomic but non-persistent: `POST /admin/topics/authorization` updates `consumer_authorization` and `topic_authorization` at runtime only, with no configuration file write, and the response reports `persistent: false` and `changed` (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md:89`, `Documentation only`; `scripts/eventbus/admin_route.py:149` returns `{"status": "ok", "persistent": False, "changed": changed}`, `Explicit in code`).
- There is no generation concept for authorization: a search for `generation`, `expected_generation`, `ttl`, and `expires` in `scripts/eventbus/` finds only a comment in `scripts/eventbus/auth.py:111` about the "previous generation" remaining in force after a failed build (`Explicit by absence search`). The "generation" in `issues/done/20261028-122206_ebgen001_authz-generation-role-tests.md` is about test fixtures, not a runtime counter.
- The audit record for an effective update currently carries `request_id=""` and `detail="updated"` (`scripts/eventbus/admin_route.py:141-147`); the in-flight plan `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md` adds the request ID, the actor fingerprint, and a mapping or count summary.
- The publish order of an update is being fixed by `plans/done/20261029-091959_eventbus001_admin-authz-publish-order.md` (procedures `implementations/20261029-101422_01_scripts_eventbus_auth.py.md`, `_02_scripts_eventbus_admin_route.py.md`, `_03_tests_eventbus_test_admin_topics_authorization.py.md`, not yet implemented): build the replacement config and principal map first, publish both afterwards.
- A no-op update (no change) publishes nothing and reports `changed: false` (`Verified by test`, `tests/eventbus/test_admin_topics_authorization.py`).

## Problem
Responses and audit records do not identify which authorization generation is in effect, and a concurrent administrative update can silently overwrite an earlier decision. A temporary grant stays active until restart or the next update unless someone removes it manually. Because runtime overrides disappear at restart, an operator cannot tell from the record that a previously granted exception no longer exists.

## Reason for Change
Authorization state is security-sensitive and runtime edits are an operational tool, so conflict-awareness, bounded temporary access, and visible baseline drift reduce the chance of an unnoticed grant or an overwritten decision. Priority is Medium: these are enhancements to an already atomic, fail-closed mechanism with no incident cited, and the audit identity part overlaps work already planned. Not time-sensitive.

## Implementation Intent
Add an authorization generation number with immutable generation metadata to the runtime state published by the admin update, and require an expected generation on mutating updates (or an equivalent optimistic-concurrency mechanism). Return the previous and new generation, changed pair count, effective time, persistence flag, and configuration-baseline hash; record actor principal, request ID, and both generations in the audit record. Add optional TTL for temporary grants, applied as an atomic generation update on expiry, and audit the removal of runtime overrides at restart. Keep one-generation publication and the previous-generation-on-failure behavior from the publish-order work, and build on the audit identity fields instead of adding a second audit schema.

## Target Files or Areas
- `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/audit.py`
- EventBus authorization models (location to be confirmed) and the authorization and concurrency tests under `tests/eventbus/` (`test_admin_topics_authorization.py`, `test_eventbus_auth.py`; others to be confirmed)
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` and the EventBus operations document

## Required Changes
- Add an authorization generation number and immutable generation metadata; require an expected generation (or equivalent) on mutating updates and reject stale concurrent writes without partial change.
- Return previous generation, new generation, changed pair count, effective time, persistence flag, and configuration-baseline hash; keep the existing response fields.
- Record actor principal, request ID, previous generation, and new generation in audit records.
- Support optional TTL for temporary grants, apply expiry as an atomic generation update, and reject invalid TTL values.
- Audit the removal of runtime overrides at restart.
- Add tests for update races, expiry, restart, no-op rejection, and a failed generation rebuild.

## Constraints
- Preserve fail-closed behavior and one-generation publication: a failed rebuild keeps the previous generation fully active.
- Keep the runtime-only persistence contract (no file write) unless an Accepted ADR changes it.
- No audit record may contain token values or other secrets (ADR-013 INV-05).
- Preserve the existing request and response fields (`status`, `persistent`, `changed`) as a compatible extension.

## Acceptance Criteria
- Every effective authorization update produces one unique generation; concurrent stale updates are rejected without partial change.
- Temporary grants expire deterministically and fail closed.
- A failed rebuild preserves the previous generation.
- Restart-related loss of runtime overrides is observable.
- No audit record contains token values or other secrets.

## Testing Expectations
- Deterministic concurrency tests for racing updates with and without the expected generation, expiry tests with an injectable clock, restart tests, and a failed-rebuild test.
- `uv run pytest tests/eventbus`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_docs_consistency.py --domain eventbus`.

## Documentation Impact
Yes. ADR-013 and the EventBus operations document must describe the generation contract, the stale-update rejection, TTL semantics, and restart behavior; operational behavior and failure semantics only (`skills/DESIGN.md` Docs content policy).

## Out of Scope
- Persisting runtime overrides to configuration files.
- Changes to the token-to-role matrix, authentication, or the principal derivation rules.
- Audit identity fields already planned in `ebaudit005`, except for adding the generation fields.
- Unrelated refactoring or formatting-only changes.

## Dependencies
- Depends on the publish-order work landing first: `plans/done/20261029-091959_eventbus001_admin-authz-publish-order.md` and its procedures `implementations/20261029-101422_01_scripts_eventbus_auth.py.md`, `implementations/20261029-101422_02_scripts_eventbus_admin_route.py.md`, `implementations/20261029-101422_03_tests_eventbus_test_admin_topics_authorization.py.md`.
- Depends on `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md` for the audit identity fields; both edit `scripts/eventbus/admin_route.py` and `tests/eventbus/test_admin_topics_authorization.py`, so land that plan first or rebase.
- Related: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md` (a separate, Agent-side generation notion); no ordering required.

## Unresolved Questions
- `Needs confirmation`: whether the expected generation should be required (rejecting clients that omit it) or optional for backward compatibility; the memo allows "an equivalent optimistic-concurrency mechanism".
- `Needs confirmation`: how TTL expiry is triggered (a background task, a lazy check on read, or both) and the maximum TTL.
- `Needs confirmation`: how the configuration-baseline hash is defined and where the restart audit record is emitted.
- `Needs confirmation`: the location of the "EventBus authorization models" named in the memo.

## AI Implementation Instruction
- Read ADR-013, `scripts/eventbus/auth.py`, `scripts/eventbus/admin_route.py`, and the `eventbus001` and `ebaudit005` documents before editing; build on their results instead of duplicating them.
- Preserve the existing response fields and the fail-closed rebuild behavior; do not add persistence.
- Do not log or return token values; stop and report open questions (required versus optional expected generation, TTL triggering) instead of choosing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-104509
- **Related target files**: `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/audit.py`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
