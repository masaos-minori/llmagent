# Plan: Restore verification opens the candidate with the target's extension configuration

## Goal
- Close the vec0 gap for real: Step 3a re-verification (2026-11-15) disproved the earlier claim that the production fix was merged upstream. The production threading must be implemented in `scripts/db/recovery_verification.py`, and the Issue's acceptance scenario then locked by a regression test.

## Priority
High (Issue Priority; full scope restored)

## Scope
- **In-Scope**: resolve `sqlite_vec_so` from `build_db_config()` inside the logical-verification stage and pass it to `SQLiteHelper` (`scripts/db/recovery_verification.py`); one e2e regression test per mandatory domain (rag, session) in `tests/db/test_db_recovery.py` restoring a real staged candidate that requires vec0, with the real logical verification.
- **Out-of-Scope**: quarantine semantics (`issues/20261114-092850_dbreview003_restore-sidecar-handling.md`); drill harness internals (already threads `sqlite_vec_so` at `scripts/db/recovery_drill.py:107`, `121`, `209`).
- **Dependencies**: none.

## Plan-Document Correction

- A `git pull` fast-forward at 2026-11-15 02:59 +0900 (reflog `HEAD@{0}` → `edc79f698`) brought commit `4543c2aa4 feat(db): stage full sidecar filenames and verify candidates before activation` into the tree while this batch was in progress. That commit implements parts of the Issue: staging/verification-before-activation and the `verification_unavailable` mapping. The earlier correction of this plan then retired the "thread config/candidate path through logical verification" requirement as merged. **That retirement was wrong** — see the re-correction below.
- **Re-correction (2026-11-15, this workflow's Step 3a adversarial verification)**: the Background claim "the production fix was already merged upstream" is disconfirmed against the current tree:
  - `scripts/db/recovery_verification.py:141` opens `SQLiteHelper(target, db_path=str(db_path))` with no `sqlite_vec_so`; the explicit-`db_path` branch sets `_default_load_vec = bool("")` → the extension is never loaded (`scripts/db/helper.py:88-95`, `209-211`).
  - `git log -S "sqlite_vec_so" -- scripts/db/recovery.py scripts/db/recovery_verification.py scripts/db/recovery_restore.py` returns no commits: the threading was never in any recovery module.
  - Probe evidence (2026-11-15, script run against a freshly built healthy rag candidate with real `vec0` rows): `_run_logical_verification(candidate, "rag")` → `consistent=False detail='embedding_unverified; url_mismatches=1'`; diagnostics `('Basic counts collection failed: no such module: vec0', ...)`; the same candidate opens cleanly and reports `chunks=1 fts=1 vec=1` with no diagnostics when `SQLiteHelper(..., sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so")` is used. Physical integrity check passes without the extension, so `_restore_from_backup` reaches the logical stage and reports `action="logical_verify_failed"` (`scripts/db/recovery.py:394-408`).
  - The drill harness documents this exact failure and threads the path (`scripts/db/recovery_drill.py:92-95`); only the drill side was fixed. `recovery.py:259` (`_post_restore_failure`) shares the same broken stage.
  - Session side: `scripts/db/session_consistency_queries.py` requires `memories_vec` by name, so healthy session restores fail the same way.
- Consequence: the "Thread config/candidate path through logical verification" row is **un-retired** and becomes `REQ-001` below; the test-only requirement becomes `REQ-002`. Requirement IDs are reassigned accordingly.

## Background
From the Source Issue (F-001) and this cycle's re-verification: every restore-flow test patches `db.recovery._run_logical_verification` (e.g. `tests/db/test_db_recovery.py:837-895`, `1024-1061`); no test exercises a candidate whose consistency checks need the `vec0` shadow table end to end. Additionally, no committed test under `tests/db` loads a real sqlite-vec extension at all (`test_rag_consistency.py` and `test_recovery_drill.py` replace vec0 virtual tables with plain-table stand-ins; `test_create_schema.py` skips vec0 tables), so the extension-dependent path is entirely unexercised.

## Problem
The failure mode the Issue describes is still live in the current tree: a healthy rag/session backup with real vec0 tables can never pass candidate logical verification, so automatic recovery of rag and session can never reach `restored` (probe evidence above). It has no regression test on either side (production fix missing; scenario untested).

## Reason for Change
A data-integrity bug reported by an adversarial review must be fixed and locked by the test the Issue asked for; otherwise the same regression keeps silently reappearing — it already reappeared once as an un-retired-but-assumed-fixed requirement.

## Implementation Intent
Fix the logical-verification stage to open the database with the configured sqlite-vec library path, resolved in the verification stage itself via `build_db_config()` (the Issue's Required Fix decision: callers do not each thread it by hand), keeping the fail-closed behavior for a database that genuinely cannot be opened. Then add e2e restore tests per mandatory domain that build a real vec0-populated candidate (created through the Helper with the extension loaded) and run `_restore_from_backup` without patching `_run_logical_verification`, asserting `action == "restored"`.

## Requirements
- `REQ-001`: `_run_logical_verification` opens mandatory-target candidates with `sqlite_vec_so` resolved from `build_db_config()`; a healthy vec0-bearing candidate passes for rag and session; a config that cannot supply the path (or any DB this stage cannot open) still fails closed as `verification_unavailable`.
- `REQ-002`: Regression tests exercise a vec0-requiring staged candidate restore end to end for rag and session and assert success (`action == "restored"`, `logical_ok is True`, `active_db_state="restored"`), with `_run_logical_verification` unpatched.

## Implementation Target Files
**Freeze status**: Frozen (rows re-validated in this cycle after the Step 3a disconfirmation: each row exists, requires modification, probe/evidence recorded, links to a Requirement).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/recovery_verification.py | Modify | `_run_logical_verification` opens `SQLiteHelper(target, db_path=...)` without `sqlite_vec_so`, so vec0 candidates are unverifiable (`no such module: vec0`); resolve the path from `build_db_config()` and pass it to the Helper, fail-closed on config failure | REQ-001 / AC-1 | Probe 2026-11-15: healthy real vec0 candidate → `consistent=False detail='embedding_unverified; url_mismatches=1'`; `git log -S "sqlite_vec_so"` over the recovery modules is empty; `helper.py:88-95` explicit-db_path branch never loads the extension | tests/db/test_db_recovery.py | Verified (gap verified; fix pending) |
| tests/db/test_db_recovery.py | Modify | No committed test exercises a real vec0 candidate through the recovery path; every `action == "restored"` test patches `_run_logical_verification` | REQ-002 / AC-2 | grep over `tests/db/test_db_recovery.py`: `patch("db.recovery._run_logical_verification")` in every `action == "restored"` test (lines 82, 824, 884, 1056, 1457 contexts); `git log -S sqlite_vec_so` over `tests/db/test_db_recovery.py` is empty | tests/db/test_db_recovery.py | Pending |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/recovery.py | `_verify_candidate` / `_post_restore_failure` call sites and the `verification_unavailable` action mapping (`recovery.py:259`, `280`, `394-408`) — unchanged by this fix but define the contract | scripts/db/recovery_verification.py / REQ-001 |
| scripts/db/helper.py | Explicit-`db_path` branch: `sqlite_vec_so` must be passed for the extension to load; `open(load_vec=...)` defaults | scripts/db/recovery_verification.py / REQ-001; tests/db/test_db_recovery.py / REQ-002 |
| scripts/db/recovery_drill.py | `_verify_rag_session` (`:89-125`) documents the identical failure and the threading pattern this fix must match | scripts/db/recovery_verification.py / REQ-001 |
| scripts/db/config.py | `build_db_config()` rejects empty `sqlite_vec_so` with `ValueError` (`config.py:29`, `66-69`) — drives the fail-closed guard design | scripts/db/recovery_verification.py / REQ-001 |
| scripts/db/schema_sql.py | Canonical rag/session DDL: `chunks_vec` / `memories_vec` are `CREATE VIRTUAL TABLE ... USING vec0(...)` | tests/db/test_db_recovery.py / REQ-002 |
| tests/conftest.py | Isolation root keeps read-only resources (the real `vec0.so` path) and rewrites writable DB paths; extension-availability fallback pattern | tests/db/test_db_recovery.py / REQ-002 |

## Acceptance Criteria
- AC-1 (`REQ-001`): a healthy rag and a healthy session backup built with real vec0 tables pass `_run_logical_verification`; a target/config whose extension path cannot be resolved still returns `(False, "verification_unavailable")` with an error log — never success.
- AC-2 (`REQ-002`): new e2e tests pass with `_run_logical_verification` unpatched and assert `action == "restored"`, `logical_ok is True`, `active_db_state == "restored"` for rag and session.
- AC-3: `uv run pytest tests/db` stays green.

## Tests
- `REQ-001`: unit test in `tests/db/test_db_recovery.py`: patch `db.recovery_verification.build_db_config` to raise `ValueError` → `_run_logical_verification(candidate, "rag")` returns `(False, "verification_unavailable")` (fail-closed config path).
- `REQ-002`: new integration tests in `tests/db/test_db_recovery.py`: build a candidate DB via `SQLiteHelper("rag", db_path=..., sqlite_vec_so=<resolved path>)` with `CREATE VIRTUAL TABLE ... USING vec0(...)` and one populated row (plus documents/chunks/FTS rows so the report is fully consistent); same pattern for `session` (`memories_vec`); corrupt live DB file; `_restore_from_backup` with only `_run_integrity_check` patched for the corrupt/healthy transitions and `_run_logical_verification` left real; assert `action == "restored"` (AC-2). When the sqlite-vec extension is unavailable on the host, the tests skip with an explicit reason naming the missing extension path (Issue Testing Expectations).

## Documentation Impact
None. The `verification_unavailable` vocabulary is unchanged; `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is already the recovery reference and is edited by Plans 002/003/004 in this batch (see Cross-Plan Target Overlap Scan).

## Baseline Consistency (Step 5)
| Dimension | Baseline Value | Source (exact command) | Recorded |
|---|---|---|---|
| radon CC target 1 (recovery_verification.py) | top A (5) `_verify_rag_logic`, `_run_logical_verification` | `uv run radon cc scripts/db/recovery_verification.py -s` (run this cycle) | 2026-11-15 |
| vulture target 1 (recovery_verification.py) | No findings | `uv run vulture scripts/db/recovery_verification.py --min-confidence 80` (run this cycle) | 2026-11-15 |
| radon CC target 2 (test file) | test-file top B(12) | `uv run radon cc tests/db/test_db_recovery.py -s` (run this cycle) | 2026-11-15 |
| vulture target 2 | No `scripts/db` findings repo-wide | `uv run vulture scripts/ --min-confidence 80` (run this cycle) | 2026-11-15 |
| bandit targets | 45 low / 0 medium / 0 high | `uv run bandit -r scripts/ -c pyproject.toml` (run this cycle) | 2026-11-15 |
| coverage | project total 95%; tree clean at recording (no diff lines) | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (run this cycle) | 2026-11-15 |

## Assumptions
- The sqlite-vec extension exists on this host at the configured path (`/opt/llm/sqlite-vec/vec0.so`, verified loadable in this cycle's probe); the test suite itself does not currently depend on a real extension load, so the new tests resolve the path from the isolated config (`tests/conftest.py` keeps read-only resources at their real paths) and skip with an explicit reason when it is absent (Issue Testing Expectations; supersedes the earlier "fail loudly, not skip" design sentence — the Source Issue says skip with a clear reason).
- The `load_vec` semantics of `SQLiteHelper` are unchanged: explicit `db_path` + non-empty `sqlite_vec_so` → the extension loads on `open()` (`tests/db/test_sqlite_helper.py:277-349` pins this).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | None (the Issue's open question "DbConfig-only resolution vs Helper fallback" is resolved No-fallback by its Required Fix: the verification stage resolves via `build_db_config()`; no maintainer decision outstanding for this scope) | — | — | — |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/recovery_verification.py | Modify | Medium (rag/session restore verification behavior; no signature change, no caller change) | 0 | High (single author, >70%) | rsynced file; restart required (see Deploy notes) |
| tests/db/test_db_recovery.py | Modify | Low (test-only) | 0 | High (single author, >70%) | not applicable (rsynced) |

## Cross-Plan Target Overlap Scan

- Re-run after the re-correction (`tools/check_plan_target_overlaps.py`, 2026-11-15): `tests/db/test_db_recovery.py` shared with Plans 002/003/004 (judgment unchanged: disjoint test functions — 001 adds the vec e2e and fail-closed config tests, sequencing 001 first). `scripts/db/recovery_verification.py` newly shared with `plans/20261115-041859_dbreview004_integrity-probe-side-effects.md`. Judgment: **compatible (sequencing)** — 001 threads `sqlite_vec_so` into the Helper call at `recovery_verification.py:141`; Plan 004's REQ-005 later opens the same call read-only, and its Design already pins "load_vec behavior is unchanged (extension loading is connection-local and legal on ro connections)" (Plan 004, Helper read-only mode). Batch order 001→…→004; 004 re-reads the landed code at its Phase 4.

## Design
- Production (`scripts/db/recovery_verification.py`): in `_run_logical_verification`, after the verifier lookup and only for targets that have a logical verifier, resolve `cfg = build_db_config()`; on `ValueError` (empty/absent `sqlite_vec_so`, or config load failure) log an error and return `(False, "verification_unavailable")` — the same fail-closed vocabulary `_restore_from_backup` already maps (`recovery.py:394-408`). Open the candidate with `SQLiteHelper(target, db_path=str(db_path), sqlite_vec_so=cfg.sqlite_vec_so)` so `open()` loads the extension (matching `recovery_drill._verify_rag_session`). No signature change; `_verify_candidate` and `_post_restore_failure` need no edits. Rejected alternative: a `SQLiteHelper` config fallback when `db_path` is explicit — the Issue's Required Fix places resolution in the verification stage so the helper's explicit-path contract ("self-contained config", `helper.py:79-82`) stays intact.
- Tests (`tests/db/test_db_recovery.py`): reuse the fixture pattern of `test_wal_shm_sidecars_land_at_final_locations_after_activation` (`1024-1061`) but leave `db.recovery._run_logical_verification` unpatched; build candidates through `SQLiteHelper` with the extension explicitly passed; resolve the extension path from the isolated config; extension availability handled by skip-with-reason (see Assumptions).

## Implementation steps
1. **Phase 1: Production fix** (REQ-001; `scripts/db/recovery_verification.py`)
   - [ ] Resolve `sqlite_vec_so` from `build_db_config()` inside `_run_logical_verification`, pass it to `SQLiteHelper`, fail closed on config failure (REQ-001)
2. **Phase 2: Regression tests** (REQ-002; `tests/db/test_db_recovery.py`)
   - [ ] Add the fail-closed config unit test and the rag/session vec0-requiring e2e restore tests (REQ-001 unit + REQ-002)
   - [ ] Run `uv run pytest tests/db` and the full suite `-n auto` (AC-3)

### Release units
**Unit**: vec-restore-verification | **Phases**: 1, 2 | **Reason**: production fix and its locking tests are one release unit; Phase 2 asserts Phase 1's behavior. Batch order relative to other plans is unchanged (001 first; this plan touches no region owned by Plans 002/003/004).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/recovery_verification.py | Fail-closed unit test + real-candidate e2e verification | `uv run pytest tests/db/test_db_recovery.py -v` | AC-1 scenario asserted; healthy vec0 candidates pass; config failure returns `verification_unavailable` |
| tests/db/test_db_recovery.py | Integration e2e restore with real vec0 candidates (rag + session) | `uv run pytest tests/db/test_db_recovery.py -v` | New tests pass; AC-2 scenario asserted |
| tests/db (regression) | Existing suite | `uv run pytest tests/db -v` | No regressions |

## Risks
- **Risk**: sqlite-vec .so unavailable on some test host → **Mitigation**: new tests skip with an explicit reason naming the missing path; production keeps its fail-closed `verification_unavailable` behavior on config failure.
- **Risk**: existing tests that mock `SQLiteHelper` reach the new `build_db_config()` call inside `db.recovery_verification` unpatched → **Mitigation**: they read the isolated-root config (valid path) and pass kwargs into mock helpers; behavior verified by the full `tests/db` run in Phase 2.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Production fix (scripts/db/recovery_verification.py) | Completed | 20261115-095020 | 20261115-095020 | Procedure generated: implementations/20261115-075008_1 |
| 2 | Regression tests (tests/db/test_db_recovery.py) | Completed | 20261115-095020 | 20261115-095020 | Procedure generated: implementations/20261115-075008_2 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261115-075008_1_scripts_db_recovery_verification.py.md | 1 | Procedure | Created | — | — |
| implementations/20261115-075008_2_tests_db_test_db_recovery.py.md | 2 | Procedure | Created | — | — |

## Traceability
- **Workflow type**: B (issue-to-plan)
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261114-092848_dbreview001_logical-verify-vec-extension.md (archived to issues/done/)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-033931 (corrected 2026-11-15 after the upstream pull; re-corrected 2026-11-15 in the procedure workflow after Step 3a disconfirmed the "fix already merged" claim)
- **Related target files**: scripts/db/recovery_verification.py, tests/db/test_db_recovery.py

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Change 1 / Required Fix ("Resolve sqlite_vec_so from build_db_config() ... pass it to SQLiteHelper") — un-retired by this cycle's probe evidence | scripts/db/recovery_verification.py | Phase 1 | AC-1 | Fail-closed unit test + e2e tests | Pending |
| REQ-002 | Testing Expectations (vec0-requiring candidate success; AC line "healthy rag and healthy session backups ... pass _run_logical_verification") | tests/db/test_db_recovery.py | Phase 2 | AC-2 | New e2e tests | Pending |

### Retired Requirements (upstream resolution, `4543c2aa4`)
| Original REQ | Original target | Resolution evidence |
|---|---|---|
| ~~Thread config/candidate path through logical verification~~ | scripts/db/recovery_verification.py | **Un-retired 2026-11-15**: the threading was never merged (`git log -S "sqlite_vec_so"` over the recovery modules is empty; probe shows healthy vec0 candidates still fail). Carried as REQ-001. |
| Replace the drill bypass fixture | tests/db/test_recovery_drill.py | Fixture removed upstream (`_run_with_vec_extension` no longer exists in repo); drill threads `sqlite_vec_so` (`recovery_drill.py:107`, `121`, `209`). Still retired. |
| Map unverifiable candidate to `verification_unavailable` | scripts/db/recovery.py | `recovery.py:394-408`; tests at `tests/db/test_db_recovery.py` (unverified-candidate tests). Still retired. |
| Add verification tests | tests/db/test_db_recovery.py | Partially merged upstream; the vec0-requiring success scenario remains — carried as REQ-002. |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261115-075008 -->