## Goal
- Reference `tools/fill_affected_areas.py` in the Step 5 `Affected areas` bullet of `skills/issue-to-plan/workflow.md` with a net growth of at most 7 B (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Verified in Step 3a: the file is 42533 B and `tools/check_skill_size_baseline.txt` records the ceiling `skills/issue-to-plan/workflow.md	42540`, so 7 B of headroom exists; a larger file fails as a regression. The bullet is at lines 382-387 (`Path B: take ... from the historical analysis in \`workflow-path-b.md\`,`).
- Sibling Issues wfeff006 to wfeff009 may also edit this file; re-measure `wc -c` immediately before editing.

## Design decisions
- Replace, never append: the 48-byte phrase "the historical analysis in `workflow-path-b.md`," becomes the 54-byte phrase "`tools/fill_affected_areas.py` (`workflow-path-b.md`)," (net +6 B, within the 7 B headroom).
- Do not edit `tools/check_skill_size_baseline.txt` (the ceiling is not raised).

## Alternatives considered
- Add a new sentence: rejected, it exceeds the headroom. Raising the baseline: rejected, the baseline is a ceiling that must shrink.

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Run `wc -c skills/issue-to-plan/workflow.md` and confirm it is at most 42534 B before the edit (a larger value means a sibling consumed the headroom: stop and report).
2. In the Step 5 `Affected areas` bullet, replace "from the historical analysis in `workflow-path-b.md`," with "from `tools/fill_affected_areas.py` (`workflow-path-b.md`),".
3. Run `wc -c` again and confirm the result is at most 42540 B.

### Method
- Use an exact-string edit on that one phrase; it occurs once (checked with `rg -c` before the edit).

### Details
- The resulting sentence reads: "Path B: take `Blast Radius` from the dependency graphing and `Churn (30d)` and `Bus Factor` from `tools/fill_affected_areas.py` (`workflow-path-b.md`), and mark a column `N/A` when the tool that would fill it is unavailable."

## Compatibility considerations
- N/A: procedure text only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py` exits 0 with the file at or below 42540 B.
- `uv run python tools/check_workitem_structure.py` is not applicable (not a work item); run the changed-file gates of `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The bullet names the tool, the file is at most 42540 B, and the baseline file is unchanged.

## Out of Scope
- `skills/issue-to-plan/workflow-path-b.md` (seq 04) and any other text in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure, then replace the phrase per Procedure | Completed | 20261127-091145 | 20261127-092340 | Changed: skills/issue-to-plan/workflow.md 42533 -> 42539 B (ceiling 42540); baseline unchanged |
| 2 | Run `uv run python tools/check_skill_size.py` and the changed-file gates | Completed | 20261127-092340 | 20261127-092340 | check_skill_size.py and changed-file gates pass |

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
- **Requirement ID**: `REQ-006` (skill reference within the size ceiling)
- **Source issue**: issues/20261126-151440_wfeff005_affected-areas-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-085326_wfeff005_affected-areas-tool.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-090100
- **Related target files**: `skills/issue-to-plan/workflow.md`