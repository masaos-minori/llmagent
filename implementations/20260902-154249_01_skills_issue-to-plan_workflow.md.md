## Goal
Satisfy `REQ-001`/`REQ-002`/`REQ-003` (itp011): add an explicit correction-and-recheck cycle
bound to `skills/issue-to-plan/workflow.md` near Step 2 and Step 8, with `Blocked`-report
content requirements and an explicit `AGENTS.md` Attempt Limit cross-reference.

## Scope
Modify exactly two locations in `skills/issue-to-plan/workflow.md`: Step 2's
adversarial-verification correction text (current lines 142-146) and Step 8's Pass/Fail/
Partial/Blocked paragraph (current lines 355-357). No other line in this file is touched.

## Assumptions
- Re-verified 2026-09-02: both target sentences match the Plan's cited line ranges exactly
  (145-146 for Step 2's "write the corrected understanding" sentence; 355 for Step 8's
  Pass/Fail/Partial/Blocked paragraph) — no drift.
- `itp003` (`plans/done/20260901-214951_plan.md`, processed earlier in this same
  `plan-to-implementation-procedure` batch) resolved its own structurally identical bound to
  N=3, matching `AGENTS.md`'s Attempt Limit. This Plan's UNK-01 adopts the same value for
  consistency (Plan Unknowns, resolved 2026-09-02).
- `itp005`'s Plan (`plans/done/20260901-215253_plan.md`, also processed earlier in this batch)
  defines a cause → re-entry-Step table for Step 8 `Fail`/`Partial` — this Plan's cycle bound
  composes with that table (bounds how many times its re-entry points may be used for the same
  Plan) without redefining it.

## Design decisions
One correction-cycle bound (N=3, matching `AGENTS.md`'s Attempt Limit — Plan Unknowns UNK-01,
resolved 2026-09-02), referenced from both Step 2 and Step 8 as a single rule, not two
independently-worded ones (Plan `Design`/Risks). The `Blocked` report must summarize all
remaining unresolved issues, not only the last one encountered (`REQ-002`).

## Alternatives considered
Leaving the numeric bound unstated pending `itp003`'s own resolution — rejected: `itp003` has
already landed its own resolution (N=3) earlier in this same processing batch, so there is no
longer a reason to defer; using a different number for this Plan's bound (Plan Risks: "Adding
this bound... could read as two separate, inconsistent rules") is exactly the risk avoided by
adopting the same value.

## Implementation
### Target file
skills/issue-to-plan/workflow.md

### Procedure
Add one correction-cycle bound statement, referenced from both Step 2's correction sentence and
Step 8's Pass/Fail/Partial/Blocked paragraph.

### Method
1. Locate Step 2's sentence (current lines 142-146):
   ```
   - If adversarial verification surfaces an unconfirmed item or inconsistency between
     the Issue and current source, do not silently reconcile it — classify it per the
     rule above (`Needs confirmation` if unresolved; `Confirmed by repository evidence` /
     `Derived from confirmed evidence` if resolved) and write the corrected understanding
     into the Plan (Step 5), not the Issue's original, possibly stale claim.
   ```
   Append:
   ```
     A single Issue's Plan tolerates at most 3 consecutive correction-and-recheck cycles
     (matching `AGENTS.md` Loop Prevention > Attempt Limit — this is the same 3-attempt
     bound, applied to Plan-correction cycles specifically, not a separate workflow-specific
     value). If a clean `Pass` is not reached within that bound, stop and report `Blocked:
     Plan requires more than 3 correction cycles — {summary of all remaining unresolved
     issues}` rather than continuing to patch — the summary must list every remaining
     unresolved issue, not only the last one encountered.
   ```
2. Locate Step 8's paragraph (current line 355):
   ```
   Report one of: `Pass` / `Fail` / `Partial` / `Blocked`. If any requirement information
   is unmapped or untraceable, or `Implementation Target Files` is not `Frozen`, do not
   report `Pass` or `Completed`.
   ```
   Append:
   ```
     If reaching `Pass` requires more than 3 consecutive correction-and-recheck cycles (see
     Step 2's cycle bound above), stop and report `Blocked` per that same bound rather than
     continuing to cycle through Step 2/Step 8 indefinitely.
   ```

### Details
This bound composes with, rather than redefines, `itp005`'s Step 8 `Fail`/`Partial` cause →
re-entry-Step mapping (`plans/done/20260901-215253_plan.md`) — it caps how many times that
mapping's re-entry points may be used for the same Plan, it does not change which Step each
failure category resumes from.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a correction-cycle-bound clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added text is internally consistent with `itp003`'s and `itp005`'s landed wording, and does not conflate this bound with `itp003`'s filename-collision retry bound or `itp004`'s Rollback Directive (Plan `Validation plan`).

## Completion criteria
Step 2 and Step 8 both state the same explicit 3-cycle correction bound, the `Blocked`-report
content requirement (summarize all remaining unresolved issues), and an explicit statement that
this bound is the same value as `AGENTS.md`'s Attempt Limit.

## Out of scope
Building actual cycle-counting tooling (Plan Scope Out-of-Scope). `itp003`'s filename-collision
retry bound and `itp004`'s Rollback Directive applicability (Plan Scope Out-of-Scope — distinct
mechanisms, each with its own already-processed Plan). Redefining `itp005`'s Step 8 re-entry
point itself (Plan Scope Out-of-Scope — this Plan only bounds how many times it may be used).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add correction-cycle bound to Step 2 per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 149-153 matched exactly |
| 2 | Add correction-cycle bound cross-reference to Step 8 per Method | Completed | 2026-09-02 | 2026-09-02 | Inserted before itp005's cause→re-entry-Step table, which remains intact at line 402 |
| 3 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 4 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed distinct from itp003's filename-collision retry (line 271) and itp004's Rollback Directive; both cite the same AGENTS.md Attempt Limit consistently |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (correction-cycle bound + Blocked-report content + Attempt Limit cross-reference)
- **Source issue**: `issues/20260901-170327_itp011_chained_plan_corrections_lack_convergence_condition.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260902-104101_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-154249
- **Related target files**: `skills/issue-to-plan/workflow.md`
