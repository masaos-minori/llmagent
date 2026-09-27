# Add unit test for ADR-002 config isolation enforcement (CI-009)

## Priority
Medium

## Summary
Add automated test coverage for ADR-002's config isolation invariant, currently confirmed correct only by code inspection (Known Issue CI-009 in `governance_03`).

## Background
CI-009 has been open since 2026-09-03, one of five sibling "ADR invariant verified by code inspection, no automated test" entries (CI-009, CI-010, CI-012, CI-014, CI-016), previously batched in `governance_03` as one cross-cutting initiative pending an ownership decision. A deep-dive investigation (2026-09-27) found no existing cross-cutting engineering role anywhere in this repo — only a per-area RACI model (`docs/00_governance/governance_01_documentation-policy.md`) — and recommends reverting to per-area ownership rather than creating a new role, citing this repo's own precedent of deferring rather than force-fitting new structure for one-off cross-cutting gaps (see the Configuration Ownership Map precedent, `governance_01` line 342). This issue assigns CI-009 specifically to `@db-admin` (Shared/DB), per that recommendation.

## Problem
`scripts/shared/config_loader.py::restrict_to()` enforces config isolation per ADR-002 — confirmed correct via code inspection (per CI-009's existing entry) — but no automated test exists, so a future regression of this invariant would not be caught.

## Reason for Change
Without test coverage, a future change to `restrict_to()` could silently violate ADR-002 with no automated signal, and CI-009 cannot be removed from the Known Issues inventory until coverage exists.

## Implementation Intent
Add a focused unit test asserting `restrict_to()`'s isolation enforcement, following existing test conventions in `tests/shared/`. No production code change is expected — the behavior is already confirmed correct by code inspection.

## Target Files or Areas
- `scripts/shared/config_loader.py` (reference only, not expected to change)
- `tests/shared/` (new or updated test)

## Required Changes
- Add a unit test exercising `restrict_to()` that asserts config isolation is enforced (e.g. a request for a key/path outside the restricted scope is rejected).

## Constraints
N/A: no constraints beyond standard repository test conventions.

## Acceptance Criteria
- A new test exists covering ADR-002's config isolation invariant and passes.
- Full test suite passes with no regression.

## Testing Expectations
Unit test (pytest). Run the targeted test, then the full suite once per `rules/toolchain.md`.

## Documentation Impact
Once the test lands and passes, remove the CI-009 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 (Known Issues), and update the CI-009/010/012/014/016 batching note to reflect one fewer remaining member (and drop CI-009 from any `Related` cross-references).

## Out of Scope
- CI-010, CI-012, CI-014, CI-016 — tracked as separate issues.
- Any change to `config_loader.py`'s actual behavior (already confirmed correct; this is a test-coverage-only gap).

## Dependencies
N/A: none. (The shared batching note in `governance_03` should be updated once all 5 sibling issues land, but each is independently completable.)

## Unresolved Questions
N/A: none — the per-area ownership recommendation (`@db-admin` for this item) was already established via a 2026-09-27 deep-dive investigation; confirm with the owner only if a formal RACI sign-off is required before starting.

## AI Implementation Instruction
Add only the missing test. Do not modify `scripts/shared/config_loader.py` unless the new test reveals an actual bug (none is currently expected, per the code-inspection evidence already recorded in CI-009). Keep the diff scoped to the new test file/function only.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211337
- **Related target files**: tests/shared/ (new test), scripts/shared/config_loader.py (reference)
