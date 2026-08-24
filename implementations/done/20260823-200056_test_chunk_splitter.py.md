## Goal

Add test coverage to `tests/rag/ingestion/test_chunk_splitter.py` proving that every
chunk file `ChunkSplitter` writes for a single crawl record carries the identical
`fetched_at` value, once `ChunkDocument` gains a mandatory `fetched_at: str` field and
`ChunkMetadata`/`_extract_chunk_metadata()` thread it through. This file currently has
zero `fetched_at` references (confirmed by reading the file in full — 53 lines, one
class `TestIsMarkdownSource`, six test methods, no `fetched_at` anywhere).

## Scope

**In scope**
- `tests/rag/ingestion/test_chunk_splitter.py` only: add one new test class covering
  `fetched_at` propagation across `_extract_chunk_metadata()` -> `_build_chunk_payload()`
  -> `_write_chunk_files()`.

**Out of scope**
- The existing `TestIsMarkdownSource` class and its six test methods — unaffected,
  since `_is_markdown_source()`'s signature/dict branch is untouched by this plan.
- Any change to `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/models_data.py`,
  or `scripts/rag/ingestion/pipeline_utils.py` — each has its own implementation
  document under this same plan.

## Assumptions

- `ChunkMetadata` (in `scripts/rag/ingestion/chunk_splitter.py`) **already** contains
  `fetched_at: str` (line 52).
- `_extract_chunk_metadata()` **already** copies `data.fetched_at` into the returned
  dict (line 267).
- `ChunkDocument` (in `scripts/rag/models_data.py`) **already** requires a mandatory
  `fetched_at: str` constructor argument (line 43).
- `_build_chunk_payload()` spreads `**metadata` into every chunk's output dict
  (confirmed by reading the method), so `fetched_at` reaches every written `.json`
  file automatically — no per-chunk-type special case.
- The existing `_make_splitter()` helper (`object.__new__` bypassing `__init__`) sets
  only `_md_index_enable`; it is insufficient for a test that performs real file I/O
  through `_write_chunk_files()`/`process_file()`, since those paths also touch
  `_chunk_dir`, `_min_chunk`, `_max_chunk`, `_chunk_overlap`, `_en_stopwords`,
  `_ja_stop_pos`, `_sd_tkn`, and `_split_c`. Sibling tests in
  `tests/rag/ingestion/test_rag_ingester.py` use `tmp_path` + config-dict construction
  of `RagIngester` — reuse that idiom for `ChunkSplitter` as well.

## Design decisions

- Test at the boundary the plan's own Validation plan specifies for this file
  ("Every `.json` in `_chunk_dir` for one `src_path` has matching `fetched_at`"): drive
  the test through `_write_chunk_files()` or `process_file()` and inspect the emitted
  JSON files, rather than asserting only on `_extract_chunk_metadata()`'s return value.
- Use a fixture `ChunkDocument`/source content that splits into at least two chunk
  files (e.g. two distinct text segments plus one code block), so "all chunks share
  identical `fetched_at`" is a non-vacuous assertion (a single-chunk output would pass
  trivially even with a bug in the spread).
- Use a canonical UTC-with-`Z` fixture value (e.g. `"2026-01-01T00:00:00Z"`) for
  `fetched_at` even though this file's own responsibility is only "identical across
  chunks," not "is canonical UTC" — keeps the fixture realistic without duplicating
  `test_crawler_integration.py`'s format assertion.

## Alternatives considered

- Mocking `_extract_chunk_metadata()`'s return value directly and asserting the dict
  contains `fetched_at` — rejected: this only proves the metadata dict carries the
  key, not that every written chunk file actually receives it; the propagation crosses
  a second hop (`**metadata` spread inside `_build_chunk_payload()`) that a
  metadata-only test would not exercise.
- Asserting purely at the `ChunkMetadata`/`TypedDict` structural-typing level (no
  filesystem write) — rejected: the plan's Validation plan for this file specifies a
  filesystem-level assertion ("Every `.json` in `_chunk_dir`"), not a type-level one.

## Implementation

### Target file
`tests/rag/ingestion/test_chunk_splitter.py`

### Procedure
1. Dependencies confirmed: `ChunkMetadata.fetched_at` (chunk_splitter.py:52),
   `_extract_chunk_metadata()` copy (chunk_splitter.py:267), and
   `ChunkDocument.fetched_at` (models_data.py:43) are already present.
2. Add a new test class (e.g. `TestFetchedAtPropagation`) below the existing
   `TestIsMarkdownSource` class.
3. Build a real, file-I/O-capable `ChunkSplitter` instance (see Assumptions) rooted at
   a `tmp_path`-backed `_rag_src_dir`/`_chunk_dir`.
4. Construct one `ChunkDocument` fixture (or, if driving through `process_file()`
   end-to-end, a crawl JSON dict written to a `tmp_path` source file) with
   `fetched_at="2026-01-01T00:00:00Z"` and content/code_blocks sized to produce at
   least two output chunk files.
5. Invoke `_write_chunk_files()` directly (unit-level) or `process_file()`
   (integration-level) against the fixture.
6. Glob every `*.json` file written under `_chunk_dir` for that source's stem, parse
   each with `orjson.loads()`, and assert: (a) at least two files were written, and
   (b) every parsed payload's `"fetched_at"` key equals the fixture's value.

### Method
- Black-box test through the same public/protected methods the plan's Validation plan
  names (`_write_chunk_files()`/`process_file()`), not a mock-based unit test of
  `_extract_chunk_metadata()` alone — see Alternatives considered.

### Details
- Use pytest's built-in `tmp_path` fixture for `_chunk_dir`/`_rag_src_dir` isolation;
  check whether other files in `tests/rag/ingestion/` already share a reusable
  splitter-construction fixture before adding a new one.
- Do not assert on `etag`/`last_modified`/`title` propagation beyond what is needed to
  isolate `fetched_at` — those are not part of this plan's new coverage.
- Keep the new test class independent of `TestIsMarkdownSource`'s `_make_splitter()`
  helper if that helper is not extended; introducing a second, more capable
  constructor helper is acceptable and should be named distinctly (e.g.
  `_make_io_splitter()`) to avoid confusion with the existing one.

## Compatibility considerations

- Purely additive: does not modify or remove `TestIsMarkdownSource`'s six existing
  test methods, which remain valid because `_is_markdown_source()` is untouched.
- Can be written immediately — all three dependencies (`ChunkMetadata.fetched_at`,
  `_extract_chunk_metadata()` copy, `ChunkDocument.fetched_at`) are already in place.

## Security considerations

N/A: test-only file: exercises only local `tmp_path` file I/O, no external input
surface or production code path is added.

## Rollback considerations

- Independently revertable: a new test class with no other test's dependency on it.
- If `fetched_at` propagation in `chunk_splitter.py` is ever reverted, this test should
  fail loudly rather than be deleted — it is the one test in this plan's Affected
  areas required to cover that specific guarantee.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` — all six existing
  `TestIsMarkdownSource` cases plus the new `fetched_at` propagation case(s) pass.
- `rg -n "fetched_at" tests/rag/ingestion/test_chunk_splitter.py` shows at least one
  match after the change (0 today, per the source plan's Affected areas table).
- Cross-check the new assertion's wording against the source plan's Validation plan
  row for `scripts/rag/ingestion/chunk_splitter.py`: "Every `.json` in `_chunk_dir`
  for one `src_path` has matching `fetched_at`."

## Out of scope

- Modifying `_is_markdown_source()` or its existing `TestIsMarkdownSource` cases.
- Asserting `fetched_at`'s canonical-UTC/`Z`-suffix format — that belongs to
  `tests/rag/ingestion/test_crawler_integration.py` (and sibling crawler test files)
  per the source plan's Affected areas table, since `chunk_splitter.py` only
  propagates the value, it does not generate it.
- Any change to `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/models_data.py`,
  or `scripts/rag/ingestion/pipeline_utils.py` themselves.

##### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Adversarial validation of assumptions | Complete | — | — | Assumption error found: fetched_at already present in ChunkMetadata and _extract_chunk_metadata() |
| 2 | Update procedure document | Complete | — | — | Corrected Assumptions and Procedure sections |
| 3 | Add TestFetchedAtPropagation class | Complete | — | — | 6 test methods added |
| 4 | Fix test payloads for chunking rules | Complete | — | — | Replaced empty content/code_blocks payloads; used multi-sentence long text for >=2 chunks |
| 5 | Toolchain validation | Complete | — | — | ruff format/check OK, mypy OK, pytest 12/12 passed |

##### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-095054_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-200056
- Related target files: tests/rag/ingestion/test_chunk_splitter.py

## Completion

### Validation results

- **ruff format**: applied (1 file reformatted)
- **ruff check**: fixed by --fix (2 errors resolved: import sorting, unused pytest)
- **myPy**: no issues found
- **pytest**: 12/12 passed (TestIsMarkdownSource: 6/6, TestFetchedAtPropagation: 6/6)

### Tests added

- `test_long_text_splits_into_multiple_chunks_with_matching_fetched_at` — verifies >=2 chunks from long single-paragraph content (>500 chars), each carries identical fetched_at
- `test_text_plus_code_block_both_have_matching_fetched_at` — verifies both content-derived and code-block-derived chunks carry matching fetched_at
- `test_long_single_paragraph_has_fetched_at` — verifies single chunk from long content has fetched_at
- `test_md_heading_splits_have_matching_fetched_at` — verifies markdown heading-split chunks carry matching fetched_at
- `test_different_fetched_at_values_are_preserved_per_file` — verifies two crawl records with different fetched_at values produce separate chunk sets with correct per-file values
- `test_code_only_chunk_has_fetched_at` — verifies code-only payload produces a chunk with fetched_at

### Key findings during adversarial validation

1. **Assumption error corrected**: Procedure originally claimed zero fetched_at references in chunk_splitter.py. Found fetched_at in ChunkMetadata (line 52) and _extract_chunk_metadata() return dict (line 267). Dependencies confirmed present — no additional changes needed.
2. **Payload design constraint discovered**: Crawl JSON payloads must have either non-empty content OR non-empty code_blocks (per read_crawl_json cross-field validation). Empty content + empty code_blocks raises ChunkFormatError.
3. **English chunker behavior**: Single-paragraph content stays within max_chunk=500 threshold → 1 chunk. Need >500 chars for >=2 chunks. Stopword removal discards short paragraphs below min_chunk=40.
