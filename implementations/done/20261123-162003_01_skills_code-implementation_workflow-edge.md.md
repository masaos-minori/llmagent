## Goal

Create `workflow-edge.md`, the edge-case file of `code-implementation`, holding the conditional sections of the workflow verbatim under their original headings.

## Scope
**Release unit**: code-implementation-edge-split

In scope: the new file only. Content is copied unchanged from `skills/code-implementation/workflow.md` at the current commit: `### Batch mode (plan batch)` (lines 98-141), `### Batch mode (release unit)` (lines 142-171), the `All-steps-completed check`, `Partial-completion resume`, and `Superseded procedure` bullets of Step 1 (lines 263-295), the `Manual path` bullet of the Plan Execution Status update (lines 672-702), and `## Rollback on Failure` (lines 703-725).

## Assumptions

- Verified: the line ranges above match the current file (the first line of each range was read in the planning cycle); the `Gated check` bullet (line 296) and `Dependency order` stay in the main workflow.
- Verified: `tools/check_skills_heading_cycles.py` links a backticked `.md` path followed by a resolvable section name; references inside the moved text that name a main-workflow step by path (if any) are rewritten as `Step N of the main workflow` so the edge file adds no edge back to `workflow.md`.
- The extraction check (below) is the proof of verbatim content; it runs against `git show HEAD:skills/code-implementation/workflow.md`.

## Design decisions

- File layout: a short header paragraph (what the file is and that every section is loaded only when its trigger in `workflow.md` holds), then the moved sections in this order: `### Batch mode (plan batch)`, `### Batch mode (release unit)`, `### Step 1 edge cases` (the three bullets, each unchanged), `### Plan Execution Status update: manual path` (the bullet, unchanged), `## Rollback on Failure`.
- Original headings and heading levels are kept for the three sections that have one; the two new headings group bullets that had no heading.

## Alternatives considered

Rejected: a pointer-only edge file (the moved text must stand alone); rejected: splitting by step (steps are the main path).

## Implementation
### Target file
`skills/code-implementation/workflow-edge.md` (new)

### Procedure
1. Read lines 98-171, 263-295, 672-702, and 703-725 of `skills/code-implementation/workflow.md` and write them into the new file in the layout above, unchanged.
2. Search the moved text for a backticked path followed by a step or section name that points back at `workflow.md`; rewrite only such a reference as `Step N of the main workflow` (record each rewrite in Notes).
3. Run the extraction check and the reference checkers.

### Method
Copy with a script (slice the original by line number) rather than retyping; then diff each moved section against the original and expect no difference.

### Details
- Extraction check: collect the sentences containing `MUST`, `MUST NOT`, or `SHOULD` from `git show HEAD:skills/code-implementation/workflow.md`; every one must appear in the union of the new main workflow (procedure 02) and this file.
- Keep the file under 16,384 B (it is about 11 KB).

## Compatibility considerations

New file; the main workflow points to it from procedure 02.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`
- Moved sections byte-identical to the original (a short script comparing slices)

## Completion criteria

- The file holds the five moved groups verbatim and the reference and heading-cycle checks pass.

## Out of Scope

Editing `workflow.md` (procedure 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-162340 | 20261123-162624 | Created workflow-edge.md (12258 B) by slicing the original lines; one recorded rewrite: '(this file)' to '(workflow.md)' in the release-unit batch text |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-162624 | 20261123-162624 | check_skills_references and check_skills_heading_cycles pass; the five moved groups are byte-identical to the original |

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
- **Requirement ID**: `REQ-001` (edge file holds the moved sections verbatim), `REQ-005` (no normative sentence lost)
- **Source issue**: issues/20261123-155940_skillsize002_compress-skill-workflows-structure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-161734_skillsize002_compress-skill-workflows-structure.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-162003
- **Related target files**: `skills/code-implementation/workflow-edge.md`
