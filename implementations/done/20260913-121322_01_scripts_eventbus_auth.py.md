## Goal
Close the 403 "Forbidden: unknown route" gap for `/events/{event_id}/ack` (REQ-001)
by adding a `_ROUTE_ROLE_MAP` entry whose prefix actually matches that endpoint's
registered path.

## Scope
Only the `_ROUTE_ROLE_MAP` dict literal in `scripts/eventbus/auth.py`. No change to
`_check_role`'s scan mechanism, any other entry's role set, or any route handler.

## Assumptions
- `_check_role`'s in-order `startswith` scan (confirmed by reading
  `scripts/eventbus/auth.py`) is correct as-is and is not being redesigned here — the
  Plan's own Assumptions section states the same.
- `scripts/eventbus/app.py`'s `ack_event` handler is registered at
  `/events/{event_id}/ack` (confirmed by reading `app.py`'s
  `@app.post("/events/{event_id}/ack")` decorator) and requires `Role.CONSUMER` per
  its `Depends(require_role(Role.CONSUMER))`.

## Design decisions
Add one new key, `"/events"`, mapped to `{Role.CONSUMER}`. `"/events"` is the
narrowest prefix that (a) matches `/events/{event_id}/ack` and (b) does not overlap
any existing key (`/health`, `/publish`, `/subscribe`, `/ack`, `/nack`, `/dlq`,
`/dlq/requeue`, `/replay` — none starts with or is a prefix of `/events`). Position
does not matter for correctness (no existing or new key is a prefix of another), but
it is added adjacent to `/ack`/`/nack` to group consumer-role entries together for
readability.

## Alternatives considered
- **Change `_check_role` to match by registered route pattern instead of
  `startswith` on a hand-maintained dict**: rejected — out of scope per the Plan
  (Requirements only ask for the missing entry; redesigning the matching mechanism
  is a larger, unrelated change with its own risk).
- **Reuse the existing `"/ack"` key by changing its value to match** (e.g. renaming
  it to `"/events"`): rejected — `"/ack"` does not currently match anything (no route
  is registered at a path starting with `/ack`), but silently repurposing a
  dead/incorrect key is harder to review than adding the correct one; leaving the
  stale `"/ack"` key as a separate cleanup matches the Plan's `UNK-01` judgment call
  (non-blocking, left to implementer's discretion — see Out of scope below).

## Implementation
### Target file
scripts/eventbus/auth.py

### Procedure
1. In the `_ROUTE_ROLE_MAP` dict literal (`scripts/eventbus/auth.py`), add
   `"/events": {Role.CONSUMER},` as a new entry.

### Method
A single dict-literal line addition; no function logic changes.

### Details
- Do not remove or modify the existing `"/ack"` key — the Plan's `UNK-01` treats
  the separate, unrelated dead-entry question (`"/dlq/requeue"` being unreachable
  after `"/dlq"`) as non-blocking and left to implementer's judgment; this document
  does not extend that judgment call to `"/ack"` since the Plan's Requirements only
  ask for the missing `/events` entry, not for auditing/removing other keys.
- No change to `_check_role`, `require_role`, `verify_bearer_token`, or any other
  function in this file.

## Compatibility considerations
Purely additive: a new dict key cannot change the behavior of any path that did not
previously match it. Every path currently reaching `/events/...` currently 403s
unconditionally, so no existing caller can depend on that 403 as intended behavior.

## Security considerations
Narrows access correctly: only `Role.CONSUMER` tokens will be authorized for
`/events/{event_id}/ack` after this change, matching the endpoint's own
`Depends(require_role(Role.CONSUMER))` declaration in `app.py`. No broadening of
access beyond what the endpoint already declares.

## Rollback considerations
Single dict-entry addition in one file — revert the line to roll back. No schema,
migration, or data impact.

## Validation plan
- Directly confirm the routing fix via `_ROUTE_ROLE_MAP` prefix-match inspection
  (no HTTP layer involved): `/events/{event_id}/ack`-shaped paths now match the new
  `"/events"` key, and every pre-existing route path (`/health`, `/publish`,
  `/subscribe`, `/nack`, `/dlq`, `/dlq/{id}/requeue`, `/replay`) still matches its
  original key unchanged (AC-1, AC-3).
- Run `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py
  tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_auth.py -v`.
  **Correction (found during Step 3a/Step 4 verification, not anticipated by the
  source Plan):** most cases in the first two files still fail after this fix, but no
  longer for the "unknown route" 403 this Plan targets — `require_role`'s role check
  now passes and the request reaches `require_consumer_identity`, which then fails for
  two reasons entirely outside this row's scope: (a) eb004's un-fixed missing
  `consumer_id` default (422 "missing" errors), and (b) a separate, previously
  undiscovered bug in `_TOKEN_CONSUMER_MAP`'s allowlist check —
  `_populate_token_maps()` comments `set()` as meaning "any consumer_id allowed", but
  `require_consumer_identity`'s actual check (`consumer_id not in
  _TOKEN_CONSUMER_MAP.get(token, set())`) rejects every non-empty `consumer_id` when
  the mapped set is empty, the opposite of the comment's intent (confirmed via direct
  `uv run python -c ...` inspection of the two pieces of code together). Neither of
  these is this row's `_ROUTE_ROLE_MAP` concern; both need their own fix (eb004 covers
  (a); (b) is undocumented by any existing issue and needs a new one). This document's
  own validation therefore checks AC-1/AC-3 directly (bullet above) rather than via
  this test file's end-to-end pass/fail, since the Plan's AC-2 ("currently-failing
  cases pass") is not achievable by this row's change in isolation.
- Run `uv run pytest tests/eventbus/ -q --timeout=30` to confirm no *new* regression
  is introduced by this change specifically (i.e. no previously-passing test now
  fails) — pre-existing failures caused by eb002/eb004/the newly-found allowlist bug
  are expected and out of scope for this row.
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, diff-cover.

## Completion criteria
- `/events/{event_id}/ack` no longer returns 403 for the "unknown route" reason —
  confirmed directly via `_ROUTE_ROLE_MAP` prefix-match inspection (AC-1).
- No pre-existing `_ROUTE_ROLE_MAP` entry's match behavior changed (AC-3).
- The full `tests/eventbus/` suite introduces no new failures beyond the
  already-known, out-of-scope eb002/eb004/allowlist-bug failures (AC-3, corrected
  scope).
- AC-2 ("currently-failing cases pass") is **not** a completion criterion for this
  row in isolation — it requires eb004 and a yet-to-be-filed fix for the
  `_TOKEN_CONSUMER_MAP` allowlist bug to also land; recorded here rather than
  silently claimed.

## Out of scope
- The per-role token validation issue (eb002), the `_dlq_loop` shutdown/segfault
  issue (eb003, already implemented), and the `require_consumer_identity`
  `consumer_id` default issue (eb004) — each is tracked separately.
- Cleaning up the seemingly-unreachable `"/dlq/requeue"` entry (Plan `UNK-01`,
  non-blocking) — left as-is since it is unrelated to this fix and both `"/dlq"` and
  `"/dlq/requeue"` already map to the same role, so there is no observed behavioral
  difference.
- The newly-discovered `_TOKEN_CONSUMER_MAP`/`require_consumer_identity` allowlist
  bug (see Validation plan's Correction) — not previously tracked by any issue; needs
  its own issue/plan rather than a fix folded into this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-121916 | 20260913-121916 | Added '/events': {Role.CONSUMER} entry to _ROUTE_ROLE_MAP in scripts/eventbus/auth.py |
| 2 | Add or update tests per Validation plan | Completed | 20260913-121916 | 20260913-121916 | Verified via direct _ROUTE_ROLE_MAP prefix-match inspection (AC-1/AC-3); full tests/eventbus/ suite diffed against pre-fix baseline via git stash -- no new regressions, only pre-existing eb002/eb004/allowlist-bug failures remain (some now fail for a different reason, not 'unknown route') |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-121916 | 20260913-121916 | ruff format/check, mypy, bandit all passed; lint-imports shows only pre-existing unrelated shared/agent violations |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-121916 | 20260913-121916 | N/A: no docs/00_index.md task-scope mapping for scripts/eventbus/auth.py |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-093327_eb001_eventbus-ack-endpoint-403-route-role-map.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-094449_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-121322
- **Related target files**: scripts/eventbus/auth.py