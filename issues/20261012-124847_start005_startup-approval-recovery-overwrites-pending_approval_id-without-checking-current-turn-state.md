# Startup approval recovery overwrites pending_approval_id unconditionally while pending_approval_task_id has a stale-check

## Priority
Low

## Summary
In `ApprovalRecovery.recover()`, `ctx.turn.pending_approval_id` is assigned unconditionally
(line 49), whereas `ctx.turn.pending_approval_task_id` (lines 50–70) guards against overwriting
an active current-session value with a stale previous-session value. The two fields are set by
different rules within the same recovery routine, which is an inconsistency. Because recovery
runs at startup when `ctx.turn` is typically fresh, the practical impact is low, but the
asymmetry suggests the `pending_approval_id` assignment was not carried through when the
stale-check was added to `pending_approval_task_id`. Verify the intent and align the two.

## Background
`startup_approval_recovery.py` restores workflow approval-pending state from a previous session.
It wires up the most recent pending approval for immediate action. The code deliberately added
a stale-vs-active guard for `pending_approval_task_id` (keeping an existing active value), but
the sibling field `pending_approval_id` is overwritten without a comparable guard.

## Problem
`pending_approval_id` and `pending_approval_task_id` describe the same recovered approval but
are guarded differently. If, in any scenario where `recover()` runs against a turn that already
carries an active approval (e.g. a restart mid-turn, or a future caller that re-invokes
recovery), the unconditional assignment can clobber the live `pending_approval_id` with the
previous-session id, leaving the REPL pointing at an approval that is no longer the active one.
The task-id field avoids this; the id field does not.

## Reason for Change
Consistency between two closely related fields set in the same routine reduces the chance of a
subtle clobber and makes the recovery contract obvious. Even if currently low-impact, the
asymmetry is a latent footgun worth resolving before recovery is ever called outside startup.

## Implementation Intent
- Confirm whether `recover()` is only ever called once at startup with a fresh turn. If so,
  document that the unconditional assignment is safe-by-construction and add a comment noting
  why no stale-check is needed here.
- If `recover()` could run against a non-fresh turn, apply the same stale-vs-active guard to
  `pending_approval_id` as exists for `pending_approval_task_id`, or otherwise avoid clobbering
  a live value.
Do not change the recovery semantics for the happy path (wire up the most recent approval).

## Target Files or Areas
- `scripts/agent/startup_approval_recovery.py` (`recover()`)
- `scripts/agent/startup.py` — read only, to confirm recover() is called once at startup
- `scripts/agent/context.py` — read only, to inspect `ctx.turn` lifecycle

## Required Changes
- Either document the safe-by-construction case (single startup call, fresh turn) or align the
  `pending_approval_id` assignment with the `pending_approval_task_id` stale-check.

## Constraints
- Preserve the happy-path behavior: the most recent pending approval must be wired up.
- Do not change `pending_approval_task_id`'s existing guard logic.

## Acceptance Criteria
- The relationship between `pending_approval_id` and `pending_approval_task_id` assignment is
  explicit (documented or aligned).
- No regression to the happy-path recovery wiring.
- Existing `tests/agent/test_startup_approval_recovery.py` passes.

## Testing Expectations
- Re-run `tests/agent/test_startup_approval_recovery.py`.
- If the guard is aligned, add a test asserting a live `pending_approval_id` is preserved when
  recovery runs against a non-fresh turn.

## Documentation Impact
If `docs/` documents the approval-recovery contract, note the single-call-at-startup
assumption.

## Out of Scope
- Any change to `find_all_pending_approvals()` or the StateStore.
- Changes to other startup checks.

## Dependencies
N/A: none

## Unresolved Questions
- Whether `recover()` is guaranteed to run exactly once against a fresh turn (confirm before
  deciding the unconditional assignment is safe-by-construction).
- What `ctx.turn` looks like if recovery were invoked outside startup.

## AI Implementation Instruction
First confirm via `startup.py` that `recover()` is called once at startup with a fresh turn.
If yes, add a comment documenting why no stale-check is needed for `pending_approval_id`; if no,
apply the same stale-vs-active guard used for `pending_approval_task_id`. Do not change the
happy-path wiring or other startup checks.

## Traceability
- **Workflow phase**: `python-code-review` + `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `N/A: not filed from a Plan`
- **Source implementation procedure**: `N/A: not filed from an implementation procedure`
- **Generated at**: 20261012-124847
- **Related target files**: `scripts/agent/startup_approval_recovery.py`
