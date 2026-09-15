## Goal
Remove ADR-009's redundant file/class/config/test list from `## Implementation
Notes` once reconciled into `### Implementation References`, per `REQ-009` —
correcting the same wrong class/file citation found in ADR-005's References
(byte-identical text, apparently copy-pasted between the two RAG-maintenance
ADRs).

## Scope
- In scope: correct References' `scripts/rag/repository.py` —
  `RagRepository.delete_existing_document()`/`RagRepository.delete_document(url)`
  entry to `scripts/rag/ingestion/document_manager.py` —
  `DocumentManager.delete_existing_document()`, `delete_document_chain()`; delete
  the Notes list; insert the one-line pointer.
- Out of scope: any other ADR-009 content.

## Assumptions
- The one-line pointer is used verbatim.
- This is the same correction as `implementations/20260915-160939_05_docs_adr_ADR-005-rag-source-derived-index-relationships.md.md`'s
  REQ-005 — apply independently to this file (do not assume this file's edit
  depends on that one having been applied first).

## Design decisions
- See the sibling ADR-005 procedure document for the full evidence (`RagRepository`
  has no delete method; the real symbols live on `DocumentManager` in
  `scripts/rag/ingestion/document_manager.py`) — identical reasoning applies here
  since the wrong text is byte-identical between the two ADRs.

## Alternatives considered
- See the sibling ADR-005 procedure document's Alternatives considered — same
  reasoning applies.

## Implementation
### Target file
`docs/adr/ADR-009-rag-ft5-text-separation.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   343-347 and References at 429-441.
2. Re-confirm via `grep -n "def delete" scripts/rag/repository.py
   scripts/rag/ingestion/document_manager.py` that `RagRepository` still has no
   delete method and `DocumentManager.delete_existing_document()`/
   `delete_document_chain()` are the real symbols.
3. Replace References' `scripts/rag/repository.py` —
   `RagRepository.delete_existing_document()`, `RagRepository.delete_document(url)`
   bullet with `scripts/rag/ingestion/document_manager.py` —
   `DocumentManager.delete_existing_document()`, `delete_document_chain()`.
4. Delete the Notes list (実装ファイル / 主要ClassまたはFunction /
   データベーススキーマ / トリガー / 対応するテスト, lines 343-347) —
   データベーススキーマ, トリガー, and both test citations are already correctly
   duplicated in References, no migration needed for those.
5. Insert: "See Related Documents > Implementation References for the current
   file/symbol list."

### Method
Use `Edit` (exact-string replacement) — one call per step 3-5.

### Details
- Do not alter References' other, unaffected bullets.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-009-rag-ft5-text-separation.md` if validation fails.

## Validation plan
- `grep -n "def delete" scripts/rag/repository.py scripts/rag/ingestion/document_manager.py` — confirm the correction target before editing.
- Manual diff: confirm References cites `DocumentManager`/`document_manager.py`; confirm Notes list removed.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-009-rag-ft5-text-separation.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-009-rag-ft5-text-separation.md` — record baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- References no longer cites `RagRepository` for a delete method; cites
  `DocumentManager` in `document_manager.py` instead.
- `## Implementation Notes` contains only the one-line pointer plus boilerplate.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- Any other section of ADR-009.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-163103 | Corrected same wrong RagRepository citation as ADR-005; deleted Notes list; inserted pointer |
| 2 | Add or update tests per Validation plan | Completed | 20260915-163103 | 20260915-163103 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-163103 | 20260915-163103 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 12 pre-existing unrelated findings, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-163103 | 20260915-163103 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-009 — correct same wrong RagRepository citation as ADR-005, delete Notes list
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-009-rag-ft5-text-separation.md