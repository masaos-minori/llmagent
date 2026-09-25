# Remove duplicate Maintenance Rules from 00_governance_04_documentation-checks.md

## Priority
Low

## Summary
Remove the `## Maintenance Rules` section from `docs/00_governance/00_governance_04_documentation-checks.md`. The exact same three rules are duplicated verbatim in `docs/00_governance/00_governance_01_documentation-policy.md` line 520-524. Having identical maintenance rules in two places creates drift risk: updating one without the other leaves stale policy text.

## Background
Both governance documents define their own `## Maintenance Rules` section with identical content:
- New ADRs must be created within one week of the decision being made
- "Proposed" ADRs must be reviewed quarterly
- "Needs confirmation" items must be reviewed quarterly

The policy document (`00_governance_01_documentation-policy.md`) is the authoritative source for governance policies. The checks document (`00_governance_04_documentation-checks.md`) references the policy document in multiple places (Merge Conditions, Review Rule, Change Impact Rule) and should continue to defer to it for policy definitions.

## Problem
Identical maintenance rules appear in two governance documents. When rules change, both locations must be updated — increasing review burden and creating a silent-drift vector where one location gets updated and the other does not.

## Reason for Change
Single-source-of-truth principle: governance policies should be defined once and referenced, not duplicated. The checks document already follows this pattern for Merge Conditions, Review Rule, and Change Impact Rule by referencing the policy document. Maintenance Rules should follow the same pattern.

## Implementation Intent
Delete the entire `## Maintenance Rules` section from `docs/00_governance/00_governance_04_documentation-checks.md`. Add a single cross-reference line pointing readers to the policy document, consistent with how other sections in the checks document reference the policy document (e.g., "See [Policy's Merge Conditions](...)").

## Target Files or Areas
- `docs/00_governance/00_governance_04_documentation-checks.md`

## Required Changes
- Delete the `## Maintenance Rules` heading and its three bullet points from `00_governance_04_documentation-checks.md`
- Replace with a single line: `- [Maintenance Rules](00_governance_01_documentation-policy.md#maintenance-rules)` or similar cross-reference

## Constraints
- Do not modify `00_governance_01_documentation-policy.md` (the authoritative source)
- Preserve surrounding section structure (Non-Goals, Related Documents, Keywords must remain intact)
- Do not alter any other content in the checks document

## Out of Scope
- Modifying the authoritative Maintenance Rules in the policy document
- Adding automated enforcement of maintenance rule compliance
- Changing the review cadence values themselves

## Dependencies
- None

## Acceptance Criteria
- [ ] `## Maintenance Rules` section removed from `00_governance_04_documentation-checks.md`
- [ ] Cross-reference to policy document's Maintenance Rules section added in place
- [ ] No other content in `00_governance_04_documentation-checks.md` modified
- [ ] Policy document unchanged
- [ ] `uv run python tools/check_docs_structure.py docs/00_governance/00_governance_04_documentation-checks.md` passes (no new broken links)

## Testing Expectations
Not required — documentation-only change. Manual verification that the cross-reference resolves correctly.

## Documentation Impact
This is a deduplication in governance documents. One section is removed, replaced with a cross-reference.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Perform exactly one edit in `docs/00_governance/00_governance_04_documentation-checks.md`: locate the `## Maintenance Rules` heading (near end of file, before `## Non-Goals`), delete the heading and its three bullet points, replace with a single cross-reference line pointing to the policy document's Maintenance Rules section. Do not touch any other file. After editing, verify `check_docs_structure.py` reports no new issues.

## Traceability
- **Workflow phase**: issue-creator
- **Source finding**: L-1 from governance folder audit (2026-09-25)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-125053
- **Related target files**: docs/00_governance/00_governance_04_documentation-checks.md
