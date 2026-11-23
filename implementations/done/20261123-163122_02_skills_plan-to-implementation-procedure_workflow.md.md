## Goal

Replace each moved body in the `plan-to-implementation-procedure` workflow with one trigger line, keeping every heading and all other text unchanged.

## Scope
**Release unit**: pipeline-edge-split

In scope: the six ranges of procedure 01. Nothing else changes; the `Partially implemented` and evidence-gap bullets stay.

## Assumptions

- Trigger lines name the edge file in backticks and quote the heading in plain quotes, so `check_skills_heading_cycles.py` resolves no section (the Stage A pattern).

## Design decisions

- Non-conforming Plan structure (heading stays; body lines 162-183 replaced): `Applies only when the structure check reports "missing-section" findings: load \`skills/plan-to-implementation-procedure/workflow-edge.md\` and follow its "Non-conforming Plan structure" section.`
- Step 3b paragraph: `If "plans/{filename}.md" is reverted during an active Step 3 pass: load ... its "Step 3b: reverted Plan timestamp marker" section.`
- Step 3c existing-path sub-bullet: `- If the resulting path already exists (an interrupted cycle is being resumed): load ... its "Step 3c: existing output path" section.`
- Step 3c additional-target bullet: `- If investigation reveals that implementing this row requires modifying a file not listed in "Implementation Target Files" (an additional target file discovery): load ... its "Step 3c: additional target file discovery" section.`
- Step 3c Plan Gap bullet: `- If investigation instead reveals that this row's approach needs to change but no additional file is involved (a Plan Gap): load ... its "Step 3c: Plan Gap" section.`
- Step 3c gated bullet: `- When the user chose to proceed with a gated Plan in Step 2: load ... its "Step 3c: gated Plan marker" section.`

## Alternatives considered

Rejected: deleting the headings or bullet labels (citations by name would break).

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
1. Replace each range with its trigger line (bullets keep their indentation).
2. Run the extraction check and confirm the file is at least 4,000 B smaller (39,108 B before).
3. Run the reference and heading-cycle checks.

### Method
Apply the edits with a script that replaces exact line ranges of the original, then compare with `git show HEAD:...`.

### Details
- Extraction check: collect the sentences containing `MUST`, `MUST NOT`, or `SHOULD` from `git show HEAD:skills/plan-to-implementation-procedure/workflow.md`; every one must appear in the union of the new main workflow and its edge file; the moved sections must be byte-identical to the original slices (apart from recorded rewrites) and the text outside the moved ranges must be unchanged and in order.

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

- Every heading remains, each moved body is one trigger line, the file is at least 4,000 B smaller, and the extraction and reference checks pass.

## Out of Scope

The edge file (procedure 01) and other skills.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-163225 | 20261123-163505 | Replaced six moved bodies with trigger lines; workflow.md 39108 to 34876 B (4232 B smaller) |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-163505 | 20261123-163505 | Extraction: 33 MUST/MUST NOT/SHOULD sentences, none missing; text outside the moved ranges preserved in order; checks and gates pass. Full suite 13572 passed, 2 failed in tests/db/test_schema_validation_per_database.py (mcp_dedup stamp 2 vs user_version=1, caused by the concurrent mcpdl004 schema bump, unrelated) |

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
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
