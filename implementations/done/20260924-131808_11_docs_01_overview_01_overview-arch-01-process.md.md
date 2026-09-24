## Goal
Fix `docs/01_overview/01_overview-arch-01-process.md`'s relative link to
`docs/adr/ADR-002-config-isolation.md`, broken because that file is now one directory
level deeper than the bare `adr/ADR-002-config-isolation.md` reference assumed,
implementing `REQ-002`.

## Scope
In scope: the single relative-path string `adr/ADR-002-config-isolation.md` →
`../adr/ADR-002-config-isolation.md`. Out of scope: any other content in this file
(including the adjacent `90_shared_03_01_runtime_and_execution-config-and-logging.md`
link on the same line, a same-directory bare filename that needs no change); any other
file (see seq 12/13 for the Plan's other 2 REQ-002 rows).

## Assumptions
- `docs/adr/ADR-002-config-isolation.md` exists and did not itself move — confirmed via
  `ls docs/adr/ADR-002-config-isolation.md`.
- `tools/check_docs_structure.py`'s `check_links()` resolves a `/`-containing link via
  plain `(path.parent / target).resolve()`, with no basename-index fallback — confirmed
  via Read — so this is a genuine break, not a tool false-positive.
- This row runs after seq 02 (this file's own `git mv`) has landed.

## Design decisions
None beyond the mechanical path-string fix.

## Alternatives considered
Convert to a bare filename and rely on the basename index instead of a relative path:
rejected — inconsistent with this file's existing relative-link style; out of scope for
this row (a repository-wide link-convention change).

## Implementation
### Target file
`docs/01_overview/01_overview-arch-01-process.md`

### Procedure
1. Locate the line containing `[ADR-002](adr/ADR-002-config-isolation.md)`.
2. Change the link target to `../adr/ADR-002-config-isolation.md`, leaving the rest of
   the line (including the adjacent same-directory link on the same line) unchanged.

### Method
Single-line text replacement targeting only the one link target; no other line in the
file is touched.

### Details
Confirmed via `grep -n "adr/ADR-002-config-isolation.md"
docs/01_overview-arch-01-process.md`: exactly one occurrence, on a line that also
contains a second, same-directory link (`90_shared_03_01_runtime_and_execution-config-and-logging.md`)
which must be left unchanged.

## Compatibility considerations
N/A: a single relative-path string fix with no behavioral surface beyond link
resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout -- docs/01_overview/01_overview-arch-01-process.md`, or `git
revert` the commit containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports a `broken link` finding for this file
(Plan `AC-4`).

## Completion criteria
The link resolves to `docs/adr/ADR-002-config-isolation.md`; no other content in this
file changed.

## Out of scope
Any other link or content in this file; any other REQ-002 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the `adr/ADR-002-config-isolation.md` link to `../adr/ADR-002-config-isolation.md` | Completed | 20260924-133359 | 20260924-133359 | Fixed adr/ADR-002-config-isolation.md link to ../adr/ADR-002-config-isolation.md. |
| 2 | N/A: no test to add for a link-string fix | Completed | 20260924-133359 | 20260924-133359 | N/A: no test to add for a link-string fix. |
| 3 | Run `check_docs_structure.py` (see Validation plan) | Completed | 20260924-133359 | 20260924-133359 | check_docs_structure.py re-run across all 13 rows: the ADR-002 finding for this file is gone; only pre-existing, unrelated findings remain. |
| 4 | N/A: no further documentation update | Completed | 20260924-133359 | 20260924-133359 | N/A: no further documentation update. |

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
- **Requirement ID**: `REQ-002` (fix relative-path references broken by the move)
- **Source issue**: issues/20260923-141038_docsreorg06_move-overview-docs-into-new-overview-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-130409_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-131808
- **Related target files**: docs/01_overview/01_overview-arch-01-process.md