## Goal
Determine whether `scripts/eventbus/route_helpers.py` requires modification to
satisfy REQ-001/REQ-002 (the shutdown-vs-sweep race), per the Plan's own conditional
listing of this file ("Modify (if the chosen fix requires it)").

## Scope
N/A: covered by Goal — this document's scope is the determination itself, not a code
change (see Design decisions below).

## Assumptions
- The design decision made in the companion document for `scripts/eventbus/app.py`
  (`implementations/20260913-102829_01_scripts_eventbus_app_py.md`) — routing
  `db.close()` through the existing `get_db_lock()` — is the mechanism actually
  implemented. If a future revision of that document changes the chosen mechanism,
  this determination must be re-checked.

## Design decisions
The companion document for `scripts/eventbus/app.py` adopted the design of routing
`db.close()` through `get_db_lock()` (the same lock `run_with_db_lock()` already
acquires for every DB operation). This mechanism requires no change to
`run_with_db_lock()` itself: it already acquires and releases `get_db_lock()`
correctly for its own callers, and the shutdown path in `app.py` acquires the same
lock object directly via `eventbus.db.get_db_lock()` rather than by calling through
`run_with_db_lock()`. **Conclusion: no code change to `scripts/eventbus/route_helpers.py`
is required.** This satisfies the Plan's own conditional framing for this row — the
condition ("if the chosen fix requires it") did not hold.

## Alternatives considered
Had the Plan's first candidate mechanism been chosen instead (tracking `_dlq_loop`'s
in-flight `run_with_db_lock` call via an exposed thread/future handle),
`run_with_db_lock()` would have needed to return or expose that handle to its caller,
which would have required modifying this file. That path was not taken (see the
companion `app.py` document's Alternatives considered), so this file remains
unchanged.

## Implementation
### Target file
scripts/eventbus/route_helpers.py

### Procedure
No implementation changes. Confirm (by re-reading `run_with_db_lock()` after the
companion document's `app.py` change is implemented) that its existing
`get_db_lock()` usage still matches what the shutdown path in `lifespan()` now
assumes — specifically, that both acquire the exact same lock object returned by
`eventbus.db.get_db_lock()`.

### Method
N/A: no code method to implement.

### Details
N/A: no code details to implement.

## Compatibility considerations
N/A: no change made.

## Security considerations
N/A: no change made.

## Rollback considerations
N/A: no change made, so there is nothing to roll back for this file specifically.

## Validation plan
- After the companion `app.py` implementation lands, re-read
  `run_with_db_lock()` and confirm its `get_db_lock()` usage is unchanged and still
  correct relative to the new shutdown-path caller.
- No new tests are added against this file specifically — its behavior is already
  covered by `run_with_db_lock()`'s existing callers' tests, and the shutdown race
  regression test lives in the companion `app.py` document's scope.

## Completion criteria
This item is complete once the "no change required" determination above is
confirmed still valid against the as-implemented `app.py` change (Validation plan),
with no further action needed.

## Out of scope
- Any change to `run_with_db_lock()`'s implementation, since none is required.
- The `_ROUTE_ROLE_MAP` routing fix, the per-role token validation fix, and the
  `require_consumer_identity` missing-default fix — each is a separate Plan/issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm no code change is required (re-read `run_with_db_lock()` against the implemented `app.py` change) | Pending | — | — | |

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
- **Source issue**: issues/20260913-093534_eb003_eventbus-dlq-loop-shutdown-segfault.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-094951_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-102829
- **Related target files**: scripts/eventbus/route_helpers.py
