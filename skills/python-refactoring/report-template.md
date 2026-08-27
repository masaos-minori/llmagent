# Python Refactoring — Final Report Template

Load this file at Step 0 (unconditionally). It defines `workflow.md` Step 10's report
structure and the Completion gate that decides whether the cycle may be reported
complete.

---

## Report Structure (Step 10)

Keep diffs minimal. For each file (or approved atomic migration group, per `path-c.md`),
report:

- The Step 2 refactoring intent declaration.
- The Path A/B/C classification decided in Step 2 and its rationale.
- What changed and why.
- The Step 4 behavior lock manifest.
- The Step 5/7 side-effect inventory (`validation.md`) and confirmation that it is
  unchanged.
- The Step 7 public API stability check result (`validation.md`).
- The Step 7 exception behavior freeze result (`validation.md`).
- The Step 7 import boundary evidence, if imports changed (`validation.md`).
- The Step 8 diff classification summary.
- **Conditional tool status** (`validation.md` Conditional Validation):
  - Which conditional tools were not run and why.
  - Whether any `Blocked` items remain.
- **Mutation testing evidence**:
  - Mutated paths
  - Number of mutations generated
  - Number of killed mutations
  - Number of surviving mutations
  - Number of equivalent mutations
  - Actions taken for surviving mutations
  - Tests added because of mutation results
  - Final mutation status

  A surviving mutation is acceptable only if it is explicitly classified as equivalent and
  the reason is documented.
- **Behavior preservation evidence**:
  - Baseline tests run before refactoring
  - Characterization tests added, if any
  - Public API signatures checked
  - Visible output checked, if applicable
  - Exception behavior checked
  - Side effects checked
  - Mutation testing result
  - Final validation result
- **Proposals not implemented**, for every behavior-changing idea that was not implemented,
  using this format:
  - Title:
  - Reason:
  - Behavior risk:
  - Affected files:
  - Suggested follow-up issue:
  - Recommended validation:
- **Technical Debt Findings**: report every Finding recorded by `discovery.md`
  Technical Debt Discovery for the current target file/migration group, or
  `None found`.
- **Responsibility Analysis**: report the five fields recorded by `discovery.md`
  Responsibility Analysis (responsibilities, dependencies, side effects, state
  ownership, branching) and any split candidate reported (not implemented) per that
  section's rule, or `Not applicable` if Responsibility Analysis was not run for this
  file.
- **Documentation Drift**: report every Drift Finding recorded by `discovery.md`
  Documentation Drift Detection's six-field schema during Step 3, or `None found`.
- **Architecture Baseline**: report the eight fields captured by `path-c.md`
  Architecture Baseline when the change is Path C, or `Not applicable` for Path A/B.
- **Architecture Before and After**: report the before/after comparison result for each
  item defined by `path-c.md` Architecture Comparison Validation, each as
  `Pass`/`Fail`/`Not run`/`Blocked` per that section's reporting rule, or `Not
  applicable` for Path A/B.
- **Migration and Rollback Evidence**: report the atomic migration group's membership
  and completion state (per `path-c.md` Architectural Refactoring Requirements) and the
  rollback strategy's exercisability (per that section's pre-implementation checklist
  item, cross-validated by `path-c.md` Architecture Comparison Validation's "Rollback
  validation" item), or `Not applicable` for Path A/B.
- **ADR Status**: report the ADR's `Status` value (per `path-c.md` ADR Requirement's
  convention) and whether the file was actually created under `docs/adr/` this cycle or
  remains a draft pending explicit documentation-update instruction, or `Not applicable`
  when no ADR was required or chosen for this change.

All seven items above use exactly the vocabulary `None found` / `Not applicable` /
`Not run` / `Blocked` where no positive finding exists, matching `validation.md`
Conditional Validation's existing reporting pattern ("do not report the skipped check
as passed").

---

## Completion Gate

The refactoring is complete only when all of the following are true:

- Target behavior is locked by tests or documented characterization evidence.
- External behavior is unchanged.
- Public APIs are unchanged.
- Visible output is unchanged.
- No new side effects are introduced.
- No unrelated files are modified.
- Required validation passes.
- Conditional validation items are reported with their actual status (`Not run` or `Blocked`).
- The final report includes behavior preservation evidence.
- Any behavior-changing ideas are recorded as proposals, not implemented.

Path C requires additional items — see `path-c.md` Path C Completion Requirements; they
are additive to, not a replacement for, the gate above.

If any item is not satisfied, do not report the task as complete.
