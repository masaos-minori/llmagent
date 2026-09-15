## Goal
Add an explicit "Completed when" line to Step 3 (Architecture Integrity), Step 7
(Static Security Validation), and Step 8 (Diff Scope Enforcement) in
`skills/python-lint-typecheck/workflow.md` (REQ-001 through REQ-003), each tying
completion to the underlying check actually passing.

## Scope
In scope: one "Completed when" line appended to each of Step 3, 7, and 8. Out of
scope: the mypy/pyright disagreement rule at line 176 (already present, confirmed
during this document's own Step 3a verification, no change needed); any other Step;
the shared "Step failure handling" rule (line 18, not restated per-Step).

## Assumptions
- Adding 3 short lines will not push this file over the 400-line File Split Rule
  trigger in `skills/DESIGN.md`.
- Line 176's mypy/pyright disagreement rule remains present and unrelated to this
  document's 3 target Steps, confirmed by re-reading the file's current content.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), each line requires the underlying check to actually pass, not merely
that a remediation procedure ran once — REQ-001 in particular reuses Step 3's own
existing statement ("a suppression comment does not apply to this checker") as
reinforcement that only a clean `lint-imports` result (or an explicit contract
update) counts.

## Alternatives considered
- Wording each "Completed when" line as "the remediation procedure above was
  followed" — rejected: this is exactly the ambiguity the Issue identifies (running
  the procedure once vs. the underlying check actually passing); the Plan's AC-2
  requires the stricter, outcome-based wording instead.

## Implementation
### Target file
skills/python-lint-typecheck/workflow.md

### Procedure
1. Locate the end of Step 3 ("Architecture Integrity"), Step 7 ("Static Security
   Validation"), and Step 8 ("Diff Scope Enforcement") sections, each immediately
   before its trailing `---` separator.
2. Insert the corresponding "Completed when" line (REQ-001 through REQ-003) at each
   location.
3. Leave line 176 (mypy/pyright disagreement rule) and all other Steps unchanged.

### Method
Use `Edit` with 3 separate `old_string`/`new_string` pairs, each anchored on the exact
final sentence/code block of the corresponding Step (unique in the file), appending
the new "Completed when" line as a new paragraph after it, before the `---`
separator.

### Details
- Step 3 (after the `ast-grep`/`rg` cross-reference commands at the end of
  "Architecture Integrity"): add `**Completed when**: \`lint-imports\` reports no
  violation, either because no accidental import remained or because every
  intentional import is now covered by an explicit \`.importlinter\` contract
  update.`
- Step 7 (after "Priority findings — must resolve before merge: see
  \`rules/coding.md\` Bandit priority findings."): add `**Completed when**:
  \`bandit\` has been run and every priority finding (per \`rules/coding.md\` Bandit
  priority findings) is resolved or suppressed with the required justification (per
  \`rules/coding.md\` Suppression governance).`
- Step 8 (after "Do not add tests for unrelated lines to inflate coverage — scope
  tests to the change."): add `**Completed when**: \`diff-cover\` reports the
  changed-lines coverage at or above the threshold in \`rules/toolchain.md\` §7,
  using only tests scoped to the actual change.`

Do not alter line 176 or any other Step's content, heading, or `---` separator
placement.

## Compatibility considerations
This file is referenced by 2+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only. Step 7's new line strengthens (does not weaken) the existing
security-validation requirement.

## Rollback considerations
Single-file edit adding 3 independent lines; revertable via `git checkout --
skills/python-lint-typecheck/workflow.md` (pre-commit) or a follow-up commit
reverting this file only.

## Validation plan
- `git diff skills/python-lint-typecheck/workflow.md` — confirm exactly 3 new lines
  added, one per Step 3/7/8, no other line touched, line 176 unchanged.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
Each of Step 3, 7, and 8 has an explicit "Completed when" line worded per REQ-001
through REQ-003, tying completion to the underlying check actually passing; line 176
is unchanged; `tools/check_skills_references.py` passes (Plan AC-1, AC-2).

## Out of scope
Line 176's mypy/pyright disagreement rule; any other Step in this file; any other
file; any other evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-105308 | 20260915-105308 | 3 insertions, one per Step 3/7/8 |
| 2 | Add or update tests per Validation plan | Completed | 20260915-105308 | 20260915-105308 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-105308 | 20260915-105308 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-105308 | 20260915-105308 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 through REQ-003 (add "Completed when" to Step 3/7/8)
- **Source issue**: issues/20260914-115214_skillqa07_python-lint-typecheck-workflow-step-completion-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085821_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-095324
- **Related target files**: skills/python-lint-typecheck/workflow.md