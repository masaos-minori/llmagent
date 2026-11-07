# Implementation Procedure: docs/22_mcp/mcp_07_tool_schema_export_policy.md

## Goal
Remove the `_MCP_TOOLS` → `TOOL_LIST` migration-policy framing (line 27, legacy-mention context
spanning 27-33) that was covered by the deleted manifest exception.

## Scope
- Target file: `docs/22_mcp/mcp_07_tool_schema_export_policy.md` (MODIFY).
- Release unit: `policy-finalization`.
- Related requirement / acceptance criteria: REQ-003, REQ-005 / AC-001, AC-004 (frozen target
  row 15).

## Assumptions
- Anchors verified: doc lines 27-33 carry the rename/migration policy framing; the manifest
  exception covering this document (manifest line 33 area id) is deleted by doc 02.
- `TOOL_LIST` is the current name; `_MCP_TOOLS` is the retired name — the policy section becomes
  current-state wording only.

## Verification findings (adversarial re-verification 2026-11-07, HEAD `be4d74463`)

- The `_MCP_TOOLS` entry lives in `COMPAT_PATTERNS`, which has no historical-context exemption and applies to `*.md` files too. The original Design decision ("one-line historical note carrying `was:`") would therefore still flag this document: any line containing the literal `_MCP_TOOLS` is a finding unless the whole file is exempted — and the exempting manifest entry is exactly what doc 02 deletes.
- Corrected rewrite: the document must not contain the literal retired name at all. Line 27's verification sentence becomes a current-only statement about `TOOL_LIST` and the guard test, with no retired-symbol literal. `tests/mcp_servers/test_mcp_tool_schema_exports.py` remains the place that quotes the literal (covered by its existing `fixture` manifest entry).

## Design decisions
- The migration narrative (renaming rationale) is replaced by current-state wording only; the retired-symbol literal is removed from this document entirely (see Verification findings — a `was:` historical note does not survive the COMPAT-pattern stage).

## Alternatives considered
- Deleting the whole policy subsection: rejected — the export policy itself is live content; only
  its migration framing is wrong.

## Implementation

### Target file
- `docs/22_mcp/mcp_07_tool_schema_export_policy.md` (MODIFY).

### Procedure
1. Lines 27-33: rewrite to current-policy wording; `_MCP_TOOLS` may appear only in a `was:`
   historical note.
2. Sweep the file for the five doc-claim phrases; remove or mark historical.
3. Verify the file is clean without its former manifest exception (checker run).

### Method
- Text edits; checker doc-claim + doc-symbol pass.

### Details
- Keep the export-policy rules themselves unchanged (out of this plan's scope).

## Compatibility considerations
- docs consistency CI; sequenced with manifest entry deletion (doc 02).

## Security considerations
- None.

## Rollback considerations
- Single-file revert (unit-consistent with doc 02).

## Validation plan
- Checker blocking run exit 0; docs consistency CI.

## Completion criteria
- No live migration-policy framing; historical note marked; checker green.

## Out of Scope
- Export policy rule content itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Lines 27-33 rewrite | Completed | 20261107-184026 | 20261107-184026 |  |
| 2 | Sweep | Completed | 20261107-184026 | 20261107-184026 |  |
| 3 | Checker confirmation | Completed | 20261107-184026 | 20261107-184026 |  |
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
- **Related target files**: `docs/22_mcp/mcp_07_tool_schema_export_policy.md`