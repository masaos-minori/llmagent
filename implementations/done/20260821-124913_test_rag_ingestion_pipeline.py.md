## Goal
Fix `tests/rag/ingestion/test_rag_ingestion_pipeline.py`'s misleadingly-named
`_make_chunk_json()` helper, which currently builds a crawl-shaped payload, so the 5 tests
that feed its output directly to `RagIngester.ingest_all()` as a chunk file continue to pass
once `read_chunk_json()` enforces the full chunk-mandatory key set.

## Scope
- In scope: `tests/rag/ingestion/test_rag_ingestion_pipeline.py` only (583 lines, 12 test
  functions).
- Out of scope: `ingester.py`'s own migration (own implementation document);
  `chunk_splitter.py`'s own migration (own implementation document).

## Assumptions
- Confirmed by reading the file: `_make_chunk_json()` (lines 93-113) is misleadingly named —
  despite its name, it builds a **crawl**-shaped dict (its own docstring says "matching the
  crawler output format"): `url`/`title`/`lang`/`fetched_at`/`content`/`code_blocks`/
  `schema_version`/`artifact_type`/`created_by`/`etag`/`last_modified` — all 8 crawl-mandatory
  keys plus envelope, but entirely missing all 5 chunk-mandatory keys: `chunk_index`,
  `chunking_strategy`, `normalized_content`, `chunk_type`, `source_file`.
- **Gap found (adversarial review, 2026-08-21), added to `plans/20260820-094150_plan.md`'s
  Affected-areas table.** Two distinct, differently-affected usage patterns exist:
  - **(A) Correct usage — fed as crawl input to `ChunkSplitter`** (no problem): the
    `chunk_json` fixture (lines 129-142) writes `_make_chunk_json(...)` into `rag-src/` and
    `test_chunk_json_has_required_fields` (144-156) / `test_chunk_splitter_processes_json`
    (158-174) consume it as crawl input — consistent with `read_crawl_json()`'s eventual
    consumer contract. No change needed for these two tests.
  - **(B) Problematic usage — the same crawl-shaped dict written directly into the `chunk/`
    directory and fed straight to `RagIngester.ingest_all()`, bypassing `ChunkSplitter`
    entirely** — 5 tests: `test_ingester_reads_chunk_json` (176-216),
    `test_full_pipeline_preserves_metadata` (218-268), `test_sha256_same_content_no_reingest`
    (311-371), `test_sha256_different_content_triggers_reingest` (373-441),
    `test_sha256_etag_changes_triggers_reingest` (443-511). Each of these writes
    `_make_chunk_json()`'s output into the `chunk/` directory and calls `ingester.ingest_all()`
    directly (call sites: 413/437/351/366/483/507/258/etc., per the investigation). Today this
    "works" only because `ingester.py` silently defaults all 5 missing keys
    (`chunking_strategy` -> `"text"` at `ingester.py:217`; `chunk_index` -> `0` via
    `_normalize_chunk_index()`; `normalized_content` -> `None`; `chunk_type`/`source_file` ->
    `""`). Once `read_chunk_json()` enforces the full mandatory-key set, **all 5 of these tests
    will unconditionally raise `ChunkFormatError`** — this is not a maybe, it is a certain
    failure without a fixture fix.
  - **(C) Unaffected** — `test_chunk_file_has_json_suffix` (542-554),
    `test_source_file_field_has_json_extension` (557-567),
    `test_ingester_chunk_dir_collects_json_files` (570-583),
    `test_collect_source_files_returns_json_only` (517-527),
    `test_collect_source_files_ignores_txt` (529-540) — these only exercise
    `collect_source_files()` (unrelated to `read_chunk_json()`) or do a plain `json.load`
    round-trip, never through `RagIngester`'s strict reader. No change needed.
- An additional inert fixture, `local_file` (lines 290-309, a raw dict literal, not built via
  the helper), is missing envelope keys (`schema_version`/`artifact_type`/`created_by`)
  entirely and is written to `rag-src/` — but no test in this file re-reads it through any
  reader; it exists only to produce a `file://` URI string used as the `url` value inside the
  separately-constructed chunk-directory fixtures in group (B). It requires no fix for this
  plan (verified: it is never parsed by `read_crawl_json()` or any consumer).

## Design decisions
- Add a second, correctly-named helper — e.g. `_make_chunk_output_json(url=..., title=...,
  lang=..., content=..., **chunk_fields)` — that returns a fully chunk-mandatory-key-compliant
  dict (all 5 crawl-shared fields plus `chunk_index=0`, `chunking_strategy="text"`,
  `normalized_content=None`, `chunk_type="text"`, `source_file=""`, plus `etag`/`last_modified`
  nullable and envelope fields), and repoint the 5 group-(B) tests to use it instead of
  `_make_chunk_json()`. Do not repurpose `_make_chunk_json()` itself in place, since group-(A)
  tests genuinely need the crawl-shaped output it already correctly produces.
- Keep `_make_chunk_json()`'s name and behavior unchanged for group (A)'s benefit; the new
  helper is additive, not a replacement, to avoid touching the 2 already-correct call sites.

## Alternatives considered
- Renaming `_make_chunk_json()` to something crawl-accurate (e.g. `_make_crawl_json()`) and
  updating its 7 call sites (2 correct + 5 incorrect) — rejected as broader churn than
  necessary for this plan: the misleading name is a pre-existing readability issue, not
  something this migration is required to fix, and renaming risks unrelated merge conflicts
  with `chunk_splitter.py`'s test coverage that also touches this area. Flag the naming issue
  in the PR description instead; fix only the functional gap (missing chunk-mandatory keys)
  that the schema migration actually requires.
- Making chunk-mandatory fields optional with defaults inside the new helper (mirroring
  `ChunkDocument`'s old, now-removed defaults) — rejected: that would recreate exactly the
  permissive behavior this plan eliminates; the new helper's whole purpose is to produce
  fully-valid fixtures without leaning on removed defaults.

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingestion_pipeline.py`

### Procedure
1. Add a new helper function near `_make_chunk_json()` (after line 113), e.g.:
   ```python
   def _make_chunk_output_json(
       url, title, lang, content,
       chunk_index=0, chunking_strategy="text", normalized_content=None,
       chunk_type="text", source_file="",
   ) -> dict:
       ...  # all crawl-shared fields (url/title/lang/content/code_blocks/etag/last_modified
       ...  # + envelope) plus the 5 chunk-mandatory fields above
   ```
2. In each of the 5 group-(B) call sites (lines ~183-188, ~226-231, ~319-324, ~382-387/417-422,
   ~452-457/486-491), replace the `_make_chunk_json(...)` call with
   `_make_chunk_output_json(...)`, preserving each test's specific `url`/`title`/`lang`/
   `content` argument values and any post-construction overrides (e.g. `chunk_data2["etag"] =
   ...` at line 492 in `test_sha256_etag_changes_triggers_reingest`).
3. Leave the `chunk_json` fixture (lines 129-142) and its 2 consuming tests (144-174) using
   `_make_chunk_json()` unchanged — they are already correct crawl-side usage.
4. Leave group (C)'s 5 tests and the inert `local_file` fixture unchanged.

### Method
- Additive helper, targeted call-site swap in exactly 5 places — no change to test assertions,
  only to the fixture-construction call that feeds each test's `ingest_all()` invocation.

### Details
- `test_sha256_different_content_triggers_reingest` and `test_sha256_etag_changes_triggers_reingest`
  each build TWO chunk dicts (`chunk_data1`/`chunk_data2`) — both must switch to the new
  helper, including preserving the post-construction field override at line 492
  (`chunk_data2["etag"] = ...`) which becomes a keyword argument or a post-construction
  dict-key assignment on the new helper's returned dict (the helper still returns a plain
  dict, not a dataclass, so in-place key overrides after construction remain valid).

## Compatibility considerations
- None beyond the fixture fix — no production behavior is affected; this restores the 5
  affected tests' ability to exercise `ingest_all()`'s real ingestion path exactly as they did
  before, just with a schema-compliant fixture.

## Security considerations
N/A — test-only file, no external input surface.

## Rollback considerations
- Additive change (new helper function); the 5 call-site edits are independently revertable
  per test if needed.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_rag_ingestion_pipeline.py -v` after `ingester.py`'s
  migration lands — all 12 tests pass, specifically confirming the 5 group-(B) tests no longer
  raise `ChunkFormatError`.
- Spot-check group (A)'s 2 tests and group (C)'s 5 tests remain unaffected (no fixture change
  applied to them).

## Out of scope
- Renaming `_make_chunk_json()` to a crawl-accurate name — flag as a pre-existing readability
  issue, not fixed here (see Alternatives considered).
- `ingester.py`'s own reader migration.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260820-094150_plan.md
- Source implementation procedure: N/A
- Generated at: 20260821-124913
- Related target files: test_rag_ingestion_pipeline.py
