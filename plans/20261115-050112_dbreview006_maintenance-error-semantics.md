# Plan 006: Maintenance STRICT/BEST_EFFORT contract and transactional purge

## Goal
- Make `db.maintenance` honor its documented STRICT/BEST_EFFORT contract: every `sqlite3.Error` subclass is mode-handled, config-load failures are explicitly documented as propagating in both modes, and multi-statement maintenance work commits or rolls back as one unit with reported counts and ids derived from the transaction that performed the change.

## Priority
Medium (Issue Priority)

## Scope
- **In-Scope**: transactional `purge_old_sessions`; `vacuum_db` catching `sqlite3.Error`; documented propagation of config-load errors; explicit-exception re-raise in `_handle_maintenance_error`; `MemoryDeleteResult.deleted_ids` as the single source for `prune_old_memories` reported ids; unit tests per path.
- **Out-of-Scope**: retention value validation and timestamp-format fixes (`plans/...007` issue `issues/20261114-092855_dbreview007_retention-input-validation.md`); archive retention gaps (issue 008); `checkpoint_wal` config read (Issue: "not part of this claim" — it has no mode parameter).
- **Dependencies**: none per the Issue.
  - **Depends on**: plans/20261115-041859_dbreview004_integrity-probe-side-effects.md | phase all | sequencing only: 004 adds rotation-invariance tests to `tests/db/test_db_maintenance.py` and lands first; 006 adds tests to disjoint sections of the same file. No behavioral dependency.

## Background
From the Source Issue (F-006), re-verified against the post-pull tree (HEAD `edc79f698`, 2026-11-15). All five claims hold:

- `purge_old_sessions` (`scripts/db/maintenance.py:242-298`) runs `_delete_sessions_by_age` and `_delete_sessions_beyond_limit` as raw `db.execute` calls and commits once at `:276`; a failure in the second rule leaves the first delete in an open implicit transaction on the shared connection, and the failure `extra_data` (`:292-297`) reports the attempted `age_deleted`/`count_deleted` and the requested `keep_session_id`, not what was committed.
- `vacuum_db` (`:151-165`) catches `(sqlite3.OperationalError, RuntimeError)` at `:163`; `sqlite3.DatabaseError` (corrupt file) escapes BEST_EFFORT.
- Config errors already propagate today: `RetentionConfig.from_config` / `CorruptArchiveRetentionConfig.from_config` are called outside the `try` (`:259-260`, `:357-358`), and `build_db_config` in `purge_corrupt_archives` is inside the `try` but the handler catches only `OSError` (`:383`). **Maintainer decision (2026-11-15): propagate — the Issue's Unresolved Question is resolved as "config-load failure is NOT absorbed in BEST_EFFORT"; the behavior is documented in docstrings and pinned by characterization tests.**
- `_handle_maintenance_error` (`:65-85`) re-raises with a bare `raise` (`:79`), valid only inside an `except` block.
- `prune_old_memories` (`:388-414`) calls `store.collect_prunable_ids` (`:400`) outside the transaction `delete_memories_before` later opens inside `SQLiteMemoryDeleteStore` (`scripts/db/store_impl.py:191-205`), so reported `pruned_ids` can diverge from rows actually deleted.

Consumers: `agent.services.db_maintenance_service` / `rag_maintenance_service` rely on the mode contract; `scripts/agent/commands/memory_data_ops.py:402-403` reads `data["pruned_ids"]` to emit delete events (its own `collect_prunable_ids` call at `:371-373` is a dry-run/confirm count and is unaffected).

## Problem
A BEST_EFFORT maintenance call can crash the agent (DatabaseError, config errors) or leave partial deletes pending on a shared connection that a later commit persists — while the returned result reports counts that were never committed. `pruned_ids` events can name rows that were not deleted.

## Reason for Change
Callers rely on the documented mode contract to keep maintenance from crashing the agent, and on `MaintenanceResult.data` to describe what actually changed; both are currently broken on named paths.

## Implementation Intent
Reuse `SQLiteHelper.begin_immediate` (single transaction with rollback on any exception, `scripts/db/helper.py:242-261`) for the session purge; widen the vacuum handler to `sqlite3.Error`; document config-error propagation in both modes; re-raise the passed exception explicitly; make the delete transaction's `RETURNING` ids the only source of reported `pruned_ids`.

## Requirements
- `REQ-001`: `purge_old_sessions` runs both delete rules inside one `db.begin_immediate()`; on failure nothing is committed and no transaction stays open; failure `data` reports `age_deleted=0`, `count_deleted=0`, `kept_active_session=None`; success `data` unchanged (AC-1).
- `REQ-002`: `vacuum_db` catches `sqlite3.Error` (covers `DatabaseError`) and `RuntimeError`; STRICT still re-raises; BEST_EFFORT returns `action="vacuum_failed"` for a corrupt-file `DatabaseError` (AC-2).
- `REQ-003`: config-load failures (`from_config`, `build_db_config`) propagate in both modes; control flow unchanged; each mode-taking entry point states this in its docstring (AC-3, maintainer decision 2026-11-15).
- `REQ-004`: `_handle_maintenance_error` re-raises the passed exception explicitly (`raise exc`) so it works when called outside an `except` block; BEST_EFFORT return unchanged (AC-4).
- `REQ-005`: `MemoryDeleteResult` gains `deleted_ids: tuple[str, ...] = ()`; `delete_memories_before` populates it from `DELETE ... RETURNING`; `prune_old_memories` sets `data["pruned_ids"]` from it and no longer calls `collect_prunable_ids` (AC-5).
- `REQ-006`: tests in `tests/db/test_db_maintenance.py` pin each behavior: rollback atomicity, DatabaseError capture, config-error propagation in both modes, direct helper re-raise, `pruned_ids` == deleted ids and `collect_prunable_ids` not called by maintenance (AC-1..AC-5).

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8: every row exists, requires modification, has supporting evidence recorded this cycle, and links to a Requirement).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/maintenance.py | Modify | `begin_immediate` wrap + honest failure data in `purge_old_sessions`; `sqlite3.Error` in `vacuum_db`; docstring propagation statements; `raise exc` in `_handle_maintenance_error`; `prune_old_memories` data from `delete_result.deleted_ids` | REQ-001..REQ-005 / AC-1..AC-5 | `maintenance.py:242-298` (no transaction, `extra_data` at `:292-297`), `:163`, `:79`, `:400` (checked Step 2, post-pull) | tests/db/test_db_maintenance.py | Verified |
| scripts/db/store_protocols.py | Modify | `MemoryDeleteResult` gains `deleted_ids: tuple[str, ...] = ()` (default keeps all existing constructions valid) | REQ-005 / AC-5 | `store_protocols.py:145-149` frozen dataclass with single field `deleted` (checked Step 2) | tests/db/test_db_maintenance.py | Verified |
| scripts/db/store_impl.py | Modify | `delete_memories_before` returns `deleted_ids=tuple(deleted_ids)` from the RETURNING statement (`:196-205`) | REQ-005 / AC-5 | `store_impl.py:196-205`: `deleted_ids` already collected in the delete transaction but discarded into a count-only result (checked Step 2) | tests/db/test_db_maintenance.py | Verified |
| tests/db/test_db_maintenance.py | Modify | Add rollback-atomicity, DatabaseError, config-propagation, helper-re-raise, and pruned-ids-source tests | REQ-006 / AC-1..AC-5 | `:941-1010` mode tests are all `OperationalError`-based mock tests; no rollback/`in_transaction` assertion exists (grep this cycle) | tests/db/test_db_maintenance.py | Verified |
| tests/agent/commands/test_memory_data_ops.py | Verify, edit only if needed | Confirm the prune-event tests (`:380-420`) do not depend on `maintenance` calling `collect_prunable_ids`; adjust patch targets only if they do | REQ-005 / AC-5 | They patch `SQLiteMemoryDeleteStore.collect_prunable_ids` (`:386-387`, `:418-419`), which remains used by `memory_prune` itself (`memory_data_ops.py:371-373`) (checked Step 2) | tests/agent/commands/test_memory_data_ops.py | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/helper.py | `begin_immediate`/`_begin_transaction` (`:242-261`) is the reuse point — rolls back on any normal exception and re-raises; **no edit required** | scripts/db/maintenance.py / REQ-001 |
| scripts/db/store_impl.py `:177-214` | `delete_memories_before` already opens its own `begin_immediate` — an outer wrap would nest `BEGIN` and fail; this is why REQ-005 derives ids instead of wrapping | scripts/db/maintenance.py / REQ-005 |
| scripts/agent/commands/memory_data_ops.py `:360-403` | Consumer of `data["pruned_ids"]` and independent caller of `collect_prunable_ids` — its contract must stay intact | scripts/db/maintenance.py / REQ-005 |
| plans/20261115-041859_dbreview004_integrity-probe-side-effects.md | Lands first in `tests/db/test_db_maintenance.py` (rotation invariance tests); 006 re-reads its landed test sections before appending | tests/db/test_db_maintenance.py / REQ-006 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-006`): Forcing the count rule to fail after a successful age delete leaves the sessions table unchanged, the helper connection not `in_transaction`, and `success=False` with committed-deletion counts of zero and `kept_active_session=None`.
- AC-2 (`REQ-002`, `REQ-006`): `vacuum_db` with a `sqlite3.DatabaseError` raises in STRICT and returns `success=False, action="vacuum_failed"` in BEST_EFFORT.
- AC-3 (`REQ-003`, `REQ-006`): Config-load failure raises in both modes for `purge_old_sessions` and `purge_corrupt_archives`, and every mode-taking entry point's docstring states it.
- AC-4 (`REQ-004`, `REQ-006`): `_handle_maintenance_error` called outside any `except` block re-raises the passed exception object in STRICT mode.
- AC-5 (`REQ-005`, `REQ-006`): `data["pruned_ids"]` equals exactly the ids deleted by the delete transaction (asserted against post-run table state), and `maintenance.prune_old_memories` does not call `collect_prunable_ids`.

## Tests
- `REQ-001` (AC-1): real-DB test (pattern of the existing real purge tests `:140-300`): seed 5 sessions all age-expired; patch `db.maintenance._delete_sessions_beyond_limit` to raise `sqlite3.OperationalError`; BEST_EFFORT → `success is False`, sessions row count unchanged, `helper._require_conn().in_transaction is False`, `data == {"age_deleted": 0, "count_deleted": 0, "kept_active_session": None}`.
- `REQ-002` (AC-2): `mock_db.vacuum.side_effect = sqlite3.DatabaseError("database disk image is malformed")` → BEST_EFFORT `success=False`/`vacuum_failed`; STRICT raises.
- `REQ-003` (AC-3): monkeypatch `db.maintenance.ConfigLoader.load` to raise `OSError` → `purge_old_sessions(..., mode=BEST_EFFORT)` raises; patch `db.maintenance.build_db_config` to raise `ValueError` → `purge_corrupt_archives(mode=BEST_EFFORT)` raises (characterization).
- `REQ-004` (AC-4): call `_handle_maintenance_error(ValueError("x"), "op", STRICT)` outside any `except` → raises the same `ValueError` (no `RuntimeError: No active exception`).
- `REQ-005` (AC-5): real-DB seed of pinned + unpinned memories; run `prune_old_memories`; assert `sorted(data["pruned_ids"])` equals the ids removed from the `memories` table (verified against post-run table state) and `data["deleted"] == len(data["pruned_ids"])`; with `collect_prunable_ids` patched via `patch.object(..., autospec=True)`, assert it is NOT called by `prune_old_memories`.
- Regression watch (no assertion changes expected): `test_prune_best_effort_returns_failure_on_error` (`:992-1004`) — the mocked `fetchall`/`execute` flow still reaches the store's internal fast-path SELECT + failing DELETE → same result; `test_prune_returns_ids_in_result_data` (`:416`) — data key unchanged; `test_purge_best_effort_returns_partial_result_on_error` (`:963-980`) — no data-count assertions exist, assertions stay green (rename to `..._returns_failure_result_on_error` allowed as test-only cleanup); `tests/agent/commands/test_memory_data_ops.py:380-420` — re-run and adjust patch targets only if they depended on maintenance's removed `collect_prunable_ids` call.

## Documentation Impact
- `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`: the mode bullets (`:29-30`) claim BEST_EFFORT catches "Exceptions" — correct this stale claim by stating config-load failures propagate in both modes; state that `purge_old_sessions` is one transaction (failure means no deletions) and that `prune_old_memories` reports the ids its delete transaction removed. The Issue permits this: the doc is the place where the per-mode config-error behavior is documented.

## Baseline Consistency (Step 5)
| Dimension | Baseline Value | Source (exact command) | Recorded |
|---|---|---|---|
| radon CC targets | `maintenance.py` top `_delete_sessions_beyond_limit` B(7), `purge_old_sessions` B(6) | `uv run radon cc scripts/db/maintenance.py scripts/db/store_impl.py scripts/db/store_protocols.py -s` (run this cycle) | 2026-11-15 |
| vulture targets | No `scripts/db` findings | `uv run vulture scripts/db --min-confidence 80` (run this cycle) | 2026-11-15 |
| bandit targets | 45 low / 0 medium / 0 high | `uv run bandit -r scripts/ -c pyproject.toml` (run this cycle, recorded under Plan 005; tree unchanged) | 2026-11-15 |
| coverage targets | project total 95%; tree clean at recording | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (run this cycle, recorded under Plan 005; tree unchanged) | 2026-11-15 |
| operational check | no process holds `/opt/llm/db/rag.sqlite` or `/opt/llm/db/session.sqlite` (`fuser` empty, exit 1); dev-host only | `fuser /opt/llm/db/rag.sqlite /opt/llm/db/session.sqlite` (recorded under Plan 002 Step 3; re-run before implementation) | 2026-11-15 |

## Assumptions
- `MagicMock(spec=SQLiteHelper)` tests accept `db.begin_immediate()` as a no-op context manager because the method exists on the real class (checked Step 2 against `helper.py:261`); mock-based mode tests stay valid after the wrap.
- Python sqlite3's implicit-transaction behavior today is what the Issue reproduced (partial delete visible on the connection until commit); the wrap makes commit/rollback ownership explicit instead of incidental.
- Adding a defaulted field to the frozen `MemoryDeleteResult` breaks no existing construction (`store_impl.py:186,205`, `scripts/db/__init__.py` re-export only; grep found no other constructions this cycle).
- `store_protocols.py` `MemoryDeleteStore` protocol method signature stays unchanged (return type is the same class, extended).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `tests/agent/commands/test_memory_data_ops.py:380-420` assertions depend on `maintenance.prune_old_memories` calling `collect_prunable_ids` (they patch the store method) | Their dependence not provable without running them against the modified maintenance | Phase 2 runs that test file; adjust patch targets only if a failure appears | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/maintenance.py | Modify | Medium (called by agent/rag maintenance services and agent commands) | 2 | High (single author, >70%) | not applicable (rsynced) |
| scripts/db/store_impl.py | Modify | Low-medium (`SQLiteMemoryDeleteStore` used by maintenance and agent memory commands) | 2 | High (single author, >70%) | not applicable (rsynced) |
| scripts/db/store_protocols.py | Modify | Low (defaulted field addition) | 1 | High (single author, >70%) | not applicable (rsynced) |
| tests/db/test_db_maintenance.py | Modify | Low (test-only) | 5 | High (single author, >70%) | not applicable (rsynced) |
| tests/agent/commands/test_memory_data_ops.py | Verify (conditional edit) | Low (test-only) | — | High (single author, >70%) | not applicable (rsynced) |

## Cross-Plan Target Overlap Scan

- Run with all plans frozen so far (`tools/check_plan_target_overlaps.py`, 2026-11-15, after this Plan freezes): finding — `tests/db/test_db_maintenance.py` shared with Plans 002 (read-only regression check row, no edit) and 004 (rotation-invariance test additions). Judgment: **sequencing** — fixed batch order 004 → 006; 004 adds rotation/archive probe tests, 006 adds purge/vacuum/prune mode-and-transaction tests; disjoint test classes, no shared fixtures modified. Plan 006 Phase 2 re-reads 004's landed sections before appending. Plans 007 (frozen 2026-11-15: guards at the top of the same purge helpers and the cutoff-SQL rewrite inside them — 007 Phase 1 re-reads 006's landed shapes; 007 Phase 3 re-runs 006's rollback tests) and 008 will share `scripts/db/maintenance.py`, `scripts/db/store_impl.py` and this test file; fixed order 006 → 007 → 008, recorded here and in those plans when they freeze.
- Update after Plan 008 froze (same tool, 2026-11-15): `scripts/db/maintenance.py` now 3 plans (006+007+008), `tests/db/test_db_maintenance.py` now 4 plans (004+006+007+008), `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` now 2 plans (006+008). Judgment: **disjoint regions, sequencing** — 008 adds a new config class + `purge_archive_artifacts()` entry point and appends a new test class and a new docs paragraph; it edits no function 006 landed. Order 004 → 006 → 007 → 008; 008's mode contract reuses 006's landed semantics. No contradiction.

## Design
- **Reuse, do not reimplement, transaction control**: `helper._begin_transaction` (`:242-258`) already rolls back on any normal exception and re-raises; `purge_old_sessions` gets `with db.begin_immediate():` around both delete calls and drops its manual `db.commit()`. Rejected alternative: adding rollback inside `_handle_maintenance_error` — the helper would need connection access and would still leave the first-delete ownership problem; the Issue's Required Change names `begin_immediate`.
- **No outer transaction around `prune_old_memories`**: `delete_memories_before` already opens its own `BEGIN IMMEDIATE` (`store_impl.py:191`); an outer wrap would raise `OperationalError: cannot start a transaction within a transaction`. Identity-consistent reporting is instead achieved by returning the `RETURNING` ids (REQ-005). Rejected alternative: removing the store's inner transaction — it is what makes the cross-table delete atomic today.
- **Honest failure data**: on failure the transaction has rolled back, so failure `extra_data` reports committed deletions: zeros and `kept_active_session=None` (fixes the "requested id, not the computed one" claim). Success-path `data` is unchanged (computed `kept`, `:271-273`).
- **Config errors: documented propagation (maintainer decision)**: `from_config` calls stay outside the `try`; `build_db_config` stays inside `purge_corrupt_archives`'s `try` whose handler catches only `OSError` — `ValueError` propagates in both modes. Docstrings of `vacuum_db`, `purge_old_sessions`, `purge_corrupt_archives`, `prune_old_memories` state it explicitly (Issue AC-2 second branch). Rejected alternative: absorbing config errors — hides persistent misconfiguration behind per-run logs (maintainer choice: propagate).
- **`raise exc` in the error helper**: makes `_handle_maintenance_error` context-independent (`:79`); traceback still chains the original frames via `exc.__traceback__`.
- **`MemoryDeleteResult` extension**: `deleted: int` stays (all current consumers read it); `deleted_ids` defaults to `()` so the fast path (`store_impl.py:186`) and any external constructor keep working. `maintenance` converts to `list[str]` when building `data["pruned_ids"]` to keep the consumer shape (`memory_data_ops.py:403`, `test_db_maintenance.py:416`) identical.
- **Architecture check** (Step 3): no new import edges; `maintenance.py` already imports `db.store_impl` and `db.helper`; `lint-imports` contracts unchanged (6 kept, recorded this cycle).
- **Persisted schema check**: N/A — no schema or stored-format changes.

## Implementation steps
1. **Phase 1: Purge transaction and error-handler fixes** (REQ-001..REQ-004; `scripts/db/maintenance.py`)
   - [ ] Wrap both delete rules in `with db.begin_immediate():`, drop the manual `db.commit()`, report zeroed committed-deletion data on failure (REQ-001; scripts/db/maintenance.py)
   - [ ] Widen `vacuum_db` handler to `(sqlite3.Error, RuntimeError)` (REQ-002; scripts/db/maintenance.py)
   - [ ] State config-error propagation in the four mode docstrings (REQ-003; scripts/db/maintenance.py)
   - [ ] Replace bare `raise` with `raise exc` in `_handle_maintenance_error` (REQ-004; scripts/db/maintenance.py)
2. **Phase 2: Delete-transaction ids as the single source** (REQ-005; `scripts/db/store_protocols.py`, `scripts/db/store_impl.py`, `scripts/db/maintenance.py`)
   - [ ] Add `deleted_ids: tuple[str, ...] = ()` to `MemoryDeleteResult` and populate it in `delete_memories_before` (REQ-005; scripts/db/store_protocols.py, scripts/db/store_impl.py)
   - [ ] `prune_old_memories` builds `data["pruned_ids"]` from `delete_result.deleted_ids` and drops the `collect_prunable_ids` call (REQ-005; scripts/db/maintenance.py)
3. **Phase 3: Tests, docs and validation** (REQ-006; `tests/db/test_db_maintenance.py`, `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`)
   - [ ] Add the Tests-section tests; run `uv run pytest tests/db tests/agent/commands -v` including the regression watch list and the UNK-01 check (REQ-006)
   - [ ] Update the mode/atomicity statements in `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` (Documentation Impact)
   - [ ] Run ruff, mypy (CI form), bandit `-ll`, `lint-imports`, `tools/check_docs_consistency.py --domain db`; diff-cover ≥ 90% on the branch diff
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md` after commit+push; deploying is the user's decision

### Release units
**Unit**: maintenance-error-semantics | **Phases**: 1, 2, 3 | **Reason**: the transaction wrap, widened handlers, and id-source change together define the corrected mode contract tested by the same suite run; splitting leaves a half-atomic purge.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/maintenance.py | Rollback-atomicity integration test on a real temp DB | `uv run pytest tests/db/test_db_maintenance.py -v` | AC-1 asserted incl. `in_transaction is False` |
| scripts/db/maintenance.py | Mode-matrix unit tests (vacuum DatabaseError, config propagation, helper re-raise) | `uv run pytest tests/db/test_db_maintenance.py -v` | AC-2..AC-4 asserted |
| scripts/db/store_impl.py + maintenance.py | Id-source test against post-run table state; collect-not-called spy | `uv run pytest tests/db/test_db_maintenance.py -v` | AC-5 asserted |
| tests/agent/commands/test_memory_data_ops.py | Regression run for UNK-01 | `uv run pytest tests/agent/commands -v` | Green as-is, or patch targets adjusted |
| scripts/ (regression) | Full suite (maintenance services consumers) | `uv run pytest tests/ -n auto` | No regressions |
| scripts/db/maintenance.py (radon) | Complexity guard | `uv run radon cc scripts/db/maintenance.py -s` | Top stays ≤ B(7); `begin_immediate` wrap adds no branch |
| branch diff | Coverage gate | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (`--fail-under=90`) | Baseline recorded this cycle (95%); branch diff ≥ 90% |

## Risks
- **Risk**: wrapping the purge changes failure-path `data` (attempted counts → zeros), which a caller could misread → **Mitigation**: zero values are the truthful committed-deletion count after rollback; docstrings and the docs update state it; existing tests assert no counts on failure (checked this cycle).
- **Risk**: mock-based purge tests (`:963-990`) interact with `begin_immediate` on `MagicMock` differently than a real connection → **Mitigation**: `spec=SQLiteHelper` exposes the method as a usable no-op context manager; regression run confirms; AC-1 uses a real DB instead of mocks.
- **Risk**: `deleted_ids` default `()` silently hides a store that does not populate it (third-party `MemoryDeleteStore` implementations) → **Mitigation**: the protocol docstring states the ids are the authoritative report; only in-repo implementation exists (grep this cycle).
- **Risk**: overlapping edits with Plans 004/007/008 in `tests/db/test_db_maintenance.py` and `maintenance.py`/`store_impl.py` → **Mitigation**: fixed batch order 004 → 006 → 007 → 008 recorded in the Overlap Scan; each later plan re-reads landed code before editing.
- **Risk**: `sqlite3.Error` widening in `vacuum_db` absorbs errors that should crash STRICT → **Mitigation**: STRICT path unchanged (`_handle_maintenance_error` re-raises); only BEST_EFFORT handling widens, which is exactly the Issue's Required Change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Purge transaction and error-handler fixes (scripts/db/maintenance.py) | Pending | — | — | |
| 2 | Delete-transaction ids as the single source (store_protocols.py, store_impl.py, maintenance.py) | Pending | — | — | |
| 3 | Tests, docs and validation | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261114-092854_dbreview006_maintenance-error-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-050112
- **Related target files**: scripts/db/maintenance.py, scripts/db/store_protocols.py, scripts/db/store_impl.py, tests/db/test_db_maintenance.py, tests/agent/commands/test_memory_data_ops.py

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem bullet 1; Required Changes bullet 1 | scripts/db/maintenance.py | Phase 1 | AC-1 | Real-DB rollback-atomicity test | Verified by test (Issue reproduction; re-verified Step 2 at `:242-298`) |
| REQ-002 | Problem bullet 2; Required Changes bullet 2 | scripts/db/maintenance.py | Phase 1 | AC-2 | DatabaseError mode tests | Verified by test (Issue reproduction; `:163` checked Step 2) |
| REQ-003 | Problem bullet 3; Required Changes bullet 2 second half; Unresolved Question answered 2026-11-15 (propagate) | scripts/db/maintenance.py | Phase 1 | AC-3 | Config-propagation characterization tests | Explicit in code (`:259-260`, `:357-358`, `:383`) |
| REQ-004 | Problem bullet 4; Required Changes bullet 3 | scripts/db/maintenance.py | Phase 1 | AC-4 | Direct-call re-raise test | Explicit in code (`:79`) |
| REQ-005 | Problem bullet 5; Required Changes bullet 4 | scripts/db/store_protocols.py, scripts/db/store_impl.py, scripts/db/maintenance.py | Phase 2 | AC-5 | Id-source test + not-called spy | Explicit in code (`store_impl.py:196-205`, `maintenance.py:400`) |
| REQ-006 | Testing Expectations | tests/db/test_db_maintenance.py | Phase 3 | AC-1..AC-5 | New tests | Verified by test (gap confirmed this cycle: mode tests are OperationalError-only) |
