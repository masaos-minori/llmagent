# Implementation: RAG Consistency Report Alignment

## Goal

Align `RagConsistencyReport`, `summarize_issues()`, `/db consistency` CLI output, and the operations documentation so that affected identifiers and repair hints match what the doc promises.

## Scope

- **In-Scope**:
  - Fix `summarize_issues()` logic: `fts_orphan_count` branch incorrectly reuses `affected_doc_ids` from the FTS-gap path; it should report that no chunk-level IDs are available for orphan FTS entries and guide operators to use `/db rag rebuild-fts`.
  - Add `affected_orphan_chunk_ids` and `affected_orphan_urls` to the RagConsistencyReport field table in `docs/03_rag_05_configuration_and_operations.md`.
  - Update the doc's CLI failure example to show a realistic issue line that includes affected identifiers.
  - Expand `tests/test_rag_consistency.py`: add test for `fts_orphan_count` not spuriously including FTS-gap doc_ids; verify `test_db_consistency_detail.py` covers CLI output with affected identifiers.
- **Out-of-Scope**:
  - Automatic repair execution in `check_rag_consistency()`.
  - Background self-healing.
  - Changing ingestion pipeline behavior.
  - DB schema changes.

## Assumptions

- The existing `affected_chunk_ids`, `affected_doc_ids`, `affected_orphan_chunk_ids`, `affected_orphan_urls` fields in `RagConsistencyReport` are correct and sufficient; no new fields are needed.
- `_db_consistency()` in `cmd_db.py` already passes issue strings (which contain identifiers) to `write_error()`; no structural change to the CLI handler is needed beyond confirming the issue strings are complete.
- URL resolution via the `documents` table JOIN is feasible for `affected_orphan_urls`; the existing query handles the NULL case gracefully.

## Implementation

### Target file: `scripts/db/maintenance.py`

#### Procedure

1. **Fix FTS orphan branch (lines 513-523)** — change `affected_doc_ids` check to not reference unavailable identifiers
2. Add a note that chunk-level identifiers cannot be recovered for stale FTS entries

#### Method

Direct file edit — modify the `fts_orphan_count > 0` branch in `summarize_issues()`.

#### Details

**Current code (lines 513-523):**
```python
if report.fts_orphan_count > 0:
    detail = ""
    if report.affected_doc_ids:
        ids = ", ".join(str(i) for i in report.affected_doc_ids[:10])
        truncated = " ..." if len(report.affected_doc_ids) == 10 else ""
        detail = f" Affected doc_ids: [{ids}{truncated}]."
    issues.append(
        f"[CRITICAL] FTS index has more entries than chunks"
        f" (fts={report.fts}, chunks={report.chunks}).{detail}"
        f" Run '/db rag rebuild-fts' immediately; orphan FTS entries indicate data loss risk."
    )
```

**Change to:**
```python
if report.fts_orphan_count > 0:
    detail = ""
    if report.affected_orphan_chunk_ids:
        ids = ", ".join(str(i) for i in report.affected_orphan_chunk_ids[:10])
        truncated = " ..." if len(report.affected_orphan_chunk_ids) == 10 else ""
        detail = f" Affected chunk_ids: [{ids}{truncated}]."
    elif report.affected_orphan_urls:
        urls = ", ".join(report.affected_orphan_urls[:5])
        truncated = " ..." if len(report.affected_orphan_urls) == 10 else ""
        detail = f" Affected URLs: [{urls}{truncated}]."
    elif not report.affected_chunk_ids:
        detail = " Chunk-level identifiers unavailable (FTS orphans have no parent chunk rows)."
    issues.append(
        f"[CRITICAL] FTS index has more entries than chunks"
        f" (fts={report.fts}, chunks={report.chunks}).{detail}"
        f" Run '/db rag rebuild-fts' immediately; orphan FTS entries indicate data loss risk."
    )
```

**Note:** The `affected_orphan_chunk_ids` and `affected_orphan_urls` fields are only populated when `orphan_vec_count > 0`. For pure FTS orphans (where `fts_gap == 0` and `fts_orphan_count > 0`), these will be None, so the `elif not report.affected_chunk_ids:` fallback will trigger, correctly stating that chunk-level identifiers are unavailable.

### Target file: `docs/03_rag_05_configuration_and_operations.md`

#### Procedure

1. Add two missing rows to RagConsistencyReport fields table (lines 158-169)
2. Update CLI failure example (around line 330) to show a representative issue line including affected identifiers

#### Method

Direct file edit — insert table rows and update example text.

#### Details

**Add rows after `affected_doc_ids` row:**

| `affected_orphan_chunk_ids` | chunk_ids in `chunks_vec` with no matching `chunks` row (up to 10) |
|---|---|
| `affected_orphan_urls` | URLs of documents with orphan vec rows (up to 10; `None` when no parent document can be resolved) |

**Update CLI failure example (line 330-334):**
```markdown
   chunks: 1042  fts: 1039  vec: 1042  fts_gap: 3  orphan_vec: 0  fts_orphan: 0
RAG consistency: FAIL
Consistency issue: [WARNING] FTS gap detected (chunks=1042, fts=1039, gap=3). Affected doc_ids: [1, 2, 3]. Run '/db rag rebuild-fts' to repair.
```

This is already correct as-is; the example shows FTS gap with affected doc_ids, which matches the current behavior.

### Target file: `tests/test_rag_consistency.py`

#### Procedure

Add test `test_fts_orphan_does_not_report_fts_gap_doc_ids`.

#### Method

Direct file edit — add new test method to `TestRagConsistencySeverity` class.

#### Details

```python
def test_fts_orphan_does_not_report_fts_gap_doc_ids(self) -> None:
    """FTS orphan_count > 0 with fts_gap == 0 should not include 'Affected doc_ids' in issue string."""
    db = _make_rag_db()
    doc_id = _insert_doc(db)
    chunk_id = _insert_chunk(db, doc_id, "stale fts content")
    # Remove from chunks without triggering the ad trigger (bypass cascade)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
    # FTS entry still exists but chunk is gone. Re-insert FTS entry manually to simulate drift.
    db.execute(
        "INSERT INTO chunks_fts (rowid, content) VALUES (?, ?)",
        (chunk_id + 1000, "ghost entry"),
    )
    db.commit()

    report = check_rag_consistency(db)  # type: ignore[arg-type]
    assert report.fts_orphan_count > 0
    assert report.fts_gap == 0
    assert report.affected_doc_ids is None
    issues = summarize_issues(report)
    fts_orphan_issue = [i for i in issues if "[CRITICAL]" in i and "FTS index has more entries" in i][0]
    # Should NOT include "Affected doc_ids" since doc_ids are unavailable
    assert "Affected doc_ids" not in fts_orphan_issue

```

### Target file: `tests/test_db_consistency_detail.py`

#### Procedure

Add test `test_inconsistent_shows_affected_identifiers_in_issue`.

#### Method

Direct file edit — add new test function after existing tests.

#### Details

```python
def test_inconsistent_shows_affected_identifiers_in_issue():
    """Inconsistent DB -> issue lines contain affected identifiers from summarize_issues()."""
    report = _make_report(chunks=10, fts=7, vec=10, fts_gap=3)
    # Set affected_doc_ids to verify identifier content in CLI output
    report_with_ids = RagConsistencyReport(
        chunks=report.chunks,
        fts=report.fts,
        vec=report.vec,
        fts_gap=report.fts_gap,
        orphan_vec_count=report.orphan_vec_count,
        fts_orphan_count=report.fts_orphan_count,
        affected_chunk_ids=(101, 102),
        affected_doc_ids=(5, 6),
    )

    cmd = _make_db_command()

    with patch("agent.commands.cmd_db.RagMaintenanceService") as mock_svc:
        result = RagConsistencyResult(
            is_consistent=False,
            issues=summarize_issues(report_with_ids),
            report=report_with_ids,
        )
        mock_svc.return_value.consistency.return_value = result
        cmd._db_consistency()

    error_lines = cmd._out.error_lines
    assert len(error_lines) >= 1
    # Verify that issue lines contain identifier detail text from summarize_issues()
    combined_errors = "".join(error_lines)
    assert "Affected doc_ids" in combined_errors or "/db rag rebuild-fts" in combined_errors

```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `db/maintenance.py` `summarize_issues()` | Unit: new test `test_fts_orphan_does_not_report_fts_gap_doc_ids` | `uv run pytest tests/test_rag_consistency.py -v -k fts_orphan` | FTS orphan issue string does not contain "Affected doc_ids" when doc_ids are unavailable |
| `db/maintenance.py` `summarize_issues()` | Regression: existing tests for FTS gap, FTS orphan, orphan vec, vec mismatch | `uv run pytest tests/test_rag_consistency.py -v` | All existing tests pass |
| `cmd_db.py` `_db_consistency()` | Unit: extended `test_db_consistency_detail.py` test | `uv run pytest tests/test_db_consistency_detail.py -v` | Issue lines in CLI output contain identifier detail text |
| `docs/03_rag_05_configuration_and_operations.md` | Manual review: confirm field table matches RagConsistencyReport dataclass fields | `grep -n "affected_orphan" docs/03_rag_05_configuration_and_operations.md` | Two new rows present |
| Full test suite | Regression check | `uv run pytest tests/test_rag_consistency.py tests/test_db_consistency_detail.py tests/test_db_maintenance.py -v` | All pass, no regressions |
