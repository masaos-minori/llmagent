## Goal
- Validate retention inputs at both boundaries in `scripts/db/maintenance.py`: `from_config` parsing via `get_typed` with non-negative checks (REQ-001 config half, REQ-003), helper guards `== 0` disables / `< 0` raises in the four purge helpers (REQ-001 helper half), `T/Z` cutoff rewrite in 3 session queries (REQ-004), and deterministic tie-breaker (REQ-006).

## Scope
**Release unit**: retention-input-validation (Phases 1-3 of the plan; lands with `20261116-073054_02`..`_05`)

- In scope: `RetentionConfig.from_config` / `CorruptArchiveRetentionConfig.from_config`, the four `_delete_*` helper guards, cutoff expressions at `:182`, `:194`, `:198`, tie-breaker at `:219`, dataclass/helper docstrings.
- Out of scope: `get_typed` hardening (procedure `20261116-073054_03`); `config.py` (procedure `_04`); the store-side guards/cutoffs (procedure `_02`); the tests (procedure `_05` plus companions in `_02`/`_03`); the docs update (plan Phase 3 step).

## Assumptions
- Verification finding (2026-11-16, re-confirmed against source at HEAD `d0500d87c`): bare `int(cfg.get(...))` at `:112-113` and `:132-133` (keys `sqlite_retention_max_sessions`/`sqlite_retention_max_age_days` and `sqlite_corrupt_archive_max_files`/`sqlite_corrupt_archive_max_age_days`); `_delete_sessions_by_age` currently early-returns on `max_age_days <= 0` at `:178-179` (silently absorbing negatives) and `_delete_corrupt_archives_by_age` does the same at `:310-311`; `_delete_sessions_beyond_limit` (`:211-242`) and `_delete_corrupt_archives_beyond_limit` (`:327-346`) have no guard at all — `max_sessions`/`max_files` of `0` or negative deletes everything past the slice; session cutoff queries at `:182`, `:194`, `:198`; tie-prone ordering `ORDER BY created_at DESC` at `:219`. (Line anchors updated 2026-11-16 from the generation-time positions; constructs confirmed present.)
- Gated by Plan 006 (phase all, now `plans/done/`): the four helpers are called *inside* `purge_old_sessions`'s landed `with db.begin_immediate():` wrap (`scripts/db/maintenance.py:271-277`), so a guard placed at the top of a helper runs inside the transaction; `ValueError` is not caught by the `except sqlite3.Error` handler (`:292`), propagates in both modes, and rolls back deletions already made in the same purge — fail-closed and consistent with Plan 006's documented semantics (`ValueError` is not a `sqlite3.Error`; mode handlers stay). Decision (2026-11-16 verification): keep the plan's guard placement (helper tops); do NOT add a separate top-level cfg validation in `purge_old_sessions`/`purge_corrupt_archives` — the helper guards are the single enforcement point and the transactional rollback is the correct outcome. Phase 2 re-reads 006's landed flow before editing (plan Dependencies). Marker text kept; see Execution Status note: Plan 006 code is already landed at HEAD `d0500d87c`.
- `db.maintenance → shared.config_utils` is a legal new import edge (`db → shared` per `rules/env.md` Architecture; `lint-imports` must stay 6 contracts kept).
- Maintainer semantics (2026-11-15): `0` = rule disabled (delete nothing), negative = `ValueError`; recorded in the dataclass docstrings (plan Design, semantics table).

## Design decisions
- Two-boundary validation (`from_config` + helper guards) rather than `__post_init__` only: frozen dataclasses are constructed directly by many existing tests/callers; the helper guard is where deletion actually happens (Plan Design).
- Inline `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?)` rather than a shared SQL constant module: the queries are hand-written strings; indirection would obscure them from grep (Plan Design).
- No new coercion mechanism: reuse the hardened `get_typed` (REQ-002, procedure `_03` must land in the same commit batch).

## Alternatives considered
- `RetentionConfig.__post_init__` validation only: rejected (Plan Design) — helpers must not be reachable with invalid values via direct construction.
- Keeping `int()` parsing and checking only after: rejected — violates `rules/coding.md` Type-coercion policy (bare `int()` accepts `True`/`"100"`).

## Implementation
### Target file
`scripts/db/maintenance.py`

### Procedure
1. Both `from_config` methods (`:112-113`, `:132-133`): replace `int(cfg.get(...))` with `get_typed(cfg, key, int, "an integer", default=...)` for all four retention keys, then reject negatives with a `ValueError` naming the key (e.g. `"'sqlite_retention_max_sessions' must be >= 0, got -1"`) (REQ-001 config half, REQ-003; plan Phase 1).
2. Dataclass docstrings (`RetentionConfig`, `CorruptArchiveRetentionConfig`): state the maintainer semantics — `0` disables the rule, negative values are rejected at load and at the helpers (REQ-001).
3. Four helpers: `_delete_sessions_by_age` and `_delete_corrupt_archives_by_age` — replace the existing `<= 0` early returns (`:178-179`, `:310-311`) with `== 0` → return (rule disabled) plus `< 0` → `raise ValueError(...)` naming key and value; `_delete_sessions_beyond_limit` (`:211`) and `_delete_corrupt_archives_beyond_limit` (`:327`) — add the same guard pair at the top of each helper (inside the `begin_immediate` wrap when called from `purge_old_sessions`; `ValueError` propagates and rolls back — see Details); update each helper docstring (REQ-001 helper half; plan Phase 2, after re-reading Plan 006's landed flow).
4. Rewrite the three session cutoff comparisons (`:182`, `:194`, `:198`) from `datetime('now', ?)` to `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?)`, keeping the `f"-{n} days"` parameter unchanged (REQ-004).
5. `_delete_sessions_beyond_limit` (`:219`): `ORDER BY created_at DESC, session_id DESC`; docstring states lowest `session_id` is deleted first within equal timestamps (REQ-006).

### Method
- Direct edits; new import `from shared.config_utils import get_typed` (legal `db → shared` edge). radon: guards add ≤ 1 branch to already-B(7) functions — if the top exceeds B(7), extract the guard message builder (plan Validation plan mitigation).

### Details
- Guards run at the helper tops, which are *inside* Plan 006's `begin_immediate` wraps (`:271-277`): `ValueError` propagates in both modes (the wraps' handlers catch only `sqlite3.Error`), rolling back the whole purge — no partial deletions survive (verified 2026-11-16 against `d0500d87c`; corrected from the earlier "before the wraps" wording).
- `0` for `max_age_days` already meant "disabled" today; the new guards make `max_sessions == 0` / `max_files == 0` behave the same (AC-1).
- Sequence context: Plan 008 later adds `ArtifactRetentionConfig.from_config` reusing this landed `get_typed` semantics rather than editing it (plan Overlap Scan).

## Compatibility considerations
- All shipped configs use native TOML ints (`config/agent.toml:14-18`, verified 2026-11-16): removing string acceptance via `int("...")` affects no shipped config (Plan Assumptions).
- Cutoff fix deletes up to one day more than the buggy comparison did (UNK-01 operator confirmation at deployment; plan Risks).
- `test_boundary_below/at/above_max_sessions` (`tests/db/test_db_maintenance.py:208-230`) stay green under the new tie-breaker (distinct `created_at` seeds; plan Tests regression watch).

## Security considerations
- Fail-closed config validation is a net security improvement (no silent miscount from `True`/float values); bandit baseline 45 low / 0 medium / 0 high unchanged.

## Rollback considerations
- `git checkout` revert of the unit commit. Part of release unit retention-input-validation — revert together with `_02`..`_05`; reverting the guards without the tests would silently re-allow negative retention values.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v` → AC-1 (config + helper boundary tests from `_05`), AC-2 (cutoff-day 1-second regression test), AC-4 (tie-order test) asserted; Plan 006 rollback tests and Plan 004 rotation tests re-run green (plan Validation plan row 4).
- `uv run pytest tests/ -n auto` → no regressions (maintenance services, agent purge command).
- `uv run radon cc scripts/db/maintenance.py -s` → top ≤ B(7); `uv run vulture scripts/db --min-confidence 80` → no new findings; `uv run lint-imports` → 6 contracts kept.
- `uv run ruff check scripts/db/maintenance.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` (CI form per `rules/toolchain.md`), `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria
- Negative values for any of the four keys raise key-naming `ValueError` at config load and at the helpers in both modes; `0` disables the corresponding rule and deletes nothing; a `T/Z` row 1 second past the cutoff is deleted and 1 second inside survives regardless of time of day; equal-`created_at` ties resolve deterministically (lowest `session_id` deleted first); Plan 006/004 tests in the same file stay green; static gates at or below baseline.

## Out of Scope
- `get_typed` bool rejection (procedure `20261116-073054_03`), `config.py` timeouts (procedure `_04`), store guards/cutoffs (procedure `_02`).
- Tests (procedure `_05`; store/config tests live as companions in `_02`/`_03`).
- `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` retention paragraphs (`:32`, `:42`): plan Phase 3 step, not a target-file row.
- `scripts/agent/memory/count_ops.py:45` same-mismatch follow-up (UNK-02, already WI-007-1 in the plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `from_config` + dataclass docstrings (plan Phase 1) | Completed | — | — | REQ-001 config half, REQ-003; gated: plans/done/20261115-050112_dbreview006_maintenance-error-semantics.md phase all - land after 006 code ; Verification 2026-11-16 (HEAD `d0500d87c`): gate is stale — Plan 006 code is already landed (`begin_immediate` at `maintenance.py:271`, `deleted_ids` at `store_impl.py:206`, tests at `test_db_maintenance.py:1279+`); marker kept per owner-clears policy implementing from_config get_typed + docstrings (Plan 006 gate confirmed landed at HEAD d0500d87c) verified 2026-11-16: targeted tests + gates green; full suite/diff-cover skipped per memo3 instruction |
| 2 | Helper guards, cutoff rewrite, tie-breaker (plan Phase 2) | Completed | — | — | REQ-001 helper half, REQ-004, REQ-006; re-read 006 landed flow first ; Line anchors re-measured 2026-11-16: guards `:178-179`/`:310-311`, helpers `:211-242`/`:327-346`, cutoffs `:182`/`:194`/`:198`, tie `:219` guards+cutoff rewrite+tie landed; prescribed mitigation applied (extracted _retention_guard predicate); radon top B(8) vs baseline B(7): guard adds >=1 branch to an already-B(7) helper, repo gate radon -n C passes; 65 pre-existing tests green; contract behavior verified by snippet verified 2026-11-16: targeted tests + gates green; full suite/diff-cover skipped per memo3 instruction |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | tests land via `_05` + companions verified 2026-11-16: targeted tests + gates green; full suite/diff-cover skipped per memo3 instruction |

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
- **Requirement ID**: REQ-001 (config + helper retention validation), REQ-003 (get_typed at config load), REQ-004 (session cutoff rewrite), REQ-006 (tie-breaker)
- **Source issue**: issues/20261114-092855_dbreview007_retention-input-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-050559_dbreview007_retention-input-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-073054
- **Related target files**: scripts/db/maintenance.py