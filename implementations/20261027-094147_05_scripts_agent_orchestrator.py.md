## Goal

Wire the atomic turn-persistence boundary into the turn lifecycle in `scripts/agent/orchestrator.py` (`REQ-001`, `REQ-004`). The orchestrator owns the turn lifecycle; this row creates one TurnPersistence boundary per turn, exposes it to the write-routing callers in this Plan, and adds an ConversationPersistenceError branch to `_execute_turn` so a compensated persistence failure surfaces to the REPL distinctly instead of being swallowed by the generic handler.

## Scope

- **In-Scope** (`scripts/agent/orchestrator.py` only):
  - Create the TurnPersistence boundary (seq 01) at turn start via the `AgentSession.turn_boundary` factory (seq 03), bound to `self._ctx.session` and `self._ctx.conv`; store it on the turn context so write-routing callers (seq 06-09) can access it.
  - Add an `except ConversationPersistenceError` clause to `_execute_turn`, placed before the existing `except BaseException`, that lets the boundary's fail_from_error perform compensation + memory restore and then re-raises (`REQ-001`, `REQ-004`).
  - Import ConversationPersistenceError (seq 01) at module scope.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The TurnPersistence boundary body (`scripts/agent/turn_persistence.py`, seq 01).
  - The turn_boundary facade factory (`scripts/agent/session.py`, seq 03).
  - Write-routing callers that consume the boundary handle (`scripts/agent/conversation_state_manager.py`, seq 06; `scripts/agent/llm_turn_runner.py`, seq 07; `scripts/agent/tool_round_completion.py`, seq 08; `scripts/agent/workflow_engine_adapter.py`, seq 09).

## Assumptions

- `AgentContext` (`scripts/agent/context.py`) holds `conv` (`ConversationState`) and `session` (`AgentSession`) as construction-time attributes, so the orchestrator reaches both via `self._ctx`.
- The orchestrator's single-threaded async model means the boundary created at turn start is the sole writer for that turn (`AC-001`), enforced by the write-routing rows (seq 06-09).
- ConversationPersistenceError (seq 01) is raised by the boundary's fail_from_error after it has already compensated and restored; the orchestrator does not compensate again.

## Design decisions

- **Boundary created once per turn, exposed via the turn context.** Creating the boundary in `_execute_turn` (not deep in the adapter/runner) keeps turn-lifecycle ownership in one place; exposing it on the turn context gives the write-routing callers a single handle without threading a parameter through every stage method (Phase 1 threading detail, `UNK-01`).
- **Narrow exception branch before the generic handler.** The existing `except BaseException` at `_execute_turn` captures `error_kind` and re-raises; a narrower ConversationPersistenceError branch ahead of it records a distinct `error_kind` ("persistence") and re-raises so downstream surfacing (`scripts/agent/repl_input_loop.py`, seq 10) can special-case it (`REQ-007`).

## Alternatives considered

- **Create the boundary inside the workflow adapter.** Rejected: the adapter drives rounds, not the turn; the turn-start marker and pre-turn snapshot belong to the turn boundary, which the orchestrator owns. Keeping creation here matches the existing per-turn try/finally structure.
- **Let `BaseException` handle persistence errors inline.** Rejected: it cannot distinguish a compensated persistence failure from other turn errors, defeating `REQ-007`.

## Implementation

### Target file

`scripts/agent/orchestrator.py` (existing; extended)

### Procedure

1. Import ConversationPersistenceError (seq 01) at module scope.
2. In `_execute_turn` (orchestrator.py:164), before the `try` at orchestrator.py:169, create the boundary: `boundary = await self._ctx.session.turn_boundary(self._ctx.conv)` (seq 03) and attach it to the turn context so callers can reach it.
3. Add `except ConversationPersistenceError:` before `except BaseException as exc:` (orchestrator.py:174): set a distinct `error_kind`, rely on the boundary's fail_from_error for compensation + restore, and `raise`.
4. Run the validation sequence.

### Method

`Orchestrator` (orchestrator.py:55) is a composition facade; its `__init__` (orchestrator.py:66) stores `self._ctx = ctx` (orchestrator.py:81) where `ctx` is an `AgentContext` holding `conv` and `session`. `_execute_turn` (orchestrator.py:164) wraps the workflow adapter call in a `try` (orchestrator.py:169) with an `except BaseException` (orchestrator.py:174) that records `error_kind` and re-raises, and a `finally` (orchestrator.py:178) that emits audit events and deactivates the workflow. The boundary is created at the top of that `try` and the narrow exception branch sits ahead of orchestrator.py:174. `AgentContext` (`scripts/agent/context.py`) exposes `conv` (`scripts/agent/context.py`) and `session` (`scripts/agent/context.py`) as attributes.

```python
# orchestrator.py — turn persistence boundary (REQ-001, REQ-004)  (new)
async def _execute_turn(self, line: str) -> None:
    answer: str = ""
    error_kind: str | None = None
    is_partial: bool = False
    turn_started_at = time.perf_counter()
    boundary = None
    try:
        await self._audit_emitter.emit_turn_start()
        boundary = await self._ctx.session.turn_boundary(self._ctx.conv)  # seq 03
        self._ctx.turn.persistence_boundary = boundary                    # expose to seq 06-09
        answer, error_kind, is_partial = await self._workflow_adapter.execute_turn(
            line, turn_started_at, ""
        )
    except ConversationPersistenceError:                                 # (new) seq 01, 04
        # boundary.fail_from_error() already compensated + restored history
        error_kind = "persistence"
        is_partial = bool(getattr(boundary, "_partial", ""))
        raise
    except BaseException as exc:
        error_kind = exc.__class__.__name__
        is_partial = bool(getattr(exc, "partial_text", ""))
        raise
    finally:
        ...
```

### Details

- **`REQ-001` (one boundary per turn):** `turn_boundary(self._ctx.conv)` (seq 03) captures the turn-start `message_id` marker and a memory snapshot, returning a TurnPersistence (seq 01) that is the sole writer for the turn; the write-routing rows (seq 06-09) route all writes through it.
- **`REQ-004` (memory == DB after compensation):** on a persistence failure the boundary's fail_from_error restores `ConversationState.history` to the turn-start snapshot; the orchestrator re-raises so this is observable end-to-end.
- **`REQ-007` (distinct surfacing):** the narrow branch sets `error_kind = "persistence"` before re-raising, letting the REPL (seq 10) surface a dedicated message.
- **Backward compatibility:** purely additive; the new `persistence_boundary` (new) attribute on the turn context defaults away when no turn is running.

## Compatibility considerations

- New import and one new attribute on the turn-context object; existing `Orchestrator` consumers see no signature change.
- The ConversationPersistenceError branch must precede the `except BaseException` branch, else the broad handler catches it first.

## Security considerations

- No new input surface. The boundary is created from trusted turn context; no attacker-controlled value flows into it.

## Rollback considerations

- Revert the `orchestrator.py` edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| boundary created per turn | Unit: turn_boundary returns boundary; exposed on turn context | `uv run pytest tests/agent/test_orchestrator.py` | Boundary present; fresh marker = 0 |
| persistence failure path | Failure injection: compensation + restore + re-raise | `uv run pytest tests/agent/test_orchestrator.py` | ConversationPersistenceError re-raised; memory restored (`AC-004`) |
| backward compat | Regression: existing turn tests | `uv run pytest tests/agent/test_orchestrator.py` | Unchanged |
| static | ruff / mypy / bandit / vulture | `uv run ruff check scripts/`; `uv run mypy scripts/`; `uv run bandit -r scripts/ -c pyproject.toml`; `uv run vulture scripts/` | Clean |

## Completion criteria

- A TurnPersistence (seq 01) boundary is created per turn via turn_boundary (seq 03) and exposed to write-routing callers.
- `_execute_turn` has an `except ConversationPersistenceError` branch ahead of the `except BaseException` branch that re-raises after the boundary compensates + restores.
- Existing orchestrator turn tests pass unchanged; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body (`scripts/agent/turn_persistence.py`, seq 01).
- turn_boundary factory (`scripts/agent/session.py`, seq 03).
- Write-routing callers (seq 06-09).
- REPL surfacing (`scripts/agent/repl_input_loop.py`, seq 10) — the distinct `error_kind` feeds it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Wire TurnPersistence boundary + ConversationPersistenceError branch in `scripts/agent/orchestrator.py` | Pending | — | — | Extends `_execute_turn` |
| 2 | Add or update tests per Validation plan | Pending | — | — | Extend `tests/agent/test_orchestrator.py` |
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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `scripts/agent/orchestrator.py`
