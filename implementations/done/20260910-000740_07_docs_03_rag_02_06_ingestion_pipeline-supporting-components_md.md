## Goal

Remove class/function/method signature-and-description index tables from the supporting components document and replace each with a one-sentence pointer to the source file.

## Scope

Modify `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`: remove the Public Methods table for ETagManager (lines 35-39) and the Configuration parameter table (lines 78-83), replacing them with pointer sentences to the respective source files.

## Assumptions

- The Public Methods table (lines 35-39) is a class/function-method signature-and-description index that violates the policy.
- The Configuration parameter table (lines 78-83) is a configuration-value table that duplicates `config/ingester.toml` and goes stale when values change.
- The surrounding prose sections (ETagManager description, Boundary Conditions, Freshness Comparison edge cases) are design-intent prose that should be preserved unchanged.

## Design decisions

- Replace each removed table with a single pointer sentence directing readers to the source file for exhaustive detail.
- Preserve existing module-purpose/design-intent prose paragraphs unchanged.

## Alternatives considered

- Retain the tables as reference material: rejected because the policy explicitly targets class/function/method signature-and-description index tables as they duplicate what the module's own docstrings/type annotations already state authoritatively, and go stale on every signature change or added/removed method.
- Retain the configuration table as a quick-reference: rejected because the policy targets literal configuration values in prose regardless of intent.

## Implementation

### Target file

`docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`

### Procedure

1. Read all flagged lines to classify each as genuine violation (remove) or false positive (keep).
2. Remove the Public Methods table and replace with a pointer sentence.
3. Review the Configuration parameter table against the same policy and remove/compress it if it is a signature-and-description index in substance.
4. Verify remaining warnings via `uv run python tools/check_docs_content_policy.py`.
5. Run `uv run python tools/check_docs_consistency.py --domain rag`.

### Method

Read all 1 flagged line individually. For each, determine whether it is part of a class/function/method signature-and-description index table (contains `| Method | Signature | Description |` or similar column headers) or represents design-intent content (component responsibility, owned state, etc.). Remove only the former; preserve the latter.

Also review the Configuration parameter table (lines 78-83) against the same policy even though it is not a function-signature table per se — it is a field-catalog table for configuration parameters that duplicates `config/ingester.toml` and goes stale when values change.

### Details

The Public Methods table at lines 35-39 contains:
```
**Public Methods**

| Method | Signature | Description |
|---|---|---|
| `update` | `(etag: str \| None, last_modified: str \| None, new_fetched_at: str)` | Updates the ETag/Last-Modified of an existing document; returns early if both `etag` and `last_modified` are `None`. |
```

This is a class/function-method signature-and-description index table cataloging methods with their signatures and descriptions. It duplicates what the class's own docstrings/type annotations already state authoritatively, and goes stale on every signature change or added/removed method.

The Configuration parameter table at lines 78-83 contains:
```
| Parameter | Default | Description |
|---|---|---|
| `embed_url` | `http://127.0.0.1:8081/embedding` | Endpoint URL for the embedding API |
| `embed_retry` | 3 | Maximum retries on embedding API failure (exponential backoff) |
| `embed_workers` | 4 | Maximum number of concurrent embedding threads via `ThreadPoolExecutor` |
| Embedding dimension | Fixed code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`) | Expected dimensions of the embedding vector |
```

This is a configuration-value table that duplicates `config/ingester.toml` and goes stale when values change. The first row also contains a literal port number ("8081") which is a separate violation.

Replace both tables with:
```
For exhaustive detail, see `scripts/rag/ingestion/etag_manager.py` (ETagManager public methods) and `config/ingester.toml` (configuration parameters).
```

## Compatibility considerations

- The replacement must maintain traceability to the original information. The pointer sentence directs readers to the source files where details are documented authoritatively.
- Cross-references to other documents (e.g., `[03_rag_02_04_ingestion_pipeline-ingester.md]`, `[ADR-005](adr/ADR-005-rag-source-derived-index-relationships.md)`) must be preserved.
- The Boundary Conditions section and Freshness Comparison edge cases should be preserved as they describe operational behavior, not implementation details.

## Security considerations

- None identified. This is a documentation-only change removing signature-catalog tables and configuration-value tables.

## Rollback considerations

- If the pointer replacement loses critical identification of specific methods/parameters, the original tables can be restored temporarily while a better prose summary is drafted.
- The rollback path is straightforward: revert the edit and restore the original tables.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/03_rag_02_06_ingestion_pipeline-supporting-components.md` | Zero class/function/method index table findings; zero literal-port-number findings; structure check passes |

## Completion criteria

- All flagged lines have been classified (removed as genuine violation or kept as false positive).
- Each removed table is replaced by a pointer sentence to its source file, not silently deleted with no trace.
- `check_docs_content_policy.py` reports zero class/function/method index table findings and zero literal-port-number findings for this file.
- `check_docs_consistency.py --domain rag` passes.

## Out of scope

- Modifying any other content in this file beyond the flagged tables and their immediate context.
- Altering `03_rag_02_01_ingestion_pipeline-overview.md`, `-02_...-crawler.md`, `-03_...-chunksplitter.md`, `-04_...-ingester.md`, `-05_...-document-manager.md`, `-07_...-utils.md`, `-08_...-shared.md`, or `-09_...-shared-utilities.md`.
- Any file outside the RAG domain.

## execution status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read all flagged lines and classify each as genuine violation or false positive | Pending | — | — | |
| 2 | Replace removed tables with pointer sentences | Pending | — | — | |
| 3 | Run validation checks | Pending | — | — | |

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
- **Related target files**: docs/03_rag_02_06_ingestion_pipeline-supporting-components.md
