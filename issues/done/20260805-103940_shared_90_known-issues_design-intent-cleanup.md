# Reduce template-memo-style detail in docs/90_shared_90_inconsistencies_and_known_issues.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_90_inconsistencies_and_known_issues.md`: keep the operational meaning of known issues (including SHARED-001's impact); remove the full 17-field template, unverified metadata, and migration notes.

## Reason for Change
This chapter is the canonical source for known issues (per `memo-doc-shared-review.md` §「章間の正本ルール」: 既知問題・未解決事項 = `90_shared_90_inconsistencies_and_known_issues`), but a Known Issues section that degrades into a metadata-field template loses its value as an operational reference, per this memo's explicit prohibition (§「禁止事項」: Known Issues を単なるバグ一覧にすること).

## Implementation Intent
Restructure each entry to explain what the issue means, why it matters, operational cautions, and fix-decision criteria — not a metadata template. Explicitly retain SHARED-001 (`recover_corruption` propagating an exception instead of a `RecoveryResult` on real page corruption) and its unresolved status.

## Target Files or Areas
`docs/90_shared_90_inconsistencies_and_known_issues.md`

## Required Changes
- Keep: the meaning of each known issue, why it is a problem, operational cautions, fix-decision criteria, SHARED-001's impact, that `recover_corruption` can propagate an exception on real page corruption, that this remains unresolved.
- Remove or compress: the full 17-field issue template, unverified metadata fields (Owner / First Found / Target / Related), migration notes, detailed implementation file/test names, a mechanical documentation-gap classification.
- Before removing any entry, verify against current code per `rules/coding.md` §「Documentation notes — "Current behavior" classification」 whether the discrepancy still applies; do not delete a note without this verification.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 where applicable to a known-issues chapter.
- No entry uses the full 17-field template or unverified metadata fields; each entry states operational meaning instead.
- Every entry is classified per `rules/coding.md`'s five-way classification (Accepted current specification / Implementation fix required / Documentation fix required / Issue already tracked / Obsolete and removable) before being kept, cross-referenced, or deleted.
- SHARED-001's impact and unresolved status remain explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task. Coordinate with `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`'s cleanup issue so SHARED-001 is not duplicated across both chapters — that chapter should cross-reference here instead of re-explaining.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Fixing the underlying `recover_corruption` code issue itself (a separate implementation issue if pursued).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_90_inconsistencies_and_known_issues」 and `rules/coding.md`'s "Current behavior" classification table. Do not edit code — if a code fix for SHARED-001 is warranted, file it as a separate issue rather than implementing it here. Do not silently delete a discrepancy note without first verifying against current code that it no longer applies. Mark unclear items as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_90_inconsistencies_and_known_issues」
- Generated at: 2026-08-05
