# Startup approval recovery only surfaces the most recent pending approval

## Priority
Medium

## Summary
`ApprovalRecovery.recover()` (`scripts/agent/startup_approval_recovery.py`) queries `find_all_pending_approvals()` -- which returns ALL globally pending approvals ordered newest-first -- but acts on only `results[0]`. When a previous session left multiple tasks pending approval, only the newest becomes actionable; the others remain `pending` in the database without being surfaced for resolution. Decide whether this lossy behavior is intentional and, if not, recover or enumerate all pending approvals.

## Background
`find_all_pending_approvals()` (`scripts/agent/workflow/approval_ops.py`) joins `tasks` and `approvals`, filtering `tasks.status = 'pending_approval' AND approvals.status = 'pending'`, excluding expired entries (24h TTL), ordered by creation descending. Recovery runs during startup (`StartupOrchestrator._recover_pending_approvals()`).

## Problem
`recover()` takes `results[0]`, sets `ctx.workflow.approval_pending = True`, and points `ctx.turn.pending_approval_id` / `pending_approval_task_id` at just that one record. It logs `{len(results)} pending approval(s)` but only wires up the latest. Any additional pending approvals stay in the workflow DB in a `pending_approval` state that the current session does not expose or resolve.

## Reason for Change
On restart after a crash/shutdown with multiple in-flight approval gates, users are told a count exists but can act on only one. The remainder linger until they expire, then vanish unresolved -- potentially leaving tasks stuck in `pending_approval`.

## Implementation Intent
Clarify the intended model: (a) at most one approval may be pending at a time (in which case `find_all_pending_approvals()` returning many is itself suspicious and should be investigated), or (b) multiple approvals can legitimately be pending (in which case recovery must enumerate and let the user resolve each, or queue them). Implement the confirmed model without changing the underlying approval lifecycle.

## Target Files or Areas
- `scripts/agent/startup_approval_recovery.py` (`recover()`)
- `scripts/agent/workflow/approval_ops.py` (`find_all_pending_approvals()`)
- `AgentContext` fields `workflow.approval_pending`, `turn.pending_approval_id`, `turn.pending_approval_task_id`

## Required Changes
- If multiple-pending is supported: surface every pending approval (not just the latest) and define a deterministic order/resolution flow; store enough state to resume them.
- If single-pending is intended: add a clear comment or Needs Confirmation resolution documenting why only one is recovered, and confirm `find_all_pending_approvals()` cannot return more than one under normal operation.

## Constraints
- Must not lose or corrupt existing pending approvals.
- Must preserve the 24h approval TTL/expiry semantics.
- Backward compatible with sessions that already have pending approvals on disk.

## Acceptance Criteria
- Behavior for the single-pending case is unchanged.
- For the multi-pending case: every pending approval from the prior session is either surfaced for resolution or explicitly, documentedly deferred with a defined resume path -- no silent orphaning.
- Tests cover both the single- and multi-pending recovery cases.

## Testing Expectations
- Insert two+ pending approvals into a test workflow DB, run `recover()`, assert all are accounted for per the chosen model.
- Assert expiry/TTL still prunes expired approvals during recovery.

## Documentation Impact
Document the resolved single-vs-multi pending-approval model in the workflow docs.

## Out of Scope
- Changing how approvals are requested or resolved during a live session.
- Altering the approval table schema.

## Dependencies
N/A: none.

## Unresolved Questions
Whether the workflow engine ever allows more than one task to be `pending_approval` simultaneously -- this determines whether the fix is enumeration (multi) or a documentation/correctness clarification (single). Needs owner confirmation.

## AI Implementation Instruction
Do not guess the intended model. Determine whether multiple simultaneous pending approvals are possible; if uncertain, implement the minimal safe behavior (do not drop pending approvals) and flag the decision for owner confirmation.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260930-161945
- **Related target files**: scripts/agent/startup_approval_recovery.py, scripts/agent/workflow/approval_ops.py
