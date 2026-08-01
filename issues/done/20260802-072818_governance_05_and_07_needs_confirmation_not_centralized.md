# Add docs/00_governance_05's 4 uncentralized Needs Confirmation items to the docs/00_governance_07 inventory

## Priority
High

## Summary
`docs/00_governance_05_deprecated-items.md` marks 4 items (`config/rag_pipeline.toml`, `common.toml`, workflow optional mode, shared common config) with "Status: Needs confirmation" using an ad-hoc Current Replacement/Status/Notes/Evidence format, but none of the 4 appear in `docs/00_governance_07`'s centralized NC-001–017 inventory, contradicting 07's stated purpose of centralized management.

## Reason for Change
07's Extraction Process appears not to be run against all `docs/*.md` files, meaning readers who trust 07 as the single source for open Needs Confirmation items will silently miss these 4.

## Implementation Intent
Convert the 4 items in 05 to the standard NC entry format defined by 07 (using the field definition reconciled in the related 03/07 field-mismatch issue) and add them to 07's inventory as new NC entries, without altering their underlying content or meaning.

## Target Files or Areas
`docs/00_governance_05_deprecated-items.md`, `docs/00_governance_07_needs-confirmation-inventory.md`

## Required Changes
- Extract the 4 Needs Confirmation items currently in 05.
- Reformat each into 07's standard entry template.
- Add them to 07 as new NC entries, continuing the NC-XXX numbering.
- Replace or link the entries in 05 to their canonical location in 07 to avoid re-duplication.

## Acceptance Criteria
All 4 items appear as properly-formatted entries in `docs/00_governance_07`'s inventory; `docs/00_governance_05` no longer maintains a separate, non-standard Needs Confirmation format for these items.

## Testing Expectations
Not required (documentation-only). Manually re-run the Extraction Process description against `docs/*.md` after the change to confirm no other files have uncentralized Needs Confirmation items.

## Documentation Impact
`docs/00_governance_05` and `docs/00_governance_07` updated; the Extraction Process description in 07 may need a note that it must cover all `docs/*.md`, not only a subset.

## Out of Scope
Do not resolve the underlying substance of the 4 Needs Confirmation questions themselves in this issue — only centralize their tracking.

## AI Implementation Instruction
Depends on the field-definition reconciliation issue (docs/00_governance_03 vs 07) being decided first, or decide the format inline if that issue is not yet done. Do not lose any of the 4 items' original content during reformatting.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §1 (連結文書としての問題), §6 Needs confirmation items (05 フォーマット不備と07未収載 / 07 に05項目が未収載である理由)
- Generated at: 2026-08-02
