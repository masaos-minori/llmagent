# Reduce implementation-derived detail in docs/05_agent_00_document-guide.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to `docs/05_agent_00_document-guide.md`: keep the document focused on navigation and governance, remove mechanical file/link inventories that duplicate what code search already shows.

## Reason for Change
The current `05_agent_*.md` set mixes design/operational judgment with content that is mechanically derivable from code (exhaustive file indexes, keyword lists). This makes the doc set stale-prone and harder to use as a decision reference. `memo-doc-agent-review.md` was written specifically to identify what to keep vs. remove per chapter.

## Implementation Intent
Restructure this chapter to serve as the doc-guide entry point: overall purpose of the doc set, chapter structure, "which question maps to which chapter," the Canonical Source Rule, and how Known Issues / Deprecated Items / Needs Confirmation are handled. Do not turn this into a full API or file reference.

## Target Files or Areas
`docs/05_agent_00_document-guide.md`

## Required Changes
- Keep: overall purpose of the doc set, chapter structure, question-to-chapter navigation, Canonical Source Rule, handling of Known Issues / Deprecated Items / Needs Confirmation.
- Remove or compress: overly detailed file indexes, mechanical duplication of link lists, keyword enumeration, implementation-diff-memo-style notes.
- Where information is removed, verify it is not the sole source of a fact needed elsewhere before deleting.

## Acceptance Criteria
- The chapter follows the template in `memo-doc-agent-review.md` §「修正後の章構成テンプレート」 (目的 / 設計意図 / 責務境界 / 主要な制約 / 運用上の注意 / 既知の制限・未解決事項 / 関連資料) where applicable to this chapter's role as a guide.
- No mechanical file/keyword listing remains that duplicates content already covered by `tools/check_agent_docs_consistency.py` or code search.
- Any judgment that could not be reconstructed from the current doc is recorded as `Needs Confirmation` rather than invented.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing to confirm no broken internal links or removed-file references were introduced.

## Documentation Impact
This issue is itself a documentation-only cleanup task; no other doc changes are in scope.

## Out of Scope
- Other `docs/05_agent_*.md` chapters (tracked in separate issues).
- Any `docs/04_mcp_*.md`, `docs/03_rag_*.md`, or `docs/02_deploy_*.md` files.
- Code changes.

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_00_document-guide」 exactly for what to keep/remove. Do not rewrite content beyond this chapter. If a design rationale is not recoverable from the current text, mark it `Needs Confirmation` per `memo-doc-agent-review.md` §「情報不足時の扱い」 instead of guessing.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_00_document-guide」
- Generated at: 2026-08-05
