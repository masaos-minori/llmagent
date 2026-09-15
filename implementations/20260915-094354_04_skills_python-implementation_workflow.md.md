## Goal
Cross-reference "sufficient context" in `skills/python-implementation/workflow.md`
line 163 (REQ-002) to its own immediately-preceding worked example, rather than
inventing a new definition.

## Scope
In scope: the "log errors with sufficient context before re-raising" bullet under Step
5b (Error handling rules). Out of scope:
`skills/python-implementation/SKILL.md`'s own "smallest change" wording (a separate
target-file row in this same Plan); the other Step 5b bullets ("add context to an
error when the raw exception does not already identify which value or call site
failed", "trust internal invariants; validate only at public boundaries"); any other
section of this file.

## Assumptions
- Adding one short clause will not push this file over the 400-line File Split Rule
  trigger in `skills/DESIGN.md`.
- The worked example at lines 158-161 (naming the function and invalid value in a
  raised `ValueError`) already demonstrates concretely what "sufficient context" means
  for this specific bullet — confirmed present and immediately preceding the target
  bullet during this document's own Step 3a verification (re-read against current
  source, not merely trusted from the Plan's citation).

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), the fix is a cross-reference to the adjacent example, not a new
standalone definition — the Plan's own Problem section already identifies that "the
qualifier is a summary of that adjacent example, not an independently undefined
term," so restating a new definition would duplicate what the example already shows.

## Alternatives considered
- Writing a new abstract definition of "sufficient context" (e.g. "include the
  function name, the invalid value, and the call site") — rejected: this would
  duplicate the worked example's content in prose form, violating
  `skills/DESIGN.md` Avoid implementation-reference duplication; a direct
  cross-reference to the example is more maintainable (one place to update if the
  example changes).

## Implementation
### Target file
skills/python-implementation/workflow.md

### Procedure
1. Open Step 5b ("Error handling rules"), locate "log errors with sufficient context
   before re-raising" (line 163).
2. Append a cross-reference to the worked example two bullets above it (lines
   158-161).
3. Leave the other Step 5b bullets and all surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full bullet line
(unique in the file), appending the cross-reference at its end.

### Details
Change:
`- log errors with sufficient context before re-raising`
to:
`- log errors with sufficient context before re-raising — "sufficient" means the
function name and invalid value/call site, per the raised-exception example above`

Do not alter the two preceding bullets (the error-context and worked-example bullets)
or the "trust internal invariants" bullet in the same Step.

## Compatibility considerations
This file is referenced by 5+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file) — the change only clarifies what an existing rule means, without altering the
rule's actual requirement.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to one bullet; revertable independently of
the other 7 documents in this pass via `git checkout -- skills/python-implementation/
workflow.md` (pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff skills/python-implementation/workflow.md` — confirm only the named
  bullet's appended clause changed, no other line touched, and the worked example
  above it unchanged.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
The "sufficient context" bullet cross-references the adjacent worked example
concretely; the bullet's original wording, the worked example, and the other Step 5b
bullets are unchanged; `tools/check_skills_references.py` passes (Plan AC-2's
python-implementation/workflow.md half).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document, including `skills/python-implementation/SKILL.md`'s own row for the same
Requirement ID); the other Step 5b bullets; any other section of `skills/python-
implementation/workflow.md`; any other evaluation criterion from the source review
batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-102131 | 20260915-102131 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-102131 | 20260915-102131 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-102131 | 20260915-102131 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-102131 | 20260915-102131 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-002 (cross-reference "sufficient context" in python-implementation/workflow.md)
- **Source issue**: issues/20260914-114854_skillqa02_replace-vague-qualifiers-with-concrete-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-094354
- **Related target files**: skills/python-implementation/workflow.md