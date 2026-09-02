## Goal
Satisfy `REQ-001`/`REQ-002` (ptip004): add an explicit short-circuit to
`skills/plan-to-implementation-procedure/workflow.md` Step 2 for the case where every
`Implementation Target Files` row is already implemented, mirroring `code-implementation`
Step 1's precedent.

## Scope
Modify exactly Step 2 of `skills/plan-to-implementation-procedure/workflow.md` (current lines
94-117): insert a new bullet after the Freeze-status confirmation (current lines 103-105) and
before the Revalidation instruction (current lines 106-109). No other Step in this file is
touched.

## Assumptions
- Re-verified 2026-09-02: Step 2's current structure (lines 94-117) matches the Plan's
  Background description exactly — no existing short-circuit for the all-rows-implemented case,
  confirmed by direct read.
- `code-implementation/workflow.md` Step 1's "All-steps-completed check" precedent (cited in
  Plan Background) is used as the model for this short-circuit's report format.

## Design decisions
Place the short-circuit check immediately after Freeze-status confirmation and before the more
expensive per-row Revalidation step, so a fully-covered Plan can skip both Revalidation and
Step 3's full per-row loop (Plan `Design`). Reuse Step 3's existing `Already implemented`
classification criteria verbatim (`REQ-002`) — do not restate them with any drift risk.

## Alternatives considered
Placing the short-circuit in Step 1 instead of Step 2 — rejected: Step 1 only validates that
the target Plan file exists (per `rules/workflow-lifecycle.md` Target Validation); the
`Implementation Target Files` table and its rows are not read until Step 2, so the check cannot
run any earlier than Step 2 without duplicating Step 2's own file-read.

## Implementation
### Target file
skills/plan-to-implementation-procedure/workflow.md

### Procedure
Insert a short-circuit check and report format into Step 2, between Freeze-status confirmation
and Revalidation.

### Method
1. Locate current lines 103-109:
   ```
   - Confirm the `Implementation Target Files` section's `Freeze status` is `Frozen`. If
     it is not `Frozen`, stop and report `Blocked` — freezing is `issue-to-plan` Step 8's
     responsibility, not this workflow's; do not freeze it here.
   - Revalidate the frozen inventory per `rules/workflow-lifecycle.md` Implementation
     Target Files Validation (Plan Freeze) — Revalidation, before proceeding to Step 3.
     If revalidation finds a discrepancy, correct the Plan per that section's rules
     before continuing.
   ```
2. Insert a new bullet between them:
   ```
   - **All-rows-already-implemented short-circuit**: check whether every
     `Implementation Target Files` row's `target_file_slug` already matches a document
     under `implementations/` or `implementations/done/` whose `Source plan` and
     `Related target files` confirm full coverage of that row — the identical criteria
     Step 3's `Already implemented` classification uses per-row (see Step 3 below), not
     a separate, looser check. If every row meets this criteria, skip Revalidation and
     Step 3's per-row loop entirely and proceed directly to Step 4's move, reporting the
     short-circuit explicitly: `All rows already implemented — proceeding to Step 4`.
   ```

### Details
This does not change Step 3's own per-row classification logic (Plan Scope Out-of-Scope) —
it only adds an earlier, equivalent check for the all-rows case, reusing the same criteria.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure short-circuit clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added short-circuit reuses Step 3's classification criteria verbatim rather than restating them with drift (Plan `Tests`).

## Completion criteria
Step 2 recognizes a Plan whose every row is already implemented before the full Step 2
Revalidation/Step 3 per-row loop runs, with an explicit short-circuit report, using criteria
identical to Step 3's existing classification.

## Out of scope
Changing Step 3's own per-row classification logic (Plan Scope Out-of-Scope) — only adding an
earlier, equivalent check for the all-rows case.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert all-rows-implemented short-circuit per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 103-108 matched exactly |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 3 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed reference to Step 3's `Already implemented` classification resolves correctly (line 210) |
| 4 | Documentation update | Completed | 2026-09-02 | 2026-09-02 | N/A: this file is the documentation being updated; no `docs/00_index.md` task-scope mapping applies |

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
- **Requirement ID**: REQ-001, REQ-002 (all-rows-already-implemented short-circuit)
- **Source issue**: `issues/20260901-171500_ptip004_no_short_circuit_when_all_rows_already_implemented.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-213217_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153048
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
