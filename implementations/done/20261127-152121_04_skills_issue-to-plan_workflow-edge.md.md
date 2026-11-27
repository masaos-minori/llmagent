## Goal
- Add the Skill size item and extend the trigger of the fallout check in `skills/issue-to-plan/workflow-edge.md` (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs after the tool procedure (seq 01), because the item names `--headroom`.

## Assumptions
- Verified in Step 3a: "### Step 3: predictable fallout check" (lines 19-37) opens with "- **Predictable fallout check** (any Plan that adds code to a file, changes a list or\n  inventory, or adds or removes a tool): before Step 5, ..." and lists Module size, Pinned counts, Tool inventory, and Generated blocks; the file is 5833 B with no baseline entry (limit 16384 B).

## Design decisions
- Put the new item right after "Module size" because both compare a size with a gate.

## Alternatives considered
N/A: the Plan fixes the wording and the places.

## Implementation
### Target file
`skills/issue-to-plan/workflow-edge.md`

### Procedure
1. In the trigger, replace "changes a list or\n  inventory, or adds or removes a tool)" with "changes a list or\n  inventory, adds or removes a tool, or adds text to a covered instruction file)".
2. After the Module size bullet insert: "- Skill size: for a covered instruction file (`skills/`, `rules/`, `prompts/`, `templates/`, `routing.md`, `AGENTS.md`, `CLAUDE.md`) that gains text, run `uv run python tools/check_skill_size.py --headroom <file> [<file> ...]` and record size, ceiling, and headroom. When the planned growth exceeds the headroom, the Plan has a target row for the edge file that receives the text, or states the text the change replaces." (wrapped at the file's line width, with the bullet's continuation indent).

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
- The file stays below 16384 B; the new item sits inside the fallout section only.

## Completion criteria
- The trigger and the Skill size item are in place; the skill checks pass.

## Out of Scope
- Any other text of this file and the other target files of the Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the trigger and insert the item per Procedure | Completed | 20261127-152535 | 20261127-152546 | Changed: skills/issue-to-plan/workflow-edge.md 5833 -> 6315 B (trigger extended, Skill size item added after Module size) |
| 2 | Run the skill size, reference, and heading-cycle checks | Completed | 20261127-152546 | 20261127-152546 | skill size, references, heading cycles pass |

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
- **Requirement ID**: `REQ-003`, `REQ-004` (Skill size item and trigger)
- **Source issue**: issues/20261127-120059_flowopt001_skill-size-fallout-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-151623_flowopt001_skill-size-fallout-check.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152121
- **Related target files**: `skills/issue-to-plan/workflow-edge.md`