## Goal

Add the new test module `tests/agent/test_turn_persistence.py` that verifies the atomic turn-persistence boundary end to end (`REQ-001`–`REQ-004`): the boundary commits per phase on the happy path, raises the single persistence error type, compensates by deleting exactly the turn's rows on an injected DB failure, and restores memory to the turn-start snapshot.

## Scope

- **In-Scope** (`tests/agent/test_turn_persistence.py`, new):
  - Happy-path: the boundary commits user/round/final rows through its reused connection.
  - Exception type: a persisted failure surfaces as the dedicated persistence error type (`REQ-003`).
  - Compensation: an injected `sqlite3.Error` at any single turn write leaves zero of that turn's rows (`AC-002`).
  - Snapshot restore: after compensation, memory equals the turn-start snapshot element-wise (`AC-004`).
- **Out-of-Scope** (exercised by other rows this Plan generates):
  - The boundary body (turn_persistence.py, seq 01).
  - The facade factory (session.py, seq 03).
  - Memory snapshot/restore API (context.py, seq 04).

## Assumptions

- Tests run under `uv run pytest` against a temp `session.sqlite` and a fake conversation memory object exposing the same snapshot/restore surface as context.py (seq 04).
- The orchestrator creates the boundary via session.py (seq 03); tests may construct the boundary directly or through that factory.

## Design decisions

- **Inject failures at each phase.** A failure-injection hook (per the project's existing injection service pattern) raises `sqlite3.Error` at the user-append, round-N, final-save, and compression points; each case asserts the turn's rows are deleted and memory restored (`AC-002`, `AC-004`).
- **One assertion per acceptance criterion.** Each `AC-001`–`AC-004` maps to at least one dedicated test so coverage is traceable.

## Alternatives considered

- **Drive through the full orchestrator.** Rejected: unit tests construct the boundary (or the seq 03 factory) directly for isolation; end-to-end coverage lives in test_orchestrator.py (seq 17).

## Implementation

### Target file

`tests/agent/test_turn_persistence.py` (new)

### Procedure

1. Create `tests/agent/test_turn_persistence.py` with async tests for the happy path, exception type, compensation, and snapshot restore.
2. Wire a failure-injection point so `sqlite3.Error` can be raised at each turn write.
3. Run the validation sequence.

### Method

The boundary (turn_persistence.py, seq 01) owns the turn-start marker, per-phase writes on a reused connection, compensation, and memory restore. The facade factory (session.py, seq 03) materializes it; the memory snapshot/restore API (context.py, seq 04) provides the turn-start image. Tests assert the four behaviors above.

```python
# test_turn_persistence.py — new boundary tests (REQ-001..REQ-004)  (new)
async def test_boundary_commits_per_phase():
    ...

async def test_failure_raises_persistence_error_type():
    ...

async def test_compensation_deletes_only_turn_rows():
    ...

async def test_memory_restored_to_turn_start_snapshot():
    ...
```

### Details

- **`REQ-001` / `AC-001`:** happy-path test asserts per-phase commits through the reused connection.
- **`REQ-003` / `AC-003`:** the exception-type test asserts the dedicated persistence error type is raised and no raw DB error escapes.
- **`REQ-002` / `AC-002`:** the compensation test injects a failure at each phase and asserts zero of that turn's rows remain.
- **`REQ-004` / `AC-004`:** the snapshot-restore test asserts memory equals the turn-start snapshot element-wise after compensation.

## Compatibility considerations

- New file; name collision already checked (`ls scripts/agent tests/agent`). Does not touch existing test modules.

## Security considerations

- Tests use a temp DB; no secrets involved.

## Rollback considerations

- Delete the new test file (`git checkout` is a no-op for untracked; remove the file). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| happy path | Unit: per-phase commit | `uv run pytest tests/agent/test_turn_persistence.py` | Passes |
| exception type | Unit: dedicated type raised | `uv run pytest tests/agent/test_turn_persistence.py` | `AC-003` |
| compensation | Failure injection at each phase | `uv run pytest tests/agent/test_turn_persistence.py` | Zero turn rows (`AC-002`) |
| snapshot restore | Failure + memory check | `uv run pytest tests/agent/test_turn_persistence.py` | Memory == snapshot (`AC-004`) |

## Completion criteria

- `tests/agent/test_turn_persistence.py` covers happy-path commit, exception type, compensation, and snapshot restore.
- All new tests pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body (turn_persistence.py, seq 01).
- Facade factory (session.py, seq 03).
- Memory snapshot/restore (context.py, seq 04).
- Orchestrator-level coverage (orchestrator.py, seq 05; test_orchestrator.py, seq 17).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `tests/agent/test_turn_persistence.py` covering boundary behavior | Pending | — | — | New test module |
| 2 | Add or update tests per Validation plan | Pending | — | — | This module |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `tests/agent/test_turn_persistence.py`
