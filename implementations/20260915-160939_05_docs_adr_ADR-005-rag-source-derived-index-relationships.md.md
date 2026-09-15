## Goal
Remove ADR-005's redundant file/class/config/test list from `## Implementation
Notes` once reconciled into `### Implementation References`, per `REQ-005` —
including correcting a wrong class/file citation found in References during
adversarial verification.

## Scope
- In scope: correct References' `scripts/rag/repository.py` —
  `RagRepository.delete_existing_document()`/`RagRepository.delete_document(url)`
  entry (confirmed wrong — `RagRepository` has no delete method) to
  `scripts/rag/ingestion/document_manager.py` —
  `DocumentManager.delete_existing_document()`, `delete_document_chain()`; delete
  the Notes list; insert the one-line pointer.
- Out of scope: any other ADR-005 content.

## Assumptions
- The one-line pointer is used verbatim.
- This correction replaces the wrong entry — it does not add the new file
  alongside the old, wrong one.

## Design decisions
- `RagRepository` (`scripts/rag/repository.py:121`) has no delete method at all;
  `DocumentManager.delete_existing_document()` and `delete_document_chain()`
  (`scripts/rag/ingestion/document_manager.py`) are the real symbols Notes' own
  line 337 already correctly names (`delete_document_chain()`), just without
  listing their actual containing file. References' independent claim of a
  `RagRepository.delete_document(url)` method appears to be fabricated/stale with
  no current counterpart at all — do not invent a replacement for this specific
  sub-citation; only carry forward what actually exists
  (`delete_existing_document()`, `delete_document_chain()`).

## Alternatives considered
- Keep the wrong `scripts/rag/repository.py` entry and merely add the correct
  `document_manager.py` entry alongside it — rejected; leaving a confirmed-wrong
  entry in the sole surviving canonical section (References) after Notes' copy is
  deleted would make the ADR worse than before this change.

## Implementation
### Target file
`docs/adr/ADR-005-rag-source-derived-index-relationships.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   336-340 and References at 423-433.
2. Re-confirm via `grep -n "def delete" scripts/rag/repository.py
   scripts/rag/ingestion/document_manager.py` that `RagRepository` still has no
   delete method and `DocumentManager.delete_existing_document()`/
   `delete_document_chain()` are the real symbols.
3. Replace References' `scripts/rag/repository.py` —
   `RagRepository.delete_existing_document()`, `RagRepository.delete_document(url)`
   bullet with `scripts/rag/ingestion/document_manager.py` —
   `DocumentManager.delete_existing_document()`, `delete_document_chain()`.
4. Delete the Notes list (実装ファイル / 主要ClassまたはFunction /
   データベーススキーマ / トリガー / 対応するテスト, lines 336-340) — データベース
   スキーマ and トリガー are both already correctly duplicated in References, no
   migration needed for those two.
5. Insert: "See Related Documents > Implementation References for the current
   file/symbol list."

### Method
Use `Edit` (exact-string replacement) — one call per step 3-5.

### Details
- Do not alter References' other, unaffected bullets (`rag_maintenance_service.py`,
  `check_rag_consistency()`/`scripts/db/maintenance.py`, `config_loader.py`,
  the schema/trigger/test bullets).

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-005-rag-source-derived-index-relationships.md` if
validation fails.

## Validation plan
- `grep -n "def delete" scripts/rag/repository.py scripts/rag/ingestion/document_manager.py` — confirm the correction target before editing.
- Manual diff: confirm References no longer cites `RagRepository` for a delete method and now cites `DocumentManager`/`document_manager.py`; confirm Notes list removed.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-005-rag-source-derived-index-relationships.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-005-rag-source-derived-index-relationships.md` — record baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- References no longer cites `RagRepository.delete_existing_document()`/
  `RagRepository.delete_document(url)`; cites `DocumentManager` in
  `document_manager.py` instead.
- `## Implementation Notes` contains only the one-line pointer plus boilerplate.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- Any other section of ADR-005.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-162657 | Corrected wrong RagRepository citation to DocumentManager/document_manager.py; deleted Notes list; inserted pointer |
| 2 | Add or update tests per Validation plan | Completed | 20260915-162657 | 20260915-162657 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-162657 | 20260915-162657 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 12 pre-existing unrelated findings, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-162657 | 20260915-162657 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-005 — correct wrong RagRepository citation, delete Notes list
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-005-rag-source-derived-index-relationships.md