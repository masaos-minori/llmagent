## Goal
Fix `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`'s relative link to
the moved `docs/00_governance/00_governance_03_issue-and-uncertainty-management.md`,
broken because that target file is now one directory level deeper than the
`../00_governance_03_issue-and-uncertainty-management.md` reference assumed,
implementing `REQ-005`.

## Scope
In scope: the single relative-path string
`../00_governance_03_issue-and-uncertainty-management.md` →
`../00_governance/00_governance_03_issue-and-uncertainty-management.md`. Out of scope:
any other content in this file; any other file (see the Plan's other 10 REQ-005
implementation procedure documents for those rows).

## Assumptions
`docs/00_governance/00_governance_03_issue-and-uncertainty-management.md` exists at
this new location (moved by this same Plan's seq 03) — confirmed via `ls`.
`tools/check_docs_structure.py` resolves a `/`-containing link via plain
`(path.parent / target).resolve()`, with no basename-index fallback — confirmed via
Read.

## Design decisions
None beyond the mechanical path-string fix.

## Alternatives considered
Convert to a bare filename and rely on the basename index instead of a relative path:
rejected — inconsistent with this file's existing relative-link style; out of scope for
this row (a repository-wide link-convention change).

## Implementation
### Target file
`docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`

### Procedure
1. Locate the line
   `[Issue and Uncertainty Management](../00_governance_03_issue-and-uncertainty-management.md)`.
2. Change the link target to
   `../00_governance/00_governance_03_issue-and-uncertainty-management.md`.

### Method
Single-line text replacement; no other line in the file is touched.

### Details
Confirmed via `grep -n "00_governance_03_issue-and-uncertainty-management.md"
docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`: exactly one occurrence.

## Compatibility considerations
N/A: a single relative-path string fix with no behavioral surface beyond link
resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout --
docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`, or `git revert` the
commit containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports a `broken link` finding for this file
(Plan `AC-7`).

## Completion criteria
The link resolves to
`docs/00_governance/00_governance_03_issue-and-uncertainty-management.md`; no other
content in this file changed.

## Out of scope
Any other link or content in this file; any other REQ-005 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the relative link to add the `00_governance/` directory component | Completed | 20260924-124616 | 20260924-124616 | Fixed ../00_governance_03_...md link to ../00_governance/00_governance_03_...md. |
| 2 | N/A: no test to add for a single link-string fix | Completed | 20260924-124616 | 20260924-124616 | N/A: no test to add for a link-string fix. |
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
- **Related target files**: docs/adr/ADR-003-runtime-tool-registry-routing-authority.md