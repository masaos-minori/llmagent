## Goal
Add one positive-form alternative clause to `skills/git-commit-and-sync/SKILL.md`
"Core rules"' "Never run dangerous commands" bullet (REQ-005), so the prohibition
resolves to a concrete next action.

## Scope
In scope: the "Never run dangerous commands: `reset --hard`, `clean -fd`,
`clean -fdx`, `checkout -- .`, `restore .`, `restore --staged .`." bullet under
`## Core rules`. Out of scope: the adjacent "Never run history-rewriting or unsafe
sync commands" bullet (a separate, already-differently-scoped prohibition not named
in the Plan's Requirements); any other section of this file; any other file (see the
Plan's other 7 target-file rows).

## Assumptions
- Adding one short alternative clause will not push this file over the 400-line File
  Split Rule trigger in `skills/DESIGN.md`.
- This file's own "When not to use" section already states the correct alternative
  action pattern for destructive commands ("branch deletion or untracked file cleanup
  → do not run") in the same file, giving a same-file style precedent for phrasing.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), the alternative clause references this same file's own Phase 1 (Check
Status) and existing safe alternatives already documented elsewhere in this skill
(e.g. Phase 2's explicit-path `git add`, Phase 7's fetch-then-fast-forward-or-rebase)
rather than restating them, since this skill's entire procedure is itself already the
"instead" for any of the listed dangerous commands.

## Alternatives considered
- Naming each of the 6 listed dangerous commands' own specific safe substitute
  individually (e.g. "instead of `reset --hard`, use X; instead of `clean -fd`, use
  Y") — considered, but rejected as unnecessarily verbose for a single bullet; the
  skill's own existing Phase-based procedure already is the intended alternative to
  all 6 commands as a group, so one clause naming that fact is sufficient and matches
  the Plan's "one alternative clause" framing (singular) for this bullet.

## Implementation
### Target file
skills/git-commit-and-sync/SKILL.md

### Procedure
1. Open `## Core rules`, locate the "Never run dangerous commands" bullet.
2. Append an alternative clause after the existing sentence, before the next bullet.
3. Leave the rest of `## Core rules` and all surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full "Never run
dangerous commands" bullet line (unique in the file), appending the alternative
clause at its end.

### Details
Change:
`Never run dangerous commands: \`reset --hard\`, \`clean -fd\`, \`clean -fdx\`,
\`checkout -- .\`, \`restore .\`, \`restore --staged .\`. This skill's own procedure
never needs them, so — unlike \`AGENTS.md\` Policy's confirmation-based exception for
multi-file/recursive destructive commands — there is no confirmation path to offer
here; treat them as forbidden, not as "ask first".`
to (append at the end, same bullet):
`... treat them as forbidden, not as "ask first" — instead, use this skill's own
Phase 1 status check plus Phase 2's explicit-path staging to recover a clean state
without discarding work.`

Do not alter the adjacent "Never run history-rewriting or unsafe sync commands"
bullet or any other bullet in `## Core rules`.

## Compatibility considerations
N/A: additive prose-only change to a skill instruction file; no public/runtime
interface, no code behavior affected.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only. The change does not weaken the existing forbidden-command list; it only
adds a safe-recovery pointer.

## Rollback considerations
Single-file, additive-only edit confined to one bullet; revertable independently of
the other 7 documents in this pass via `git checkout -- skills/git-commit-and-sync/
SKILL.md` (pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff skills/git-commit-and-sync/SKILL.md` — confirm only the appended clause
  changed, no other line touched, and the forbidden-command list itself unchanged.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
The "Never run dangerous commands" bullet has an adjacent positive-form alternative;
the forbidden-command list's original wording and the adjacent history-rewriting
bullet are unchanged; `tools/check_skills_references.py` passes (Plan AC-5, AC-8 for
this file's portion).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document); the adjacent "Never run history-rewriting or unsafe sync commands" bullet;
any other section of `skills/git-commit-and-sync/SKILL.md`; any other evaluation
criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-101132 | 20260915-101132 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-101132 | 20260915-101132 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-101132 | 20260915-101132 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-101132 | 20260915-101132 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-005 (add positive alternative to "Never run dangerous commands")
- **Source issue**: issues/20260914-114822_skillqa01_negative-instructions-add-positive-alternatives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-084829_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-093800
- **Related target files**: skills/git-commit-and-sync/SKILL.md