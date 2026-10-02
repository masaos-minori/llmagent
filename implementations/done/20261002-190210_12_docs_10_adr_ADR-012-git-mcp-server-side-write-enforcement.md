# Implementation Procedure: Fix stale governance paths in docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md

## Goal

Replace stale `docs/governance_0N_*` path references in `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md` with actual existing paths under `docs/00_governance/governance_0N_*`.

## Scope

- Modify only `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`.
- In-Scope: Replace stale paths on lines 212, 231, and 272.
- Out-of-Scope: Changing any other content in the file.

## Assumptions

- The correct paths are `docs/00_governance/governance_01_documentation-policy.md` and `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (confirmed by filesystem inspection).

## Design decisions

- **Approach**: Direct string replacement — replace `docs/governance_01_documentation-policy.md` with `docs/00_governance/governance_01_documentation-policy.md` on lines 231 and 272, and `docs/governance_03_issue-and-uncertainty-management.md` with `docs/00_governance/governance_03_issue-and-uncertainty-management.md` on line 212.

## Alternatives considered

None — direct replacement is the only sensible approach for stale paths.

## Implementation

### Target file

`docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure

Replace the stale path strings on lines 212, 231, and 272 with the correct paths.

### Method

Edit `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`:

**Line 212:** Change `docs/governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

**Line 231:** Change `docs/governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`

**Line 272:** Change `docs/governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`

### Details

Line 212 currently reads:
```
`docs/governance_03_issue-and-uncertainty-management.md`'s MCP-001 (`verify_postcondition()` unconditional-success placeholder) and MCP-002 (`PipelineResult` missing `post_state`) are both registered and marked `resolved` (confirmed this cycle). Whether any further deviation remains open after Phase 1's dead-method removal lands is tracked in row 4 of that document.
```

Change to:
```
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s MCP-001 (`verify_postcondition()` unconditional-success placeholder) and MCP-002 (`PipelineResult` missing `post_state`) are both registered and marked `resolved` (confirmed this cycle). Whether any further deviation remains open after Phase 1's dead-method removal lands is tracked in row 4 of that document.
```

Line 231 currently reads:
```
- **Approval Reference**: `docs/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
```

Change to:
```
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
```

Line 272 currently reads:
```
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
```

Change to:
```
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
```

Only the path strings change; surrounding text is preserved.

## Compatibility considerations

- The corrected paths resolve to existing files (`docs/00_governance/governance_01_documentation-policy.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`).

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path strings if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md` | Path resolution | `grep -rnE "docs/governance_0[0-4]_" docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md` | No matches |
| `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md` | File existence | `test -f docs/00_governance/governance_01_documentation-policy.md && test -f docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Files exist |

## Completion criteria

- All `docs/governance_0N_*` paths on lines 212, 231, and 272 of `ADR-012-git-mcp-server-side-write-enforcement.md` resolve to existing files.
- No remaining `docs/governance_0N_*` patterns in `ADR-012-git-mcp-server-side-write-enforcement.md`.

## Out of scope

- Other stale paths in `ADR-012-git-mcp-server-side-write-enforcement.md` (if any).
- Changes to other files.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-003 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test needed for path string fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | REQ-003 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No documentation update needed |

### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
