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

## Design decisions
- The migration narrative (renaming rationale) is replaced by a one-line historical note carrying
  `was:` on the same line (10-line window rule), preserving reader context without asserting an
  active migration policy.

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
| Step | Status | Notes |
|---|---|---|
| 1 Lines 27-33 rewrite | Pending | |
| 2 Sweep | Pending | |
| 3 Checker confirmation | Pending | |

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
