## Goal

Add one Step 8a row-order check bullet to `skills/issue-to-plan/workflow.md` so Step 8
rejects an out-of-order `Implementation Target Files` table before it can be marked
`Frozen` (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

- **In-Scope**: one text-only check bullet in the existing `### Step 8a` validation list.
- Text-only edit: no new heading, sub-step, tool, or test.

## Assumptions

- The 381 B headroom (`skills/issue-to-plan/workflow.md` 42152 B, ceiling 42533 B in
  `tools/check_skill_size_baseline.txt`, measured 2026-11-28) fits one short bullet
  (~200-250 B). If the measured growth exceeds it, move the explanatory detail into
  `skills/issue-to-plan/workflow-edge.md` (Plan Phase 2 branch) instead of raising the
  baseline.
- `### Step 8a` ("Verify information completeness and traceability") is the check list
  that runs before the Step 8b freeze; the Plan names this placement.

## Design decisions

- Insert the check in Step 8a so it gates the freeze before Step 8b marks the section
  `Frozen`, matching the Plan's AC-2 ("rejects out-of-order `Frozen` tables").
- Wording mirrors the rule text added to `templates/plan.md` (companion procedure seq 01)
  and the `seq` derivation in `skills/plan-to-implementation-procedure/workflow.md`.

## Alternatives considered

N/A: the Plan prescribes one bullet in Step 8a; a mechanical checker is excluded by the
Plan (`Unknowns` UNK-01).

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Measure `wc -c skills/issue-to-plan/workflow.md` (before).
2. Insert one check sentence into the `### Step 8a` list.
3. Re-measure `wc -c skills/issue-to-plan/workflow.md` (after) and confirm it is at or
   under 42533 B; on overflow move explanatory text to `skills/issue-to-plan/workflow-edge.md`.

### Method
Insert one paragraph after the `Affected areas` verification paragraph in Step 8a, using
the same "Verify ..." sentence pattern as the neighboring checks. Do not touch headings
or other Steps.

### Details
- New Step 8a sentence: "Verify the `Implementation Target Files` rows are ordered by
  implementation sequence and `Implementation steps` cites them in 1-indexed row order;
  an out-of-order table MUST NOT be marked `Frozen`."
- Keep the sentence in one paragraph so the file grows well under the 381 B headroom.

## Compatibility considerations

- The bullet adds no heading, so `tools/check_workitem_structure.py` heading comparison
  and `tools/check_skills_heading_cycles.py` are unaffected.
- No referenced-file changes needed: `skills/issue-to-plan/workflow-edge.md` is only the
  overflow destination, not modified unless the Phase 2 branch triggers.

## Security considerations

N/A: instruction text only, no code or data.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `wc -c skills/issue-to-plan/workflow.md` after the edit is at or under 42533 B.
- `uv run python tools/check_skill_size.py --headroom skills/issue-to-plan/workflow.md`
  exits 0.
- `uv run python tools/check_skills_references.py` reports 0 missing references.
- `uv run python tools/check_skills_heading_cycles.py` passes.

## Completion criteria

- Step 8a contains a row-order check bullet that rejects an out-of-order table before
  `Frozen`; the file is at or under 42533 B; all Validation plan commands pass.

## Out of Scope

- A mechanical row-order checker tool or test (Plan `Out-of-Scope`, UNK-01).
- Raising the ceiling in `tools/check_skill_size_baseline.txt`.
- Modifying `skills/issue-to-plan/workflow-edge.md` unless the size-overflow branch triggers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Step 8a row-order check bullet per Procedure/Method/Details | Pending | — | — | Size overflow fallback: move text to `workflow-edge.md` |
| 2 | Run the documentation checkers (`check_skill_size.py`, `check_skills_references.py`, `check_skills_heading_cycles.py`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: issues/20261127-120100_flowopt002_plan-row-order-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-155958_flowopt002_plan-row-order-check.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-161650
- **Related target files**: `skills/issue-to-plan/workflow.md`
