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

**Rationale:** The 5-tier scheme serves a distinct classification purpose not directly expressible by the common template's Status/Type fields. Specifically, it separates "confirmed design decision" (意図的な設計判断) from "active defect" (実装上の不具合) at a granularity that the common template's Status (open/resolved/deferred) and Type (implementation-bug/documentation-gap/design-gap/operational-gap) fields do not directly express. The common template conflates "this is a known and accepted design choice" with "this is an acknowledged bug awaiting fix," whereas the Agent document's domain-specific workflow benefits from keeping these semantically distinct.

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

## Related Docs

- `05_agent_00_document-guide.md`
