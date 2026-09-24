## Goal
Fix `docs/adr/ADR-015-reference-document-class-disposition.md`'s relative link to the
moved `docs/00_governance/00_governance_01_documentation-policy.md`, in both its front
matter `related` field and its body `## Related Documents` link, implementing
`REQ-005`.

## Scope
In scope: the front matter `related` field's entry
`../00_governance_01_documentation-policy.md` and the body link with the same target —
both become `../00_governance/00_governance_01_documentation-policy.md`. Out of scope:
any other content in this file; any other REQ-005 file.

## Assumptions
- `docs/00_governance/00_governance_01_documentation-policy.md` exists at this new
  location (moved by this same Plan's seq 01) — confirmed via `ls`.
- `tools/check_docs_structure.py`'s `check_related_links()` resolves a
  `/`-containing front matter entry via plain `(path.parent / entry).resolve()`, with
  no basename-index fallback — confirmed via Read — the same mechanism as
  `check_links()` for body links.

## Design decisions
None beyond the mechanical path-string fix, applied identically in both locations
(front matter and body) since both cite the exact same target file.

## Alternatives considered
Convert to a bare filename in either location: rejected — inconsistent with this file's
existing relative-link style; out of scope for this row (a repository-wide
link-convention change).

## Implementation
### Target file
`docs/adr/ADR-015-reference-document-class-disposition.md`

### Procedure
1. In the front matter block, change the `related` field's entry
   `../00_governance_01_documentation-policy.md` to
   `../00_governance/00_governance_01_documentation-policy.md`.
2. In the body, locate the line
   `[Documentation Policy](../00_governance_01_documentation-policy.md)` under
   `## Related Documents` and change the link target to
   `../00_governance/00_governance_01_documentation-policy.md`.

### Method
Two single-line text replacements (front matter entry, body link) targeting the same
underlying file reference; no other line in the file is touched.

### Details
Confirmed via `grep -n "00_governance_01_documentation-policy.md"
docs/adr/ADR-015-reference-document-class-disposition.md`: exactly 2 occurrences (one
in front matter, one in the body), both requiring the same fix.

## Compatibility considerations
N/A: a relative-path string fix with no behavioral surface beyond link/front-matter
resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout --
docs/adr/ADR-015-reference-document-class-disposition.md`, or `git revert` the commit
containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports either the `broken link` finding or
the `front matter references missing file` finding for this file (Plan `AC-7`).

## Completion criteria
Both the front matter `related` entry and the body link resolve to
`docs/00_governance/00_governance_01_documentation-policy.md`; no other content in this
file changed.

## Out of scope
Any other front matter field or body content in this file; any other REQ-005 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the front matter `related` entry and the body link to add the `00_governance/` directory component | Completed | 20260924-124616 | 20260924-124616 | Fixed front matter related field and body link to ../00_governance/00_governance_01_...md. |
| 2 | N/A: no test to add for a link-string fix | Completed | 20260924-124616 | 20260924-124616 | N/A: no test to add for a link-string fix. |
| 3 | Run `check_docs_structure.py` (see Validation plan) | Completed | 20260924-124616 | 20260924-124616 | uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json re-run: the finding(s) for this file are gone (verified via before/after diff across all 11 REQ-005 files together: 17 findings resolved, only pre-existing size-limit findings remain). |
| 4 | N/A: no further documentation update | Completed | 20260924-124616 | 20260924-124616 | N/A: no further documentation update. |

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
- **Requirement ID**: `REQ-005` (fix relative-path references broken by the move)
- **Source issue**: issues/20260923-140944_docsreorg05_move-governance-docs-into-new-governance-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20260924-115855_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121124
- **Related target files**: docs/adr/ADR-015-reference-document-class-disposition.md