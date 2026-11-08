## Goal
Retarget `test_find_stale_running_attempts_exposes_lease_keys` — the only caller of the facade `StateStore.find_stale_running_attempts` in `test_state_store.py` — onto the production recovery path `recover_stale_attempts`, keeping the lease-expiry classification it proves (`REQ-003`).

## Scope
**Release unit**: wfaudit009-full

- Covers Plan `plans/20261108-084010_wfaudit009_test-only-state-helpers.md` row 5 only: `tests/agent/workflow/test_state_store.py`.
- This is a Phase 1 (plan step 1) document: the edit lands while the facade still exists; the suite must be green with helpers present before document 02 deletes it (equivalence gate).

## Assumptions
- Call site verified at HEAD `ad48bfa28`: the test lives in class `TestRecoverStaleAttemptsOptimisticLocking` (L117), spans L256-269, and calls `store.find_stale_running_attempts(store.get_connection())` at L267. The module helpers `_iso` (L33), `_seed_attempt` (L71) and `_attempt_row` (L105) already exist and are used unchanged.
- Per plan Notes, `wfaudit001` and `wfaudit007` land before this plan; `wfaudit007` extends `RecoveryReport` (its procedure document `implementations/20261108-135741_01_scripts_agent_workflow_state_store.py.md`), so this test asserts only the stable surface: `recover_stale_attempts` return value, the recovered row's columns, and `last_recovery_report.recovered`. `wfaudit001` additionally rewrites the processed_events semantics comment — unrelated to this file.
- The file's module docstring (L2-8) already frames every scenario as seeding real rows for the production `recover_stale_attempts` path; the retarget continues that framing.

## Design decisions
- Assert behavior, not the finder's dicts: the deleted method returned `[dict]` rows with `attempt_id`/`owner_id`/`lease_expires_at` keys; the production entry point exposes the same classification outcome as a recovery decision — the lease-expired row is marked `failed` with reason text `lease expired` in `error_msg`, while `last_recovery_report.recovered == 1` (plan `REQ-003`: recovery coverage unchanged).
- Rename the test (new name `test_recover_stale_lease_expired_row` (new)) so the file contains zero occurrences of the deleted helper name, keeping the `REQ-001` grep clean on the test side before deletion lands.

## Alternatives considered
- Deleting the test outright (the same lease-key classification is exercised by the sibling stale tests in `test_workflow_state_store.py`, retargeted by document 04): rejected — plan AC `REQ-003` requires recovery coverage to survive on the production path, and this is the test that pins lease-based (not age-based) classification in this file; deletion would shrink coverage.

## Implementation
### Target file
`tests/agent/workflow/test_state_store.py`

### Procedure
Rename the test and swap its final assertion block; the seed block is unchanged.

### Method
1. Rename `test_find_stale_running_attempts_exposes_lease_keys` (L256) to `test_recover_stale_lease_expired_row` (new); keep the `(self, store, workflow_db: Path)` signature.
2. Keep the seed identical: `lease = _iso(10)` using the existing `_iso` helper, then `_seed_attempt(workflow_db, "att-1", started_at=_iso(7200), owner_id="host-a", lease_expires_at=lease)` — a lease-stamped row older than the legacy age but with a lease that expired 10 seconds ago.
3. Replace the `stale = store.find_stale_running_attempts(store.get_connection())` call and the dict-key assertions with:
   - `result = store.recover_stale_attempts(store.get_connection())` then `assert result == 1`.
   - `row = _attempt_row(workflow_db, "att-1")`; `assert row["status"] == "failed"`; `assert "lease expired" in row["error_msg"]` — the reason string proves the lease-expiry branch classified the row (the age fallback would say `legacy attempt older than ...` instead).
   - `assert store.last_recovery_report.recovered == 1`.

### Details
- No import changes: the file imports `StateStore` (L20) and the fixtures already exist; `Path` is already imported for the signature.
- The single seed is the only running row in the fixture DB, so `recovered == 1` is exact and the test stays independent of the `wfaudit007` report-shape extension (`recovered` is a field both before and after).

## Compatibility considerations
- Behavior-preserving for coverage: the same seeded row and the same classification decision are exercised, only through the production entry point.
- `tests/agent/workflow/test_workflow_state_store.py` (document 04) handles the other facade caller (L528); no cross-file helpers here.

## Security considerations
- None.

## Rollback considerations
- Revert this document alone: the renamed test returns to the HEAD version, which still passes until document 02 deletes the facade.

## Validation plan
- Phase 1 equivalence gate: `uv run pytest tests/agent/workflow/test_state_store.py -q` green with the facade still present.
- Mutation guard (plan Risks): flip the lease-vs-age branch in the classification path and confirm the `error_msg` reason assertion fails.
- After deletion (plan step 2): `uv run pytest tests/agent/workflow/ -q` green; full `uv run pytest tests/ -q` per `rules/toolchain.md`.

## Completion criteria
- The file has zero references to the deleted facade name; the lease-expiry classification remains pinned through `recover_stale_attempts`; the suite is green.

## Out of Scope
- Deleting `StateStore.find_stale_running_attempts` itself (document 02).
- `RecoveryReport` shape changes owned by `wfaudit001`/`wfaudit007`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-071047 | 20261109-071047 | the test edit is the implementation; lands before document 02 |
| 2 | Add or update tests per Validation plan | Completed | 20261109-071047 | 20261109-071047 | merged into step 1: rename plus recovery-behavior assertions |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-071047 | 20261109-071047 | Phase 1 equivalence gate runs here with helpers still present |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-071047 | 20261109-071047 | docs grep verified zero matches; verification-only N/A: no docs/00_index.md task-scope mapping; grep zero matches for deleted helper names |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261107-203222_wfaudit009_test-only-state-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084010_wfaudit009_test-only-state-helpers.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-170505
- **Related target files**: `tests/agent/workflow/test_state_store.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-170505 -->