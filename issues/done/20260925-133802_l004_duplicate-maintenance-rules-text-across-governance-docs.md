# Duplicate Maintenance Rules text across governance policy and checks documents

## Priority
Low

## Summary
Align the Maintenance Rules presentation in `docs/00_governance/00_governance_01_documentation-policy.md` with the deduplication pattern applied to `docs/00_governance/00_governance_04_documentation-checks.md`. The checks doc was previously updated to use a cross-reference to the policy doc's Maintenance Rules section. The policy doc still contains the raw three-bullet text, creating an asymmetry: one document defers to the other, but the source document does not acknowledge the deference relationship.

## Background
In commit `df6cf9eb` (doc001), the `## Maintenance Rules` section was removed from `00_governance_04_documentation-checks.md` and replaced with a cross-reference to `00_governance_01_documentation-policy.md#maintenance-rules`. However, `00_governance_01_documentation-policy.md` lines 520-524 still contain the verbatim three-bullet Maintenance Rules text:
- New ADRs must be created within one week of the decision being made
- "Proposed" ADRs must be reviewed quarterly
- "Needs confirmation" items must be reviewed quarterly

The policy doc is the authoritative source. The checks doc correctly defers to it. But the policy doc does not reference the checks doc's adoption of this cross-reference pattern, leaving the deduplication one-directional.

## Problem
The deduplication effort (doc001) fixed the symptom in the checks document but did not establish a bidirectional awareness between the two documents. If future maintenance rules changes are made only in the policy doc, the checks doc's cross-reference will remain correct. But if someone edits the policy doc's Maintenance Rules without knowing the checks doc exists as a consumer, they lose the opportunity to add a "consumed by" note. More importantly, the asymmetry signals incomplete cleanup — the governance corpus should have a clear source-of-truth chain, not a one-way pointer.

## Reason for Change
Completing the deduplication pattern established by doc001. Governance documents should have explicit, bidirectional awareness of their cross-reference relationships to prevent accidental divergence during future edits.

## Implementation Intent
Add a brief "Consumed By" or "Referenced In" note at the end of the Maintenance Rules section in `00_governance_01_documentation-policy.md`, pointing to the checks document's cross-reference. This establishes the full circle: policy → checks (cross-ref) → policy (consumer note). Keep the change minimal — one sentence addition, no restructuring.

## Target Files or Areas
- `docs/00_governance/00_governance_01_documentation-policy.md`

## Required Changes
- Add a single line after the three Maintenance Rules bullets (around line 524): `- Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)` or equivalent cross-reference noting that the checks document defers to this section
- Ensure the added line follows the same formatting convention as other cross-references in the policy document

## Constraints
- Do not modify the three bullet points themselves
- Do not add a second copy of the Maintenance Rules anywhere
- Do not modify `00_governance_04_documentation-checks.md` (already correct)
- Keep the addition to a single line

## Acceptance Criteria
- [ ] `00_governance_01_documentation-policy.md` Maintenance Rules section includes a cross-reference to the consuming document (`00_governance_04_documentation-checks.md`)
- [ ] The three original bullet points are unchanged
- [ ] No additional content added beyond the consumer cross-reference
- [ ] `uv run python tools/check_docs_structure.py docs/00_governance/00_governance_01_documentation-policy.md` passes

## Testing Expectations
Not required — documentation-only change. Manual verification that the cross-reference resolves correctly.

## Documentation Impact
This is a governance document consistency improvement. One line added to establish bidirectional awareness.

## Out of Scope
- Applying this bidirectional pattern to other sections (e.g., Merge Conditions, Review Rule, Change Impact Rule) — those are separate opportunities
- Restructuring the Maintenance Rules section
- Adding automated enforcement of cross-reference symmetry

## Dependencies
- None

## Unresolved Questions
- Should the bidirectional consumer-note pattern be codified as a general governance writing convention in the policy document?
- Are there other policy→checks cross-references that lack reverse pointers?

## AI Implementation Instruction
Perform one edit in `docs/00_governance/00_governance_01_documentation-policy.md`: after line 524 (the third Maintenance Rules bullet), insert a single line: `- Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)`. Verify no other content is changed. Run `check_docs_structure.py` on the file to confirm no new broken links.

## Traceability
- **Workflow phase**: issue-creator
- **Source finding**: L-4 from governance folder audit (2026-09-25)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-133802
- **Related target files**: docs/00_governance/00_governance_01_documentation-policy.md
