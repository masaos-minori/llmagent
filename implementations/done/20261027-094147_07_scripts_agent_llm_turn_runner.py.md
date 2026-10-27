## Goal

Route the per-round assistant tool-call persistence in `scripts/agent/llm_turn_runner.py` through the atomic turn-persistence boundary instead of committing it with a standalone `session.save` (`REQ-001`, `REQ-005`). The per-round separate commit is explicitly called out as one of the partial-write sources this Plan removes; persisting the assistant row through the boundary makes each round's write part of the turn's all-or-nothing unit.

## Scope

- **In-Scope** (`scripts/agent/llm_turn_runner.py` only):
  - In `run`, replace the standalone `ctx.session.save("assistant", ...)` (llm_turn_runner.py:107) with a boundary-routed persist of the same assistant tool-call row (`REQ-005`).
  - Preserve the memory append (`ctx.conv.append_message`) and all tool-execution/stats logic unchanged.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The turn-persistence boundary and its handle (turn_persistence.py, seq 01; orchestrator.py, seq 05).
  - The transaction-grouped repository variant (session_message_repo.py, seq 02).
  - Tool-result grouping in tool_round_completion.py (seq 08).

## Assumptions

- The turn's boundary handle (seq 05) is reachable from the runner as `self._ctx.turn.persistence_boundary`.
- Only the turn path writes `messages` rows during a turn (`AC-001`), so routing the assistant row through the boundary makes the round atomic with the rest of the turn.

## Design decisions

- **Persist the assistant row via the boundary, keep memory append as-is.** The in-memory `conv.append_message` stays (memory and DB must both advance); only the DB persistence target moves to the boundary, so a failed later round compensates this row too (`AC-002`).
- **No change to the guard/tool-execution flow.** The runner's tool-call guards, stats deltas, and error handling are untouched; only the persistence call site changes.

## Alternatives considered

- **Group the assistant row with its tool results in one write.** Rejected: the assistant row is persisted before tool execution (results are unknown yet); grouping happens at round completion (seq 08) for the tool-result rows, while the assistant row joins the turn unit via the boundary here.

## Implementation

### Target file

`scripts/agent/llm_turn_runner.py` (existing; extended)

### Procedure

1. In `run` (llm_turn_runner.py:62), locate the per-round persist at llm_turn_runner.py:106-111 (`await ctx.conv.append_message(message)` followed by `ctx.session.save("assistant", ...)`).
2. Replace the `ctx.session.save("assistant", ...)` (llm_turn_runner.py:107) with a boundary-routed persist of the same role/content/tool_calls through the turn boundary handle (seq 05).
3. Run the validation sequence.

### Method

`LLMTurnRunner` (llm_turn_runner.py:40) drives one turn's LLM/tool loop. `run` (llm_turn_runner.py:62) iterates `ctx.cfg.tool.max_tool_turns`; for each tool-calling response it awaits `_stream_llm`, checks guards, then at llm_turn_runner.py:106-113 does `await ctx.conv.append_message(message)` and persists the assistant row through the boundary via `await ctx.turn.persistence_boundary.save("assistant", message.get("content") or "", tool_calls=message.get("tool_calls"))` before executing the tool calls. The boundary handle (seq 05) provides the same insert with turn-level all-or-nothing semantics. A missing boundary (`persistence_boundary is None` outside a turn) is a programming error caught by an `assert ... is not None` guard.

```python
# llm_turn_runner.py — routed assistant persist (REQ-005)  (new)
await ctx.conv.append_message(message)
boundary = ctx.turn.persistence_boundary   # TurnPersistence | None
assert boundary is not None, "persistence boundary not set for this turn"  # noqa: B101
await boundary.save(
    "assistant",
    message.get("content") or "",
    tool_calls=message.get("tool_calls"),
)
```

### Details

- **`REQ-001` (one writer per turn):** the assistant row now goes through the turn boundary (seq 05); no standalone commit remains in the round path (`AC-001`).
- **`REQ-005` (atomic round):** a failure in a later round compensates this assistant row via the boundary's `message_id >= marker` delete (seq 01/02).
- **Backward compatibility:** memory append, guards, stats, and error handling are unchanged; only the DB persistence target moves.

## Compatibility considerations

- Additive; no signature changes. Depends on the boundary handle existing on the turn context (seq 05).

## Security considerations

- No new input surface; the inserted row carries the same role/content/tool_calls as before.

## Rollback considerations

- Revert the `llm_turn_runner.py` edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| assistant routed | Unit: assistant row persisted via boundary | `uv run pytest tests/agent/test_llm_turn_runner.py` | Row present; no standalone save |
| round atomicity | Failure injection: failed round leaves no partial rows | `uv run pytest tests/agent/test_llm_turn_runner.py` | Compensated (`AC-002`) |
| backward compat | Regression: existing runner cases | `uv run pytest tests/agent/test_llm_turn_runner.py` | Unchanged |
| static | ruff / mypy / bandit / vulture | `uv run ruff check scripts/`; `uv run mypy scripts/`; `uv run bandit -r scripts/ -c pyproject.toml`; `uv run vulture scripts/` | Clean |

## Completion criteria

- The per-round assistant row is persisted through the turn boundary handle instead of a standalone `session.save`.
- Runner regression tests pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body (turn_persistence.py, seq 01).
- Orchestrator boundary creation (orchestrator.py, seq 05).
- Tool-result grouping (tool_round_completion.py, seq 08).
- Repository grouping (session_message_repo.py, seq 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route assistant persist through boundary in `scripts/agent/llm_turn_runner.py` | Complete | 2026-10-27 | 2026-10-27 | Replaces standalone save; `ctx.session.save` → `await ctx.turn.persistence_boundary.save(...)`; assert guard for mypy narrowing |
| 2 | Add or update tests per Validation plan | Complete | 2026-10-27 | 2026-10-27 | Awaitable boundary wired into `_make_ctx` (test_llm_turn_runner), `_ctx` (test_tool_loop_guard_wiring), `_make_turn_ctx` (test_rag_turn_integration); assert boundary.save awaited once with assistant row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Complete | 2026-10-27 | 2026-10-27 | ruff check/format clean, mypy clean, lint-imports 6/6, bandit full gate exit 0 (Low only), vulture @80 unchanged vs baseline; 192 turn-flow tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Complete | 2026-10-27 | 2026-10-27 | Corrected pseudo-code (save() not append_assistant()); method + execution-status updated |

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
- **Related target files**: `scripts/agent/llm_turn_runner.py`
