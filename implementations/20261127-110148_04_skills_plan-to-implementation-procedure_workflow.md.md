## Goal
- Replace the final-report body of `skills/plan-to-implementation-procedure/workflow.md` with the compact form, its deviation conditions, and a pointer (`REQ-002`, `REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs after seq 03. Ceiling 34876 B (file 34756 B).

## Assumptions
- Verified in Step 3a: `### Final report` is 926 B; its first sentence `Emit once per Plan, whether the cycle ended moved or \`Blocked\`.` stays; nothing else in the file refers to the report's bullets except the Step 4 text that names the report as the place for the Plan edits and unmapped steps (a deviation).

## Design decisions
- Rows `Already implemented` and `Partially implemented` count as deviations because the full form reports them.

## Alternatives considered
N/A: the Plan fixes the design (compact default in the workflow, full form verbatim in the edge file).

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
1. Measure `wc -c` (expect 34756).
2. In `### Final report` keep the heading and the first sentence, delete the moved region, and insert: "Use the compact form when the cycle had none of these deviations: a row `Already implemented` or `Partially implemented`, a non-blocking `Needs confirmation` caveat, a `Plan Gap`, an uncovered row, a Step 3a edit to the Plan, an unmapped Plan step, a Plan-level overlap, a gated procedure, or `Blocked`. Report three lines: the Plan path and outcome (`moved to plans/done/`); the generated documents in `seq` order as paths; and `Validation:` the coverage, structure, and stale results, with the next step (run `code-implementation` over the documents in `seq` order). Any deviation requires the full form: load `skills/plan-to-implementation-procedure/workflow-edge.md` and follow its "Final report: full form" section."
3. Measure again: at most 34876 B.

### Method
- Copy moved text exactly (whitespace included); edit with exact-string replacements and check each anchor occurs once with `rg -c` first.

### Details
- Plain ASCII punctuation as in the neighboring sections; a heading must be unique in its file.

## Compatibility considerations
N/A: procedure text only; `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` must still pass.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py`, `uv run python tools/check_skills_references.py`, and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- The file is at most 34876 B.

## Completion criteria
- The compact form and its conditions are stated; the full form is reachable; the file is within its ceiling.

## Out of Scope
- Any other section of this file, the persisted records the report summarizes, and the other three workflows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure and replace the body | Pending | — | — | |
| 2 | Run the skill checks | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-005`, `REQ-006` (compact default, size ceiling)
- **Source issue**: issues/20261126-151444_wfeff009_compact-final-reports.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104723_wfeff009_compact-final-reports.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-110148
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
