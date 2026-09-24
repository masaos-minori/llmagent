## Goal
Fix `docs/03_rag_05_1-configuration-reference.md`'s anchor-suffixed relative link to
the moved `docs/90_deployment/02_deployment.md`, broken because that file is now one
directory level deeper than the bare `./02_deployment.md` reference assumed,
implementing `REQ-002`. This row was discovered during Phase 3 verification, not this
Plan's original Design search (whose regex missed anchor-suffixed links) — see the
Plan's Design section for the methodology gap.

## Scope
In scope: the single relative-path string `./02_deployment.md` (with anchor
`#14-llm--How to get models`) → `./90_deployment/02_deployment.md` (same anchor
preserved). Out of scope: any other content in this file; any other REQ-002 file (see
seq 02/03/04/05).

## Assumptions
- `docs/90_deployment/02_deployment.md` exists at this new location (moved by this
  same Plan's seq 01) — confirmed via `ls`.
- `tools/check_docs_structure.py`'s `LINK_RE`
  (`\[([^\]]+)\]\(([^)]+\.md)(?:#[^)]*)?\)`) captures the link target up to `.md`,
  tolerating an optional `#anchor` suffix, then resolves a `/`-containing target via
  plain `(path.parent / target).resolve()` with no basename-index fallback — confirmed
  via Read — so this is a genuine break, not a tool false-positive.
- This row runs after seq 01 (the file's own `git mv`) has landed.

## Design decisions
None beyond the mechanical path-string fix — the anchor text itself is preserved
unchanged since it addresses a section within the target document, unaffected by the
document's own relocation.

## Alternatives considered
Convert to a bare filename and rely on the basename index instead of a relative path:
rejected — inconsistent with this file's existing relative-link style; out of scope for
this row.

## Implementation
### Target file
`docs/03_rag_05_1-configuration-reference.md`

### Procedure
1. Locate the line containing
   `[docs/02_deployment.md section 1.4](./02_deployment.md#14-llm--How to get models)`.
2. Change the link target from `./02_deployment.md#14-llm--How to get models` to
   `./90_deployment/02_deployment.md#14-llm--How to get models`, leaving the anchor
   text and the link's visible label unchanged.

### Method
Single-line text replacement targeting only the path component of the one link target
(before the `#`); no other line in the file is touched.

### Details
Confirmed via `grep -n "02_deployment"
docs/03_rag_05_1-configuration-reference.md`: exactly one occurrence in the whole
file.

## Compatibility considerations
N/A: a single relative-path string fix with no behavioral surface beyond link
resolution; the anchor itself is unaffected by the path change.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout -- docs/03_rag_05_1-configuration-reference.md`, or `git
revert` the commit containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports a `broken link` finding for this file
(Plan `AC-3`).

## Completion criteria
The link resolves to `docs/90_deployment/02_deployment.md` (anchor preserved); no
other content in this file changed.

## Out of scope
Any other link or content in this file; any other REQ-002 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the `./02_deployment.md` link to `./90_deployment/02_deployment.md` (anchor preserved) | Completed | 20260924-135642 | 20260924-135642 | Fixed ./02_deployment.md link (anchor preserved) to ./90_deployment/02_deployment.md. |
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
- **Source plan**: plans/done/20260924-133825_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-134638
- **Related target files**: docs/03_rag_05_1-configuration-reference.md