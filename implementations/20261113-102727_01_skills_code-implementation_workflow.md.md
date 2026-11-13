## Goal
- Add a documentation-only case to Step 4 (path definition and replacement verification), scope the 0-collected and full-suite rules, and align Row mapping rows 2 and 3 and the Final Report's test-row description (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new bullet at the start of Step 4's bullet list, Row mapping rows 2 and 3, and the Final Report description of the fourth step.
- Not in scope: the existing Step 4 bullets (targeted scope, full suite, coverage), Step 3e, Step 5, Step 6, the question policy.

## Assumptions
- Step 4 requires the 0-collected check ("a 0-collected, exit-0 run is not a pass") and the full-suite run "exactly once per cycle", and has only the diff-cover `N/A` exemption for documentation; Row 3 reads "Step 3e passes and Step 4's full-suite run passes"; the Final Report row 4 reads "Test the feature and pass required tests/coverage". Falsifier: the text moved; locate it with `rg -n "exactly once per cycle|Test the feature and pass"`.
- Step 6 skips its content checks when Step 5 made no edits, so the replacement checkers must run in Step 4 for the files Step 3d changed; Step 6 keeps covering the files Step 5 edits.
- The documentation-only path set is the default `docs/`, `issues/`, `plans/`, `implementations/`; `skills/`, `rules/`, `templates/`, `prompts/` stay on the existing Step 4 (Plan `UNK-01`: seven test files mention those trees). The owner may widen it by amending the Plan before this procedure is written.
- The replacement does not include `pre-commit run --files` (about 210 s on one docs file on 2026-11-13) or a repository-scan run; the commit-phase gates (`skills/git-commit-and-sync/workflow.md` Phase 4 and the hooks run by `git commit`) are the second line, not the evidence that closes the cycle.
- Overlap judged sequencing (Plan Step 2): the Plans for `testspeed001` (one targeted-scope command) and `testspeed004` (full-suite and coverage wording) also edit Step 4 of this file; this procedure adds a separate bullet and edits Row mapping and the Final Report. Implement the procedures of those Plans first and re-read Step 4 before editing.

## Design decisions
- Define documentation-only by the set of files the cycle changes, not by the files its procedure mentions (the 14 archived procedures of 2026-11-12 mention code paths as evidence but each changes one `docs/` file).
- State the replacement by reference to `routing.md` "When to run which tool" and do not copy its table.

## Alternatives considered
- `pre-commit run --files` in the cycle: rejected (cost comparable to the full suite).
- A repository-scan run (the repo_scan marker): rejected (runs the same checkers the commit hooks run again; Plan `UNK-02`).

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Re-read Step 4, Row mapping, and the Final Report (the Plans for `testspeed001` and `testspeed004` may have changed Step 4).
2. Add as the first bullet of Step 4 a documentation-only case: when every file the cycle changed (Step 3d's file list plus the files Step 5 edits) lies under `docs/`, `issues/`, `plans/`, or `implementations/`, and no file under `scripts/`, `tests/`, `tools/`, `config/`, or any other path changed, no test run applies; the 0-collected rule, the targeted run, the once-per-cycle full-suite run, and the coverage gate (recorded `N/A`) are skipped; instead run, for each file Step 3d changed, the checkers `routing.md` Tools "When to run which tool" requires for that file (the same list Step 6 applies) and record `N/A: documentation-only change; replaced by {checkers run}` in the Execution Status Notes of procedure row 3; a cycle whose changed files include any other path follows the bullets below unchanged.
3. In Row mapping, extend row 2's "Completed when" with "or the documentation-only case of Step 4 applies (Notes as there)" and row 3's with "Step 3e passes and Step 4's full-suite run passes, or, in the documentation-only case, the replacement checkers pass".
4. In the Final Report's Execution Status descriptions, change the fourth step to "Test the feature and pass required tests/coverage (or the documentation-only replacement checkers)".
5. Run the two skill checkers.

### Method
Edit the three places in place. Keep the existing exceptions list for "exactly once per cycle" untouched and describe the new case as scoped to the bullet it introduces.

### Details
- Do not copy the checker list from `routing.md`; name the table only.
- Mention in one clause that Step 6 still covers the files Step 5 edits, so a checker is not run twice for the same file.
- Do not change Step 3e or the batch-mode and release-unit text.

## Compatibility considerations
Cycles that change any path outside the four directories keep Step 4 exactly as it is; documentation-only cycles gain an explicit rule in place of an executor's judgment.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`.
- `uv run python tools/run_validation_gates.py`.
- Read-only dry application to the 14 archived procedures `implementations/done/20261112-123928_*`: each changes one `docs/` file and classifies as documentation-only; the replacement checkers cover the documentation checkers that were run; record the result in the commit message.

## Completion criteria
- Step 4 has the documentation-only case with the path definition and the replacement, naming `routing.md` by reference (`AC-001`).
- The 0-collected and full-suite rules are scoped and the Notes wording is stated (`AC-002`).
- Row 3 and the Final Report agree; both skill checkers pass (`AC-003`).
- The dry application of the 14 procedures is recorded (`AC-005`).

## Out of Scope
- Full-suite and coverage rules for code cycles; `routing.md` and the checkers; adding or removing tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the skill checkers named in Validation plan (`routing.md` Tools "When to run which tool") | Pending | — | — |  |

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
- **Requirement ID**: REQ-001 (documentation-only case), REQ-002 (scope the rules), REQ-003 (Row 3 and Final Report), REQ-005 (dry application)
- **Source issue**: issues/20261112-184029_testspeed006_docs-only-step4-exemption.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-094441_testspeed006_docs-only-step4-exemption.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-102727
- **Related target files**: `skills/code-implementation/workflow.md`
