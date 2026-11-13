## Goal
- Keep the skill summary consistent with the Step 4 documentation-only case by a single reference (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the Core Execution Rules bullet that repeats the full-suite rule and row 4 of the phase overview.
- Not in scope: restating the case or the path definition.

## Assumptions
- Row 4 reads "Determine targeted test scope, run it, then run the full suite once (retry on failure within Attempt Limit)." and the Core Execution Rules bullet reads "Run the repository-defined full test suite once per cycle after targeted tests pass; a failure may be fixed and re-run within Attempt Limit (3 attempts) (`workflow.md` Step 4)." Falsifier: the text changed; locate it with `rg -n "full test suite once per cycle|Test the feature"`.
- Implement this after the `workflow.md` procedure so the referenced case exists (filename order does so).
- A one-way reference from `SKILL.md` to `workflow.md` creates no heading-level cycle (`workflow.md` does not reference `SKILL.md` Step 4).

## Design decisions
- One reference per place: "except the documentation-only case defined in `workflow.md` Step 4".

## Alternatives considered
N/A: restating the rule in the summary would duplicate it.

## Implementation
### Target file
`skills/code-implementation/SKILL.md`

### Procedure
1. In phase-overview row 4 append "; a documentation-only cycle follows `workflow.md` Step 4 instead".
2. In the Core Execution Rules bullet append "; the documentation-only case is defined in `workflow.md` Step 4".
3. Run the two skill checkers.

### Method
Edit the two sentences in place, keeping the table row on one line.

### Details
- Do not restate the path definition or the replacement.
- Read both files after the edit and confirm they do not contradict each other.

## Compatibility considerations
N/A: skill text only.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`.
- `uv run python tools/run_validation_gates.py`.

## Completion criteria
- Row 4 and the Core Execution Rules bullet each refer to `workflow.md` Step 4 once, and the two files do not contradict each other (`AC-004`).
- Both skill checkers pass.

## Out of Scope
- The rule text and path definition (sibling procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-135413 | 20261113-140155 | Changed skills/code-implementation/SKILL.md: row 4 of the phase overview and the Core Execution Rules full-suite bullet each gained one reference to the documentation-only case defined in workflow.md Step 4. The path definition and the replacement are not restated here. |
| 2 | Run the skill checkers named in Validation plan (`routing.md` Tools "When to run which tool") | Completed | 20261113-140155 | 20261113-140155 | check_skills_references and check_skills_heading_cycles: No issues found; run_validation_gates exit 0 with no Fail or Blocked; the two files read consistently (the rule lives in workflow.md Step 4 only). Full suite serial 12151 passed, 3 failed: the known mdq cases (unrelated, Plan testspeed004); diff-cover N/A: no source file changed. |

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
- **Requirement ID**: REQ-004 (consistent reference from the skill summary)
- **Source issue**: issues/20261112-184029_testspeed006_docs-only-step4-exemption.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-094441_testspeed006_docs-only-step4-exemption.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-102727
- **Related target files**: `skills/code-implementation/SKILL.md`
