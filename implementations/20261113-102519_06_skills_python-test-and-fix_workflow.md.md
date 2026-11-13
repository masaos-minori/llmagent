## Goal
- Update the `pytest-xdist` row and the Step 10 full-run command, and keep serial for flaky, mutation, and coverage runs (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `pytest-xdist` row of the tool table, the full-run command in Step 10, and one sentence for the serial exceptions.
- Not in scope: the flaky-investigation commands, Step 11's coverage command (stays serial), `--testmon` guidance.

## Assumptions
- Write this document only after the Phase 3 verification of the Plan (three random-order parallel runs) passed; if it did not, document the serial recommendation and the open failures instead of the parallel default.
- The `pytest-xdist` row says it is not part of the default run and only after confirming the isolation guard under workers; Step 10 gives the full run as `uv run pytest -m "not integration and not production_paths_allowed"` without `-n`.
- Overlap judged sequencing (Plan Step 2): `plans/20261113-093307_testspeed001_mark-repo-scan-tests.md` (done, its procedures pending) edits the `--testmon-forceselect` line and adds a paragraph in Step 10; this procedure edits the table row and the full-run sentence; different lines, compatible. Implement that Plan's procedures first and re-read Step 10 before editing.
- Shared sentence: Full-suite runs use `-n auto` (`pytest-xdist`; each worker has its own isolation root). Serial execution (no `-n`, or `-n 0`) stays the mode for flaky-test investigation, mutation runs, and every coverage run, because `coverage run` does not measure code executed in worker processes and would report 0% for it.

## Design decisions
- The row states that the isolation guard was confirmed safe under workers (per-worker root) and that parallel is the standard for full runs.

## Alternatives considered
N/A: one statement per file as the Plan requires.

## Implementation
### Target file
`skills/python-test-and-fix/workflow.md`

### Procedure
1. Rewrite the `pytest-xdist` row: parallel execution (`-n auto`) is the standard for local full-suite runs; each worker has its own isolation root (`tests/conftest.py`); `addopts` has no `-n`; do not use it for flaky investigation (Step 3), mutation runs, or coverage runs.
2. In Step 10 change the full-run command to `uv run pytest -n auto -m "not integration and not production_paths_allowed"` and add the shared sentence about the serial exceptions after the paragraph describing the full run.
3. Leave Step 11's coverage command as it is and add that it stays serial.
4. Run the two skill checkers.

### Method
Edit the three places in place; do not restate the isolation design beyond one clause.

### Details
- The flaky-investigation commands keep `-p no:randomly` or explicit seeds and no `-n`.
- Do not edit the `-m` expression of any command other than the Step 10 full run.

## Compatibility considerations
Documentation of local full runs only; no code or CI change.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`.
- `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The row, Step 10, and Step 11 state the default, the opt-out, and the serial exceptions consistently with `rules/toolchain.md` (`AC-005`).
- Both checkers pass.

## Out of Scope
- Other commands carrying the `-m` expression; the marker rule of the `testspeed001` Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the skill and rule checkers named in Validation plan (`routing.md` Tools "When to run which tool") | Pending | — | — |  |

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
- **Related target files**: `skills/python-test-and-fix/workflow.md`
