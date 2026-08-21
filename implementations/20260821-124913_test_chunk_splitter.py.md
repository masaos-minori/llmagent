## Goal
Update `tests/rag/ingestion/test_chunk_splitter.py` so its fixtures construct/consume
values compatible with the migrated `_is_markdown_source()` signature once
`scripts/rag/ingestion/chunk_splitter.py` moves to `read_crawl_json()`/`CrawlJsonPayload`/
`CrawlDocument`.

## Scope
- In scope: `tests/rag/ingestion/test_chunk_splitter.py` only (52 lines, 6 test functions,
  all under `class TestIsMarkdownSource`).
- Out of scope: `chunk_splitter.py` itself (own implementation document); `pipeline_utils.py`
  (own implementation document).

## Assumptions
- Confirmed by reading the file: the only method under test is `ChunkSplitter._is_markdown_source()`
  (called 6 times, at lines 20, 26, 30, 35, 43, 50). No other `chunk_splitter.py` method is
  exercised. No import of `CrawlFilePayload`, `ChunkOutputPayload`, `ChunkJsonRaw`,
  `read_json_file`, `CrawlPayload`, `ChunkDocument`, or `CrawlDocument` exists in this file
  today (`grep` confirms zero hits) — only `from rag.ingestion.chunk_splitter import
  ChunkSplitter` (line 7).
- **Correction (adversarial review, 2026-08-21):** the source plan
  (`plans/20260820-094150_plan.md`) originally described `_is_markdown_source()`'s post-migration
  type union as `ChunkDocument | ChunkJsonPayload`. This is incorrect — `_is_markdown_source()`
  is called on crawl-side data (from `process_file()`/`_build_text_triples()`), not
  chunk-output data. The plan has been corrected to `CrawlDocument | CrawlJsonPayload`. This
  document assumes the corrected union.
- Current signature (chunk_splitter.py:165): `_is_markdown_source(self, data: ChunkDocument |
  ChunkJsonRaw) -> bool`. Body branches on `isinstance(data, ChunkDocument)` (attribute access)
  vs. dict (`data.get("url", "")`/`data.get("content", "")`). All 6 test fixtures pass a bare
  dict literal (`{"url": ...}` or `{"url": ..., "content": ...}`) down the dict branch, relying
  on `.get(key, default)` never raising on a missing key.
- **Open design question inherited from the plan, not resolved here:** whether the raw-dict
  branch is kept (as `CrawlJsonPayload`, which — depending on Phase 1's implementation of that
  `TypedDict` — may make every key mandatory) or dropped entirely in favor of `CrawlDocument`
  only. This changes what these 6 fixtures must look like:
  - If the raw-dict branch is kept with `CrawlJsonPayload` as a fully-mandatory-key `TypedDict`,
    each of the 6 dict literals must be expanded to the full crawl-mandatory key set (`url`,
    `title`, `lang`, `fetched_at`, `content`, `code_blocks`, `etag`, `last_modified`, plus
    envelope fields if `CrawlJsonPayload` includes them) — a minimal `{"url": ...}` dict would
    no longer type-check or, if validated at construction, would fail.
  - If the raw-dict branch is dropped, all 6 fixtures must become `CrawlDocument(...)` dataclass
    instances instead of dict literals, and `_is_markdown_source()`'s dict-branch code path
    disappears.
  - Resolve this by reading the finalized `chunk_splitter.py` implementation (from its own
    implementation document) before editing this test file — do not guess ahead of that
    decision.

## Design decisions
- Keep the existing 6 test cases' semantics unchanged (each tests one URL-extension/heuristic
  branch of `_is_markdown_source()`); only the fixture *shape* changes, driven by whichever
  design `chunk_splitter.py`'s own implementation document settles on.
- Do not invent a 7th test case or additional coverage here — this is a mechanical fixture
  migration, not new test design (out of scope per the workflow's Out-of-scope: "unrelated
  refactoring").

## Alternatives considered
- Leaving the dict literals as-is and hoping `CrawlJsonPayload`/`CrawlDocument` union tolerates
  partial dicts — rejected: the entire point of this plan is exact-key-set enforcement: any
  raw-dict branch that survives migration will almost certainly type/validate against the same
  mandatory-key set `read_crawl_json()` enforces, so a partial dict cannot be assumed to still
  work.

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_splitter.py`

### Procedure
1. Read the finalized `_is_markdown_source()` signature and branch structure in the migrated
   `chunk_splitter.py` (from its own implementation document / actual code at implementation
   time) to determine which of the two paths above was chosen.
2. If the raw-dict (`CrawlJsonPayload`) branch was kept:
   - Expand each of the 6 dict literals (lines 20, 26, 30, 35, 43, 50) to include every
     mandatory key `CrawlJsonPayload` requires, with values that do not affect the assertion
     under test (e.g. `title=""`, `lang="en"`, `fetched_at="2024-01-01T00:00:00"`,
     `code_blocks=[]`, `etag=None`, `last_modified=None`), while keeping the specific `url`/
     `content` values that drive each test's assertion unchanged.
3. If the raw-dict branch was dropped in favor of `CrawlDocument` only:
   - Add `from rag.models_data import CrawlDocument` (or wherever it lives) to the imports
     (line 7 area).
   - Replace each of the 6 dict literals with a `CrawlDocument(url=..., content=..., title="",
     lang="en", fetched_at="2024-01-01T00:00:00", code_blocks=[], etag=None,
     last_modified=None)` construction, preserving each test's specific `url`/`content` value.
4. Re-run the test file to confirm all 6 cases still pass with the same pass/fail outcome per
   test (the assertions themselves — `assert result is True`/`False` — do not change).

### Method
- This is a pure fixture-shape migration: no new behavior is tested, no existing assertion
  value changes. The `_make_splitter()` helper (lines 10-13, uses `object.__new__` to bypass
  `__init__`) is unaffected and needs no change.

### Details
- Test-by-test mapping (line -> current dict -> field to preserve):
  - Line 20 `test_md_extension_returns_true_regardless_of_flag`: `url="https://example.com/README.md"`.
  - Line 26 `test_markdown_extension_returns_true`: `url="docs/guide.markdown"`.
  - Line 30 `test_mdx_extension_returns_true`: `url="component.mdx"`.
  - Line 35 `test_non_md_url_returns_false_when_flag_disabled`: `url="https://example.com/page.html"`.
  - Line 43 `test_non_md_url_heuristic_when_flag_enabled`: `url="page.html"`, `content=<markdown
    headings string>` — this test depends on `content`'s actual value (heading heuristic), so
    `content` must be preserved exactly, not replaced with a placeholder.
  - Line 50 `test_non_md_no_headings_returns_false_even_when_flag_enabled`: `url="page.html"`,
    `content="plain text"` — same caveat as above.

## Compatibility considerations
- None beyond the fixture shape change — no production behavior change originates from this
  file.

## Security considerations
N/A — test-only file, no external input surface.

## Rollback considerations
- Independently revertable; this file has no runtime dependents.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` — all 6 tests pass with
  unchanged pass/fail outcomes per case.
- Re-run after `chunk_splitter.py`'s own migration lands, not before — this file's fixtures
  cannot be finalized independent of that decision (see Assumptions).

## Out of scope
- Deciding whether `_is_markdown_source()` keeps its raw-dict branch — that decision belongs to
  `chunk_splitter.py`'s own implementation document; this document only describes how to react
  to either outcome.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260820-094150_plan.md
- Source implementation procedure: N/A
- Generated at: 20260821-124913
- Related target files: test_chunk_splitter.py
