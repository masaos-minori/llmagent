## Goal
- Leave one implementation of attempt creation and finishing per purpose: remove the dead `StateStore.start_attempt` and `StateStore.count_attempts`, make the live `StateStore.finish_attempt` delegate to `attempt_ops.finish_attempt`, and document why `begin_stage_if_new` keeps its own transaction-bound insert, with no change to the production write path.

## Priority
Low

## Scope
- **In-Scope**: deletion of two zero-caller `StateStore` methods; delegation of `StateStore.finish_attempt` to `attempt_ops`; a cross-reference comment at the insert in `begin_stage_if_new`; removal of imports left unused.
- **Out-of-Scope**: task-side CRUD; `processed_events` semantics and attempt fencing; schema changes to `attempts`; `recover_stale_attempts` (its `UPDATE attempts` is a recovery transition, see Problem); removing or changing `attempt_ops.start_attempt` / `count_attempts`, which tests use and which `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` REQ-003 rewrites.
- **Dependencies**: no blocking dependency. Sequencing note: the wfrecovery001 Plan (REQ-003, REQ-005) also removes the `StateStore` bypass `start_attempt` and makes `finish_attempt` conditional; this Plan lands the part of that change that is behavior-neutral, so wfrecovery001's later `finish_attempt` change is made in one place (`attempt_ops.py`). `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md` is the task-side precedent whose delegation pattern this Plan mirrors.

## Background
Adversarial review (2026-11-03) found attempt-row writes in three places: `attempt_ops`, `StateStore`, and the raw insert in `idempotency_ops.begin_stage_if_new`.

## Problem
Verified in Step 2 (`scripts/agent/workflow/`):
- `StateStore.start_attempt` inserts without `owner_id` / `lease_expires_at`, and `StateStore.count_attempts` is a raw `COUNT(*)`; `rg` finds no caller of either in `scripts/`, `tests/`, or `docs/`. `StateStore.finish_attempt` is called only by `workflow_engine.py` (five sites) and runs the same `UPDATE` and `commit()` as `attempt_ops.finish_attempt`.
- `attempt_ops.start_attempt` / `finish_attempt` / `count_attempts` are imported only by tests (`tests/agent/workflow/test_workflow_state_store.py`, `test_workflow_stage_persistence.py`, `test_workflow_engine.py`).
- The production creation path is `begin_stage_if_new`, whose `INSERT INTO attempts` must stay inside its `begin_immediate()` transaction together with the `processed_events` check and insert.

Corrections to the Issue:
- A fourth raw attempt statement exists: `StateStore.recover_stale_attempts` runs `UPDATE attempts SET status='failed' ...`. It is a stale-recovery transition, not the generic finish, so it stays; the Issue's acceptance wording "no public `StateStore` method performs raw attempt SQL" is therefore narrowed to exclude it.
- The Issue treats wfrecovery001 as open. Its Plan is in `plans/done/` and already requires removing the `start_attempt` bypass (REQ-003), but its `Execution Status` rows are all `Pending` and the code has none of its markers (no `scripts/agent/workflow/errors.py`, no `AttemptFencedError`), so that Plan is consumed but not implemented. This resolves the Issue's open question: wfrecovery001 intends to own the removal, and this Plan takes only the behavior-neutral subset.

## Reason for Change
Two unused public methods are traps (one writes lease-less rows that only the 3600-second legacy rule recovers), and the live finish path has a second copy that can drift from the module copy.

## Implementation Intent
Owner decision: `attempt_ops` owns attempt CRUD, mirroring how `state_store.py` already imports `create_task` and `get_task_by_id` from `task_ops`. Delete `StateStore.start_attempt` and `StateStore.count_attempts` (no callers; deletion is preferred over delegation for `start_attempt`). `StateStore.finish_attempt` keeps its signature and delegates to `attempt_ops.finish_attempt(self._db, ...)`, which issues the same SQL and commit. `begin_stage_if_new` is not changed in behavior: only a comment states why it does not call `attempt_ops.start_attempt` (atomicity with the ledger check) and points to `attempt_ops.start_attempt` as the non-transactional variant.

## Requirements
- `REQ-001`: `StateStore.start_attempt` and `StateStore.count_attempts` are removed.
- `REQ-002`: `StateStore.finish_attempt` delegates to `attempt_ops.finish_attempt` with unchanged signature, SQL, and commit.
- `REQ-003`: The `INSERT INTO attempts` in `begin_stage_if_new` stays in its single `begin_immediate()` transaction and carries a comment explaining why it does not call `attempt_ops.start_attempt`.
- `REQ-004`: Imports that become unused in `state_store.py` (`uuid`, `AttemptRecord`, and `_now` only if no other use remains) are removed.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Workflow store facade | Delete `start_attempt` and `count_attempts`; delegate `finish_attempt`; drop unused imports | REQ-001, REQ-002, REQ-004 / AC-1, AC-2, AC-4 | `start_attempt`, `finish_attempt`, `count_attempts` in the `# ── Attempt` section; `uuid` used only there, `AttemptRecord` only in `start_attempt`'s return, `_now` also used at the recovery code (checked in Step 2) | `tests/agent/workflow/test_workflow_engine.py` | Verified |
| `scripts/agent/workflow/idempotency_ops.py` | Stage idempotency | Add the explanatory comment at the `INSERT INTO attempts` | REQ-003 / AC-3 | `begin_stage_if_new` inserts inside `with db.begin_immediate()` (checked in Step 2) | `tests/agent/workflow/test_workflow_engine.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/attempt_ops.py` | Owner of attempt CRUD after the change; unchanged | REQ-002 |
| `scripts/agent/workflow/workflow_engine.py` | Only production caller of `StateStore.finish_attempt` | REQ-002 |
| `tests/agent/workflow/test_workflow_state_store.py` | Imports `attempt_ops` functions; must pass unchanged | REQ-001 |
| `tests/agent/workflow/test_workflow_stage_persistence.py` | Same | REQ-001 |
| `tests/agent/workflow/test_workflow_engine.py` | Real-DB lock for the finish path and the begin path | REQ-002, REQ-003 |
| `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` | REQ-003 and REQ-005 of that Plan overlap this Plan's subset | Scope |

## Acceptance Criteria
- AC-1 (REQ-001): `rg "def (start_attempt|count_attempts)" scripts/agent/workflow/state_store.py` finds nothing.
- AC-2 (REQ-002): `StateStore.finish_attempt` contains no SQL and calls `attempt_ops.finish_attempt`; `UPDATE attempts SET status=?` appears once in `scripts/` (in `attempt_ops.py`), plus `recover_stale_attempts`'s stale-recovery update.
- AC-3 (REQ-003): `INSERT INTO attempts` appears twice in `scripts/` (`attempt_ops.py` and `idempotency_ops.py`), the latter with the cross-reference comment, and its transaction is unchanged.
- AC-4 (REQ-004): ruff reports no unused import in `state_store.py`.
- AC-5: `uv run pytest tests/agent/workflow tests/agent/test_orchestrator.py` passes unchanged; `uv run python tools/generate_reference_table.py --check` is clean.

## Tests
- `REQ-001`, `REQ-002`, `REQ-003`: no new tests (no behavior change). `tests/agent/workflow/test_workflow_engine.py` drives `StateStore.finish_attempt` and `begin_stage_if_new` against a real database and is the behavior lock; the grep checks in Validation plan cover the structural criteria.

## Documentation Impact
N/A: `rg` over `docs/` finds no mention of `StateStore.start_attempt`, `count_attempts`, or `finish_attempt`; the generated reference showed no drift in Step 3 and is re-checked in Phase 2. `agent_04_03` describes `begin_stage_if_new` only by behavior, which is unchanged.

## Assumptions
- `attempt_ops.finish_attempt` and `StateStore.finish_attempt` are SQL- and commit-identical (both read in Step 2), so delegation is behavior-neutral.
- The wfrecovery001 Plan, when implemented, starts from the post-change state; its REQ-005 edit then lands only in `attempt_ops.py`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether wfrecovery001 (consumed Plan, all rows `Pending`, code unimplemented) is still scheduled | No `Execution Status` change or open Issue after 2026-11-01 | The owner decides; this Plan is valid in either case because it keeps `attempt_ops.start_attempt` | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Modify | Medium: `StateStore` is used across the workflow package; two public methods removed (no callers) | 5 | High: one author (name variants) | Runtime code under `scripts/`; copied by deploy, no schema or config change |
| `scripts/agent/workflow/idempotency_ops.py` | Modify | Low: comment only | 1 | High: one author | Runtime code under `scripts/`; copied by deploy, no schema or config change |

## Design
Path A (2 files, no schema change; removal of two public methods with zero callers is not a runtime-facing interface change). Consumer scan: `rg` for the three names over `scripts/`, `tests/`, `docs/` (Step 2) lists the `workflow_engine.py` finish calls (kept), the `attempt_ops` imports in three test files (kept, they import `attempt_ops` not `StateStore`), and nothing else; `tools/scan_change_consumers.py` is text-only and would add no candidate. `StateStore.recover_stale_attempts` is deliberately left with its own SQL.

## Implementation steps
1. **Phase 1: Consolidation**
   - [ ] Delete the two dead methods, delegate `finish_attempt`, remove unused imports (REQ-001, REQ-002, REQ-004; `scripts/agent/workflow/state_store.py`)
   - [ ] Add the cross-reference comment (REQ-003; `scripts/agent/workflow/idempotency_ops.py`)
2. **Phase 2: Deployment & Verification**
   - [ ] Hand-off to `skills/deploy/SKILL.md`: committed and pushed first; deploying is the user's decision (approval gate). Run the Validation plan commands (REQ-002; `scripts/agent/workflow/state_store.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Existing real-DB tests | `uv run pytest tests/agent/workflow tests/agent/test_orchestrator.py` | Pass, unchanged |
| both files | Structural grep | `rg "INSERT INTO attempts\|UPDATE attempts" scripts` | Matches the counts in AC-2 and AC-3 |
| both files | Lint, type, security, size, reference drift | `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check` | No new findings (radon, vulture: Not available) |

## Risks
- **Risk**: A caller outside `scripts/`, `tests/`, `docs/` (for example an operator script) uses a removed method → **Mitigation**: `rg` over those three trees found none; `config/` and `tools/` are checked in Phase 1 with the same `rg`.
- **Risk**: wfrecovery001's procedures (already generated against the old layout) conflict with the removal → **Mitigation**: its REQ-003 requires the same removal; the implementer reconciles when it is picked up (UNK-01).
- **Risk**: Delegation changes the commit behavior of `finish_attempt` → **Mitigation**: both copies end with `commit()` (read in Step 2); the engine tests assert persisted statuses.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Consolidate attempt CRUD in `state_store.py` and comment `idempotency_ops.py` | Pending | — | — | |
| 2 | Deploy hand-off and verification | Pending | — | — | |

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
- **Source issue**: issues/20261103-134148_wfreview006_duplicate-attempt-crud-apis.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-090240
- **Related target files**: `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/idempotency_ops.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes 1; zero callers by `rg` | `scripts/agent/workflow/state_store.py` | Phase 1 | AC-1 | grep check; workflow tests | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes 2 | `scripts/agent/workflow/state_store.py` | Phase 1 | AC-2 | engine tests; grep check | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes 3, Constraints 1 | `scripts/agent/workflow/idempotency_ops.py` | Phase 1 | AC-3 | grep check; engine tests | Explicit in issue |
| REQ-004 | Derived from the deletions (unused imports) | `scripts/agent/workflow/state_store.py` | Phase 1 | AC-4 | `uv run ruff check` | Derived from confirmed evidence |
