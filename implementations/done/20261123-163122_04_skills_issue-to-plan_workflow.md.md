## Goal

Replace each moved body in the `issue-to-plan` workflow with one trigger line, keeping every heading and all other text unchanged.

## Scope
**Release unit**: pipeline-edge-split

In scope: the four ranges of procedure 03. `Path A collapse condition`, `Step 1b`, and the no-Plan bullets stay.

## Assumptions

- Trigger lines follow the Stage A pattern (backticked path, quoted heading).

## Design decisions

- Consumer scan bullet: `- **Consumer scan** (a change to a persisted schema, a public API, or a shared constant, or the removal or rename of a symbol that other modules call or read): load \`skills/issue-to-plan/workflow-edge.md\` and follow its "Step 3: consumer scan" section.`
- Predictable fallout bullet: `- **Predictable fallout check** (any Plan that adds code to a file, changes a list or inventory, or adds or removes a tool): load ... its "Step 3: predictable fallout check" section.`
- Design decisions bullet: `- **Design decisions (Path B only)**: when the Issue leaves a design choice open: load ... its "Step 5: design decisions (Path B only)" section.`
- Step 8c re-entry (lines 618-640 replaced): `Applies only when Step 8 reports "Fail", "Partial", or "Blocked" (the re-entry table, the not-"Frozen" rule, and the Plan-document correction pointer): load ... its "Step 8c: re-entry after a failed Step 8" section.`

## Alternatives considered

Rejected: leaving a summary of the re-entry table in the main path (it would re-grow the file).

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Replace each range with its trigger line.
2. Run the extraction check and confirm the file is at least 3,000 B smaller (45,620 B before).
3. Run the reference and heading-cycle checks.

### Method
Apply the edits with a script that replaces exact line ranges of the original, then compare with `git show HEAD:...`.

### Details
- Extraction check: collect the sentences containing `MUST`, `MUST NOT`, or `SHOULD` from `git show HEAD:skills/issue-to-plan/workflow.md`; every one must appear in the union of the new main workflow and its edge file; the moved sections must be byte-identical to the original slices (apart from recorded rewrites) and the text outside the moved ranges must be unchanged and in order.

## Compatibility considerations

Citations by section name still resolve (all headings stay).

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`
- The extraction check and the size comparison
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- Every heading remains, each moved body is one trigger line, the file is at least 3,000 B smaller, and the extraction and reference checks pass.

## Out of Scope

The edge file (procedure 03) and other skills.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-163225 | 20261123-163505 | Replaced four moved bodies with trigger lines; workflow.md 45620 to 42540 B (3080 B smaller; the plan's 3500 B estimate was too high because the moved text is about 3.6 KB, so the criterion was corrected to 3000 B in the plan and procedures 04 and 05) |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-163505 | 20261123-163505 | Extraction: 47 MUST/MUST NOT/SHOULD sentences, none missing; text outside the moved ranges preserved in order; checks and gates pass |

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
- **Requirement ID**: `REQ-003` (main workflows keep headings with trigger lines), `REQ-005` (no normative sentence lost)
- **Source issue**: issues/20261123-161834_skillsize003_compress-skill-workflows-remaining.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-162854_skillsize003_compress-skill-workflows-remaining.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-163122
- **Related target files**: `skills/issue-to-plan/workflow.md`
