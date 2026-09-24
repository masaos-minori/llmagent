## Goal
Fix `docs/adr/ADR-004-environment-failure-handling-policy.md`'s relative link to the
moved `docs/90_deployment/02_deployment.md`, implementing `REQ-002`. Same fix class as
seq 03.

## Scope
In scope: the single relative-path string `../02_deployment.md` →
`../90_deployment/02_deployment.md`. Out of scope: any other content in this file; any
other file (see seq 02/03/05 for the Plan's other 3 REQ-002 rows).

## Assumptions
Same as seq 03: the target file exists at its new location; `check_docs_structure.py`
has no basename-index fallback for `/`-containing links.

## Design decisions
None beyond the mechanical path-string fix.

## Alternatives considered
Same as seq 03 — converting to a bare filename is rejected as inconsistent with this
file's existing link style and out of scope.

## Implementation
### Target file
`docs/adr/ADR-004-environment-failure-handling-policy.md`

### Procedure
1. Locate the line `- [Deployment Guide](../02_deployment.md) — デプロイメント時のワークフロー検証`.
2. Change the link target to `../90_deployment/02_deployment.md`.

### Method
Single-line text replacement targeting only the one link target; no other line in the
file is touched.

### Details
Confirmed via `grep -n "\.\./02_deployment\.md"
docs/adr/ADR-004-environment-failure-handling-policy.md`: exactly one occurrence
(line 588).

## Compatibility considerations
N/A: a single relative-path string fix with no behavioral surface beyond link
resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout -- docs/adr/ADR-004-environment-failure-handling-policy.md`,
or `git revert` the commit containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports a `broken link` finding for this file
(Plan `AC-3`).

## Completion criteria
The link resolves to `docs/90_deployment/02_deployment.md`; no other content in this
file changed.

## Out of scope
Any other link or content in this file; any other REQ-002 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the `../02_deployment.md` link to `../90_deployment/02_deployment.md` | Completed | 20260924-135642 | 20260924-135642 | Fixed ../02_deployment.md link to ../90_deployment/02_deployment.md. |
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
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md