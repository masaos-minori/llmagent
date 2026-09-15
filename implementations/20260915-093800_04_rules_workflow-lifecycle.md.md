## Goal
Add one positive-form alternative clause to each of the 3 items in
`rules/workflow-lifecycle.md` "Global Safety Restrictions" (REQ-004), so each
prohibition resolves to a concrete next action.

## Scope
In scope: the 3 bullets under `## Global Safety Restrictions` ("move existing
documentation files", "change the workflow directory structure", "change
implementation behavior during document-only phases"). Out of scope: this section's
lead-in sentence (which applies `rules/ai-execution.md` Global Safety Restrictions
(Base) and Sequential Target Processing (Base) by reference) and any other section of
this widely-shared file; any other file (see the Plan's other 7 target-file rows).

## Assumptions
- This file is referenced by 201+ other repository files (Plan Affected areas), the
  highest reference count among this Plan's 8 target files, so the edit must be
  strictly additive with no restructuring, per the Plan's Design section.
- Adding 3 short alternative clauses will not push this file over the 400-line File
  Split Rule trigger in `skills/DESIGN.md`.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), each alternative names the concrete correct-scope action for a
document-generation workflow (`issue-to-plan`, `plan-to-implementation-procedure`)
rather than restating those skills' own procedures, matching the style of the Plan's
cited model sentences.

## Alternatives considered
- One combined trailing sentence covering all 3 restrictions ("instead, keep changes
  to the document-generation output paths only") — rejected: the source Issue's
  Required Changes and this Plan's REQ-004 call for one alternative per item, since
  each restriction's correct alternative differs (move vs. restructure vs. behavior
  change).
- Rewording the 3 restrictions' existing wording — rejected: the Plan's Constraint
  (shared across the whole Plan) requires preserving the existing prohibition wording
  unchanged, adding only the alternative.

## Implementation
### Target file
rules/workflow-lifecycle.md

### Procedure
1. Open `## Global Safety Restrictions`, locate the 3-item list following the
   "Additionally, for document-generation workflows, do not perform any of the
   following:" lead-in.
2. Append an alternative clause to each of the 3 bullets, in place.
3. Leave the lead-in sentence and all surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full 3-item list (so the
match is unique), replacing it with the same 3 items plus their appended alternative
clauses.

### Details
Append, to each bullet (do not alter the existing bullet text before the added
clause):
- `move existing documentation files` → append ` — instead, leave documentation files
  in place; only `issue-to-plan`/`plan-to-implementation-procedure`'s own designated
  archival moves (\`issues/\` → \`issues/done/\`, \`plans/\` → \`plans/done/\`) are
  permitted.`
- `change the workflow directory structure` → append ` — instead, raise a directory-
  structure change as its own separate Issue/Plan outside this document-generation
  cycle.`
- `change implementation behavior during document-only phases` → append ` — instead,
  record the needed behavior change as a Requirement in the generated Plan/
  implementation procedure document for a later, dedicated implementation phase to
  apply.`

Do not change the bullets' existing wording, order, the lead-in sentence, or the
heading itself.

## Compatibility considerations
This file is referenced by 201+ other repository Markdown files (Plan Affected areas)
— the change must not alter any existing sentence's wording that another file might
quote verbatim, only append new text after each of the 3 named bullets. No public/
runtime interface or code behavior is affected (this is a rules/prose file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to 3 bullets; revertable independently of the
other 7 documents in this pass via `git checkout -- rules/workflow-lifecycle.md`
(pre-commit) or a follow-up commit reverting this file only. Given the file's very
high reference count, a revert carries no special risk since no existing line was
altered or removed.

## Validation plan
- `git diff rules/workflow-lifecycle.md` — confirm only the 3 appended clauses
  changed, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced (relevant given this file's
  very high reference count).

## Completion criteria
All 3 items under `## Global Safety Restrictions` have an adjacent positive-form
alternative; none of the 3 prohibitions' original wording changed;
`tools/check_skills_references.py` passes (Plan AC-4, AC-8 for this file's portion).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document); the section's lead-in sentence; any other section of
`rules/workflow-lifecycle.md`; any other evaluation criterion from the source review
batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-101051 | 20260915-101051 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-101051 | 20260915-101051 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-101051 | 20260915-101051 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-101051 | 20260915-101051 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-004 (add positive alternatives to "Global Safety Restrictions")
- **Source issue**: issues/20260914-114822_skillqa01_negative-instructions-add-positive-alternatives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-084829_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-093800
- **Related target files**: rules/workflow-lifecycle.md