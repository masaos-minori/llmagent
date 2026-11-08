## Goal
Delete the test-only attempt writers `attempt_ops.start_attempt` (L42-77) and `attempt_ops.count_attempts` (L104-110) so the workflow attempt surface has a single creation path (`begin_stage_if_new`) and no unused counter helper (`REQ-001`).

## Scope
**Release unit**: wfaudit009-full

- Covers Plan `plans/20261108-084010_wfaudit009_test-only-state-helpers.md` row 1 only: `scripts/agent/workflow/attempt_ops.py`.
- This is a Phase 2 (plan step 2) document: the deletion lands only after every test caller has been retargeted by documents 04-08 (plan step 1, Phase 1).

## Assumptions
- Census re-verified at HEAD `ad48bfa28`: `start_attempt` callers are `tests/agent/workflow/test_workflow_state_store.py` (import L20; calls L153, L160-161, L166, L182, L252-254), `tests/agent/workflow/test_workflow_stage_persistence.py` (import L11; calls L42, L61, L73) and `tests/agent/workflow/test_workflow_status_vocabulary.py` (import L21; call L115); `count_attempts` callers are `tests/agent/workflow/test_workflow_engine.py` (import L15; asserts L221, L378, L405, L462, L622, L643, L683) and `test_workflow_state_store.py` (L162). Zero production callers in `scripts/` apart from the naming mention in the `idempotency_ops.py` comment (document 03).
- All of those test edits land before this document (plan Dependencies/Notes: Phase 1 first; `wfaudit001` -> `wfaudit007` -> wfaudit009). Citations here are HEAD `ad48bfa28` anchors.
- `wfaudit015` (`plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`, Draft) must not reintroduce a `start_attempt`-style writer when it lands: the single-source rule is `begin_stage_if_new`.

## Design decisions
- Delete, not wire (plan Design): production already creates attempts only through `begin_stage_if_new` (`workflow_engine.py` L313-319, with `lease_duration_sec`), counts attempts via its retry loop range, and classifies stale rows via `recover_stale_attempts`/`_classify_running_attempts`.
- Keep the rest of `attempt_ops.py` untouched: `get_owner_id` (L19-29) and `lease_expires_from` (L32-39) are imported by `idempotency_ops.py` (L9) for the surviving lease-stamping branch; `finish_attempt` (L80-101) is used by production and the facade.

## Alternatives considered
- Wiring `count_attempts` into the engine retry loop: rejected in the plan Design — the engine counts attempts via its own retry range, and a production counter would re-create the API this plan removes.

## Implementation
### Target file
`scripts/agent/workflow/attempt_ops.py`

### Procedure
Delete the two function blocks and prune the imports they alone used.

### Method
1. Delete `start_attempt` (the whole def block L42-77, symbol-anchored: from `def start_attempt(` through its `return AttemptRecord(...)`).
2. Delete `count_attempts` (L104-110, from `def count_attempts(` through `return int(rows[0][0])`).
3. Drop `import uuid` (L7): only `start_attempt` used it; `get_owner_id` uses `secrets`, not `uuid`.
4. Narrow L14 to `from agent.workflow.models import ATTEMPT_STATUSES`: `AttemptRecord` is only referenced by `start_attempt`'s signature and return; `ATTEMPT_STATUSES` is still required by the `finish_attempt` vocabulary guard (L93-96). `timedelta` and `parse_iso_utc` stay (used by `lease_expires_from`).

### Details
- Remaining public surface of the module: `get_owner_id`, `lease_expires_from`, `finish_attempt`. No other edits, no rename, no signature changes elsewhere.
- The `AttemptRecord` dataclass itself stays in `agent/workflow/models.py` (used by `idempotency_ops.py` and `task_ops`).

## Compatibility considerations
- Imports are module-level function imports in the test files only (census above); documents 04-08 remove them in Phase 1, so no import error occurs at any point.
- The `wfaudit001` procedures `implementations/20261108-134201_01_scripts_agent_workflow_state_store.py.md` and `implementations/20261108-134201_02_scripts_agent_workflow_idempotency_ops.py.md` and the `wfaudit007` procedure `implementations/20261108-135741_01_scripts_agent_workflow_state_store.py.md` do not target `attempt_ops.py`; this document touches no region those plans edit.
- `docs/` references: `grep -rn` for `start_attempt` and `count_attempts` across `docs/` returned zero matches at planning time (plan Documentation Impact) — verification-only, no doc row.

## Security considerations
- None: removing an unauthenticated test-only writer shrinks the writable surface of `attempts`.

## Rollback considerations
- Revert this commit restores both helpers with no state to unwind; the Phase 1 test edits are behavior-preserving and remain valid either way.

## Validation plan
- Gate order (plan Validation plan): Phase 1 suite already green with the helpers present before this document lands; after deletion run `uv run pytest tests/agent/workflow/ -q`, then the REQ-001 grep `grep -rn "start_attempt\|count_attempts" scripts/ tests/` expecting zero matches.
- Full `uv run pytest tests/ -q` before completion; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- `start_attempt` and `count_attempts` no longer exist in `scripts/` or `tests/`; the workflow and full suites are green; the module keeps `get_owner_id`, `lease_expires_from`, `finish_attempt`.

## Out of Scope
- The test retargeting itself (documents 04-08, plan step 1).
- `state_store.py` and `idempotency_ops.py` deletions/edits (documents 02-03).
- `wfaudit015` facade routing (separate plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | lands after documents 04-08 (plan step 1) |
| 2 | Add or update tests per Validation plan | Pending | — | — | no new tests here; coverage moved in documents 04-08 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | includes the REQ-001 grep |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | docs grep verified zero matches; verification-only |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261107-203222_wfaudit009_test-only-state-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084010_wfaudit009_test-only-state-helpers.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-170505
- **Related target files**: `scripts/agent/workflow/attempt_ops.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-170505 -->
