## Goal
- Unify RAG ingestion artifact file extensions from `.txt` to `.json`, fixing test fixtures in `tests/test_ingester.py` that still reference `.txt`.

## Scope
- **In-Scope**:
  - Replace `c.txt` references with `c.json` in `tests/test_ingester.py`
  - Verify `tests/test_ingestion_freshness.py` `.txt` is used as URL fixtures (not artifact filenames)
  - Confirm no `.txt` references in related docs (`docs/03_rag_02_ingestion_pipeline.md`, etc.)
- **Out-of-Scope**:
  - Production code changes (`scripts/rag/ingestion/`) — already clean, uses only `.json`
  - JSON payload schema changes
  - Migration to `.jsonl`

## Assumptions
1. No `.txt` references in production ingestion code (confirmed by grep)
2. No `.txt` references in docs (confirmed by grep)
3. `_write_chunk` writes arbitrary data regardless of extension — changing to `.json` is safe
4. `.txt` in `test_ingestion_freshness.py` is URL fixtures, not artifact references

## Unknowns
| Unknown | Evidence missing | Resolution | Blocking |
|---|---|---|---|
| `_write_chunk` validates file extension based on filename | test_ingester.py read — confirmed L106-L114: no validation | None | False |
| Other test files have `.txt` artifact references | grep not yet run on all tests | Check before implementation | False |

## Implementation

### Target file
`tests/test_ingester.py` — replace all `c.txt` with `c.json`

### Procedure
1. Verify `_write_chunk` does not validate extension (confirmed L106-L114)
2. Replace all `c.txt` occurrences with `c.json` in `tests/test_ingester.py`
3. Verify `test_ingestion_freshness.py` `.txt` usage is URL-only
4. Run tests to confirm no regressions

### Method
- Use `replaceAll` to replace all `c.txt` → `c.json` in `tests/test_ingester.py`
- The `_write_chunk` function (L106-L114) writes arbitrary bytes via `orjson.dumps(dataclasses.asdict(spec))` — extension is irrelevant

### Details

```python
# tests/test_ingester.py — all "c.txt" → "c.json"
# Key replacements:
#   - "c.txt", → "c.json",  (string literals)
#   - _write_chunk(tmp_path / "chunk", "c.txt") → _write_chunk(tmp_path / "chunk", "c.json")
#   - (registered_dir / "c.txt").exists() → (registered_dir / "c.json").exists()
#   - path2 = _write_chunk(chunk_dir, "c2.txt") → path2 = _write_chunk(chunk_dir, "c2.json")
#   - "c_new.txt", → "c_new.json",  (new file test)
```

## Validation plan
- Run lint: `ruff check tests/test_ingester.py` for 0 errors
- Run tests: `uv run pytest tests/test_ingester.py -x -q` to confirm all pass
- Run pre-commit: `pre-commit run --all-files` to confirm no regressions
