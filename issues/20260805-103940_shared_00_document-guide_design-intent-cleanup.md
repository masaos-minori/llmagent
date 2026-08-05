# Reduce implementation-derived detail in docs/90_shared_00_document-guide.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_00_document-guide.md`: keep it as the shared/db doc-set entry point (navigation, Canonical Source Rule, Known Issues handling, safety-relevant AI-use guidance); remove overly detailed file indexes and AI-query-routing granularity.

## Reason for Change
`docs/90_shared_*.md` currently mixes design/operational judgment with content mechanically derivable from code (full type field lists, DDL, function signatures, module-by-module API tables). `memo-doc-shared-review.md` was written to identify what each chapter should keep vs. remove; this issue covers the entry-point chapter, which must remain a reading guide rather than a design-doc substitute (per the memo's explicit 注意 for this chapter).

## Implementation Intent
Restructure this chapter to serve purely as navigation: doc-set purpose, high-level chapter guidance, the Canonical Source Rule, Known Issues handling, and only the safety/design-relevant subset of "Guidance for Safe AI Use." Do not let this chapter substitute for the design body.

## Target Files or Areas
`docs/90_shared_00_document-guide.md`

## Required Changes
- Keep: the purpose of the shared/db doc set, high-level chapter navigation, the Canonical Source Rule, how Known Issues are handled, the subset of "Guidance for Safe AI Use" relevant to operational/design judgment.
- Remove or compress: an overly detailed File Index, an overly fine-grained AI Query Routing Table, keyword enumeration, a mechanical full-file-name listing, safety-memo duplication that is closer to implementation detail.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 where applicable to a navigation-guide chapter.
- No mechanical file index or AI-query-routing table remains at excessive granularity.
- This chapter is not used as a substitute for design content that belongs in other chapters.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated shared/db docs-consistency script currently exists (only `check_agent_docs_consistency.py` / `check_mcp_docs_consistency.py` / `check_rag_docs_consistency.py` / `check_deployment_docs_consistency.py` / `check_overview_docs_consistency.py`, none of which cover `90_shared_*.md`) — manually verify internal Markdown links after editing.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/90_shared_*.md` chapters (tracked in separate issues).
- Any code under `scripts/shared/` or `scripts/db/`.

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_00_document-guide」 including its 注意 note that this chapter must remain a reading guide, not a design-doc replacement. Do not edit code. If a design rationale is not recoverable from the current text, mark it `Needs Confirmation` per `memo-doc-shared-review.md` §「情報不足時の扱い」 instead of guessing.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_00_document-guide」
- Generated at: 2026-08-05
