## Goal

Extend `tests/agent/test_history_compression_consistency.py` to cover a mid-turn compression failure: after an injected failure during compression, the DB rows, `sessions.undo_floor_message_id`, and conversation memory remain mutually consistent and are restored to their pre-turn values (`REQ-004`, `REQ-006`). Existing successful-compression consistency cases stay as regression coverage.

## Scope

- **In-Scope** (`tests/agent/test_history_compression_consistency.py`, existing; extended):
  - Compression-failure test: inject a failure during the boundary-routed compression persist; assert messages, `undo_floor_message_id`, and memory are all restored to pre-turn values (`AC-006`).
  - Consistency test: after a successful compression, DB rows and memory agree (`REQ-006`).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The boundary body (turn_persistence.py, seq 01).
  - The manager routing (conversation_state_manager.py, seq 06).
  - Memory snapshot/restore (context.py, seq 04).

## Assumptions

- Compression is routed through the turn boundary (seq 06); a failure there is compensated like any other turn write (`AC-006`).
- `replace_messages` updates `undo_floor_message_id` atomically (schema_sql.py); the test asserts it returns to its pre-turn value on compensation.

## Design decisions

- **Append, do not rewrite.** New failure-path tests are added alongside existing success cases so both remain (`AC-008`).
- **Mutual-consistency assertion.** The failure test asserts DB rows == memory == pre-turn `undo_floor_message_id` simultaneously, matching `AC-006`.

## Alternatives considered

- **New module.** Rejected: the existing module fixtures the history manager and temp DB; extending it reuses setup.

## Implementation

### Target file

`tests/agent/test_history_compression_consistency.py` (existing; extended)

### Procedure

1. Add a compression-failure test that injects a DB failure during the boundary-routed compression and asserts restoration.
2. Keep the existing successful-compression consistency test.
3. Run the validation sequence.

### Method

`handle_history_compression` (conversation_state_manager.py, seq 06) compresses history and persists via the boundary; on failure the boundary compensates (turn_persistence.py, seq 01) and restores memory (context.py, seq 04). `replace_messages` updates `undo_floor_message_id` atomically. Tests assert pre-turn consistency on both failure and success paths.

```python
# test_history_compression_consistency.py — compression failure path  (new)
async def test_compression_failure_restores_pre_turn_state():
    ...

async def test_successful_compression_keeps_db_and_memory_consistent():
    ...
```

### Details

- **`REQ-006` / `AC-006`:** the failure test asserts DB rows, memory, and `undo_floor_message_id` are all restored to pre-turn values.
- **`REQ-004` / `AC-004`:** memory equals the turn-start snapshot after compensation.
- **`AC-008`:** existing success cases unchanged.

## Compatibility considerations

- Additive; existing tests untouched.

## Security considerations

- Temp DB only; no secrets.

## Rollback considerations

- Revert the test-file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| compression failure | Failure injection: full restoration | `uv run pytest tests/agent/test_history_compression_consistency.py` | Pre-turn state restored (`AC-006`) |
| compression success | Consistency check | `uv run pytest tests/agent/test_history_compression_consistency.py` | DB == memory |
| backward compat | Regression: existing cases | `uv run pytest tests/agent/test_history_compression_consistency.py` | Unchanged (`AC-008`) |

## Completion criteria

- Compression-failure restoration test passes; success-consistency and existing cases pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body (turn_persistence.py, seq 01).
- Manager routing (conversation_state_manager.py, seq 06).
- Orchestrator coverage (orchestrator.py, seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend compression-consistency tests with failure-restoration case | Pending | — | — | Extend existing module |
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
- **Requirement ID**: `REQ-004`, `REQ-006`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `tests/agent/test_history_compression_consistency.py`
