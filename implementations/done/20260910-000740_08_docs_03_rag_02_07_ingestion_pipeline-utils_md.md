## Goal

Remove class/function/method signature-and-description index tables from the ingestion pipeline utilities document and replace each with a one-sentence pointer to the source file.

## Scope

Modify `docs/03_rag_02_07_ingestion_pipeline-utils.md`: remove the Module-level Constants table (lines 39-47), CJK Detection Unicode Code Point Ranges table (lines 49-55), Public Functions table (lines 57-67), Chunk Utils Public Functions table (lines 88-93), and Actual Usage table (lines 95-101), replacing them with pointer sentences to the respective source files.

## Assumptions

- The Module-level Constants table (lines 39-47) is a constant-value index that violates the policy.
- The CJK Detection Unicode Code Point Ranges table (lines 49-55) is a constant-value index that violates the policy.
- The Public Functions table (lines 57-67) is a class/function-method signature-and-description index that violates the policy.
- The Chunk Utils Public Functions table (lines 88-93) is a class/function-method signature-and-description index that violates the policy.
- The Actual Usage table (lines 95-101) is a caller-function mapping table that duplicates what the module's own docstrings/type annotations already state authoritatively.
- The surrounding prose sections (Module Overview paragraphs) are design-intent prose that should be preserved unchanged.

## Design decisions

- Replace each removed table with a single pointer sentence directing readers to the source file for exhaustive detail.
- Preserve existing module-purpose/design-intent prose paragraphs unchanged.

## Alternatives considered

- Retain the tables as reference material: rejected because the policy explicitly targets class/function/method signature-and-description index tables and constant-value tables as they duplicate what the module's own docstrings/type annotations already state authoritatively, and go stale on every signature change or added/removed constant.
- Rewrite the tables as prose summaries: rejected because the policy requires replacing removed tables with a pointer sentence to the source file, not a longer substitute listing.

## Implementation

### Target file

`docs/03_rag_02_07_ingestion_pipeline-utils.md`

### Procedure

1. Read all flagged lines to classify each as genuine violation (remove) or false positive (keep).
2. Remove the Module-level Constants table and replace with a pointer sentence.
3. Review the CJK Detection Unicode Code Point Ranges table against the same policy and remove/compress it if it is a constant-value index in substance.
4. Remove the Public Functions table and replace with a pointer sentence.
5. Remove the Chunk Utils Public Functions table and replace with a pointer sentence.
6. Review the Actual Usage table against the same policy and remove/compress it if it is a signature-and-description index in substance.
7. Verify remaining warnings via `uv run python tools/check_docs_content_policy.py`.
8. Run `uv run python tools/check_docs_consistency.py --domain rag`.

### Method

Read all 2 flagged lines individually. For each, determine whether it is part of a class/function/method signature-and-description index table (contains `| Function | Signature | Description |` or similar column headers) or represents design-intent content (component responsibility, owned state, etc.). Remove only the former; preserve the latter.

Also review the Module-level Constants table, CJK Detection Unicode Code Point Ranges table, and Actual Usage table against the same policy even though they are not function-signature tables per se — they are constant-value and caller-function mapping tables that duplicate what the modules' own docstrings/type annotations already state authoritatively, and go stale on every constant change or added/removed caller.

### Details

The Module-level Constants table at lines 39-47 contains:
```
**Module-level Constants**

| Constant | Value | Description |
|---|---|---|
| `_SUPPORTED_LANGS` | `frozenset({"en", "ja"})` | Supported language codes after resolution (output) |
| `_VALID_HINT_LANGS` | `frozenset({"en", "ja", "auto"})` | Valid hint language values for per-page CJK ratio detection, including `"auto"` |
| `_CJK_RATIO_THRESHOLD` | `0.1` | CJK character ratio threshold above which text is identified as Japanese |
| `_TARGET_URL_ENTRY_LENGTH` | `2` | Expected number of elements in a `target_urls` entry: `[url, lang]` |
| `MIN_TEXT_LENGTH_FOR_DETECTION` | `100` (from `rag.utils`) | Minimum text length required for language detection |
```

This is a constant-value index table cataloging module-level constants with their values and descriptions. It duplicates what the module's own type annotations/docstrings already state authoritatively, and goes stale on every constant change or added/removed constant.

The CJK Detection Unicode Code Point Ranges table at lines 49-55 contains:
```
**CJK Detection Unicode Code Point Ranges**

| Constant | Range | Description |
|---|---|---|
| Hiragana + Katakana | "぀"–"ヿ" | Unicode range for Hiragana and Katakana |
| CJK Unified Ideographs | "一"–"鿿" | Unicode range for CJK Unified Ideographs |
| CJK Extension A | "㐀"–"䶿" | Unicode range for CJK Extension A |
```

This is a constant-value index table cataloging Unicode code point ranges. It duplicates what the module's own type annotations/docstrings already state authoritatively, and goes stale when the ranges change.

The Public Functions table at lines 57-67 contains:
```
**Public Functions**

| Function | Signature | Description |
|---|---|---|
| `url_to_slug` | `(url: str) -> str` | Converts a URL into an ASCII slug safe for the filesystem ... |
| `normalize_url` | `(url: str) -> str` | Removes fragments and trailing slashes |
| `same_origin` | `(url: str, base: str) → bool` | Returns `True` if schemes and hostnames match |
| `extract_text` | `(soup: BeautifulSoup) → str` | Removes noise tags ... |
| `detect_lang` | `(text: str) → str \| None` | CJK ratio detection; returns `'ja'` if ratio ≥ 0.1, otherwise `'en'`; returns `None` for text shorter than 100 characters |
| `parse_target_urls` | `(target_raw: list[list[str]]) → list[tuple[str,str]]` | Validates `target_urls` configuration and parses them into `(url, lang)` tuples ... |
| `parse_targets_file` | `(path: Path) → list[tuple[str,str]]` | Parses TOML files containing `target_urls = [[url, lang], ...]` ... |
```

This is a class/function-method signature-and-description index table cataloging functions with their signatures and descriptions. It duplicates what the module's own docstrings/type annotations already state authoritatively, and goes stale on every signature change or added/removed function.

The Chunk Utils Public Functions table at lines 88-93 contains:
```
**Public Functions**

| Function | Signature | Description |
|---|---|---|
| `start_next_buf` | `(prev: str, next_item: str, sep: str, chunk_overlap: int) → str` | Starts a new accumulation buffer while optionally handling trailing duplicates from `prev`. ... |
| `merge_text_items` | `(items: list[str], sep: str, min_chunk: int, max_chunk: int, chunk_overlap: int) → list[str]` | Accumulates items into chunks such that `min_chunk` ≤ len ≤ `max_chunk`. ... |
```

This is a class/function-method signature-and-description index table cataloging functions with their signatures and descriptions. It duplicates what the module's own docstrings/type annotations already state authoritatively, and goes stale on every signature change or added/removed function.

The Actual Usage table at lines 95-101 contains:
```
**Actual Usage (Code Verified):**

| Caller | Function Used | Purpose |
|---|---|---|
| `ChunkEnglishMixin` (`chunk_english.py`) | `start_next_buf` | Handling trailing duplicates during paragraph accumulation |
| `ChunkSplitter._chunk_code` (`chunk_splitter.py`) | `merge_text_items` | Accumulating code blocks (empty line splitting) |
| `ChunkJapaneseMixin` (`chunk_japanese.py`) | (Does NOT import this module) | Uses proprietary implementation for accumulating sentence pairs. ... |
```

This is a caller-function mapping table that duplicates what the modules' own imports/docstrings already state authoritatively, and goes stale when callers change.

Replace all tables with:
```
For exhaustive signature and constant detail, see `scripts/rag/ingestion/crawler_utils.py` (crawler utils), `scripts/rag/ingestion/chunk_english.py` (chunk English mixin), and `scripts/rag/ingestion/chunk_utils.py` (chunk utils).
```

## Compatibility considerations

- The replacement must maintain traceability to the original information. The pointer sentence directs readers to the source files where details are documented authoritatively.
- Cross-references to other documents (e.g., `[03_rag_02_03_ingestion_pipeline-chunksplitter.md]`, `[03_rag_02_09_ingestion_pipeline-shared-utilities.md]`) must be preserved.
- The Module Overview paragraphs should be preserved as they describe component responsibilities, not implementation details.

## Security considerations

- None identified. This is a documentation-only change removing signature-catalog tables and constant-value tables.

## Rollback considerations

- If the pointer replacement loses critical identification of specific functions/constants, the original tables can be restored temporarily while a better prose summary is drafted.
- The rollback path is straightforward: revert the edit and restore the original tables.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_02_07_ingestion_pipeline-utils.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/03_rag_02_07_ingestion_pipeline-utils.md` | Zero class/function/method index table findings; zero constant-table findings; structure check passes |

## Completion criteria

- All flagged lines have been classified (removed as genuine violation or kept as false positive).
- Each removed table is replaced by a pointer sentence to its source file, not silently deleted with no trace.
- `check_docs_content_policy.py` reports zero class/function/method index table findings and zero constant-table findings for this file.
- `check_docs_consistency.py --domain rag` passes.

## Out of scope

- Modifying any other content in this file beyond the flagged tables and their immediate context.
- Altering `03_rag_02_01_ingestion_pipeline-overview.md`, `-02_...-crawler.md`, `-03_...-chunksplitter.md`, `-04_...-ingester.md`, `-05_...-document-manager.md`, `-06_...-supporting-components.md`, `-08_...-shared.md`, or `-09_...-shared-utilities.md`.
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
- **Related target files**: docs/03_rag_02_07_ingestion_pipeline-utils.md
