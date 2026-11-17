## Goal

Describe the batch path in Step 10.2 of `skills/issue-creator/workflow.md`: filing several
issues from one Markdown spec through `tools/generate_issue_batch.py` in a single call,
without changing the single-issue path.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 3 of the plan's frozen `Implementation Target Files` table:
`skills/issue-creator/workflow.md` (REQ-007 filing documentation, AC-7).

## Assumptions
- `tools/generate_issue_batch.py` is created by the seq 01 document; this row documents it,
  so the tool row must land before or with this edit for the description to be true.
- Overlap with the wftool001 Plan on this file is compatible: that Plan edits the Step 10.4
  snippet, this edit is the Step 10.2 batch text (plan Assumptions).

## Design decisions
- Add a `Batch path:` note at the end of Step 10.2 (after the Manual procedure list, before
  Step 10.2a); the Default, Tool path notes, and Manual procedure blocks stay verbatim.

## Alternatives considered
N/A: the placement follows the plan's REQ-007 wording ("Step 10.2 describes the batch path
without changing the single-issue path").

## Implementation
### Target file
`skills/issue-creator/workflow.md`
### Procedure
Append a short `Batch path:` paragraph to Step 10.2 stating: one call per batch through
`uv run python tools/generate_issue_batch.py SPEC.md`; the tool validates the whole spec,
allocates timestamps, refuses on any collision in `issues/` or `issues/done/` before the
first write, honors `--dry-run`, and runs the structure and leftover checker over all
created paths; a `{{issue:<id>}}` token in the spec resolves to the allocated path.
### Method
State that Steps 10.2a collision handling and 10.4 verification apply to each created file;
name the checker exit codes (`0`/`1`/`2`) as the tool's contract.
### Details
Do not restate the spec grammar in full; point to the `tools/TOOL_DESCRIPTIONS.md` row
(seq 05) for the format contract.

## Compatibility considerations
N/A: documentation-only; existing single-issue text is untouched.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` — no finding.
- `uv run python tools/check_skills_heading_cycles.py` — no finding.

## Completion criteria
Step 10.2 names the batch tool and its pre-write refusal behavior, the single-issue path
text is unchanged, and both skills checkers pass (AC-7).

## Out of Scope
Any other step of `skills/issue-creator/workflow.md`; the SKILL.md note (seq 04); the tool
itself (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in Validation plan | Pending | — | — | `check_skills_references.py`, `check_skills_heading_cycles.py` |

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
- **Requirement ID**: `REQ-007` (batch-path documentation)
- **Source issue**: issues/20261117-123334_wftool005_workitem-batch-generate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125502_wftool005_workitem-batch-generate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-200906
- **Related target files**: `skills/issue-creator/workflow.md`
