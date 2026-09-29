# ACK endpoint authorization bypassed when principal.allowed_consumer_ids is None

## Priority
High

## Summary
`tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint::test_ack_event_principal_ownership_validation` fails: an ACK request for a `consumer_id` not owned by the calling principal returns `200 OK` instead of the expected `403`/`409`. Root-cause evidence points to `_principal.allowed_consumer_ids` being `None` at authorization-check time in `scripts/eventbus/ack_route.py`, even though the test's fixture explicitly constructs a `Principal` with `allowed_consumer_ids=frozenset({"consumer-A"})`.

## Background
Discovered as a pre-existing, unrelated full-suite failure while syncing an unrelated documentation change (NC-027 closure) via `git-commit-and-sync`. Confirmed to reproduce identically on `origin/master` alone (verified in an isolated worktree with no other changes applied), so this is not a regression introduced by that unrelated work — it already existed upstream.

`scripts/eventbus/auth.py`'s own comment (line 95) states the current role-based principal-resolution path "Replaces the old `_TOKEN_CONSUMER_MAP` / `_TOKEN_TOPIC_MAP` / `_TOKEN_ROLE_MAP`" scheme, but the failing test's inline comment (`tests/eventbus/test_eventbus_ack_endpoint.py:217`) still references `_TOKEN_CONSUMER_MAP` as the source of `allowed_consumer_ids` — suggesting the auth refactor and this test/fixture may have drifted apart.

## Problem
In `scripts/eventbus/ack_route.py`'s `_do_ack()`, the ownership check is:
```
if (
    _principal
    and _principal.allowed_consumer_ids
    and consumer_id not in _principal.allowed_consumer_ids
):
    raise HTTPException(status_code=403, ...)
```
Because `allowed_consumer_ids` is falsy (`None`) when this check runs, the entire condition short-circuits to `False` and no authorization error is raised regardless of `consumer_id` — the request proceeds to create a delivery record and returns `200`. The debug log captured during the failing test run confirms this directly: `_principal=Principal(roles=frozenset({<Role.CONSUMER: 'consumer'>}), allowed_consumer_ids=None, ...)`, while the test's `principal_client` fixture (`tests/eventbus/test_eventbus_ack_endpoint.py:73`) constructs its `Principal` with `allowed_consumer_ids=frozenset({"consumer-A"})`. The value the route actually receives does not match what the fixture configured — the principal object reaching `_do_ack` is not the one the test set up, or is being re-resolved/overwritten somewhere between the fixture's dependency override and the route handler (`ack_route.py`'s own comment notes `_principal` is "set by app.py wrapper").

## Reason for Change
An authorization bypass on a consumer-scoped ACK endpoint is a security-relevant correctness defect: any caller can ACK/consume events belonging to a `consumer_id` it does not own once `allowed_consumer_ids` ends up `None` for its principal, silently defeating the ownership check this endpoint exists to enforce.

## Implementation Intent
Trace how `_principal` reaches `_do_ack()` for a request through `principal_client` (the FastAPI dependency chain / "app.py wrapper" mentioned in `ack_route.py`), and determine why its `allowed_consumer_ids` differs from what the test fixture (or, in production, `scripts/eventbus/auth.py`'s role-based resolution) actually sets. Fix at the point where the value is lost or defaulted incorrectly — do not special-case the ACK route's own check to work around a wiring bug elsewhere. If the drifted `_TOKEN_CONSUMER_MAP` comment in the test is itself stale relative to the current auth design, correct the comment as part of the same fix (do not leave a misleading reference).

## Target Files or Areas
- `scripts/eventbus/ack_route.py` (`_do_ack()` authorization check, `ack_event()` wrapper)
- `scripts/eventbus/auth.py` (principal resolution / `allowed_consumer_ids` population, lines ~90-190)
- `tests/eventbus/test_eventbus_ack_endpoint.py` (`principal_client` fixture and its stale `_TOKEN_CONSUMER_MAP` comment)
- Unknown: the FastAPI dependency-override or "app.py wrapper" path connecting the two — not yet traced to a specific file/line

## Required Changes
- Trace the exact path `_principal` takes from the test's dependency override (or, in production, from the real auth resolution in `scripts/eventbus/auth.py`) to `_do_ack()`'s parameter, and identify where `allowed_consumer_ids` is lost or reset to `None`.
- Fix the identified gap so a principal's `allowed_consumer_ids` set by auth resolution (or by the test fixture) is the same value the ownership check evaluates.
- Update or remove the stale `_TOKEN_CONSUMER_MAP` reference in the test comment if the current design no longer uses that map.

## Constraints
- Do not weaken or remove the ownership check itself (`consumer_id not in _principal.allowed_consumer_ids`) — the fix must restore enforcement, not bypass it further.
- Do not change the endpoint's response codes/contract for the already-passing cases (`test_ack_event_delivery_verification`, `test_ack_event_mandatory_consumer_id`).

## Acceptance Criteria
- `tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint::test_ack_event_principal_ownership_validation` passes (`resp.status_code in (403, 409)`).
- All other tests in `tests/eventbus/test_eventbus_ack_endpoint.py` continue to pass.
- The full `tests/eventbus/` suite passes with no new failures.

## Testing Expectations
Run `uv run pytest tests/eventbus/ -v` targeted, then the repository-defined full suite (`uv run pytest`) per `rules/toolchain.md`, to confirm no regression outside `tests/eventbus/`.

## Documentation Impact
N/A: not yet confirmed whether this is a wiring bug or a documented-but-unimplemented auth contract — assess during implementation whether `docs/22_mcp/*` or an eventbus-specific auth doc needs a correction once the root cause is identified.

## Out of Scope
- Broader auth-model redesign (role-based vs. token-map) — fix the wiring/resolution gap only, per Implementation Intent.
- The two `TestAllowedToolsOverride`/orchestrator failures filed separately (see Dependencies) — unrelated subsystem.

## Dependencies
N/A: none. (A separate, unrelated pre-existing failure — `tests/agent/test_orchestrator.py::TestAllowedToolsOverride::test_original_config_restored_even_on_error` — was discovered at the same time and filed as its own issue; the two do not depend on each other.)

## Unresolved Questions
- Is the test's `principal_client` fixture not correctly wired to override the same dependency `ack_route.py` reads `_principal` from, or does `scripts/eventbus/auth.py`'s real resolution path also produce `allowed_consumer_ids=None` for an equivalent production request? Both need checking — the evidence available (log output) confirms the value is `None` at the check site, but not yet which layer introduces it.

## AI Implementation Instruction
Do not fix this by loosening or removing the `403` check in `_do_ack()`. Trace the actual dependency-injection/override path first (add temporary logging or read `app.py`'s route wiring directly) before changing any file — the bug is in how `_principal` is constructed or passed, not in the check's logic itself. Keep the diff scoped to the identified wiring/resolution gap; do not refactor `scripts/eventbus/auth.py`'s broader role-based model. Stop and report if the trace reveals the bug is actually in production code reachable from real traffic (not just test wiring) — that has a materially larger security-impact scope than a test-only issue and should be flagged before proceeding.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260929-111108
- **Related target files**: scripts/eventbus/ack_route.py, scripts/eventbus/auth.py, tests/eventbus/test_eventbus_ack_endpoint.py
