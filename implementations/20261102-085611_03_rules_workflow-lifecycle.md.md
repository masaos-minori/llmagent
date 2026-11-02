## Goal
- Add proposed text to `rules/workflow-lifecycle.md` defining the two approval classes for a post-freeze Plan amendment and the report owed for the first class, marked pending the owner's decision (`REQ-004`).

## Scope
- In scope: one new subsection. Out of scope: any change to the Plan Freeze validation text (initial validation, revalidation, additional-discovery paragraph), and the skills that apply the classes (seq 04 and 05).

## Assumptions
- Step 3a verification: the "Implementation Target Files Validation (Plan Freeze)" section holds `### Initial validation (issue-to-plan, Step 8)` and `### Revalidation (plan-to-implementation-procedure, Step 2)`; the Revalidation paragraph on additional target file discovery requires amending the Plan and re-freezing but states no approval classes (verified by Read, 2026-11-02). No `tools/amend_plan.py` mention exists yet.
- Overlap (Step 2): no other Frozen Plan targets this file (Plan A8; `check_plan_target_overlaps.py` lists none).
- `tools/amend_plan.py` is created by the seq 01 procedure; a reference to it here may be reported by `tools/stale_detector.py` as a name an earlier-`seq` row creates (acceptable).
- The skills in seq 04 and 05 will cite this subsection by heading, so the heading text is fixed here: `Plan Amendment Approval Classes (proposed)`. This rule file MUST NOT cite skill sections back (avoids a heading-level cycle, `tools/check_skills_heading_cycles.py`).

## Design decisions
- Add `### Plan Amendment Approval Classes (proposed)` after the Revalidation subsection and before `## Requirement Reference Format`, opening with a status line: proposed, pending the owner's decision (Plan UNK-01), no effect until accepted.
- Content: fallout (a file added only to keep existing behavior, tests, inventories, or checkers working) may be amended by the executor through `tools/amend_plan.py` and owes a report afterward naming the file, the class, and the reason; a change to scope or behavior, a new requirement, or a removed row needs approval before it is made; the caller states the class and the tool records it; the Plan Freeze validation above is unchanged.

## Alternatives considered
- Rewriting the existing additional-discovery paragraph: rejected, `REQ-004` and AC-5 require that text unchanged.

## Implementation
### Target file
`rules/workflow-lifecycle.md`

### Procedure
1. Re-read the section at execution time and locate the end of the Revalidation subsection (the additional target file discovery paragraph) by its text.
2. Insert the new subsection after it with Edit; make no other change in the file.

### Method
- Keep it to one short status line and two bullet groups, in the file's `MUST` style, with no table. Name the report fields explicitly: file path, class, reason.

### Details
- State that when the policy is not accepted, every amendment follows the second class (approval first), so the skills have a safe default.

## Compatibility considerations
- Additive text under a marked-proposed heading; existing validation rules and readers are unaffected.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`: no findings.
- Diff review: the Plan Freeze text above the new subsection is byte-identical (AC-5).

## Completion criteria
- The two classes and the report owed for the first are stated, marked pending the owner's decision, and the Plan Freeze validation text is unchanged (AC-5); both checkers pass.

## Out of Scope
- Changing freeze rules, the two skills, the tool, and any decision on UNK-01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `### Plan Amendment Approval Classes (proposed)` to `rules/workflow-lifecycle.md` | Pending | — | — |  |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py`, and confirm the Freeze text is unchanged by diff | Pending | — | — |  |

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
- **Requirement ID**: `REQ-004` (approval classes as proposed text)
- **Source issue**: issues/20261030-191737_flowimp011_plan-amend-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081027_flowimp011_plan-amend-tool.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085611
- **Related target files**: rules/workflow-lifecycle.md
