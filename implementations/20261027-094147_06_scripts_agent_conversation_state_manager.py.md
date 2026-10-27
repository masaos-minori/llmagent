## Goal

Route the conversation-state manager's turn-path DB writes through the atomic turn-persistence boundary instead of committing each write independently (`REQ-001`, `REQ-005`, `REQ-006`). `conversation_state_manager.py` currently appends memory then calls `session.save` / `session.replace_messages` per operation; this row keeps the memory-mutation semantics identical but persists through the boundary handle owned by the turn (created by the orchestrator, seq 05), so a failure anywhere in the turn is compensated atomically.

## Scope

- **In-Scope** (`scripts/agent/conversation_state_manager.py` only):
  - In `append_user_message`, persist the user row through the boundary handle instead of a standalone `save` (`REQ-005`).
  - In `handle_history_compression`, persist the compressed snapshot through the boundary handle instead of a standalone `replace_messages`, leaving `undo_floor` semantics intact (`REQ-006`).
  - Preserve all existing memory-mutation behavior (`conv.append_message`, `conv.extend_messages`, `undo_floor` assignment).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The turn-persistence boundary and its handle (turn_persistence.py, seq 01; exposed on the turn context as persistence_boundary by orchestrator.py, seq 05).
  - The transaction-grouped repository variant (`scripts/agent/session_message_repo.py`, seq 02).
  - Memory snapshot/restore (`scripts/agent/context.py`, seq 04).

## Assumptions

- The orchestrator (seq 05) creates one boundary per turn and exposes it on the turn context as persistence_boundary (new, orchestrator.py seq 05), reachable here as self._ctx.turn.persistence_boundary.
- Only the turn path writes `messages` rows during a turn (`AC-001`), so routing through the boundary handle is sufficient to make every turn-path write part of the all-or-nothing unit.
- `replace_messages` (used by compression) keeps its atomic DELETE + INSERT + `undo_floor_message_id` update; the boundary groups it with the turn rather than changing its internals (`UNK-03`).

## Design decisions

- **Reuse the existing repo methods via the boundary, do not fork them.** The boundary already owns the reused connection and per-phase transactions (seq 01/02); this row simply directs the manager's writes at the boundary instead of at `session` directly, avoiding a second persistence code path.
- **Compression stays a boundary call, not a bypass.** Compression is a legitimate turn-path write; routing it through the boundary means a mid-turn compression failure is compensated like any other (`AC-006`), while `/undo` boundaries (`undo_floor`) are untouched.

## Alternatives considered

- **Add a dedicated manager-level persist helper.** Rejected: it would duplicate the boundary's connection/transaction ownership and risk diverging from the all-or-nothing contract; the boundary is the single writer (seq 01).

## Implementation

### Target file

`scripts/agent/conversation_state_manager.py` (existing; extended)

### Procedure

1. In `append_user_message` (conversation_state_manager.py:106), replace the standalone `ctx.session.save("user", line)` (conversation_state_manager.py:119) with a boundary-routed persist of the same user row.
2. In `handle_history_compression` (conversation_state_manager.py:148), replace `ctx.session.replace_messages(ctx.conv.history)` (conversation_state_manager.py:161) with a boundary-routed persist of the compressed snapshot; keep the `undo_floor` assignment unchanged.
3. Run the validation sequence.

### Method

`ConversationStateManager` (conversation_state_manager.py:36) owns turn-memory bookkeeping. `append_user_message` (conversation_state_manager.py:106) syncs the system prompt, awaits `ctx.conv.append_message` (conversation_state_manager.py:110), increments `stat_turns`, and persists the user row via `ctx.session.save("user", line)` (conversation_state_manager.py:119). `handle_history_compression` (conversation_state_manager.py:148) compresses `ctx.conv.history` and, when `compressed_count > 0`, persists via `ctx.session.replace_messages(ctx.conv.history)` (conversation_state_manager.py:161) and sets `conv.undo_floor`. The boundary handle (seq 05) provides the same persistence with turn-level all-or-nothing semantics.

```python
# conversation_state_manager.py — routed user persist (REQ-005)  (new)
async def append_user_message(self, line: str) -> None:
    ctx = self._ctx
    self.sync_system_prompt()
    await ctx.conv.append_message({"role": "user", "content": line})
    ctx.stats.stat_turns += 1
    ...
    await self._ctx.turn.persistence_boundary.append_user(line)   # seq 05, 01

# conversation_state_manager.py — routed compression persist (REQ-006)  (new)
async def handle_history_compression(self) -> None:
    ctx = self._ctx
    if ctx.services_required.hist_mgr is not None:
        ctx.conv.history, result = await ctx.services_required.hist_mgr.compress(
            ctx.conv.history
        )
        if result.compressed_count > 0:
            await self._ctx.turn.persistence_boundary.compress_snapshot(  # seq 05, 01
                ctx.conv.history
            )
            ctx.conv.undo_floor = len(ctx.conv.history)
```

### Details

- **`REQ-001` (one writer per turn):** both writes go through the turn's boundary handle (seq 05), so the manager no longer opens independent commits; `AC-001` holds.
- **`REQ-005` (grouped round):** the boundary groups the user/compression writes with the turn's phase transactions (seq 01/02).
- **`REQ-006` / `UNK-03` (compression + `/undo` untouched):** `replace_messages` internals are unchanged; only the caller moves from `ctx.session` to the boundary, and `undo_floor` is still set immediately after.
- **Backward compatibility:** memory-mutation calls (`conv.append_message`, `undo_floor`) are unchanged; only the persistence target changes.

## Compatibility considerations

- Additive routing change; no signature changes to public methods.
- Depends on the boundary handle existing on the turn context (seq 05); callers outside a turn are unaffected.

## Security considerations

- No new input surface; writes carry the same session binding as before.

## Rollback considerations

- Revert the `conversation_state_manager.py` edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| user append routed | Unit: user row persisted via boundary | `uv run pytest tests/agent/test_history_compression_consistency.py` | Row present; memory consistent |
| compression routed | Regression: compression consistency | `uv run pytest tests/agent/test_history_compression_consistency.py` | `undo_floor` + rows consistent (`AC-006`) |
| backward compat | Regression: existing manager cases | `uv run pytest tests/agent/test_history_compression_consistency.py` | Unchanged |
| static | ruff / mypy / bandit / vulture | `uv run ruff check scripts/`; `uv run mypy scripts/`; `uv run bandit -r scripts/ -c pyproject.toml`; `uv run vulture scripts/` | Clean |

## Completion criteria

- `append_user_message` and `handle_history_compression` persist through the turn boundary handle instead of standalone `session.save`/`session.replace_messages`.
- Memory-mutation semantics and `undo_floor` behavior unchanged; compression-consistency tests pass; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary body (`scripts/agent/turn_persistence.py`, seq 01).
- Orchestrator boundary creation (`scripts/agent/orchestrator.py`, seq 05).
- Repository grouping (`scripts/agent/session_message_repo.py`, seq 02).
- Memory snapshot/restore (`scripts/agent/context.py`, seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route manager writes through the boundary in `scripts/agent/conversation_state_manager.py` | Pending | — | — | Extends append/compression |
| 2 | Add or update tests per Validation plan | Pending | — | — | Extend `tests/agent/test_history_compression_consistency.py` |
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
- **Requirement ID**: `REQ-001`, `REQ-005`, `REQ-006`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `scripts/agent/conversation_state_manager.py`
