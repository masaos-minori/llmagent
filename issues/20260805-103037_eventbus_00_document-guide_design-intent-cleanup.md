# Reduce implementation-derived detail in docs/06_eventbus_00_document-guide.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_00_document-guide.md`: keep it as the doc-set entry point (navigation, Canonical Source Rule, Known Issues/Deferred handling); remove overly detailed file indexes and mechanical per-file summaries.

## Reason for Change
`docs/06_eventbus_*.md` currently mixes design/operational judgment with content mechanically derivable from code (HTTP parameter tables, response field lists, DDL, function signatures). `memo-doc-eventbus-review.md` was written to identify what each chapter should keep vs. remove; this issue covers the entry-point chapter.

## Implementation Intent
Restructure this chapter to serve purely as navigation: doc-set purpose, which chapter answers which question, the Canonical Source Rule, and how Known Issues / Deferred Items are handled. Reference API should be explicitly noted as separate from the design-doc body.

## Target Files or Areas
`docs/06_eventbus_00_document-guide.md`

## Required Changes
- Keep: the doc set's role as an entry point, high-level guidance on which chapter to read for which question, the Canonical Source Rule, how Known Issues / Deferred Items are handled, the note that Reference API is for detail lookup and kept separate from the design body.
- Remove or compress: overly detailed file indexes, an overly fine-grained AI query-routing table, keyword enumeration, mechanical per-file content descriptions.

## Acceptance Criteria
- The chapter follows the template in `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 where applicable to a navigation-guide chapter.
- No mechanical file index or per-file description remains that duplicates what a directory listing already shows.
- Any judgment not reconstructable from the current text is recorded as `Needs Confirmation` rather than invented.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated `check_eventbus_docs_consistency.py` currently exists (only `check_agent_docs_consistency.py` / `check_mcp_docs_consistency.py` / `check_rag_docs_consistency.py` / `check_deployment_docs_consistency.py` / `check_overview_docs_consistency.py` do) — manually verify internal Markdown links and cross-references remain valid after editing.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters (tracked in separate issues).
- Any code under `scripts/eventbus/` — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_00_document-guide」 exactly for what to keep/remove. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). If a design rationale is not recoverable from the current text, mark it `Needs Confirmation` per `memo-doc-eventbus-review.md` §「情報不足時の扱い」 instead of guessing.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_00_document-guide」
- Generated at: 2026-08-05
