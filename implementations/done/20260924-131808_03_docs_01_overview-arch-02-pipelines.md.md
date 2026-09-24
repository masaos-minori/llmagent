## Goal
Relocate `docs/01_overview-arch-02-pipelines.md` to
`docs/01_overview/01_overview-arch-02-pipelines.md` via `git mv`, with no filename or
content change, implementing `REQ-001`. (The 2 outbound links this file's move breaks
are fixed separately by seq 12, not this row.)

## Scope
In scope: the single `git mv` of this file. Out of scope: the outbound-link content fix
(seq 12's row); any other file's move.

## Assumptions
- `git mv` preserves `git log --follow` history continuity for this same-content move.
- Destination directory `docs/01_overview/` already exists by the time this row runs.
- This file has 2 outbound relative links (to `docs/adr/ADR-001-workflow-engine-mandatory.md`
  and `docs/adr/ADR-004-environment-failure-handling-policy.md`) that will break once
  this move lands — fixed by seq 12's separate row, not this one.

## Design decisions
None beyond the mechanical move itself.

## Alternatives considered
Same as seq 02 — fixing the outbound links in this same row is rejected in favor of the
separate pre-move/post-move row split the Plan's Implementation Target Files table
already establishes.

## Implementation
### Target file
`docs/01_overview-arch-02-pipelines.md`

### Procedure
1. Confirm the destination directory `docs/01_overview/` exists.
2. Run `git mv docs/01_overview-arch-02-pipelines.md docs/01_overview/01_overview-arch-02-pipelines.md`.
3. Confirm the destination file exists, the source path no longer exists, and `git
   status` shows the change staged as a rename.

### Method
Single Git CLI invocation; no code change, no content diff expected between source and
destination blob.

### Details
Do not pass any other flag to `git mv` beyond the two paths. Do not edit either ADR
link in this row — that is seq 12's scope.

## Compatibility considerations
Bare-filename cross-references to this file continue to resolve after the move via the
basename index. Its 2 outbound relative links break once this move lands, until seq 12
fixes them.

## Security considerations
N/A: a file relocation with no content change carries no security-relevant surface.

## Rollback considerations
Revert with `git mv docs/01_overview/01_overview-arch-02-pipelines.md
docs/01_overview-arch-02-pipelines.md`, or `git revert` the commit containing this move
if already committed. Coordinate any rollback with seq 12.

## Validation plan
- `git log --follow -- docs/01_overview/01_overview-arch-02-pipelines.md` shows
  continuous history through the move (Plan `AC-1`).
- Deferred to Phase 3: `uv run python tools/check_docs_structure.py "docs/**/*.md"
  --schema schemas/doc_front_matter.json` (Plan `AC-3`, `AC-4`, exercised together with
  seq 12's fix).

## Completion criteria
`docs/01_overview/01_overview-arch-02-pipelines.md` exists;
`docs/01_overview-arch-02-pipelines.md` no longer exists at the flat path; the move is
recorded as a Git rename.

## Out of scope
The 2 ADR link content fixes (seq 12); any other file's move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git mv docs/01_overview-arch-02-pipelines.md docs/01_overview/01_overview-arch-02-pipelines.md` | Completed | 20260924-132745 | 20260924-132745 | git mv succeeded as staged rename. |
| 2 | N/A: no test to add for a content-identical move | Completed | 20260924-132745 | 20260924-132745 | N/A: content-identical move, no test to add. |
| 3 | Confirm `git log --follow` continuity and staged rename status | Completed | 20260924-132745 | 20260924-132745 | git status confirms staged rename. Full git log --follow history continuity verification deferred until this change is committed. |
| 4 | N/A: no documentation update beyond the move itself | Completed | 20260924-132745 | 20260924-132745 | N/A: no documentation update beyond the move itself; full-tree validation deferred until this batch (seq01-05) plus the remaining seq06-13 rows are all complete. |

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
- **Requirement ID**: `REQ-001` (git mv the 10 overview files into `docs/01_overview/`)
- **Source issue**: issues/20260923-141038_docsreorg06_move-overview-docs-into-new-overview-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-130409_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-131808
- **Related target files**: docs/01_overview-arch-02-pipelines.md