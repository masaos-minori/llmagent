# Fix meaningless asyncio.sleep(0) timeout check in ResourceShutdownCoordinator.close_resources

## Summary

close_resources uses asyncio.wait_for(asyncio.sleep(0), timeout=_GRACEFUL_TIMEOUT_S) which will NEVER trigger TimeoutError under normal circumstances. asyncio.sleep(0) yields control and immediately returns; it cannot timeout within the grace period.

## Background

ResourceShutdownCoordinator.close_resources attempts to wait for async operations to settle before finalizing shutdown. The intent seems correct but the mechanism is wrong.

## Problem

The timeout check is a no-op. If async operations do not settle within _GRACEFUL_TIMEOUT_S seconds, the timeout error is never raised, and the coordinator proceeds as if everything completed cleanly.

## Reason for Change

Silent correctness risk: the timeout guard gives false confidence that operations are settling, but it actually never fires. This masks real shutdown delays.

## Implementation Intent

Replace asyncio.sleep(0) with a proper settlement check. Options: (1) await asyncio.gather(*pending_tasks, return_exceptions=True) with a timeout, (2) poll asyncio.all_tasks() until only the main task remains, or (3) use asyncio.shield() around critical operations. Choose the approach that best matches the existing shutdown coordination pattern.

## Target Files or Areas

- scripts/agent/resource_shutdown_coordinator.py

## Required Changes

- Replace the asyncio.sleep(0) block with a meaningful timeout-aware operation
- Ensure the timeout actually fires when operations don't settle
- Update the error message to reflect the new behavior

## Constraints

- Must not change the timeout constant value (_GRACEFUL_TIMEOUT_S = 10.0)
- Must preserve existing error collection semantics

## Out of Scope

- Adding new configuration options
- Changing the overall shutdown flow

## Dependencies

N/A: none

## Acceptance Criteria

- [ ] Timeout fires when async operations exceed _GRACEFUL_TIMEOUT_S seconds
- [ ] Error is collected and reported correctly
- [ ] No regression in shutdown timing for healthy cases

## Testing Expectations

- Unit test: verify timeout fires when a task blocks indefinitely
- Integration test: verify no regression in shutdown timing for normal cases

## Documentation Impact

Update the close_resources docstring to document the new settlement mechanism.

## Priority

Medium

## AI Implementation Instruction

Fix only the asyncio.sleep(0) timeout block. Do not rewrite the entire coordinator. Preserve the timeout constant and error collection pattern. Stop and report if the intended settlement semantics are unclear from context.
