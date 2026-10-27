## Goal

Route the final-assistant persistence in `scripts/agent/workflow_engine_adapter.py` through the atomic turn-persistence boundary instead of committing it with a standalone `session.save` (`REQ-001`, `REQ-005`). The final-answer save is described as the last independent commit of the turn; persisting it through the boundary makes it part of the turn's all-or-nothing unit so a later compensation cannot leave a dangling final answer.

## Scope

- **In-Scope** (`scripts/agent/workflow_engine_adapter.py` only):
  - In `_run_execute_stage`, replace the standalone `ctx.session.save("assistant", answer)` (workflow_engine_adapter.py:358) with a boundary-routed persist of the final assistant answer (`REQ-005`).
  - Preserve the action/error classification and `audit_stage_completed` call unchanged.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The assistant-row persist in llm_turn_runner.py (seq 07).
  - The transaction-grouped repository variant (session_message_repo.py, seq 02).
  - The boundary body and handle (turn_persistence.py, seq 01; orchestrator.py, seq 05).

## Assumptions

- The turn's boundary handle (seq 05) is reachable from the adapter as `ctx.turn.persistence_boundary` (`_run_execute_stage` takes `ctx` as a parameter, not `self`).
- Only the turn path writes `messages` rows during a turn (`AC-001`).

## Design decisions

- **Persist the final answer via the boundary, keep classification as-is.** The `result.action` / `error_kind` / `is_partial` classification and the audit stage event stay unchanged; only the DB persistence target moves to the boundary, so the final answer participates in turn-level all-or-nothing.

## Alternatives considered

- **Move the persist to turn exit.** Rejected: the answer is produced inside `_run_execute_stage`; persisting there (rather than at turn exit) preserves the existing per-attempt semantics while still routing through the boundary.

## Implementation

### Target file

`scripts/agent/workflow_engine_adapter.py` (existing; extended)

### Procedure

1. In `_run_execute_stage` (workflow_engine_adapter.py:326), locate the final-assistant persist at workflow_engine_adapter.py:357-362 (`elif result.persist_as_assistant:` then the boundary-routed save).
2. Replace `ctx.session.save("assistant", answer)` (workflow_engine_adapter.py:359, original) with `await ctx.turn.persistence_boundary.save("assistant", answer)` guarded by `assert boundary is not None` (seq 05).
3. Run the validation sequence.

### Method

`WorkflowEngineAdapter` (workflow_engine_adapter.py:65) adapts the workflow engine to turn execution. `execute_turn` (workflow_engine_adapter.py:148) plans/executes/verifies via staged functions; `_run_execute_stage` (workflow_engine_adapter.py:326) runs one execute-stage attempt, classifies the result, and at workflow_engine_adapter.py:357-362 does `elif result.persist_as_assistant:` then persists via the turn boundary before returning `(answer, error_kind, is_partial)`. The boundary handle (seq 05) provides the same insert with turn-level all-or-nothing semantics.

```python
# workflow_engine_adapter.py — routed final-assistant persist (REQ-005)  (new)
elif result.persist_as_assistant:
    boundary = ctx.turn.persistence_boundary   # TurnPersistence | None
    assert boundary is not None, "persistence boundary not set for this turn"  # noqa: B101
    await boundary.save("assistant", answer)
```

### Details

- **`REQ-001` (one writer per turn):** the final answer now goes through the turn boundary (seq 05); no standalone commit remains in the execute stage (`AC-001`).
- **`REQ-005` (atomic turn):** a later failure compensates the final answer via the boundary's `message_id >= marker` delete (seq 01/02).
- **Backward compatibility:** classification, partial handling, and the audit stage event are unchanged; only the DB persistence target moves.

## Compatibility considerations

- Additive; no signature changes. Depends on the boundary handle existing on the turn context (seq 05).

## Security considerations

- No new input surface; the inserted row carries the same answer content as before.

## Rollback considerations

- Revert the `workflow_engine_adapter.py` edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| final answer routed | Unit: answer persisted via boundary | `uv run pytest tests/agent/test_orchestrator.py::TestHandleTurnLLMTransportError::test_success_still_saved_as_assistant_message` | Assistant row present on `ctx.turn.persistence_boundary.save`; no standalone save |
| turn atomicity | Failure injection: final answer compensated | `uv run pytest tests/integration/test_orchestrator_integration.py::TestCompleteTurnExecution::test_handle_turn_saves_assistant_message_on_success` | Compensated (`AC-002`) |
| backward compat | Regression: existing workflow cases | `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py` | Unchanged |
| static | ruff / mypy / bandit / vulture | `uv run ruff check scripts/`; `uv run mypy scripts/`; `uv run bandit -r scripts/ -c pyproject.toml`; `uv run vulture scripts/` | Clean |

## Completion criteria

- The final-assistant answer is persisted through the turn boundary handle instead of a standalone `session.save`.
- Workflow regression tests pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Assistant-row persist (llm_turn_runner.py, seq 07).
- Boundary body (turn_persistence.py, seq 01).
- Orchestrator boundary creation (orchestrator.py, seq 05).
- Repository grouping (session_message_repo.py, seq 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route final-assistant persist through boundary in `scripts/agent/workflow_engine_adapter.py` | Complete | 2026-10-27 | 2026-10-27 | `ctx.session.save("assistant", answer)` -> `await ctx.turn.persistence_boundary.save("assistant", answer)` + assert guard; L359->L362 |
| 2 | Add or update tests per Validation plan | Complete | 2026-10-27 | 2026-10-27 | Updated `test_success_still_saved_as_assistant_message` (test_orchestrator.py) and `test_handle_turn_saves_assistant_message_on_success` (test_orchestrator_integration.py) to assert the assistant row on `ctx.turn.persistence_boundary.save` (the boundary also persists the user row first) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Complete | 2026-10-27 | 2026-10-27 | ruff check/format clean, mypy clean, bandit full gate exit 0 (High=0), vulture @80 clean; 3871 agent+integration tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Complete | 2026-10-27 | 2026-10-27 | Corrected handle (`self._ctx` -> `ctx.turn`), method (`persist_final_answer` -> `save`), pseudocode, Validation plan, Execution Status to match implementation |

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
- **Requirement ID**: `REQ-001`, `REQ-005`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`
