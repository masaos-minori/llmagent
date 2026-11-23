## Goal

Create the edge-case file of `plan-to-implementation-procedure` holding the conditional sections of its workflow verbatim.

## Scope
**Release unit**: pipeline-edge-split

In scope: the new file only. Content is copied unchanged from `skills/plan-to-implementation-procedure/workflow.md` at the current commit: `### Non-conforming Plan structure` (lines 161-183, heading included), the reverted-Plan timestamp-marker paragraph of Step 3b (266-272), the already-existing-path sub-bullet of Step 3c (356-365), the additional-target-file discovery bullet (372-391), the `Plan Gap` bullet (392-398), and the gated-Plan marker bullet (409-414).

## Assumptions

- Verified in this cycle: the first and last line of each range match the plan's description and the lines around each range are blank or the next bullet.
- Moved text that names a main-workflow step by path (if any) is rewritten as `Step N of the main workflow` so the edge file adds no heading-cycle edge back to `workflow.md`; each rewrite is recorded in Notes.

## Design decisions

- Layout: a short header paragraph (what the file is, loaded only when a trigger in `workflow.md` holds), then `### Non-conforming Plan structure` (original heading, body unchanged), `### Step 3b: reverted Plan timestamp marker`, `### Step 3c: existing output path`, `### Step 3c: additional target file discovery`, `### Step 3c: Plan Gap`, `### Step 3c: gated Plan marker`; each bullet keeps its text unchanged and loses only its leading indentation if the new heading makes it a top-level item (record that).

## Alternatives considered

Rejected: one shared edge file for both skills (each skill is loaded separately).

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow-edge.md` (new)

### Procedure
1. Slice the original by the line ranges above and write the sections into the new file in the layout above.
2. Search the moved text for a backticked path plus section name that points back at `workflow.md` and rewrite only such references.
3. Run the extraction check and the reference checkers.

### Method
Copy with a script that slices the original by line number; compare each section against the original afterwards.

### Details
- Extraction check: collect the sentences containing `MUST`, `MUST NOT`, or `SHOULD` from `git show HEAD:skills/plan-to-implementation-procedure/workflow.md`; every one must appear in the union of the new main workflow and its edge file; the moved sections must be byte-identical to the original slices (apart from recorded rewrites) and the text outside the moved ranges must be unchanged and in order.
- Keep the file under 16,384 B (about 5.6 KB).

## Compatibility considerations

New file; `workflow.md` points to it from procedure 02.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`
- Moved sections byte-identical to the original slices

## Completion criteria

- The file holds the six moved groups verbatim and the reference and heading-cycle checks pass.

## Out of Scope

Editing `workflow.md` (procedure 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-163225 | 20261123-163505 | Created workflow-edge.md (6089 B) by slicing the original lines; moved bullets dedented where needed |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-163505 | 20261123-163505 | check_skills_references and check_skills_heading_cycles pass; moved sections verbatim |

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
- **Requirement ID**: `REQ-001` (plan-to-implementation-procedure edge file), `REQ-005` (no normative sentence lost)
- **Source issue**: issues/20261123-161834_skillsize003_compress-skill-workflows-remaining.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-162854_skillsize003_compress-skill-workflows-remaining.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-163122
- **Related target files**: `skills/plan-to-implementation-procedure/workflow-edge.md`
