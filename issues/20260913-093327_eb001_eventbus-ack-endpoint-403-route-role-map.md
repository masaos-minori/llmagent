# EventBus auth `_ROUTE_ROLE_MAP` missing `/events` entry causes ack endpoint to always return 403

## Priority
High

## Summary
`scripts/eventbus/auth.py`'s `_ROUTE_ROLE_MAP` has no entry matching the consumer ack
endpoint's actual path (`/events/{event_id}/ack`), so `require_role`'s prefix-match
routing falls through to "Forbidden: unknown route" for every request to it, regardless
of the caller's token.

## Background
N/A: covered by Summary

## Problem
`_ROUTE_ROLE_MAP` maps a path prefix to the role(s) allowed to call it, and
`require_role`'s `_check_role` resolves the caller's role by checking
`request.url.path.startswith(route_path)` against each key. The map defines `/ack` as a
key, but the endpoint's actual route is `/events/{event_id}/ack` (`scripts/eventbus/
app.py`'s `ack_event` handler) — `/events/...` never starts with `/ack`, so no entry
matches and the fallback `raise HTTPException(status_code=403, detail="Forbidden:
unknown route")` fires unconditionally.

## Reason for Change
Confirmed by repository evidence: running `tests/eventbus/test_eventbus_ack_endpoint.py`
and `tests/eventbus/test_eventbus_ack_nack.py` shows every request to `/events/
{event_id}/ack` returning 403 even with a valid, correctly-scoped consumer token. This
means the ack endpoint is unusable end-to-end in the current codebase, not only in
tests — any real consumer calling it would be rejected the same way.

## Implementation Intent
Add a `_ROUTE_ROLE_MAP` entry whose key matches the ack endpoint's actual path prefix
(`/events`), mapped to `Role.CONSUMER`, without changing the existing prefix-match
lookup mechanism itself.

## Target Files or Areas
- `scripts/eventbus/auth.py` (`_ROUTE_ROLE_MAP` definition)

## Required Changes
- Add an entry to `_ROUTE_ROLE_MAP` whose key matches `/events/{event_id}/ack`'s path
  prefix, mapped to `Role.CONSUMER`.
- Confirm the new entry does not shadow or get shadowed by an existing entry given
  `_check_role`'s in-order `startswith` scan (dict iteration order matters here).

## Constraints
Do not change the existing entries' roles or the prefix-match mechanism itself —
scope this to the missing entry only.

## Acceptance Criteria
- A request to `/events/{event_id}/ack` with a valid Consumer-role token no longer
  returns 403 for the "unknown route" reason.
- `tests/eventbus/test_eventbus_ack_endpoint.py` and `tests/eventbus/
  test_eventbus_ack_nack.py`'s currently-failing cases pass.
- No regression in the authorization behavior of the other routes already covered by
  `_ROUTE_ROLE_MAP` (`/health`, `/publish`, `/subscribe`, `/nack`, `/dlq`,
  `/dlq/{event_id}/requeue`, `/replay`).

## Testing Expectations
Run `tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/
test_eventbus_ack_nack.py`, and `tests/eventbus/test_eventbus_auth.py`'s ack-related
cases; confirm no new failures elsewhere in `tests/eventbus/`.

## Documentation Impact
N/A: this is an internal authorization-routing fix with no user-facing or
operational-behavior documentation dependent on it.

## Out of Scope
- Completing the per-role token feature (tracked separately).
- The `_dlq_loop` shutdown/segfault issue (tracked separately).
- The `/nack` endpoint's `consumer_id` dependency-injection issue (tracked separately).
- Cleaning up the `_ROUTE_ROLE_MAP`'s `/dlq/requeue` entry, which appears unreachable
  given the dict's current iteration order (the earlier `/dlq` entry already matches
  first) — noted below as an open question, not required by this issue's Acceptance
  Criteria.

## Dependencies
N/A: none

## Unresolved Questions
- The existing `"/dlq/requeue"` entry appears to be a dead entry: `_check_role` iterates
  `_ROUTE_ROLE_MAP` in definition order, and the earlier `"/dlq"` entry already matches
  any `/dlq/...` path first (both map to `Role.OPERATOR`, so there is no observed
  behavioral difference today, but the entry itself never actually gets used). Whether
  to also fix this in the same change is left to the implementer's judgment — it is not
  required by this issue's Acceptance Criteria.

## AI Implementation Instruction
Change only `scripts/eventbus/auth.py`'s `_ROUTE_ROLE_MAP`. Do not touch the per-role
token config/validation logic, the `_dlq_loop` shutdown path, or the `/nack` endpoint's
`consumer_id` handling — each has its own tracked issue. Run the acceptance-criteria
tests above before considering this complete.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-093327
- **Related target files**: scripts/eventbus/auth.py
