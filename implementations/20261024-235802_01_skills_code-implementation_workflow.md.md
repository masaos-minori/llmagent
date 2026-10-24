## Goal
- In `skills/code-implementation/workflow.md` make impact-based test selection take effect with the `-m` safety filter (`REQ-001`), scope post-fix re-validation to affected validators (`REQ-002`), require a passing targeted run before a full-suite re-run (`REQ-003`), and record skipped re-runs (`REQ-004`), without weakening any gate.

## Scope
- Step 3e (lines 306-333 at time of writing: the `On a failure` paragraph and `Completed when`) and Step 4 (lines 335-378: the first two bullets and the full-suite bullet).
- No change to the single per-cycle full-suite gate, the 90% `diff-cover` threshold, Attempt Limit or Failure Log wording, or anything in `rules/` or `routing.md`.

## Assumptions
- Anchors confirmed 2026-10-24: Step 4 first bullet (line 341) `pytest --testmon tests/ ... when available`; full-suite bullet (line 355) `exactly once per cycle`; Step 3e `On a failure: fix the code and re-run this same Step 3e`.
- Selector measured 2026-10-24 on `tests/tools/test_check_workitem_structure.py`: `--testmon -m ...` is deactivated ("selection automatically deactivated because -m was used"); `--testmon-forceselect -m ...` deselects unchanged tests. The iteration command is `uv run pytest --testmon-forceselect -m "not integration and not production_paths_allowed" <targeted test file or tests/>`.
- Overlap: `plans/20261024-233356_cut-blocking-question-waits.md` (new `## Question policy` section and Final Report line) and the perf001 procedure (`## Multi-file processing`; `implementations/20261024-235107_03_skills_code-implementation_workflow.md.md`) edit other sections: sequencing dependency, compatible. Re-read the file and re-anchor immediately before editing.
- The Step 4 coverage run (`uv run coverage run -m pytest tests/`) stays separate from testmon (testmon is off under `coverage`).

## Design decisions
- Fix-family table for scoped re-validation: formatting or lint fix runs `ruff`; type fix runs `mypy` and `ruff`; import change runs `lint-imports`, `mypy`, and `ruff`; security fix runs `bandit` and `ruff`. A fix spanning families, or changing imports or public signatures, re-runs the complete Step 3e sequence.
- "Completed when: all of the above pass" is read as "every validator passed against the final content of the files it examines".

## Alternatives considered
- Plain `--testmon` and `--testmon-noselect` were rejected in the Plan Design (deactivated by `-m`, or deselects nothing).

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Step 4 first bullet: replace `pytest --testmon tests/ ... when available` with the `-m`-compatible iteration command above; state the fallback (mirrored-path tests plus `rg`-found importers) only when testmon cannot run, and require the reason to be recorded.
2. Step 3e `On a failure`: add the fix-family table, the full-sequence re-run condition, and the "final content" reading of `Completed when`; add the rule that each skipped validator is recorded in the validation row's Notes as `skipped: {validator} — passed earlier, unaffected by {fix}`.
3. Step 4 fix bullet: apply the same scoped re-run wording by reference to Step 3e (no copy).
4. Step 4 full-suite bullet: state that a full-suite re-run after a failure follows only a passing targeted run that includes the previously failing tests, within the existing Attempt Limit.

### Method
- Define the family table once in Step 3e and reference it from Step 4.
- Cite `skills/python-test-and-fix/workflow.md` Step 10 by name; do not copy its commands beyond the one iteration command.

### Details
- Keep `If a fix here touched formatting, typing, or imports, re-run Step 3e ...` consistent with the new family rule (it becomes an instance of it).

## Compatibility considerations
- Gates and thresholds are unchanged; only iteration discipline and its audit record change. Cold `.testmondata` selects everything on the first run (Plan UNK-02).

## Security considerations
N/A: instruction text only; the `-m` filter keeps `production_paths_allowed` tests excluded from iteration runs.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- After `pgrep -af "pytest|mutmut"` shows no other session, run the iteration command twice on a targeted test file; the second run reports deselected tests.
- `git diff` shows no change to gates, thresholds, Attempt Limit text, `rules/`, or `routing.md`.

## Completion criteria
- Step 4 names the `--testmon-forceselect -m` command with the recorded-reason fallback and no "when available"; Steps 3e and 4 carry the family table, targeted-before-full rule, and skip note; both checkers exit 0.

## Out of Scope
- `## Multi-file processing`, the Question policy, Step 0 load sets, and `rules/toolchain.md` gate definitions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update Step 4's iteration command and fallback | Pending | — | — | |
| 2 | Add scoped re-validation, skip note, and targeted-before-full rule to Steps 3e and 4 | Pending | — | — | |
| 3 | Run the iteration command twice, then both skills checkers, and review `git diff` | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (testmon iteration selector), `REQ-002` (scoped re-validation), `REQ-003` (targeted before full), `REQ-004` (skipped-run record)
- **Source issue**: issues/20261024-203550_perf004_bound-verification-sequence-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-233036_bound-verification-sequence-cost.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235802
- **Related target files**: `skills/code-implementation/workflow.md`
