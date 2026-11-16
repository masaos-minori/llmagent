## Goal
- Align the `tests/db/test_db_maintenance.py` harness to the production `T/Z` timestamp format and add the boundary/negative/bool/tie-order tests that pin Plan 007's validation contract (REQ-007; AC-1..AC-4).

## Scope
**Release unit**: retention-input-validation (Phases 1-3 of the plan; lands with `20261116-073054_01`..`_04`)

- In scope: `_make_session_db` harness alignment (`:112-122`; DDL defaults `:42,50`; seeded literals `:163-328`, 27 space-format literals); new config-boundary, helper-guard, cutoff-day, `0`-disables, and tie-order tests in this file.
- Out of scope: store-side tests (companion in procedure `20261116-073054_02`) and `get_typed` matrix tests (companion in `_03`); the production edits (procedures `_01`..`_04`); `docs/41_db/db_06...` update (plan Phase 3 step).

## Assumptions
- Verification finding (2026-11-16, re-measured at HEAD `d0500d87c`): the file has 65 tests (58 at the plan's re-verification baseline `8fc337615`; Plan 006 added 8 tests in classes landed at `:1279`+ — `TestPurgeTransactionAtomicity`, `TestVacuumDatabaseError`, `TestConfigErrorPropagation`, `TestHandleMaintenanceErrorReraise`, `TestPruneIdsSource` — and replaced 1 `TestMaintenanceMode` test, net +7); the harness `_make_session_db` (`:112-122`) seeds space-format `created_at` literals (`:163-328`, 27 literals) via DDL defaults at `:42,50` (`datetime('now')` space form) — the production-vs-harness format mismatch is invisible today (plan row evidence). Plan 004's rotation-invariance class is landed at `:1128` (`TestArchiveVerification`).
- Own-document decision (companion rule, condition 3): this row is NOT a companion of procedure `_01` — the harness realignment re-formats seeded literals used by Plan 004's landed tests and (once implemented) Plan 006's rollback tests in the same shared file; the seed-migration scope is a decision of its own, not a plan-prescribed detail (SKILL.md companion conditions).
- Gated by Plan 007's upstream: run only after Plan 006's code is implemented (its rollback tests and `begin_immediate` flow are landed) — re-read those landed sections before appending (plan Dependencies).
- The alignment is assertion-neutral for existing tests: differing year/month positions dominate the comparison byte, so delete/keep expectations are format-independent (plan Risks mitigation, checked Step 2 against the `:163-328` seeds at current HEAD).

## Design decisions
- Align DDL default to `strftime('%Y-%m-%dT%H:%M:%SZ','now')` and move seeded literals to the same shape in one edit, so the whole file exercises the production comparison (plan Design, harness alignment) — the alternative of only adding new T/Z-seeded tests was rejected: the hidden regression class would stay invisible to the existing tests.
- 5-second test margins (not 1 s) to prove the one-second contract deterministically: SQL `now` and Python `utcnow` are both UTC and test execution is sub-second (plan Assumptions).

## Alternatives considered
- Fold this row as a companion of `_01`: rejected (see Assumptions — condition 3 fails; shared-harness migration scope is its own decision).
- A second T/Z-only harness beside the old one: rejected — two harnesses diverge; the plan requires the shared `_make_session_db` to match production.

## Implementation
### Target file
`tests/db/test_db_maintenance.py`

### Procedure
1. Harness alignment: `_make_session_db` DDL defaults (`:42,50`) become `strftime('%Y-%m-%dT%H:%M:%SZ','now')`; the seeded literals at `:163-328` switch from space format to the `T/Z` shape (REQ-007).
2. Config-boundary tests (AC-1, AC-3; monkeypatch `db.maintenance.ConfigLoader.load`, pattern of `:384` and `:1356`): negative/bool/float/string for each of the four retention keys → `ValueError` naming the key; `0` values load cleanly and the corresponding rule deletes nothing (`max_sessions=0` with expired-by-count sessions keeps all; `max_files=0` keeps all archives; `max_age_days=0` stays disabled as today) (REQ-001, REQ-003).
3. Helper-direct-construction tests (AC-1): `RetentionConfig(max_sessions=-1, max_age_days=0)` → `purge_old_sessions` raises `ValueError` in both modes; `CorruptArchiveRetentionConfig(max_files=-1, ...)` → `purge_corrupt_archives` raises in both modes (validation precedes the mode handler) (REQ-001).
4. Cutoff-day regression test (AC-2) with the aligned harness: seed one session stamped `utcnow - 1 day - 5 s` and one `utcnow - 1 day + 5 s`; `max_age_days=1` → exactly the past-cutoff row deleted, regardless of time of day (REQ-004).
5. Tie-order test (AC-4): seed 5 sessions with one identical `created_at` and `max_sessions=2`; assert the exact kept set (`session_id` 4,5 kept; 1-3 deleted), repeated twice for determinism (REQ-006).
6. Regression watch (no assertion changes expected): `test_boundary_below/at/above_max_sessions` (`:208-230`) under the new tie-breaker; Plan 006 rollback/atomicity tests and Plan 004 rotation-invariance tests (`:1128+`) re-run after the SQL rewrite and harness alignment (plan Tests regression watch).

### Method
- Append new test classes disjoint from Plan 004's (`:1128-1278`) and Plan 006's landed sections (`:1279-1389`+); the harness edit is the one shared-region change and is verified by running the whole file.

### Details
- Store-side `days=0` boundary and negative tests are covered by the companion section in procedure `_02`; `get_typed` matrix tests by `_03` — do not duplicate them here.
- Sequence context: Plan 008 later appends a new test class to this file (artifact retention); this document lands disjoint classes first.

## Compatibility considerations
- 65 pre-existing tests keep their assertions; only the harness DDL/seed format changes (format-independent expectations, plan Risks mitigation).
- The file is shared with Plans 004 (landed) / 006 (procedure `20261116-072110_04`) / 008 (later): disjoint test classes, fixed order 004 → 006 → 007 → 008 (plan Overlap Scan).

## Security considerations
- Test-only change; bandit does not scan `tests/` in the `-r scripts/` run; no secrets or subprocess use added.

## Rollback considerations
- `git checkout` revert of the unit commit; part of release unit retention-input-validation — these tests are the AC-1..AC-4 regression gate; revert together with `_01`..`_04`.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v` → new tests pass (AC-1..AC-4) and all pre-existing tests, incl. Plan 006 rollback tests and Plan 004 `:1128+` class, stay green (plan Validation plan row 4).
- `uv run pytest tests/db tests/shared tests/agent/commands -v` → plan Phase 3 combined run.
- `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` → ≥ 90% on the branch diff (baseline 95%).

## Completion criteria
- The harness stores and seeds `T/Z` timestamps; a row 1 s past the cutoff is deleted and 1 s inside survives regardless of time of day; negative retention values raise key-naming `ValueError` from both config load and direct construction in both modes; `0` disables its rule; tie groups resolve deterministically; the whole file (pre-existing + new tests) is green.

## Out of Scope
- Store/config test files (companions in procedures `20261116-073054_02`/`_03`); production edits (`_01`..`_04`); `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` update (plan Phase 3 step).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Harness alignment to `T/Z` (REQ-007 part) | Completed | — | — | gated: plans/done/20261115-050112_dbreview006_maintenance-error-semantics.md phase all - re-read landed 006 tests first; gate satisfied 2026-11-16: Plan 006 completed, procedures 20261116-072110_01.._05 archived (commit d0500d87c); landed 006 sections re-verified at :1279-1405 verified 2026-11-16: targeted tests + gates green; full suite/diff-cover skipped per memo3 instruction |
| 2 | Add boundary/negative/bool/tie-order tests (plan Phase 3) | Completed | — | — | REQ-007; after `_01`..`_04` land; citations re-anchored 2026-11-16 at HEAD d0500d87c (file 65 tests, harness :112-122, seeds :163-328, DDL :42,50, monkeypatch pattern :384/:1356, Plan 004 class :1128) verified 2026-11-16: targeted tests + gates green; full suite/diff-cover skipped per memo3 instruction |
| 3 | Run the validation sequence (`rules/toolchain.md`) + diff-cover | Completed | — | — | verified 2026-11-16: targeted tests + gates green; full suite/diff-cover skipped per memo3 instruction |

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
- **Requirement ID**: REQ-007 (harness alignment + boundary/tie/validation tests for REQ-001..REQ-006)
- **Source issue**: issues/20261114-092855_dbreview007_retention-input-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-050559_dbreview007_retention-input-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-073054
- **Related target files**: tests/db/test_db_maintenance.py