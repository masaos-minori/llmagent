## Goal
Define "small change" (line 104) and "long functions" (line 115) in
`skills/python-refactoring/SKILL.md` (REQ-006) with a concrete threshold, reusing
`rules/toolchain.md`'s existing `radon cc -n C` complexity-grade check.

## Scope
In scope: "Keep every change small." (`### Refactoring rules`) and "Reduce nesting,
branching, and long functions." (also `### Refactoring rules`). Out of scope: the
other bullets in `### Refactoring rules` and `### Type safety rules`, including the
"Do not mix fetching, transformation, decision logic, and persistence in one
function." and "Do not use `Any`, unnecessary casts, or unsafe assertions." bullets —
those are addressed by a separate Plan (`skillqa01`, already implemented as
`implementations/20260915-093800_06_skills_python-refactoring_SKILL.md.md`, for
missing positive alternatives, a different defect from this Plan's vague-qualifier
scope); any other section of this file.

## Assumptions
- Adding clauses to 2 short bullets will not push this file over the 400-line File
  Split Rule trigger in `skills/DESIGN.md`.
- A different Plan (`skillqa01`) already added positive-alternative clauses to 2 other
  bullets in the same `### Refactoring rules`/`### Type safety rules` subsections
  (confirmed by re-reading current content: those 2 bullets are distinct from "Keep
  every change small." and "Reduce nesting, branching, and long functions." — no
  overlap between the two Plans' edits to this file).
- `rules/toolchain.md`'s `radon cc scripts/ -s -n C` command (confirmed present via
  Reference Files below) is the correct, single existing complexity-grade check to
  reuse, per the Plan's own citation.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), both thresholds reuse `rules/toolchain.md`'s existing `radon cc -n C`
grade-C-or-worse check rather than inventing a new line-count number, per the Plan's
Constraint (reuse an existing standard) and its explicit citation of this exact
command for "long functions." "Keep every change small" is tied to the same check
since a change confined to functions below the C-grade complexity threshold is, by
construction, a small, reviewable change at the function level.

## Alternatives considered
- A separate, independent line-count number for "small change" (e.g. "no more than 20
  changed lines") distinct from the complexity grade — rejected: the Plan's own
  Constraint and REQ-006 wording group both qualifiers under the same reused
  `radon cc -n C` check; introducing a second, unrelated number would create two
  competing "smallness" standards in the same file.

## Implementation
### Target file
skills/python-refactoring/SKILL.md

### Procedure
1. Open `### Refactoring rules`, locate "Keep every change small." (line 104).
2. Append a cross-reference to `rules/toolchain.md`'s `radon cc -n C` check.
3. Locate "Reduce nesting, branching, and long functions." (line 115).
4. Append the same cross-reference, scoped to "long functions" specifically.
5. Leave the other bullets in both subsections (including the 2 bullets already
   amended by `skillqa01`) unchanged.

### Method
Use `Edit` with two separate `old_string`/`new_string` pairs (each bullet's exact
current text is unique in the file), each appending its cross-reference.

### Details
- `Keep every change small.` → append ` — as a concrete bound, keep every touched
  function at or below \`rules/toolchain.md\`'s \`radon cc -n C\` grade-C-or-worse
  threshold (a change that pushes a function past that grade is not small).`
- `Reduce nesting, branching, and long functions.` → append ` — "long" means at or
  above \`rules/toolchain.md\`'s \`radon cc -n C\` grade-C-or-worse threshold; reduce
  below it.`

Do not alter the 2 bullets already amended by `skillqa01` in the same subsections, or
any other bullet.

## Compatibility considerations
This file is referenced by 16+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected — this is a skill instruction
file, and the reused `radon cc -n C` check is already an existing, unmodified
repository standard (`rules/toolchain.md`), not a new enforcement gate.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file edit confined to 2 bullets; revertable independently of the other 7
documents in this pass via `git checkout -- skills/python-refactoring/SKILL.md`
(pre-commit) or a follow-up commit reverting this file only. Given the file also
carries the separately-applied `skillqa01` edits, verify after any revert that only
this Plan's 2 target bullets are affected.

## Validation plan
- `git diff skills/python-refactoring/SKILL.md` — confirm only the 2 named bullets'
  appended clauses changed, no other line touched (including the 2 bullets already
  amended by `skillqa01`).
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced (the new clauses reference
  `rules/toolchain.md` by name).

## Completion criteria
Both "small change" and "long functions" have a concrete threshold reusing
`rules/toolchain.md`'s `radon cc -n C` check; neither bullet's original wording
changed; the file's other content (including `skillqa01`'s separate edits) is
unaffected; `tools/check_skills_references.py` passes (Plan AC-6, AC-8 for this
file's portion of this Plan).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document); the other bullets in `### Refactoring rules` and `### Type safety rules`,
including the 2 already handled by the separate `skillqa01` Plan; any other section of
`skills/python-refactoring/SKILL.md`; any other evaluation criterion from the source
review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-102453 | 20260915-102453 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-102453 | 20260915-102453 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-102453 | 20260915-102453 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-102453 | 20260915-102453 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-006 (define "small change"/"long functions" via radon cc -n C)
- **Source issue**: issues/20260914-114854_skillqa02_replace-vague-qualifiers-with-concrete-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-094354
- **Related target files**: skills/python-refactoring/SKILL.md