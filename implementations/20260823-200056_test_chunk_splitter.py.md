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

- This test cannot pass until `chunk_splitter.py`'s own implementation lands:
  `ChunkMetadata` (currently `url`, `title`, `lang`, `etag`, `last_modified`,
  `source_file`, `chunking_strategy`) gains `fetched_at: str`, and
  `_extract_chunk_metadata()` copies `data.fetched_at` into it. Confirmed by reading
  the current `chunk_splitter.py`: neither `ChunkMetadata` nor
  `_extract_chunk_metadata()`'s return dict includes `fetched_at` today.
- `ChunkDocument` (in `scripts/rag/models_data.py`) will require a mandatory
  `fetched_at: str` constructor argument once its own implementation document lands;
  this test's fixture construction must supply it.
- `_build_chunk_payload()` spreads `**metadata` into every chunk's output dict
  (confirmed by reading the method), so once `fetched_at` is in `ChunkMetadata`, it
  reaches every written `.json` file automatically — no per-chunk-type special case.
- The existing `_make_splitter()` helper (`object.__new__` bypassing `__init__`) sets
  only `_md_index_enable`; it is insufficient for a test that performs real file I/O
  through `_write_chunk_files()`/`process_file()`, since those paths also touch
  `_chunk_dir`, `_min_chunk`, `_max_chunk`, `_chunk_overlap`, `_en_stopwords`,
  `_ja_stop_pos`, `_sd_tkn`, and `_split_c`. The new test must either extend a
  splitter-construction helper to set these, or construct `ChunkSplitter(config=...)`
  with a `tmp_path`-backed config dict — verify at implementation time which idiom
  sibling tests in `tests/rag/ingestion/` already use for real chunking I/O, and reuse
  it rather than inventing a third pattern.

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
1. Confirm `chunk_splitter.py`'s and `models_data.py`'s own implementation documents
   (this plan's Phase 1/Phase 2 steps) have landed — `ChunkMetadata` includes
   `fetched_at: str`, `_extract_chunk_metadata()` copies it, and `ChunkDocument`
   requires it. Do not write this test's fixtures ahead of that change landing.
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
- Must fail (not error with `AttributeError`/`TypeError`) before the corresponding
  `chunk_splitter.py`/`models_data.py` changes land, and pass once `fetched_at`
  propagation is implemented — this is the intended sequencing across Phase 2
  (propagation) and Phase 5 (test migration) of the source plan.

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
| — | — | Pending | — | — | |

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
