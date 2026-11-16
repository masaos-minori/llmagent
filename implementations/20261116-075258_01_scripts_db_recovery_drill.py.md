## Goal
- In `scripts/db/recovery_drill.py`: catch the archive stage's full exception set per domain and persist a failed artifact before continuing (REQ-001), start the RTO clock before `shutil.copy2` (REQ-002), delete the dead `_last_archive` helper (REQ-003), and route the per-domain status line through `logger` with `main()` configuring logging (REQ-004) — with `tests/db/test_recovery_drill.py` as companion covering AC-1/AC-2/AC-4.

## Scope
**Release unit**: drill-harness-fidelity (Phases 1-3 of the plan; lands with `20261116-075258_03`)

- In scope: `scripts/db/recovery_drill.py` archive-stage `except` (region `:185-192`), `started` placement (`:206`), `_last_archive` deletion (`:248-263`), `print` → `logger.info` (`:300`) + `basicConfig` in `main` (`:305-336`); companion tests in `tests/db/test_recovery_drill.py`.
- Out of scope: drill-artifact/archive retention (Plan 008, later in the batch; it edits 009's landed shape only); `scripts/db/rotation.py` (read-only reference — the drill catches what it raises); docs section 12 update (procedure `20261116-075258_03`).

## Assumptions
- Verification finding (2026-11-16, re-confirmed against source at HEAD `948d7b6d5`): `_drill_one_domain` catches only `FileNotFoundError` at `:187` (branch `:187-192`); `_archive_db_file` also raises `RuntimeError` from `_verify_archive` (`scripts/db/rotation.py:74,80`) and `sqlite3.Error` from connect/backup (`rotation.py:50-53`); an escaping error skips `_persist_artifact` and aborts `run_drill`'s loop (`:290-301`), contradicting the docstring "always return its audit artifact" (`:150-153`).
- Failure-artifact shape reuses the existing `FileNotFoundError` pattern (`verification = {"missing_source": False}` + `error`, `:188-189`): archive-stage failures set `verification = {"archive_failed": False}` and `error=str(exc)`; `integrity` stays `None` (artifact init at `:180`) so `run_drill`'s `ok` computation (`:294-298`) yields FAIL with no further changes. UNK-01 fallback: if the maintainer rejects the additive key before Phase 1, express the failing verdict with existing keys (`integrity: False` + `error`) — same AC-1 outcome.
- `started` is `time.time()` at `:206`, after `shutil.copy2` at `:204`; moving it before the copy shifts `restore_start_ts` (`:220`) and `rto_seconds` (`:222`) together, so the exact-tolerance test at `tests/db/test_recovery_drill.py:282` stays satisfiable and `:278` (`restore_start_ts >= archive_ts_epoch`) still holds (archive precedes the copy).
- Companion eligibility for `tests/db/test_recovery_drill.py`: plan table row 2 under `tests/`, named in exactly one other row's Related Tests (this row, backticked), fully prescribed tests (plan Tests section names patch targets and assertions), same fixture harness as the existing tests (`_domain_dbs`, `_write_cli_config`, `_run_cli`, `_load_artifacts`) — no design decision of its own (SKILL.md companion conditions 1-4).
- Dependency gate satisfied: plan 004 (`plans/done/20261115-041859_dbreview004_integrity-probe-side-effects.md`) landed (commit `693f71679`) and owns `scripts/db/recovery.py` + the restore/probe sections of `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`; this document edits no file 004 owns (sequencing only).

## Design decisions
- Catch at the domain boundary, not inside rotation: the `except` set is exactly what `_archive_db_file` documents — `(FileNotFoundError, RuntimeError, sqlite3.Error)` (plan Design; `rotation.py:39`, `:74,80`, `:50-53`). The existing `FileNotFoundError` branch (`:187-192`) stays byte-identical; a new `except (RuntimeError, sqlite3.Error) as exc:` branch follows it.
- Clock placement: `started = time.time()` moves to directly before `shutil.copy2` (`:204→before`); the `rto_seconds` formula (`:222`) is unchanged, only its meaning widens to the true restore (copy + verification). `backup_duration_seconds` (`:198`, archive creation) is unaffected (maintainer decision 2026-11-15: include the copy; field names unchanged).
- Logging instead of print: `logger.info("[drill] %s: %s %s", target, status, artifact["verification"])` preserves the message text verbatim; `main()` gains `logging.basicConfig(level=logging.INFO)` per `scripts/db/create_schema.py:127` (pattern re-confirmed this cycle).

## Alternatives considered
- Catching `Exception` at the archive stage: rejected — absorbs programming errors the docstring doesn't promise (plan Design).
- Making `_verify_archive` non-raising: rejected — rotation's contract "a failing archive raises" is documented at `rotation.py:35`.
- Wiring `_last_archive` into Plan 008 instead of deleting it: rejected — 008's scope is rotation archive retention and drill-artifact retention windows, not selecting "latest archive" (plan Design; 008's plan does not reference this helper).
- Moving the loop report into `main()`: rejected — would duplicate the domain loop and the `ok` computation, which must stay with `run_drill` (its tests call it directly) (plan Design).

## Implementation
### Target file
`scripts/db/recovery_drill.py`

### Procedure
1. After the existing `except FileNotFoundError` branch (`:187-192`), add `except (RuntimeError, sqlite3.Error) as exc:` with the same body shape: `artifact["verification"] = {"archive_failed": False}`; `artifact["error"] = str(exc)`; `logger.error("drill %s: %s", domain, exc)`; `_persist_artifact(drill_dir, artifact)`; `return artifact` (REQ-001; AC-1).
2. Move `started = time.time()` (`:206`) to directly before `shutil.copy2(recovery_point, isolated)` (`:204`); keep `restore_start_ts`/`rto_seconds`/`restore_end_ts` assignments at `:220-222` unchanged (REQ-002; AC-2).
3. Delete `_last_archive` (`:248-263`) entirely (REQ-003; AC-3). No import becomes unused — `Path`/glob use persists via other call sites (plan Design; ruff confirms).
4. Replace `print(f"[drill] {target}: {status} {artifact['verification']}")` (`:300`) with `logger.info("[drill] %s: %s %s", target, status, artifact["verification"])`; add `logging.basicConfig(level=logging.INFO)` at the top of `main()` (`:305`) per the `create_schema.py:127` pattern (REQ-004; AC-4).

### Companion test files
- `tests/db/test_recovery_drill.py`
  - Procedure: add (a) archive-failure continuation tests — `patch("db.recovery_drill._archive_db_file", side_effect=RuntimeError("archive verification failed for x: integrity check ..."))` on one domain while the others drill normally → failing domain's artifact exists with `error` set and non-passing `verification`, remaining domains' artifacts exist, `run_drill("all", ...)` returns False; repeat with `sqlite3.Error("disk I/O error")` (AC-1); (b) timing-order test — wrap `shutil.copy2` with a recorder capturing `time.time()` after the copy returns; assert `artifact["restore_start_ts"] <= recorded_copy_end` and `artifact["rto_seconds"] >= 0` (deterministic, no sleeps) (AC-2); (c) status-line test — `caplog.at_level(logging.INFO, logger="db.recovery_drill")` around `run_drill` asserts one INFO line per drilled domain containing the domain name and PASS/FAIL (AC-4). Keep every pre-existing artifact-key and verdict assertion unchanged (AC-5). Regression watch (no assertion changes expected): `test_all_domains_drill_passes_and_live_dbs_untouched` (`:235-248`), the rag/session/workflow verdict tests (`:291-557`), the CLI exit tests (`:593-637` — confirmed 2026-11-16: no capsys/stdout assertions in the file).
  - Validation: `uv run pytest tests/db/test_recovery_drill.py -v` → AC-1/AC-2/AC-4 asserted; then `uv run pytest tests/db -q` for the full-file regression.

### Method
- Direct edits inside the existing module; imports unchanged (plan Design). radon baseline: `run_drill` C(11), `_verify_rag_session` B(6), `_drill_one_domain` A(5) — the new except branch adds ≤1 branch to `_drill_one_domain` (stays A/B); no restructuring of `run_drill` (logging swap is 1:1).

### Details
- The plan's superseded-issue note stands: the current harness has no dataclass result type, no quarantine step, and no success-path redundant copy; only the four claims above are implemented.
- Failure-path artifact gains one key (`verification["archive_failed"]`) only; success-path schema keys are untouched (AC-5, plan Persisted schema check).
- Sequence context: Plan 008 (`plans/20261115-054021_dbreview008_artifact-retention-gaps.md`) lands after 009 and extends this file's landed shape (end-of-drill `isolated` unlink, `_persist_artifact` naming); this document changes no region 008 will not re-read.

## Compatibility considerations
- CLI cron output preserved: message text verbatim; logging writes to stderr and cron captures it; the CLI subprocess tests (`:593-637`) assert returncode and artifacts only and re-run unchanged (plan Risks).
- Historical drill artifacts under `/opt/llm/data/archives/drills` (if any) keep verification-only `rto_seconds` values; post-change artifacts are copy+verification — recorded as the plan's open follow-up WI-009-1 (no dashboard consumes them today).
- `logging.basicConfig` in `main` does not double-log for cron because the module runs as `__main__` only there (`:337-338`, plan Assumptions).

## Security considerations
- Broadening the `except` is bounded to the documented exception set (not `Exception`); the error text is persisted and logged, and `run_drill` still returns False (exit 1) so cron alerts fire on broader outages (plan Risks). bandit baseline 45 low / 0 medium / 0 high unchanged (no new file handling).

## Rollback considerations
- `git checkout` revert of the unit commit; part of release unit drill-harness-fidelity — revert together with `20261116-075258_03` (its companion tests are part of this document).

## Validation plan
- `uv run pytest tests/db/test_recovery_drill.py -v` → companion tests assert AC-1/AC-2/AC-4.
- `uv run pytest tests/db -q` → all pre-existing tests green unchanged.
- `uv run pytest tests/ -n auto` → no regressions.
- `uv run vulture scripts/db/recovery_drill.py` → no findings (baseline: 1 `_last_archive` at 60%, re-confirmed 2026-11-16).
- `grep -n "print(" scripts/db/recovery_drill.py` → no matches (AC-4).
- `uv run ruff check scripts/db/recovery_drill.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` (CI form), `uv run lint-imports` → contracts kept; `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria
- With `_archive_db_file` patched to raise `RuntimeError` (and separately `sqlite3.Error`) for one domain: that domain's artifact exists with `error` populated and a non-passing `verification`, the other domains are still drilled and persisted, `run_drill` returns False (AC-1).
- `restore_start_ts` ≤ recorded copy-completion timestamp and `rto_seconds` covers the copy (AC-2); `_last_archive` absent and vulture clean (AC-3); no `print(` remains and the status line appears via caplog and via CLI logging output (AC-4); all pre-existing artifact-key and verdict assertions unchanged (AC-5).

## Out of Scope
- Drill-output/archive retention and the end-of-drill `isolated` unlink (Plan 008).
- `scripts/db/rotation.py` behavior (unchanged; reference only).
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 12 wording (procedure `20261116-075258_03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Drill failure handling, clock, dead code, logging (plan Phase 1) | Pending | — | — | REQ-001..REQ-004; gated: plans/done/20261115-041859_dbreview004_integrity-probe-side-effects.md phase all - sequencing only, 004 landed at commit `693f71679` |
| 2 | Companion tests in `tests/db/test_recovery_drill.py` (plan Phase 2) | Pending | — | — | REQ-005; run `uv run pytest tests/db/test_recovery_drill.py -v`, then the regression watch list |
| 3 | Run the validation sequence (`rules/toolchain.md`) (plan Phase 3) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004 (drill changes), REQ-005 (companion tests)
- **Source issue**: issues/20261114-092858_dbreview009_drill-harness-fidelity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-051359_dbreview009_drill-harness-fidelity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-075258
- **Related target files**: `scripts/db/recovery_drill.py`, `tests/db/test_recovery_drill.py`
