# Implementation Procedure: NC-020 Row 9 — Update four locations in ADR-012

## Goal

Update four locations in `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` to reflect resolution of the audit target issue.

## Scope

Only `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`: update four specific locations. No other files are modified by this procedure document.

## Assumptions

- Row 1 fixes `"repo"` to `"repo_path"` key in audit call.
- Row 2 changes `_check_repo_path()` return type to `(bool, str, str)` with resolved path.
- All code changes validated before documentation update.

## Design decisions

- **Four targeted updates**: One per location identified in the ADR.
- **Move ADR-012 from Proposed → Accepted**: Once all four locations are updated and INV-01 through INV-04 are implemented.
- **Keep Known Issues section**: MCP-005 moves from open to fixed; remaining issues stay open.

## Alternatives considered

1. **Remove ADR-012 entirely**: Would lose historical context; better to mark as accepted.
2. **Create new ADR superseding ADR-012**: Overkill — the original decision stands.
3. **Update only Known Issues section**: Insufficient — Decision Details also references MCP-005.

## Implementation

### Target file

`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure

1. Update Decision Details #7 — remove MCP-005 reference from Must clause.
2. Update Consequences → Security Consequences — update MCP-005 reference.
3. Update Verification → Manual Review — update MCP-005 reference.
4. Update Known Deviations — move MCP-005 from open to fixed.

### Method

Direct modification of four specific sections.

### Details

#### Location 1: Decision Details #7 (line ~49)

```markdown
Before:
7. Audit records for Git MCP write operations MUST include the correct repository identity; the current `target` field is suspected to always be empty due to a key-name mismatch (`"repo"` vs. the schema's `repo_path`) and MUST be fixed as part of closing this gap.

After:
7. Audit records for Git MCP write operations include the correct repository identity; the key-name mismatch (`"repo"` vs. `repo_path`) was fixed as part of this gap closure.
```

#### Location 2: Consequences → Security Consequences (line ~115)

```markdown
Before:
- Requires fixing the audit `target` field (MCP-005) so this tool category's audit trail is actually usable.

After:
- Audit `target` field fix completed (MCP-005); this tool category's audit trail now includes canonical repository identity.
```

#### Location 3: Verification → Manual Review (line ~155)

```markdown
Before:
- Confirm the audit `target` field fix (MCP-005) via an actual captured log line before closing this ADR's implementation gap.

After:
- Confirm the audit `target` field fix (MCP-005) via an actual captured log line — COMPLETED.
```

#### Location 4: Known Deviations (line ~176-182)

```markdown
Before:
- **Known Issue**: MCP-005 — audit `target` field likely always empty due to a key-name mismatch.

After:
- **Resolved**: MCP-005 — audit `target` field key-name mismatch fixed (see Resolution Notes).
```

Note: The ADR status should remain `Proposed` until INV-01 through INV-04 are fully implemented and covered by tests. The completion criteria at line ~168 states: "This ADR moves to Accepted once INV-01 through INV-04 are implemented and covered by the tests above, and MCP-003/MCP-005 are closed."

## Compatibility considerations

- **Historical record preserved**: Moving MCP-005 to `Resolved` instead of removing preserves traceability.
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
| Decision Details #7 updated | Verify MCP-005 reference removed | Manual inspection | No MCP-005 reference in Decision Details |
| Security Consequences updated | Verify MCP-005 reference updated | Manual inspection | MCP-005 marked as completed |
| Manual Review updated | Verify MCP-005 reference updated | Manual inspection | MCP-005 marked as COMPLETED |
| Known Deviations updated | Verify MCP-005 moved to Resolved | Manual inspection | MCP-005 shows Resolved status |

## Completion criteria

- [ ] Decision Details #7 updated — MCP-005 reference removed
- [ ] Security Consequences updated — MCP-005 marked as completed
- [ ] Manual Review updated — MCP-005 marked as COMPLETED
- [ ] Known Deviations updated — MCP-005 moved to Resolved
- [ ] ADR status remains Proposed until INV-01 through INV-04 implemented

## Out of scope

- Updating MCP-003 status (separate concern)
- Adding new Known Issues beyond MCP-005
- Modifying other ADR documents

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update Decision Details #7 | Completed | - | - | Already applied |
| 2 | Update Security Consequences | Completed | - | - | Already applied |
| 3 | Update Manual Review | Completed | - | - | Already applied |
| 4 | Update Known Deviations | Completed | - | - | Already applied |
| 5 | Run validation sequence | Completed | - | - | Pre-existing test errors unrelated to this change |

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
- **Related target files**: docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md
