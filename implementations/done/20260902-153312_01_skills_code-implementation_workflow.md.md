## Goal
Satisfy `REQ-001`/`REQ-002` (cip006): add an explicit cross-file conflict detection-and-stop
instruction to `skills/code-implementation/workflow.md` Step 3, and state the required
re-validation action (full test-suite re-run) for an already-processed, potentially-affected
earlier file in Step 4.

## Scope
Modify exactly two locations in `skills/code-implementation/workflow.md`: Step 3's
adversarial-verification paragraph (current lines 124-130) and Step 4's "exactly once"
full-suite-run bullet (current lines 158-159). This is one merged target-file row (see Plan's
2026-09-02 correction note: the original Plan had two rows both citing this same file, violating
the one-row-per-file rule; merged into one row covering both edits). Out of scope: building
automated cross-file dependency-detection tooling (Plan Scope Out-of-Scope) — this only adds
the workflow instruction for the case where a conflict is discovered during normal Step 3/Step
4 work.

## Assumptions
- Re-verified 2026-09-02: Step 3's adversarial-verification paragraph is at current lines
  124-130 (same location confirmed for `cip003`, processed earlier in this batch — note
  `cip003`'s own edit to this same paragraph has not yet been applied to the actual file, so no
  conflict between the two Plans' procedure documents exists yet; whichever lands first should
  be re-verified against the other's edit before the second is applied). Step 4's "exactly
  once" rule is at current lines 158-159, not the Plan's originally-cited "line 142-145" — a
  ~15-line shift with unchanged content, corrected in the Plan.
- Per Plan Unknowns (UNK-01, non-blocking) and the Plan's own Assumptions, the re-validation
  action is always a full test-suite re-run for the earlier file (not a narrower targeted
  re-check) — this choice is stated explicitly per the Plan's own Assumptions.

## Design decisions
Use the exact format `Blocked: cross-file conflict with {earlier file} — {description}` for
the stop-and-report instruction (Plan `Design`), mirroring `ptip003`'s document-consistency
resolution pattern but for real source code, with materially higher stakes (Plan `Reason for
change`).

## Alternatives considered
A narrower, targeted re-check instead of a full test-suite re-run for the affected earlier file
— considered per Plan Unknowns (UNK-01) but not adopted; the Plan's own Assumptions section
already commits to "always a full test-suite re-run," so this document follows that decision
rather than re-opening it.

## Implementation
### Target file
skills/code-implementation/workflow.md

### Procedure
Add a cross-file-conflict detection-and-stop instruction to Step 3, and a conditional
re-validation instruction to Step 4.

### Method
1. Locate Step 3's current lines 124-130 (the adversarial-verification paragraph — see also
   `cip003`'s seq for this same paragraph's own, separate termination-condition addition):
   ```
   Before implementing, perform **adversarial verification** of the procedure's claims
   about current source: do not assume its Procedure/Method/Details are still
   accurate — check via `rg`/Read whether the target file, symbol, line numbers, and
   call path it describes still match current source, and whether any stated assumption
   or scope boundary is stale or inconsistent with a sibling procedure document or the
   source Plan.
   ```
   Append a new paragraph (after the existing "If verification finds an unconfirmed item..."
   correction paragraph that follows it):
   ```
   If adversarial verification, or the implementation itself, reveals that the current
   file's required change conflicts with, or invalidates an assumption of, an
   already-processed file's change in the same Multi-file-processing batch, stop and
   report `Blocked: cross-file conflict with {earlier file} — {description}` rather than
   proceeding. Do not implement around the conflict silently.
   ```
2. Locate Step 4's current lines 158-159:
   ```
   - Run the repository-defined full test suite exactly once, after targeted tests
     pass — the only full-suite run for this cycle; Step 6 MUST NOT run tests again.
   ```
   Append a conditional exception clause:
   ```
     If Step 3 reported a cross-file conflict with an already-processed earlier file (see
     Step 3), re-run the full test suite for that earlier file's implementation procedure
     cycle before continuing the batch — this is a required exception to "exactly once,"
     scoped strictly to the conflict-detected case, not a routine re-run.
   ```

### Details
The cross-file-conflict instruction (Step 3) does not change what Step 3 already checks for the
*current* file (Plan Scope Out-of-Scope: no new detection tooling) — it only adds the
stop-and-report action for a conflict discovered through existing checks. The Step 4 exception
is conditional on that Step 3 report, not routine, per the Plan's own Risk mitigation ("Ensure
the re-validation trigger is conditional on an actually-detected conflict, not routine").

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure conflict-handling clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file. Both edits (Step 3 and
Step 4) belong to this one row/document — if reverting, revert both together to avoid a
dangling cross-reference (Step 4's clause references "see Step 3").

## Validation plan
- Manual review: confirm the added instruction does not conflict with Step 4's existing "exactly once" full-suite-run rule outside the conflict-detected case (Plan `Tests`).

## Completion criteria
Step 3 states an explicit stop-and-report action (`Blocked: cross-file conflict with {earlier
file} — {description}`) for a detected cross-file conflict, and Step 4 states the required
full-test-suite re-validation action for the affected earlier file, scoped to that
conflict-detected case only.

## Out of scope
Building automated cross-file dependency-detection tooling (Plan Scope Out-of-Scope) — this
document only adds the workflow instruction for the case where a conflict is discovered during
normal Step 3/Step 4 work.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add cross-file-conflict detection-and-stop instruction to Step 3 per Method | Completed | 2026-09-02 | 2026-09-02 | `cip003`'s edit to the same paragraph had already landed (confirmed at lines 135-152); this edit inserted after it with no conflict |
| 2 | Add conditional re-validation exception to Step 4 per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 174-176 matched exactly |
| 3 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 4 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed the Step 4 exception is explicitly scoped to the conflict-detected case, not routine |

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
- **Requirement ID**: REQ-001 (Step 3 cross-file-conflict stop-and-report), REQ-002 (Step 4 re-validation action)
- **Source issue**: `issues/20260901-172400_cip006_cross_file_implementation_ordering_dependency_undefined.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-212238_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153312
- **Related target files**: `skills/code-implementation/workflow.md`
