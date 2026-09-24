## Goal
Fix `docs/90_deployment/02_deployment.md`'s relative link to
`docs/adr/ADR-001-workflow-engine-mandatory.md`, broken because that file is now one
directory level deeper than the bare `adr/ADR-001-workflow-engine-mandatory.md`
reference assumed, implementing `REQ-002`.

## Scope
In scope: the single relative-path string `adr/ADR-001-workflow-engine-mandatory.md`
→ `../adr/ADR-001-workflow-engine-mandatory.md`. Out of scope: any other content in
this file; any other file (see seq 03/04/05 for the Plan's other 3 REQ-002 rows).

## Assumptions
- `docs/adr/ADR-001-workflow-engine-mandatory.md` exists and did not itself move —
  confirmed via `ls docs/adr/ADR-001-workflow-engine-mandatory.md`.
- `tools/check_docs_structure.py`'s `check_links()` resolves a `/`-containing link via
  plain `(path.parent / target).resolve()`, with no basename-index fallback — confirmed
  via Read — so this is a genuine break, not a tool false-positive.
- This row runs after seq 01 (this file's own `git mv`) has landed.

## Design decisions
None beyond the mechanical path-string fix.

## Alternatives considered
Convert to a bare filename and rely on the basename index instead of a relative path:
rejected — inconsistent with this file's existing relative-link style; out of scope for
this row (a repository-wide link-convention change).

## Implementation
### Target file
`docs/90_deployment/02_deployment.md`

### Procedure
1. Locate the line containing
   `[ADR-001](adr/ADR-001-workflow-engine-mandatory.md)`.
2. Change the link target to `../adr/ADR-001-workflow-engine-mandatory.md`.

### Method
Single-line text replacement targeting only the one link target; no other line in the
file is touched.

### Details
Confirmed via `grep -n "adr/ADR-001-workflow-engine-mandatory.md"
docs/02_deployment.md`: exactly one occurrence.

## Compatibility considerations
N/A: a single relative-path string fix with no behavioral surface beyond link
resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout -- docs/90_deployment/02_deployment.md`, or `git revert` the
commit containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports a `broken link` finding for this file
(Plan `AC-3`).

## Completion criteria
The link resolves to `docs/adr/ADR-001-workflow-engine-mandatory.md`; no other content
in this file changed.

## Out of scope
Any other link or content in this file; any other REQ-002 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the `adr/ADR-001-workflow-engine-mandatory.md` link to `../adr/ADR-001-workflow-engine-mandatory.md` | Completed | 20260924-135642 | 20260924-135642 | Fixed adr/ADR-001-workflow-engine-mandatory.md link to ../adr/ADR-001-workflow-engine-mandatory.md. |
| 2 | N/A: no test to add for a link-string fix | Completed | 20260924-135642 | 20260924-135642 | N/A: no test to add for a link-string fix. |
| 3 | Run `check_docs_structure.py` (see Validation plan) | Completed | 20260924-135642 | 20260924-135642 | check_docs_structure.py re-run across all 6 rows: the finding(s) for this file are gone (before/after diff confirmed); check_docs_quality.py exit 0 no ERROR; check_docs_consistency.py --domain deployment exit 0, only pre-existing best-effort WARNINGs; scoped pre-commit passes except the known pre-existing adr-invariant-matrix/adr-reference-scoped gap, no unrelated files touched. |
| 4 | N/A: no further documentation update | Completed | 20260924-135642 | 20260924-135642 | N/A: no further documentation update. |

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
- **Source issue**: issues/20260923-141102_docsreorg07_move-deployment-doc-into-new-deployment-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-133825_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-134638
- **Related target files**: docs/90_deployment/02_deployment.md