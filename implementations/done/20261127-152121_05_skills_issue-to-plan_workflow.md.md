## Goal
- Extend the Step 3 fallout trigger sentence of `skills/issue-to-plan/workflow.md` so it covers a Plan that adds text to an instruction file, within the 42533 B ceiling (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs after seq 04. Ceiling 42533 B in `tools/check_skill_size_baseline.txt`.

## Assumptions
- Verified in Step 3a: the file is 42111 B (422 B of headroom). Step 3 holds the bullet "- **Predictable fallout check** (any Plan that adds code to a file, changes a list or inventory, or adds or removes a tool): load `skills/issue-to-plan/workflow-edge.md` and follow its \"Step 3: predictable fallout check\" section."; the growth planned here is about 45 B.

## Design decisions
- Only the parenthesized trigger changes; the pointer wording and the section name stay, so the edge heading reference still resolves.

## Alternatives considered
N/A: the Plan fixes the wording and the places.

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Measure `wc -c` (expect 42111).
2. Replace "changes a list or inventory, or adds or removes a tool)" with "changes a list or inventory, adds or removes a tool, or adds text to a covered instruction file)" in that bullet (the phrase occurs once in this file: check with `rg -c`).
3. Measure again: at most 42533 B.

### Method
- Exact-string edits; check each anchor occurs once with `rg -c` before editing, and measure `wc -c` before and after.

### Details
- Plain ASCII punctuation as in the neighboring text.

## Compatibility considerations
N/A: procedure text only; `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` must still pass.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py`, `uv run python tools/check_skills_references.py`, and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- `skills/issue-to-plan/workflow.md` is at most 42533 B; `git diff` shows only the trigger phrase changed.

## Completion criteria
- The trigger covers a text-only Plan; the file is within its ceiling.

## Out of Scope
- Any other text of this file and the other target files of the Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure, edit the trigger phrase, and measure again | Completed | 20261127-152546 | 20261127-152555 | Changed: skills/issue-to-plan/workflow.md 42111 -> 42152 B (ceiling 42533; headroom 381 B by the new --headroom); only the trigger phrase changed |
| 2 | Run the skill size, reference, and heading-cycle checks | Completed | 20261127-152555 | 20261127-152555 | skill checks pass |

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
- **Requirement ID**: `REQ-003`, `REQ-004` (trigger repeated in Step 3, size ceiling)
- **Source issue**: issues/20261127-120059_flowopt001_skill-size-fallout-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-151623_flowopt001_skill-size-fallout-check.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152121
- **Related target files**: `skills/issue-to-plan/workflow.md`