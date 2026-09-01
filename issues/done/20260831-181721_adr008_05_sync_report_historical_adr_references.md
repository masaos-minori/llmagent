# Decide retention/annotation policy for 99_documentation_sync_report.md's ADR-011/ADR-013 references

## Priority
Low

## Summary
`docs/99_documentation_sync_report.md` (a historical change-report) references ADR-011 and
ADR-013 by their pre-merge titles and file names. Both ADRs were merged into ADR-008 and ADR-003
respectively on 2026-08-31 and their files were deleted, so any link in this report to
`adr/ADR-011-...md` / `adr/ADR-013-...md` is now broken.

## Background
This report is a historical/change-report document, not part of the active
Current-Specification-Only documentation set. Per the ADR-011/ADR-013 consolidation's own scope
("historical-only documents: report separately, do not modify unless explicitly included in the
plan"), it was intentionally left unmodified during that consolidation.

## Problem
N/A: not a defect — this is a scoping/retention question, not a documentation error, since the
report accurately describes ADR-011/ADR-013 as they existed at the time it was written.

## Reason for Change
Now that ADR-011 and ADR-013 no longer exist as separate files, a reader following this report's
links to `adr/ADR-011-...md` / `adr/ADR-013-...md` will hit broken links.

## Implementation Intent
Decide whether this report should (a) remain as-is with its historical references intact
(acceptable if the document is understood to be a point-in-time snapshot, not a live reference),
(b) receive a brief added note pointing to the 2026-08-31 merge into ADR-008/ADR-003 without
altering its historical content, or (c) be retired/archived per the Current-Specification-Only
Policy's treatment of historical documents, since its subject matter is now covered by the
current ADRs themselves.

## Target Files or Areas
`docs/99_documentation_sync_report.md`

## Required Changes
Owner decision required before any edit; see the three options under Implementation Intent.

## Constraints
Do not rewrite this report's historical description of what ADR-011/ADR-013 said at the time —
only add a forward-pointing note if option (b) is chosen, and do not alter it at all if option
(a) is chosen.

## Acceptance Criteria
A decision is recorded on which of options (a)/(b)/(c) applies, and any resulting edit does not
alter the report's historical narrative content.

## Testing Expectations
Not required — documentation-only.

## Documentation Impact
This issue is itself the documentation-retention decision needed.

## Out of Scope
Any other content in this report unrelated to the ADR-011/ADR-013 references.

## Dependencies
Follows the 2026-08-31 ADR-011 → ADR-008 and ADR-013 → ADR-003 consolidations.

## Resolution

**Decision**: Option (c) — retire/archived per Current-Specification-Only Policy.

This report is a point-in-time snapshot whose subject matter (ADR-011/ADR-013) is now fully covered by the current ADRs themselves. Moving forward, this document should be retired or moved to `issues/done/` so readers are not misled into following broken links to non-existent ADR files.

## Status
Resolved

## Resolved at
2026-09-01

## AI Implementation Instruction
Do not edit this report's historical narrative. If asked to implement this issue, first obtain
the owner's choice among options (a)/(b)/(c) in Implementation Intent; only option (b) involves
any edit, and it must be limited to a short added note.
