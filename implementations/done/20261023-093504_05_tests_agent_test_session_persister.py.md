## Goal

Add the new mirror test file `tests/agent/test_session_persister.py` that asserts
the write-or-skip gate and failure containment this Plan installs (REQ-003,
REQ-004, REQ-005, REQ-006, REQ-011, AC-3, AC-4). The gate is verified against a
**real temporary `session_diagnostics` table** with row-count assertions (not mock
counts), per REQ-011.

## Scope

New test-only file `tests/agent/test_session_persister.py`. Reference reads:
`scripts/agent/session_persister.py` (rows 3, the gate and widened guard),
`scripts/agent/diagnostic_store.py` (`save`/`fetch`), `scripts/db/schema_sql.py`
(`session_diagnostics` DDL, `:138-146`), `scripts/agent/memory/ingestion.py`
(`on_session_stop` no-op, `:87-89`). Dependent file: `tests/agent/test_repl.py`
(row 4).

## Assumptions

- `SQLiteHelper("session")` resolves its path from `build_db_config().session_db_path`
  (`scripts/db/helper.py:100-108`); patching `db.helper.build_db_config` redirects
  it. This is the same seam `tests/agent/test_repl.py:758`, `:835` use.
- `DiagnosticStore.save(session_id=None, …)` inserts a row (the `session_id` column
  is a nullable FK, `schema_sql.py:140`); the store contract stays as recorded
  (REQ-006).
- `persist_session_diagnostics` reads `ctx.stats.*`, `ctx.services.llm`,
  `ctx.services.hist_mgr`, `ctx.session.session_id`; the `StateStore`/`fetch`
  enrichment is wrapped in `try/except (RuntimeError, sqlite3.Error)` and degrades
  to zero counts when unavailable.
- `persist_session_memories` reads `ctx.services.memory`, `ctx.conv.history`,
  `ctx.turn.current_turn_id`.

## Design decisions

- **Real temp DB, row-count evidence.** A module helper seeds a temporary
  `session_diagnostics` table under `tmp_path` and returns a live
  `DiagnosticStore`, all inside a `build_db_config` patch. Assertions count rows in
  that table rather than mock calls (REQ-011, AC-3).
- **Gate, both methods.** One test class covers
  `persist_session_diagnostics` (row count + store contrast), another covers
  `persist_session_memories` (no `on_session_stop` when session-less).
- **Containment, whole step.** A payload-defect (`json.dumps` raising `TypeError`
  from a non-serializable stat value — the shape the probe produced) exercises the
  widened outer guard (REQ-005); a `save` raising `RuntimeError` exercises the
  inner channel (REQ-004). Each produces one non-fatal line and neither escapes.
- **Store contrast.** After the gated case, calling `save(None, …)` directly still
  writes a row, proving the gate sits above the store, not inside it (REQ-006).

## Alternatives considered

- Asserting `mock_save.assert_not_called()` — rejected: REQ-011 forbids an
  assertion that cannot fail; a real table with a row count cannot be satisfied by
  accident.
- Testing only `persist_session_diagnostics` — insufficient: REQ-003 gates *both*
  methods, so `persist_session_memories` is covered too.

## Implementation

### Target file

`tests/agent/test_session_persister.py` (new).

### Procedure

1. **Create the file** with the sections below. Structure:
   - imports: `sqlite3`, `pytest`, `unittest.mock` (`AsyncMock`, `MagicMock`,
     `patch`); `from pathlib import Path`; `from db.config import DbConfig`;
     `from db.helper import SQLiteHelper`; `from agent.diagnostic_store import
     DiagnosticStore`; `from agent.session_persister import SessionPersister`.
   - a `_seed_session_diagnostics(tmp_path)` helper that patches
     `db.helper.build_db_config` to a `DbConfig` whose `session_db_path` points at
     `tmp_path / "session.db"`, creates the `session_diagnostics` table there (DDL
     copied from `schema_sql.py:138-146`; verify how `SQLiteHelper.open()` exposes
     `execute`/context management against HEAD), and returns a live
     `DiagnosticStore()`.
   - a `_diag_ctx(session_id)` helper returning a `MagicMock` `ctx` with
     `stats` (`stat_latency={}`, `stat_turns=3`, `stat_tool_calls=1`,
     `stat_tool_errors=0`, `stat_partial_completions=0`, `stat_input_tokens=10`,
     `stat_output_tokens=5`, plus the `llm`/`hist_mgr` attributes the payload
     builder reads via `getattr`), `services` (`None` is acceptable — the
     `getattr(..., 0)` defaults cover it), `conv`, `turn`, and
     `session.session_id = session_id`.
   - the test classes below.

2. **`TestPersistSessionDiagnosticsGate`** (REQ-003, REQ-006, AC-3):
   - `test_skips_write_when_no_session`: seed the table, build a
     `SessionPersister(diag_ctx(None), store, view)`, call
     `persist_session_diagnostics()`, then assert (a) the table has **0** rows,
     (b) a mocked `ctx.services.memory.on_session_stop` was **not** called, and
     (c) a log record stating the skip reason was emitted (`caplog`, matching
     "no started session").
   - `test_writes_row_when_session_exists`: same fixture with
     `diag_ctx(1)`; assert the table has exactly **1** row of
     `kind="session_summary"` (proves the gate is a session test, not a blanket
     disable, REQ-010).
   - `test_store_accepts_null_session_id_directly`: after the gated case, call
     `store.save(None, kind="session_summary", content="{}")` directly and assert
     the table now has a row (REQ-006).

3. **`TestPersistSessionDiagnosticsContainment`** (REQ-004, REQ-005, AC-4):
   - `test_payload_defect_is_reported_and_does_not_escape`: build
     `diag_ctx(1)` with `stats.stat_turns = MagicMock()` (non-serializable →
     `json.dumps(summary)` raises `TypeError` inside the payload body), call the
     method against the real store, and assert `view.write_warning` was called
     once and the method returned normally (no exception escaped).
   - `test_store_failure_is_reported_and_does_not_escape`: patch
     `store.save` with `side_effect=RuntimeError("store down")`, call the method,
     and assert `view.write_warning` was called once and no exception escaped.

4. **`TestPersistSessionMemoriesGate`** (REQ-003):
   - `test_skips_ingestion_when_no_session`: build a memories ctx with
     `session_id=None` and a mocked `ctx.services.memory.on_session_stop`, call
     `persist_session_memories()`, and assert
     `on_session_stop.assert_not_called()`.
   - `test_writes_when_session_exists`: same with `session_id=1` and a real
     (empty) `ctx.conv.history`; assert `on_session_stop` was awaited.

5. **Verify the fixture against HEAD.** Confirm the exact `ctx` attributes each
   method reads (the `getattr` defaults in the payload builder hide some
   requirements), that `SQLiteHelper.open()` provides the execute/context API used
   to seed the table, and that `on_session_stop` on an empty history does not
   raise. Adjust the helpers accordingly.

### Method

Read-only reference reads of `scripts/agent/memory/ingestion.py` (`on_session_stop`
no-ops on empty history, `:87-89`) confirm the started-session memories case can
start with an empty `conv.history`; `scripts/agent/session.py:148` confirms
`session_id` is the sole existence key the gate reads.

### Details

- `view` is a `MagicMock` throughout (consistent with `test_repl.py`);
  `write_warning` is asserted by call count. The skip-reason log line is captured
  with pytest's `caplog` (the persister logs via `logging.getLogger(__name__)`).
- The payload-defect case relies on the widened outer guard (row 3). Before row 3
  is applied, `TypeError` escapes and this test fails — implement row 3 first.
- `StateStore()` is constructed inside the payload builder for the started-session
  case; if it cannot open its own DB it is swallowed by the builder's
  `try/except (RuntimeError, sqlite3.Error)`, leaving counts at zero, so the row
  still writes. No extra seeding is required for that path.

## Compatibility considerations

### Corrections found while implementing

- The real `build_db_config` seam was replaced by an in-memory fake `SQLiteHelper` patched at `agent.diagnostic_store.SQLiteHelper` (the pattern of `test_regression_diagnostic_persist.py`); `StateStore` is patched to raise so no real DB is opened. Row counts are asserted on the in-memory table.


- New file; does not touch existing tests. Must pass alongside
  `tests/agent/test_repl.py` (row 4), `test_repl_error_handling.py`,
  `test_regression_diagnostic_persist.py`, `test_import_smoke.py` (AC-7).
- Uses `tmp_path` and the `build_db_config` patch precedent; no process is
  started, so no `@pytest.mark.integration` marker is needed.

## Security considerations

- N/A: test-only; the temp DB lives under `tmp_path` and never touches
  `/opt/llm/db/session.sqlite`.

## Rollback considerations

- New file; delete it to remove. Reversible; touches no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_session_persister.py -q` (AC-3, AC-4).
- `uv run pytest tests/agent/test_repl.py tests/agent/test_session_persister.py
  tests/agent/test_repl_error_handling.py tests/agent/test_regression_diagnostic_persist.py
  tests/agent/test_import_smoke.py -q` (AC-7).
- `uv run ruff check tests/agent/test_session_persister.py`,
  `uv run pytest tests/agent -q --durations=10` (leaked-handle / slow-check).

## Completion criteria

The gate asserts zero rows and no `on_session_stop` for a session-less context and
a written row for a started one, against a real temp table; a payload defect and a
store failure each produce one non-fatal line without escaping; direct
`save(None, …)` still writes a row; both persist methods are covered; AC-3/AC-4/
AC-7 hold.

## Out of Scope

- The production gate and containment — row 3. The `TestRunResourceCleanup` order
  assertions and fixture deletion — row 4. Docs — rows 6/7.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create file with temp-DB seed helper + ctx builders | Completed | 20261023-150350 | 20261023-150350 | REQ-003 implemented; full suite 9879 passed |
| 2 | Gate suite for `persist_session_diagnostics` (skip/write/store-contrast) | Completed | 20261023-150350 | 20261023-150350 | REQ-003, REQ-006, AC-3 |
| 3 | Containment cases (payload defect, store failure) | Completed | 20261023-150350 | 20261023-150350 | REQ-004, REQ-005, AC-4 |
| 4 | Gate suite for `persist_session_memories` | Completed | 20261023-150350 | 20261023-150350 | REQ-003 |
| 5 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-150350 | 20261023-150350 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Exact `ctx` attributes and `SQLiteHelper.open()` seeding API must be verified against HEAD before writing assertions. | No | — |
| 3 | Payload-defect case passes only after row 3 widens the outer guard. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | 1 | Verification | Open | implementer | Phase 2 |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004, REQ-005, REQ-006, REQ-011
- **Source issue**: `issues/20261021-093421_shutdown002-session-persistence-skipped-on-startup-failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-071052_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-093504
- **Related target files**: `tests/agent/test_session_persister.py`