## Goal

Route the tool-result persistence in `scripts/agent/tool_round_completion.py` through the atomic turn-persistence boundary, grouped in a single phase transaction with the round's assistant message (`REQ-001`, `REQ-005`). Currently `complete_round` persists tool results with a standalone `save_many` that commits separately from the assistant save moments earlier; grouping them through the boundary makes the round's assistant + tool-result rows land atomically (`AC-005`).

## Scope

- **In-Scope** (`scripts/agent/tool_round_completion.py` only):
  - In `complete_round`, replace the standalone `ctx.session.save_many(tool_msgs)` (tool_round_completion.py:82) with a boundary-routed, single-transaction persist of the round's tool-result rows (`REQ-005`).
  - Preserve `_merge_in_declared_order`, `build_denied_messages`, `pair_round_results`, and the `conv.extend_messages` memory append unchanged.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The assistant-row persist in llm_turn_runner.py (seq 07).
  - The transaction-grouped repository variant (session_message_repo.py, seq 02).
  - The boundary body and handle (turn_persistence.py, seq 01; orchestrator.py, seq 05).

## Assumptions

- The turn's boundary handle (seq 05) exposes a grouped/atomic persist method that writes a whole round's rows in one `begin_immediate` transaction on one connection (session_message_repo.py, seq 02).
- The round's assistant row was already persisted via the boundary in llm_turn_runner.py (seq 07); this row groups the tool-result rows with it so the round is atomic.

## Design decisions

- **One grouped transaction for the whole round.** The boundary's grouped variant (seq 02) runs the round's assistant + tool-result rows under a single IMMEDIATE lock on one connection, so a single injected failure leaves either all or none of the round's rows (`AC-005`, `UNK-01`).
- **Keep memory append where it is.** `conv.extend_messages` stays as the memory advance; only the DB persistence moves to the boundary.

## Alternatives considered

- **Reuse `save_many` directly.** Rejected: `save_many` opens its own default-mode connection and cannot hold one IMMEDIATE lock across the round; the grouped boundary variant (seq 02) is required for `AC-005`.

## Implementation

### Target file

`scripts/agent/tool_round_completion.py` (existing; extended)

### Procedure

1. In `complete_round` (tool_round_completion.py:55), locate the tool-result persist at tool_round_completion.py:80-82 (`await ctx.conv.extend_messages([...])`, `tool_msgs.extend([...])`, `ctx.session.save_many(tool_msgs)`).
2. Replace `ctx.session.save_many(tool_msgs)` (tool_round_completion.py:82) with a boundary-routed grouped persist through the turn boundary handle (seq 05).
3. Run the validation sequence.

### Method

`complete_round` (tool_round_completion.py:55) takes `ctx`, `state`, `tool_calls`, `turn`, `out_failed_keys`, `reason`. It merges results (`_merge_in_declared_order`, tool_round_completion.py:71), collects tool messages (tool_round_completion.py:74), builds denied/pair messages (tool_round_completion.py:75-79), appends memory via `await ctx.conv.extend_messages([...])` (tool_round_completion.py:80), extends the message tuples (tool_round_completion.py:81), and persists via `ctx.session.save_many(tool_msgs)` (tool_round_completion.py:82). The boundary's grouped variant (seq 02) writes the same rows in one transaction.

```python
# tool_round_completion.py — grouped tool-result persist (REQ-005)  (new)
await ctx.conv.extend_messages([*denied_history, *pair_history])
tool_msgs.extend([*denied_msgs, *pair_msgs])
await self._ctx.turn.persistence_boundary.save_tool_results(   # seq 05, 01
    tool_msgs
)
```

### Details

- **`REQ-005` / `AC-005` (grouped atomic round):** the boundary's grouped variant (seq 02) writes the round's tool-result rows in one `begin_immediate` transaction on one connection; a single injected failure leaves either all or none.
- **`REQ-001` (one writer per turn):** no standalone `save_many` commit remains in the round path (`AC-001`).
- **Backward compatibility:** result merging, denied/pair handling, and the memory append are unchanged; only the DB persistence target moves.

## Compatibility considerations

- Additive; no signature changes to `complete_round`. Depends on the boundary handle's grouped persist (seq 02) existing on the turn context (seq 05).

## Security considerations

- No new input surface; the inserted rows carry the same content as before.

## Rollback considerations

- Revert the `tool_round_completion.py` edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| tool-results routed | Unit: tool rows persisted via boundary | `uv run pytest tests/agent/test_tool_round_completion.py` | Rows present; no standalone save_many |
| round atomicity | Failure injection: all-or-none round | `uv run pytest tests/agent/test_tool_round_completion.py` | Either all round rows or none (`AC-005`) |
| backward compat | Regression: existing completion cases | `uv run pytest tests/agent/test_tool_round_completion.py` | Unchanged |
| static | ruff / mypy / bandit / vulture | `uv run ruff check scripts/`; `uv run mypy scripts/`; `uv run bandit -r scripts/ -c pyproject.toml`; `uv run vulture scripts/` | Clean |

## Completion criteria

- `complete_round` persists tool results through the boundary's grouped variant instead of a standalone `save_many`.
- Completion regression tests pass; round atomicity holds; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Assistant-row persist (llm_turn_runner.py, seq 07).
- Boundary body (turn_persistence.py, seq 01).
- Orchestrator boundary creation (orchestrator.py, seq 05).
- Repository grouping (session_message_repo.py, seq 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route tool-result persist through boundary in `scripts/agent/tool_round_completion.py` | Pending | — | — | Replaces save_many at L82 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Update `tests/agent/test_tool_round_completion.py` |
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
- **Requirement ID**: `REQ-001`, `REQ-005`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `scripts/agent/tool_round_completion.py`
