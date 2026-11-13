## Goal

Update `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md` to match the narrowed diagnostics shape: drop `fallback_reason` from the `SearchDiagnostics` field sentence (section 4.2) and the fetch-hit-counts key from the `get_diagnostics()` key groups (section 4.3) (REQ-006 / AC-6).

## Scope
**Release unit**: single-diagnostics-model

## Assumptions
- `rmcompat003` (`plans/done/20261112-120011_rmcompat003_rag-corpus-identity-decision.md`) has landed first: the corpus-identity counter is already removed from the section 4.2 field sentence. This procedure edits the post-`rmcompat003` text.
- `fallback_reason` is a never-set field being removed by this Plan's `models_result.py`/`diagnostics.py` edits; the fetch-hit-counts key repeats `fetch_result.hits` and is dropped from `to_dict()`.
- Documents state intent and failure behavior only, with no copied field table (`skills/DESIGN.md` Avoid implementation-reference duplication).

## Design decisions
- Keep the two sentences at the level of intent; remove only the identifiers for the removed keys so the doc matches the code without re-summarizing the whole shape.

## Implementation
### Target file
`docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md`

### Procedure
1. Verify `rmcompat003` has landed (precondition below).
2. Remove `fallback_reason` from the section 4.2 field sentence.
3. Remove the fetch-hit-counts key from the section 4.3 key groups.

### Method
Edit the markdown in place; no structural change.

### Details
- **Precondition (do not skip):** confirm the corpus-identity counter no longer appears in the section 4.2 sentence (line 41). If it is still present, `rmcompat003` has not landed; order it first.
- Section 4.2 (current line 41): after `rmcompat003` the sentence lists `(..., `degraded`), `fallback_reason``. Remove `, `fallback_reason`` so it reads `(..., `degraded`)`.
- Section 4.3 (current line 45): the key list contains `` , the fetch-hit-counts key, and the `search_diagnostics` summary ``. Remove the fetch-hit-counts key so the list flows `... refiner counters (see [rag_03_05...]), and the `search_diagnostics` summary including `degraded`.`

## Compatibility considerations
- The rest of the document (the `fetch_result` note, the "safe to call before run()" paragraph) is unchanged.
- `rag_04` (this Plan's sibling doc) makes the matching edit to its `SearchDiagnostics` entry.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Revert the commit; the edits are one-line deletions.

## Validation plan
- The removed keys (`fallback_reason` in section 4.2, the fetch-hit-counts key in section 4.3) no longer appear in the doc.
- Docs checkers: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag` report no findings (AC-6).

## Completion criteria
`fallback_reason` is gone from section 4.2 and the fetch-hit-counts key from section 4.3; the documents match the code; the rag-domain docs checkers pass.

## Out of Scope
the corpus-identity counter (`rmcompat003`), the DTO entry in `rag_04` (sibling doc), and comment sweeping (`rmcompat007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-160336 | 20261113-160336 | PROC-05 applied: section 4.2 dropped SearchDiagnostics.fallback_reason (confirmed absent from models_result.py); section 4.3 dropped fetch-hit-counts key. Line 51 StageResult.fallback_reason left intact (real field, out of scope). Stale detector clean after rewording bare symbols to descriptive phrases. |
| 2 | Add or update tests per Validation plan | Completed | 20261113-160336 | 20261113-160336 | N/A: docs-only change; no tests. Validation = 4 rag docs checkers. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-160336 | 20261113-160336 | check_docs_quality/structure/content_policy(--strict)/consistency(--domain rag): all No issues found. Gated on end-of-unit full suite. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-160336 | 20261113-160336 | Doc updated per AC-6 (section-specific): fallback_reason gone from 4.2, fetch-hit-counts key gone from 4.3. rag-domain docs checkers pass. |

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
- **Requirement ID**: REQ-006 (diagnostics doc states the shape at the level of intent)
- **Source issue**: issues/20261110-170709_rmcompat002_rag-diagnostics-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120425_rmcompat002_rag-diagnostics-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-070042
- **Related target files**: docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md