# Reconcile front-matter `related` field with body `## Related Documents` headings

## Priority
Low

## Summary
Reconcile every `docs/*.md` document's front-matter `related:` list against its body
`## Related Documents` heading so the two converge, per the owner's ruling on NC-031
that front-matter `related:` is authoritative.

## Background
NC-031 (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`) tracked
whether the front-matter `related` field and the body `## Related Documents` heading were
expected to match. During `implementations/20260927-124641_01_docs_00_governance_governance_02_documentation-metadata.md.md`'s
execution, the owner ruled: this is drift, not intentional duality — front-matter
`related:` is authoritative, and body `## Related Documents` headings should be
reconciled to match it going forward.

## Problem
Confirmed example (`docs/00_governance/governance_01_documentation-policy.md`):
front-matter `related:` lists `../00_index.md` and
`../01_overview/overview_00_document-guide.md`, while the body `## Related Documents`
heading lists `governance_02_documentation-metadata.md`,
`governance_03_issue-and-uncertainty-management.md`,
`governance_04_documentation-checks.md`, and `../10_adr/adr-index.md` — zero overlap.
This pattern has not been checked across the rest of `docs/`, so the total scope of
drift is currently unknown.

## Reason for Change
`docs/00_governance/governance_02_documentation-metadata.md`'s `related` field
description now states that front-matter `related:` is authoritative over the body
heading when they diverge. Leaving existing documents unreconciled means the stated
policy does not yet match actual document content repository-wide.

## Implementation Intent
For each `docs/*.md` file, compare its front-matter `related:` list against its body
`## Related Documents` heading (where both exist) and reconcile the body heading to
match the front-matter list — adding missing entries and removing ones no longer in
front matter — rather than the reverse, since front matter is now the authoritative
source per the owner's ruling.

## Target Files or Areas
All `docs/*.md` files that have both a front-matter `related:` list and a body
`## Related Documents` heading. Not yet enumerated — a first implementation step should
inventory the full set via `rg` before editing any file.

## Required Changes
- Inventory every `docs/*.md` file with both a front-matter `related:` list and a body
  `## Related Documents` heading, and record where the two diverge.
- For each divergent file, update the body `## Related Documents` heading to match the
  front-matter `related:` list.
- Confirm `docs/00_governance/governance_02_documentation-metadata.md`'s `related`
  field description (already updated by this issue's originating cycle) accurately
  reflects the reconciled state as the ongoing policy, not a one-time note.

## Constraints
N/A: none beyond the existing Documentation content policy (`skills/DESIGN.md`).

## Acceptance Criteria
- Every `docs/*.md` file with both a front-matter `related:` list and a body
  `## Related Documents` heading has matching entries between the two.
- `docs/00_governance/governance_01_documentation-policy.md`'s own divergence
  (the confirmed example in Problem) is resolved as part of this issue.

## Testing Expectations
`uv run python tools/check_docs_structure.py` and `uv run python tools/check_docs_quality.py`
after each edit, per `routing.md` Tools → "When to run which tool". No code behavior is
affected.

## Documentation Impact
This issue is itself documentation reconciliation work — no further Known
Issue/Needs Confirmation entry is needed once complete.

## Out of Scope
- Changing the authoritative-field ruling itself (already decided).
- Any `docs/*.md` file that has only one of the two (front-matter `related:` or body
  `## Related Documents`), not both.

## Dependencies
N/A: none.

## Unresolved Questions
The full inventory of affected files across `docs/` has not been enumerated — the
first implementation step must do this via `rg` before scoping the actual edit list.

## AI Implementation Instruction
Enumerate affected files first; do not edit any file's body heading without first
confirming its own front-matter `related:` list via Read. Apply
`skills/python-documentation` conventions for the edit itself.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121543_plan.md
- **Source implementation procedure**: implementations/done/20260927-124641_01_docs_00_governance_governance_02_documentation-metadata.md.md
- **Generated at**: 20260927-160936
- **Related target files**: docs/*.md (full set not yet enumerated; see Unresolved Questions)
