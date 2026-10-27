## Goal

Extend `tests/agent/test_repl_error_handling.py` to verify that a ConversationPersistenceError is surfaced distinctly and the REPL loop continues with consistent state (`REQ-007`). A compensated persistence failure must print a dedicated "turn not persisted, history rolled back" message rather than the generic `{name}: {exc}` format.

## Scope

- **In-Scope** (`tests/agent/test_repl_error_handling.py`, existing; extended):
  - Distinct-message test: inject a persistence failure and assert the dedicated view method/message is used.
  - Loop-continuation test: after the persistence error, the loop accepts the next input with consistent state.
  - Backward-compat: existing generic-error tests still pass.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The boundary body + compensation (turn_persistence.py, seq 01).
  - The orchestrator narrow branch (orchestrator.py, seq 05).

## Assumptions

- The orchestrator (seq 05) re-raises the dedicated persistence error type after compensation.
- The REPL (repl_input_loop.py, seq 10) has a dedicated branch ahead of the generic handler.

## Design decisions

- **Append persistence-error tests** to the existing REPL-error module, reusing its view stub.

## Alternatives considered

- **New module.** Rejected: the existing module already stubs the view and drives `_repl_loop`.

## Implementation

### Target file

`tests/agent/test_repl_error_handling.py` (existing; extended)

### Procedure

1. Add a distinct-message test asserting the dedicated persistence message is surfaced.
2. Add a loop-continuation test asserting the next input is accepted after a persistence error.
3. Keep existing generic-error tests as regression coverage.
4. Run the validation sequence.

### Method

The REPL `_repl_loop` (repl_input_loop.py, seq 10) catches the dedicated persistence error before the generic handler and writes a distinct message via a dedicated view method, then continues the loop.

```python
# test_repl_error_handling.py — persistence-error surfacing  (new)
async def test_persistence_error_surfaced_distinctly():
    ...

async def test_loop_continues_after_persistence_error():
    ...
```

### Details

- **`REQ-007` / `AC-007`:** the persistence failure prints a distinct message and the loop continues.
- **`AC-008`:** existing generic-error tests still pass.

## Compatibility considerations

- Additive; existing error-handling tests untouched.

## Security considerations

- Temp DB only; no secrets.

## Rollback considerations

- Revert the test-file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| distinct message | Unit: dedicated message surfaced | `uv run pytest tests/agent/test_repl_error_handling.py` | Distinct message |
| loop continuation | Behavior: next input accepted | `uv run pytest tests/agent/test_repl_error_handling.py` | Loop consistent (`AC-007`) |
| backward compat | Regression: existing cases | `uv run pytest tests/agent/test_repl_error_handling.py` | Unchanged (`AC-008`) |

## Completion criteria

- Persistence-error surfacing and loop-continuation cases pass; existing error tests pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body + compensation (turn_persistence.py, seq 01).
- Orchestrator narrow branch (orchestrator.py, seq 05).
- Generic `_surface_turn_error` formatting (repl_input_loop.py, seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend test_repl_error_handling.py with persistence-error cases | Done | 2026-10-27 | 2026-10-27 | Test added under seq 10 commit 223fd7766 (surface ConversationPersistenceError distinctly in REPL loop) |
| 2 | Add or update tests per Validation plan | Done | 2026-10-27 | 2026-10-27 | `test_repl_surfaces_persistence_error_distinctly` asserts distinct message + loop continuation |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-10-27 | 2026-10-27 | All 3 tests in test_repl_error_handling.py pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 2026-10-27 | 2026-10-27 | This doc |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `tests/agent/test_repl_error_handling.py`
