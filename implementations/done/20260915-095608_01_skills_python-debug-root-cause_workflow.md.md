## Goal
Add a lead-in sentence to `skills/python-debug-root-cause/workflow.md` Phase 5
pointing to Phase 3's classification table as the tool-selection basis, and an
explicit "Completed when" line to both Phase 2 and Phase 5 (REQ-001, REQ-002,
REQ-003).

## Scope
In scope: one lead-in sentence at the start of Phase 5's content, one "Completed
when" line at the end of Phase 2, one "Completed when" line at the end of Phase 5.
Out of scope: sub-splitting Phase 5 into lettered sub-steps; Phase 1, 3, 4, 6, 7, 8,
9 (unchanged); duplicating Phase 3's table content inside Phase 5.

## Assumptions
- Adding 1 lead-in sentence and 2 short lines will not push this file over the
  400-line File Split Rule trigger in `skills/DESIGN.md`.
- Phase 3's classification table's "Execution model"/"Failure domain" column headers
  (confirmed via Reference Files below) are still the correct columns to name in the
  lead-in, without restating the table's cell values.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), REQ-001's lead-in names only the two relevant column headers from
Phase 3's table, not its cell values, so the two sections cannot drift apart. Phase
2's existing priority-logic sentences ("Use X first... reach for Y only when...")
model REQ-002's phrasing style; Phase 1/6/9's existing "Completed when" lines model
REQ-002/REQ-003's format.

## Alternatives considered
- Copying Phase 3's table (or a summary of it) into Phase 5 — rejected per the Plan's
  own Constraint and AC-3: this would duplicate content that already exists once in
  Phase 3, risking drift if either copy is edited independently.

## Implementation
### Target file
skills/python-debug-root-cause/workflow.md

### Procedure
1. Locate the end of Phase 2's content (after "Remove before committing. DSN must
   come from environment only."), insert the "Completed when" line (REQ-002) before
   the `---` separator.
2. Locate the "## Phase 5: Runtime / Trace Inspection" heading, insert the lead-in
   sentence (REQ-001) immediately after it, before the first tool subsection
   ("#### viztracer").
3. Locate the end of Phase 5's content (after the "rich + stackprinter" subsection's
   closing code block), insert the "Completed when" line (REQ-003) before the `---`
   separator.
4. Leave Phase 1, 3, 4, 6, 7, 8, 9 unchanged.

### Method
Use `Edit` with three separate `old_string`/`new_string` pairs, each anchored on
unique existing text (Phase 2's closing sentence, the Phase 5 heading, and Phase 5's
final code block).

### Details
- Phase 2 (after "Remove before committing. DSN must come from environment only."):
  add `**Completed when**: at least one observability source above has surfaced
  enough signal to inform Phase 3's classification, or all applicable sources were
  checked and none did.`
- Phase 5 heading (immediately after "## Phase 5: Runtime / Trace Inspection", before
  "#### viztracer"): add `Select the tool(s) using Phase 3's classification table
  (Execution model / Failure domain columns) — do not try tools in the order listed
  below without that basis.`
- Phase 5 (after the "rich + stackprinter" subsection's closing code block): add
  `**Completed when**: the tool(s) selected via Phase 3's table have been run and
  produced either a concrete lead for Phase 6's hypothesis table or a confirmed
  absence of signal from that tool.`

Do not restate Phase 3's table content, and do not alter any other Phase.

## Compatibility considerations
This file is referenced by 2+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file edit adding 3 independent blocks; revertable via `git checkout --
skills/python-debug-root-cause/workflow.md` (pre-commit) or a follow-up commit
reverting this file only.

## Validation plan
- `git diff skills/python-debug-root-cause/workflow.md` — confirm exactly 3 additions
  (Phase 2 completion line, Phase 5 lead-in, Phase 5 completion line), no other Phase
  touched, Phase 3's table not duplicated.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
Phase 5 explicitly references Phase 3's classification table as its tool-selection
basis without duplicating it; Phase 2 and Phase 5 each have an explicit "Completed
when" line; `tools/check_skills_references.py` passes (Plan AC-1, AC-2, AC-3).

## Out of scope
Sub-splitting Phase 5 into lettered sub-steps; Phase 1, 3, 4, 6, 7, 8, 9 of this same
file; any other file; any other evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-105842 | 20260915-105842 | 3 additions: Phase 2 completion, Phase 5 lead-in, Phase 5 completion |
| 2 | Add or update tests per Validation plan | Completed | 20260915-105842 | 20260915-105842 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-105842 | 20260915-105842 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-105842 | 20260915-105842 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (Phase 5 lead-in; Phase 2/5 completion conditions)
- **Source issue**: issues/20260914-115344_skillqa09_debug-workflow-phase2-phase5-completion-and-tool-selection-link.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-090108_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-095608
- **Related target files**: skills/python-debug-root-cause/workflow.md