# Add consistency check for _cmds duplication between _repl_loop and _dispatch_line

## Summary

_repl_loop checks `if self._cmds is None` at line 191-194 and raises. _dispatch_line checks again at line 170-173. Between these two checks, if _cmds is modified by another coroutine, the second check could fail even though the first passed. In practice, _cmds is only written once during initialization, so this is unlikely. But the defensive check duplication suggests the author anticipated this concern.

## Background

Both methods independently guard against _cmds being None. This redundancy is unusual for a value set once during initialization.

## Problem

If _cmds were ever mutated concurrently (even accidentally), the first check would pass but the second might not, leading to inconsistent behavior.

## Reason for Change

Code quality concern: duplicated defensive checks suggest uncertainty about ownership. A single authoritative check would be clearer.

## Implementation Intent

Option A: Remove the redundant check from _dispatch_line and document that _cmds must not be mutated after initialization. Option B: Replace both checks with a single invariant assertion at initialization time. Option C: Keep both checks but add a comment explaining why each is necessary. Choose the approach that best reflects the actual mutability contract for _cmds.

## Target Files or Areas

- scripts/agent/repl_input_loop.py

## Required Changes

- Unify the _cmds None-check into a single location
- Document the immutability contract for _cmds after initialization

## Constraints

- Must not change the runtime behavior of command dispatch
- Must preserve the safety guarantee that _cmds is always available during dispatch

## Out of Scope

- Adding new command types
- Changing the command registration mechanism

## Dependencies

N/A: none

## Acceptance Criteria

- [ ] Single authoritative check for _cmds availability
- [ ] Immutability contract documented
- [ ] No behavioral regression

## Testing Expectations

- Verify command dispatch works correctly after all initialization paths
- Type checker pass (if invariant assertion is added)

## Documentation Impact

Document the _cmds lifecycle in the class docstring.

## Priority

Low

## AI Implementation Instruction

Unify the _cmds check only. Do not change command dispatch behavior. Preserve the safety guarantee. Stop and report if the mutability contract for _cmds is unclear.
