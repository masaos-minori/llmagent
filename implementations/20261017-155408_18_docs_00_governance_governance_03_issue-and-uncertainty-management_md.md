# Implementation Procedure — `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

## Goal

Remove the MCP-006 entry from Part 1 Active Items once every category is resolved
(`REQ-007`).

## Scope

Modify only `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.
Remove the MCP-006 Known Issue entry (lines 94–112) from Part 1 Active Items, applying the
Known Issue Registration Rule in `governance_01_documentation-policy.md` (record
resolution/closure per that rule rather than silently deleting).

## Assumptions

- MCP-006 entry exists at lines 94–112.
- This removal is the last step (Phase 6) and must only occur after every category is
  resolved implemented-or-not-applicable (plan Risk / UNK-01).

## Design decisions

- Remove the active-item entry and, per the documentation policy, record the closure
  (resolution summary + date) in the location that policy prescribes — do not leave a
  dangling reference in `security_02` (row 17) without a corresponding closure record.

## Alternatives considered

- Appending to a single shared test module across servers: rejected — each
  server owns its existing test file and fixtures; keeping tests co-located
  preserves coverage locality and reuse.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Confirm all six categories are resolved implemented-or-not-applicable (rows 1–6 + their
   docs).
2. Read the Known Issue Registration Rule in `governance_01_documentation-policy.md`
   (Reference File) to learn how closure must be recorded.
3. Remove the MCP-006 entry from Part 1 Active Items and add the closure record as the
   rule requires.

### Method

- Delete the MCP-006 block (94–112); add closure per `governance_01`.

### Details

- Ensure no other active item or index cross-references MCP-006 as still-open.

## Compatibility considerations

This ledger is referenced by `security_02` (row 17) and possibly an index; keep references
consistent (MCP-006 no longer open).

## Security considerations

N/A.

## Rollback considerations

Revert the commit to the doc.

## Validation plan

- Documentation-consistency check (`governance_04_documentation-checks.md`, GV-022 family)
  passes; confirm MCP-006 is absent from active items.

## Completion criteria

The MCP-006 entry is removed from Part 1 Active Items and closure recorded per policy.

## Out of scope

Other docs, code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove MCP-006 entry from governance_03 active items | Pending | — | — | gated on all categories resolved |
| 2 | Add or update tests per Validation plan | N/A (docs-only) | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs consistency check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | — | — | this doc |

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
- **Requirement ID**: `REQ-007` (remove MCP-006 entry once resolved)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
