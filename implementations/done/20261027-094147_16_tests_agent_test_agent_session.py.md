## Goal

Extend `tests/agent/test_agent_session.py` to cover the `turn_boundary()` facade factory (`REQ-001`): it materializes a TurnPersistence boundary bound to the session, captures the turn-start `message_id` marker (`0` for a fresh session), and takes a memory snapshot.

## Scope

- **In-Scope** (`tests/agent/test_agent_session.py`, existing; extended):
  - Factory test: `turn_boundary()` returns a boundary bound to the session with the correct turn-start marker.
  - Fresh-session marker test: a session with no rows yields marker `0` (`UNK-02`).
  - Snapshot test: the returned boundary holds a turn-start memory snapshot.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The boundary body (turn_persistence.py, seq 01).
  - The snapshot/restore API (context.py, seq 04).

## Assumptions

- `turn_boundary()` (session.py, seq 03) is an async factory receiving the conversation memory explicitly.
- The turn-start marker is `MAX(message_id)` for the session (`0` when there are no rows).

## Design decisions

- **Append factory tests** to the existing facade-test module, reusing its session fixtures.

## Alternatives considered

- **New module.** Rejected: the existing module already builds `AgentSession` instances and fixtures.

## Implementation

### Target file

`tests/agent/test_agent_session.py` (existing; extended)

### Procedure

1. Add a factory test asserting `turn_boundary()` returns a boundary bound to the session.
2. Add a fresh-session marker test asserting marker `0`.
3. Add a snapshot test asserting the boundary holds a turn-start snapshot.
4. Run the validation sequence.

### Method

`AgentSession.turn_boundary()` (session.py, seq 03) computes the turn-start marker, awaits a memory snapshot (context.py, seq 04), and returns a TurnPersistence (turn_persistence.py, seq 01) bound to the session.

```python
# test_agent_session.py — turn_boundary factory tests  (new)
async def test_turn_boundary_returns_bound_boundary():
    ...

async def test_turn_boundary_fresh_session_marker_is_zero():
    ...

async def test_turn_boundary_captures_snapshot():
    ...
```

### Details

- **`REQ-001`:** the factory returns a boundary bound to the session.
- **`UNK-02`:** fresh-session marker is `0`.

## Compatibility considerations

- Additive; existing facade tests untouched.

## Security considerations

- Temp DB only; no secrets.

## Rollback considerations

- Revert the test-file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| factory | Unit: boundary bound to session | `uv run pytest tests/agent/test_agent_session.py` | Boundary returned |
| fresh marker | Unit: marker == 0 | `uv run pytest tests/agent/test_agent_session.py` | `UNK-02` |
| snapshot | Unit: snapshot captured | `uv run pytest tests/agent/test_agent_session.py` | Snapshot held |
| backward compat | Regression: existing facade cases | `uv run pytest tests/agent/test_agent_session.py` | Unchanged (`AC-008`) |

## Completion criteria

- `turn_boundary()` factory tests pass; existing facade tests pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body (turn_persistence.py, seq 01).
- Snapshot/restore (context.py, seq 04).
- Orchestrator wiring (orchestrator.py, seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend test_agent_session.py with turn_boundary factory tests | Complete | 2026-10-27 | 2026-10-27 | Extend existing module |
| 2 | Add or update tests per Validation plan | Complete | 2026-10-27 | 2026-10-27 | This module |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Complete | 2026-10-27 | 2026-10-27 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Complete | 2026-10-27 | 2026-10-27 | N/A |

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
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `tests/agent/test_agent_session.py`
