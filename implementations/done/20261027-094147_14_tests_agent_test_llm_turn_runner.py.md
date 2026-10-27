## Goal

Update `tests/agent/test_llm_turn_runner.py` mocks and expectations so the runner's per-round assistant persistence goes through the turn boundary instead of a standalone `session.save` (`REQ-005`). The runner's write path changed (seq 07); the existing runner tests must be adjusted to expect boundary-routed persistence while still covering the tool loop.

## Scope

- **In-Scope** (`tests/agent/test_llm_turn_runner.py`, existing; extended):
  - Update mocks so the assistant-row insert is asserted on the boundary handle rather than on `session.save`.
  - Add a round-atomicity case: a failed later round leaves no partial round rows (`AC-002`).
  - Preserve existing tool-loop, guard, and error-handling assertions.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The boundary body (turn_persistence.py, seq 01).
  - The runner change itself (llm_turn_runner.py, seq 07).

## Assumptions

- The runner (seq 07) persists the assistant row via the turn boundary handle; tests mock that handle instead of `session.save`.

## Design decisions

- **Redirect the mock, keep the loop.** Existing tests already drive `run` with mocked LLM responses; the change is which object receives the assistant insert. Round-atomicity is added as a new case.

## Alternatives considered

- **Rewrite the module.** Rejected: only the persistence assertion changes; redirecting the mock preserves all existing loop coverage.

## Implementation

### Target file

`tests/agent/test_llm_turn_runner.py` (existing; extended)

### Procedure

1. Update existing cases to expect the assistant insert on the boundary handle (seq 07) instead of `session.save`.
2. Add a round-atomicity case injecting a failure at a later round and asserting no partial round rows.
3. Run the validation sequence.

### Method

The runner (llm_turn_runner.py, seq 07) persists each round's assistant row via the turn boundary handle; tests assert that insert and a failed-round compensation.

```python
# test_llm_turn_runner.py — boundary-routed round assertions  (new)
async def test_round_assistant_persisted_via_boundary():
    ...

async def test_failed_round_leaves_no_partial_rows():
    ...
```

### Details

- **`REQ-005` / `AC-002`:** the failed-round case asserts no partial round rows remain after compensation.
- **Backward compat:** existing loop/guard/error assertions preserved.

## Compatibility considerations

- Adjusts existing mocks; does not remove existing test functions.

## Security considerations

- Temp DB only; no secrets.

## Rollback considerations

- Revert the test-file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| boundary routing | Mock update: insert on boundary | `uv run pytest tests/agent/test_llm_turn_runner.py` | Insert on boundary handle |
| round atomicity | Failure injection | `uv run pytest tests/agent/test_llm_turn_runner.py` | No partial rows (`AC-002`) |
| backward compat | Regression: existing cases | `uv run pytest tests/agent/test_llm_turn_runner.py` | Unchanged (`AC-008`) |

## Completion criteria

- Runner tests expect boundary-routed persistence; round-atomicity case passes; existing cases pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body (turn_persistence.py, seq 01).
- Runner change (llm_turn_runner.py, seq 07).
- Tool-result grouping (tool_round_completion.py, seq 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update runner tests for boundary-routed persistence | Complete | 2026-10-27 | 2026-10-27 | Per-round assistant persist already asserted on `runner._ctx.turn.persistence_boundary.save` (test_executes_tool_calls_then_returns); no stale `session.save` assertions remain in the module |
| 2 | Add or update tests per Validation plan | Complete | 2026-10-27 | 2026-10-27 | Added `TestRunRoundAtomicity.test_failed_later_round_leaves_no_partial_rows`: real `AgentSession` + in-memory DB, pre-turn user row, two tool rounds, round-2 `repo.save` fails via counting side_effect, asserts `ConversationPersistenceError` and that only the user row remains (AC-002). Negative-checked: disabling `_compensate` leaves the assistant row (assertion fails) so the test exercises the real compensation path |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Complete | 2026-10-27 | 2026-10-27 | ruff check/format clean, mypy --no-namespace-packages clean (441 files), lint-imports 6/6, bandit severity High/Medium 0, vulture @80 exit 0; full suite 10237 passed, 12 skipped |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Complete | 2026-10-27 | 2026-10-27 | Marked Execution Status Complete |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `tests/agent/test_llm_turn_runner.py`
