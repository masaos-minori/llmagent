# Implementation Procedure: Update needs confirmation inventory

## Goal

Update `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Known Issues, Needs Confirmation Inventory, and Canonical Source Conflict inventories to reflect the outcomes of canon001 classification and the addition of Registry entries for uncovered areas.

## Scope

- Modify only `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.
- In-Scope: Register unresolved items produced by canon001 classification; update Known Issues; update Canonical Source Conflict inventory.
- Out-of-Scope: Modifying inline Needs Confirmation markers in the Policy (REQ-001); adding Registry entries (REQ-002); updating area Document Guides (REQ-004–REQ-009).

## Assumptions

- The Needs Confirmation Inventory currently states that no active items remain open, which contradicts the canon001 findings.
- Areas without valid canonical sources (RAG, MCP, Agent, Shared/DB) will be registered as design gaps during REQ-002 execution.
- The checker `check_needs_confirmation_inventory.py` skips governance docs due to ncinv001; manual verification is needed.

## Design decisions

- **Approach**: Register every unresolved item produced by canon001 classification as an Active Item in the Needs Confirmation Inventory. Ensure the Inventory accurately reflects the current state of open uncertainties.
- **Classification of unresolved items**: Items that cannot be resolved within this issue's scope are registered as Concrete Follow-Up Issues with specific file paths.

## Alternatives considered

- Leave the Inventory unchanged and rely on manual tracking: rejected — violates the rule that unresolved items must be registered centrally.
- Remove the Inventory entirely: rejected — loses the structured tracking mechanism.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Review the current state of the Needs Confirmation Inventory.
2. Register unresolved items produced by canon001 classification.
3. Update Known Issues section.
4. Update Canonical Source Conflict inventory.

### Method

Edit `docs/00_governance/governance_03_issue-and-uncertainty-management.md` in-place using targeted edits.

### Details

**Step 1: Review current inventory state**

Read the current Needs Confirmation Inventory `### Active Items` section. Confirm it currently states no active items remain open.

**Step 2: Register unresolved items**

Register the following items as Active Items:

| Item ID | Title | Category | Priority | Evidence | Required Decision |
|---------|-------|----------|----------|----------|-------------------|
| NC-001 | RAG canonical source not identified | Missing-canonical-source | Medium | No `*specification*` file exists under `docs/`; no close equivalent in `docs/21_rag/` | Determine whether a specification document should exist for RAG |
| NC-002 | MCP canonical source not identified | Missing-canonical-source | Medium | No `*specification*` file exists under `docs/`; no close equivalent in `docs/22_mcp/` | Determine whether a specification document should exist for MCP |
| NC-003 | Agent canonical source not identified | Missing-canonical-source | Medium | No `*specification*` file exists under `docs/`; no close equivalent in `docs/23_agent/` | Determine whether a specification document should exist for Agent |
| NC-004 | Shared/DB canonical source not identified | Missing-canonical-source | Medium | No `*specification*` file exists under `docs/`; no close equivalent in `docs/40_shared/` or `docs/41_db/` | Determine whether a specification document should exist for Shared/DB |

**Step 3: Update Known Issues**

Add or update Known Issues related to:
- The hand-maintained `## Area Canonical Maps` table competing with the Registry.
- The discrepancy between the Policy's inline Needs Confirmation markers and the central Inventory.

**Step 4: Update Canonical Source Conflict inventory**

If any conflicting canonical source declarations were discovered during investigation, add them to the Canonical Source Conflict inventory.

## Compatibility considerations

- The Needs Confirmation Inventory must accurately reflect all unresolved items after changes.
- Any area not migrated to the Registry in this issue must be recorded as a concrete follow-up issue in `issues/`, not a vague TODO.

## Security considerations

N/A: documentation-only change; no runtime security surface.

## Rollback considerations

Revert the Inventory updates and restore the original Known Issues and Canonical Source Conflict sections.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Inventory conformance | `uv run python tools/check_needs_confirmation_inventory.py` | Pass (may skip governance docs due to ncinv001) |
| Repository-wide | Manual grep fallback | `grep -n "path does not exist in repository" docs/00_governance/governance_01_documentation-policy.md` | Every remaining marker has a matching Active Item in the central Inventory |

## Completion criteria

- The Needs Confirmation Inventory `### Active Items` reflects every unresolved item produced by canon001 classification.
- No orphaned inline Needs Confirmation markers remain in the Policy without a matching Active Item.
- Known Issues accurately reflect the current state of known problems.
- Canonical Source Conflict inventory includes any discovered conflicts.

## Out of scope

Modifying inline Needs Confirmation markers in the Policy (REQ-001). Adding Registry entries (REQ-002). Updating area Document Guides (REQ-004–REQ-009). Fixing the `eventbus.persistence-schema` Registry validation failure (canon002). Fixing checker defects (ncinv001).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Review current inventory state | Pending | — | — | REQ-003 |
| 2 | Register unresolved items | Pending | — | — | REQ-003 |
| 3 | Update Known Issues | Pending | — | — | REQ-003 |
| 4 | Update Canonical Source Conflict inventory | Pending | — | — | REQ-003 |

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
- **Requirement ID**: REQ-003 — classify nonexistent canonical source paths in documentation policy and align Policy, Registry, and Document Guides
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-222351_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-224049
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
