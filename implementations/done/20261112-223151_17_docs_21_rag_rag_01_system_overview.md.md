## Goal

Remove the stale identity-comparison paragraph and the `corpus identity` keyword from the RAG
system overview document (`REQ-010`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The identity-comparison description lives in the `RagPipeline` interaction note
  (~line 180): it explains how the `augment()` fallback compares remote vs local identity.
- The `corpus identity` keyword appears in the Keywords list (~line 189).

## Design decisions
- Delete the identity-comparison clause from the paragraph; remove the keyword entry. Keep
  the rest of the paragraph (configuration risk / divergence detection) where it stands on
  its own, or trim it to the configuration-risk point.

## Alternatives considered
N/A: removal is the decided Option B; leaving the wording would contradict REQ-010.

## Implementation
### Target file
`docs/21_rag/rag_01_system_overview.md`
### Procedure
- Remove the whole identity clause from the Note paragraph (line 180): from "Divergence is
  detected: the corpus identity is computed ..." through "... recording the unverifiable
  state." Verified: this clause names `rag_identity_mismatch_policy`, which is now a
  rejected config key (`scripts/shared/config_validator.py:96`), so the entire clause is
  dead wording. Keep the preceding configuration-risk sentence and the following "The startup
  RAG index consistency check additionally reports ..." sentence.
- Remove `corpus identity` from the Keywords list (line 189).
### Method
Two localized deletions; confirm no `corpus identity` or identity-comparison wording remains.
### Details
- Re-read before editing; line numbers shift as earlier edits land.

## Compatibility considerations
N/A: documentation-only; the compared identity is removed by the sibling code documents.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus identity" docs/21_rag` returns nothing (AC-10 scope: the five target docs).
  Verified remaining hits elsewhere are preserved historical text in `docs/10_adr/adr_02_06_010_rag-fallback.md`
  (lines 76, 160) and a decision-ledger entry in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
  (line 212); neither is in the Plan's frozen target table and neither is edited here.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag` report no
  findings.

## Completion criteria
The overview names no identity comparison and lists no `corpus identity` keyword; the RAG
docs checkers pass.

## Out of Scope
The startup warnings (`REQ-009`, seq 15) and the consistency-checks doc (seq 16).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261113 | cycle G 20261113 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113 | cycle G 20261113 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113 | Documentation checkers only cycle G 20261113 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113 | cycle G 20261113 |

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
- **Requirement ID**: `REQ-010`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `docs/21_rag/rag_01_system_overview.md`