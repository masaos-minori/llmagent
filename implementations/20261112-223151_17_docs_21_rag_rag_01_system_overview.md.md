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
- Remove the identity-comparison sentence ("Divergence is detected: the corpus identity is
  computed ... before accepting a fallback") from the paragraph (~line 180); keep the
  configuration-divergence point that precedes it.
- Remove `corpus identity` from the Keywords list (~line 189).
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
- `rg -n "corpus identity" docs` returns nothing.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Documentation checkers only |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
