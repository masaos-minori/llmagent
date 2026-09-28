# Add missing integration test for unreachable INVALID_FORMAT branch (NC-021)

## Priority
Medium

## Summary
Add one integration test for `_classify_error()`'s `INVALID_FORMAT` dispatch branch in `scripts/db/recovery.py`, mirroring the existing pattern already used for its sibling conditions, to close NC-021's remaining open question.

## Background
NC-021 originally asked whether `_classify_error()` should be extended to produce `INVALID_FORMAT`, or whether the enum value/branch should be removed as dead code. ADR-008 Decision Details #14 (merged from former ADR-011) already settles that question in favor of keeping the enum and branch. A deep-dive investigation (2026-09-27) found the remaining, narrower question — whether test coverage is needed for the unreachable branch — is also effectively resolved: a unit test for the `INVALID_FORMAT` classification mapping already exists (`tests/db/test_db_recovery.py::test_classify_error_invalid_format`, line 560), but the recovery flow's own dispatch (`if condition in (LOCK_CONTENTION, PERMISSION_FAILURE, INVALID_FORMAT): return RecoveryResult(...)`) has integration-level tests for its sibling conditions `LOCK_CONTENTION` and `PERMISSION_FAILURE` (mocking `_run_integrity_check`'s return value) but not for `INVALID_FORMAT`.

## Problem
The recovery flow's dispatch branch for `INVALID_FORMAT` has no integration-level test, unlike its two sibling conditions in the same `if` clause — an inconsistent coverage gap, not an open design question.

## Reason for Change
This is a small, mechanical, low-judgment gap-fill: mirroring an already-established, already-approved test pattern for the third of three sibling conditions. Closing it removes the last open item blocking NC-021's removal from the Needs Confirmation inventory.

## Implementation Intent
Locate the existing `LOCK_CONTENTION`/`PERMISSION_FAILURE` integration tests for this dispatch branch in `tests/db/test_db_recovery.py` and add a parallel test for `INVALID_FORMAT`, mocking `_run_integrity_check()`'s return value the same way.

## Target Files or Areas
- `tests/db/test_db_recovery.py`
- `scripts/db/recovery.py` (reference only, not expected to change)

## Required Changes
- Add one integration test asserting the recovery flow dispatches correctly (returns the expected `RecoveryResult`) when `_run_integrity_check()`'s mocked return value classifies as `INVALID_FORMAT`, following the exact structure of the existing `LOCK_CONTENTION`/`PERMISSION_FAILURE` tests.

## Constraints
N/A: no constraints beyond mirroring the existing test pattern exactly.

## Acceptance Criteria
- The new test exists, follows the same structure as its `LOCK_CONTENTION`/`PERMISSION_FAILURE` siblings, and passes.
- Full test suite passes with no regression.

## Testing Expectations
Integration test (pytest), mirroring existing sibling tests. Run the targeted test, then the full suite once per `rules/toolchain.md`.

## Documentation Impact
Once the test lands and passes, remove the NC-021 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 2 (Needs Confirmation).

## Out of Scope
- Any change to `_classify_error()`'s or the recovery flow's actual behavior — this issue is coverage-only; ADR-008 #14 already settled the design question.
- Re-litigating whether `INVALID_FORMAT` should be removed as dead code (already settled by ADR-008 #14).

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — resolved by the 2026-09-27 deep-dive investigation; this is now a mechanical implementation task, not an open design question.

## AI Implementation Instruction
Add only the one missing integration test, mirroring the `LOCK_CONTENTION`/`PERMISSION_FAILURE` test structure exactly. Do not modify `scripts/db/recovery.py`. Keep the diff scoped to the new test function only.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211353
- **Related target files**: tests/db/test_db_recovery.py, scripts/db/recovery.py (reference)
