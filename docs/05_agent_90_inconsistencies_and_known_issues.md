---
title: "Agent Inconsistencies and Known Issues"
category: agent
tags:
  - agent
  - inconsistencies
  - known-issues
  - bugs
related:
  - 05_agent_00_document-guide.md
---

# Agent Inconsistencies and Known Issues

## Purpose

Records known bugs, specification contradictions, documentation inconsistencies, unimplemented areas, and unresolved questions within the agent layer (`agent/`, `shared/`).

## Design Intent

- Each entry must clearly state "what the problem is", "why it is a problem", "what the operator should check", and "how to address it".
- Remove mechanical mappings like "Code diff note" or "Confirmed at File X Line Y" (information that can be mechanically derived from code should simply point to the source).
- Never omit operational decisions. If something is unclear, keep it and mark it for human review.

## 5-Tier Scheme Exception Rationale

This document retains its 5-tier classification scheme (Design Decision / Implementation Bug / Documentation Gap / Needs Confirmation / Operational Observation) as an intentional, documented area-specific exception to the common 17-field Known Issues template (`00_governance_04_known-issues-template.md`).

**Rationale:** The 5-tier scheme serves a distinct classification purpose not directly expressible by the common template's Status/Type fields. Specifically, it separates "confirmed design decision" (intentional design decision) from "active defect" (implementation bug) at a granularity that the common template's Status (open/resolved/deferred) and Type (implementation-bug/documentation-gap/design-gap/operational-gap) fields do not directly express. The common template conflates "this is a known and accepted design choice" with "this is an acknowledged bug awaiting fix," whereas the Agent document's domain-specific workflow benefits from keeping these semantically distinct.

**Current state:** This document currently has zero open entries to migrate (all historical items resolved or reclassified). The 5-tier scheme adds zero maintenance overhead in its current state.

**Future consideration:** If the common template evolves to include a "Design Decision" type or equivalent discriminator, re-evaluation of this exception may be warranted. Until then, the 5-tier scheme remains the canonical classification for Agent-known-issues.

## Responsibility Boundary

- **What this file owns**: Catalog of known inconsistencies in the agent layer (with 5-level classification).
- **What this file does NOT own**: Individual bug tracking (`issues/`), detailed implementation fix procedures.

## Key Constraints

- Verify that inconsistencies still exist in the current code before deleting an entry.
- For entries classified as "Implementation fix required", create a separate ticket in `issues/`.
- Always specify the reason for "Needs Confirmation" entries.
- Assign one of the 5 classifications to each entry: Accepted current specification / Implementation fix required / Documentation fix required / Issue already tracked / Obsolete and removable.

## Operational Notes

- There are currently no open items (all entries were processed with 5-level classification after migration on 2026-07-23).

## Known Limitations

- Existing entries are classified based on the codebase as of the migration date (2026-07-23). New entries must be added as needed.

## Workflow Engine Discrepancies (ADR-001)

### WF-001: INV-01 and INV-05 duplicate the same invariant condition

- **ID**: WF-001
- **Title**: INV-01 and INV-05 duplicate the same invariant condition
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: documentation-gap
- **Source**: `docs/adr/ADR-001-workflow-engine-mandatory.md`
- **Owner**: Unassigned
- **First Found**: 2026-08-22
- **Target**: `docs/adr/ADR-001-workflow-engine-mandatory.md`
- **Related**: ADR-001
- **Summary**: INV-01 ("All execution paths must flow through the Workflow Engine") and INV-05 ("The Workflow Engine is the sole orchestrator of tool execution") express the same invariant — that all tool execution must go through the Workflow Engine. This duplication creates ambiguity about whether they represent distinct requirements or redundant statements.
- **Current Description**: Both INV-01 and INV-05 assert that tool execution must pass through the Workflow Engine, but neither distinguishes between "execution path" and "orchestration" as separate concerns.
- **Observed Implementation**: The two invariants use different phrasing but cover identical ground — no code pattern exists where a tool executes outside the Workflow Engine while still being orchestrated by it.
- **Impact**: Redundant invariants may lead to confusion during audits and maintenance; operators cannot determine which invariant is violated if a bypass occurs.
- **Recommended Action**: Consolidate INV-01 and INV-05 into a single invariant, or clarify the distinction between "execution path" and "orchestration" if they are meant to be separate concerns.
- **Resolution Notes**: Open — documentation cleanup pending.

---

### WF-002: Missing explicit test for INV-03 (execution success vs verification success)

- **ID**: WF-002
- **Title**: No test verifies that Workflow Engine execution success implies document state verification success
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: missing-test
- **Source**: `docs/adr/ADR-001-workflow-engine-mandatory.md`; `scripts/rag/ingester.py`
- **Owner**: Unassigned
- **First Found**: 2026-08-22
- **Target**: `tests/` directory
- **Related**: ADR-001
- **Summary**: INV-03 states "When the Workflow Engine reports successful execution, the corresponding document state must reflect that execution." However, there is no test that verifies this postcondition — specifically, no test checks that a document's state in the database matches the Workflow Engine's reported outcome after ingestion.
- **Current Description**: The Workflow Engine's `execute()` method returns success/failure, but no test asserts that the document's persisted state aligns with this return value.
- **Observed Implementation**: `ingester.py::execute_ingestion()` calls `WorkflowEngine.execute()`, but the caller does not verify that the document's `status` field in the database reflects the returned outcome.
- **Impact**: A silent failure scenario where the Workflow Engine reports success but the document state remains unchanged — no regression would be caught by existing tests.
- **Recommended Action**: Add a test that calls `WorkflowEngine.execute()` and then queries the document state to confirm alignment between the return value and the database record.
- **Resolution Notes**: Open — test coverage gap identified.

---

### WF-003: Simple Q&A single-stage workflow not implemented per Decision #5

- **ID**: WF-003
- **Title**: Decision #5 of ADR-001 specifies a simple Q&A single-stage workflow, but no such workflow is implemented
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: unimplemented-feature
- **Source**: `docs/adr/ADR-001-workflow-engine-mandatory.md`
- **Owner**: Unassigned
- **First Found**: 2026-08-22
- **Target**: `scripts/workflow_engine/`
- **Related**: ADR-001
- **Summary**: ADR-001 Decision #5 describes a "simple Q&A single-stage workflow" as an example of what the Workflow Engine should support. No implementation of this workflow exists in the current codebase.
- **Current Description**: The ADR explicitly mentions a "simple Q&A single-stage workflow" as a target capability, but no matching workflow definition or handler exists in `scripts/workflow_engine/`.
- **Observed Implementation**: Grep for "q&a", "qa", "single_stage", or similar patterns in `scripts/workflow_engine/` yields no results. The only workflows implemented are multi-stage pipeline workflows.
- **Impact**: The ADR promises a capability that does not exist; users expecting this feature will encounter unexpected behavior.
- **Recommended Action**: Implement the simple Q&A single-stage workflow described in Decision #5, or update the ADR to remove the reference if it was aspirational rather than prescriptive.
- **Resolution Notes**: Open — feature gap identified.

## Related Docs

- `05_agent_00_document-guide.md`
