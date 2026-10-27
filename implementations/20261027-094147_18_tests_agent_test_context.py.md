## Goal

Extend `tests/agent/test_context.py` to cover the new `snapshot_messages()` and `restore_messages()` API (`REQ-004`): snapshot returns a defensive copy independent of later mutations, restore replaces history element-wise without re-validation, and both are safe under concurrent mutation (lock behavior).

## Scope

- **In-Scope** (`tests/agent/test_context.py`, existing; extended):
  - Snapshot independence: a snapshot is unaffected by subsequent appends.
  - Restore correctness: after restore, history equals the snapshot element-wise.
  - Lock safety: snapshot/restore under concurrent appends do not tear.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The boundary that consumes the snapshot (turn_persistence.py, seq 01).
  - The facade factory (session.py, seq 03).

## Assumptions

- `snapshot_messages()` / `restore_messages()` (context.py, seq 04) guard `history` with the async lock, matching `append_message`/`replace_history`.

## Design decisions

- **Append snapshot/restore tests** to the existing context-test module, reusing its conversation fixtures.

## Alternatives considered

- **New module.** Rejected: the existing module already builds `ConversationState`/fixtures.

## Implementation

### Target file

`tests/agent/test_context.py` (existing; extended)

### Procedure

1. Add a snapshot-independence test: snapshot, append, assert snapshot unchanged.
2. Add a restore-correctness test: restore, assert history equals snapshot element-wise.
3. Add a lock-safety test: concurrent appends during snapshot/restore do not tear.
4. Run the validation sequence.

### Method

`snapshot_messages()` (context.py, seq 04) returns `[dict(msg) for msg in history]` under the lock; `restore_messages(snapshot)` clears and extends history element-wise under the lock without re-validating.

```python
# test_context.py — snapshot/restore tests  (new)
async def test_snapshot_is_independent_of_later_appends():
    ...

async def test_restore_sets_history_to_snapshot_elementwise():
    ...

async def test_snapshot_restore_under_concurrent_append():
    ...
```

### Details

- **`REQ-004` / `AC-004`:** restore sets history equal to the snapshot element-wise.
- **Lock safety:** concurrent-append test asserts no torn snapshot.

## Compatibility considerations

- Additive; existing context tests untouched.

## Security considerations

- Temp DB only; no secrets.

## Rollback considerations

- Revert the test-file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| snapshot independence | Unit: snapshot stable across appends | `uv run pytest tests/agent/test_context.py` | Snapshot unchanged |
| restore correctness | Unit: history == snapshot | `uv run pytest tests/agent/test_context.py` | `AC-004` |
| lock safety | Concurrency: snapshot under append | `uv run pytest tests/agent/test_context.py` | No torn snapshot |
| backward compat | Regression: existing cases | `uv run pytest tests/agent/test_context.py` | Unchanged (`AC-008`) |

## Completion criteria

- Snapshot/restore tests pass; existing context tests pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary consumer (turn_persistence.py, seq 01).
- Facade factory (session.py, seq 03).
- Write-routing callers (orchestrator.py seq 05; llm_turn_runner.py seq 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend test_context.py with snapshot/restore tests | Pending | — | — | Extend existing module |
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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `tests/agent/test_context.py`
