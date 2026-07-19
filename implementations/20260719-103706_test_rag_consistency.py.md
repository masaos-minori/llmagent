## Goal

Update the existing behavior-lock assertion that currently locks in the removed-command bug, and
add a drift-guard test so a future re-introduction of a `/db`-prefixed command reference in
`summarize_issues()` fails loudly, once `scripts/db/rag_consistency.py`'s guidance strings are fixed
(paired doc: `implementations/20260719-103628_rag_consistency.py.md`).

No prior implementation doc exists for this specific change (checked: `find implementations
implementations/done -iname "*test_rag_consistency*"` matches only
`implementations/done/20260618-093440_test_rag_consistency.py.md`, an earlier, unrelated historical
doc — checked, not a genuine overlap, since it predates this issue's discovery and does not touch
`test_summarize_issues_fts_gap_includes_rebuild_guidance` or any drift-guard test).

## Scope

**In scope**
- Update `TestRagConsistencySeverity::test_summarize_issues_fts_gap_includes_rebuild_guidance`
  (currently `tests/test_rag_consistency.py:248-259`): change the assertion from
  `assert any("/db rag rebuild-fts" in i for i in issues)` to
  `assert any("/session rag-rebuild-fts" in i for i in issues)`.
- Add a new drift-guard test to `TestRagConsistencySeverity` asserting that no string returned by
  `summarize_issues()`, across all four triggerable issue scenarios already exercised elsewhere in
  this file, contains the substring `"/db "` or `"/db rag"`.

**Out of scope**
- Any change to `test_summarize_issues_orphan_vec_includes_force_guidance` (line 261-267) or
  `test_vec_chunk_mismatch_includes_repair_guidance` (line 322-330) — both assert
  `ingester.py --force`-style guidance, which is accurate and unchanged (verified out of scope by the
  plan itself).
- Any change to `_make_rag_db`/`_insert_doc`/`_insert_chunk` helpers (lines 80-108) — reused as-is.
- Any change to `TestRagConsistencyReport` or other test classes in this file (lines 1-200) — not
  touched by this plan.

## Assumptions

1. Verified by direct read of `tests/test_rag_consistency.py:248-259`
   (`test_summarize_issues_fts_gap_includes_rebuild_guidance`): current content is exactly:
   ```python
   def test_summarize_issues_fts_gap_includes_rebuild_guidance(self) -> None:
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       chunk_id = _insert_chunk(db, doc_id, "rebuild guidance test")
       db.execute(
           "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
           (chunk_id, "rebuild guidance test"),
       )
       db.commit()

       issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
       assert any("/db rag rebuild-fts" in i for i in issues)
   ```
   Only the final assertion line (line 259) needs to change; the fixture setup (lines 249-256) stays
   as-is since it correctly triggers `fts_gap > 0` (the WARNING-severity branch), unaffected by the
   string-literal fix in `rag_consistency.py`.
2. The plan's cited test name and line range (248-259) match the current file exactly — no drift.
3. The four triggerable `summarize_issues()` issue types and their existing fixture setups in this
   file (used as the drift-guard test's building blocks):
   - `fts_gap > 0` (WARNING): `test_summarize_issues_fts_gap_has_warning_prefix`
     (lines 227-238) / `test_summarize_issues_fts_gap_includes_rebuild_guidance` (lines 248-259) —
     insert a chunk, then `INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)`
     to remove it from FTS only.
   - `fts_orphan_count > 0` (CRITICAL): `test_fts_orphan_detected_when_fts_exceeds_chunks`
     (lines 202-225) — insert a chunk, delete its parent document (cascades to remove the chunk),
     then manually re-insert an orphan `chunks_fts` row.
   - `orphan_vec_count > 0` (CRITICAL): `test_summarize_issues_orphan_vec_has_critical_prefix`
     (lines 240-246) — `INSERT INTO chunks_vec (chunk_id) VALUES (99999)` with no matching chunk row.
   - `vec != chunks` (WARNING): `test_vec_chunk_mismatch_detected` (lines 307-320) — insert a chunk
     without a corresponding `chunks_vec` row.
   Each scenario uses its own fresh `_make_rag_db()` instance (in-memory SQLite, no shared state
   across scenarios) — the drift-guard test builds four independent DBs, one per scenario, mirroring
   this existing pattern rather than attempting to trigger all four issues in a single shared DB
   (which is unnecessary and would risk cross-scenario interference, e.g. the `fts_gap` and
   `fts_orphan_count` setups both mutate `chunks_fts` in ways that could mask each other if combined).
4. `summarize_issues()` returns `list[str]`; every element is independent per issue type — checking
   `"/db "` (with trailing space, to also catch a bare `/db` command) and `"/db rag"` as two literal
   substrings covers both the flat and `rag`-scoped removed command forms, per the plan's
   Implementation step 3 wording.

## Implementation

### Target file

`tests/test_rag_consistency.py` (existing file; `TestRagConsistencySeverity` class starts at line
201).

### Procedure

1. Edit line 259 in `test_summarize_issues_fts_gap_includes_rebuild_guidance`:
   ```python
   assert any("/db rag rebuild-fts" in i for i in issues)
   ```
   to:
   ```python
   assert any("/session rag-rebuild-fts" in i for i in issues)
   ```
2. Add a new test method to `TestRagConsistencySeverity` (placement: after
   `test_fts_orphan_does_not_report_fts_gap_doc_ids`, the last method in the class, or any position
   within the class — ordering has no effect on test semantics):
   ```python
   def test_summarize_issues_never_references_removed_db_command(self) -> None:
       """Drift guard: no summarize_issues() output may reference a removed '/db'-prefixed command."""
       all_issues: list[str] = []

       # fts_gap > 0
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       chunk_id = _insert_chunk(db, doc_id, "drift guard fts gap")
       db.execute(
           "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
           (chunk_id, "drift guard fts gap"),
       )
       db.commit()
       all_issues += summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]

       # fts_orphan_count > 0
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       chunk_id = _insert_chunk(db, doc_id, "drift guard fts orphan")
       db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
       db.execute(
           "INSERT INTO chunks_fts (rowid, content) VALUES (?, ?)",
           (chunk_id + 1000, "ghost entry"),
       )
       db.commit()
       all_issues += summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]

       # orphan_vec_count > 0
       db = _make_rag_db()
       db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (77777)", ())
       db.commit()
       all_issues += summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]

       # vec != chunks
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       _insert_chunk(db, doc_id, "drift guard vec mismatch")
       db.commit()
       all_issues += summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]

       assert len(all_issues) == 4, "expected exactly one issue string per triggered scenario"
       assert not any("/db " in i for i in all_issues)
       assert not any("/db rag" in i for i in all_issues)
   ```
3. Run `uv run ruff format tests/test_rag_consistency.py` and
   `uv run ruff check tests/test_rag_consistency.py --fix`.

### Method

Straight test-assertion update plus one new test method built entirely from patterns already present
in this file (`_make_rag_db`/`_insert_doc`/`_insert_chunk` helpers, existing per-scenario fixture
setups). No new fixtures, no new helper functions, no changes to production code.

### Details

No new types or imports beyond what the file already imports (`check_rag_consistency`,
`is_consistent`, `summarize_issues` at line 11). The `len(all_issues) == 4` assertion is a sanity
check that each of the four independent DB scenarios triggers exactly one issue (guards against a
future `check_rag_consistency()` change silently making a scenario stop triggering, which would
otherwise let the drift-guard's substring assertions pass vacuously on an empty list).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format tests/test_rag_consistency.py && uv run ruff check tests/test_rag_consistency.py` | 0 errors |
| Type check | `uv run mypy tests/test_rag_consistency.py` | 0 new errors vs. baseline |
| Updated assertion passes | `uv run pytest tests/test_rag_consistency.py -v -k test_summarize_issues_fts_gap_includes_rebuild_guidance` | passes only after paired `rag_consistency.py` doc's fix lands (`/session rag-rebuild-fts` present) |
| New drift-guard test passes | `uv run pytest tests/test_rag_consistency.py -v -k test_summarize_issues_never_references_removed_db_command` | passes after the paired fix lands |
| Full file regression | `uv run pytest tests/test_rag_consistency.py -v` | all 16 tests pass (15 existing + 1 new) |
| No stale substring anywhere in file | `rg -n "/db rag rebuild-fts" tests/test_rag_consistency.py` | 0 matches after step 1's edit |
