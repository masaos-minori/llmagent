## Goal
Fix `docs/adr/ADR-008-sqlite-4db-separation.md`'s 2 relative links to the moved
`docs/00_governance/00_governance_03_issue-and-uncertainty-management.md`, implementing
`REQ-005`. Same fix class as seq 12, applied to both of this file's occurrences.

## Scope
In scope: both occurrences of the relative-path string
`../00_governance_03_issue-and-uncertainty-management.md` →
`../00_governance/00_governance_03_issue-and-uncertainty-management.md`. Out of scope:
any other content in this file (including its own pre-existing, unrelated broken links
to `03_rag_04_02_rag-persistence.md`, `03_rag_04_03_rag-recovery.md`,
`05_agent_04_01_agent-session-persistence.md`, and its size-limit finding — all
confirmed pre-existing and unrelated to this Plan); any other REQ-005 file.

## Assumptions
Same as seq 12: the target file exists at its new location; `check_docs_structure.py`
has no basename-index fallback for `/`-containing links. This file's other broken-link
findings (the 3 RAG/agent doc references, plus its size-limit finding) are confirmed
pre-existing via `check_docs_structure.py`'s own output — none reference the 5 moved
governance files, and none are new as a result of this Plan.

## Design decisions
None beyond the mechanical path-string fix, applied identically to both occurrences.

## Alternatives considered
Same as seq 12 — converting to a bare filename is rejected as inconsistent with this
file's existing link style and out of scope.

## Implementation
### Target file
`docs/adr/ADR-008-sqlite-4db-separation.md`

### Procedure
1. Locate both lines containing
   `[Issue and Uncertainty Management](../00_governance_03_issue-and-uncertainty-management.md)`
   (one per bullet, adjacent lines).
2. Change both link targets to
   `../00_governance/00_governance_03_issue-and-uncertainty-management.md`.

### Method
Two single-line text replacements (identical target string, two separate source
lines); no other line in the file is touched.

### Details
Confirmed via `grep -c "00_governance_03_issue-and-uncertainty-management.md"
docs/adr/ADR-008-sqlite-4db-separation.md`: exactly 2 occurrences, both requiring the
same fix. This file's other, pre-existing broken-link findings (RAG/agent doc
references, size-limit) are explicitly out of scope for this row (see Scope).

## Compatibility considerations
N/A: a relative-path string fix with no behavioral surface beyond link resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout -- docs/adr/ADR-008-sqlite-4db-separation.md`, or `git revert`
the commit containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports either of the 2
`00_governance_03_issue-and-uncertainty-management.md`-related `broken link` findings
for this file (its other, pre-existing, unrelated findings remain and are out of scope)
(Plan `AC-7`).

## Completion criteria
Both links resolve to
`docs/00_governance/00_governance_03_issue-and-uncertainty-management.md`; no other
content in this file changed.

## Out of scope
This file's pre-existing, unrelated broken-link and size-limit findings; any other
REQ-005 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix both relative links to add the `00_governance/` directory component | Completed | 20260924-124616 | 20260924-124616 | Same fix as ADR-003, applied to both of this file's 2 occurrences. |
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
- **Related target files**: docs/adr/ADR-008-sqlite-4db-separation.md