## Goal
Satisfy `REQ-001`/`REQ-002` (itp002): add concrete, checkable termination conditions to
`skills/issue-to-plan/workflow.md` Step 2 (adversarial verification) and Step 3 (Path B full
inspection).

## Scope
Modify exactly two locations in `skills/issue-to-plan/workflow.md`: Step 2's adversarial
verification bullet (current lines 127-133) and Step 3's Path B bullet (current lines
171-174). `skills/issue-to-plan/workflow-path-b.md` is read as a reference (its four analysis
dimensions and existing "once all four analyses above are complete" gate are cited by name) but
is **not** modified — see the Plan's revalidation note explaining why that file was removed as
a target during this cycle.

## Assumptions
- Re-verified 2026-09-02: Step 2's adversarial-verification text and Step 3's Path B text both
  still match the Plan's Background quotes exactly (current line numbers 122-154 for the Step 2
  section, 158-177 for Step 3 — a shift from the Plan's originally-cited "line 14-18"/"line
  20-23", which referred to line numbers within the Plan's own Background quotation, not
  `workflow.md`'s actual line numbers; content is unchanged).
- `skills/issue-to-plan/workflow-path-b.md` already lists specific example commands per
  dimension and already gates progression on "once all four analyses above are complete" (its
  closing line) — no edit to that file is needed for Step 3's new condition to cite it
  accurately by reference.

## Design decisions
Two termination conditions, each anchored to existing structure rather than inventing new
metrics (Plan `Design`, corrected 2026-09-02 after this session found the Plan's original
Design section was copy-pasted from an unrelated sibling plan, itp007):
- Step 2: stop once every field extracted per `templates/issue.md` has been checked against at
  least one concrete source, and no new disconfirming evidence was found in the last full pass.
- Step 3 Path B: stop each of the four analysis dimensions once its `workflow-path-b.md`-listed
  toolchain command(s) have been run once and reviewed — no re-run without a changed input, per
  `rules/ai-execution.md` Tool Usage.

## Alternatives considered
Also editing `workflow-path-b.md` to add a per-dimension termination note — rejected after
re-reading that file: it already lists one set of example commands per dimension and already
closes with a completion gate, so Step 3's new condition can cite it by reference without
duplicating or restating its content there.

## Implementation
### Target file
skills/issue-to-plan/workflow.md

### Procedure
Add one termination-condition sentence to Step 2 and one to Step 3, plus a sentence relating
both to the workflow-level Completion Criteria.

### Method
1. Locate Step 2's adversarial-verification bullet (current lines 127-133):
   ```
   - **Adversarial verification**: do not stop at confirming the Issue's claims — actively
     look for evidence that would refute or narrow them: whether the described problem has
     already been fixed elsewhere, whether the named files/symbols/line numbers still
     exist as stated, whether a claimed dependency or side effect is missing or
     overstated, and whether two claims within the same Issue (or against a related
     `plans/`/`implementations/` document) contradict each other. Treat this as a search
     for disconfirming evidence, not reconfirmation of prior findings.
   ```
   Append a new sentence:
   ```
     Stop once every field extracted per `templates/issue.md` (Step 2's own extraction list,
     below) has been checked against at least one concrete source (a file, test, or existing
     Plan/Implementation document), and no new disconfirming evidence was found in the last
     full pass over that field list — this is complementary to, not a replacement for,
     `rules/workflow-lifecycle.md`'s workflow-level Completion Criteria, which gates the whole
     cycle rather than this Step alone.
   ```
2. Locate Step 3's Path B bullet (current lines 171-174):
   ```
   - **Path B**: perform the full inspection — source files, tests, configuration,
     documentation, callers and callees, dependencies, data ownership, side effects, error
     handling, compatibility constraints, and security constraints. This inspection feeds
     the broader analysis in Step 5.
   ```
   Append a new sentence:
   ```
     Stop each of the four analysis dimensions (Architecture analysis, Dependency graphing,
     Historical analysis, Operational dependency inspection — see
     `workflow-path-b.md`) once its listed toolchain command(s) have been run once against
     the relevant target and their output reviewed; do not re-run the same command against
     the same target without a changed input, per `rules/ai-execution.md` Tool Usage. This
     is consistent with `workflow-path-b.md`'s own existing "once all four analyses above
     are complete" gate, not a change to it.
   ```

### Details
Neither edit changes what evidence Step 2/3 require finding (Plan Scope Out-of-Scope) — only
when to stop looking for it.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure termination-condition clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added termination conditions are checkable (an agent following them can determine "done" without further judgment calls) and do not introduce a contradiction with existing Step 2/3 text or `rules/ai-execution.md` Reasoning and Planning (Plan `Tests`).

## Completion criteria
Step 2 and Step 3 (Path B) each state a concrete, checkable condition under which
investigation for that Step is considered complete, without contradicting
`rules/ai-execution.md`'s existing qualitative guidance.

## Out of scope
`skills/issue-to-plan/workflow-path-b.md` — read as a reference only, not modified (see
Assumptions/Alternatives considered). Changing what evidence Step 2/3 require finding (Plan
Scope Out-of-Scope). Termination conditions for other skills' Steps not covered by this issue.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Step 2 termination condition per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 127-133 matched exactly |
| 2 | Add Step 3 Path B termination condition per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 171-174 matched exactly |
| 3 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 4 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed both additions cite `workflow-path-b.md`'s existing dimension names/gate accurately, no contradiction introduced |

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
- **Requirement ID**: REQ-001, REQ-002 (concrete termination conditions for Step 2 and Step 3 Path B)
- **Source issue**: `issues/20260901-170327_itp002_missing_explicit_step_termination_conditions.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-214617_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152247
- **Related target files**: `skills/issue-to-plan/workflow.md`
