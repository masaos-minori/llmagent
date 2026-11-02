## Goal
- Add a release-unit line to the procedure template (`REQ-002`: each generated procedure carries its unit name).

## Scope
- In scope: one `**Release unit**` line as the body of `## Scope` in the fenced skeleton, and one bullet in "Notes on filling sections". Out of scope: the `(new)` notes, the one-file statements, and any `##` heading.

## Assumptions
- Step 3a: `tools/generate_workitem.py` copies the fenced skeleton verbatim, so the line appears in every generated procedure; `## Scope` is currently an empty body in the skeleton.
- Overlap (Step 2): `templates/implementation-procedure.md` is also targeted by the Plans filed from `flowimp007` (the `(new)` notes) and `flowimp009` (the one-file statements and a companion section). Judged compatible (plan Assumption A5 scope; the other Plans' own Assumptions A6 and A7 agree): this row edits the `## Scope` body and adds one separate notes bullet.
- The default text is written so a procedure generated before the unit rule landed stays valid (no checker reads the line).

## Design decisions
- Skeleton line: `**Release unit**: N/A: not part of a release unit`; a member procedure carries the unit name instead.
- The notes bullet says the name is copied from the Plan's `### Release units` entry whose `Phases` include the step that cites this row's `File Path`.

## Alternatives considered
N/A: format fixed by the Plan's Design section.

## Implementation
### Target file
`templates/implementation-procedure.md`

### Procedure
- In the fenced skeleton, put the `**Release unit**` default line directly under `## Scope`.
- Add one bullet to "Notes on filling sections" describing the line and the copy rule.

### Method
- Keep the line outside any list marker in the skeleton; the generator output and the row 04 workflow text refer to it by the bold label `Release unit`.
- Do not alter the heading set: `tools/check_workitem_structure.py` reads `## ` headings only.

### Details
N/A: covered by Procedure and Method.

## Compatibility considerations
- Generated procedures gain one default line. No existing document or checker depends on `## Scope` being empty.

## Security considerations
N/A: template text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_workitem_structure.py --file {a fixture procedure with the line}` reports no findings (AC-1).
- `uv run pytest tests/tools/test_generate_workitem.py -v` passes.

## Completion criteria
- The skeleton carries the `Release unit` line and the notes bullet exists; the heading set is unchanged (AC-1).

## Out of Scope
- The workflow instruction that fills the line (row 04) and the batch-mode reader (row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `Release unit` skeleton line and the notes bullet | Pending | — | — |  |
| 2 | Validate a fixture procedure and run `tests/tools/test_generate_workitem.py` | Pending | — | — | N/A for new tests: structure checks only |
| 3 | Run the documentation checkers (`rules/toolchain.md`) | Pending | — | — | `check_skills_references.py`, `check_skills_heading_cycles.py` |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/20261030-191057_flowimp002_plan-release-units.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080336_flowimp002_plan-release-units.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085047
- **Related target files**: templates/implementation-procedure.md
