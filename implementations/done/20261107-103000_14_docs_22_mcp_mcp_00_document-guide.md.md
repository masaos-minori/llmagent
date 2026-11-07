# Implementation Procedure: docs/22_mcp/mcp_00_document-guide.md

## Goal
Remove the migration-framing row (line 94) and the content that was covered by the deleted
`mcp-00-document-guide` manifest exception, so the guide describes only the current document set.

## Scope
- Target file: `docs/22_mcp/mcp_00_document-guide.md` (MODIFY).
- Release unit: `policy-finalization`.
- Related requirement / acceptance criteria: REQ-003, REQ-005 / AC-001, AC-004 (frozen target
  row 14).

## Assumptions
- Anchors verified: doc line 94 carries the migration-framing row; the manifest exception
  (`migration-*` id covering this document, manifest line 24 area) is deleted by doc 02, so the
  checker will flag this document unless its content is corrected in the same release unit.
- The document-guide structure (row table of mcp docs) stays; only the migration-era row/wording
  changes.

## Verification findings (adversarial re-verification 2026-11-07, HEAD `be4d74463`)

- The only finding was line 94's guide-table row naming `_MCP_TOOLS` (a COMPAT-pattern literal;
  no historical-context exemption applies to it in docs, so the exempting manifest entry deleted
  by sibling document 02 made it blocking). Row rewritten to "Naming convention for tool schema
  modules and `TOOL_LIST` exports, verified by the schema-export guard test"; the retired literal
  now appears in zero docs files (grep-verified after the edit), only in the guard test file
  (covered by its `fixture` manifest entry).

## Design decisions
- Replace the migration-framing row's description with the current doc-set description; do not
  delete the row if it maps to a live document — delete only the migration framing text.
- If the row maps solely to retired material, delete the row.

## Alternatives considered
- Keeping a new fixture exception for this doc: rejected — the plan's purpose is zero production
  (non-`fixture`) exceptions; fixture entries are for test data only.

## Implementation

### Target file
- `docs/22_mcp/mcp_00_document-guide.md` (MODIFY).

### Procedure
1. Line 94: rewrite the row description to current-policy wording (no migration framing).
2. Sweep the file for the five doc-claim phrases; remove or mark historical.
3. Confirm no other line in the file was relying on the deleted manifest exception (compare the
   exception's recorded reason/path from doc 02's deletion list).

### Method
- Text edits; checker doc-claim pass.

### Details
- Backticked doc-name references must still resolve (`--check-doc-symbols`): do not rename rows to
  names that don't exist as files.

## Compatibility considerations
- docs consistency CI; sequenced with manifest entry deletion (doc 02).

## Security considerations
- None.

## Rollback considerations
- Single-file revert (must revert with the manifest deletion to keep checker green).

## Validation plan
- Checker blocking run exit 0; docs consistency CI.

## Completion criteria
- Zero migration framing in the guide; file clean without its former manifest exception.

## Out of Scope
- Other mcp docs (doc 15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Line 94 rewrite | Completed | 20261107-184026 | 20261107-184026 |  |
| 2 | Sweep | Completed | 20261107-184026 | 20261107-184026 |  |
| 3 | Exception-reliance check | Completed | 20261107-184026 | 20261107-184026 |  |
### Blocker Log
- None.

### Work Items Created
- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-005 / AC-001, AC-004
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `docs/22_mcp/mcp_00_document-guide.md`