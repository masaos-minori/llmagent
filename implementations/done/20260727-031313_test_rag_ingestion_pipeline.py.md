## Goal

Replace weak assertion in `test_chunk_splitter_processes_json` with an actual ChunkSplitter invocation that verifies chunk splitting behavior.

## Scope

**In-Scope:**
- Replace the test body at lines 136-146 to invoke `ChunkSplitter.process_file()` directly
- Assert on the returned chunk count and verify chunk files are written

**Out-of-Scope:**
- Adding new fixtures or changing existing ones beyond what's needed for this test

## Assumptions

1. `ChunkSplitter.process_file()` returns an integer representing the number of chunks created
2. The chunk_json fixture contains plain English text (no Markdown headings), so it will use the "text" chunking strategy
3. The existing `tmp_dir` fixture provides a writable directory for ChunkSplitter output

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | What is the expected chunk count for the fixture content (plain text × 50) | Check ChunkSplitter constants and run the test to observe actual count | False |
| UNK-02 | Whether ChunkSplitter constructor requires additional parameters beyond config | Read ChunkSplitter class definition | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `tests/test_rag_ingestion_pipeline.py:136-146` — replace test body to invoke ChunkSplitter

- **Blast Radius:**
  - Very low churn — single test method modification
  - Very low risk since change is purely test replacement

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `test_rag_ingestion_pipeline.py` and `ChunkSplitter`:
```python
# Current (weak assertion):
def test_chunk_splitter_processes_json(self, chunk_json: Path) -> None:
    assert chunk_json.exists()
    with open(chunk_json, encoding="utf-8") as f:
        data = json.load(f)
    assert "content" in data
    assert "url" in data
    assert "title" in data

# Proposed fix:
def test_chunk_splitter_processes_json(self, chunk_json: Path, tmp_path: Path) -> None:
    chunker = ChunkSplitter(config={"rag_src_dir": str(tmp_path)})
    chunk_dir = tmp_path / "chunk"
    chunk_dir.mkdir(exist_ok=True)
    result = chunker.process_file(chunk_json, force=True)
    assert result >= 1  # At least one chunk should be produced
    assert (chunk_dir / f"{chunk_json.stem}-0000.json").exists()
```

## Implementation

### Target file
`tests/test_rag_ingestion_pipeline.py`

### Procedure
1. Open `tests/test_rag_ingestion_pipeline.py`
2. Locate line 136: `def test_chunk_splitter_processes_json(self, chunk_json: Path) -> None:`
3. Add `tmp_path: Path` parameter to the method signature
4. Replace lines 137-146 with ChunkSplitter invocation logic
5. Save the file

### Method
Replace direct JSON assertions with actual ChunkSplitter invocation and verification.

### Details
- Add `tmp_path: Path` parameter to method signature
- Create `ChunkSplitter` instance with config pointing to `tmp_path`
- Create chunk directory: `chunk_dir = tmp_path / "chunk"; chunk_dir.mkdir(exist_ok=True)`
- Call `chunker.process_file(chunk_json, force=True)` and capture return value
- Assert `result >= 1` (at least one chunk produced)
- Verify chunk file exists: `(chunk_dir / f"{chunk_json.stem}-0000.json").exists()`

## Compatibility considerations

N/A — test modification has no runtime effect

## Security considerations

N/A

## Rollback considerations

- Simple revert: restore original test body from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_rag_ingestion_pipeline.py` | Test invokes ChunkSplitter and asserts on chunk count | `uv run pytest tests/test_rag_ingestion_pipeline.py::TestRagIngestionPipeline::test_chunk_splitter_processes_json -v` | Test passes with real ChunkSplitter invocation |

## Out of scope

- Adding new fixtures or changing existing ones beyond what's needed for this test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-163226_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-031313
- Related target files: tests/test_rag_ingestion_pipeline.py, rag/ingestion/chunk_splitter.py
