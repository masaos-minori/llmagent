## Goal

Replace each moved body in the main workflow with one trigger line, keeping every heading and all other text unchanged.

## Scope
**Release unit**: code-implementation-edge-split

In scope: the bodies of `### Batch mode (plan batch)`, `### Batch mode (release unit)`, `## Rollback on Failure`, the three Step 1 bullets, and the `Manual path` bullet. Nothing else changes.

## Assumptions

- Verified: every moved section has a heading or a bullet label that can stay; the `Gated check` bullet of Step 1 stays verbatim because the check runs every cycle.
- The trigger lines name the edge file in backticks and quote the heading in plain quotes, so `check_skills_heading_cycles.py` resolves no section and adds no edge.

## Design decisions

- Plan batch: `Applies only when one run covers two or more procedures with the same "Source plan" that are not members of a declared release unit: load \`skills/code-implementation/workflow-edge.md\` and follow its "Batch mode (plan batch)" section; a run holding one procedure of a Plan keeps the per-cycle gate and per-file archival.`
- Release unit: `Applies only when the procedures of one "Source plan" carry the same unit name on the "Release unit" line of "## Scope": load ... its "Batch mode (release unit)" section.`
- Step 1: one bullet `**Edge cases of Step 1** (every row "Completed", some rows "Completed", or the user decided not to implement the procedure): load ... its "Step 1 edge cases" section.`
- Manual path: one bullet `**Manual path** (the tool is unavailable or refused, or the procedure was already moved with "close-implementation"): load ... its "Plan Execution Status update: manual path" section.`
- Rollback on Failure: keep the heading; body `Applies only when implementation breaks existing functionality, a validator or test reaches the Attempt Limit, or the procedure's "Rollback considerations" apply: load ... its "Rollback on Failure" section.`

## Alternatives considered

Rejected: deleting the headings (citations by section name would break); rejected: leaving a summary of the moved rules in the main path (it would re-grow the file).

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Replace each moved body with its trigger line (above).
2. Run the extraction check: every `MUST`, `MUST NOT`, and `SHOULD` sentence of the original appears in this file or `workflow-edge.md`; text outside the moved sections is byte-identical to the original.
3. Confirm the file is at least 8,000 B smaller (52,593 B before).

### Method
Apply the edits with a script that replaces exact line ranges of the original, then re-run the comparison against `git show HEAD:...`.

### Details
- Every other heading, including `Multi-file processing`, `Dependency order`, and `Question policy`, stays unchanged.

## Compatibility considerations

Citations by section name still resolve; the two outside citations are updated in procedures 03 and 04.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`
- The extraction check and the size comparison above
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- Every heading remains, each moved body is one trigger line, the file is at least 8,000 B smaller, and the extraction and reference checks pass.

## Out of Scope

The edge file (procedure 01) and other skills.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (main workflow keeps headings with trigger lines), `REQ-005` (no normative sentence lost)
- **Source issue**: issues/20261123-155940_skillsize002_compress-skill-workflows-structure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-161734_skillsize002_compress-skill-workflows-structure.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-162003
- **Related target files**: `skills/code-implementation/workflow.md`
