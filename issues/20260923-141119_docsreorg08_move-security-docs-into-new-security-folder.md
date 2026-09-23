# Move security docs into new security folder

## Priority
Medium

## Summary
`git mv` the 2 security-area files from `docs/` (flat) into a new `docs/91_security/`
subfolder. No filename or content change beyond required reference fixups.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This issue covers the `91_security` area.

## Problem
`docs/00_security_01_architecture-and-trust-boundaries.md` and
`docs/00_security_02_high-risk-tool-common-policy.md` currently sit directly under
`docs/`. Both currently declare `area: governance` in Front Matter (not `area: adr`/
`area: security`, even though the schema already defines those enum values) — this
issue does not change the `area:` Front Matter value, only the physical folder; see Out
of Scope.

## Reason for Change
Same rationale as `docsreorg05`: group this area's docs into its own folder as part of
the broader `docs/` reorganization.

## Implementation Intent
Use `git mv` only — do not rename any file and do not change either file's `area:`
Front Matter value.

## Target Files or Areas
- `docs/00_security_01_architecture-and-trust-boundaries.md` → `docs/91_security/00_security_01_architecture-and-trust-boundaries.md`
- `docs/00_security_02_high-risk-tool-common-policy.md` → `docs/91_security/00_security_02_high-risk-tool-common-policy.md`

## Required Changes
- `git mv` each of the 2 files listed above into `docs/91_security/`.
- `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS` currently has
  no entries keyed to either file (confirmed during issue drafting) — no baseline
  update expected.
- Confirm `docsreorg01` and `docsreorg02` have landed before merging this move.
- `docsreorg04`'s reference updates cover any specific mentions of these two files.

## Constraints
- `git mv` only — no filename change, no `area:` Front Matter change, no content
  rewriting beyond what `docsreorg04` already covers.

## Acceptance Criteria
- `git log --follow` on each moved file shows continuous history through the move.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run python -m tools.check_docs_quality` passes (or reports only pre-existing,
  unrelated findings).
- Both files' `area:` Front Matter value is unchanged (`governance`) after the move.

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`

## Documentation Impact
This issue is itself the documentation-location change for the security area.

## Out of Scope
- Any filename change or prefix removal.
- Changing either file's `area:` Front Matter value from `governance` to `security` —
  this is an independent decision (folder placement and `area:` value are being kept
  separate) and is not part of this issue.
- Any content edit beyond what `docsreorg04` already covers.

## Dependencies
- Depends on: `docsreorg01`, `docsreorg02`.
- Coordinate with: `docsreorg04` (canonical reference updates).

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Move only the 2 files listed, using `git mv`, into `docs/91_security/`. Do not rename
either file and do not change their `area:` Front Matter value. If
`docsreorg01`/`docsreorg02` have not landed yet, stop and report `Blocked`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141119
- **Related target files**: docs/00_security_01_architecture-and-trust-boundaries.md, docs/00_security_02_high-risk-tool-common-policy.md
