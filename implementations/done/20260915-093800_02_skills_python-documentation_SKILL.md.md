## Goal
Add one positive-form alternative clause to `skills/python-documentation/SKILL.md`'s
"Respect boundaries" bullet, specifically its "trust README claims unverified" clause
(REQ-002), so the prohibition resolves to a concrete next action.

## Scope
In scope: the "trust README claims unverified" clause inside the "Respect boundaries"
bullet under `## Core Documentation Rules`. Out of scope: the rest of the "Respect
boundaries" bullet's other prohibited items (expand scope, expose secrets, paste long
code blocks, infer behavior from `requirements.txt` alone, document private members as
public API) — the Plan's Problem/Requirements scope this document to only the README
clause; any other section of this file; any other file (see the Plan's other 7
target-file rows).

## Assumptions
- Adding one short alternative clause will not push this file over the 400-line File
  Split Rule trigger in `skills/DESIGN.md` (Plan Assumptions).
- The Plan's own Acceptance Criterion (AC-2) example wording ("verify against actual
  code/config instead") is a suitable, non-binding starting point for the actual
  clause — this document is free to phrase it more precisely against this file's own
  surrounding rules (Evidence first, No hallucination) as long as the alternative is
  concrete.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), the alternative clause points to this same file's existing "Evidence
first" bullet (same `## Core Documentation Rules` section) rather than restating its
content, consistent with the Plan's model of referencing existing project rules by
name instead of duplicating them.

## Alternatives considered
- Appending a alternative to the "Respect boundaries" bullet as a whole (covering all
  6 prohibited items in that bullet) — rejected: the Plan's Implementation Target
  Files row and Requirement (REQ-002) scope this document to only the "trust README
  claims unverified" clause; the other 5 items in the same bullet are out of scope for
  this Plan.
- Rewording "trust README claims unverified" itself — rejected: the Plan's Constraint
  (shared across the whole Plan) requires preserving the existing prohibition wording
  unchanged, adding only the alternative.

## Implementation
### Target file
skills/python-documentation/SKILL.md

### Procedure
1. Open `## Core Documentation Rules`, locate the "Respect boundaries" bullet
   (contains "trust README claims unverified").
2. Insert an alternative clause immediately after "trust README claims unverified"
   within that same bullet, before the next comma-separated item ("or document
   private members as public API").
3. Leave the rest of the bullet and all surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full "Respect
boundaries" bullet line (unique in the file), inserting the alternative clause at the
correct position within it.

### Details
Within the "Respect boundaries" bullet, change:
`... infer behavior from \`requirements.txt\` alone, trust README claims unverified,
or document private members as public API.`
to:
`... infer behavior from \`requirements.txt\` alone, trust README claims unverified
(verify against the actual code or config the README describes instead), or document
private members as public API.`

Do not alter any other clause in the same bullet, and do not alter the bullet's
opening ("**Respect boundaries**: MUST NOT ...") or any other bullet in this section.

## Compatibility considerations
N/A: additive prose-only change to a skill instruction file; no public/runtime
interface, no code behavior affected.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to one bullet; revertable independently of
the other 7 documents in this pass via `git checkout -- skills/python-documentation/
SKILL.md` (pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff skills/python-documentation/SKILL.md` — confirm only the "Respect
  boundaries" bullet's inserted clause changed, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
The "trust README claims unverified" clause has an adjacent positive-form alternative;
no other item in the "Respect boundaries" bullet or elsewhere in the file changed
meaning; `tools/check_skills_references.py` passes (Plan AC-2, AC-8 for this file's
portion).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document); the other 5 prohibited items in the same "Respect boundaries" bullet; any
other section of `skills/python-documentation/SKILL.md`; any other evaluation
criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-100920 | 20260915-100920 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-100920 | 20260915-100920 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-100920 | 20260915-100920 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-100920 | 20260915-100920 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-002 (add positive alternative to "Respect boundaries" bullet's README clause)
- **Source issue**: issues/20260914-114822_skillqa01_negative-instructions-add-positive-alternatives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-084829_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-093800
- **Related target files**: skills/python-documentation/SKILL.md