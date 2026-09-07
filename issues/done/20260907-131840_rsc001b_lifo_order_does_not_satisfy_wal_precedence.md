# LIFO task cancellation does not satisfy REQ-RSC001-2 (WAL checkpoint before history-write cancellation)

## Priority
High

## Summary
`issues/done/20260904-001051_rsc001_deterministic_task_cancellation_order.md` required (REQ-RSC001-2)
that the WAL checkpoint complete before any history-write task is cancelled during shutdown. Its
implementation procedure (`implementations/done/20260904-101440_01_scripts_agent_resource_shutdown_coordinator_py.md`)
explicitly rejected tier-based classification ("no naming convention exists" — confirmed by its
own `rg 'set_name|\.name\s*=' scripts/agent/` finding zero matches) and substituted LIFO
(last-created-first-cancelled) ordering instead, applied and present in the current code
(`scripts/agent/resource_shutdown_coordinator.py:78`, `for t in reversed(pending_tasks):`). LIFO
ordering does not implement, and cannot guarantee, "WAL checkpoint before history-write
cancellation" — task creation order has no defined relationship to which task performs the WAL
checkpoint versus the history write. REQ-RSC001-2 remains unmet even though the procedure's own
Step 1 is marked `Completed`.

## Background
`Explicit in code`: `close_resources()` (`scripts/agent/resource_shutdown_coordinator.py:60`)
collects `pending_tasks` via `asyncio.all_tasks(loop)` (line 71), cancels them in LIFO order
(line 78) and awaits their completion via `asyncio.gather(*pending_tasks, return_exceptions=True)`
(line 81) — all of this happens *before* the explicit WAL checkpoint call
(`self._wal.checkpoint_sync()`, line 90). If a history-write task is among `pending_tasks`, it is
cancelled and awaited to completion before the WAL checkpoint runs at all, which is the reverse
of what REQ-RSC001-2 requires, regardless of LIFO creation-order position.

## Problem
- LIFO ordering only controls the relative cancellation order *among* `pending_tasks` themselves;
  it says nothing about the WAL checkpoint, which is not itself one of the tracked
  `asyncio.all_tasks()` entries — it is a separate, explicit call made after the entire
  cancel-and-gather block completes.
- If any in-flight history-write task exists in `pending_tasks` at shutdown time, it is cancelled
  and its cancellation is awaited (line 81) *before* `checkpoint_sync()` runs (line 90) — the
  opposite of the required WAL-before-history-write-cancellation ordering.
- The implementation procedure's own "Design decisions" section acknowledges the pivot from
  tier-based ordering to LIFO but does not re-verify the resulting order against REQ-RSC001-2
  specifically — its "Alternatives considered" section rejects tier-based and topological-sort
  approaches without checking whether the LIFO fallback still satisfies the original acceptance
  criterion it replaced.

## Reason for Change
Data-loss risk during shutdown: cancelling a history-write task before the WAL checkpoint runs is
exactly the scenario REQ-RSC001-2 was written to prevent (operational risk: "inconsistent state
from arbitrary cancellation order can cause data loss (e.g., WAL checkpoint interrupted mid-
operation while history write proceeds)", per the original issue's Reason for Change). The current
code's ordering — cancel everything including any history-write task first, checkpoint second —
does not close this risk; it only replaced non-determinism with a deterministic order that still
does not guarantee the required precedence.

## Implementation Intent
Since no task-naming convention exists to identify which pending task performs history writes
(confirmed by the implementation procedure's own investigation), do not attempt a second
name-based classification. Instead, ensure the explicit WAL checkpoint (`checkpoint_sync()`)
completes before the general task-cancellation-and-gather block runs, or identify the
history-write task by a mechanism other than name (e.g. a dedicated handle/reference held by the
coordinator, if one exists) so it can be excluded from blanket cancellation until the checkpoint
completes.

## Target Files or Areas
- `scripts/agent/resource_shutdown_coordinator.py` (`close_resources()`, lines 60-104: task
  collection/cancellation at 70-84, WAL checkpoint at 86-104)

## Required Changes
- Re-order `close_resources()` so the WAL checkpoint (`self._wal.checkpoint_sync()`) completes
  before any task that could be performing a history write is cancelled — either by running the
  checkpoint before the blanket cancellation block, or by giving the coordinator a way to
  identify and defer cancelling the specific history-write task until after the checkpoint.
- Document the actual guarantee the resulting order provides (and its limits) in the class
  docstring, replacing or supplementing the current "LIFO ordering" description if the ordering
  mechanism changes.
- Add a test that constructs a pending history-write task and pending WAL-checkpoint-adjacent
  state, and asserts the checkpoint completes before that task is cancelled.

## Constraints
- Must not reintroduce a task-naming-convention dependency without adding the naming
  infrastructure itself — the prior attempt correctly found none exists today.
- Must not increase shutdown latency significantly beyond the existing `_GRACEFUL_TIMEOUT_S`
  budget.
- Must preserve existing `asyncio.gather(..., return_exceptions=True)` error-collection semantics
  for tasks that are cancelled.

## Acceptance Criteria
- [ ] A test demonstrates the WAL checkpoint completes before a pending history-write-equivalent
      task is cancelled.
- [ ] `close_resources()`'s docstring accurately describes the actual ordering guarantee provided
      (not "LIFO order" alone, if LIFO order is not what satisfies REQ-RSC001-2).
- [ ] No regression in existing `resource_shutdown_coordinator.py` tests.

## Testing Expectations
Add an integration-style test simulating a pending history-write task and a WAL checkpoint call,
asserting checkpoint-before-cancellation ordering; run the full existing test suite for this
module to confirm no regression.

## Documentation Impact
Update `ResourceShutdownCoordinator`'s class docstring (currently describes "LIFO
(last-created-first-cancelled) order" per the prior procedure) to describe whatever ordering
mechanism actually satisfies REQ-RSC001-2 after this fix.

## Out of Scope
- Re-litigating whether LIFO ordering is useful for other (non-WAL-related) tasks — this issue
  only concerns the WAL-checkpoint/history-write precedence guarantee.
- Adding a general task-naming/tagging infrastructure across the agent process, unless the
  chosen fix specifically requires it for this coordinator alone.

## Dependencies
Follows `issues/done/20260904-001051_rsc001_deterministic_task_cancellation_order.md` and its
implementation procedure — this issue re-opens only the REQ-RSC001-2 portion of that work, which
the LIFO substitution did not satisfy.

## Unresolved Questions
- Whether the coordinator currently holds any reference to a specific "history write" task
  distinct from `asyncio.all_tasks()`'s generic set — if not, the implementer must determine how
  to identify it without a naming convention, or confirm no such distinguishable task exists at
  the point `close_resources()` runs (in which case the requirement may need re-scoping with the
  issue owner rather than implemented as originally worded).

## AI Implementation Instruction
Re-read `scripts/agent/resource_shutdown_coordinator.py` in full before editing, and confirm
current line numbers via `rg -n "checkpoint_sync|all_tasks|reversed\(pending_tasks\)"
scripts/agent/resource_shutdown_coordinator.py`. If no mechanism exists to distinguish a
history-write task from other pending tasks, stop and report this as a blocking design question
rather than guessing at a classification heuristic.
