## Goal
Rewrite the functionally-empty INV-07 test to actually exercise the production manual
rebuild path (`RagMaintenanceService.rebuild_fts()`) against trigger-populated data,
and add a new static-analysis test for DESIGN-2 (no unsanctioned direct `chunks_fts`
writes).

## Scope
In scope: (1) rewrite
`test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule` in
`tests/rag/test_fts_sync.py`; (2) add
`test_no_unsanctioned_direct_chunks_fts_write` to the same file (REQ-001, REQ-002 of
`plans/20260920-203952_plan.md`).
Out of scope: `docs/adr/ADR-009-rag-ft5-text-separation.md` and
`docs/00_governance_03_issue-and-uncertainty-management.md` edits — covered by this
Plan's Rows 2 and 3, separate implementation procedure documents.

## Assumptions
- `RagMaintenanceService.rebuild_fts()` uses `SQLiteHelper("rag").open(write_mode=True)`
  internally (confirmed via Read of `scripts/agent/services/rag_maintenance_service.py`
  lines 31-44), which resolves its DB path via `db.helper.build_db_config()` unless
  `db_path` is passed explicitly to `SQLiteHelper`'s constructor — `RagMaintenanceService`
  does not expose a `db_path` parameter (confirmed via Read of its `__init__`), so the
  test must monkeypatch `db.helper.build_db_config` to point at a `tmp_path`-based
  temporary SQLite file, following the existing, working pattern in
  `tests/db/test_db_maintenance.py::TestRagDbMaintenanceService.test_rebuild_fts`
  (confirmed via Read, lines 292-301) rather than the `:memory:`-connection pattern
  this same file's other tests use (those other tests exercise the trigger only, via a
  raw `sqlite3.connect(":memory:")`, never `RagMaintenanceService` itself).
- `_make_db_cfg`-equivalent test helper does not yet exist in `tests/rag/test_fts_sync.py`
  — it must be added (or imported/reused if a shared conftest helper exists; confirm via
  `rg -n "_make_db_cfg\|build_db_config" tests/rag/conftest.py tests/conftest.py` during
  implementation before duplicating one inline).

## Design decisions
- Build the trigger-populated baseline and the rebuild-populated result against the
  **same temporary SQLite file** (not two separate in-memory connections), so the
  comparison is a genuine "does `rebuild_fts()` reproduce what the trigger already
  wrote" check: (1) create the schema via the real DDL (`scripts/db/schema_sql.py`'s
  trigger definitions, reused verbatim or via the file's existing `_FTS_SCHEMA_SQL`
  constant if its trigger bodies match — confirm via Read before assuming they are
  identical, since `_FTS_SCHEMA_SQL` is a test-local duplicate, not an import of the
  production DDL), (2) insert chunks (populating `chunks_fts` via the trigger), (3)
  snapshot `chunks_fts` rows, (4) call the real `RagMaintenanceService.rebuild_fts()`
  against that same file (via the `build_db_config` monkeypatch), (5) snapshot
  `chunks_fts` rows again, (6) assert the two snapshots are identical.
- For DESIGN-2's static-analysis test, use a simple `rg`-equivalent regex scan
  (`re.search` over each file's text, or `subprocess.run(["rg", ...])` if the
  repository's existing test-tooling precedent favors shelling out — confirm via `rg
  -l "subprocess.run" tests/tools/*.py` for a precedent before choosing) rather than
  AST parsing, consistent with the source Plan's Assumptions section and the
  project's existing `stale_detector.py` design philosophy.
- Allowlist exactly three files for the DESIGN-2 scan: `scripts/db/schema_sql.py` (the
  trigger DDL), `scripts/agent/services/rag_maintenance_service.py` (the production
  `rebuild_fts()`), and `scripts/rag/maintenance.py` (the confirmed dead-code
  duplicate, allow-listed per the source Plan's Design section rather than removed —
  see `issues/20260920-203952_unknowns.md`).

## Alternatives considered
- Using `:memory:` for the REQ-001 test instead of a `tmp_path` file: rejected —
  `RagMaintenanceService.rebuild_fts()` cannot be pointed at an in-memory connection
  without either changing its production code (out of scope) or monkeypatching at a
  lower level than `build_db_config`; the `tmp_path`-file pattern is the existing,
  proven approach for testing this exact class of production code (confirmed working
  in `tests/db/test_db_maintenance.py`).
- Testing `scripts/rag/maintenance.py::RagDbMaintenanceService.rebuild_fts()` instead
  of (or in addition to) the real one for REQ-001: rejected — that class is dead code
  with no production caller (confirmed in the source Plan's Problem section); testing
  it would validate the wrong implementation and give false confidence about INV-07 as
  actually experienced by `/session rag-rebuild-fts`.

## Implementation
### Target file
`tests/rag/test_fts_sync.py`

### Procedure
1. Read `scripts/db/schema_sql.py`'s trigger DDL (lines 56-66, already confirmed) and
   compare it verbatim against this file's own `_FTS_SCHEMA_SQL` constant (lines 11-40,
   confirmed present) — if they differ in any way relevant to `chunks_fts`/trigger
   behavior, note the discrepancy in the Plan Gap channel (do not silently reconcile a
   production-DDL mismatch beyond this row's scope) and proceed using `_FTS_SCHEMA_SQL`
   as-is, since it is the file's existing, already-passing-tests baseline.
2. Rewrite `test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`
   (currently at lines 171-208) to: build a `tmp_path` SQLite file with
   `_FTS_SCHEMA_SQL`'s schema, insert one English chunk (`normalized_content=None`)
   and one Japanese chunk (`normalized_content` set) via plain `INSERT` (exercising the
   trigger), snapshot `SELECT rowid, content FROM chunks_fts ORDER BY rowid`,
   monkeypatch `db.helper.build_db_config` to point at the same `tmp_path` file
   (following `tests/db/test_db_maintenance.py`'s pattern), call
   `RagMaintenanceService().rebuild_fts()`, snapshot `chunks_fts` again from a fresh
   connection to the same file, and assert the two snapshots are equal.
3. Add `test_no_unsanctioned_direct_chunks_fts_write`: scan
   `scripts/rag/`, `scripts/agent/`, and `scripts/db/` (via `Path.rglob("*.py")`) for
   `INSERT INTO chunks_fts`, `DELETE FROM chunks_fts`, `UPDATE chunks_fts`, and the
   FTS5 special-command form `INSERT INTO chunks_fts(chunks_fts)` (regex,
   case-insensitive), and assert every matching file path is one of the three
   allowlisted paths (Design decisions above).
4. Manually verify zero false positives for the new DESIGN-2 test against the current
   tree before finalizing (per the source Plan's Risks mitigation) — run the scan
   standalone (e.g. via a throwaway script or by running the new test itself) and
   confirm its match set is exactly the 3 allowlisted files, no more, no fewer.

### Method
Direct file edit (`Edit` tool) — rewrite one existing test function body, append one
new test function; no change to `_FTS_SCHEMA_SQL` or any other existing test.

### Details
Existing (non-functional) test to replace (confirmed via Read, lines 171-208):
```python
def test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule(self) -> None:
    """INV-009: FTS trigger and manual rebuild use identical text selection rules.
    ...
    """
    conn = sqlite3.connect(":memory:")
    ...
    fts_text1 = None or "test"
    assert fts_text1 == "test"
    ...
    fts_text2 = "日本 語" or "日本語"
    assert fts_text2 == "日本 語"
```

Target replacement (illustrative — write exact final code during implementation,
adapting `_make_db_cfg`'s shape from `tests/db/test_db_maintenance.py` lines 55-74):
```python
def test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """INV-07: FTS trigger and manual rebuild (RagMaintenanceService.rebuild_fts())
    produce identical chunks_fts contents for the same underlying chunk data."""
    from agent.services.rag_maintenance_service import RagMaintenanceService

    db_file = tmp_path / "rag.sqlite"
    conn = sqlite3.connect(str(db_file))
    conn.executescript(_FTS_SCHEMA_SQL)
    conn.execute(
        "INSERT INTO documents(url, lang) VALUES(?, ?)", ("http://a.com", "en")
    )
    doc_id = conn.execute("SELECT doc_id FROM documents").fetchone()[0]
    conn.execute(
        "INSERT INTO chunks(doc_id, content, normalized_content, chunk_index)"
        " VALUES(?,?,?,?)",
        (doc_id, "Hello world", None, 0),
    )
    conn.execute(
        "INSERT INTO documents(url, lang) VALUES(?, ?)", ("http://b.com", "ja")
    )
    doc_id = conn.execute(
        "SELECT doc_id FROM documents WHERE url = ?", ("http://b.com",)
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO chunks(doc_id, content, normalized_content, chunk_index)"
        " VALUES(?,?,?,?)",
        (doc_id, "こんにちは世界", "こんにちは 世界", 1),
    )
    conn.commit()
    before = conn.execute(
        "SELECT rowid, content FROM chunks_fts ORDER BY rowid"
    ).fetchall()
    conn.close()

    monkeypatch.setattr(
        "db.helper.build_db_config",
        lambda: _make_db_cfg(tmp_path, rag_name="rag.sqlite"),
    )
    RagMaintenanceService().rebuild_fts()

    conn2 = sqlite3.connect(str(db_file))
    after = conn2.execute(
        "SELECT rowid, content FROM chunks_fts ORDER BY rowid"
    ).fetchall()
    conn2.close()
    assert before == after


def test_no_unsanctioned_direct_chunks_fts_write(self) -> None:
    """DESIGN-2: only sanctioned files may write to chunks_fts directly."""
    import re
    from pathlib import Path

    allowlist = {
        "scripts/db/schema_sql.py",
        "scripts/agent/services/rag_maintenance_service.py",
        "scripts/rag/maintenance.py",
    }
    write_pattern = re.compile(
        r"(INSERT\s+INTO\s+chunks_fts|DELETE\s+FROM\s+chunks_fts"
        r"|UPDATE\s+chunks_fts)",
        re.IGNORECASE,
    )
    repo_root = Path(__file__).resolve().parents[2]  # confirm actual depth at impl time
    offenders: list[str] = []
    for base in ("scripts/rag", "scripts/agent", "scripts/db"):
        for path in (repo_root / base).rglob("*.py"):
            rel = str(path.relative_to(repo_root))
            if write_pattern.search(path.read_text(encoding="utf-8")):
                if rel not in allowlist:
                    offenders.append(rel)
    assert offenders == []
```
Confirm `Path(__file__).resolve().parents[N]`'s exact `N` at implementation time (must
resolve to the repository root containing `scripts/`) — do not guess the depth without
checking `tests/rag/test_fts_sync.py`'s actual directory nesting.
`_make_db_cfg` must be added to this file (or imported from a shared conftest helper,
if `rg -n "_make_db_cfg" tests/rag/conftest.py tests/conftest.py` finds one — confirm
during implementation before duplicating `tests/db/test_db_maintenance.py`'s version
inline).

## Compatibility considerations
No production code change. The rewritten test changes only its own internal
implementation — its name is unchanged, so any external reference to this test name
(e.g. ADR-009's Verification section, updated by this Plan's Row 2) remains valid.

## Security considerations
N/A: test-only change; the DESIGN-2 scan reads `.py` source files already in the
repository, no external input or network access.

## Rollback considerations
Reverting this row restores the prior (non-functional but passing) test body and
removes the new DESIGN-2 test — no persisted state or migration involved, since all
DB operations occur inside `tmp_path` (auto-cleaned by pytest).

## Validation plan
- `uv run pytest tests/rag/test_fts_sync.py -v` — confirms the rewritten test actually
  exercises `rebuild_fts()` and passes, and the new DESIGN-2 test passes with zero
  offenders (REQ-001, REQ-002, AC-1, AC-2, AC-5 of `plans/20260920-203952_plan.md`).
- `uv run pytest tests/rag/ tests/agent/services/test_rag_index_integrity.py -v` —
  regression check per the source Plan's Tests section.
- `uv run ruff check tests/rag/test_fts_sync.py` / `uv run mypy tests/rag/test_fts_sync.py`.
- Temporarily introduce a synthetic unsanctioned write (e.g. add a throwaway
  `chunks_fts` INSERT to a scratch file under `scripts/rag/`) during implementation to
  confirm the DESIGN-2 test actually fails when it should, then remove the scratch
  file — per the general regression-test-quality practice of confirming a test can
  fail before trusting it as a guard.

## Completion criteria
- The rewritten INV-07 test calls the real `RagMaintenanceService.rebuild_fts()` and
  passes.
- `test_no_unsanctioned_direct_chunks_fts_write` passes with exactly the 3 allowlisted
  files matched (or zero non-allowlisted matches) against the current tree.
- No pre-existing test in `tests/rag/test_fts_sync.py` regresses.

## Out of scope
- `docs/adr/ADR-009-rag-ft5-text-separation.md` edits — this Plan's Row 2.
- `docs/00_governance_03_issue-and-uncertainty-management.md` edits — this Plan's Row 3.
- Deleting `scripts/rag/maintenance.py::RagDbMaintenanceService` — filed separately as
  `issues/20260920-203952_unknowns.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Compare `_FTS_SCHEMA_SQL` against production DDL; rewrite the INV-07 test to call the real `rebuild_fts()` | Completed | 20260920-212200 | 20260920-212200 | _FTS_SCHEMA_SQL trigger bodies confirmed identical to scripts/db/schema_sql.py; rewrote INV-07 test to call real RagMaintenanceService.rebuild_fts() via db.helper.build_db_config monkeypatch |
| 2 | Add `test_no_unsanctioned_direct_chunks_fts_write` and verify it fails on a synthetic offender before finalizing | Completed | 20260920-212200 | 20260920-212200 | Verified DESIGN-2 test fails on a synthetic offender (scripts/rag/_scratch_offender_test.py, removed after verification) before finalizing |
| 3 | Run full validation (`tests/rag/test_fts_sync.py`, regression check, lint/type) | Completed | 20260920-212200 | 20260920-212200 | 6/6 tests pass in test_fts_sync.py; 10 pre-existing failures in tests/rag_http_mode.py etc. confirmed unrelated via git stash comparison |

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
- **Requirement ID**: REQ-001, REQ-002 (real INV-07 regression test; DESIGN-2 static-analysis test)
- **Source issue**: issues/20260920-191952_ci007_validate-fts5-rebuild-rules-from-adr-009-against-implementation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203952_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-210021
- **Related target files**: tests/rag/test_fts_sync.py