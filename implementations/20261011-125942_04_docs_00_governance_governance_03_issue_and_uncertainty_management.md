# Implementation Procedure: docs/00_governance/governance_03_issue-and-uncertainty-management.md

## Goal

Remove AGENT-002 and RAG-002 from the Known Issues ledger, confirming they have been resolved by the INV-02 regression test and empty normalization fix.

## Scope

- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`: Remove AGENT-002 and RAG-002 entries from the Known Issues ledger.

## Assumptions

- AGENT-002 and RAG-002 entries exist in the current governance file.
- Both issues are resolved after the implementation of REQ-001 (INV-02 regression test) and REQ-002/REQ-003 (empty normalization fix).
- The adversarial verification confirmed that AGENT-002 and RAG-002 entries are found in the current governance file.

## Design decisions

- Search for AGENT-002 and RAG-002 entries in the governance file.
- Remove them since they have been resolved by the per-consumer ACK/NACK changes.
- Update the Known Deviations section if either entry appears there.

## Alternatives considered

1. Leave the entries as-is since they may have been removed — rejected because we need to confirm the current state and ensure consistency.
2. Move the entries to a "Resolved" section — rejected because the entries should be removed entirely since they are resolved.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Search for AGENT-002 and RAG-002 entries in the governance file.
2. If present, remove them from the Known Issues ledger.
3. If not present, confirm this in the documentation update.

### Method

Documentation modification — remove resolved entries from the Known Issues ledger.

### Details

1. **Remove AGENT-002 and RAG-002 from Known Issues ledger (REQ-004)**:
   - Current state: AGENT-002 at line 65 (table) / 141 (detail); RAG-002 at line 62 (table) / 79 (detail).
   - Action: Remove both entries from the Active Items table and their detail sections.
   - Also check the Known Deviations section for any references to these entries.
   - Evidence: AGENT-002 line 60 (table) / 113 (detail); RAG-002 line 58 (table) / 73 (detail) — corrected from plan's line numbers.

## Compatibility considerations

- Removing entries from the Known Issues ledger is a documentation-only change with no runtime impact.
- Other documents referencing AGENT-002 or RAG-002 (e.g., ADR-014) should also be updated separately.

## Security considerations

N/A — this is a documentation cleanup, not a security boundary change.

## Rollback considerations

- Re-adding the entries restores the Known Issues tracking for these items.
- No production code change — rollback is safe (re-add the entries).

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| governance_03 | Documentation review: verify AGENT-002 and RAG-002 absent | rg | No AGENT-002/RAG-002 entries |

## Completion criteria

- [ ] AGENT-002 and RAG-002 confirmed absent from Known Issues ledger (REQ-004).
- [ ] Documentation review confirms accuracy.

## Out of scope

- Updates to other documents referencing AGENT-002 or RAG-002 (e.g., ADR-014).
- Changes to the Known Issues ledger structure or template.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test changes needed (documentation-only) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No docs/00_index.md mapping for this file |

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
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261007-154050_regtest01_add-inv-02-regression-test-and-keep-original-japanese-text-on-empty-normalization.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-164920_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-125942
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
