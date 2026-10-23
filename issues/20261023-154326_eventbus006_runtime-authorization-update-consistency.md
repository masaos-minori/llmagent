# Make runtime authorization updates consistent, explicit about persistence, audited, and fail-closed in tests

## Priority
Medium

## Summary
Treat authorization state as a versioned snapshot: update configuration and principal mappings atomically, state whether an admin update is runtime-only or persistent, audit every effective change, and test authorization through the production path.

## Background
Confirmed against HEAD (adversarial re-verification):
- `update_topics_authorization()` in `scripts/eventbus/admin_route.py` validates the body, swaps `request.app.state.config` with `dataclasses.replace(...)`, and only then calls `_populate_token_maps(config)` as a separate step. The config swap is visible to concurrent requests before the principal map is rebuilt.
- `_populate_token_maps()` in `scripts/eventbus/auth.py` calls `_TOKEN_PRINCIPAL_MAP.clear()` and repopulates the same dict in place. There is a window in which the map is empty (concurrent requests see 401), and if the function raises after the clear (for example `consumer_token is configured but consumer_authorization is missing`), the map is left partially populated while the config has already been replaced. This is a stronger form of the memo's "mixed generation" claim.
- The admin handler never writes the configuration file, so the update is runtime-only, and it never calls `log_privileged_action` (`scripts/eventbus/audit.py`), which `dlq_route.py` and `replay_route.py` do call. It logs only `admin: topics authorization updated`.
- An empty body `{}` produces no replacements and still returns `{"status": "ok"}`.
- Tests accept the wrong code: `tests/eventbus/test_eventbus_ack_endpoint.py:228` and `tests/eventbus/test_eventbus_crash_ack.py:277` assert `status_code in (403, 409)`. `tests/eventbus/test_eventbus_crash_ack.py` assigns `_TOKEN_PRINCIPAL_MAP["consumer-token"] = Principal(...)` directly, and `_TOKEN_PRINCIPAL_MAP` is referenced 82 times across `tests/`.
- `ack_route.py:39` logs `_principal` and `_identity` with `%r` at debug level. `Principal` carries a token fingerprint, not the token, so the exposure is low; the memo's removal request is hygiene.
Aggregated from the memo's runtime authorization update item and the authorization tests/route consistency subset of its M-04.

## Problem
Configuration and principal map swaps are separate operations, so concurrent requests can observe a mixed authorization generation; the change is runtime-only and may be mistaken for durable configuration; security-sensitive changes lack structured audit evidence; authorization tests can pass while consumer authorization is skipped.

## Reason for Change
Security-sensitive updates need one consistent generation, explicit persistence semantics and audit evidence, and a regression in authorization must fail the test suite.

## Implementation Intent
Update configuration and token-principal maps under one lock and generation; decide and document runtime-only versus persistent behavior (return `persistent: false` and describe restart behavior, or write the file atomically); reject or explicitly report empty and no-op updates; emit a redacted privileged-action audit record; build principals through the production config-loader path in tests.

## Target Files or Areas
`scripts/eventbus/admin_route.py`, `scripts/eventbus/auth.py` (`_populate_token_maps`, `resolve_principal`, `require_consumer_identity`), `scripts/eventbus/app.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/audit.py`, tests `tests/eventbus/test_admin_topics_authorization.py`, `test_eventbus_auth.py`, `test_eventbus_consumer_authorization.py`, `test_eventbus_ack_endpoint.py`, `test_eventbus_crash_ack.py`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`.

## Required Changes
- Decide and document runtime-only versus persistent behavior.
- Swap configuration and principal maps atomically under one lock and generation.
- Reject or explicitly report empty and no-op updates; emit a redacted privileged-action audit record for every effective change.
- Require exactly HTTP 403 for unauthorized consumer IDs before database-state checks; unify dependency and handler authorization checks and remove principal `repr` logging.
- Build principals via the production config-loader path in tests and remove direct mutation of private token-map globals.
- Build the new principal map completely first and publish it with one reference swap (no in-place `clear()`), together with the config, so a failed rebuild leaves the previous generation intact.

## Constraints
Token values must stay out of audit records and logs. Public admin API shape changes only where the persistence decision requires it.

## Acceptance Criteria
- Every request observes one authorization generation.
- Restart behavior matches the documented persistence contract and every effective admin change is auditable.
- Empty updates are not reported as successful changes; unauthorized consumer IDs return 403 before delivery-state checks.
- An authorization regression fails the test suite.
- A failed principal-map rebuild leaves the previous generation in force, and no request observes an empty map during an update.

## Testing Expectations
Concurrent admin update and ACK/NACK; two concurrent admin updates; empty and no-op updates; restart after update; audit redaction; all role-token route boundaries; missing and empty authorization mappings. Then ruff and mypy.

## Documentation Impact
Yes: runtime-only versus persistent semantics, the audit record, and the failure behavior of the admin endpoint.

## Out of Scope
Token uniqueness and loader fixes (H-02); startup gate (H-03).

## Dependencies
Depends on H-02 (loader-built principals in tests). No open issue under `issues/` overlaps.

## Unresolved Questions
- Persistent versus runtime-only is an owner decision; the code today is runtime-only without saying so in the response.
- Should an empty or no-op update return 422/400, or 200 with `changed: false`? Needs confirmation against API consumers (none found in `scripts/`).
- The memo's request to unify the dependency and handler authorization checks needs a concrete list of the duplicated checks; not enumerated in this review.

## AI Implementation Instruction
- Read the listed implementation, tests, and design documents before editing; keep changes minimal and do not rewrite unrelated files.
- Preserve the existing public contract unless this issue explicitly names a contract change; an unresolved owner decision is reported, not guessed.
- Do not resolve an implementation defect by changing documentation alone.
- Keep transaction, locking, authorization, durability and fail-closed boundaries explicit.
- Add or update automated tests for every acceptance criterion; do not implement out-of-scope items.

## Traceability
- **Workflow phase**: `issue-creator` (converted from `memo-issue.md`, task `M-01`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-154326
- **Related target files**: `scripts/eventbus/admin_route.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/ack_route.py`
