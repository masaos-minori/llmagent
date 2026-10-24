## Goal
- Add a one-line pointer in the `skills/issue-creator/SKILL.md` Phase overview naming the conditional batch pre-investigation pass between Phase 2 and Phase 3 and the two-tier sibling check, without renumbering (`REQ-005`: Phase overview pointer).

## Scope
- The `## Phase overview` list (lines 72-87 at time of writing): extend the Phase 2 and Phase 4 items, or add one line under the list; numbering 1 to 10 unchanged.

## Assumptions
- Confirmed 2026-10-24: the overview is a numbered list of phases 1 to 10 with no mention of a batch pass.
- Overlap: `plans/20261024-234023_align-scaffold-policy-with-practice.md` rewrites Phase overview item 10 only; this row touches the Phase 2 and Phase 4 items or the line below the list. Sequencing dependency, compatible; re-read and re-anchor immediately before editing.
- Row `01` (`skills/issue-creator/workflow.md`) is applied first so the referenced sections exist.

## Design decisions
- One short clause per touched item, pointing to `workflow.md` by file name: batch mode (two or more issues) runs a shared verification pass after Phase 2; Phase 4's sibling check reads full bodies only for candidates.

## Alternatives considered
N/A: wording-only edit.

## Implementation
### Target file
`skills/issue-creator/SKILL.md`

### Procedure
1. Append the batch-pass clause to item 2 (Task Grouping) and the two-tier clause to item 4 (Scope and Boundaries), each kept to one line.

### Method
- Edit in place with unique `old_string` values; do not touch item 10.

### Details
- Do not add a new numbered item.

## Compatibility considerations
N/A: wording only.

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0; numbering unchanged.

## Completion criteria
- The pointer exists, references resolve, and the phase numbering 1 to 10 is unchanged.

## Out of Scope
- Phase overview item 10 and all other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the batch-pass and two-tier clauses to items 2 and 4 | Pending | — | — | |
| 2 | Run both skills checkers | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (Phase overview pointer)
- **Source issue**: issues/20261024-212502_perf006_amortize-preinvestigation-in-batch-drafting.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-233702_amortize-preinvestigation-in-batch-drafting.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235959
- **Related target files**: `skills/issue-creator/SKILL.md`
