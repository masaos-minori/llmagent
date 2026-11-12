## Goal

Update the `SearchDiagnostics` entry in `docs/21_rag/rag_04_dto-models-types.md` to drop `fallback_reason` (a never-set field removed by this Plan) (REQ-006 / AC-6).

## Scope
**Release unit**: single-diagnostics-model

## Assumptions
- `rmcompat003` (`plans/done/20261112-120011_rmcompat003_rag-corpus-identity-decision.md`) has landed first: `corpus_generation` is already removed from the `SearchDiagnostics` entry (line 90). This procedure edits the post-`rmcompat003` text.
- `fallback_reason` is a stored-but-never-set field removed by this Plan's `models_result.py`/`diagnostics.py` edits.
- Documents state intent and failure behavior only, with no copied field table (`skills/DESIGN.md` Avoid implementation-reference duplication).

## Design decisions
- Keep the one-sentence entry; remove only the identifier for the removed key so it matches the surviving class.

## Implementation
### Target file
`docs/21_rag/rag_04_dto-models-types.md`

### Procedure
1. Verify `rmcompat003` has landed (precondition below).
2. Remove `fallback_reason` from the `SearchDiagnostics` entry.

### Method
Edit the markdown in place; no structural change.

### Details
- **Precondition (do not skip):** confirm `corpus_generation` no longer appears in the `SearchDiagnostics` entry (line 90). If it is still present, `rmcompat003` has not landed; order it first.
- Current line 90 lists `(..., `degraded`), `fallback_reason`, and `corpus_generation``. After `rmcompat003` only `..., `fallback_reason`` remains; remove `, `fallback_reason`` so it reads `(..., `degraded`)`.

## Compatibility considerations
- The rest of the DTO document is unchanged.
- `rag_03_03` (this Plan's sibling doc) makes the matching diagnostics edit.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Revert the commit; the edit is a one-line deletion.

## Validation plan
- `rg -n "fallback_reason" docs/21_rag/rag_04_dto-models-types.md` returns nothing.
- Docs checkers: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag` report no findings (AC-6).

## Completion criteria
`fallback_reason` is gone from the `SearchDiagnostics` entry; the document matches the code; the rag-domain docs checkers pass.

## Out of Scope
`corpus_generation` (`rmcompat003`), the diagnostics doc `rag_03_03` (sibling doc), and comment sweeping (`rmcompat007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: REQ-006 (DTO doc states the shape at the level of intent)
- **Source issue**: issues/20261110-170709_rmcompat002_rag-diagnostics-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120425_rmcompat002_rag-diagnostics-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-070042
- **Related target files**: docs/21_rag/rag_04_dto-models-types.md
