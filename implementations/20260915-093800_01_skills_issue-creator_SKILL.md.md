## Goal
Add one positive-form alternative clause to each of the 4 items in
`skills/issue-creator/SKILL.md` "When not to use" (REQ-001), so each prohibition
resolves to a concrete next action.

## Scope
In scope: the 4 bullets under `## When not to use` (currently: direct code
implementation; speculative issues without evidence or context; bulk issue generation
that mixes unrelated concerns; writing long implementation manuals inside issues).
Out of scope: any other section of this file; any other file (see the Plan's other 7
target-file rows, each its own document).

## Assumptions
- Adding 4 short alternative clauses will not push this file over the 400-line File
  Split Rule trigger in `skills/DESIGN.md` (Plan Assumptions).
- The existing sentence immediately after the list ("When requirements are unclear,
  use this skill, but follow `workflow.md` Phase 1: mark assumptions and open
  questions instead of inventing missing requirements.") already models the
  prohibition-plus-alternative style within this same file and is the closest local
  precedent, in addition to the three cross-file examples the Plan cites.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), each alternative names the correct workflow/skill to route to instead
of restating that skill's own procedure. Each clause reuses this project's existing
pipeline vocabulary (`python-implementation`, `issue-to-plan` →
`plan-to-implementation-procedure` → `code-implementation`, this skill's own Phase
1/Phase 2) rather than inventing new terminology, matching the Plan's cited model
sentences (`rules/ai-execution.md` Context Reading; `skills/python-design/SKILL.md`;
`skills/python-code-review/SKILL.md`).

## Alternatives considered
- A single combined note after the list (e.g. "for all of the above, see workflow.md")
  instead of one clause per item — rejected: the Plan's Required Changes explicitly
  requires one alternative per item, since each item's correct alternative differs.
- Rewording the 4 prohibitions themselves to be positive-only (dropping "do not use
  this skill for") — rejected: the Plan's Constraint requires the existing prohibition
  wording to be preserved unchanged, adding only the alternative.

## Implementation
### Target file
skills/issue-creator/SKILL.md

### Procedure
1. Open `## When not to use` (the 4-item list following "Do not use this skill for:").
2. Append one alternative clause to each of the 4 bullets, in place.
3. Leave the existing trailing sentence ("When requirements are unclear...") and all
   surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full 4-item list (so the
match is unique), replacing it with the same 4 items plus their appended alternative
clauses.

### Details
Append, to each bullet (do not alter the existing bullet text before the added
clause):
- `direct code implementation` → append ` — instead, route it through
  \`python-implementation\` directly, or through \`issue-to-plan\` →
  \`plan-to-implementation-procedure\` → \`code-implementation\` for larger scope.`
- `speculative issues without evidence or context` → append ` — instead, gather at
  least one concrete piece of evidence (a repository file, log, or existing document)
  first, or record the gap as an assumption/open question per Phase 1.`
- `bulk issue generation that mixes unrelated concerns` → append ` — instead, apply
  Phase 2's Task Grouping to split them into separate issues.`
- `writing long implementation manuals inside issues` → append ` — instead, keep
  Implementation Intent high-level and let \`plan-to-implementation-procedure\`
  produce the file-level manual.`

Do not change the bullets' existing wording, order, or the heading itself.

## Compatibility considerations
N/A: additive prose-only change to a skill instruction file; no public/runtime
interface, no code behavior affected.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit; revertable with `git checkout -- skills/issue-creator/
SKILL.md` (pre-commit) or a follow-up commit reverting this file only, with no
dependency on the other 7 documents in this pass.

## Validation plan
- `git diff skills/issue-creator/SKILL.md` — confirm only the 4 appended clauses
  changed, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
All 4 items under `## When not to use` have an adjacent positive-form alternative;
none of the 4 prohibitions' original wording changed; `tools/check_skills_references.py`
passes (Plan AC-1, AC-8 for this file's portion).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document); any other section of `skills/issue-creator/SKILL.md`; any other evaluation
criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-100737 | 20260915-100737 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-100737 | 20260915-100737 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-100737 | 20260915-100737 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-100737 | 20260915-100737 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 (add positive alternatives to "When not to use")
- **Source issue**: issues/20260914-114822_skillqa01_negative-instructions-add-positive-alternatives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-084829_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-093800
- **Related target files**: skills/issue-creator/SKILL.md