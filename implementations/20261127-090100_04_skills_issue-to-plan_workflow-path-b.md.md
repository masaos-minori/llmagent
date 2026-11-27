## Goal
- Reference `tools/fill_affected_areas.py` in the "Historical analysis" section of `skills/issue-to-plan/workflow-path-b.md` and state the bus factor rule in place of the unavailable `git-fame` sentence (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Verified in Step 3a: the churn command is at lines 62-64, the explanatory paragraph at 66-71, and the `git-fame` sentence ends the paragraph at lines 70-71; the file is 4149 B, far under the 16384 B skill size limit. `git-fame` is not installed on this host.
- The Toolchain table row for `git-fame` (line 18) stays: it names an optional tool and is not wrong.

## Design decisions
- Keep the existing churn command (it is the manual equivalent and the `REQ-007` comparison reference).
- Add one sentence after the paragraph; this skill edit revises the procedure itself, so it does not route through `python-documentation` (`routing.md` Documentation row exception).

## Alternatives considered
- N/A: single-location edit.

## Implementation
### Target file
`skills/issue-to-plan/workflow-path-b.md`

### Procedure
1. Replace the sentence "`git-fame` for bus-factor if installed (>70% single author = flag as high bus factor)." with: "For both columns of the `Affected areas` table run `uv run python tools/fill_affected_areas.py plans/{filename}.md`; it prints `Churn (30d)` and `Bus Factor` (High when one lowercased author name holds more than 70% of a file's commits; `git-fame` is not required) and leaves `Blast Radius` for you."

### Method
- Edit in place, keeping the paragraph's other sentences and the line wrapping style.

### Details
- Do not restate the tool's full rules; `tools/TOOL_DESCRIPTIONS.md` owns them.

## Compatibility considerations
- N/A: procedure text only; Path A Plans never load this file.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py` exits 0; `uv run python tools/check_skill_refs.py` or the skill-reference gate reported by `uv run python tools/run_validation_gates.py` passes for the changed file.

## Completion criteria
- The paragraph names the tool and the 70 percent rule; the size gate passes.

## Out of Scope
- The Toolchain table, other sections of the file, and `skills/issue-to-plan/workflow.md` (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `git-fame` sentence per Procedure | Pending | — | — | |
| 2 | Run `uv run python tools/check_skill_size.py` and the changed-file gates | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (skill reference)
- **Source issue**: issues/20261126-151440_wfeff005_affected-areas-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-085326_wfeff005_affected-areas-tool.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-090100
- **Related target files**: `skills/issue-to-plan/workflow-path-b.md`
