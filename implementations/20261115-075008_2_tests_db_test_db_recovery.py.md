## Goal

Lock the vec0 restore-verification fix with regression tests: a fail-closed config unit test for the new `build_db_config()` resolution in `_run_logical_verification`, and per-domain (rag, session) end-to-end restore tests that run `_restore_from_backup` against a real vec0-bearing candidate with `_run_logical_verification` unpatched and assert `action == "restored"`.

## Scope
**Release unit**: vec-restore-verification (Phase 2 of 2; Phase 1 is the production procedure `implementations/20261115-075008_1_scripts_db_recovery_verification.py.md` — this document's tests assert its behavior and must be landed after it)

Target file: `tests/db/test_db_recovery.py` (REQ-002; plus the REQ-001 fail-closed unit test listed in the Plan's Tests section).

## Assumptions
- Cross-plan overlap `tests/db/test_db_recovery.py` (shared with Plans 002/003/004): **compatible (sequencing)** — this procedure only adds new test functions (vec e2e + fail-closed config); Plan 002 edits the rollback-failure tests (~996-1021), Plan 003 the quarantine-flip tests, Plan 004 the probe-invariance/MISSING tests. Disjoint functions; batch order 001 first.
- Cross-plan overlap `scripts/db/recovery_verification.py` (Plan 004): **compatible (sequencing)** — 004 later opens the same verification call `read_only=True` with "load_vec behavior unchanged"; these tests will be re-run after 004 lands (004's own procedure covers that re-run).
- The tests are expected to FAIL against the current tree (before Phase 1 lands) — that is the plan's regression-lock intent: they are written against the fixed behavior (Plan batch order 001 Phase 1 → Phase 2).
- Extension availability: resolve the path from the isolated config (`build_db_config().sqlite_vec_so`; `tests/conftest.py` keeps read-only resources at real paths). Skip with an explicit reason when the file is absent (Source Issue Testing Expectations; supersedes the earlier "fail loudly" sentence — see Plan Assumptions).
- Verified this cycle: the host extension `/opt/llm/sqlite-vec/vec0.so` loads and `SQLiteHelper(db_path=..., sqlite_vec_so=...)` opens vec0 virtual tables (probe 2026-11-15). No committed test under `tests/db` loads a real extension today.

## Design decisions
- Test-real, not mock-real: candidates are built through `SQLiteHelper(..., db_path=..., sqlite_vec_so=...)` (the same load path the fixed production stage uses) with the canonical DDL from `db.schema_sql`; `_run_logical_verification` and `_run_integrity_check` for backup/candidate/post-activation run for real except the single corrupt-live-DB transition.
- Single integrity patch only: `patch("db.recovery._run_integrity_check")` side_effect `[HEALTHY(backup), HEALTHY(candidate), HEALTHY(post)]` (the existing WAL-test pattern at `tests/db/test_db_recovery.py:1044-1052`); `_run_logical_verification` is never patched in these tests.
- Skip-with-reason for a missing extension instead of a silent pass or a hard failure (Issue Testing Expectations).

## Alternatives considered
- Plain-table stand-ins for `chunks_vec`/`memories_vec` (the `test_rag_consistency.py` pattern): rejected — they cannot reproduce `no such module: vec0`, which is the exact failure mode under test.
- Calling `recover_corruption` end to end: rejected — adds the corrupt-classification stage that the existing suite already covers with mocks; `_restore_from_backup` is the function whose staging→verify→activate flow the Issue's scenario needs.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Module-level availability guard: resolve `VEC_SO = Path(build_db_config().sqlite_vec_so)` once (import `db.config.build_db_config`); define `vec0_available = VEC_SO.is_file()` and mark the new real-extension tests with `pytest.mark.skipif(not vec0_available, reason=f"sqlite-vec extension not available at {VEC_SO}")`. Import `db.schema_sql.build_rag_schema_sql` / `build_session_schema_sql` and `db.store_protocols.get_embedding_dims` / `get_embedding_bytes`.
2. Add candidate-builder helpers (module-private, near the WAL test):
   - `_make_vec_rag_db` (new): `with SQLiteHelper("rag", db_path=str(path), sqlite_vec_so=str(VEC_SO)).open(write_mode=True) as db:` → `executescript(build_rag_schema_sql(get_embedding_dims()))` → insert one `documents` row, one `chunks` row (`chunk_index=0`, non-empty content; the `chunks_ai` trigger fills `chunks_fts`), one `chunks_vec` row with a `get_embedding_bytes()`-length float32 BLOB.
   - `_make_vec_session_db` (new): same pattern for `session`: `build_session_schema_sql(get_embedding_dims())`, one `sessions` row, one `messages` row, one `memories` row, one `memories_vec` row with a valid float32 BLOB.
3. Add `test_restore_rag_vec0_candidate_reaches_restored(tmp_path)`: corrupt live `db_dir/rag.sqlite`; backup built by `_make_vec_rag_db` (new); `_restore_from_backup(db_path, str(backup), target="rag")` under `patch("db.recovery._run_integrity_check")` with the 3×HEALTHY side_effect and no logical patch; assert `result.success is True`, `result.action == "restored"`, `result.logical_ok is True`, `result.active_db_state == "restored"`, and `db_path.read_bytes() == backup.read_bytes()` (AC-2).
4. Add the same for session: `test_restore_session_vec0_candidate_reaches_restored(tmp_path)` with `target="session"` and `_make_vec_session_db` (new) (asserts the `memories_vec`-requiring stage passes).
5. Add `test_logical_verification_config_failure_is_verification_unavailable(tmp_path)`: `patch("db.recovery_verification.build_db_config", side_effect=ValueError("sqlite_vec_so is empty"))` → `_run_logical_verification(<any existing file>, "rag")` returns `(False, "verification_unavailable")` (REQ-001 fail-closed config path; no real extension needed, no skip mark).
6. Keep all existing tests byte-identical (Plan 002/003/004 edit other regions).

### Method
Add-only test edit appended after `test_wal_shm_sidecars_land_at_final_locations_after_activation`; reuse its fixture style (`tempfile.TemporaryDirectory`/`tmp_path`, real files under the tmp dir only).

### Details
- The vec inserts must satisfy the consistency layer so the report is fully clean: equal `chunks`/`chunks_fts`/`chunks_vec` counts (1 each), zero orphans, `length(embedding) == get_embedding_bytes()`, `_check_schema_recognition` satisfied by the canonical DDL, read smoke test passing with ≥1 row per table.
- Session fingerprint gate: `check_session_consistency` fingerprints against the canonical session DDL; building with `build_session_schema_sql` guarantees a match (no `RuntimeError` path).
- Clean helper close removes WAL sidecars, so backups may have no `-wal`/`-shm`; staging handles either shape (existing staging tests pin this).
- conftest production-path guard: all DBs live under `tmp_path`; loading the extension from `/opt/llm/sqlite-vec/vec0.so` is a file read, not a DB open under `/opt/llm` — no `production_paths_allowed` marker needed.

## Compatibility considerations
- Tests import only public `db.*` modules already on `sys.path` via conftest.
- The new real `build_db_config()` call inside `db.recovery_verification` (Phase 1) must be importable at test-module import time for the guard; conftest sets the isolation env at import time, so ordering is safe.
- `mock_db_cfg`/`mock_sqlite_helper` fixtures are not used by the new tests (they must run unpatched); they remain untouched.

## Security considerations
- Tests write only under pytest `tmp_path`; the production DB fingerprint guard in conftest stays active as an extra check.

## Rollback considerations
- Test-only file: revert by checkout. If Phase 1 is reverted without reverting these tests, the two e2e tests fail loudly (`action == "logical_verify_failed"`) — the intended regression alarm.

## Validation plan
- Targeted: `uv run pytest tests/db/test_db_recovery.py -v` → new tests pass (AC-2), all existing tests unchanged and green.
- Regression: `uv run pytest tests/db -v`, then full suite `uv run pytest -n auto` (AC-3).
- Static: `uv run radon cc tests/db/test_db_recovery.py -s` (baseline top B(12); keep added functions small), `uv run bandit -r tests/db/test_db_recovery.py` (test file; no new HIGH), per `rules/toolchain.md`.

## Completion criteria
- Both e2e tests assert `action == "restored"`, `logical_ok is True`, `active_db_state == "restored"` with `_run_logical_verification` unpatched (AC-2).
- The fail-closed config test returns `(False, "verification_unavailable")` (AC-1 unit side).
- `tests/db` and the full suite green; on hosts without the extension the vec tests report an explicit skip reason naming the missing path.

## Out of Scope
- Production code changes (companion document 20261115-075008_1), `test_recovery_drill.py` and drill harness changes, Plan 002/003/004 test regions, documentation changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Land after procedure 20261115-075008_1 |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document is the test work itself |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Documentation Impact: None per Plan |

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
- **Requirement ID**: REQ-002 (and the REQ-001 fail-closed unit test per the Plan's Tests section)
- **Source issue**: issues/20261114-092848_dbreview001_logical-verify-vec-extension.md (archived to issues/done/)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-033931_dbreview001_logical-verify-vec-extension.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-075008
- **Related target files**: tests/db/test_db_recovery.py
