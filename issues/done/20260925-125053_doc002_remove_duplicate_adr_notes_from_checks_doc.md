# Remove duplicate ADR notes from 00_governance_04_documentation-checks.md

## Priority
Low

## Summary
Remove the duplicate ADR notes section from `docs/00_governance/00_governance_04_documentation-checks.md` manual check #11 (ADR Section Header Compliance). The exact same three bilingual notes are duplicated verbatim in `docs/00_governance/00_governance_01_documentation-policy.md` line 386-388. This creates the same drift risk as L-1.

## Background
Both governance documents contain identical ADR duplicate notes under their respective ADR Section Header Standardization / ADR Section Header Compliance sections:

```
- "この章は設計判断の根拠にしない" (Do not use this chapter as the basis for design decisions)
- "該当しない場合は「対象外」と記載する" (If not applicable, write "Not applicable")
- "ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する" (ADR text must not be unconditionally aligned to current implementation; manage discrepancies via Known Issues)
```

The policy document defines the ADR section header standard. The checks document describes how to verify compliance with that standard.

## Problem
Identical ADR notes appear in two governance documents. Maintaining both increases review burden and creates silent-drift risk.

## Reason for Change
Consistency with the single-source-of-truth approach applied elsewhere in the checks document. The policy document defines ADR standards; the checks document verifies compliance. The notes belong in the policy definition, not duplicated in the verification procedure.

## Implementation Intent
Delete the "Duplicate notes shared across all ADRs" bullets from manual check #11 in `00_governance_04_documentation-checks.md`. Keep the section header list (items 1-14) and add a cross-reference to the policy document's ADR Section Header Standardization section for the duplicate notes.

## Target Files or Areas
- `docs/00_governance/00_governance_04_documentation-checks.md`

## Required Changes
- In manual check #11 (ADR Section Header Compliance), remove the three "Duplicate notes shared across all ADRs" bullet lines
- Optionally add a brief note referencing the policy document's equivalent section for completeness

## Constraints
- Do not modify `00_governance_01_documentation-policy.md`
- Preserve the 14-item section header list in check #11
- Preserve surrounding content (Manual Checks numbering, subsequent checks #12-16, Governance Verification Matrix)

## Out of Scope
- Modifying the authoritative ADR notes in the policy document
- Changing the ADR section header order or content
- Modifying any other manual or automated checks

## Dependencies
- None

## Acceptance Criteria
- [ ] Duplicate ADR notes removed from manual check #11 in `00_governance_04_documentation-checks.md`
- [ ] 14-item section header list preserved intact
- [ ] No other content in `00_governance_04_documentation-checks.md` modified
- [ ] Policy document unchanged
- [ ] `uv run python tools/check_docs_structure.py docs/00_governance/00_governance_04_documentation-checks.md` passes

## Testing Expectations
Not required — documentation-only change. Manual verification that check #11 remains structurally coherent.

## Documentation Impact
This is a deduplication in governance documents. Three bullet lines are removed from one section.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Perform exactly one edit in `docs/00_governance/00_governance_04_documentation-checks.md`: locate manual check #11 "ADR Section Header Compliance", find the "Duplicate notes shared across all ADRs:" line and its three bullet points (Japanese + English parenthetical translations), delete them entirely. Do not touch any other file. After editing, verify `check_docs_structure.py` reports no new issues.

## Traceability
- **Workflow phase**: issue-creator
- **Source finding**: L-2 from governance folder audit (2026-09-25)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-125053
- **Related target files**: docs/00_governance/00_governance_04_documentation-checks.md
