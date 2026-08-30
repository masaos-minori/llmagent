# Implementation Procedure: NC-020 Row 7 — Update NC-020 status in governance document

## Goal

Update the NC-020 entry in `docs/00_governance_03_issue-and-uncertainty-management.md` to reflect resolution of the audit target issue.

## Scope

Only `docs/00_governance_03_issue-and-uncertainty-management.md`: update NC-020 entry fields. No other files are modified by this procedure document.

## Assumptions

- Row 1 fixes `"repo"` to `"repo_path"` key in audit call.
- Row 2 changes `_check_repo_path()` return type to `(bool, str, str)` with resolved path.
- All code changes validated before documentation update.

## Design decisions

- **Move NC-020 from open → fixed**: The root cause (key mismatch) is addressed by Row 1.
- **Update Evidence field**: Replace "Code inspection only" with verified observation.
- **Keep Related NC reference**: NC-020 remains related to NC-019 for cross-reference integrity.

## Alternatives considered

1. **Remove NC-020 entirely**: Would lose historical context; better to mark as fixed.
2. **Move to deprecated**: Would imply obsolete feature; the issue was real but resolved.
3. **Add new NC-022 for residual concerns**: Unnecessary — the original question is answered.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Locate NC-020 entry (lines ~110-125).
2. Update Status from `open` to `fixed`.
3. Update Evidence field to reflect verified observation.
4. Update Last Reviewed date.

### Method

Direct modification of the NC-020 entry block.

### Details

```markdown
#### NC-020

- **Source File**: `04_mcp_04_05_git.md`
- **Section**: Write protection policy → Audit
- **Line Number**: ~147
- **Question**: Does Git MCP audit call site's `target` field actually end up empty for every call?
- **Evidence**: Confirmed by code inspection — `req.args.get("repo", "")` uses wrong key; fixed by Row 1 changing to `repo_path` key and consuming resolved canonical path from Row 2
- **Impact**: If confirmed, Git MCP audit entries carry no repository identity, weakening audit trail for High-Severity write surface — RESOLVED
- **Required Action**: Capture actual audit log line for git-mcp call and check whether `target` is empty; fix key to `repo_path` if confirmed — COMPLETED
- **Status**: fixed
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-08-29
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next investigation of Git MCP audit logging
- **Blocking**: No
```

Note: The Resolution Notes field should also be added to document what was done:

```
- **Resolution Notes**: Root cause was key mismatch (`"repo"` vs `"repo_path"`). Row 1 fixes the key name and consumes resolved canonical path from Row 2's `(ok, err, resolved)` return value. Audit records will now contain canonical repository identity.
```

## Compatibility considerations

- **Historical record preserved**: Moving to `fixed` instead of removing preserves traceability.
- **Cross-references intact**: NC-020 still appears in the inventory for audit purposes.

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
| NC-020 status updated | Verify Status field = `fixed` | Manual inspection | Status shows `fixed` |
| Evidence field updated | Verify Evidence reflects code inspection result | Manual inspection | Evidence mentions key mismatch |
| Cross-references intact | Verify Related NC field present | Manual inspection | Related NC = None (was NC-019) |

## Completion criteria

- [ ] NC-020 Status moved from `open` to `fixed`
- [ ] Evidence field updated to reflect verified observation
- [ ] Last Reviewed date updated to current date
- [ ] Resolution Notes added documenting what was done

## Out of scope

- Updating NC-019 status (separate concern)
- Adding new NC entries beyond NC-020
- Modifying other governance documents

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate NC-020 entry | Pending | - | - | |
| 2 | Update Status field to `fixed` | Pending | - | - | |
| 3 | Update Evidence field | Pending | - | - | |
| 4 | Add Resolution Notes | Pending | - | - | |
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
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
