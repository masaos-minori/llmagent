## Goal

Implement **REQ-003**: remove the now-resolved AGENT-001 from the Known Issues ledger in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, consistent with Part 1's convention that resolved items are removed (not kept).

## Scope

Modify `docs/00_governance/governance_03_issue-and-uncertainty-management.md` only. Reference read only: the AGENT-001 entry itself.

## Assumptions

- Part 1 removes resolved entries rather than marking them closed (stated in the doc near line 50).
- AGENT-001 is now resolved by seq 01/02 (default.json set to `true` + loader enforcement).

## Design decisions

- Remove both the table row and the detail subsection so no dangling reference to an open AGENT-001 remains.

## Alternatives considered

- Marking AGENT-001 status as `resolved` in place: rejected — Part 1's convention is removal, and the adr-index/ledger consistency checks expect resolved items gone.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
Remove the AGENT-001 entries from the ledger.

### Method
1. **Active Items table.** Remove the row whose ID is `AGENT-001`:
   ```
   | AGENT-001 | Default workflow definition does not satisfy the documented require_approval policy | open | Medium | Agent | design-gap |
   ```
2. **Detail subsection.** Remove the `#### AGENT-001` section (starts at `- **ID**: AGENT-001` and runs through its final `- **Recommended Action**`/`- **Resolution Target` lines, immediately before the next `#### ` heading, i.e. `#### AGENT-002` or the next group header).

### Details
- Re-read the file before editing to confirm the exact boundaries of the `#### AGENT-001` subsection (line numbers shift after the table-row removal).
- Confirm no other section (e.g. adr-index, Known Deviations) still cites AGENT-001 as open; if it does, that is a separate finding to report, not to fix here.

## Compatibility considerations

- Doc-only. Ensure no internal link pointed at the removed subsection as live.

## Security considerations

- Leaving a resolved design-gap in the ledger would mislead the quarterly review into treating AGENT-001 as still open.

## Rollback considerations

- Restore the two removed regions from git.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `governance_03` | Doc review | manual / `check_docs_*` | AGENT-001 absent from table and detail |

## Completion criteria

- No `AGENT-001` row in the Active Items table.
- No `#### AGENT-001` detail subsection remains.

## Out of scope
- Other ledger entries. Loader/default.json changes (seq 01-02). agent_03_03 doc (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261009-122445 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261009-122445 | N/A: doc-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261009-122445 | doc quality checks |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261009-122445 |  |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/done/20261007-154046_approval01_enforce-approval-policy-in-configuration-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-161457_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-120153
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`