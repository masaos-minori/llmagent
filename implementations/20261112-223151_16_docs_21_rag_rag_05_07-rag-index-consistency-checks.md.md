## Goal

Remove the unverifiable-corpus-generation fatal class and all identity wording from the RAG
index consistency-checks document (`REQ-010`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The class appears in four places: the Fatal-findings bullet, the CRITICAL example code
  block, the Severity Classes table Fatal row, and the findings table row.
- Identity wording appears in the "A failed or timed-out check" bullet (the
  `corpus_generation` diagnostic sentence and the `identity-unverified` reference).

## Design decisions
- Drop the five class references and the identity sentence; keep every other fatal/degraded
  finding and the surrounding structure intact.

## Alternatives considered
N/A: removal is the decided Option B; leaving the wording would contradict REQ-010 and
AC-9 (`identity-unverified` must not appear in docs).

## Implementation
### Target file
`docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
### Procedure
- Remove `unverifiable corpus generation` from the Fatal-findings bullet (~line 25).
- Remove the `[CRITICAL] Unverifiable corpus generation detected ...` example code block
  (~lines 31-33).
- Remove `unverifiable corpus generation` from the Severity Classes table Fatal row (~line
  45).
- Remove the `unverifiable corpus generation` row from the findings table (~line 103).
- Drop the identity sentence in the "A failed or timed-out check" bullet that references the
  corpus identity and `corpus_generation` (~line 26); reword the remaining clause so no
  `identity-unverified` wording stays.
### Method
Five localized deletions plus one reword; confirm no `identity-unverified`,
`corpus_generation`, or `corpus_meta_verified` remains.
### Details
- Re-read before editing: a sibling procedure edits the same document's sentences.

## Compatibility considerations
N/A: documentation-only; the runtime class is removed by the sibling code documents (seq 10,
11).

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "identity-unverified" docs` returns nothing.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag` report no
  findings.

## Completion criteria
The document names no unverifiable-generation class and no identity wording; the RAG docs
checkers pass.

## Out of Scope
The startup warning prefix (`REQ-009`, seq 15) and the consistency class (seq 11).

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
- **Related target files**: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
