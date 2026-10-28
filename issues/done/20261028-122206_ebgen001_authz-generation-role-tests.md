# Publish EventBus authorization as one immutable generation and remove obsolete all-role token tests

## Priority
Medium

## Summary
Make the runtime authorization update publish the configuration and the derived token-to-principal map as one unit, and remove authorization tests that still model the shared and admin tokens as all-role credentials, which production configuration can no longer create.

## Background
Source: `memo-issue.md` item 01, re-verified against current source on 2026-10-28.

- `update_topics_authorization()` in `scripts/eventbus/admin_route.py` builds the replacement config with `dataclasses.replace`, assigns it to `request.app.state.config`, and only then calls `_populate_token_maps(config)`. The two assignments are separate statements. `Explicit in code`.
- `_populate_token_maps()` in `scripts/eventbus/auth.py` already builds the new principal map into a local dict and publishes it with one assignment. The config and the map are two independently published objects. `Explicit in code`.
- No `await` sits between the config assignment and the map publication, and the config replacement is validated by `EventBusConfig.__post_init__` before it is assigned. A concurrent request therefore cannot interleave on the event loop, and the one failure `_populate_token_maps` raises with a valid config (a `consumer_token` without `consumer_authorization`) is rejected at startup. Whether a mixed generation is observable from a worker thread, and whether the failure path is reachable, is `Needs confirmation`.
- Production gives the shared `auth_token` and `admin_token` only the control-plane roles (`_CONTROL_PLANE_ROLES`: operator, monitoring, admin). `tests/eventbus/test_eventbus_auth.py` still contains `test_admin_token_grants_all_roles` and `test_shared_token_grants_all_roles_for_backward_compat`, which inject a `Principal` with `roles=frozenset(Role)` into `_TOKEN_PRINCIPAL_MAP` and assert it, so they exercise a principal no configuration can produce. The current model is asserted by `test_shared_and_admin_tokens_have_no_consumer_bypass`. `Explicit in code`.
- Prior work: `issues/done/20261007-154015_ebauthz01_fix-eventbus-authorization-model-for-consumer-tokens.md` and the archived `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (procedures pending) change the principal model and the same test file.

## Problem
- Authorization state is two objects published at two points; the update path has no single generation and no serialization against a second admin update.
- Two tests assert impossible role assignments, so the suite documents two role models and can hide a regression in the real one.

## Reason for Change
The test drift misleads a reader about the security contract now. The publication hardening removes a dependence on event-loop scheduling rather than fixing a demonstrated fault, so it is not time-sensitive; severity is Medium (testability and an ambiguous contract), not High.

## Implementation Intent
Keep one immutable authorization generation (configuration plus principal map) and swap it in one assignment, building the replacement completely before publishing so a failure leaves the previous generation active. Build test principals through `_populate_token_maps()` so tests can only describe principals that production can create. Keep the runtime-only persistence contract and the deny-all semantics unchanged.

## Target Files or Areas
- `scripts/eventbus/admin_route.py`
- `scripts/eventbus/auth.py`
- `scripts/eventbus/app.py` (where the generation is read)
- `tests/eventbus/test_eventbus_auth.py`
- `tests/eventbus/test_admin_topics_authorization.py`
- the EventBus authorization ADR (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`) for the role matrix, if it needs a pointer only

## Required Changes
- Build the replacement config and principal map without publishing either, then publish both in one assignment (or one generation object), preserving the previous generation on any failure.
- Serialize concurrent admin updates or reject a conflicting one deterministically.
- Remove `test_admin_token_grants_all_roles` and `test_shared_token_grants_all_roles_for_backward_compat`; add role-matrix tests that build principals through `_populate_token_maps()`.
- State one canonical token-to-role matrix and use it in the tests and the production comments.
- Keep the fail-closed behavior for a missing or empty consumer authorization mapping.

## Constraints
- Preserve the runtime-only update contract (`persistent: false`) and the no-op detection (a no-op publishes nothing).
- Do not change token roles or the credential configuration format.
- ADR edits must pass `tools/check_adr_preservation.py`.

## Acceptance Criteria
- Configuration and principal map change together; a failed update leaves both unchanged.
- No test expects a role assignment that production configuration cannot create.
- Shared and admin tokens receive exactly operator, monitoring and admin; publisher, consumer, operator and monitoring tokens receive exactly their own role.
- Two concurrent admin updates are serialized or one is rejected deterministically.
- The endpoint tests exercise the real admin route, not only `_populate_token_maps()`.

## Testing Expectations
- A failed admin update leaves config and principal map unchanged.
- A no-op update publishes nothing.
- Role-matrix tests for all five token fields, and a duplicate-token case that fails closed without echoing token values.
- Concurrency test for two admin updates using explicit synchronization (no sleeps).
- `uv run pytest tests/eventbus`, mypy and ruff on changed files.

## Documentation Impact
Small: record the role matrix and the generation semantics where the ADR describes the runtime update (Implementation Notes only; no Decision or Invariant change).

## Out of Scope
- Pairwise (consumer_id, topic) grants (the ebauth001 plan).
- Persisting runtime updates to the config file.
- Token rotation.

## Dependencies
- Coordinate with the archived `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md`: its pending procedures (`implementations/20261028-114911_01_scripts_eventbus_auth.py.md`, `implementations/20261028-114911_06_tests_eventbus_test_eventbus_auth.py.md`, `implementations/20261028-114911_11_tests_eventbus_test_admin_topics_authorization.py.md`) replace the `Principal` fields in the same files. Implement after them, or rebase carefully; the two removed tests also construct `Principal` with the old fields.

## Unresolved Questions
- Is a mixed generation observable today (for example from a worker thread reading `app.state.config`)? `Needs confirmation`: if not, this part is hardening only.
- Is the failure path of `_populate_token_maps` after a valid config reachable? `Needs confirmation`.

## AI Implementation Instruction
Keep the change to authorization publication and its tests. Do not change role definitions or the pairwise model. Re-read `auth.py` and `test_eventbus_auth.py` first, because the pairwise procedures change both. If the generation object would change a public interface, stop and report.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261028-122206
- **Related target files**: `scripts/eventbus/admin_route.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_admin_topics_authorization.py`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
