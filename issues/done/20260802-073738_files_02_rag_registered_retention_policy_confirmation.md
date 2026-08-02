# Confirm and document the registered/ retention policy in docs/01_overview-files-02-rag.md

## Priority
Low

## Summary
`docs/01_overview-files-02-rag.md` (~lines 27-34) documents a naming convention indicating state transitions, but does not state the retention/cleanup policy for files under `registered/`.

## Reason for Change
The naming convention itself is valuable state-transition information, but without a stated retention policy, disk-usage operational decisions cannot be made confidently from this document alone.

## Implementation Intent
Check whether the retention policy is documented elsewhere (e.g. `docs/03_rag_*.md` files, out of this review's scope); if found, add a cross-reference here; if not found, add an explicit Needs Confirmation note.

## Target Files or Areas
`docs/01_overview-files-02-rag.md`; check `docs/03_rag_*.md` for existing coverage.

## Required Changes
- Search `docs/03_rag_*.md` for any existing statement of `registered/` retention/cleanup policy.
- If found, add a one-line cross-reference from this file to that documentation.
- If not found, add an explicit note: "`registered/`配下のファイル保持期間・クリーンアップ方針は本ドキュメント範囲では未確認(要確認)。"

## Acceptance Criteria
Either a cross-reference to existing retention-policy documentation is added, or an explicit Needs Confirmation note is present — the gap is not left silently unaddressed.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/01_overview-files-02-rag.md` gains either a cross-reference or an explicit Needs Confirmation note.

## Out of Scope
Do not implement any retention/cleanup mechanism in this issue — documentation only.

## AI Implementation Instruction
Check `docs/03_rag_*.md` files before concluding the policy is undocumented elsewhere — do not add a Needs Confirmation note without first searching.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §3 要約候補 item 4, §6B (registered/配下の保持方針)
- Generated at: 2026-08-02
