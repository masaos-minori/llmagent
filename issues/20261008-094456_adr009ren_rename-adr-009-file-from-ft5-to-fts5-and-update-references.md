# Rename ADR-009 file from ft5 to fts5 and update references

## Priority
Low

## Summary
Rename the ADR-009 file to correct the typo "ft5" to "fts5" and update every document that references the old name.

## Background
Source: local investigation notes (memo2.md, ADR-009 section; review finding L01).

## Problem
The filename `ADR-009-rag-ft5-text-separation.md` misspells FTS5. A repository search (excluding `.claude/worktrees/` copies and archived work items) finds the old name in `docs/21_rag/rag_02_08_ingestion_pipeline-shared.md`, `docs/21_rag/rag_00_document-guide.md`, `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`, `docs/10_adr/adr-index.md`, `docs/10_adr/adr_00_document-guide.md`, and `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (RAG-002).

## Reason for Change
Wrong names hamper search and look like a defect; fixing them later gets costlier as references grow.

## Implementation Intent
- Rename with `git mv` and update references mechanically; no content change in the same commit.

## Target Files or Areas
- `docs/10_adr/ADR-009-rag-ft5-text-separation.md`
- the six referencing documents listed in Problem; re-run a repository-wide search for other references (config, tools, skills, plans, issues)

## Required Changes
- Rename to `ADR-009-rag-fts5-text-separation.md`.
- Update all references, including front matter `related:` entries and links.

## Constraints
- Do not rewrite references inside archived history (`issues/done/`, `plans/done/`, `implementations/done/`) unless a checker requires it.

## Acceptance Criteria
- No reference to `ft5` remains outside archived work items.
- `check_docs_structure.py` link reachability passes.

## Testing Expectations
Run the doc checkers listed in `routing.md` (structure and link reachability, consistency for the rag domain).

## Documentation Impact
Documentation only: filename and links.

## Out of Scope
- Content changes to ADR-009 (see the adr009fix issue).

## Dependencies
- None blocking; sequence with the adr009fix issue to avoid merge conflicts.

## Unresolved Questions
- N/A: none.

## AI Implementation Instruction
Use `git mv`; do not change ADR body text. Search the whole repository for the old name before and after.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094456
- **Related target files**: `docs/10_adr/ADR-009-rag-ft5-text-separation.md`, `docs/10_adr/adr-index.md`, `docs/10_adr/adr_00_document-guide.md`, `docs/21_rag/rag_00_document-guide.md`, `docs/21_rag/rag_02_08_ingestion_pipeline-shared.md`, `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
