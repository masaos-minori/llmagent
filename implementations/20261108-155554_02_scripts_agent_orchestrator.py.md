## Goal
Give `Orchestrator` a narrow public close path for the `StateStore` it constructs (L91), so the orchestrator-owned store is closed exactly once at service shutdown through the shutdown coordinators (`REQ-003`), and pin the double-close safety the shutdown retry path relies on (`REQ-005`) with regression tests.

## Scope
**Release unit**: wfaudit006-full

- Covers Plan `plans/20261108-084008_wfaudit006_state-store-lifecycle-ownership.md` row 2 only: `scripts/agent/orchestrator.py`.
- Also hosts the `REQ-005` double-close regression test in `tests/agent/workflow/test_state_store.py` (the `state_store.py` target row was demoted to confirmed no-change; see plan Notes 2026-11-08).

## Assumptions
- Sibling overlap: sibling procedure 134201_03 (wfaudit001) edits the initialization region of this same file (the recovery call at L92). That region is disjoint from the method added here; if 134201_03 lands first, re-anchor on the symbol `workflow_status` instead of the line numbers cited below, which refer to HEAD `ad48bfa28`. Sibling procedures are design references, not implemented code.
- `StateStore.close` (L54-56 of `scripts/agent/workflow/state_store.py`) delegates to `SQLiteHelper.close` (`scripts/db/helper.py` L232-241), which already no-ops on a second close: early return when `conn` is `None`, `OSError` swallowed with a warning. The `REQ-005` "idempotent-safe" side of the choice therefore holds at HEAD and needs no production code change.
- The hook wiring that calls the new method is added by sibling procedures 03 and 04 of this plan; this procedure alone does not change any shutdown behavior.

## Design decisions
- One-statement delegation in a public `close` method (plan Design: "The orchestrator exposes a narrow close that the wiring calls"): `self._state_store.close()` and nothing else — no orchestrator-level closed-flag, because idempotence is owned in exactly one layer (`SQLiteHelper`).
- Insert the method in the public method region after `workflow_status` (L202-211) so shutdown wiring never reaches into private attributes; the coordinators (rows 3-4) only call the public method.

## Alternatives considered
- Closed-flag guard inside `StateStore`: rejected at the procedure pass — the underlying close is already idempotent-safe; adding a second guard double-books the invariant (plan Notes 2026-11-08 supersede the original closed-flag design).
- Closing the store from `__del__` or `atexit`: rejected — implicit close destroys the auditable ownership rule (whoever constructs closes, via the visible shutdown coordinators).

## Implementation
### Target file
`scripts/agent/orchestrator.py`

### Procedure
Add one public method; no other edits.

### Method
Insert after the `workflow_status` method:

```python
    def close(self) -> None:
        """Close the workflow StateStore. Called once by the shutdown coordinator hook."""
        self._state_store.close()
```

### Details
- `__init__` (L91-92: the `StateStore()` construction and the `recover_stale_attempts` call) is untouched.
- No new imports; `StateStore` is already imported (L40).
- The method is intentionally idempotent-by-delegation: a coordinator retry or a duplicated hook call cannot raise (`REQ-005`).

## Compatibility considerations
- Orchestrator construction and turn behavior are unchanged; existing tests that construct an `Orchestrator` without calling close behave exactly as today (the connection closes at process exit).
- Tests using the `_status_harness` probe store (its teardown closes the store) still pass when `close` is called on the same probe store first — the close is idempotent-safe.

## Security considerations
- No new attack surface: close exposes no parameters and releases one owned resource.

## Rollback considerations
- Revert the commit; the method and its tests disappear with no persisted state to unwind. Revert rows 3-4's procedures together with this one to restore today's leak-on-shutdown behavior exactly (plan Release units: one contract).

## Validation plan
- `tests/agent/test_orchestrator.py`: add class `TestOrchestratorClose` (new) built on the existing `_status_harness` (real engine + adapter over a temp `workflow.sqlite` with the pre-built probe store): call `close` once, assert the probe store's `conn` is `None`; call `close` a second time, assert no exception is raised and `conn` stays `None`.
- `tests/agent/workflow/test_state_store.py` (existing file): add `test_double_close_is_noop` (new) — open a real `StateStore` over the temp workflow DB, call `close` twice, assert no raise and `conn` is `None` after the second call (`REQ-005` regression pin).
- Orchestrator shutdown wiring coverage is added by row 4's REPL test; the coordinator hook semantics by row 3's tests.
- `uv run pytest tests/agent/ -q` after the change, then full `uv run pytest tests/ -q`; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- `Orchestrator` has the public `close` delegating to `self._state_store.close()`; the new close and double-close tests pass; full suite green.

## Out of Scope
- The coordinator hook API (row 3 procedure) and the REPL registration call (row 4 procedure).
- Any close-guard code in `scripts/agent/workflow/state_store.py` (confirmed no-change Reference row).
- `scripts/agent/session_persister.py`'s own `StateStore()` usage (L93) — owned by plan `wfreview002`, not this plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | docs verified no-change; out of scope |

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
- **Requirement ID**: `REQ-003` (orchestrator close path), `REQ-005` (double-close safety pin)
- **Source issue**: `issues/20261107-203219_wfaudit006_state-store-lifecycle-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084008_wfaudit006_state-store-lifecycle-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-155554
- **Related target files**: `scripts/agent/orchestrator.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-155554 -->
