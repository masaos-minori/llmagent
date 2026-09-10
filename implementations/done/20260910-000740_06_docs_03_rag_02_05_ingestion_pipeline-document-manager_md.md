## Goal

Remove class/function/method signature-and-description index tables from the DocumentManager detail document and replace each with a one-sentence pointer to the source file.

## Scope

Modify `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`: remove the Module-level Functions table (lines 32-36) and Class method table (lines 38-45), replacing them with pointer sentences to `scripts/rag/ingestion/document_manager.py`.

## Assumptions

- The Module-level Functions table (lines 32-36) is a function-signature index that violates the policy.
- The Class method table (lines 38-45) is a class/function-method signature-and-description index that violates the policy.
- The surrounding prose ("DocumentManager manages the lifecycle of documents for RagIngester...") is design-intent prose that should be preserved unchanged.
- The CLI Entrypoint code block (lines 49-53) is a code example, not a signature-catalog table.

## Design decisions

- Replace each removed table with a single pointer sentence directing readers to the source file for exhaustive signature detail.
- Preserve existing module-purpose/design-intent prose paragraphs unchanged.

## Alternatives considered

- Retain the tables as reference material: rejected because the policy explicitly targets class/function/method signature-and-description index tables as they duplicate what the module's own docstrings/type annotations already state authoritatively, and go stale on every signature change or added/removed method.
- Rewrite the tables as prose summaries: rejected because the policy requires replacing removed tables with a pointer sentence to the source file, not a longer substitute listing.

## Implementation

### Target file

`docs/03_rag_02_05_ingestion_pipeline-document-manager.md`

### Procedure

1. Read all flagged lines to classify each as genuine violation (remove) or false positive (keep).
2. Remove the Module-level Functions table and replace with a pointer sentence.
3. Remove the Class method table and replace with a pointer sentence.
4. Verify remaining warnings via `uv run python tools/check_docs_content_policy.py`.
5. Run `uv run python tools/check_docs_consistency.py --domain rag`.

### Method

Read all 2 flagged lines individually. For each, determine whether it is part of a class/function/method signature-and-description index table (contains `| Function | Signature | Description |` or similar column headers) or represents design-intent content (component responsibility, owned state, etc.). Remove only the former; preserve the latter.

### Details

The Module-level Functions table at lines 32-36 contains:
```
**Module-level Functions**

| Function | Signature | Description |
|---|---|---|
| `delete_document_chain` | `(db: SQLiteHelper, doc_id: int) -> None` | Deletes in order: `chunks_vec` → `chunks` → `documents`. ... |
```

This is a function-signature index table cataloging exported functions with their signatures and descriptions. It duplicates what the module's own docstrings/type annotations already state authoritatively, and goes stale on every signature change or added/removed function.

The Class method table at lines 38-45 contains:
```
**Class: `DocumentManager`**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(db: SQLiteHelper) -> None` | Holds a reference to the DB connection |
| `handle_existing_document` | `(url: str, existing_doc_id: int, force: bool, etag|None, last_modified|None, fetched_at: str, is_file_url: Callable[[str], bool]) -> bool` | Processes an existing document; returns `True` if the caller should skip insertion. ... |
| `delete_existing_document` | `(doc_id: int) -> None` | Deletes the document and its chunks; ... |
| `check_consistency` | `(embed_failed: int, on_ingest_complete: Callable[[], None]|None = None) -> RagConsistencyReport | None` | Executes post-ingestion consistency checks and callbacks; ... |
```

This is a class/function-method signature-and-description index table cataloging methods with their signatures and descriptions. It duplicates what the class's own docstrings/type annotations already state authoritatively, and goes stale on every signature change or added/removed method.

Replace both tables with:
```
For exhaustive signature detail, see `scripts/rag/ingestion/document_manager.py`.
```

## Compatibility considerations

- The replacement must maintain traceability to the original information. The pointer sentence directs readers to the source file where signatures are documented authoritatively.
- Cross-references to other documents (e.g., `[03_rag_02_06_ingestion_pipeline-supporting-components.md]`) must be preserved.
- The CLI Entrypoint code block should be preserved as it is a code example, not a signature-catalog table.

## Security considerations

- None identified. This is a documentation-only change removing signature-catalog tables.

## Rollback considerations

- If the pointer replacement loses critical identification of specific functions/methods, the original tables can be restored temporarily while a better prose summary is drafted.
- The rollback path is straightforward: revert the edit and restore the original tables.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_02_05_ingestion_pipeline-document-manager.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/03_rag_02_05_ingestion_pipeline-document-manager.md` | Zero class/function/method index table findings; structure check passes |

## Completion criteria

- All flagged lines have been classified (removed as genuine violation or kept as false positive).
- Each removed table is replaced by a pointer sentence to its source file, not silently deleted with no trace.
- `check_docs_content_policy.py` reports zero class/function/method index table findings for this file.
- `check_docs_consistency.py --domain rag` passes.

## Out of scope

- Modifying the CLI Entrypoint code block (lines 49-53).
- Altering `03_rag_02_01_ingestion_pipeline-overview.md`, `-02_...-crawler.md`, `-03_...-chunksplitter.md`, `-04_...-ingester.md`, `-06_...-supporting-components.md`, `-07_...-utils.md`, `-08_...-shared.md`, or `-09_...-shared-utilities.md`.
- Any file outside the RAG domain.

## execution status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read all flagged lines and classify each as genuine violation or false positive | Completed | — | — | All flagged lines classified as genuine violations (signature-catalog tables) |
| 2 | Replace removed tables with pointer sentences | Completed | — | — | Replaced Module-level Functions table and Class method table with single pointer sentence |
| 3 | Run validation checks | Completed | — | — | Zero class/function/method index table findings for this file; consistency check has pre-existing warnings unrelated to this change |

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
- **Requirement ID**: REQ-003: Read and resolve the remaining findings in other five files, applying the same remove/replace pattern for genuine index-table or file-tree/location-mapping content
- **Source issue**: issues/20260905-153715_dcp005_rag_docs_content_policy_cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-211729_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-000740
- **Related target files**: docs/03_rag_02_05_ingestion_pipeline-document-manager.md
