## Goal
Fix `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`'s relative link to
the moved `docs/00_governance/00_governance_03_issue-and-uncertainty-management.md`,
implementing `REQ-005`. Same fix class as seq 12.

## Scope
In scope: the single relative-path string
`../00_governance_03_issue-and-uncertainty-management.md` →
`../00_governance/00_governance_03_issue-and-uncertainty-management.md`. Out of scope:
any other content in this file; any other REQ-005 file.

## Assumptions
Same as seq 12: the target file exists at its new location; `check_docs_structure.py`
has no basename-index fallback for `/`-containing links.

## Design decisions
None beyond the mechanical path-string fix.

## Alternatives considered
Same as seq 12 — converting to a bare filename is rejected as inconsistent with this
file's existing link style and out of scope.

## Implementation
### Target file
`docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`

### Procedure
1. Locate the line
   `[Issue and Uncertainty Management](../00_governance_03_issue-and-uncertainty-management.md)`.
2. Change the link target to
   `../00_governance/00_governance_03_issue-and-uncertainty-management.md`.

### Method
Single-line text replacement; no other line in the file is touched.

### Details
Confirmed via `grep -n "00_governance_03_issue-and-uncertainty-management.md"
docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`: exactly one occurrence.

## Compatibility considerations
N/A: a single relative-path string fix with no behavioral surface beyond link
resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout --
docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`, or `git revert` the
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
| 1 | Fix the relative link to add the `00_governance/` directory component | Completed | 20260924-124616 | 20260924-124616 | Same fix as ADR-003. |
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
- **Related target files**: docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md