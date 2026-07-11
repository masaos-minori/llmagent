# Implementation Procedure: tests/test_rag_index_integrity.py — fixture FK/cascade prerequisite

Source plan: `plans/20260711-164446_plan.md` — Phase 2

## Goal

Fix the test fixture in `tests/test_rag_index_integrity.py` so it actually enables and
exercises `ON DELETE CASCADE`: add `PRAGMA foreign_keys=ON` to the `db` fixture (currently
absent, so CASCADE has never been enforced by any test in this file), and add the
`chunks_vec_ad` trigger to `_SCHEMA_SQL` (currently absent) so the defensive-backstop
behavior can be tested. This is a prerequisite for Phase 3's new/updated assertions.

## Scope

**In-Scope:**
- `tests/test_rag_index_integrity.py`: the `db` fixture (currently lines ~102-109) — add
  `conn.execute("PRAGMA foreign_keys=ON")` immediately after `sqlite3.connect(":memory:")`
- `tests/test_rag_index_integrity.py`: `_SCHEMA_SQL` (currently lines 28-70) — append the
  `chunks_vec_ad` trigger DDL

**Out-of-Scope:**
- Any test function body/docstring changes (covered by the Phase 3 implementation doc)
- `_FakeSQLiteHelper` class itself — no change
- `chunks_ai`/`chunks_ad`/`chunks_au` (FTS5 sync triggers) — already present, unchanged
- Any production source file

## Assumptions

1. `_SCHEMA_SQL` (lines 28-70) defines `chunks.doc_id ... REFERENCES documents(doc_id) ON
   DELETE CASCADE` (line 38) but the `db` fixture (lines 102-109) never executes `PRAGMA
   foreign_keys=ON` — confirmed by direct read. SQLite disables FK enforcement by default,
   so no test in this file today actually exercises CASCADE.
2. `_SCHEMA_SQL` omits the `chunks_vec_ad` trigger entirely — confirmed by direct read;
   only `chunks_ai`/`chunks_ad`/`chunks_au` (FTS triggers) are present.
3. Adding `PRAGMA foreign_keys=ON` may surface previously-hidden FK-related behavior
   differences in other tests in this same file (flagged as a Risk in the plan) — this must
   be checked by running the full file, not just the directly-modified tests, in Phase 5
   verification (out of scope for this doc, but the fixture change here is what enables it).

## Implementation

### Target file

`tests/test_rag_index_integrity.py`

### Procedure

1. Locate `_SCHEMA_SQL` (currently lines 28-70, ending with the `chunks_au` trigger
   definition).
2. Append a new trigger definition to `_SCHEMA_SQL`:
   ```sql
   CREATE TRIGGER IF NOT EXISTS chunks_vec_ad
   AFTER DELETE ON chunks BEGIN
       DELETE FROM chunks_vec WHERE chunk_id = old.chunk_id;
   END;
   ```
3. Locate the `db` fixture (currently lines 102-109):
   ```python
   @pytest.fixture
   def db() -> Generator[_FakeSQLiteHelper]:
       conn = sqlite3.connect(":memory:")
       conn.row_factory = sqlite3.Row
       conn.executescript(_SCHEMA_SQL)
       conn.commit()
       yield _FakeSQLiteHelper(conn)
       conn.close()
   ```
4. Add `conn.execute("PRAGMA foreign_keys=ON")` immediately after
   `conn = sqlite3.connect(":memory:")` (before or after setting `row_factory` — either
   order is fine since PRAGMA is independent of row_factory).

### Method

Direct in-place edits: one appended trigger block in the `_SCHEMA_SQL` string constant, one
added line in the `db` fixture function body. No new fixtures, no signature changes.

### Details

Resulting fixture shape (illustrative, not final production code — exact line placement
may vary slightly):

```python
@pytest.fixture
def db() -> Generator[_FakeSQLiteHelper]:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    yield _FakeSQLiteHelper(conn)
    conn.close()
```

`_SCHEMA_SQL` gains the `chunks_vec_ad` trigger block appended after the existing
`chunks_au` trigger, before the closing `"""`.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this fixture change:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_rag_index_integrity.py` | 0 errors |
| Tests | `uv run pytest tests/test_rag_index_integrity.py -v` | All existing tests still pass after the fixture change (before Phase 3's new assertions are added) — confirms enabling `PRAGMA foreign_keys=ON` does not break any currently-passing test |
| Regression | Full-file run as part of Phase 5, not just modified tests | Any newly-surfaced failure from enabling FK enforcement is itself valuable information and must be triaged, not silently worked around |
