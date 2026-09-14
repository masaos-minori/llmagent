# Remove misleading security parameters and stale implementation wording

## Priority
Low

## Summary
Some EventBus route handlers may accept unused security-context parameters or carry stale comments implying enforcement that no longer happens at that layer; this issue removes unused parameters and keeps security boundaries explicit at the layer that actually enforces them, once `eventbus02`/`eventbus03` finalize where authorization is actually checked.

## Background
N/A: covered by Summary — this is a direct code-level finding, contingent on `eventbus02`/`eventbus03`'s authorization changes settling which layer performs the check.

## Problem
Unused security parameters or stale comments in handler signatures can falsely imply that a control is enforced at that layer, when the actual enforcement may have moved (e.g. to endpoint-level authorization dependencies introduced by `eventbus02`/`eventbus03`), creating a misleading contract for future readers/maintainers.

## Reason for Change
Unused security parameters and stale comments can falsely imply that controls are enforced.

## Implementation Intent
Make code contracts, messages, and terminology accurately reflect runtime behavior, using a typed principal (from `eventbus02`) where handlers genuinely require authorization context, and removing parameters that do not.

## Target Files or Areas
- `scripts/eventbus/dlq_route.py`
- `scripts/eventbus/publish_route.py`
- `scripts/eventbus/replay_route.py`
- `scripts/eventbus/ack_route.py`

## Required Changes
- Use a typed principal where handlers require authorization context.
- Remove unused security parameters from handlers that rely exclusively on endpoint-level authorization.
- Keep security boundaries explicit in function contracts.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- No internal handler accepts unused security context parameters.
- Authorization responsibility is documented at the correct layer.
- Static analysis reports no unused authorization parameters.

## Testing Expectations
Not required beyond confirming existing tests for the touched handlers still pass; static analysis (see Acceptance Criteria) is the primary check for this cleanup.

## Documentation Impact
Update any inline comments in the touched handlers that describe security enforcement, to match where enforcement actually happens after `eventbus02`/`eventbus03`.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
Depends on `eventbus02` (principal-based authentication) and `eventbus03` (consumer/topic authorization) landing first, since this issue's correct removal/typed-principal decision depends on where those issues place enforcement.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Do not start this issue until `eventbus02`/`eventbus03` are implemented — removing a parameter before enforcement has moved elsewhere risks a real authorization regression rather than a cleanup. Keep changes scoped to parameter removal and comment accuracy; do not change actual authorization logic here (that belongs to `eventbus02`/`eventbus03`). Confirm via static analysis that no handler silently drops a still-needed check.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102654
- **Related target files**: scripts/eventbus/dlq_route.py, scripts/eventbus/publish_route.py, scripts/eventbus/replay_route.py, scripts/eventbus/ack_route.py
