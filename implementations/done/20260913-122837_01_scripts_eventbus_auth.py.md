## Goal
Give `require_consumer_identity`'s `consumer_id` parameter a default value (REQ-001)
so `/subscribe`, `/events/{event_id}/ack`, and `/nack` actually treat `consumer_id` as
optional, matching each endpoint's own `Query(default="")` declaration.

## Scope
Only `require_consumer_identity`'s `consumer_id` parameter signature in
`scripts/eventbus/auth.py`. No change to its internal allowlist logic, to
`_ROUTE_ROLE_MAP` (eb001, separately implemented in this same file), or to any route
handler.

## Assumptions
- `require_consumer_identity`'s internal guard `if consumer_id and consumer_id not in
  _TOKEN_CONSUMER_MAP.get(token, set())` (confirmed by reading the function, line
  163) already treats an empty string as "no consumer_id supplied" — only the missing
  parameter default itself is being fixed, not this logic.
- All three call sites (`subscribe`, `ack_event`, `nack` in `scripts/eventbus/app.py`)
  already declare their own `consumer_id: str = Query(default="")` (confirmed by
  reading `app.py`) — this fix makes the dependency's own default consistent with
  what every caller already assumes.

## Design decisions
Change `consumer_id: str` to `consumer_id: str = ""` in `require_consumer_identity`'s
signature — the exact fix the Issue and Plan specify, matching the empty-string
convention every call site and the function's own internal guard already use.

## Alternatives considered
- **Change `consumer_id`'s type to `str | None = None` instead of `str = ""`**:
  rejected — the internal guard (`if consumer_id and ...`) and every call site already
  use `""` as the "absent" sentinel, not `None`; introducing a second sentinel value
  for the same concept would require also changing the guard and every call site,
  which is out of scope (Constraints: do not change the authorization logic itself).

## Implementation
### Target file
scripts/eventbus/auth.py

### Procedure
1. In `require_consumer_identity`'s signature (currently `consumer_id: str,` at line
   150), change it to `consumer_id: str = "",`.

### Method
Single default-value addition on an existing parameter; no other signature or body
change.

### Details
- Do not reorder parameters — `consumer_id` keeps its current position (after
  `request`, before `topics`); Python only requires defaulted parameters to follow
  non-defaulted ones, and `topics: list[str] | None = None` (already defaulted)
  already follows it, so no reordering is needed.
- Do not change `topics`' default or `token`'s `Depends(...)` — out of scope.
- Known interaction with eb001 (also targeting this same file, already implemented in
  `implementations/done/20260913-121322_01_scripts_eventbus_auth.py.md`): eb001 added
  a `"/events"` key to `_ROUTE_ROLE_MAP` (a module-level dict, unrelated function).
  This document's change is to a different function entirely (`require_consumer_identity`)
  — no line-range or logic overlap; both changes can coexist in the file without
  conflict.

## Compatibility considerations
Purely relaxes a requirement (a previously-mandatory query parameter becomes
optional) — cannot break any caller that already supplies `consumer_id`, since the
allowlist-check guard's behavior for a non-empty `consumer_id` is unchanged.

## Security considerations
No authorization logic changes: a caller that previously had to supply `consumer_id`
to pass validation (even redundantly, e.g. an empty string) still goes through the
same allowlist check when it does supply one; only the previously-unintended
422-before-reaching-that-check case is removed.

## Rollback considerations
Single-parameter default addition in one file — revert the line to roll back. No
schema, migration, or data impact.

## Validation plan
- Static inspection (per the Plan's own Validation plan): `uv run python -c "..."`
  inspecting `eventbus.app.app.routes`' `route.dependant` for `/nack`, `/subscribe`,
  and `/events/{event_id}/ack`, confirming `consumer_id`'s default is no longer
  `PydanticUndefined` on any of the three (AC-1, AC-2).
- Run `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v` and any
  `/subscribe`-related case that omits `consumer_id`, to confirm AC-1/AC-2
  independently of eb001's routing fix (per the Plan's own Risk mitigation — `/nack`
  and `/subscribe` are not gated by eb001's `_ROUTE_ROLE_MAP` fix).
- Run `uv run pytest tests/eventbus/ -q --timeout=30` to confirm no regression in
  consumer_id allowlist enforcement or offset tracking.
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, diff-cover.

## Completion criteria
- `require_consumer_identity`'s `consumer_id` parameter has a default value (`= ""`)
  and no other signature/logic change (REQ-001).
- Route-`dependant` inspection confirms `consumer_id` is optional (no longer
  `PydanticUndefined`) on all three affected routes.
- A request to `/nack` or `/subscribe` with no `consumer_id` query parameter no
  longer returns 422 for a missing-parameter reason (AC-1, AC-2 for these two routes
  — `/events/{event_id}/ack`'s end-to-end verification depends on eb001, already
  implemented, so this criterion is also checkable end-to-end for that route now).
- Existing consumer_id-provided call paths (allowlist enforcement, offset tracking)
  are unaffected.

## Out of scope
- The `_ROUTE_ROLE_MAP` routing fix (eb001, already implemented in this same file).
- The per-role token validation issue (eb002 — already implemented in this same
  file as of this document's execution; see `implementations/done/
  20260913-122501_05_scripts_eventbus_auth.py.md`, REQ-005/REQ-006, which also fixed
  the `_TOKEN_CONSUMER_MAP` allowlist empty-set bug this document originally listed
  as "previously-undiscovered, needs its own issue/plan" — that fix landed before
  this document's own Step 3, so it is no longer an open gap).
- The `_dlq_loop` shutdown/segfault issue (eb003, already implemented).
- The `_TOKEN_TOPIC_MAP`/`subscribe_route.py` topic-allowlist empty-set bug
  discovered during eb002's REQ-006 validation (a distinct, still-unresolved
  instance of the same class of bug, requiring a change outside this file) —
  tracked by a new issue, not fixed here.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-143039 | 20260913-143039 | Added = "" default to require_consumer_identity's consumer_id parameter |
| 2 | Add or update tests per Validation plan | Completed | 20260913-143039 | 20260913-143039 | Route-dependant inspection confirms consumer_id no longer PydanticUndefined on /subscribe, /nack, /events/{event_id}/ack; tests/eventbus/test_eventbus_ack_nack.py 12/12 pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-143039 | 20260913-143039 | ruff/mypy/bandit/lint-imports/diff-cover(100%)/pre-commit all passed; full tests/eventbus/ suite: 8 pre-existing unrelated failures remain, 0 new regressions |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-143039 | 20260913-143039 | N/A: no docs/00_index.md task-scope mapping for scripts/eventbus/auth.py |

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
- **Source issue**: issues/20260913-093611_eb004_eventbus-require-consumer-identity-missing-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-095108_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-122837
- **Related target files**: scripts/eventbus/auth.py