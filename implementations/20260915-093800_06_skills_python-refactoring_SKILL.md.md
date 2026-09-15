## Goal
Add one positive-form alternative clause to each of 2 items in
`skills/python-refactoring/SKILL.md` (REQ-006): the "Refactoring rules" fetching/
transformation/decision/persistence-mixing bullet, and the "Type safety rules" `Any`/
unsafe-cast/assertion bullet, so each prohibition resolves to a concrete next action.

## Scope
In scope: the "Do not mix fetching, transformation, decision logic, and persistence in
one function." bullet (`### Refactoring rules`) and the "Do not use `Any`, unnecessary
casts, or unsafe assertions." bullet (`### Type safety rules`). Out of scope: the
other bullets in both subsections; any other section of this file; any other file (see
the Plan's other 7 target-file rows).

## Assumptions
- Adding 2 short alternative clauses will not push this file over the 400-line File
  Split Rule trigger in `skills/DESIGN.md`.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), each alternative names the concrete architectural pattern to apply
instead (function extraction by responsibility; explicit typed narrowing) rather than
a vague instruction, matching the Plan's cited model style.

## Alternatives considered
- Referencing `workflow.md` Step 6 (Deletion-First Evaluation) for both alternatives,
  mirroring the adjacent "Avoid unnecessary abstraction" bullet's own cross-reference
  style — considered for the fetching/transformation bullet, but rejected: Step 6 in
  `workflow.md` covers deletion/simplification evaluation, not function-responsibility
  splitting, so it would be an inaccurate cross-reference; a direct, self-contained
  alternative was used instead.

## Implementation
### Target file
skills/python-refactoring/SKILL.md

### Procedure
1. Open `### Refactoring rules`, locate "Do not mix fetching, transformation,
   decision logic, and persistence in one function."
2. Append an alternative clause to that bullet.
3. Open `### Type safety rules`, locate "Do not use `Any`, unnecessary casts, or
   unsafe assertions."
4. Append an alternative clause to that bullet.
5. Leave the other bullets in both subsections and all surrounding content unchanged.

### Method
Use `Edit` with two separate `old_string`/`new_string` pairs (each bullet's exact
current text is unique in the file), each appending its alternative clause.

### Details
- `Do not mix fetching, transformation, decision logic, and persistence in one
  function.` → append ` — instead, extract each concern into its own function so each
  has one responsibility (see "Give each function one responsibility" above).`
- `Do not use \`Any\`, unnecessary casts, or unsafe assertions.` → append ` — instead,
  add an explicit type annotation or a runtime boundary check that narrows the type
  safely (see the boundary-check rule above).`

Both alternatives reference an existing adjacent bullet in the same list rather than
inventing new guidance, per `skills/python-design/SKILL.md` Core Design Rules. Do not
alter any other bullet in either subsection, and do not alter the two subsection
headings.

## Compatibility considerations
N/A: additive prose-only change to a skill instruction file; no public/runtime
interface, no code behavior affected.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to 2 bullets in 2 subsections; revertable
independently of the other 7 documents in this pass via `git checkout --
skills/python-refactoring/SKILL.md` (pre-commit) or a follow-up commit reverting this
file only.

## Validation plan
- `git diff skills/python-refactoring/SKILL.md` — confirm only the 2 appended clauses
  changed, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
Both named items each have an adjacent positive-form alternative; neither
prohibition's original wording changed; the other bullets in both subsections are
untouched; `tools/check_skills_references.py` passes (Plan AC-6, AC-8 for this file's
portion).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document); the other bullets in `### Refactoring rules` and `### Type safety rules`;
any other section of `skills/python-refactoring/SKILL.md`; any other evaluation
criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-101221 | 20260915-101221 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-101221 | 20260915-101221 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-101221 | 20260915-101221 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-101221 | 20260915-101221 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-006 (add positive alternatives to the 2 named python-refactoring/SKILL.md items)
- **Source issue**: issues/20260914-114822_skillqa01_negative-instructions-add-positive-alternatives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-084829_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-093800
- **Related target files**: skills/python-refactoring/SKILL.md