## Goal

Update the mdq write row of the tool-ownership matrix, which is the canonical mapping that states
the mdq write tier and the approval consequence.

## Scope
**Release unit**: tier change and its pins

- The `index_paths, refresh_index` row (line 33): the Safety Tier cell and the Approval (effective
  risk) cell.

## Assumptions

- The matrix states the effective risk that the declared tier produces, so the Approval cell must
  change with the tier, not independently.

## Design decisions

- The Approval cell follows the wording already used for tier-mapped tools in the same table
  (`Yes, `y/N` (`medium` via tier mapping)`), so the row reads like the other tier-derived rows.

## Alternatives considered

- N/A: documentation-only change in one table row.

## Implementation
### Target file
`docs/22_mcp/mcp_01_tool_ownership_matrix.md`

### Procedure
1. Change the Safety Tier cell from `WRITE_SAFE` to `WRITE_DANGEROUS`.
2. Change the Approval cell from "No by default (`none` via tier mapping; no `approval_risk_rules`
   entry)" to `Yes, `y/N` (`medium` via tier mapping)`.

### Method

- The Capability Group, Owning MCP Server, and Typical Workflow Stage cells are unchanged.

### Details

- The row is prose in a table; `registry/manifests/tool_ownership.yaml` is the machine-readable
  source for the ownership facts, and this Plan does not change ownership, only the tier value.

## Compatibility considerations

- `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` and
  `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` state the same consequence and
  are aligned by rows 15 and 17, so the three docs must land in the same phase.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_consistency.py --domain mcp`

## Completion criteria

- The matrix row states the tier that maps to `medium` and the prompt consequence (AC-1).

## Out of Scope

- The approval_risk_rules wording in other rows of the same table, which describes removed maps:
  not part of this row's change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Docs checkers above |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This row is the documentation change |

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
- **Requirement ID**: REQ-008
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `docs/22_mcp/mcp_01_tool_ownership_matrix.md`
