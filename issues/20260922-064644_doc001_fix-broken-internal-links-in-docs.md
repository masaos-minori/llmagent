# Fix broken internal links across docs/

## Priority
High

## Summary
Repair all broken internal Markdown links in docs/ to ensure navigational integrity and prevent dead references for developers and AI agents consuming these documents.

## Background
The `docs/` directory contains 188 Markdown files with extensive cross-references between ADRs, design docs, and operational guides. The `tools/check_docs_structure.py` script detects broken internal links but has not been systematically addressed. Broken links degrade developer experience and cause AI agents to misinterpret document relationships.

## Problem
Multiple ADR and design documents contain internal links pointing to non-existent files. These broken links indicate either:
- Documents were renamed/moved without updating references
- Documents were deleted without removing dependent references
- Links were never valid (typos in filenames)

Specifically, `ADR-005`, `ADR-007`, `ADR-008`, `ADR-009`, and `ADR-010` each contain 8+ broken links to RAG-related documents that appear to have been renamed or removed.

## Reason for Change
Broken links waste developer time, confuse AI agents parsing document relationships, and reduce confidence in the documentation set. Each broken link represents a potential navigation dead-end.

## Implementation Intent
For each broken link:
1. Determine if the referenced document still exists under a different name (check git history)
2. If found, update the link to point to the current filename
3. If not found, remove the link and note the missing document
4. Preserve link text where possible to maintain readability

Focus effort on ADR documents first, as they form the architectural backbone of the project.

## Target Files or Areas
- `docs/adr/ADR-005-rag-source-derived-index-relationships.md` (10 broken links)
- `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` (11 broken links)
- `docs/adr/ADR-008-sqlite-4db-separation.md` (9 broken links)
- `docs/adr/ADR-009-rag-ft5-text-separation.md` (11 broken links)
- `docs/adr/ADR-010-rag-fallback.md` (8 broken links)
- `docs/adr/ADR-001-workflow-engine-mandatory.md` (3 broken links)
- `docs/adr/ADR-002-config-isolation.md` (3 broken links)
- `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` (6 broken links)
- `docs/adr/ADR-004-environment-failure-handling-policy.md` (4 broken links)
- `docs/adr/ADR-013-eventbus-authentication-authorization.md` (2 broken links)
- `docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md` (1 broken link)
- `docs/adr/ADR-015-reference-document-class-disposition.md` (1 broken link)
- `docs/04_mcp_02_03_audit-logging-and-errors.md` (1 broken link)
- `docs/04_mcp_05_01_access-control-and-allowlists.md` (1 broken link)
- `docs/06_eventbus_01_system-overview.md` (1 broken link)
- `docs/06_eventbus_03_persistence_schema_and_replay.md` (1 broken link)
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` (1 broken link)

## Required Changes
- For each broken link, search git history for the original filename
- Update the link to point to the current filename if found
- Remove the link entirely if the document was intentionally deleted
- Add a comment noting the removal reason if applicable
- Run `tools/check_docs_structure.py` after changes to confirm zero broken links remain

## Constraints
- Do not create new documents to satisfy old links — only fix existing references
- Preserve link text (anchor text) where possible to maintain readability
- Do not modify external links (HTTP URLs)
- Do not change link semantics (e.g., don't convert relative links to absolute)

## Acceptance Criteria
- `tools/check_docs_structure.py "docs/**/*.md"` reports zero broken internal links
- All remaining internal links resolve correctly
- No external links (HTTP URLs) were modified
- Link anchor text is preserved where possible

## Testing Expectations
- Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero broken link errors
- Manually verify a sample of repaired links resolve correctly
- Git diff review to confirm no unintended changes to link text

## Documentation Impact
This issue directly improves documentation quality. No additional documentation needs to be created.

## Out of Scope
- Creating new documents to replace deleted ones
- Renaming documents to match old link targets
- Fixing broken links in code comments or other non-docs/ locations
- External HTTP link repair
- Link formatting improvements (only broken links)

## Dependencies
- None

## Unresolved Questions
- Some documents may have been intentionally deleted; confirm deletion intent before removing links
- A few links reference files in `databases/` subdirectory — verify those exist
- Some links use fragment identifiers (#section-name); verify section names still exist

## AI Implementation Instruction
1. Run `uv run python tools/check_docs_structure.py "docs/**/*.md" 2>&1 | grep "broken link"` to get full list
2. For each broken link, check if the target file exists under a similar name using `git log --all --diff-filter=D -- "**/<filename>"`
3. If found, update the link in the source document
4. If not found, remove the link and add a TODO comment noting the missing document
5. After all repairs, re-run `uv run python tools/check_docs_structure.py "docs/**/*.md"` to confirm zero broken links
6. Do NOT modify any files outside docs/

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260922-064644
- **Related target files**: docs/adr/ADR-005-rag-source-derived-index-relationships.md, docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md, docs/adr/ADR-008-sqlite-4db-separation.md, docs/adr/ADR-009-rag-ft5-text-separation.md, docs/adr/ADR-010-rag-fallback.md
