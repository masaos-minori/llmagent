# Decide the relationship between front matter related and Related Documents

## Priority
Low

## Summary
Obtain an owner decision on whether front matter's `related` field and the body `## Related Documents` section are an intentional duality or unintentional drift, closing Needs Confirmation item NC-031.

## Background
NC-031 records that both `related` (front matter) and `## Related Documents` (body heading) exist in active use across the document set, with no design rationale found in `governance_01_documentation-policy.md` or `governance_02_documentation-metadata.md` explaining why both exist.

## Problem
This issue's own spot check found the two lists have already diverged in at least one document: `docs/00_governance/governance_01_documentation-policy.md`'s front-matter `related:` lists `../00_index.md` and `../01_overview/overview_00_document-guide.md`, while its body `## Related Documents` lists `governance_02_documentation-metadata.md`, `governance_03_issue-and-uncertainty-management.md`, `governance_04_documentation-checks.md`, and `../10_adr/adr-index.md` — zero overlap between the two lists. This is consistent with one plausible reading (front matter points to fixed navigation entry points; the body section points to substantive cross-references) but is not documented as intentional anywhere, so a reader cannot distinguish that reading from accidental drift.

## Reason for Change
Without a recorded decision, this ambiguity will keep resurfacing, and any future tooling that assumes the two fields should agree (e.g. a consistency checker) would misfire against this repository's actual, apparently-intentional pattern.

## Implementation Intent
Present the owner with this issue's finding (the fields already diverge, in a way that looks like a deliberate front-matter-for-navigation vs. body-for-cross-reference split) and ask for a ruling: document this as the intended distinction, or treat it as drift to reconcile. Do not decide unilaterally which reading is correct — this is a documentation-design decision, not a fact this issue can resolve through more code investigation.

## Target Files or Areas
- `docs/00_governance/governance_02_documentation-metadata.md` (Existing Metadata Fields — `related`)
- `docs/00_governance/governance_01_documentation-policy.md` (used as this issue's concrete divergence example)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (NC-031 entry)

## Required Changes
- Present the owner with the confirmed divergence example and the two candidate readings (intentional dual-purpose vs. drift).
- Record the owner's decision in `governance_02_documentation-metadata.md`'s `related` field description.
- If ruled intentional: state the distinction explicitly (e.g. front matter = tooling-facing navigation entry points, body = human-facing cross-references).
- If ruled drift: decide which field is authoritative and file a separate follow-up issue to reconcile existing documents — do not perform that reconciliation as part of this issue.
- Remove NC-031 from Active Items once the decision is recorded.

## Constraints
N/A: this issue itself is a decision-recording task; any resulting reconciliation work is a separate, larger issue.

## Acceptance Criteria
- The owner's decision (intentional duality vs. drift) is recorded in `docs/00_governance/governance_02_documentation-metadata.md`.
- NC-031 is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items.

## Testing Expectations
Not required: documentation/decision task, no behavior change.

## Documentation Impact
Update `docs/00_governance/governance_02_documentation-metadata.md`'s `related` field description to record the decision. Remove the NC-031 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` once resolved.

## Out of Scope
- Reconciling any specific document's `related` vs. `## Related Documents` content — that is separate follow-up work if the owner rules this is drift.
- Building tooling to auto-generate one field from the other.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none — the decision itself is this issue's entire content.

## AI Implementation Instruction
Do not reconcile any document's `related`/`## Related Documents` content as part of this issue, and do not decide which reading is correct unilaterally — present the evidence and record whichever decision the owner gives.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-115902
- **Related target files**: docs/00_governance/governance_02_documentation-metadata.md
