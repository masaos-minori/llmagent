# Fix Front Matter inconsistencies across docs/

## Priority
Medium

## Summary
Repair all Front Matter violations in docs/ to ensure consistent metadata structure, valid field references, and proper YAML parsing across all Markdown documents.

## Background
The `docs/` directory uses YAML Front Matter with required fields (`area`, `status`, `related`, `source`). The canonical schema is defined in `schemas/doc_front_matter.json`. Multiple documents violate these constraints: missing required fields, referencing non-existent related documents, and missing structural sections (`## Keywords`, `## Related Documents`).

## Problem
Front Matter inconsistencies cause three categories of problems:
1. **Missing required fields** — documents lack `area` or `related` fields, breaking schema validation
2. **Invalid cross-references** — `related` and `source` fields point to non-existent files
3. **Missing structural sections** — documents lack required `## Keywords` or `## Related Documents` sections that downstream tooling expects

Specifically:
- 6 documents have missing `area` field (including `active_databases.md` which has no Front Matter at all)
- 6 documents have missing `related` field
- 10+ ADR documents reference non-existent ADR numbers (e.g., `ADR-001` instead of `ADR-001-workflow-engine-mandatory.md`)
- 7 documents have incorrect H1 heading counts (0 or 2+ headings)

## Reason for Change
Inconsistent Front Matter breaks automated documentation tooling (schema validation, link checking, navigation generation). It also reduces developer confidence in the documentation set's reliability.

## Implementation Intent
For each category of violation:
1. **Missing required fields**: Add the missing field with a reasonable default value
   - Missing `area`: infer from document location/content
   - Missing `related`: add empty array `[]` if no specific references exist
2. **Invalid cross-references**: Update references to match actual filenames
   - Use `git log --all --diff-filter=D -- "**/<filename>"` to find renamed/deleted files
   - If found under new name, update the reference
   - If intentionally deleted, remove the reference
3. **Missing structural sections**: Add the required section with placeholder content
4. **H1 heading count**: Consolidate or split headings to meet exactly-one requirement

## Target Files or Areas
### Missing area field (6):
- `docs/index.md`
- `docs/databases/ack-nack-endpoints.md`
- `docs/databases/dlq-endpoint.md`
- `docs/databases/health-endpoint.md`
- `docs/databases/replay-endpoint.md`
- `docs/databases/active_databases.md`

### Missing related field (6):
- Same as above + `docs/adr-index.md`

### Invalid related/source references (10+):
- `docs/adr/ADR-002-config-isolation.md` → references `ADR-001`
- `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` → references `ADR-001`, `ADR-002`
- `docs/adr/ADR-004-environment-failure-handling-policy.md` → references `ADR-001`, `ADR-002`, `ADR-003`, `ADR-010`
- `docs/adr/ADR-005-rag-source-derived-index-relationships.md` → references `ADR-002`
- `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` → references `ADR-002`
- `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` → references `ADR-002`
- `docs/adr/ADR-008-sqlite-4db-separation.md` → references `ADR-002`
- `docs/adr/ADR-009-rag-ft5-text-separation.md` → references `ADR-002`
- `docs/adr/ADR-010-rag-fallback.md` → references `ADR-002`
- `docs/adr/ADR-013-eventbus-authentication-authorization.md` → references `ADR-002`, `ADR-006`
- `docs/adr/ADR-015-reference-document-class-disposition.md` → references `00_governance_01_documentation-policy.md`
- `docs/04_mcp_02_03_audit-logging-and-errors.md` → long related text
- `docs/04_mcp_05_01_access-control-and-allowlists.md` → long related text
- `docs/00_security_01_architecture-and-trust-boundaries.md` → references `agent/startup.py`, `shared/mcp_health.py`
- `docs/04_mcp_01_tool_ownership_matrix.md` → references `scripts/shared/tool_constants.py`
- `docs/04_mcp_02_service_boundaries.md` → references `scripts/shared/tool_constants.py`
- `docs/06_eventbus_01_system-overview.md` → references `index.md`
- `docs/06_eventbus_03_persistence_schema_and_replay.md` → references `index.md`
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` → references `index.md`

### H1 heading count violations (7):
- `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` (2 H1)
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md` (3 H1)
- `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md` (2 H1)
- `docs/agent_02_runtime-architecture.md` (2 H1)
- `docs/agent_12_01_memory-overview-and-modes.md` (2 H1)
- `docs/agent_12_02_memory-gate-data-model-search.md` (2 H1)
- `docs/agent_13_reference-api.md` (2 H1)
- `docs/04_mcp_05_01_access-control-and-allowlists.md` (0 H1)
- `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` (0 H1)
- `docs/databases/active_databases.md` (0 H1)

## Required Changes
- Add missing `area` field to 6 documents (infer from context)
- Add missing `related` field to 6 documents (use `[]` if no specific references)
- Update invalid `related` references to use correct filenames (check git history)
- Remove references to intentionally deleted documents
- Add missing `## Keywords` section where required
- Add missing `## Related Documents` section where required
- Fix H1 heading counts to exactly one per document
- Ensure `active_databases.md` has proper Front Matter and H1 heading

## Constraints
- Do not change the semantic meaning of existing Front Matter values
- Preserve document content — only modify metadata and structural sections
- When inferring `area`, use the document's directory path as primary signal
- For broken `related` references, prefer removing over guessing
- Do not modify any files outside docs/

## Acceptance Criteria
- `tools/check_docs_structure.py "docs/**/*.md"` reports zero Front Matter errors
- All remaining `related` and `source` references resolve to existing files
- Every document has exactly one H1 heading
- Every document has required `## Keywords` and `## Related Documents` sections
- Schema validation against `schemas/doc_front_matter.json` passes for all documents

## Testing Expectations
- Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors
- Run `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json` — expect schema validation pass
- Manual spot-check of repaired references

## Documentation Impact
This issue directly improves documentation quality. No additional documentation needs to be created.

## Out of Scope
- Renaming documents to match old reference names
- Adding new Front Matter fields beyond what the schema requires
- Restructuring document content (only metadata and structural sections)
- Fixing broken internal links (covered by separate issue DOC-001)
- External HTTP link repair

## Dependencies
- None (can be done independently of DOC-001)

## Unresolved Questions
- Some `related` references may need human judgment to determine intent (e.g., long descriptive text vs. filename)
- `active_databases.md` appears to be an orphaned file — confirm whether it should exist
- Some documents may legitimately have multiple H1 headings; verify before consolidating

## AI Implementation Instruction
1. Run `uv run python tools/check_docs_structure.py "docs/**/*.md" 2>&1 | grep -E "(missing|broken)"` to get full list
2. For missing `area` fields: infer from directory path (e.g., `docs/adr/` → `adr`, `docs/05_agent_*` → `agent`)
3. For missing `related` fields: add `related: []` unless document clearly references other docs
4. For invalid references: check git history with `git log --all --diff-filter=D -- "**/<filename>"`; update if found, remove if deleted
5. For missing sections: add `## Keywords\n<placeholder>` and `## Related Documents\n<placeholder>`
6. For H1 count issues: consolidate subheadings into subsections, or demote extra H1 to H2
7. After changes, re-run `uv run python tools/check_docs_structure.py "docs/**/*.md"` to confirm zero errors
8. Do NOT modify any files outside docs/

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260922-064743
- **Related target files**: docs/index.md, docs/databases/ack-nack-endpoints.md, docs/databases/dlq-endpoint.md, docs/databases/health-endpoint.md, docs/databases/replay-endpoint.md, docs/databases/active_databases.md, docs/adr/ADR-002-config-isolation.md, docs/adr/ADR-003-runtime-tool-registry-routing-authority.md, docs/adr/ADR-004-environment-failure-handling-policy.md, docs/adr/ADR-005-rag-source-derived-index-relationships.md, docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md, docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md, docs/adr/ADR-008-sqlite-4db-separation.md, docs/adr/ADR-009-rag-ft5-text-separation.md, docs/adr/ADR-010-rag-fallback.md, docs/adr/ADR-013-eventbus-authentication-authorization.md, docs/adr/ADR-015-reference-document-class-disposition.md, docs/04_mcp_02_03_audit-logging-and-errors.md, docs/04_mcp_05_01_access-control-and-allowlists.md, docs/00_security_01_architecture-and-trust-boundaries.md, docs/04_mcp_01_tool_ownership_matrix.md, docs/04_mcp_02_service_boundaries.md, docs/06_eventbus_01_system-overview.md, docs/06_eventbus_03_persistence_schema_and_replay.md, docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md
