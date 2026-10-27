## Goal

Extend `tests/agent/test_session_message_repo.py` to cover the three repository-level primitives this Plan adds: the transaction-grouped persist variant, the compensation delete, and `sqlite3.Error` → dedicated-persistence-error wrapping (`REQ-002`, `REQ-003`, `REQ-005`). Existing per-method save/save_many/replace_messages cases stay as regression coverage.

## Scope

- **In-Scope** (`tests/agent/test_session_message_repo.py`, existing; extended):
  - Grouped-transaction test: the grouped variant writes a phase-group in one transaction; an injected failure leaves either all or none of the round's rows (`AC-005`).
  - Compensation-delete test: the delete removes exactly `message_id >= marker` rows and returns the row count, leaving earlier rows intact (`AC-002`).
  - Error-wrapping test: a DB failure on the grouped/compensation paths raises the dedicated persistence error type with the cause chained (`AC-003`).
  - Backward-compat: existing save/save_many/replace cases still pass.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The boundary body (turn_persistence.py, seq 01).
  - The facade factory (session.py, seq 03).

## Assumptions

- The repo methods operate on a temp `session.sqlite`; tests inject failures via the project's existing injection surface.
- The grouped variant and compensation delete are the primitives defined in session_message_repo.py (seq 02).

## Design decisions

- **Additive test functions.** New tests are appended to the existing module; existing cases are left untouched so they remain regression coverage (`AC-008`).
- **One test per acceptance criterion** (`AC-002`, `AC-003`, `AC-005`) for traceability.

## Alternatives considered

- **New separate test module.** Rejected: the existing module already fixtures the repo and temp DB; extending it reuses setup and keeps repo tests co-located.

## Implementation

### Target file

`tests/agent/test_session_message_repo.py` (existing; extended)

### Procedure

1. Add a grouped-transaction test that persists a phase-group and asserts atomicity under an injected failure.
2. Add a compensation-delete test asserting `message_id >= marker` deletion and row-count return.
3. Add an error-wrapping test asserting the dedicated persistence error type and chained cause.
4. Run the validation sequence.

### Method

The grouped variant (session_message_repo.py, seq 02) writes a phase-group in one `begin_immediate` transaction on one connection; the compensation delete (session_message_repo.py, seq 02) deletes `message_id >= marker` rows in one transaction; both wrap `sqlite3.Error` in the dedicated persistence error type (turn_persistence.py, seq 01). Tests exercise each against a temp DB.

```python
# test_session_message_repo.py — grouped / compensation / wrapping tests  (new)
async def test_grouped_variant_commits_atomically():
    ...

async def test_compensation_delete_removes_only_turn_rows():
    ...

async def test_db_error_wrapped_in_persistence_error():
    ...
```

### Details

- **`REQ-005` / `AC-005`:** the grouped-transaction test asserts all-or-none under a single injected failure.
- **`REQ-002` / `AC-002`:** the compensation-delete test asserts only `message_id >= marker` rows are removed.
- **`REQ-003` / `AC-003`:** the error-wrapping test asserts the dedicated persistence error type with `__cause__` set.
- **`AC-008`:** existing save/save_many/replace cases unchanged.

## Compatibility considerations

- Additive; does not modify existing test functions.

## Security considerations

- Temp DB only; no secrets.

## Rollback considerations

- Revert the test-file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| grouped variant | Unit: atomic commit | `uv run pytest tests/agent/test_session_message_repo.py` | All-or-none (`AC-005`) |
| compensation delete | Unit: targeted delete | `uv run pytest tests/agent/test_session_message_repo.py` | Earlier rows retained (`AC-002`) |
| error wrapping | Unit: dedicated type + cause | `uv run pytest tests/agent/test_session_message_repo.py` | `AC-003` |
| backward compat | Regression: existing cases | `uv run pytest tests/agent/test_session_message_repo.py` | Unchanged (`AC-008`) |

## Completion criteria

- Grouped-transaction, compensation-delete, and error-wrapping tests pass; existing cases unchanged; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body (turn_persistence.py, seq 01).
- Facade factory (session.py, seq 03).
- Write-routing callers (orchestrator.py seq 05; llm_turn_runner.py seq 07; tool_round_completion.py seq 08; workflow_engine_adapter.py seq 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend test_session_message_repo.py with grouped/compensation/wrapping tests | Pending | — | — | Extend existing module |
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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-005`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `tests/agent/test_session_message_repo.py`
