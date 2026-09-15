## Goal
Update `skills/issue-creator/workflow.md` Phase 10 to prefer
`tools/generate_workitem.py --kind issue` for scaffolding a new issue file, while
retaining the existing 6-step manual procedure as an explicit fallback (REQ-001
through REQ-003).

## Scope
In scope: Phase 10's content only — adding a preferred-tool path, its independent-
verification requirement, and a fallback lead-in before the existing 6-step
procedure. Out of scope: `tools/generate_workitem.py` itself (no change);
`skillqa03`'s separate Phase 3-8 "Completed when" additions to this same file
(`implementations/20260915-094827_01_skills_issue-creator_workflow.md.md`, confirmed
non-overlapping — different Phases); any other section of this file.

## Assumptions
- Adding 2 new lines and one lead-in sentence will not push this file over the
  400-line File Split Rule trigger in `skills/DESIGN.md`.
- `tools/generate_workitem.py --kind issue`'s CLI flags (`--id`, `--title`) and
  refusal behavior were re-confirmed present via `--help` during this document's own
  Step 3a verification, matching the Plan's Problem section exactly.
- A separate Plan (`skillqa03`) already produced its own implementation procedure
  for this same file's Phase 3-8 — confirmed non-overlapping with this document's
  Phase 10 scope by re-reading both Plans' Scope sections.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), the new lines model `skills/issue-to-plan/workflow.md` Step 5's
existing `generate_workitem.py --kind plan` cross-reference verbatim in structure,
substituting `--kind issue --id {id} --title {title}` — reusing proven phrasing
rather than inventing new wording, for consistency across the three sibling skills
that now reference this tool the same way.

## Alternatives considered
- Replacing the 6-step manual procedure entirely with only the tool-based path —
  rejected: the Plan's own Constraint requires retaining the manual procedure as a
  fallback for when the tool is unavailable, not removing it.

## Implementation
### Target file
skills/issue-creator/workflow.md

### Procedure
1. Locate the start of Phase 10's content, immediately after "generate the filename
   using the convention defined in `SKILL.md` Issue Filename Generation." and before
   the existing "1. Extract or assign an `{id}`..." numbered list.
2. Insert the preferred-tool line (REQ-001) and the independent-verification line
   (REQ-002).
3. Insert a fallback lead-in sentence (REQ-003) immediately before the existing
   6-step numbered list, framing it as the path used only if the tool is
   unavailable.
4. Leave the 6 existing numbered sub-steps' content unchanged, and leave `skillqa03`'s
   separately-tracked Phase 3-8 additions (a different Phase) untouched.

### Method
Use `Edit` with an `old_string`/`new_string` pair anchored on the sentence "generate
the filename using the convention defined in `SKILL.md` Issue Filename Generation."
through the start of the numbered list "1. Extract or assign an `{id}`..." (unique in
the file), inserting the new content between them.

### Details
After:
`After the issue body is finalized, generate the filename using the convention
defined in \`SKILL.md\` Issue Filename Generation.`
and before:
`1. Extract or assign an \`{id}\` from the issue content...`
insert:
`Prefer \`uv run python tools/generate_workitem.py --kind issue --id {id} --title
{title}\` to scaffold the file — it generates the \`{timestamp}_{id}_{slug}.md\`
filename and refuses (non-zero exit, no write) on a path collision rather than
auto-incrementing; treat that refusal as the trigger for the retry-with-
disambiguator step already described, not as a workflow failure.
After a \`0\` exit, independently verify the reported output path exists and
contains the expected \`## \` section headings before proceeding to fill in its
content — per \`rules/ai-execution.md\` Repository Tool Usage item 8, a \`0\` exit
alone MUST NOT be treated as proof the file was written correctly.
If the tool is unavailable, use the manual procedure below:`

Do not alter any of the 6 existing numbered sub-steps or the "Do NOT create issues
without following this naming convention." closing sentence.

## Compatibility considerations
This file is referenced by 8+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file). A separate Plan (`skillqa03`) already produced its own implementation
procedure for this same file's Phase 3-8 — this document's insertions are confined to
Phase 10 and do not touch Phase 3-8, so the two documents' edits do not conflict when
both are applied.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file edit confined to Phase 10; revertable via `git checkout --
skills/issue-creator/workflow.md` (pre-commit) or a follow-up commit reverting this
file only. If `skillqa03`'s Phase 3-8 edit has already landed in the same file by the
time of a revert, verify the revert does not also remove that unrelated change.

## Validation plan
- `git diff skills/issue-creator/workflow.md` — confirm the preferred-tool path,
  verification line, and fallback lead-in were added at the start of Phase 10; the 6
  existing numbered sub-steps are unchanged; no other Phase touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
Phase 10 names `tools/generate_workitem.py --kind issue` as the preferred scaffolding
method; the independent-verification step is present; the existing manual procedure
remains as an explicit fallback, not removed; `tools/check_skills_references.py`
passes (Plan AC-1 through AC-3).

## Out of scope
`tools/generate_workitem.py` itself; `skillqa03`'s Phase 3-8 additions to this same
file; any other section of `skills/issue-creator/workflow.md`; any other file; any
other evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-110656 | 20260915-110656 | Preferred-tool path, verification line, fallback lead-in |
| 2 | Add or update tests per Validation plan | Completed | 20260915-110656 | 20260915-110656 | N/A: no automated test for this file type — see Validation plan; manual smoke check already performed at Plan Step 2 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-110656 | 20260915-110656 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-110656 | 20260915-110656 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 through REQ-003 (Phase 10 preferred-tool path, verification, fallback framing)
- **Source issue**: issues/20260914-115748_skillqa14_issue-creator-use-existing-scaffold-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-090758_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-100158
- **Related target files**: skills/issue-creator/workflow.md