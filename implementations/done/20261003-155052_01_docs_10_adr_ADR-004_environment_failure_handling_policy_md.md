# Implementation Procedure: ADR-004 INV-15/INV-16 Classification Recording

## Goal

Record the owner decisions classifying two fallback-like production paths against ADR-004, and update the ADR-004 INV-15/INV-16 Manual Review item so neither path remains listed as open.

## Scope

Modify `docs/10_adr/ADR-004-environment-failure-handling-policy.md` to:
- Record Path 1 classification: ADR-004-scope fallback contradicting INV-03 → option (c) change behavior
- Record Path 2 classification: outside ADR-004 scope (within-database mode switch) → option (a) accepted current behavior
- Clear both paths from the INV-15/INV-16 Manual Review open list

## Assumptions

- The owner decision for UNK-01 has been resolved: Path 1 = option (c), Path 2 = option (a). This is recorded in the Plan's Unknowns table.
- The Manual Review section in the ADR currently lists both paths as open (baseline established during INV-15/INV-16 audit).
- No additional files require modification beyond this ADR document.

## Design decisions

- Path 1 (`orchestrator.py`) is classified as an ADR-004-scope fallback because it exhibits all six elements of Decision 26 (trigger, destination, eligibility, restrictions, result semantics, observability) yet is defined by no Accepted ADR. It contradicts INV-03 (missing/invalid Workflow → abort).
- Path 2 (`retriever.py`) is classified as outside ADR-004 scope because vector→FTS is a within-database query-mode switch, not a Destination substitution to another system/component. Both modes read the same `memories` table.

## Alternatives considered

- Path 1 could be argued as accepted current behavior if the Workflow engine is deemed non-mandatory at runtime. However, INV-03 explicitly mandates abort when the Workflow definition is missing/invalid, making this argument weak.
- Path 2 could be argued as an ADR-004-scope fallback if "Destination" under Decision 26 includes alternative query modes within the same database. The Plan's Design section presents this ambiguity but resolves it toward option (a) based on the evidence that both modes share the same data source.

## Implementation

### Target file

`docs/10_adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

1. Locate the INV-15/INV-16 Manual Review subsection within the ADR (currently under `## Manual Review`).
2. Add a new subsection or entry documenting each path's classification:
   - **Path 1** (`orchestrator.py` sentinel-workflow fallback): Classify as option (c) — ADR-004-scope fallback contradicting INV-03. Record the rationale: the path exhibits all six elements of Decision 26; INV-03 mandates abort on missing/invalid Workflow; the Workflow engine is a mandatory component per INV-03.
   - **Path 2** (`retriever.py` vector-to-FTS degradation): Classify as option (a) — accepted current behavior. Record the rationale: vector→FTS is a within-database mode switch (both modes read the same `memories` table), not a Destination substitution; therefore outside ADR-004 scope.
3. Remove both paths from the INV-15/INV-16 open list in the Manual Review baseline paragraph.
4. Update the Manual Review cadence/owner fields if needed to reflect the resolution.

### Method

Edit the ADR-004 document directly using targeted insertions and deletions:
- Insert classification entries into the Manual Review section after the baseline paragraph.
- Delete the references to the two paths from the open-list enumeration.
- Preserve all other sections of the ADR unchanged.

### Details

**Before edit — Manual Review baseline paragraph (current state):**

```
- INV-15/INV-16 cross-cutting audit (no ADR-004-scope fallback outside ADR-010):
  - **Why not automated**: ...
  - **Procedure**: search production sources for fallback paths, classify as (a) ADR-010 fallback or (b) ADR-004-scope fallback requiring Accepted ADR (Decision 26); file follow-up issue for paths fitting neither.
  - **Baseline**: ADR-010 sole Accepted ADR defining fallback. Treats HTTP errors (401/403), timeouts, connection errors as fallback conditions; empty results and parse errors as non-fallback. Two paths not defined by any Accepted ADR tracked in `issues/20261001-165722_fbaud001_fallback-like-paths-without-accepted-adr-definition.md`: sentinel-workflow mode on Workflow loader failure (`scripts/agent/orchestrator.py`, INV-03) and memory retrieval degradation from vector to FTS-only (`scripts/agent/memory/retriever.py`).
```

**After edit — Manual Review section (proposed state):**

```
- INV-15/INV-16 cross-cutting audit (no ADR-004-scope fallback outside ADR-010):
  - **Why not automated**: ...
  - **Procedure**: search production sources for fallback paths, classify as (a) ADR-010 fallback or (b) ADR-004-scope fallback requiring Accepted ADR (Decision 26); file follow-up issue for paths fitting neither.
  - **Baseline**: ADR-010 sole Accepted ADR defining fallback. Treats HTTP errors (401/403), timeouts, connection errors as fallback conditions; empty results and parse errors as non-fallback. Two paths not defined by any Accepted ADR tracked in `issues/20261001-165722_fbaud001_fallback-like-paths-without-accepted-adr-definition.md`: sentinel-workflow mode on Workflow loader failure (`scripts/agent/orchestrator.py`, INV-03) and memory retrieval degradation from vector to FTS-only (`scripts/agent/memory/retriever.py`).
  - **Resolution (2026-10-03)**: Both paths classified per owner decision (UNK-01):
    - **Path 1** (`orchestrator.py` sentinel-workflow fallback): option (c) — ADR-004-scope fallback contradicting INV-03. Rationale: the path exhibits all six elements of Decision 26 (trigger = loader failure, destination = sentinel degraded workflow, eligibility, restrictions, result semantics = degraded REPL, observability = log + warning); INV-03 mandates abort on missing/invalid Workflow; the Workflow engine is a mandatory component. Requires separate code-change handling.
    - **Path 2** (`retriever.py` vector-to-FTS degradation): option (a) — accepted current behavior. Rationale: vector→FTS is a within-database mode switch (both modes read the same `memories` table), not a Destination substitution; therefore outside ADR-004 scope. No behavioral change required.
  - **Cadence**: at each release review, and whenever a change introduces new fallback or Destination substitution.
  - **Owner**: not yet assigned; cross-cutting ownership decision remains open in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.
```

## Compatibility considerations

- This is a governance documentation change only. No runtime behavior changes are included in this procedure.
- If the owner elects option (b) for either path, a separate Accepted ADR would need to be created/amended — this is out of scope for this procedure.
- If the owner elects option (c) for Path 1, a subsequent implementation procedure must handle the code change separately.

## Security considerations

- No security impact: this is a documentation recording of an existing owner decision.
- The classification itself does not alter any security boundary or access control.

## Rollback considerations

- Revert the ADR document to its pre-edit state via git checkout if the classification is disputed.
- The rollback restores the original open-list status of both paths in the Manual Review.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-004-environment-failure-handling-policy.md` | Document/manual: verify both paths are classified and absent from the open list | Read Manual Review section + `uv run python tools/check_docs_quality.py` | Neither path listed as open; doc quality check passes |

## Completion criteria

- Both Path 1 and Path 2 have a recorded classification (option a/b/c with rationale) in the ADR-004 Manual Review section.
- Neither path appears in the INV-15/INV-16 open list anymore.
- `uv run python tools/check_docs_quality.py` passes without findings.

## Out of scope

- Changing the runtime behavior of either path (requires separate implementation procedure).
- Creating or amending an Accepted ADR for either path (requires separate implementation procedure).
- Resolving the cross-cutting owner question tracked in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.
- Establishing or confirming the INV-15/INV-16 verification mechanism (owned by `plans/done/20260930-212727_plan.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record Path 1 classification (option c) and Path 2 classification (option a) in ADR-004 Manual Review | Pending | — | — | |
| 2 | Clear both paths from the INV-15/INV-16 open list | Pending | — | — | |
| 3 | Run `uv run python tools/check_docs_quality.py` and confirm pass | Pending | — | — | |

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
- **Source issue**: issues/20261001-165722_fbaud001_fallback-like-paths-without-accepted-adr-definition.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261003-130054_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-155052
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md
