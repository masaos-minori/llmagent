## Goal

Remove the resolved findings EVENTBUS-011, EVENTBUS-012, and EVENTBUS-014 from the Known Issues ledger in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (REQ-006), since REQ-003, REQ-001, and REQ-004 respectively resolve them.

## Scope

Modify `docs/00_governance/governance_03_issue-and-uncertainty-management.md` only:

- Remove the ledger table rows for EVENTBUS-011, EVENTBUS-012, EVENTBUS-014.
- Remove the corresponding `#### EVENTBUS-011`, `#### EVENTBUS-012`, `#### EVENTBUS-014` detail subsections.
- Leave EVENTBUS-013 and EVENTBUS-015 (and all non-EventBus findings) untouched.

Referenced/updated by other documents (not modified here): ADR-006 (row 7) and `eventbus_12` (row 8), which cross-reference the same findings.

## Assumptions

- Each ledger table row has a matching detail subsection (e.g. `#### RAG-002` follows the table); both must be removed together.
- The resolution is complete only when the underlying code changes (rows 1-2) are executed; this procedure documents the doc edit, which should be applied alongside or after those.

## Design decisions

- **Remove, don't mark closed**: the plan says these findings are "removed when done"; the ledger drops the rows rather than flipping a status field, keeping the ledger open-findings-only.
- **Minimal footprint**: only the three resolved EventBus findings are touched.

## Alternatives considered

- Setting `Status: closed` instead of deleting: rejected — the plan specifies removal from the ledger.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Locate the ledger table; delete the rows for EVENTBUS-011, EVENTBUS-012, EVENTBUS-014 (current lines ~66-69).
2. Locate and delete the detail subsections `#### EVENTBUS-011`, `#### EVENTBUS-012`, `#### EVENTBUS-014` (search by heading; they follow the table like other `#### <ID>` entries).
3. Confirm EVENTBUS-013 and EVENTBUS-015 rows and detail sections remain intact.
4. Verify no other section cross-references the removed findings in a way that becomes stale (e.g. prose mentioning EVENTBUS-012/014); update such references if present.

### Method

- Delete the table rows and the three `#### EVENTBUS-XXX` heading-and-body blocks; preserve surrounding markdown and heading hierarchy.

### Details

- EVENTBUS-011 resolves under REQ-003 (atomic NACK state).
- EVENTBUS-012 resolves under REQ-001 (NACK idempotency).
- EVENTBUS-014 resolves under REQ-004 (drop `events.acked_at`).
- EVENTBUS-013 ("ACK and NACK do not enforce Consumer ID exclusivity") and EVENTBUS-015 are out of scope — retain.

## Compatibility considerations

- Documentation-only; ensure no dangling cross-reference to the removed IDs remains.

## Security considerations

- No security impact.

## Rollback considerations

- Re-inserting the removed rows and detail sections restores the prior ledger.

## Validation plan

- `rg "EVENTBUS-011|EVENTBUS-012|EVENTBUS-014" docs/00_governance/governance_03_issue-and-uncertainty-management.md` — expect no remaining occurrences (table, detail sections, and prose).
- `tools/check_docs_structure.py` and `tools/check_docs_quality.py` if doc-quality gates run on docs changes.

## Completion criteria

- EVENTBUS-011/012/014 absent from the ledger table and detail sections.
- EVENTBUS-013/015 retained.
- No stale cross-reference to the removed IDs.

## Out of scope

- ADR-006 (row 7).
- `eventbus_12` (row 8).
- The implementation that resolves the findings (rows 1-2).

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
- **Requirement ID**: `REQ-006` (documentation update — Known Issues ledger)
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-132618
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
