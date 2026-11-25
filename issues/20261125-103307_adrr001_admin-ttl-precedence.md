# Validate the admin authorization request before the generation comparison

## Priority
High

## Summary
`POST /admin/topics/authorization` compares `expected_generation` before it validates `ttl_seconds`, which contradicts ADR-013 Decision Detail 13, and it accepts a body that carries only concurrency or TTL metadata as a successful no-op. Align the route with the ADR and make the accepted request shape unambiguous.

## Background
Verified against master on 2026-11-25 (source: local note `memo-issue.md`, issues 001 and 008):
- Confirmed: the generation comparison returns HTTP 409 at `scripts/eventbus/admin_route.py:125`, and `ttl_seconds` type and range validation runs after it (`:136-150`). ADR-013 Decision Detail 13 (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md:107`) says an invalid `ttl_seconds` is rejected with HTTP 422 before any state is touched and "before the `expected_generation` comparison is acted on". A stale request with an invalid TTL therefore returns 409 instead of 422.
- Confirmed: `consumer_authorization` is optional (`admin_route.py:102`); a body with only `expected_generation`, or `expected_generation` plus `ttl_seconds`, falls through to the `changed=false` no-op response (`:166-178`).
- Not found in tests: no test combines a stale generation with an invalid TTL. Existing tests cover a stale generation on a no-op body (409, `tests/eventbus/test_admin_topics_authorization.py:275`) and invalid TTL values with a current generation (422, `:343`).
- The API reference file the note asked for exists: `docs/24_eventbus/eventbus_02_api-reference-index.md` (the admin endpoint is described at line 46).
- Not decided by the ADR: whether a metadata-only body must be rejected. The ADR requires `expected_generation` but does not say `consumer_authorization` is required, so that part is a contract decision (see Unresolved Questions).

## Problem
The ordering of checks in the admin route differs from the accepted ADR decision, and a request with no update payload can be reported as a successful update.

## Reason for Change
The route is a privileged API whose response codes clients and tests rely on; a documented precedence that the code does not follow makes the contract untrustworthy.

## Implementation Intent
Keep the accepted ADR-013 decision: authentication and Admin authorization first, structural and TTL validation next, generation-conflict handling last. Read the in-force generation only to obtain `authz_max_ttl_seconds` for TTL validation. Reserve 409 for structurally valid requests with a stale generation.

## Target Files or Areas
- `scripts/eventbus/admin_route.py`
- `tests/eventbus/test_admin_topics_authorization.py`
- `docs/24_eventbus/eventbus_02_api-reference-index.md`
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` (only if the metadata-only decision needs wording)

## Required Changes
- Move TTL type and range validation before the generation-mismatch response.
- Reject a metadata-only body (no `consumer_authorization`) with HTTP 422, once the maintainer confirms that contract; keep an explicitly present but unchanged `consumer_authorization` as 200 with `changed=false`.
- Add the missing tests and update the API reference wording.

## Constraints
- Do not change the ADR-013 decision; authentication (401) and role (403) precedence stay as they are.
- Every rejected request must leave generation identity, config, principals, expiries, and audit output unchanged.

## Acceptance Criteria
- A stale generation with an invalid TTL (`0`, `-1`, over the limit, a string, a boolean) returns 422.
- A stale generation with a valid TTL returns 409 with `error="generation_conflict"`.
- A metadata-only body returns 422 (after the contract decision).
- An unchanged explicit mapping returns 200 with `changed=false`.
- Unauthenticated invalid requests return 401 and authenticated non-Admin requests return 403.

## Testing Expectations
Parametrized stale-generation plus invalid-TTL tests, a stale-generation plus valid-TTL regression test, metadata-only body tests, authentication and role precedence tests, and state-identity and no-audit assertions for every rejection path; focused tests first, then the ADR and documentation checks.

## Documentation Impact
Update the API reference for the check order and the metadata-only rejection; no ADR decision changes.

## Out of Scope
- Publication atomicity (issues/20261125-103308_adrr002_authz-publication-invariant.md) and ADR-013 matrix coverage (issues/20261125-103309_adrr003_adr013-invariant-coverage.md).

## Dependencies
- Blocks issues/20261125-103309_adrr003_adr013-invariant-coverage.md (final test node names).
- No other open issue overlaps `admin_route.py`.

## Unresolved Questions
- `不明`: whether the maintainer wants a metadata-only body rejected (the ADR is silent; the note assumes yes).

## AI Implementation Instruction
Change only the check order and the metadata-only handling; do not alter generation publication; stop and ask if the metadata-only decision is not confirmed.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-103307
- **Related target files**: `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`, `docs/24_eventbus/eventbus_02_api-reference-index.md`
