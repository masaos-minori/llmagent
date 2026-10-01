# Implementation Procedure: Add Canonical Source Conflict entry if decision could not be made

## Goal

Add a Canonical Source Conflict entry to `docs/00_governance/governance_03_issue-and-uncertainty-management.md` if the decision on the single normative source(s) for `eventbus.persistence-schema` could not be determined based on available evidence.

## Scope

- Modify only `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.
- In-Scope: Adding a Canonical Source Conflict entry if the decision could not be made. If the decision can be made (as planned), no changes are needed.
- Out-of-Scope: Updating the Registry (REQ-001); aligning referencing documents (REQ-002–REQ-004).

## Assumptions

- The canon002 plan's design decision is to split `eventbus.persistence-schema` into two Decision Targets based on evidence from ADR-008 INV-04 and `docs/41_db/db_02_architecture_and_schema-schema-reference.md`.
- If the evidence supports this split, no Canonical Source Conflict entry is needed.
- If the evidence is insufficient or contradictory, a Canonical Source Conflict entry must be added.

## Design decisions

- **Approach**: During Phase 2 of the canon002 plan, evaluate whether the evidence supports the proposed split. If it does, proceed with the split and do NOT add a Canonical Source Conflict entry. If it does not, add an entry documenting the conflict.
- **Decision**: Based on canon002 investigation findings, the evidence supports the split — no Canonical Source Conflict entry is expected to be needed. However, this document provides the fallback procedure.

## Alternatives considered

- Always add a Canonical Source Conflict entry regardless of evidence — rejected because it would create noise when the decision can be resolved.
- Skip this step entirely — rejected because the workflow requires checking whether the decision could be made.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Evaluate whether the evidence supports the proposed split of `eventbus.persistence-schema`.
2. If yes: proceed with the split (REQ-001) and do NOT add a Canonical Source Conflict entry.
3. If no: add a Canonical Source Conflict entry documenting the unresolved conflict.

### Method

Read `docs/00_governance/governance_03_issue-and-uncertainty-management.md` to locate the Canonical Source Conflict inventory section. Add an entry only if the decision cannot be made.

### Details

**Step 1: Evaluate evidence**

Based on canon002 investigation findings:
- ADR-008 INV-04 establishes `eventbus.sqlite` as the system of record.
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` line 49 distinguishes between bootstrap DDL and incremental migration as separate operations.
- The registry contract allows multiple sources only for `runtime-behavior`, not for `database-schema`.

**Conclusion**: Evidence supports the split. No Canonical Source Conflict entry needed.

**Step 2: If decision could not be made (fallback)**

If the evidence were insufficient, add the following entry to the Canonical Source Conflict inventory:

```markdown
### eventbus.persistence-schema

- **Decision Target**: eventbus.persistence-schema
- **Competing sources**: 
  - `scripts/db/schema_sql.py::build_eventbus_schema_sql()` (bootstrap DDL)
  - `scripts/eventbus/db.py` (incremental migration)
- **Evidence**: ADR-008 INV-04 establishes eventbus.sqlite as system of record; docs/41_db/db_02_architecture_and_schema-schema-reference.md distinguishes bootstrap DDL and incremental migration as separate operations
- **Required decision**: Determine whether these represent two distinct operational concerns that warrant separate Decision Targets under the current registry contract
```

## Compatibility considerations

- None expected — this is a conditional step that only applies if the decision cannot be made.

## Security considerations

N/A: documentation-only change; no runtime security surface.

## Rollback considerations

Remove the Canonical Source Conflict entry if the decision is later resolved.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Inventory conformance | `uv run python tools/check_needs_confirmation_inventory.py` | Pass (may skip governance docs due to ncinv001) |
| Governance inventory | Conformance | `uv run python tools/check_issue_inventory_conformance.py` | Pass |

## Completion criteria

- If the decision can be made: no Canonical Source Conflict entry is added; the split proceeds per REQ-001.
- If the decision cannot be made: a Canonical Source Conflict entry exists with Decision Target, competing sources, evidence, and required decision.
- The Inventory accurately reflects the current state of open uncertainties.

## Out of scope

Updating the Registry (REQ-001). Aligning referencing documents (REQ-002–REQ-004). Changes to EventBus schema DDL or migration code. Policy `## Area Canonical Maps` cleanup (canon001). Fixing CANONICAL-006 false positives (canon003).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Evaluate evidence for decision | Pending | — | — | REQ-005 |
| 2 | Add Canonical Source Conflict entry if needed | Pending | — | — | REQ-005 |

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
- **Requirement ID**: REQ-005 — resolve Registry validation failure for eventbus.persistence-schema and stale notes paths
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-222937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-224701
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
