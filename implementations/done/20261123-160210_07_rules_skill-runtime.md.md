## Goal

Create the runtime rule file with the five `skills/DESIGN.md` sections that the workflows load at Step 0, moved verbatim.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the new file. Content is copied from `skills/DESIGN.md` under the original headings: Output language, Analysis-only phase constraint, Change-impact table, Tool availability guard, Out-of-scope paths. The text is not reworded.

## Assumptions

- Verified: the five sections are at `DESIGN.md:113-125` (Tool availability guard, Analysis-only phase constraint), `:147-165` (Output language), `:166-182` (Change-impact table), and `:264-269` (Out-of-scope paths); together about 3.8 KB.
- Verified: the moved text cites `AGENTS.md` (Role) and `rules/env.md` (Architecture); the cycle checker links cross-file edges only, and these edges existed from the original sections, so the graph keeps the same shape (UNK-02 of the Plan is re-checked by running the checker in procedure 08).

## Design decisions

- File header: one paragraph stating it holds the runtime sections loaded by the pipeline skills, and that `skills/DESIGN.md` keeps the design rationale; use the original `###` headings so citations by section name stay meaningful.

## Alternatives considered

Rejected: rewording while moving (the issue's constraint is to move, not rewrite).

## Implementation
### Target file
`rules/skill-runtime.md` (new)

### Procedure
1. Create the file with the header and the five sections copied verbatim, in the order Output language, Analysis-only phase constraint, Change-impact table, Tool availability guard, Out-of-scope paths.
2. Diff the copied text against `skills/DESIGN.md` before procedure 08 replaces the originals.

### Method
Read the five sections from `skills/DESIGN.md` and write them unchanged.

### Details
- The file must stay far below the size limit (about 4 KB).

## Compatibility considerations

New file; nothing references it until procedures 08-12.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The file holds the five sections verbatim and the reference checks pass.

## Out of Scope

Editing `skills/DESIGN.md` (procedure 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-160633 | 20261123-161116 | Edited as described; the five moved sections are verbatim (checked by a before and after comparison) |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-161116 | 20261123-161116 | check_skills_references, check_skills_heading_cycles, and the validation gates pass |

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
- **Requirement ID**: `REQ-003` (runtime rule file and pointers)
- **Source issue**: issues/20261123-155457_skillsize001_compress-skill-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-155813_skillsize001_compress-skill-workflows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-160210
- **Related target files**: `rules/skill-runtime.md`
