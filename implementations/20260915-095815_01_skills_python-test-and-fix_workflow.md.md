## Goal
Add an explicit "Completed when" line to Step 3 (Flaky Detection) and Step 7
(Contract Validation), and explicit `mutmut run` command-failure handling to Step 4
(Mutation Testing), in `skills/python-test-and-fix/workflow.md` (REQ-001, REQ-002,
REQ-003).

## Scope
In scope: one "Completed when" line at the end of Step 3; one command-failure-
handling line inserted before Step 4's existing "0 surviving mutants" paragraph; one
"Completed when" line at the end of Step 7. Out of scope: Steps 1, 2, 5, 6, 8-13;
changing Step 4's existing "0 total mutants" false-positive handling.

## Assumptions
- Adding 2 short lines and 1 command-failure line will not push this file over the
  400-line File Split Rule trigger in `skills/DESIGN.md`.
- `rules/ai-execution.md`'s "Step-Level Failure Triage (Base)" section (confirmed via
  Reference Files below) is still the correct cross-reference target for REQ-002.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), REQ-002 is inserted before Step 4's existing "0 surviving mutants"
paragraph (per the Plan's own ordering and Constraint), establishing that the command
actually ran before the existing false-positive handling is considered, and
cross-references `rules/ai-execution.md` Step-Level Failure Triage rather than
restating its branches.

## Alternatives considered
- Appending REQ-002 after the existing "0 surviving mutants" handling instead of
  before it — rejected: the Plan's own Design section and Implementation steps
  specify inserting it *before*, so the command-failure check reads first, logically
  preceding the "did it run and produce zero mutants" case.

## Implementation
### Target file
skills/python-test-and-fix/workflow.md

### Procedure
1. Locate the end of Step 3 (after "pytest tests/ -p no:randomly ..."), insert the
   "Completed when" line (REQ-001) before the `---` separator.
2. Locate Step 4, immediately after the `mutmut show <id>` code block and before "A
   surviving mutant means..." (line 134), insert the command-failure line (REQ-002).
3. Locate the end of Step 7 (after the `test_floats_to_blob_roundtrip` code block),
   insert the "Completed when" line (REQ-003) before the `---` separator.
4. Leave Steps 1, 2, 5, 6, 8-13 and Step 4's existing "0 surviving mutants" handling
   (lines 134-139) unchanged.

### Method
Use `Edit` with three separate `old_string`/`new_string` pairs, each anchored on
unique existing text (Step 3's final command, the `mutmut show <id>` line, and Step
7's final code block).

### Details
- Step 3 (after "pytest tests/ -p no:randomly # disable to see if it disappears"):
  add `**Completed when**: the failure is confirmed either as seed-order-dependent
  (fails only on certain seeds) or as true non-determinism independent of seed (fails
  under \`--reruns\` regardless of seed), with the dependency (if any) identified via
  the replay commands above.`
- Step 4 (immediately after "\`mutmut show <id>\` # inspect surviving mutant" and
  before "A surviving mutant means..."): insert `If \`mutmut run\` itself exits
  non-zero (distinct from completing and reporting results): treat as a tool failure
  per \`rules/ai-execution.md\` Step-Level Failure Triage — do not report mutation
  testing as passed.`
- Step 7 (after the \`test_floats_to_blob_roundtrip\` code block): add `**Completed
  when**: a property-based test has been written for each function meeting both
  listed conditions, or the Step is confirmed not applicable (no function in scope
  meets both conditions).`

Do not alter Step 4's existing "0 surviving mutants" paragraph (lines 134-139) or any
other Step.

## Compatibility considerations
This file is referenced by 3+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file edit adding 3 independent blocks; revertable via `git checkout --
skills/python-test-and-fix/workflow.md` (pre-commit) or a follow-up commit reverting
this file only.

## Validation plan
- `git diff skills/python-test-and-fix/workflow.md` — confirm Step 3/Step 7
  "Completed when" lines added, Step 4's command-failure line inserted before the
  existing "0 total mutants" handling (which remains unchanged), no other line
  touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
Step 3 and Step 7 each have an explicit "Completed when" line; Step 4 explicitly
distinguishes a `mutmut run` command failure from a "ran but 0 total mutants" result,
routed to Step-Level Failure Triage; `tools/check_skills_references.py` passes (Plan
AC-1, AC-2).

## Out of scope
Steps 1, 2, 5, 6, 8-13 of this same file; Step 4's existing "0 total mutants"
handling; any other file; any other evaluation criterion from the source review
batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-110115 | 20260915-110115 | 3 insertions: Step 3 completion, Step 4 command-failure, Step 7 completion |
| 2 | Add or update tests per Validation plan | Completed | 20260915-110115 | 20260915-110115 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-110115 | 20260915-110115 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-110115 | 20260915-110115 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (Step 3/7 completion; Step 4 command-failure handling)
- **Source issue**: issues/20260914-115502_skillqa11_python-test-and-fix-step-completion-and-mutmut-failure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-090326_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-095815
- **Related target files**: skills/python-test-and-fix/workflow.md