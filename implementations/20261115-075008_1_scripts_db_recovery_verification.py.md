## Goal

Make the restore logical-verification stage open candidate databases with the configured sqlite-vec extension so a healthy vec0-bearing rag/session candidate can pass verification and reach `action="restored"`, while keeping every genuine verification gap fail-closed as `verification_unavailable`.

## Scope
**Release unit**: vec-restore-verification (Phase 1 of 2; Phase 2 is the companion test procedure `implementations/20261115-075008_2_tests_db_test_db_recovery.py.md`)

Target file: `scripts/db/recovery_verification.py` (REQ-001).

## Assumptions
- Cross-plan overlap `scripts/db/recovery_verification.py` (shared with `plans/20261115-041859_dbreview004_integrity-probe-side-effects.md`): **compatible (sequencing)** — this procedure threads `sqlite_vec_so` into the Helper call at `recovery_verification.py:141`; Plan 004's REQ-005 later opens the same call `read_only=True` and its Design pins "load_vec behavior is unchanged (extension loading is connection-local and legal on ro connections)". Batch order 001→…→004; 004 re-reads landed code.
- Cross-plan overlap `tests/db/test_db_recovery.py` (Plans 002/003/004): **compatible (sequencing)** — 001's tests (companion document) add new test functions only; 002/003/004 edit their own disjoint test regions.
- Verified this cycle (probe 2026-11-15): a healthy real-vec0 candidate currently fails `_run_logical_verification` with `consistent=False detail='embedding_unverified; url_mismatches=1'` and diagnostics `no such module: vec0`; the same candidate passes when `SQLiteHelper(..., sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so")` is used.
- `build_db_config()` raises `ValueError` on empty/absent `sqlite_vec_so` (`scripts/db/config.py:29`, `66-69`); the isolated test root keeps the real vec0 path (`tests/conftest.py` rewrites writable paths only).
- No committed test currently patches `db.recovery_verification.build_db_config`; existing restore tests that patch `SQLiteHelper` in `db.recovery_verification` feed kwargs into mocks and are unaffected by the new call.

## Design decisions
- Resolution point: `_run_logical_verification` resolves the extension path itself via `build_db_config()` — the Source Issue's Required Fix decision ("Decide at the responsibility level where the path is resolved (`DbConfig` via `build_db_config`) so callers do not each thread it by hand"). No signature change; `_verify_candidate` and `_post_restore_failure` stay untouched.
- Resolution is lazy: `build_db_config()` is called only when the target has a registered logical verifier (rag/session). Unknown/skip targets (workflow) keep their current early returns with no config dependency.
- Fail-closed on config failure: `ValueError` from `build_db_config()` → log error → return `(False, "verification_unavailable")`, the existing vocabulary already mapped by `recovery.py:394-408` and documented in `docs/41_db`.
- Unloadable extension file keeps the existing fail-closed path: `SQLiteHelper._load_vec_extension` raises `sqlite3.OperationalError` (`helper.py:160-167`), caught by the existing `except sqlite3.Error` in `_run_logical_verification` → `verification_unavailable`.

## Alternatives considered
- Threading `cfg.sqlite_vec_so` from the `db.recovery` call sites (the drill pattern): rejected by the Issue's Required Fix — callers must not each thread it; recovery.py already builds config once and would need signature churn across `_verify_candidate`/`_post_restore_failure`.
- `SQLiteHelper` fallback to `build_db_config()` when `db_path` is explicit and `load_vec=True`: rejected — breaks the helper's explicit-path self-containment contract (`helper.py:79-82`) and was left as a maintainer "no" by the Issue's Required Fix wording.

## Implementation
### Target file
`scripts/db/recovery_verification.py`

### Procedure
1. Add the config import: `from db.config import build_db_config` alongside the existing `db.helper` import block.
2. In `_run_logical_verification`, after the `_LOGICAL_VERIFIERS` lookup and its early returns (unknown-mandatory → `verification_unavailable`; non-mandatory skip → `(True, None)`), resolve the config:
   - `try: cfg = build_db_config()` / `except ValueError as e: logger.error("Logical verification could not resolve DbConfig: %s", e); return False, "verification_unavailable"`.
3. Change the helper open from `SQLiteHelper(target, db_path=str(db_path)).open()` to `SQLiteHelper(target, db_path=str(db_path), sqlite_vec_so=cfg.sqlite_vec_so).open()` so `open()` loads the extension (`helper.py:91-92`, `209-211`).
4. Keep the existing `except sqlite3.Error` and `except RuntimeError` handlers exactly as-is; their contracts are unchanged.

### Method
Edit the single function body; no new helpers, no signature or call-site changes. The docstring of `_run_logical_verification` must state the resolution point and the fail-closed config behavior.

### Details
- `SQLiteHelper` explicit-`db_path` branch: non-empty `sqlite_vec_so` sets `_default_load_vec=True`, so `open()` (no `load_vec` argument) loads the extension and disables further extension loading (`helper.py:155-167`).
- The physical stage (`_run_integrity_check`) is proven to pass vec0-bearing DBs without the extension (probe `[1]`); only the logical stage changes.
- Session candidates are fixed by the same edit: `check_session_consistency` requires `memories_vec` by name (`scripts/db/session_consistency_queries.py:69`, `85`).

## Compatibility considerations
- No caller, signature, or result-vocabulary change; `recovery.py` needs no edit (its `verification_unavailable` mapping at `394-408` already exists).
- Existing mock-based tests: tests patching `db.recovery._run_logical_verification` are bypassed entirely; tests using `mock_sqlite_helper`/`mock_recovery_db` pass the new kwarg into mock classes; the real `build_db_config()` call reads the isolated-root config (valid `sqlite_vec_so` on this host). Phase 2's full `tests/db` run confirms no coupling regressions.
- Plan 004 later converts the same `open()` to `read_only=True`; this procedure must not pre-empt that (it will re-read the landed line).

## Security considerations
- Extension path comes only from `DbConfig` (operator-controlled `agent.toml`); no new user input or path is loaded. The helper loads once and immediately calls `enable_load_extension(False)` (existing behavior).

## Rollback considerations
- `git checkout -- scripts/db/recovery_verification.py` restores prior behavior. The reverted state returns to the known-broken fail-closed behavior (`logical_verify_failed` for vec0 candidates) — it never reports false success, so a rollback is operationally safe but must be paired with re-opening Issue 001.

## Validation plan
- Targeted: `uv run pytest tests/db/test_db_recovery.py -v` (companion tests assert AC-1/AC-2).
- Regression: `uv run pytest tests/db -v`, then full suite `-n auto`.
- Static sequence per `rules/toolchain.md`: `uv run radon cc scripts/db/recovery_verification.py -s` (baseline top A(5)); `uv run vulture scripts/db/recovery_verification.py --min-confidence 80` (baseline: none); `uv run bandit -r scripts/ -c pyproject.toml` (baseline 45 low / 0 medium / 0 high).

## Completion criteria
- A healthy rag and a healthy session candidate built with real vec0 tables passes `_run_logical_verification` (AC-1, asserted by the companion tests).
- A config that cannot supply `sqlite_vec_so`, or a DB the stage cannot open, returns `(False, "verification_unavailable")` with an error log — never success.
- Full `tests/db` and the full suite green; static baselines not worsened.

## Out of Scope
- `scripts/db/helper.py` (unchanged), read-only probe mode and `MISSING` classification (Plan 004), sidecar/quarantine semantics (Plan 003), drill harness internals (`recovery_drill.py` already threads `sqlite_vec_so`), documentation changes (vocabulary unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests are owned by companion document 20261115-075008_2 |
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261114-092848_dbreview001_logical-verify-vec-extension.md (archived to issues/done/)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-033931_dbreview001_logical-verify-vec-extension.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-075008
- **Related target files**: scripts/db/recovery_verification.py
