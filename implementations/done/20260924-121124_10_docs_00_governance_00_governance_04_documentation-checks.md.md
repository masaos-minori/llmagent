## Goal
Fix `docs/00_governance/00_governance_04_documentation-checks.md`'s outbound relative
link to `docs/adr/ADR-001-workflow-engine-mandatory.md`, broken by this file's own
`docsreorg05` move into `docs/00_governance/`, implementing `REQ-005`.

## Scope
In scope: the single relative-path string `adr/ADR-001-workflow-engine-mandatory.md` →
`../adr/ADR-001-workflow-engine-mandatory.md`. Out of scope: any other content in this
file; any other file (see the Plan's other 10 REQ-005 implementation procedure
documents for those rows).

## Assumptions
Same as seq 09 (`docs/00_governance/00_governance_02_documentation-metadata.md`):
`docs/adr/ADR-001-workflow-engine-mandatory.md` exists unmoved; `check_docs_structure.py`
has no basename-index fallback for `/`-containing links.

## Design decisions
None beyond the mechanical path-string fix.

## Alternatives considered
Same as seq 09 — converting to a bare filename is rejected as out of scope /
inconsistent with this file's existing link style.

## Implementation
### Target file
`docs/00_governance/00_governance_04_documentation-checks.md`

### Procedure
1. Locate the line `](adr/ADR-001-workflow-engine-mandatory.md)`.
2. Change it to `](../adr/ADR-001-workflow-engine-mandatory.md)`.

### Method
Single-line text replacement; no other line in the file is touched.

### Details
Confirmed via `grep -n "adr/ADR-001-workflow-engine-mandatory.md"
docs/00_governance/00_governance_04_documentation-checks.md`: exactly one occurrence.

## Compatibility considerations
N/A: a single relative-path string fix with no behavioral surface beyond link
resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout --
docs/00_governance/00_governance_04_documentation-checks.md`, or `git revert` the
commit containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports a `broken link` finding for this file
(Plan `AC-7`).

## Completion criteria
The link resolves to `docs/adr/ADR-001-workflow-engine-mandatory.md`; no other content
in this file changed.

## Out of scope
Any other link or content in this file; any other REQ-005 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the `adr/ADR-001-workflow-engine-mandatory.md` link to `../adr/ADR-001-workflow-engine-mandatory.md` | Completed | 20260924-124616 | 20260924-124616 | Fixed adr/ADR-001-workflow-engine-mandatory.md link to ../adr/ADR-001-workflow-engine-mandatory.md. |
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
- **Related target files**: docs/00_governance/00_governance_04_documentation-checks.md