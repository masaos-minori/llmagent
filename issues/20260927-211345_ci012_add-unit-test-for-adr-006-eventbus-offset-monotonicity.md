# Add unit test for ADR-006 EventBus offset monotonicity (CI-012)

## Priority
Medium

## Summary
Add automated test coverage for ADR-006's EventBus offset monotonicity invariant, currently confirmed correct only by code inspection (Known Issue CI-012 in `governance_03`).

## Background
CI-012 has been open since 2026-09-03, one of five sibling "ADR invariant verified by code inspection, no automated test" entries (CI-009, CI-010, CI-012, CI-014, CI-016), previously batched in `governance_03` as one cross-cutting initiative pending an ownership decision. A deep-dive investigation (2026-09-27) found no existing cross-cutting engineering role anywhere in this repo — only a per-area RACI model (`docs/00_governance/governance_01_documentation-policy.md`) — and recommends reverting to per-area ownership rather than creating a new role (see the Configuration Ownership Map precedent, `governance_01` line 342). This issue assigns CI-012 specifically to `@eventbus-dev` (EventBus), per that recommendation.

## Problem
`scripts/eventbus/offsets.py::write_offset()` enforces `seq > current` (monotonically increasing offsets) per ADR-006 — confirmed correct via code inspection — but no automated test covers this invariant.

## Reason for Change
Without test coverage, a future change to `write_offset()` could silently allow a non-monotonic (out-of-order or duplicate) offset write, violating ADR-006, with no automated signal.

## Implementation Intent
Add a focused unit test asserting `write_offset()` rejects or otherwise prevents a non-increasing offset write, following existing conventions in `tests/eventbus/`. No production code change is expected.

## Target Files or Areas
- `scripts/eventbus/offsets.py` (reference only, not expected to change)
- `tests/eventbus/` (new or updated test)

## Required Changes
- Add a unit test exercising `write_offset()` that asserts monotonicity is enforced (e.g. attempting to write a `seq` not greater than the current stored offset fails or is rejected).

## Constraints
N/A: no constraints beyond standard repository test conventions.

## Acceptance Criteria
- A new test exists covering ADR-006's offset-monotonicity invariant and passes.
- Full test suite passes with no regression.

## Testing Expectations
Unit test (pytest). Run the targeted test, then the full suite once per `rules/toolchain.md`.

## Documentation Impact
Once the test lands and passes, remove the CI-012 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 (Known Issues), and update the CI-009/010/012/014/016 batching note to reflect one fewer remaining member.

## Out of Scope
- CI-009, CI-010, CI-014, CI-016 — tracked as separate issues.
- Any change to `offsets.py`'s actual behavior (already confirmed correct; this is a test-coverage-only gap).

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — the per-area ownership recommendation (`@eventbus-dev` for this item) was already established via a 2026-09-27 deep-dive investigation.

## AI Implementation Instruction
Add only the missing test. Do not modify `scripts/eventbus/offsets.py` unless the new test reveals an actual bug (none is currently expected). Keep the diff scoped to the new test file/function only.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211345
- **Related target files**: tests/eventbus/ (new test), scripts/eventbus/offsets.py (reference)
