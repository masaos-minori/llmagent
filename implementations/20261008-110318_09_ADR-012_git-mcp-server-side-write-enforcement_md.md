# Implementation Procedure: Update ADR-012 Known Deviations

## Goal

Close MCP-001 in Known Deviations section of `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md` once fixed (REQ-010). Document resolved audit emission.

## Scope

- Modify `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`:
  - Line 184 (Known Deviations): update MCP-001 status from open to fixed.

## Assumptions

- MCP-001 is tracked in the Known Deviations section of ADR-012.
- The fix addresses the audit record emission gap (every write-tool call now produces one audit record).

## Design decisions

- **Status update**: Change MCP-001 status from "open" to "fixed" in the Known Deviations section.
- **Resolution note**: Add a brief note referencing the implementation procedure that resolved the issue.

## Alternatives considered

- Removing the MCP-001 entry entirely: rejected because it should remain documented as a resolved deviation for historical traceability.
- Moving MCP-001 to a "Resolved" section: rejected because the plan only requires closing the entry in place.

## Implementation
### Target file
`docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure
1. Close MCP-001 in Known Deviations section (REQ-010).

### Method
Edit `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`:
- Line 184 (Known Deviations): Update MCP-001 status from "open" to "fixed".
- Add resolution note referencing the implementation procedure.

### Details
- MCP-001 is tracked in the Known Deviations section of ADR-012.
- The fix addresses the audit record emission gap (every write-tool call now produces one audit record).
- The entry should remain documented as a resolved deviation for historical traceability.

## Compatibility considerations

- This is a documentation-only change; no code or configuration impact.

## Security considerations

- No security impact: this is a documentation update.

## Rollback considerations

- Revert the status change — acceptable because it's a simple text edit.

## Validation plan

- **Manual review**: Confirm the MCP-001 entry is updated with the correct resolution reference.
- **Documentation consistency**: `uv run python tools/check_docs_consistency.py --domain mcp` — confirm clean.

## Completion criteria

- MCP-001 status in Known Deviations is updated to "fixed".
- A resolution note references the implementation procedure.
- No other changes to ADR-012 beyond the MCP-001 entry.

## Out of scope

- Modifying other sections of ADR-012.
- Modifying `mcp_04_05_git.md` (covered in its own document).
- Modifying `mcp_06_05_reading-audit-logs.md` (covered in its own document).
- Modifying `governance_03_issue-and-uncertainty-management.md` (covered in its own document).

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Close MCP-001 in Known Deviations (`docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`) | Pending | — | — | REQ-010 |
| 2 | Run documentation consistency check | Pending | — | — | REQ-010 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-010
- **Source issue**: issues/20261007-153904_gitaudit01_fix-git-mcp-audit-records-and-policy-rejection-error-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261007-191952_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-110318
- **Related target files**: docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md
