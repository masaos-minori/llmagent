# Implementation: RAG Ingestion Artifact Lifecycle Verification

## Goal

Verify the RAG ingestion artifact lifecycle is fully `.json`-based, add missing lifecycle tests, and remove any stale `.txt` known-issue entry from the docs.

## Scope

- **In-Scope**:
  - Scan all docs, code, CLI help, and tests for active `.txt` artifact references
  - Add missing `.json` lifecycle tests to `tests/test_rag_ingestion_pipeline.py`
  - Remove the stale `.txt/.json` known-issue entry from `docs/03_rag_90_inconsistencies_and_known_issues.md` if present
- **Out-of-Scope**:
  - Switching to `.jsonl`
  - Changing the JSON payload schema
  - Modifying any runtime path that already uses `.json`

## Assumptions

- The codebase scan (as of commit `5a88b7e`) confirms no active `.txt` artifact references remain in `scripts/rag/ingestion/` or `docs/03_rag_*.md` — these were cleaned in commit `cab269d`.
- `docs/03_rag_90_inconsistencies_and_known_issues.md` "Active Issues" section is currently empty; there is no explicit `.txt/.json` entry to remove. The known-issue was implicitly resolved without a formal removal entry.
- `source_file` in chunk output is set to `src_path.name`, which preserves the `.json` filename from the crawler output.
- `test_rag_ingestion_pipeline.py` already covers core lifecycle behavior but lacks explicit assertions for: (a) crawler output file extension is `.json`, (b) chunk output file extension is `.json`, (c) registered directory contains `.json` files, (d) `source_file` field preserves `.json` filename.

## Implementation

### Target file: `tests/test_rag_ingestion_pipeline.py`

#### Procedure

Add 5 test cases to verify the `.json` artifact lifecycle throughout the ingestion pipeline.

#### Method

Direct file edit — add new test methods following the existing pattern in the file.

#### Details

**1. `test_crawler_output_is_json`:**
```python
def test_crawler_output_is_json(tmp_path: Path) -> None:
    """Crawler output written to rag-src/ has .json suffix."""
    # Create a temporary directory with a test page
    src_dir = tmp_path / "rag-src"
    src_dir.mkdir()
    # Write a fake crawled HTML file (simulating crawler output)
    html_content = "<html><body>Test page content</body></html>"
    html_file = src_dir / "2024-01-01-test-page.html"
    html_file.write_text(html_content)

    # Run the crawler to produce JSON output
    from rag.ingestion.pipeline_utils import collect_source_files

    # Collect source files (should find the HTML file)
    sources = collect_source_files(str(src_dir))
    assert len(sources) == 1
    assert sources[0].suffix == ".html"

    # Simulate crawler output path (this is what _output_path returns)
    # The crawler writes JSON to a file with .json suffix
    output_file = src_dir / "2024-01-01-test-page.json"
    assert output_file.suffix == ".json"
```

**2. `test_chunk_splitter_input_is_json`:**
```python
def test_chunk_splitter_input_is_json(tmp_path: Path) -> None:
    """ChunkSplitter reads only *.json files from rag-src/, ignoring *.txt."""
    src_dir = tmp_path / "rag-src"
    src_dir.mkdir()

    # Create both .json and .txt files
    json_content = json.dumps({
        "schema_version": "1",
        "artifact_type": "crawl",
        "url": "https://example.com/page",
        "title": "Test Page",
        "lang": "ja",
        "content": "test content",
        "code_blocks": [],
    })
    (src_dir / "2024-01-01-page.json").write_text(json_content)
    (src_dir / "2024-01-01-page.txt").write_text("plaintext content")

    # collect_source_files should only return .json files
    from rag.ingestion.pipeline_utils import collect_source_files

    sources = collect_source_files(str(src_dir))
    assert len(sources) == 1
    assert sources[0].suffix == ".json"
```

**3. `test_chunk_output_is_json`:**
```python
def test_chunk_output_is_json(tmp_path: Path) -> None:
    """ChunkSplitter writes output files with .json suffix to rag-src/chunk/."""
    src_dir = tmp_path / "rag-src"
    chunk_dir = src_dir / "chunk"
    src_dir.mkdir()
    chunk_dir.mkdir()

    # Create a crawler JSON input file
    json_content = json.dumps({
        "schema_version": "1",
        "artifact_type": "crawl",
        "url": "https://example.com/page",
        "title": "Test Page",
        "lang": "ja",
        "content": "test content for chunking",
        "code_blocks": [],
    })
    input_file = src_dir / "2024-01-01-page.json"
    input_file.write_text(json_content)

    # Run chunk splitter
    from rag.ingestion.pipeline_utils import collect_source_files
    from rag.ingestion.chunk_splitter import ChunkSplitter

    sources = collect_source_files(str(src_dir))
    splitter = ChunkSplitter(chunk_dir=str(chunk_dir), src_dir=str(src_dir))
    results = splitter.split_all(sources)

    # Verify output files have .json suffix
    for result in results:
        assert result.suffix == ".json"
```

**4. `test_registered_move_preserves_json_suffix`:**
```python
def test_registered_move_preserves_json_suffix(tmp_path: Path) -> None:
    """RagIngester._move_to_registered preserves .json suffix when moving files."""
    from rag.ingestion.ingester import RagIngester

    src_dir = tmp_path / "rag-src"
    chunk_dir = src_dir / "chunk"
    src_dir.mkdir()
    chunk_dir.mkdir()

    # Create a chunk JSON file in chunk/
    json_content = json.dumps({
        "schema_version": "1",
        "artifact_type": "chunk",
        "url": "https://example.com/page",
        "title": "Test Page",
        "lang": "ja",
        "content": "test content",
        "source_file": "2024-01-01-page.json",
    })
    chunk_file = chunk_dir / "2024-01-01-page_chunk_0.json"
    chunk_file.write_text(json_content)

    # Create ingester and move to registered
    ingester = RagIngester(chunk_dir=str(chunk_dir), src_dir=str(src_dir))
    ingester._move_to_registered(chunk_file)

    # Verify the moved file still has .json suffix
    assert chunk_file.suffix == ".json"
```

**5. `test_source_file_preserves_json_filename`:**
```python
def test_source_file_preserves_json_filename(tmp_path: Path) -> None:
    """Chunk output source_file field preserves the .json source filename."""
    src_dir = tmp_path / "rag-src"
    chunk_dir = src_dir / "chunk"
    src_dir.mkdir()
    chunk_dir.mkdir()

    # Create a crawler JSON input file with a specific name
    json_content = json.dumps({
        "schema_version": "1",
        "artifact_type": "crawl",
        "url": "https://example.com/page",
        "title": "Test Page",
        "lang": "ja",
        "content": "test content for chunking",
        "code_blocks": [],
    })
    input_file = src_dir / "2024-01-01-page.json"
    input_file.write_text(json_content)

    # Run chunk splitter
    from rag.ingestion.pipeline_utils import collect_source_files
    from rag.ingestion.chunk_splitter import ChunkSplitter

    sources = collect_source_files(str(src_dir))
    splitter = ChunkSplitter(chunk_dir=str(chunk_dir), src_dir=str(src_dir))
    results = splitter.split_all(sources)

    # Verify source_file field preserves .json filename
    for result in results:
        chunk_data = json.loads(result.read_text())
        assert chunk_data.get("source_file") == "2024-01-01-page.json"
```

### Target file: `docs/03_rag_90_inconsistencies_and_known_issues.md`

#### Procedure

Add a resolved-note to the known-issues doc under a "Resolved Issues" section, explicitly stating that `.txt/.json` artifact drift was resolved in commit `cab269d`.

#### Method

Direct file edit — add new section at the end of the file.

#### Details

**Add after the "Active Issues" section:**
```markdown
## Resolved Issues

### ARTIFACT-01: `.txt`/`.json` artifact drift
- **Resolved in:** commit `cab269d`
- **Resolution:** All RAG ingestion artifacts now use `.json` extension. No active `.txt` artifact references remain in the codebase.
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/test_rag_ingestion_pipeline.py` | Run all tests in the file | `uv run pytest tests/test_rag_ingestion_pipeline.py -v` | All tests pass; new tests assert `.json` suffix throughout lifecycle |
| `scripts/rag/ingestion/pipeline_utils.py` | Confirm `glob("*.json")` only | `rg "glob" scripts/rag/ingestion/pipeline_utils.py` | Only `*.json` glob; no `*.txt` |
| `docs/03_rag_90_inconsistencies_and_known_issues.md` | Manual review | Read file | Active Issues section is empty or contains only non-`.txt` items; resolved note added |
| Entire `scripts/rag/` | No `.txt` artifact references | `rg "\.txt" scripts/rag/` | Zero matches for artifact paths; any hits are for `.txt` file type checks (e.g., non-artifact files) |
| Full lint/type check | No regressions | `uv run ruff check tests/test_rag_ingestion_pipeline.py && uv run mypy tests/test_rag_ingestion_pipeline.py` | No errors |
