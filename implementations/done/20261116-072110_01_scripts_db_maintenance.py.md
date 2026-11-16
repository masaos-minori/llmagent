## Goal
- Make `scripts/db/maintenance.py` honor the STRICT/BEST_EFFORT contract: transactional session purge with honest failure data (REQ-001), `sqlite3.Error` capture in `vacuum_db` (REQ-002), documented config-error propagation (REQ-003), context-independent re-raise in `_handle_maintenance_error` (REQ-004), and `data["pruned_ids"]` sourced from the delete transaction (REQ-005, maintenance side).

## Scope
**Release unit**: maintenance-error-semantics (Phases 1-3 of the plan; lands with `20261116-072110_02`..`_05`)

- In scope: `purge_old_sessions` transaction wrap + failure data; `vacuum_db` handler widening; four mode docstrings; `raise exc`; `prune_old_memories` id-source switch.
- Out of scope: `MemoryDeleteResult.deleted_ids` field (own procedure `20261116-072110_02`) and its population (own procedure `20261116-072110_03`); the tests (own procedure `20261116-072110_04`); the `tests/agent/commands/test_memory_data_ops.py` regression check (own procedure `20261116-072110_05`); retention value validation (Plan 007); archive retention gaps (Plan 008).

## Assumptions
- Verification finding (2026-11-16, HEAD `8fc337615`): all five plan claims re-confirmed; corrected anchors are `purge_old_sessions` `:242-298` (single `db.commit()` at `:275`, failure `extra_data` at `:291-295`), `vacuum_db` handler `:163`, `from_config` calls at `:259`/`:355`, `purge_corrupt_archives` handler `except OSError` at `:379`, bare `raise` at `:79`, `collect_prunable_ids` call at `:400`.
- `SQLiteHelper.begin_immediate` (`scripts/db/helper.py:418-422`, rollback via `_begin_transaction` `:398-416`) is reused as-is; `helper.py` needs no edit in Plan 006 (reference-only row). Anchors re-verified 20261116 against HEAD `206e36a3f` (drift from the `:382`/`:362-389` cited at generation time caused by the helper-open-leak refactor).
- `MagicMock(spec=SQLiteHelper)` tests accept `db.begin_immediate()` as a no-op context manager because the method exists on the real class (Plan Assumptions); the mock-based mode tests at `tests/db/test_db_maintenance.py:963-990` stay valid after the wrap. Adversarial re-verification 20261116 finding: the `_FakeDB`-backed purge tests at `:140-300` use a bare-`sqlite3` drop-in (`_FakeDB`, `tests/db/test_db_maintenance.py:74-91`) with no `begin_immediate` method — they go red (AttributeError) when this procedure lands and stay red until procedure `_04` extends `_FakeDB` with a `begin_immediate` context manager (allowed red state under the release unit's batch mode; recorded in the unit Failure Log).
- Success-path `data` (computed `kept`, `:271-273`) is unchanged; only failure-path counts change to zeros (Plan Design, honest failure data).

## Design decisions
- Reuse `db.begin_immediate()` rather than adding rollback to `_handle_maintenance_error`: the helper already rolls back on any normal exception and re-raises, and the Issue's Required Change names it (Plan Design).
- No outer transaction around `prune_old_memories`: `delete_memories_before` already opens `BEGIN IMMEDIATE` (`scripts/db/store_impl.py:189`); an outer wrap would raise `OperationalError: cannot start a transaction within a transaction`. Identity-consistent reporting comes from `delete_result.deleted_ids` instead (REQ-005).
- Config errors propagate in both modes (maintainer decision 2026-11-15): `from_config` calls stay outside the `try`; `build_db_config` stays inside the `try` whose handler catches only `OSError`, so `ValueError` propagates. Docstrings state this explicitly.
- `raise exc` keeps traceback chaining via `exc.__traceback__` and makes the helper callable outside an `except` block.

## Alternatives considered
- Rollback inside `_handle_maintenance_error`: rejected — needs connection access and still leaves first-delete ownership (Plan Design).
- Absorbing config errors in BEST_EFFORT: rejected — hides persistent misconfiguration behind per-run logs (maintainer decision).
- Removing the store's inner transaction: rejected — it is what makes the cross-table delete atomic today.

## Implementation
### Target file
`scripts/db/maintenance.py`

### Procedure
1. `purge_old_sessions` (`:242-298`): wrap both `_delete_sessions_by_age` and `_delete_sessions_beyond_limit` calls in `with db.begin_immediate():`; drop the manual `db.commit()` at `:275`; on failure the handler reports `data == {"age_deleted": 0, "count_deleted": 0, "kept_active_session": None}` instead of the attempted counts and requested `keep_session_id` (REQ-001; fixes `extra_data` `:291-295`).
2. `vacuum_db` (`:151-165`): widen the handler at `:163` from `(sqlite3.OperationalError, RuntimeError)` to `(sqlite3.Error, RuntimeError)` — STRICT still re-raises via `_handle_maintenance_error`; BEST_EFFORT returns `action="vacuum_failed"` for `sqlite3.DatabaseError` (REQ-002).
3. Docstrings of the four mode-taking entry points (`vacuum_db`, `purge_old_sessions`, `purge_corrupt_archives`, `prune_old_memories`): state that config-load failures (`from_config`, `build_db_config`) propagate in both modes; control flow at `:259`, `:355`, `:379` stays unchanged (REQ-003).
4. `_handle_maintenance_error` (`:65-85`): replace the bare `raise` at `:79` with `raise exc` (REQ-004).
5. `prune_old_memories` (`:388-414`): remove the `store.collect_prunable_ids` call at `:400`; build `data["pruned_ids"]` as `list(delete_result.deleted_ids)` from the `MemoryDeleteResult` returned by `delete_memories_before` (REQ-005; depends on `20261116-072110_02` and `_03` landing in the same batch). Keep the consumer shape `list[str]` (`memory_data_ops.py:402`, `test_db_maintenance.py:416`).

### Method
- Direct edit in the existing module; no new imports (`maintenance.py` already imports `db.store_impl` and `db.helper`; arch-linter contracts stay 6, Plan Architecture check).

### Details
- Steps 1-4 are plan Phase 1; step 5 is plan Phase 2 (the `maintenance.py` part of REQ-005) and must be done after the `store_protocols.py`/`store_impl.py` rows land.
- radon baseline: `_delete_sessions_beyond_limit` B(7), `purge_old_sessions` B(6); the `begin_immediate` wrap adds no branch (Plan Validation plan).
- Sequence context: Plan 004 lands first (docs/tests side effects), Plans 007/008 edit `maintenance.py` later in the fixed order 004 → 006 → 007 → 008; 007 adds guards at the top of the purge helpers and rewrites cutoff SQL inside them, 008 adds a new config class and `purge_archive_artifacts()` — neither re-edits 006's landed regions.

## Compatibility considerations
- Failure-path `data` changes (attempted counts → zeros): existing tests assert no counts on failure (`test_purge_best_effort_returns_partial_result_on_error` `:973-987`, checked this cycle); docstrings and the docs update state the semantics (Plan Risks).
- `data["pruned_ids"]` stays `list[str]`; consumers (`agent.services.db_maintenance_service`, `rag_maintenance_service`, `scripts/agent/commands/memory_data_ops.py:401-402`) keep their shape (AC-5).
- STRICT behavior is unchanged everywhere; only BEST_EFFORT handling widens in `vacuum_db`.

## Security considerations
- No new attack surface; bandit baseline 45 low / 0 medium / 0 high unchanged.

## Rollback considerations
- `git checkout` revert of the unit commit; revert restores non-transactional purge but leaves no state behind. Part of release unit maintenance-error-semantics — revert together with `20261116-072110_02`..`_05` to keep the suite green (the `deleted_ids` field must not outlive its consumer).

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v` → AC-1 (real-DB rollback test, `in_transaction is False`), AC-2..AC-4 (mode matrix), AC-5 (id-source + not-called spy) asserted by the tests from `20261116-072110_04`.
- `uv run pytest tests/ -n auto` → no regressions (maintenance services consumers).
- `uv run radon cc scripts/db/maintenance.py -s` → top stays ≤ B(7).
- `uv run ruff check scripts/db/maintenance.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` (CI form per `rules/toolchain.md`), `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run lint-imports`.

## Completion criteria
- A forced failure in the count rule after a successful age delete leaves the sessions table unchanged, the helper connection not `in_transaction`, and `success=False` with `data == {"age_deleted": 0, "count_deleted": 0, "kept_active_session": None}`; a `sqlite3.DatabaseError` in `vacuum_db` raises in STRICT and returns `vacuum_failed` in BEST_EFFORT; config-load failures raise in both modes and every mode docstring says so; `_handle_maintenance_error` works outside an `except` block; `pruned_ids` equals exactly the deleted ids; lint/type/coverage gates pass.

## Out of Scope
- The tests (own procedure `implementations/20261116-072110_04_tests_db_test_db_maintenance.py.md`) and the memory-ops regression check (`_05`).
- The `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` mode/atomicity paragraph updates: plan Phase 3 step, handled at plan level (not a target-file row); the docs file is shared with Plan 008 per the Overlap Scan.
- Retention value validation and timestamp-format fixes (Plan 007); `checkpoint_wal` config read (out of Plan 006 scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement purge transaction, vacuum handler, docstrings, `raise exc` (plan Phase 1) | Completed | 2026-11-16 | 2026-11-16 | REQ-001..REQ-004 Phase 1 landed; 12 _FakeDB purge tests red (AttributeError: begin_immediate) - expected batch red until _04 lands; consumers green |
| 2 | Switch `pruned_ids` to `delete_result.deleted_ids` (plan Phase 2, maintenance part) | Completed | 2026-11-16 | 2026-11-16 | REQ-005; after `_02`/`_03` land pruned_ids now from delete_result.deleted_ids; collect_prunable_ids call removed; prune mock tests stay green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-16 | 2026-11-16 | tests land via `20261116-072110_04` ruff/mypy/lint-imports/gates clean; targeted tests only (full-suite waived per user instruction): 12 known _FakeDB reds unchanged, no new failures; radon top B(7) unchanged |

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
- **Requirement ID**: REQ-001 (transactional purge), REQ-002 (vacuum sqlite3.Error), REQ-003 (config propagation), REQ-004 (explicit re-raise), REQ-005 (pruned_ids source)
- **Source issue**: issues/20261114-092854_dbreview006_maintenance-error-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-050112_dbreview006_maintenance-error-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-072110
- **Related target files**: scripts/db/maintenance.py