## Goal
- Add the Step 3c pointer and the Toolchain line for `tools/generate_repeated_procedures.py` to `skills/plan-to-implementation-procedure/workflow.md` within the 34876 B ceiling (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Precondition (sequencing dependency on the `tools/finalize_procedures.py` Plan, wfeff006): that Plan's seq 05 procedure must be implemented first. Measure `wc -c skills/plan-to-implementation-procedure/workflow.md`: it must be at most 34876 minus the added bytes (about 330). The file is 34853 B today (23 B headroom); if the measurement fails, stop and report `Blocked`, do not shorten other text.
- Verified in Step 3a: Step 3c has the bullet "Optionally scaffold the empty file first with `uv run python tools/generate_workitem.py --kind implementation-procedure ...`" (line 301) and the Toolchain list names `generate_workitem.py` for Step 3.

## Design decisions
- Two additions only: one sentence after the scaffold bullet and one Toolchain line; no other text changes, so the edit does not touch the lines the wfeff006 procedures change.

## Alternatives considered
- Put the text in `workflow-edge.md`: acceptable later if headroom is short, but the Plan names Step 3c in `workflow.md`.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
1. Measure `wc -c` and apply the precondition above.
2. After the scaffold bullet of Step 3c add a sub-bullet: "- For rows with an identical `Change Responsibility`, `uv run python tools/generate_repeated_procedures.py {plan_path} --rows {paths} --body-template {file}` writes one document per row from one body template and refuses differing rows; run `tools/stale_detector.py` on each document afterwards."
3. In the Toolchain list add: "- `tools/generate_repeated_procedures.py` (Step 3c, one body template for rows with an identical `Change Responsibility`)."
4. Measure again: at most 34876 B.

### Method
- Exact-string insertions next to the named bullets; no rewording.

### Details
- Keep the list indentation of the neighboring bullets.

## Compatibility considerations
- N/A: procedure text only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py`, `uv run python tools/check_skills_references.py`, `uv run python tools/check_skills_heading_cycles.py` exit 0; the file at or below 34876 B.

## Completion criteria
- Step 3c and Toolchain name the tool; the file is within the ceiling; no other text changed (`git diff` shows only the two insertions).

## Out of Scope
- The wfeff006 changes to this file, `tools/check_skill_size_baseline.txt`, other text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure, then add the Step 3c sub-bullet and the Toolchain line | Completed | 20261127-101744 | 20261127-101803 | Needs the wfeff006 seq 05 change first Changed: skills/plan-to-implementation-procedure/workflow.md 34323 -> 34756 B (ceiling 34876); two insertions only |
| 2 | Run the skill size, reference, and heading-cycle checks | Completed | 20261127-101803 | 20261127-101803 | check_skill_size, check_skills_references, check_skills_heading_cycles pass |

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
- **Requirement ID**: `REQ-005` (pointer within the size ceiling)
- **Source issue**: issues/20261126-151442_wfeff007_repeated-row-procedures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-095809_wfeff007_repeated-row-procedures.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-100500
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`