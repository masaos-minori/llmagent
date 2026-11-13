## Goal

Remove `corpus_generation` from the `SearchDiagnostics` field sentence in the diagnostics
document (`REQ-010`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The field is named in the `SearchDiagnostics` field-definition sentence in
  `rag_03_03` (~line 41), which lists its fields including `corpus_generation`.

## Design decisions
- Drop `corpus_generation` from the enumerated field list; keep the other fields.

## Alternatives considered
N/A: removal is the decided Option B; keeping the name would describe a removed field.

## Implementation
### Target file
`docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md`
### Procedure
- Remove `, `corpus_generation`` from the `SearchDiagnostics` field sentence (~line 41),
  leaving `embed_ok`/`embed_failed`/`fts_errors`/`degraded` and `fallback_reason`.
### Method
Single-list-item deletion; confirm no `corpus_generation` remains in the document.
### Details
- Cross-reference `rag_04` (seq 19), which enumerates the same field.

## Compatibility considerations
N/A: documentation-only; the model field is removed by the sibling code document (seq 03).

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_generation" docs/21_rag docs/41_db` returns nothing once seq 16, 19, and 20
  land. The ADR-010 decision record legitimately names the field as removed (its Withdrawn
  bullet, seq 01) and is excluded from this search per the ADR preservation rule.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag` report no
  findings.

## Completion criteria
The diagnostics document lists no `corpus_generation` field; the RAG docs checkers pass.

## Out of Scope
The model field (`REQ-002`, seq 03) and the DTO doc (seq 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-095937 | 20261113-100523 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113-100523 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113-100523 | Documentation checkers only |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113-100523 |  |

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
- **Related target files**: `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md`