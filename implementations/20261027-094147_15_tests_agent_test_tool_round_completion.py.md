## Goal

Update `tests/agent/test_tool_round_completion.py` mocks and expectations so the round's tool-result persistence goes through the turn boundary's grouped variant instead of a standalone `save_many` (`REQ-005`). The round completion write path changed (seq 08); the existing completion tests must expect boundary-routed, grouped persistence.

## Scope

- **In-Scope** (`tests/agent/test_tool_round_completion.py`, existing; extended):
  - Update mocks to assert tool-result inserts on the boundary's grouped variant rather than `session.save_many`.
  - Add a round-atomicity case: a single injected failure leaves either all or none of the round's rows (`AC-005`).
  - Preserve existing result-merging and denied/pair-handling assertions.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The boundary body (turn_persistence.py, seq 01).
  - The round-completion change itself (tool_round_completion.py, seq 08).

## Assumptions

- The round (seq 08) persists tool results via the boundary's grouped variant; tests mock that handle instead of `session.save_many`.

## Design decisions

- **Redirect the mock, keep the round logic.** Only the persistence assertion changes; round-atomicity is added as a new case.

## Alternatives considered

- **Rewrite the module.** Rejected: only the persistence assertion changes.

## Implementation

### Target file

`tests/agent/test_tool_round_completion.py` (existing; extended)

### Procedure

1. Update existing cases to expect tool-result inserts on the boundary's grouped variant (seq 08).
2. Add a round-atomicity case asserting all-or-none under a single injected failure.
3. Run the validation sequence.

### Method

`complete_round` (tool_round_completion.py, seq 08) persists tool results via the boundary's grouped variant; tests assert that insert and round atomicity.

```python
# test_tool_round_completion.py — grouped boundary assertions  (new)
async def test_tool_results_persisted_via_grouped_variant():
    ...

async def test_round_is_all_or_none_under_failure():
    ...
```

### Details

- **`REQ-005` / `AC-005`:** the all-or-none case asserts a single injected failure leaves either all or none of the round's rows.
- **Backward compat:** result-merging and denied/pair assertions preserved.

## Compatibility considerations

- Adjusts existing mocks; does not remove existing test functions.

## Security considerations

- Temp DB only; no secrets.

## Rollback considerations

- Revert the test-file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| grouped routing | Mock update: inserts on boundary | `uv run pytest tests/agent/test_tool_round_completion.py` | Inserts on grouped variant |
| round atomicity | Failure injection | `uv run pytest tests/agent/test_tool_round_completion.py` | All-or-none (`AC-005`) |
| backward compat | Regression: existing cases | `uv run pytest tests/agent/test_tool_round_completion.py` | Unchanged (`AC-008`) |

## Completion criteria

- Round-completion tests expect boundary-routed grouped persistence; round-atomicity case passes; existing cases pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body (turn_persistence.py, seq 01).
- Round-completion change (tool_round_completion.py, seq 08).
- Assistant-row persist (llm_turn_runner.py, seq 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update round-completion tests for boundary routing | Pending | — | — | Update existing module |
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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `tests/agent/test_tool_round_completion.py`
