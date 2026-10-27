## Goal

Extend `tests/agent/test_orchestrator.py` to verify turn-level failure handling end to end (`REQ-001`, `REQ-004`): injecting a `sqlite3.Error` at any single turn write leaves zero message rows from that turn (compensation) and restores memory to the turn-start snapshot, and the failure propagates as the dedicated persistence error type so the REPL can surface it distinctly.

## Scope

- **In-Scope** (`tests/agent/test_orchestrator.py`, existing; extended):
  - Turn-level failure-injection test: inject a DB failure at the user-append, round, final-save, and compression points; assert zero of the turn's rows remain and memory is restored (`AC-002`, `AC-004`).
  - Propagation test: the orchestrator re-raises the dedicated persistence error type (`REQ-003`).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The boundary body (turn_persistence.py, seq 01).
  - The facade factory (session.py, seq 03).
  - Memory snapshot/restore (context.py, seq 04).

## Assumptions

- The orchestrator (seq 05) creates the boundary per turn and re-raises ConversationPersistenceError after compensation.
- Failure injection uses the project's existing injection surface.

## Design decisions

- **End-to-end via the orchestrator.** Unlike the boundary unit tests (test_turn_persistence.py, seq 11), these drive a full turn through `_execute_turn` to verify the whole path compensates and propagates.

## Alternatives considered

- **Unit-only.** Rejected: turn-level atomicity requires the orchestrator's per-turn boundary creation, so an integration-style case is needed.

## Implementation

### Target file

`tests/agent/test_orchestrator.py` (existing; extended)

### Procedure

1. Add a turn-level failure-injection case for each phase asserting compensation + memory restore.
2. Add a propagation case asserting the dedicated persistence error type is re-raised.
3. Run the validation sequence.

### Method

The orchestrator (orchestrator.py, seq 05) creates one boundary per turn via the facade factory (session.py, seq 03); on a persistence failure the boundary compensates (turn_persistence.py, seq 01) and restores memory (context.py, seq 04), then the orchestrator re-raises.

```python
# test_orchestrator.py — turn-level failure handling  (new)
async def test_injected_failure_compensates_and_restores():
    ...

async def test_persistence_failure_propagates_as_dedicated_type():
    ...
```

### Details

- **`REQ-002` / `AC-002`:** each phase's injection leaves zero of the turn's rows.
- **`REQ-004` / `AC-004`:** memory equals the turn-start snapshot after compensation.
- **`REQ-003` / `AC-003`:** the failure propagates as the dedicated persistence error type.

## Compatibility considerations

- Additive; existing orchestrator tests untouched.

## Security considerations

- Temp DB only; no secrets.

## Rollback considerations

- Revert the test-file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| turn compensation | Full-turn failure injection | `uv run pytest tests/agent/test_orchestrator.py` | Zero turn rows (`AC-002`) |
| memory restore | Post-failure memory check | `uv run pytest tests/agent/test_orchestrator.py` | Memory == snapshot (`AC-004`) |
| propagation | Type assertion | `uv run pytest tests/agent/test_orchestrator.py` | Dedicated type (`AC-003`) |
| backward compat | Regression: existing cases | `uv run pytest tests/agent/test_orchestrator.py` | Unchanged (`AC-008`) |

## Completion criteria

- Turn-level failure-handling cases pass; existing orchestrator tests pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body (turn_persistence.py, seq 01).
- Facade factory (session.py, seq 03).
- Memory snapshot/restore (context.py, seq 04).
- REPL surfacing (repl_input_loop.py, seq 10).

## Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend test_orchestrator.py with turn-level failure cases | Done | 2026-10-27 | 2026-10-27 | Added `TestTurnLevelPersistenceFailureRealFlow` (4 tests) |
| 2 | Add or update tests per Validation plan | Done | 2026-10-27 | 2026-10-27 | See adversarial finding below |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-10-27 | 2026-10-27 | ruff clean on test file; full suite 10242 passed / 12 skipped (was 10238; +4) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 2026-10-27 | 2026-10-27 | Execution Status only; N/A elsewhere |

### Adversarial verification findings

- **Doc claim corrected.** The original procedure asserted that an execute-stage
  persistence failure propagates out of `_execute_turn` unchanged as
  `ConversationPersistenceError`. Verified against `workflow_engine.py`
  (`_run_stage_with_retry`) and `workflow_engine_adapter.py` (`execute_turn`):
  the real engine retries execute-stage failures up to `max_attempts`, then
  raises `WorkflowHaltError`, which the adapter routes to `on_error`. Entry-prep
  writes (`append_user_message`, `handle_history_compression`) run inside
  `execute_turn`'s single `_prepare_turn_input` try/except, which wraps their
  `ConversationPersistenceError` in a `WorkflowHaltError` too. So **both** phases
  end as `WorkflowHaltError` via `on_error`; the boundary compensates every row
  after the turn-start marker and restores memory to the snapshot in every case.
- **Guard made SQL-aware.** The initial `_InjectingSQLiteHelper._guard` raised on
  *every* statement, which also blocked the compensation `DELETE` ("Turn
  compensation failed after persistence error"). Fixed to inspect the statement
  text and fail only `INSERT`s; `save`/`save_many`/`replace_messages` all reach
  the DB through an INSERT, while the marker is a `SELECT` and compensation is a
  `DELETE`.
- **Negative control added.** `test_execute_stage_zero_rows_depends_on_compensation`
  neutralizes `delete_messages_from` and confirms the committed user row survives
  a failed later write -- proving the positive zero-rows assertions depend on the
  compensation path (the append guard raises before any row is written, so a
  user-append-failure control could never leave rows behind).

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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `tests/agent/test_orchestrator.py`
