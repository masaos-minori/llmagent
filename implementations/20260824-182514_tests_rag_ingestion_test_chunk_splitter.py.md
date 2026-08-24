## Goal

Add two end-to-end guard tests for `chunk_splitter.py::process_file()` — one exercising
the English chunking path, one the Japanese chunking path — establishing a behavioral
baseline before any future refactor. No production code change.

## Scope

- In scope: add `test_process_file_end_to_end_english` and
  `test_process_file_end_to_end_japanese` to
  `tests/rag/ingestion/test_chunk_splitter.py`.
- Out of scope: the other 2 target files in the same plan
  (`tests/eventbus/test_eventbus_dlq.py`, `tests/db/test_sqlite_helper.py`, each with
  its own implementation procedure document); markdown heading-chunking path (already
  covered by the file's existing `TestIsMarkdownSource` tests); any production code
  change.

## Assumptions

**Corrected during this workflow's adversarial verification** — the source plan's
original Design (single mixed-language test, plain-text input, return-value
assertions) did not match `process_file()`'s actual contract. Verified this cycle
against `scripts/rag/ingestion/chunk_splitter.py`:

- `process_file(self, src_path: Path, force: bool = False) -> int` is an instance
  method on `ChunkSplitter(ChunkEnglishMixin, ChunkJapaneseMixin)`, returning only the
  written chunk count (an `int`) — not chunk objects or metadata.
- Input must be a JSON file matching the `CrawlFilePayload`/chunk-JSON shape (`url`,
  `title`, `lang`, `fetched_at`, `content`, `code_blocks`, `schema_version`,
  `artifact_type`, `created_by`, `etag`, `last_modified`) — not a plain text file with
  headed sections. `lang` is a single value for the entire document;
  `_build_text_triples` dispatches on `data.lang == "ja"` for the whole call, so one
  `process_file()` call cannot exercise both English and Japanese chunking — hence two
  separate tests/input files.
- Output is written to `{rag_src_dir}/chunk/{src_path.stem}-NNNN.json`, matching the
  `ChunkOutputPayload` schema (`schema_version`, `artifact_type`, `created_by`, `url`,
  `title`, `lang`, `source_file`, `chunk_index`, `chunk_type`, `content`,
  `normalized_content`) — metadata assertions must read these output files, not the
  `process_file()` return value.
- Construction pattern already established in
  `tests/rag/ingestion/test_rag_ingestion_pipeline.py::test_chunk_splitter_processes_json`:
  `ChunkSplitter(config={"rag_src_dir": str(tmp_path), "min_chunk": 10, "max_chunk":
  1000, "en_stopwords": [], "ja_stop_pos": []})` — this bypasses loading
  `chunk_splitter.toml` and the sudachi dictionary's default config path, using an
  explicit minimal config dict instead (though the sudachi tokenizer itself is still
  constructed in `__init__`, since it is not config-gated).
- No existing test in `tests/rag/ingestion/test_chunk_splitter.py` exercises
  `process_file()` end-to-end — confirmed via `grep -n "def test_"
  tests/rag/ingestion/test_chunk_splitter.py` (existing tests target
  `_is_markdown_source()` only, using a bare `object.__new__(ChunkSplitter)` +
  manually-set attributes, which is insufficient for a full `process_file()` call).

## Design decisions

- Use the full, config-based `ChunkSplitter(config=...)` construction (not the
  existing file's `object.__new__` shortcut), since `process_file()` exercises the
  complete chunking pipeline (tokenizer, stopwords, min/max chunk sizing), matching the
  pattern already proven in `test_rag_ingestion_pipeline.py`.
- Write two separate temp JSON input files (English, Japanese) rather than one mixed
  file, per the corrected Assumptions above.
- Assert chunk-content completeness by reading back all written
  `{stem}-NNNN.json` output files and concatenating their `content` fields, comparing
  against the original input `content` (allowing for the chunker's own
  splitting/normalization boundaries — assert no characters are dropped, not an exact
  byte-for-byte reassembly if the chunker trims whitespace at boundaries).

## Alternatives considered

- Reusing the exact `_make_chunk_json()` helper from `test_rag_ingestion_pipeline.py`
  by importing it — rejected in favor of a local, file-scoped helper in
  `test_chunk_splitter.py`: importing a private test helper across test modules is
  fragile or not achievable without an underscore-prefixed cross-module import; a
  small local copy is simpler.

## Implementation

### Target file

`tests/rag/ingestion/test_chunk_splitter.py`

### Procedure

1. Add a local helper `_make_crawl_json(lang: str, content: str, url: str = "http://
   example.com/page", title: str = "Test Page") -> dict` returning a dict with all
   `CrawlFilePayload`-plus-chunk-metadata fields (`url`, `title`, `lang`, `fetched_at`,
   `content`, `code_blocks: []`, `schema_version`, `artifact_type`, `created_by`,
   `etag`, `last_modified`), matching the shape used by
   `test_rag_ingestion_pipeline.py::_make_chunk_json`.
2. `test_process_file_end_to_end_english(tmp_path)`:
   - Write `_make_crawl_json(lang="en", content=<multi-paragraph English text>)` to a
     temp `.json` file under `tmp_path`.
   - Construct `ChunkSplitter(config={"rag_src_dir": str(tmp_path), "min_chunk": 10,
     "max_chunk": 1000, "en_stopwords": [], "ja_stop_pos": []})`.
   - Create `tmp_path / "chunk"` directory.
   - Call `chunker.process_file(input_path, force=True)`; assert the returned `int` is
     `>= 1`.
   - Read back `{tmp_path}/chunk/{input_path.stem}-*.json` output files; assert each
     has `lang == "en"`, `source_file == input_path.name`, sequential `chunk_index`
     values, and non-empty `content`.
   - Concatenate all output chunks' `content` in `chunk_index` order; assert every
     input content word/sentence appears (no loss).
3. `test_process_file_end_to_end_japanese(tmp_path)`: same shape as step 2, with
   `lang="ja"` and Japanese `content`, to exercise the `ChunkJapaneseMixin` path.

### Method

```python
def _make_crawl_json(lang: str, content: str, url: str = "http://example.com/page", title: str = "Test Page") -> dict:
    return {
        "url": url,
        "title": title,
        "lang": lang,
        "fetched_at": "2024-01-01T00:00:00",
        "content": content,
        "code_blocks": [],
        "schema_version": "1",
        "artifact_type": "chunk",
        "created_by": "chunk_splitter",
        "etag": "etag-test",
        "last_modified": "2024-01-01T00:00:00",
    }


def test_process_file_end_to_end_english(tmp_path: Path) -> None:
    content = "Hello world from the test page. " * 50
    data = _make_crawl_json(lang="en", content=content)
    src = tmp_path / "en-page.json"
    src.write_text(json.dumps(data), encoding="utf-8")

    chunk_dir = tmp_path / "chunk"
    chunk_dir.mkdir(exist_ok=True)
    chunker = ChunkSplitter(config={
        "rag_src_dir": str(tmp_path), "min_chunk": 10, "max_chunk": 1000,
        "en_stopwords": [], "ja_stop_pos": [],
    })

    result = chunker.process_file(src, force=True)
    assert result >= 1

    outputs = sorted(chunk_dir.glob(f"{src.stem}-*.json"))
    assert len(outputs) == result
    reassembled = ""
    for i, out_path in enumerate(outputs):
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        assert payload["lang"] == "en"
        assert payload["source_file"] == src.name
        assert payload["chunk_index"] == i
        assert payload["content"]
        reassembled += payload["content"]
    assert "Hello world" in reassembled
```
`test_process_file_end_to_end_japanese` mirrors this with `lang="ja"` and Japanese
`content` (e.g. a repeated Japanese sentence), asserting `payload["lang"] == "ja"`
instead.

### Details

`process_file()` (verified this cycle, `scripts/rag/ingestion/chunk_splitter.py:129-`):
reads the source JSON via `_read_source_data()` (`read_json_file` → `ChunkDocument`),
builds chunk triples via `_build_chunk_list()` (dispatches to English/Japanese/markdown
chunkers based on `data.lang`/`_is_markdown_source()`), then writes them via
`_write_chunk_files()` to `{chunk_dir}/{src_path.stem}-NNNN.json`, returning the
written count.

## Compatibility considerations

Test-only addition; no production code, schema, or public interface changes.

## Security considerations

N/A: test-only change against temporary files under `tmp_path`; no secrets, network,
or external input involved.

## Rollback considerations

Delete the two new test functions and the local `_make_crawl_json` helper; no other
rollback steps required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/rag/ingestion/test_chunk_splitter.py` | Integration (end-to-end on real text) | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` | 2 new tests pass (English + Japanese), no regression in existing tests |
| `tests/rag/ingestion/` (full) | Regression | `uv run pytest tests/rag/ingestion/ -v` | No new failures |
| `tests/rag/ingestion/test_chunk_splitter.py` | Static | `uv run ruff check tests/rag/ingestion/test_chunk_splitter.py` + `uv run mypy tests/rag/ingestion/test_chunk_splitter.py` | Clean |

## Out of scope

Markdown heading-chunking path (already covered); the other 2 target files in this
plan; any change to `scripts/rag/ingestion/chunk_splitter.py`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation update in scope |

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
- **Source issue**: N/A: not applicable in this phase (the source plan's own Traceability records `Source issue: N/A` — this plan predates the issue-to-plan pipeline merge)
- **Source requirement**: `requires/done/20260726-125412_require.md`
- **Source plan**: `plans/20260823-194857_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260824-182514
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`

## Adversarial verification notes (this cycle)

- **Substantive plan correction applied**: the source plan's original Design for this
  target (single test, "mixed English/Japanese input content," plain-text file,
  assertions on "the actual returned/stored chunk count" and "each chunk's
  `source_path`/heading metadata") did not match `process_file()`'s real contract —
  verified by reading `scripts/rag/ingestion/chunk_splitter.py` in full this cycle:
  the method returns only an `int` chunk count, requires a `CrawlFilePayload`-shaped
  JSON input with one `lang` per document, and per-chunk metadata is only available by
  reading the written output JSON files. Corrected `plans/20260823-194857_plan.md`'s
  Design (item 3), Implementation steps, Validation plan, and Risks sections in place
  to two per-language tests matching the actual contract, informed by the existing
  `test_chunk_splitter_processes_json` test in
  `tests/rag/ingestion/test_rag_ingestion_pipeline.py` (which already demonstrates the
  correct construction pattern). The plan's own Risks section had already anticipated
  this possibility and deferred exact assertions to implementation time — this cycle
  resolved that deferred risk rather than leaving it open.
- Confirmed via `grep -n "def test_" tests/rag/ingestion/test_chunk_splitter.py` that
  no existing test exercises `process_file()` end-to-end, and via
  `grep -rl "20260823-194857_plan" implementations/ implementations/done/` that no
  duplicate implementation procedure document exists.
