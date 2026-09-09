## Goal

Remove Module-level Constants table, TypedDict field-catalog table, and Public Functions table from the pipeline utils document and replace each with a one-sentence pointer to the source file. Review the TypedDict table against the same policy even though it is not a function-signature table per se.

## Scope

Modify `docs/03_rag_02_08_ingestion_pipeline-shared.md`: remove the Module-level Constants table (lines 46-50), TypedDict table (lines 52-56), and Public Functions table (lines 58-64), replacing them with pointer sentences to `pipeline_utils.py`. Also review the Historical field-mapping table (lines 80-93) against the same policy.

## Assumptions

- The Module-level Constants table (lines 46-50) is a constant-value index that violates the policy.
- The TypedDict table (lines 52-56) is a field-catalog table for a specific symbol that should be reviewed against the same policy even though it is not a function/method signature table per se.
- The Public Functions table (lines 58-64) is a class/function-method signature-and-description index that violates the policy.
- The Historical field-mapping table (lines 80-93) is a legacy fallback behavior table that may also violate the policy.
- The Module Overview paragraph ("pipeline_utils.py — Shared I/O utilities for the RAG ingestion pipeline...") is design-intent prose that should be preserved unchanged.

## Design decisions

- Replace each removed table with a single pointer sentence directing readers to the source file for exhaustive detail.
- Preserve existing module-purpose/design-intent prose paragraphs unchanged.

## Alternatives considered

- Retain the tables as reference material: rejected because the policy explicitly targets class/function/method signature-and-description index tables and constant-value tables as they duplicate what the module's own docstrings/type annotations already state authoritatively, and go stale on every signature change or added/removed constant.
- Rewrite the tables as prose summaries: rejected because the policy requires replacing removed tables with a pointer sentence to the source file, not a longer substitute listing.

## Implementation

### Target file

`docs/03_rag_02_08_ingestion_pipeline-shared.md`

### Procedure

1. Read all flagged lines to classify each as genuine violation (remove) or false positive (keep).
2. Remove the Module-level Constants table and replace with a pointer sentence.
3. Review the TypedDict field-catalog table against the same policy and remove/compress it if it is a signature-and-description index in substance.
4. Remove the Public Functions table and replace with a pointer sentence.
5. Review the Historical field-mapping table against the same policy and remove/compress it if it is a signature-and-description index in substance.
6. Verify remaining warnings via `uv run python tools/check_docs_content_policy.py`.
7. Run `uv run python tools/check_docs_consistency.py --domain rag`.

### Method

Read all 1 flagged line individually. For each, determine whether it is part of a class/function/method signature-and-description index table (contains `| Function | Signature | Description |` or similar column headers) or represents design-intent content (component responsibility, owned state, etc.). Remove only the former; preserve the latter.

Also review the Module-level Constants table, TypedDict field-catalog table, and Historical field-mapping table against the same policy even though they are not function-signature tables per se — they are constant-value and field-catalog tables that duplicate what the module's own type annotations/docstrings already state authoritatively, and go stale on every constant change or added/removed field.

### Details

The Module-level Constants table at lines 46-50 contains:
```
**Module-level Constants**

| Constant | Value | Description |
|---|---|---|
| `logger` | `Logger(__name__, "/opt/llm/logs/pipeline.log")` | Pipeline logging instance |
```

This is a constant-value index table cataloging module-level constants with their values and descriptions. It duplicates what the module's own type annotations/docstrings already state authoritatively, and goes stale on every constant change or added/removed constant.

The TypedDict table at lines 52-56 contains:
```
**TypedDict**

| TypedDict | Purpose |
|---|---|
| `ChunkJsonRaw` | Raw chunk JSON payload fields; Required: `url`, `content`, `fetched_at`; Optional: `title`, `lang`, `code_blocks`, `etag`, `last_modified`, `chunking_strategy`, `normalized_content`, `chunk_index`, `source_file`, `chunk_type`, `artifact_type`, `schema_version`, `created_by` |
```

This is a field-catalog table for a specific TypedDict (`ChunkJsonRaw`). While it is not a function/method signature table per se, it is a closely related pattern — a field-catalog table for a specific symbol that duplicates what the TypedDict's own type annotations already state authoritatively, and goes stale when fields are added/removed. This should be reviewed against the same policy.

The Public Functions table at lines 58-64 contains:
```
**Public Functions**

| Function | Signature | Description |
|---|---|---|
| `read_json_file` | `(path: Path) -> ChunkDocument` | Legacy fallback reader, not called by any current pipeline path ... |
| `collect_source_files` | `(rag_src_dir: Path, target: Path | None = None) → tuple[list[Path], list[SkipInfo]]` | Returns (target files, skip information); ... |
| `is_already_processed` | `(sentinel_path: Path, force: bool) → bool` | Returns `True` if the sentinel file exists and `force=False` ... |
```

This is a class/function-method signature-and-description index table cataloging functions with their signatures and descriptions. It duplicates what the module's own docstrings/type annotations already state authoritatively, and goes stale on every signature change or added/removed function.

The Historical field-mapping table at lines 80-93 contains:
```
| JSON Field | ChunkDocument Field | Fallback |
|---|---|---|
| `url` | `url` | (Required, no fallback) |
| `title` | `title` | `""` |
| `lang` | `lang` | `"en"` |
| `content` | `content` | (Required, no fallback) |
| `code_blocks` | `code_blocks` | `[]` |
| `etag` | `etag` | `None` |
| `last_modified` | `last_modified` | `None` |
| `chunking_strategy` | `chunking_strategy` | `"text"` |
| `normalized_content` | `normalized_content` | `None` |
| `chunk_index` | `chunk_index` | `0` |
| `source_file` | `source_file` | `""` |
| `chunk_type` | `chunk_type` | `""` |
```

This is a field-mapping table for a legacy fallback reader. While it is marked as "historical reference only" and notes that the function is not used by any current pipeline code path, it is still a field-catalog table that duplicates what the dataclass's own type annotations already state authoritatively, and goes stale when fields are added/removed. This should be reviewed against the same policy.

Replace all tables with:
```
For exhaustive signature and constant detail, see `scripts/rag/ingestion/pipeline_utils.py`.
```

## Compatibility considerations

- The replacement must maintain traceability to the original information. The pointer sentence directs readers to the source file where details are documented authoritatively.
- Cross-references to other documents (e.g., `[03_rag_02_03_ingestion_pipeline-chunksplitter.md]`) must be preserved.
- The Module Overview paragraph should be preserved as it describes component responsibilities, not implementation details.

## Security considerations

- None identified. This is a documentation-only change removing signature-catalog tables and constant-value tables.

## Rollback considerations

- If the pointer replacement loses critical identification of specific functions/constants/fields, the original tables can be restored temporarily while a better prose summary is drafted.
- The rollback path is straightforward: revert the edit and restore the original tables.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_02_08_ingestion_pipeline-shared.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/03_rag_02_08_ingestion_pipeline-shared.md` | Zero class/function/method index table findings; zero constant-table findings; zero TypedDict-field-catalog findings; structure check passes |

## Completion criteria

- All flagged lines have been classified (removed as genuine violation or kept as false positive).
- Each removed table is replaced by a pointer sentence to its source file, not silently deleted with no trace.
- `check_docs_content_policy.py` reports zero class/function/method index table findings, zero constant-table findings, and zero TypedDict-field-catalog findings for this file.
- `check_docs_consistency.py --domain rag` passes.

## Out of scope

- Modifying any other content in this file beyond the flagged tables and their immediate context.
- Altering `03_rag_02_01_ingestion_pipeline-overview.md`, `-02_...-crawler.md`, `-03_...-chunksplitter.md`, `-04_...-ingester.md`, `-05_...-document-manager.md`, `-06_...-supporting-components.md`, `-07_...-utils.md`, or `-09_...-shared-utilities.md`.
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
- **Requirement ID**: REQ-001: Remove `03_rag_02_08_ingestion_pipeline-shared.md`'s "Public Functions" and "Module-level Constants" tables under "## 9. Pipeline Utils", replacing them with a one-sentence pointer to `pipeline_utils.py`; REQ-002: Review the same file's "TypedDict" field-catalog table for `ChunkJsonRaw` against the same policy and remove/compress it if it is a signature-and-description index in substance
- **Source issue**: issues/20260905-153715_dcp005_rag_docs_content_policy_cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-211729_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-000740
- **Related target files**: docs/03_rag_02_08_ingestion_pipeline-shared.md
