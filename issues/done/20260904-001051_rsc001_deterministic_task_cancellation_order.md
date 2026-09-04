# Add deterministic ordering to ResourceShutdownCoordinator.close_resources task cancellation

## Summary

close_resources cancels pending tasks using asyncio.all_tasks() without guaranteeing any particular ordering. If one task holds a lock that another needs, cancelling them in arbitrary order can leave shared state inconsistent.

## Background

ResourceShutdownCoordinator coordinates cleanup during REPL shutdown. It collects pending tasks and cancels them before gathering results.

## Problem

Non-deterministic task cancellation order means shutdown behavior differs between runs when multiple async operations are active concurrently.

## Reason for Change

Operational risk: during shutdown, inconsistent state from arbitrary cancellation order can cause data loss (e.g., WAL checkpoint interrupted mid-operation while history write proceeds).

## Implementation Intent

Implement a deterministic cancellation strategy. Options include: topological sort of task dependencies, priority-based ordering (WAL before history), or sequential cancellation with explicit dependency awareness. Focus on ensuring critical operations complete before dependent ones are cancelled.

## Target Files or Areas

- scripts/agent/resource_shutdown_coordinator.py

## Required Changes

- Replace asyncio.all_tasks() iteration with ordered cancellation strategy
- Ensure WAL checkpoint tasks complete before history write tasks are cancelled
- Document the cancellation ordering rationale

## Constraints

- Must not increase shutdown latency significantly
- Must preserve existing graceful timeout semantics (_GRACEFUL_TIMEOUT_S = 10.0)

## Out of Scope

- Adding new locking primitives
- Changing the overall shutdown architecture

## Dependencies

N/A: none

## Acceptance Criteria

- [ ] Shutdown behavior is deterministic across multiple runs with same concurrent operations
- [ ] WAL checkpoint completes before history write is cancelled
- [ ] No data loss during forced shutdown scenarios

## Testing Expectations

- Integration test: simulate concurrent WAL checkpoint + history write during shutdown
- Verify deterministic outcome across repeated runs

## Documentation Impact

Document the cancellation ordering policy in the class docstring.

## Priority

Medium

## AI Implementation Instruction

Add deterministic ordering to task cancellation. Do not rewrite the entire coordinator. Preserve existing timeout constants and gather semantics. Stop and report if task dependency graph cannot be determined from current code.
