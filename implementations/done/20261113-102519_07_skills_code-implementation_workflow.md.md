## Goal
- Update the Step 4 full-suite wording so the once-per-cycle full run is parallel and the coverage run stays serial (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the full-suite bullet of Step 4 and the coverage-gate bullet.
- Not in scope: the targeted-scope command, Row mapping, the Final Report, the documentation-only case.

## Assumptions
- Write this document only after the Phase 3 verification of the Plan (three random-order parallel runs) passed; if it did not, document the serial recommendation and the open failures instead of the parallel default.
- Step 4 runs "the repository-defined full test suite exactly once per cycle" and feeds the coverage gate through `uv run coverage run -m pytest tests/`; neither names `-n`.
- Overlap judged sequencing (Plan Step 2): the Plans for `testspeed001` (one targeted-scope command) and `testspeed006` (a documentation-only case) also edit Step 4 of this file; this procedure edits the full-suite and coverage bullets only. Implement in the order `testspeed001`, `testspeed004`, `testspeed006` and re-read Step 4 each time.
- Shared sentence: Full-suite runs use `-n auto` (`pytest-xdist`; each worker has its own isolation root). Serial execution (no `-n`, or `-n 0`) stays the mode for flaky-test investigation, mutation runs, and every coverage run, because `coverage run` does not measure code executed in worker processes and would report 0% for it.

## Design decisions
- Name the parallel command by reference to `rules/toolchain.md` section 6 and keep the coverage run serial with the reason.

## Alternatives considered
N/A: one statement per file; the details live in `rules/toolchain.md`.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. In the full-suite bullet of Step 4 add that the once-per-cycle run uses the parallel command of `rules/toolchain.md` section 6 (`-n auto`).
2. In the bullet that makes the full-suite run feed the coverage gate, state that this run stays serial (no `-n`) because `coverage run` does not measure code run in worker processes, so one cycle's full run is the serial coverage run or the parallel run, not both.
3. Run the two skill checkers.

### Method
Two small edits in Step 4. Keep the wrapped line style and the existing exceptions list ("exactly once per cycle").

### Details
- Resolve the apparent tension: the cycle runs the suite once, and that run is the coverage run (serial) when a source file changed, otherwise the parallel run; state it in one sentence and do not add a second run.
- Do not change the diff-cover command or its `N/A` rule.

## Compatibility considerations
Documentation of the cycle's test run; no code or CI change.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`.
- `uv run python tools/run_validation_gates.py`.

## Completion criteria
- Step 4 names the parallel default by reference and the serial coverage exception without adding a second full run (`AC-005`).
- Both checkers pass.

## Out of Scope
- The targeted-scope command and the documentation-only case (other Plans).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-195509 | 20261113-195509 |  |
| 2 | Run the skill and rule checkers named in Validation plan (`routing.md` Tools "When to run which tool") | Completed | 20261113-195509 | 20261113-195509 |  |

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
- **Requirement ID**: REQ-005 (document the default)
- **Source issue**: issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-093804_testspeed004_adopt-parallel-test-execution.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-102519
- **Related target files**: `skills/code-implementation/workflow.md`