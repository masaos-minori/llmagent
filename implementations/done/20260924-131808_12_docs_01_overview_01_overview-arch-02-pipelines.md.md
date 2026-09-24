## Goal
Fix `docs/01_overview/01_overview-arch-02-pipelines.md`'s 2 relative links to
`docs/adr/ADR-001-workflow-engine-mandatory.md` and
`docs/adr/ADR-004-environment-failure-handling-policy.md`, both broken because those
files are now one directory level deeper than the bare `adr/ADR-...md` references
assumed, implementing `REQ-002`.

## Scope
In scope: the 2 relative-path strings `adr/ADR-001-workflow-engine-mandatory.md` →
`../adr/ADR-001-workflow-engine-mandatory.md` and
`adr/ADR-004-environment-failure-handling-policy.md` →
`../adr/ADR-004-environment-failure-handling-policy.md`. Out of scope: any other
content in this file; any other file (see seq 11/13 for the Plan's other 2 REQ-002
rows).

## Assumptions
- Both target ADR files exist and did not themselves move — confirmed via `ls
  docs/adr/ADR-001-workflow-engine-mandatory.md docs/adr/ADR-004-environment-failure-handling-policy.md`.
- `tools/check_docs_structure.py`'s `check_links()` resolves a `/`-containing link via
  plain `(path.parent / target).resolve()`, with no basename-index fallback — confirmed
  via Read.
- This row runs after seq 03 (this file's own `git mv`) has landed.

## Design decisions
None beyond the mechanical path-string fix, applied identically to both occurrences.

## Alternatives considered
Convert either link to a bare filename and rely on the basename index: rejected —
inconsistent with this file's existing relative-link style; out of scope for this row.

## Implementation
### Target file
`docs/01_overview/01_overview-arch-02-pipelines.md`

### Procedure
1. Locate the line `See [ADR-001](adr/ADR-001-workflow-engine-mandatory.md) for
   rationale and invariants.` and change the link target to
   `../adr/ADR-001-workflow-engine-mandatory.md`.
2. Locate the line `See [ADR-004](adr/ADR-004-environment-failure-handling-policy.md)
   for rationale, tradeoffs, and invariants.` and change the link target to
   `../adr/ADR-004-environment-failure-handling-policy.md`.

### Method
Two single-line text replacements, each targeting only its own link's target; no other
line in the file is touched.

### Details
Confirmed via `grep -n "adr/ADR-001-workflow-engine-mandatory.md\|adr/ADR-004-environment-failure-handling-policy.md"
docs/01_overview-arch-02-pipelines.md`: exactly one occurrence of each, on separate
lines.

## Compatibility considerations
N/A: relative-path string fixes with no behavioral surface beyond link resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout -- docs/01_overview/01_overview-arch-02-pipelines.md`, or
`git revert` the commit containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports either `broken link` finding for this
file (Plan `AC-4`).

## Completion criteria
Both links resolve to their respective `docs/adr/*.md` targets; no other content in
this file changed.

## Out of scope
Any other link or content in this file; any other REQ-002 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix both `adr/ADR-*.md` links to add the `../` prefix | Completed | 20260924-133359 | 20260924-133359 | Fixed both adr/ADR-001-workflow-engine-mandatory.md and adr/ADR-004-environment-failure-handling-policy.md links. |
| 2 | N/A: no test to add for a link-string fix | Completed | 20260924-133359 | 20260924-133359 | N/A: no test to add for a link-string fix. |
| 3 | Run `check_docs_structure.py` (see Validation plan) | Completed | 20260924-133359 | 20260924-133359 | check_docs_structure.py re-run across all 13 rows: both findings for this file are gone. |
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
- **Related target files**: docs/01_overview/01_overview-arch-02-pipelines.md