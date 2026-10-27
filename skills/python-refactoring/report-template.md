# Python Refactoring — Final Report Template

Load this file at Step 0 (unconditionally). It defines `workflow.md` Step 10's report
structure and the Completion gate that decides whether the cycle may be reported
complete.

---

## Report Structure (Step 10)

Keep diffs minimal. Populate every field from what Steps 2-9 already recorded; MUST NOT re-run
`mutmut` or any other check merely to produce this report. Path A/B report the four Path C
fields (Architecture Baseline, Architecture Before and After, Migration and Rollback Evidence,
ADR Status) as one line `Not applicable`. For each file (or approved atomic migration group,
`path-c.md`), report:

- The Step 2 refactoring intent declaration.
- The Path A/B/C classification decided in Step 2 and its rationale.
- What changed and why.
- The Step 4 behavior lock manifest.
- The Step 5/7 side-effect inventory (`validation.md`) and confirmation that it is
  unchanged.
- The Step 7 public API stability check result (`validation.md`).
- The Step 7 exception behavior freeze result (`validation.md`).
- The Step 7 complexity check: grade before and after for each touched function
  (`validation.md`).
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
  - Suggested follow-up issue: (filed on request via `issue-creator`; see `workflow.md`
    Step 10)
  - Recommended validation:
- Discovery and Path C fields, where `Absent` is the value to report when nothing positive
  exists:

  | Field | Content | Source | Absent |
  |---|---|---|---|
  | Technical Debt Findings | every Finding recorded | `discovery.md` Technical Debt Discovery | `None found` |
  | Responsibility Analysis | the five fields, plus any split candidate (reported, not implemented) | `discovery.md` Responsibility Analysis | `Not applicable` if not run |
  | Documentation Drift | every Drift Finding (six-field schema) | `discovery.md` Documentation Drift Detection | `None found` |
  | Architecture Baseline | the eight fields | `path-c.md` Architecture Baseline | `Not applicable` (Path A/B) |
  | Architecture Before and After | each comparison item as `Pass`/`Fail`/`Not run`/`Blocked` | `path-c.md` Architecture Comparison Validation | `Not applicable` (Path A/B) |
  | Migration and Rollback Evidence | group membership and completion state; rollback strategy exercisability | `path-c.md` Architectural Refactoring Requirements and "Rollback validation" | `Not applicable` (Path A/B) |
  | ADR Status | the ADR `Status`, and whether the file was created under `docs/10_adr/` this cycle or remains a draft | `path-c.md` ADR Requirement | `Not applicable` if no ADR was required or chosen |

  Use only `None found` / `Not applicable` / `Not run` / `Blocked` where no positive finding
  exists; never report a skipped check as passed (`validation.md` Conditional Validation).

---

## Completion Gate

The refactoring is complete only when all of the following are true:

- Target behavior is locked by tests or documented characterization evidence.
- External behavior is unchanged.
- Public APIs are unchanged.
- Visible output is unchanged.
- No new side effects are introduced.
- No unrelated files are modified (compared against the Step 1 working-tree baseline).
- No touched function's `radon cc` grade got worse.
- Required validation passes.
- Conditional validation items are reported with their actual status (`Not run` or `Blocked`).
- The final report includes behavior preservation evidence.
- Any behavior-changing ideas are recorded as proposals, not implemented.

Path C adds `path-c.md` Path C Completion Requirements (additive). If any item cannot be
satisfied, report `Blocked`, not a partial pass; unlike validation items, Completion Gate
items are never optional.
