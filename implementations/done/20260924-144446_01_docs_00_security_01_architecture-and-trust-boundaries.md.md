## Goal
Relocate `docs/00_security_01_architecture-and-trust-boundaries.md` to
`docs/91_security/00_security_01_architecture-and-trust-boundaries.md` via `git mv`,
with no filename, `area:` Front Matter, or content change, implementing `REQ-001`.
(The outbound links this file's move breaks are fixed separately by seq 03, not this
row.)

## Scope
In scope: the single `git mv` of this file (and creating the destination directory
first, since this is the first row in this pass). Out of scope: the outbound-link
content fix (seq 03's row); any other file's move.

## Assumptions
- `git mv` preserves `git log --follow` history continuity for this same-content move.
- This Git environment does not auto-create an intermediate destination directory for
  `git mv` — confirmed empirically during `docsreorg05`'s execution.
- This file has 2 outbound relative links (both to
  `docs/adr/ADR-013-eventbus-authentication-authorization.md`) that will break once
  this move lands — fixed by seq 03's separate row, not this one.
- `git mv` does not alter file content, so the `area: governance` Front Matter value
  is preserved automatically — no separate edit is needed.

## Design decisions
None beyond the mechanical move itself.

## Alternatives considered
- Plain filesystem `mv` + `git add`/`git rm`: rejected — the Plan's Constraints require
  `git mv` only.

## Implementation
### Target file
`docs/00_security_01_architecture-and-trust-boundaries.md`

### Procedure
1. Create the destination directory: `mkdir -p docs/91_security` (this Git
   environment does not auto-create it for `git mv`).
2. Run `git mv docs/00_security_01_architecture-and-trust-boundaries.md
   docs/91_security/00_security_01_architecture-and-trust-boundaries.md`.
3. Confirm the destination file exists, the source path no longer exists, and `git
   status` shows the change staged as a rename.

### Method
Single Git CLI invocation; no code change, no content diff expected between source and
destination blob.

### Details
- Do not pass any other flag to `git mv` beyond the two paths.
- Do not edit the `adr/ADR-013-eventbus-authentication-authorization.md` links in this
  row — that is seq 03's scope.
- Do not change the `area:` Front Matter value — the source Issue explicitly excludes
  this from scope.

## Compatibility considerations
Bare-filename cross-references to this file (its front matter `related` entries and
any bare-filename prose mention) continue to resolve after the move via the basename
index.

## Security considerations
N/A: a file relocation with no content change carries no security-relevant surface.

## Rollback considerations
Revert with `git mv docs/91_security/00_security_01_architecture-and-trust-boundaries.md
docs/00_security_01_architecture-and-trust-boundaries.md`, or `git revert` the commit
containing this move if already committed. Reverting this row without also reverting
seq 03-05 would leave those rows' link fixes pointing at a nonexistent post-move path
— coordinate any rollback with all 5 rows.

## Validation plan
- `git log --follow -- docs/91_security/00_security_01_architecture-and-trust-boundaries.md`
  shows continuous history through the move (Plan `AC-1`).
- `grep "^area:" docs/91_security/00_security_01_architecture-and-trust-boundaries.md`
  reports `governance` unchanged (Plan `AC-4`).
- Deferred to Phase 3: `uv run python tools/check_docs_structure.py "docs/**/*.md"
  --schema schemas/doc_front_matter.json`, `uv run python -m tools.check_docs_quality`
  (Plan `AC-2`, `AC-3`, exercised together with seq 03-05's fixes).

## Completion criteria
`docs/91_security/00_security_01_architecture-and-trust-boundaries.md` exists;
`docs/00_security_01_architecture-and-trust-boundaries.md` no longer exists at the
flat path; the move is recorded as a Git rename; `area:` remains `governance`.

## Out of scope
The 2 ADR-013 link content fixes (seq 03); any other file's move; the `area:`
Front Matter value.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `mkdir -p docs/91_security`; `git mv docs/00_security_01_architecture-and-trust-boundaries.md docs/91_security/00_security_01_architecture-and-trust-boundaries.md` | Completed | 20260924-145332 | 20260924-145332 | git mv succeeded as staged rename. |
| 2 | N/A: no test to add for a content-identical move | Completed | 20260924-145332 | 20260924-145332 | N/A: content-identical move, no test to add. |
| 3 | Confirm `git log --follow` continuity, staged rename status, and `area:` unchanged | Completed | 20260924-145332 | 20260924-145332 | git status confirms staged rename. grep "^area:" confirms governance unchanged. Full git log --follow history continuity verification deferred until this change is committed. |
| 4 | N/A: no documentation update beyond the move itself | Completed | 20260924-145332 | 20260924-145332 | N/A: no documentation update beyond the move itself; full-tree validation deferred until seq03-05 also land. |

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
- **Requirement ID**: `REQ-001` (git mv the 2 security files into `docs/91_security/`)
- **Source issue**: issues/20260923-141119_docsreorg08_move-security-docs-into-new-security-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-143444_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-144446
- **Related target files**: docs/00_security_01_architecture-and-trust-boundaries.md