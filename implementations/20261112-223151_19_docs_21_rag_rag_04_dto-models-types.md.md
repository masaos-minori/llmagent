## Goal

Remove `corpus_generation` from the `SearchDiagnostics` entry in the DTO types document
(`REQ-010`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The field is enumerated in the `SearchDiagnostics` definition (~line 90), which lists the
  local-execution counters, `fallback_reason`, and `corpus_generation`.

## Design decisions
- Drop `and `corpus_generation`` from the entry; keep the other enumerated fields.

## Alternatives considered
N/A: removal is the decided Option B; keeping the name would describe a removed field.

## Implementation
### Target file
`docs/21_rag/rag_04_dto-models-types.md`
### Procedure
- Remove `, and `corpus_generation`` from the `SearchDiagnostics` entry (~line 90).
### Method
Single-list-item deletion; confirm no `corpus_generation` remains in the document.
### Details
- Cross-reference `rag_03_03` (seq 18), which enumerates the same field.

## Compatibility considerations
N/A: documentation-only; the model field is removed by the sibling code document (seq 03).

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_generation" docs` returns nothing.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag` report no
  findings.

## Completion criteria
The DTO document lists no `corpus_generation` field; the RAG docs checkers pass.

## Out of Scope
The model field (`REQ-002`, seq 03) and the diagnostics doc (seq 18).

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
- **Related target files**: `docs/21_rag/rag_04_dto-models-types.md`
