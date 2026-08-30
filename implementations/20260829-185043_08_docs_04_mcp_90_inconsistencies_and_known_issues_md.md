# Implementation Procedure: NC-020 Row 8 — Update MCP-005 status in MCP Known Issues document

## Goal

Update the MCP-005 entry in `docs/04_mcp_90_inconsistencies_and_known_issues.md` to reflect resolution of the audit target issue.

## Scope

Only `docs/04_mcp_90_inconsistencies_and_known_issues.md`: update MCP-005 entry fields. No other files are modified by this procedure document.

## Assumptions

- Row 1 fixes `"repo"` to `"repo_path"` key in audit call.
- Row 2 changes `_check_repo_path()` return type to `(bool, str, str)` with resolved path.
- All code changes validated before documentation update.

## Design decisions

- **Move MCP-005 from open → fixed**: The root cause (key mismatch) is addressed by Row 1.
- **Update Resolution Notes**: Document what was done to resolve the issue.
- **Keep Severity as Low**: The issue was low severity because it affects audit records, not operational correctness.

## Alternatives considered

1. **Remove MCP-005 entirely**: Would lose historical context; better to mark as fixed.
2. **Move to deprecated**: Would imply obsolete feature; the issue was real but resolved.
3. **Add new MCP-006 for residual concerns**: Unnecessary — the original question is answered.

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure

1. Locate MCP-005 entry (lines ~114-133).
2. Update Status from `open` to `fixed`.
3. Update Resolution Notes to reflect what was done.
4. Update Observed Implementation to reflect verification.

### Method

Direct modification of the MCP-005 entry block.

### Details

```markdown
### MCP-005: Git MCP audit log `target` field likely always empty

- **ID**: MCP-005
- **Title**: Git MCP audit call reads a nonexistent `"repo"` argument key instead of `"repo_path"`
- **Status**: fixed
- **Severity**: Low
- **Area**: MCP
- **Type**: ambiguous-behavior
- **Source**: `scripts/mcp_servers/git/git_server.py::call_tool`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `04_mcp_04_05_git.md` Audit
- **Related**: MCP-003
- **Summary**: The audit call site passes `req.args.get("repo", "")` as the audit `target`, but Git MCP's input schema uses the key `repo_path`, not `repo`.
- **Current Description**: Read from code, this means the audit `target` field for every git-mcp call is likely always the empty-string default.
- **Observed Implementation**: Confirmed by code inspection — `req.args.get("repo", "")` uses wrong key; fixed by Row 1 changing to `repo_path` key and consuming resolved canonical path from Row 2
- **Impact**: If confirmed, Git MCP audit entries carry no repository identity, weakening the audit trail for a High-Severity write surface (see MCP-003).
- **Recommended Action**: Confirm by inspecting an actual audit log line for a git-mcp call; if `target` is empty, fix the key to `repo_path`.
- **Resolution Notes**: Root cause was key mismatch (`"repo"` vs `"repo_path"`). Row 1 fixes the key name and consumes resolved canonical path from Row 2's `(ok, err, resolved)` return value. Audit records will now contain canonical repository identity.
```

Note: The Status change from `open` to `fixed` and the updated Resolution Notes are the primary changes. The Observed Implementation field should also be updated to reflect that the issue was verified by code inspection.

## Compatibility considerations

- **Historical record preserved**: Moving to `fixed` instead of removing preserves traceability.
- **Cross-references intact**: MCP-005 still appears in the inventory for audit purposes.

## Security considerations

- **No credential exposure**: Documentation update only.
- **Audit trail improvement**: Resolved issue improves security posture.

## Rollback considerations

- Revert Status to `open` if code changes are reverted.
- Remove Resolution Notes if rollback occurs.
- No data loss possible since only documentation is changed.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| MCP-005 status updated | Verify Status field = `fixed` | Manual inspection | Status shows `fixed` |
| Resolution Notes updated | Verify Resolution Notes present | Manual inspection | Resolution Notes mentions key mismatch fix |
| Cross-references intact | Verify Related field present | Manual inspection | Related = MCP-003 |

## Completion criteria

- [ ] MCP-005 Status moved from `open` to `fixed`
- [ ] Resolution Notes added documenting what was done
- [ ] Observed Implementation updated to reflect verification
- [ ] Severity remains Low (no behavioral change)

## Out of scope

- Updating MCP-003 status (separate concern)
- Adding new MCP entries beyond MCP-005
- Modifying other MCP documents

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate MCP-005 entry | Pending | - | - | |
| 2 | Update Status field to `fixed` | Pending | - | - | |
| 3 | Update Resolution Notes | Pending | - | - | |
| 4 | Update Observed Implementation | Pending | - | - | |
| 5 | Run validation sequence | Pending | - | - | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| - | - | - | - |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| - | - | - | - | - | - |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260828-160910_nc020_git_mcp_audit_target_resolution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-115719_nc020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-185043
- **Related target files**: docs/04_mcp_90_inconsistencies_and_known_issues.md
