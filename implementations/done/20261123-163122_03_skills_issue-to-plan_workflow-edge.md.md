## Goal

Create the edge-case file of `issue-to-plan` holding the conditional sections of its workflow verbatim.

## Scope
**Release unit**: pipeline-edge-split

In scope: the new file only. Content is copied unchanged from `skills/issue-to-plan/workflow.md` at the current commit: the `Consumer scan` bullet of Step 3 (lines 235-242), the `Predictable fallout check` bullet (244-258), the `Design decisions (Path B only)` bullet of Step 5 (325-331), and the failure re-entry text of Step 8c (618-640).

## Assumptions

- Verified in this cycle: the first and last line of each range match the plan's description; the re-entry range starts at `If Step 8 reports "Fail" or "Partial"` and ends at the Plan-document correction pointer, and the cycle-bound paragraph before it (614-616) and the cross-check paragraph after it (642) stay in the main workflow.
- Moved text that names a main-workflow step by path is rewritten as `Step N of the main workflow`; each rewrite is recorded in Notes.

## Design decisions

- Layout: a short header paragraph, then `### Step 3: consumer scan`, `### Step 3: predictable fallout check`, `### Step 5: design decisions (Path B only)`, and `### Step 8c: re-entry after a failed Step 8` (the table and both following paragraphs unchanged); the bullets keep their text unchanged.

## Alternatives considered

Rejected: moving `Path A collapse condition` (`templates/plan.md` cites it by step).

## Implementation
### Target file
`skills/issue-to-plan/workflow-edge.md` (new)

### Procedure
1. Slice the original by the ranges above and write the sections in the layout above.
2. Search the moved text for a backticked path plus section name that points back at `workflow.md` and rewrite only such references.
3. Run the extraction check and the reference checkers.

### Method
Copy with a script that slices the original by line number; compare each section against the original afterwards.

### Details
- Extraction check: collect the sentences containing `MUST`, `MUST NOT`, or `SHOULD` from `git show HEAD:skills/issue-to-plan/workflow.md`; every one must appear in the union of the new main workflow and its edge file; the moved sections must be byte-identical to the original slices (apart from recorded rewrites) and the text outside the moved ranges must be unchanged and in order.
- Keep the file under 16,384 B (about 3.8 KB).

## Compatibility considerations

New file; `workflow.md` points to it from procedure 04.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`
- Moved sections byte-identical to the original slices

## Completion criteria

- The file holds the four moved groups verbatim and the reference and heading-cycle checks pass.

## Out of Scope

Editing `workflow.md` (procedure 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-163225 | 20261123-163505 | Created workflow-edge.md (4512 B) by slicing the original lines |
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
- **Requirement ID**: `REQ-002` (issue-to-plan edge file), `REQ-005` (no normative sentence lost)
- **Source issue**: issues/20261123-161834_skillsize003_compress-skill-workflows-remaining.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-162854_skillsize003_compress-skill-workflows-remaining.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-163122
- **Related target files**: `skills/issue-to-plan/workflow-edge.md`
