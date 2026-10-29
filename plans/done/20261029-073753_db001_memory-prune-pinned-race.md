## Goal
- Make `SQLiteMemoryDeleteStore.delete_memories_before()` evaluate its pinned-exclusion and age guards atomically with the deletion, so a concurrent writer can no longer delete (or orphan) a memory that was re-pinned or refreshed after the prune selected it.

## Priority
Medium

## Scope
- **In-Scope**: re-evaluating the `pinned = 0` / age guards inside the `begin_immediate()` write lock in `delete_memories_before()`; keying the `memories_fts` / `memories_vec` / `memory_links` cleanup on the actually-deleted ids; real-SQLite regression tests for the selection-to-deletion window.
- **Out-of-Scope**: retention policy values (`RetentionConfig`, `sqlite_retention_*` keys); the redundant double-selection in `prune_old_memories()` (`collect_prunable_ids()` followed by the re-select inside `delete_memories_before()`); other stores or delete paths (`SQLiteVectorStore`, `SQLiteDocumentStore`).
- **Dependencies**: N/A: none (verified in Step 2 — no open issue covers this gap; `mem001` is archived in `issues/done/`).

## Background
`prune_old_memories()` in `scripts/db/maintenance.py` drives deletion through `SQLiteMemoryDeleteStore`: it calls `collect_prunable_ids()` and then `delete_memories_before()`. The static `AND pinned = 0` predicate in the selection `SELECT` and the four-table `begin_immediate()` atomicity were implemented by `mem001` (`issues/done/20261014-155503_mem001_implement-memory-command-spec.md`; its scope verified here against current source, not the archived file). Step 2 verification confirmed the current code shape: `delete_memories_before()` runs the selection `SELECT` on the helper connection outside any transaction, then opens `begin_immediate()` and `DELETE`s with `WHERE memory_id IN (...)` alone.

## Problem
The selection `SELECT` holds no write lock. Between it and `begin_immediate()` acquiring the lock, a concurrent transaction can `UPDATE memories SET pinned = 1` (or refresh `updated_at`) for a selected `memory_id`. The `DELETE` matches only on `memory_id IN (...)`, so it removes the row regardless of its current `pinned`/`updated_at` state, violating the "prune never deletes pinned memories" guarantee. Two additional findings from adversarial verification:

- The Issue's preferred fix (move the `SELECT` inside `begin_immediate()`) serializes a concurrent re-pin *behind* the prune transaction — a pin arriving after `BEGIN IMMEDIATE` can never commit before the `DELETE` — which contradicts the Issue's own Acceptance Criteria 1/2 ("a memory re-pinned after it was selected ... is not deleted") and makes them not deterministically testable. This Plan therefore adopts the Issue's alternative approach (guards re-evaluated at `DELETE` time); see Design.
- The Issue's alternative, as stated, is incomplete: if only the `memories` `DELETE` re-checks the guards, the auxiliary-table cleanup loops over the stale selected `mids` and would delete the `memories_fts` / `memories_vec` / `memory_links` rows of a re-pinned memory that survives in `memories`, orphaning retained data. REQ-002 closes this gap.

## Reason for Change
The invariant is a data-safety guarantee, not a best-effort optimization, yet it is not atomically enforced. The current code gives false assurance: the static `pinned = 0` predicate reads as a complete guard while a concurrent writer can defeat it, and no existing test exercises the selection-to-delete window (`TestMemoryDeleteStoreRealSqlite` only covers the static semantics; confirmed in Step 2).

## Implementation Intent
Evaluate the retention guards (`pinned = 0` and the `updated_at` age predicate) under the write lock at `DELETE` time, and derive the actually-deleted ids from the `memories` `DELETE` itself so the auxiliary-table cleanup only touches rows that were really removed. Preserve cross-table atomicity, retention semantics, parameterized queries, and the public contract.

## Requirements
- `REQ-001`: `delete_memories_before()` re-applies the `pinned = 0` and `updated_at` age predicates inside the `DELETE` executed under `begin_immediate()`, so a row re-pinned or refreshed by a committed concurrent write between selection and `DELETE` is retained.
- `REQ-002`: `memories_fts`, `memories_vec`, and `memory_links` cleanup is keyed only on the ids actually deleted from `memories` (e.g. `DELETE ... RETURNING memory_id`), never on the pre-lock selected ids.
- `REQ-003`: the deletion across `memories`, `memories_fts`, `memories_vec`, and `memory_links` remains a single `begin_immediate()` transaction.
- `REQ-004`: the public contract (`delete_memories_before()` signature, `MemoryDeleteResult`, `MaintenanceResult` shape from `prune_old_memories()`), retention window semantics, and `?`-placeholder parameterization are unchanged.
- `REQ-005`: real-SQLite regression coverage for a re-pin and an `updated_at` refresh landing between selection and deletion.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified`; `issue-to-plan` Step 8b Implementation
Target Files Validation passed — see `rules/workflow-lifecycle.md` Implementation Target
Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/store_impl.py | Modify | Re-evaluate the `pinned = 0` / age guards in the `DELETE` inside `begin_immediate()`, and key the auxiliary-table cleanup on the actually-deleted ids | REQ-001, REQ-002, REQ-003, REQ-004 | `SQLiteMemoryDeleteStore.delete_memories_before()` selects via `self._db.fetchall` (no lock) then `DELETE`s `WHERE memory_id IN (...)` inside `with self._db.begin_immediate():` (checked in Step 2) | `TestMemoryDeleteStoreRealSqlite`, `TestSQLiteMemoryDeleteStore` in tests/db/test_db_store_impl.py | Verified |
| tests/db/test_db_store_impl.py | Modify | Add mid-window re-pin / `updated_at`-refresh regression tests; adapt the mock-based delete-store tests to the new `DELETE` statement shape | REQ-001, REQ-002, REQ-005 | `TestMemoryDeleteStoreRealSqlite` and `TestSQLiteMemoryDeleteStore` exist; no test exercises the selection-to-delete gap (checked in Step 2) | `TestMemoryDeleteStoreRealSqlite`, `TestSQLiteMemoryDeleteStore` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/maintenance.py | `prune_old_memories()` is the caller: confirms the `collect_prunable_ids()` + `delete_memories_before()` flow and the unchanged `MaintenanceResult` shape (reference only per the Issue) | REQ-004 |
| scripts/db/helper.py | `SQLiteHelper._begin_transaction()` / `begin_immediate()` / `fetchall()` semantics: same connection, explicit `BEGIN IMMEDIATE` serializes concurrent writers | REQ-001, REQ-003 |
| scripts/db/store_protocols.py | `MemoryDeleteStore` protocol — the public contract that MUST NOT change | REQ-004 |
| docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md | documents the behavioral guarantee that `/memory prune` "never [deletes] pinned ones, ... all-or-nothing"; read to confirm no documentation change is required after the fix | REQ-004 |

## Acceptance Criteria
- `AC-1` (REQ-001): a memory re-pinned after it was selected by the prune query and before the `DELETE` executes is not deleted.
- `AC-2` (REQ-001): a memory whose `updated_at` is refreshed to be recent after selection and before the `DELETE` executes is not deleted.
- `AC-3` (REQ-002): a retained (re-pinned/refreshed) memory keeps its `memories_fts` / `memories_vec` / `memory_links` rows; a deleted memory has all its auxiliary rows removed.
- `AC-4` (REQ-003): the deletion remains atomic across `memories`, `memories_fts`, `memories_vec`, `memory_links` in one transaction (rollback on failure).
- `AC-5` (REQ-004): existing prune behavior (old unpinned removed, pinned/recent kept, cross-table cleanup) and the public contract are unchanged; `uv run pytest tests/db` passes; ruff / mypy / bandit gates stay clean.

## Tests
- `T1` (REQ-001, REQ-002, REQ-005): real-SQLite regression test in `TestMemoryDeleteStoreRealSqlite` — re-pin a selected memory between selection and `DELETE` execution (via the test's DB wrapper) and assert it and its auxiliary rows are retained.
- `T2` (REQ-001, REQ-005): same shape as `T1`, refreshing `updated_at` to a recent timestamp; assert retention.
- `T3` (REQ-004): adapt `TestSQLiteMemoryDeleteStore` mock tests to the new `DELETE` shape (deleted-id retrieval via cursor) while preserving their existing SQL-shape assertions.
- `T4` (REQ-004): `uv run pytest tests/db`; `uv run ruff check scripts/db`; `uv run mypy --no-namespace-packages scripts/db`; `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Documentation Impact
N/A: no `docs/*.md` update required. The behavioral guarantee already stated in the slash-commands memory doc (see Reference Files — located via `docs/00_index.md`'s Agent/DB task mapping) becomes strictly true after the fix, so the Issue's conditional Known Issues / Needs Confirmation note does not apply (it is only needed if the concurrency caveat remained).

## Assumptions
- Chosen retention semantics: a concurrent re-pin/refresh that commits before the prune's `DELETE` acquires/evaluates under the write lock wins retention; a writer arriving after the lock is held is serialized out (blocked by `busy_timeout`) and the row is deleted — consistent with the Issue's AC-1/AC-2 and with SQLite writer serialization.
- The repo's SQLite library supports `DELETE ... RETURNING` (sqlite 3.53.4 confirmed via `uv run python -c "import sqlite3; print(sqlite3.sqlite_version)"`), so actually-deleted ids can be obtained in the same locked statement. Falsifiable by `T1`/`T2`.
- The mock-based `TestSQLiteMemoryDeleteStore` tests are call-shape coupled and require adjustment in the same change (`T3`).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether prune ever runs concurrently with active `/memory pin` / `unpin` in production (Issue Unresolved Question 1; affects practical impact sizing, not the fix itself) | No production observation data in the repository | Check production usage/logs during the implementation phase; the fix is correct regardless of the answer | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/store_impl.py | Modify | Low — two importing callers (`scripts/db/maintenance.py`, `scripts/agent/commands/memory_data_ops.py`); neither signature nor result type changes (checked in Step 3) | N/A | N/A | not applicable (rsynced) |
| tests/db/test_db_store_impl.py | Modify | Low — test file, no production importers (checked in Step 3) | N/A | N/A | not applicable (rsynced) |

## Design
Design decision (resolves the Issue's Unresolved Question 2): re-apply the guards at `DELETE` time rather than moving the `SELECT` inside `begin_immediate()`. Grounds, from Step 2 verification:

1. Implementability of both variants is confirmed: `SQLiteHelper.fetchall` / `execute` run on the same connection as `_begin_transaction()`, so a statement inside `begin_immediate()` runs under the held write lock (`scripts/db/helper.py`).
2. Moving the `SELECT` under the lock closes the window only by serializing concurrent re-pins behind the prune transaction — a pin arriving after `BEGIN IMMEDIATE` cannot commit before the `DELETE`. That contradicts the Issue's AC-1/AC-2 retention semantics and makes them non-deterministically testable.
3. Re-applying `pinned = 0` and the same age predicate (`updated_at < datetime('now', ?)` with the same `-N days` parameter) in the `DELETE` under the lock satisfies AC-1/AC-2 literally and deterministically.
4. REQ-002 is mandatory with this design: the auxiliary cleanup MUST be keyed on the ids actually deleted from `memories` (e.g. `DELETE ... RETURNING memory_id`), otherwise retained re-pinned rows lose their `memories_fts` / `memories_vec` / `memory_links` rows.

No new module, no public/runtime interface change, no database schema change — Path A classification stands (2 modification targets).

## Implementation steps
1. **Phase 1: Core Logic Implementation**
   - [ ] Modify `delete_memories_before()` so the `DELETE` re-applies the `pinned = 0` and age predicates under `begin_immediate()`, and the `memories_fts` / `memories_vec` / `memory_links` cleanup is keyed on the actually-deleted ids (REQ-001, REQ-002, REQ-003; File Path: scripts/db/store_impl.py)
2. **Phase 2: Test Update**
   - [ ] Add `T1` / `T2` real-SQLite regression tests to `TestMemoryDeleteStoreRealSqlite` and adapt `TestSQLiteMemoryDeleteStore` mock tests (`T3`) (REQ-005, REQ-004; File Path: tests/db/test_db_store_impl.py)
3. **Phase 3: Verification & Deployment Hand-off**
   - [ ] Run the Validation plan gates (`uv run pytest tests/db`, ruff, mypy, bandit `-ll`, diff-cover >= 90% on changed lines) (REQ-004; File Paths: scripts/db/store_impl.py, tests/db/test_db_store_impl.py)
   - [ ] Deployment validation/scripts check: commit and push the change, then hand off to `skills/deploy/SKILL.md`; deploying is the user's decision (approval gate) (REQ-004; File Paths: scripts/db/store_impl.py, tests/db/test_db_store_impl.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/store_impl.py | Integration (real SQLite, `T1`/`T2`) | `uv run pytest tests/db/test_db_store_impl.py -v` | New regression tests pass; re-pinned/refreshed memories and their auxiliary rows retained |
| scripts/db/store_impl.py | Static | `uv run ruff check scripts/db`; `uv run mypy --no-namespace-packages scripts/db`; `uv run bandit -r scripts/ -c pyproject.toml -ll` | No errors; no medium/high bandit findings |
| tests/db/test_db_store_impl.py | Regression | `uv run pytest tests/db` | Full db suite green |
| diff scope | Coverage | `uv run coverage run -m pytest tests/`; `uv run coverage xml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | >= 90% coverage on changed lines (baseline recorded in Step 5: clean tree vs master, no Python diff — current number is "no diff lines"; the Plan MUST raise it to the `rules/toolchain.md` threshold) |
| whole change | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No import-layer violations |

## Risks
- **Risk**: the new `DELETE` shape (deleted-id retrieval) breaks the mock-coupled `TestSQLiteMemoryDeleteStore` tests → **Mitigation**: `T3` adapts them in the same change (Phase 2), preserving their SQL-shape assertions.
- **Risk**: re-deriving the age predicate incorrectly could widen or narrow the retention window → **Mitigation**: reuse the exact same `datetime('now', ?)` predicate and `-N days` parameter as the selection `SELECT`; `T1`/`T2` and the existing age-semantics tests pin the behavior.
- **Risk**: keying the auxiliary cleanup on the wrong ids could orphan auxiliary rows of a retained memory or leave auxiliary rows of a deleted memory → **Mitigation**: REQ-002 (derive ids from the `DELETE` itself) plus `T1` auxiliary-row retention assertions (`AC-3`).
- **Risk**: production concurrency is likely low (Issue Unresolved Question 1), so the fix is preventative and adds a re-check cost on every prune → **Mitigation**: minimal diff, same indexed predicate under an already-held write lock; no behavior change for the single-writer case (existing tests unchanged).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Modify `delete_memories_before()` guards + auxiliary-cleanup keying (scripts/db/store_impl.py) | Completed | 20261029-145050 | 20261029-145050 | REQ-001, REQ-002, REQ-003 |
| 2 | Add regression tests; adapt mock tests (tests/db/test_db_store_impl.py) | Completed | 20261029-145050 | 20261029-145050 | REQ-005, REQ-004 Deviation: tests/db/test_db_maintenance.py TestPruneOldMemories mock fixtures were coupled to the old statement shape and required adaptation for the full-suite gate; not in the frozen target table - recorded in the sibling procedure document |
| 3 | Run validation gates; commit/push; deploy hand-off | Pending | — | — | REQ-004; deploy is user-gated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-134342_01_scripts_db_store_impl.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261029-134342_02_tests_db_test_db_store_impl.py.md | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-011342_db001_memory-prune-pinned-race.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-073753
- **Related target files**: scripts/db/store_impl.py, tests/db/test_db_store_impl.py

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem / Required Changes / Acceptance Criteria 1-2; confirmed against `delete_memories_before()` (Step 2) | scripts/db/store_impl.py | Phase 1 | AC-1, AC-2 | T1, T2 | Explicit in issue |
| REQ-001 | Problem / Acceptance Criteria 1-2 | tests/db/test_db_store_impl.py | Phase 2 | AC-1, AC-2 | T1, T2 | Explicit in issue |
| REQ-002 | Adversarial-verification finding: auxiliary deletes loop over stale `mids` (Step 2) | scripts/db/store_impl.py | Phase 1 | AC-3 | T1 | Derived from confirmed evidence |
| REQ-002 | Adversarial-verification finding (Step 2) | tests/db/test_db_store_impl.py | Phase 2 | AC-3 | T1 | Derived from confirmed evidence |
| REQ-003 | Constraints ("Preserve cross-table atomicity") | scripts/db/store_impl.py | Phase 1 | AC-4 | `TestMemoryDeleteStoreRealSqlite` existing test, T4 | Explicit in issue |
| REQ-004 | Constraints / Out of Scope | scripts/db/store_impl.py | Phase 1 | AC-5 | T3, T4 | Explicit in issue |
| REQ-004 | Constraints / Out of Scope | tests/db/test_db_store_impl.py | Phase 2 | AC-5 | T3, T4 | Explicit in issue |
| REQ-005 | Testing Expectations / Required Changes | tests/db/test_db_store_impl.py | Phase 2 | AC-1, AC-2 | T1, T2 | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261029-134342 -->