# CI-002 cites an ADR-011 invariant number/content that does not exist in any current document

## Priority
Medium

## Summary
`docs/90_shared_90_inconsistencies_and_known_issues.md`'s CI-002 entry claims
`recover_corruption()` violates "ADR-011 INV-01/INV-02" for a production-vs-local
auto-recovery distinction. Neither the pre-deletion ADR-011 text nor the consolidated
ADR-008 (which absorbed ADR-011 on 2026-08-31) contains any such invariant or any
production/local distinction for recovery. This entry appears to reference a stale,
since-superseded draft of ADR-011.

## Background
Discovered while merging ADR-011 into ADR-008 (2026-08-31) and reading ADR-011 in full to
classify its content. ADR-011's actual Invariants were INV-01 (`sqlite3.DatabaseError` must
not propagate unclassified) through INV-05 (lock/permission not classified as corruption);
none of them referenced a production/local distinction. CI-002's cited "INV-01 (production
MUST NOT auto-recover without explicit operator confirmation)" and "INV-02 (local MAY
auto-recover)" do not match this content.

## Problem
(Evidence: Needs confirmation) It is unclear whether (a) CI-002 describes a real, still-open
gap in `recover_corruption()` — i.e., production and local environments should behave
differently, but this requirement was never written into any current ADR — or (b) CI-002 is
simply stale, referencing an early ADR-011 draft whose numbering/content was rewritten before
the ADR-011 text read during this consolidation.

## Reason for Change
A Known Issue that cites an invariant number absent from any current, readable ADR misdirects
anyone investigating recovery behavior — they cannot verify the claim against source material,
and may either dismiss a real gap or chase a non-existent one.

## Implementation Intent
Investigate whether a production/local distinction for automatic DB recovery is an intended
current requirement anywhere in the design documentation set (other ADRs, Specifications, or
team design intent). If it is a real, currently-desired requirement, raise it as a new Decision
against ADR-008 (which now owns recovery policy) rather than reinstating a reference to the
deleted ADR-011. If it is not a current requirement, rewrite or close CI-002 to reflect that no
such invariant currently exists.

## Target Files or Areas
- `docs/90_shared_90_inconsistencies_and_known_issues.md` (CI-002)
- `docs/adr/ADR-008-sqlite-4db-separation.md` (only if a real requirement is confirmed and added)

## Required Changes
- Investigate prior ADR-011 drafts (git history, if recoverable) or consult the architecture
  owner to determine whether a production/local recovery distinction was ever an intended
  requirement.
- If yes: draft a new Decision Detail/Invariant for ADR-008 and update CI-002 to reference it.
- If no: rewrite CI-002 to describe the actual current state (no production/local distinction
  exists; `recover_corruption()` behaves identically regardless of environment) and reclassify
  its status/severity accordingly.

## Constraints
Do not invent a production/local distinction into ADR-008 without owner confirmation — ADR-008's
current, merged content deliberately contains no such distinction.

## Acceptance Criteria
- CI-002 no longer cites an ADR-011 invariant number that does not exist in any current document.
- CI-002's Design reference points to ADR-008 (or a new decision within it) rather than the
  deleted ADR-011 file.
- The entry's Status accurately reflects whether this is a confirmed gap, a stale/closed
  reference, or a newly-adopted requirement.

## Testing Expectations
Documentation-only unless a new ADR-008 requirement is adopted, in which case follow that
requirement's own testing expectations.

## Documentation Impact
This issue is itself the documentation-accuracy fix for CI-002.

## Out of Scope
- Any other CI-xxx entry in the same file.
- Re-litigating ADR-008's already-decided recovery policy for rag/session/workflow/eventbus.

## Dependencies
Follows the 2026-08-31 ADR-011 → ADR-008 consolidation.

## Unresolved Questions
Whether a production/local recovery distinction was ever a real intended requirement — this is
the central question this issue exists to resolve; do not guess at an answer.

## AI Implementation Instruction
Do not edit ADR-008's Decision or Invariants to add a production/local distinction without
explicit confirmation that this is a current, owner-approved requirement. If no such
confirmation can be obtained, limit the change to correcting CI-002's text and reference.
