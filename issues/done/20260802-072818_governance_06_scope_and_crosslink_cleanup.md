# Fix docs/00_governance_06 scope mismatch (Markdown notation rules) and add missing cross-link to 00_governance_01

## Priority
Medium

## Summary
`docs/00_governance_06_ai-reading-metadata.md` is scoped to "AI reading metadata," but its trailing "Markdown記法ルール" section is an unrelated general Markdown formatting convention. Separately, its "実装参照で確認できる情報の記載方針" section (near-identical to this review's own delete/summarize/keep classification criteria) is high-value but not linked from `docs/00_governance_01`, where readers would expect to find core documentation-writing rules.

## Reason for Change
The scope mismatch makes the file harder to navigate, and the important 記載方針 rule risks going unnoticed by readers looking for core rules in 01.

## Implementation Intent
Move the Markdown notation rules out of 06 (into 01 or a dedicated style guide), leaving a one-line pointer in 06. Add a cross-reference from `docs/00_governance_01` to 06's 記載方針 section. Do not duplicate full rule text in both places.

## Target Files or Areas
`docs/00_governance_06_ai-reading-metadata.md`, `docs/00_governance_01_documentation-governance.md`

## Required Changes
- Relocate the "Markdown記法ルール" content out of 06 into 01 (or a new style-guide reference), replacing it in 06 with a one-line pointer.
- Add a cross-reference from 01 to 06's "実装参照で確認できる情報の記載方針" section.

## Acceptance Criteria
06 no longer contains unrelated Markdown formatting rules as inline content; 01 links to 06's 記載方針 section; no information is lost across the move (verify both target locations after editing).

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_governance_01` and `docs/00_governance_06` both updated.

## Out of Scope
Do not rewrite the substance of the Markdown rules or the 記載方針 rule itself — only their location/cross-references.

## AI Implementation Instruction
Read both files fully before editing to avoid losing content during the move. Keep the moved content's wording intact unless adjustment is needed to fit the new location's context.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §3 要約候補 item 4, §4 強化候補 (docs/00_governance_06 記載方針)
- Generated at: 2026-08-02
