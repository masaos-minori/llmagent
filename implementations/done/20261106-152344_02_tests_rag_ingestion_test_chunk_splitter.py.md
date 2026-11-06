## Goal

Add English Markdown characterization baselines (`REQ-003`) and Japanese Markdown
chunking/normalization tests (`REQ-004`) to lock current behavior before the change
and to pin the language-aware behavior after it.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Sudachi is available in the test environment (existing ja tests already exercise
  `_chunk_japanese` end-to-end).
- The ja text path is crash-free (`raging001` Plan landed the fix first).
- `_make_io_splitter(tmp_path)` builds a real `ChunkSplitter` from a temp config.
  `_make_chunk_doc` currently hardcodes `lang="en"` (`test_chunk_splitter.py:26-41`,
  verified 20261106); this procedure adds a `lang: str = "en"` keyword argument to
  that helper so a ja `ChunkDocument` can drive dispatch, existing callers unchanged.

## Design decisions
- **Characterization first (behavior lock).** English Markdown baselines are added in
  a dedicated class and pass against current code before any production change
  (Plan Phase 1). They snapshot section boundaries, the oversized `_chunk_english`
  fallback, the `min_chunk` drop, empty `normalized_content`, and the `"heading"`
  strategy label.
- **Failing ja tests (RED).** ja `.md` tests are added after the en baselines and fail
  against current code, because current code routes ja Markdown through
  `_chunk_english` with empty `normalized_content` (Plan Phase 2). They go green only
  after the dispatch change (Plan Phase 3).
- **Direct-triple assertions.** ja tests drive `_build_chunk_list` /
  `_build_text_triples` with a `lang == "ja"` `ChunkDocument` and assert on the
  emitted `("text", orig, norm)` triples, comparing `norm` against the value
  `_chunk_japanese(section)` produces for the same section — the same Sudachi
  normalized-form space the ja text path uses.

## Alternatives considered
- End-to-end only (`process_all` + read chunk JSON): valid but coarser; direct triple
  assertions pin `normalized_content` per section precisely and isolate the Markdown
  path from code-block handling. Used for the ja assertions; an end-to-end variant is
  noted for coverage.

## Implementation
### Target file
- `tests/rag/ingestion/test_chunk_splitter.py`

### Procedure
1. Add an English Markdown characterization class that snapshots today's `.md`
   heading output and passes against current code.
2. Add a Japanese Markdown test class (oversized-section segmentation, in-section
   normalization, strategy pin) that fails against current code.
3. Re-run the en baselines after the production change and assert byte-equality.

### Method
- Add a ja Markdown crawl payload alongside `_CRAWL_WITH_MD_HEADINGS`: same base
  shape but `lang = "ja"`, containing one oversized section (> `md_snippet_max_chars`)
  and one in-section section (<= `md_snippet_max_chars`).
- Build a ja `ChunkDocument` (via `_make_chunk_doc(..., lang="ja")` or the io splitter)
  and assert on `_build_chunk_list` output.

### Details
- **En characterization (passes today):** feed the existing en `_CRAWL_WITH_MD_HEADINGS`
  through `_build_chunk_list` and assert: each heading section <= `md_snippet_max_chars`
  becomes one chunk; the oversized section is split by `_chunk_english`; a sub-`min_chunk`
  section is dropped; every emitted triple has empty `normalized_content` (`""`); and
  `chunking_strategy` is `"heading"`. Snapshot the exact chunk contents for the
  byte-equal regression check.
- **ja oversized (fails today):** a ja `.md` oversized section yields multiple
  `("text", orig, norm)` triples whose `orig` values follow ja sentence-boundary
  segmentation and whose `norm` values are non-empty and equal to
  `_chunk_japanese(section)` for that section. Against current code the section goes
  through `_chunk_english` with `norm == ""`, so this assertion fails until Phase 3.
- **ja in-section (fails today):** a ja `.md` section <= `md_snippet_max_chars` stays a
  single whole chunk but carries a non-empty `norm` equal to the ja text-path
  normalization of that section. Today it is emitted with `norm == ""`, so this fails
  until Phase 3 (pins design decision D2).
- **Strategy pin (passes today):** `chunking_strategy == "heading"` for both en and ja
  `.md` payloads.
- **En regression:** re-run the en characterization after Phase 3 and assert the
  snapshot is byte-identical.

## Compatibility considerations
The en characterization baseline must stay green before and after the change
(`REQ-003`, `AC-3`). This document adds tests only; it does not change production
behavior.

## Security considerations
N/A: test-only additions, no input handling or credential change.

## Rollback considerations
Revert the commit to this test file. The new test classes are additive and isolated.

## Validation plan
- En characterization runs against current code and is green (Phase 1).
- ja oversized and in-section tests fail against current code and pass after Phase 3
  (Phase 2 -> 3).
- `uv run pytest tests/rag/ingestion` passes, incl. `TestIsMarkdownSource` unchanged.
- Static gates: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll` — clean.

## Completion criteria
- En Markdown characterization baselines exist and pass against current code.
- ja Markdown oversized/in-section tests exist and fail against current code, then pass
  after the dispatch change, asserting non-empty `normalized_content`.
- `chunking_strategy` pin holds for both languages; en output unchanged.

## Out of Scope
- Modifying the `raging004` Plan's force-prune test region of this same file — that is
  a non-overlapping co-target; implement 001 -> 004 -> 007 to serialize same-file
  edits. This class targets the Markdown-dispatch region only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add en Markdown characterization baselines (pass against current code) | Completed | — | 20261106-182607 | REQ-003 REQ-003: en characterization class added, 4/4 green vs current code; helper _make_chunk_doc gained lang kwarg (procedure corrected Step 3b) |
| 2 | Add ja Markdown failing tests (RED) | Completed | — | 20261106-182607 | REQ-004 REQ-004: 3 ja tests RED vs current code (allowed unit RED), strategy pin green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261106-182620 | 20261106-185350 | unit mode: ruff Pass; full suite+diff-cover at end of unit unit validated: 44 passed, ruff Pass, gates Pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261106-182620 | N/A: test-only change, no docs/00_index.md task-scope row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation; hard dependency on the `raging001` Plan implementation recorded in the source Plan Design | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261106-073538_raging007_markdown-japanese-chunk-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-103229_raging007_markdown-japanese-chunk-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-152344
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`