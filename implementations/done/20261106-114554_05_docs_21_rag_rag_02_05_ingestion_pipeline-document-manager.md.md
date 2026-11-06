## Goal

Update the existing-document-handling description in the document-manager doc so it states that `etag`/`last_modified`/`fetched_at` are refreshed only by the commit-transaction insert, under the `ETagManager` guard (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit (Plan step 3 is outside the `etag-atomic-fix` Phases 1-2)

## Assumptions

- Only the ordering/ownership sentence at line 36 changes; the surrounding skip/replace semantics stay as written.

## Design decisions

- Describe the commit-boundary design (resolve inside `begin_immediate()`, insert carries resolved values) rather than the current pre-commit refresh.

## Alternatives considered

N/A: single-sentence documentation update.

## Implementation
### Target file
`docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`
### Procedure

- Replace "otherwise the ETag fields are refreshed and the chunks are replaced" (line 36) with wording that: the freshness fields are refreshed by the document re-insert inside the same transaction that deletes and re-creates the document and its chunks; a stale incoming payload keeps the stored values; a failed re-ingestion leaves both chunks and freshness unchanged.

### Method

- Keep the sentence's bullet structure and length comparable; do not add implementation detail beyond behavior description (`skills/DESIGN.md` Docs content policy).

### Details

- `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` §4.9 stays semantically correct (no change here); add `resolve_incoming` only if the implementation changes the documented API surface (Plan Documentation Impact).

## Compatibility considerations

N/A: prose-only change; matches the behavior introduced by sibling procedures 01-03.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Check | Command |
|---|---|
| Docs structural rules | `uv run python tools/check_docs_quality.py` |
| Docs structure | `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md` |
| Docs content policy | `uv run python tools/check_docs_content_policy.py` |
| Domain claim consistency | `uv run python tools/check_docs_consistency.py --domain rag` |

## Completion criteria

- AC-5: the doc describes the commit-boundary ordering and the guard applied at insert; all four docs checkers pass.

## Out of Scope

- `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` (semantics preserved unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the ETag refresh-ordering description per Procedure | Completed | 2026-11-06 | 2026-11-06 | Execute after sibling procedures 01-03 land so the doc describes shipped behavior Line 36 replaced per Procedure; correction: line 30 intro also updated (DocumentManager no longer performs ETag refresh after sibling 01); rag_02_06 4.9 gained Resolution Mode bullet because resolve_incoming changed the documented API surface (Details conditional satisfied) |
| 2 | Run the docs checkers in the Validation plan | Completed | 2026-11-06 | 2026-11-06 | `routing.md` Tools "When to run which tool" check_docs_quality / check_docs_structure (both files) / check_docs_content_policy / check_docs_consistency --domain rag all pass |

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
- **Requirement ID**: `REQ-005` (doc description of commit-boundary ETag refresh)
- **Source issue**: `issues/20261106-073538_raging002_etag-updated-before-reingestion.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094942_raging002_etag-updated-before-reingestion.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-114554
- **Related target files**: `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`