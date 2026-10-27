## Goal

Add the `AgentSession.turn_boundary()` (new) facade factory to `scripts/agent/session.py` that materializes one turn-persistence boundary for the turn the orchestrator is about to run (`REQ-001`). It captures the turn-start marker (the largest `message_id` for the session, `0` when the session has no rows yet) and takes a memory snapshot, then constructs and returns the `scripts/agent/turn_persistence.py::TurnPersistence` object (seq 01) that will own every write of the turn.

### Adversarial verification corrections

The implementation deviates from this document's literal pseudo-code in two ways, both required by the corrected boundary design (see seq 01/02 correction notes); pinned by `TestTurnBoundary` in `test_agent_session.py`.

- **`TurnPersistence` constructor takes `(self, conv, marker, snapshot)`, not `(self, marker, snapshot)`.** The boundary needs the live `ConversationState` to restore on failure, so `turn_boundary()` passes `conv` explicitly (seq 01).
- **Compensation operator is `> marker`, not `>= marker`.** The marker is `MAX(message_id)` — the last pre-turn row. `DELETE ... WHERE message_id >= marker` would delete that prior turn's row; the correct compensation is `> marker`. Both `>= marker` mentions below are corrected.

## Scope

- **In-Scope** (`scripts/agent/session.py` only):
  - Add `turn_boundary` (new): an async factory that computes the turn-start `message_id` marker, awaits a `scripts/agent/context.py::snapshot_messages` snapshot (seq 04), and returns TurnPersistence (seq 01) bound to `self` (`REQ-001`).
  - Keep all existing `AgentSession` delegation methods (`save`, `save_many`, `replace_messages`, `save_diagnostic`) unchanged.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The TurnPersistence boundary itself (`scripts/agent/turn_persistence.py`, seq 01).
  - The snapshot_messages / restore_messages API on `ConversationState` (`scripts/agent/context.py`, seq 04).
  - The orchestrator that calls `turn_boundary()` per turn (`scripts/agent/orchestrator.py`, seq 05).

## Assumptions

- `AgentSession` owns `session_id` and the cached `_message_repo` (`SessionMessageRepository`), but NOT the conversation memory — `ConversationState` lives on the orchestrator's `ctx.conv`, so `turn_boundary()` receives `conv` explicitly.
- The turn-start marker is `MAX(message_id)` for the session at turn start (`0` when there are no rows); no schema change is needed (`UNK-02`).
- snapshot_messages (seq 04) returns a defensive copy guarded by `ConversationState`'s async lock, so the boundary holds a stable snapshot even if history mutates during the turn.
- Only the turn path writes `messages` rows for the session during a turn (plan Assumptions; enforced by `AC-001`), so the marker cleanly delimits the turn's rows for compensation.

## Design decisions

- **Factory on the facade, not the orchestrator.** `turn_boundary()` lives on `AgentSession` because that is where `session_id` and the message repo already live; the orchestrator supplies `conv` and the turn lifecycle. This keeps the boundary construction next to the data it reads.
- **Async, because the snapshot is async.** `ConversationState` guards `history` with an `asyncio.Lock` and its mutators are `async`; capturing a consistent snapshot therefore must be awaited, so `turn_boundary()` is `async`.
- **Marker computed, not stored.** The marker is derived from `message_id` at call time; compensation (seq 01/02) deletes `message_id > marker` (strictly greater). No new column (`UNK-02`).

## Alternatives considered

- **Compute the marker + snapshot inline in the orchestrator.** Rejected: `session_id` and the repo are owned by `AgentSession`; putting the factory here keeps the turn-path delegation centralized and matches the existing `save`/`save_many`/`replace_messages` delegation pattern.
- **Reuse `undo_floor` as the turn marker.** Rejected: `undo_floor` is the `/undo` compression boundary (an index into history), not the DB `message_id` turn start; the two diverge after compression. A dedicated `MAX(message_id)` marker is required (`UNK-03`).

## Implementation

### Target file

`scripts/agent/session.py` (existing; extended)

### Procedure

1. Add `async def turn_boundary(self, conv) -> "TurnPersistence"` (new): compute the turn-start marker (`MAX(message_id)` for `self.session_id`, `0` when `None`/absent), await `conv.snapshot_messages()` (seq 04), and `return TurnPersistence(self, marker, snapshot)` (seq 01).
2. Import TurnPersistence (seq 01) at module scope (or lazily inside the method to avoid a cycle).
3. Run the validation sequence.

### Method

`AgentSession` (`scripts/agent/session.py`) is a thin facade over `SessionMessageRepository`: it caches `_message_repo` (session.py:35-43) and delegates `save` (session.py:58-66), `save_many` (session.py:68-73), `replace_messages` (session.py:75-87), and `save_diagnostic` (session.py:89-98). It holds `session_id` (session.py:51) and `_strict_mode`, and exposes NO conversation-memory attribute — `ConversationState` lives on the orchestrator. The closest existing pattern is this delegation facade; `turn_boundary()` extends it with one async factory. `ConversationState.snapshot_messages`/restore_messages (seq 04) guard `history` with the async `_history_lock`.

```python
# session.py — turn boundary factory (REQ-001)  (new)
async def turn_boundary(self, conv) -> "TurnPersistence":   # (new) seq 01, 04
    marker = (
        await self._message_repo.turn_start_marker(self.session_id)
        if self.session_id is not None else 0
    )
    snapshot = await conv.snapshot_messages()                 # seq 04
    return TurnPersistence(self, conv, marker, snapshot)      # seq 01
```

### Details

- **`REQ-001` (one boundary per turn):** the orchestrator (seq 05) calls `turn_boundary(ctx.conv)` once at turn start; the returned object is the sole writer for the turn.
- **Marker (`UNK-02`):** `MAX(message_id)` for the session, `0` when fresh; compensation (seq 01/02) deletes `message_id > marker` (strictly greater — the marker is the last pre-turn row, so `>= marker` would wrongly delete it). The exact marker-read helper (turn_start_marker shown as a placeholder) is a Phase 1 design detail — any equivalent `MAX(message_id)` read is acceptable.
- **Snapshot (seq 04):** `await conv.snapshot_messages()` returns a lock-guarded copy; the boundary restores it on failure so memory equals the turn-start state (`AC-004`).
- **Backward compatibility:** no existing method changes; turn_boundary is purely additive (13 importers of `AgentSession` are unaffected).

## Compatibility considerations

- New async method; the only caller is the orchestrator (seq 05). Existing `AgentSession` consumers see no change.
- TurnPersistence (seq 01) is imported by this module; import ordering must avoid a cycle between `session.py` and `turn_persistence.py` (forward string annotation + lazy import if needed).

## Security considerations

- No new input surface. The marker is derived from the session's own `message_id`; `conv` is supplied by the trusted orchestrator.

## Rollback considerations

- Revert the `session.py` edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `turn_boundary()` | Unit: marker + snapshot + returned boundary type | `uv run pytest tests/agent/test_agent_session.py` | Returns TurnPersistence; fresh-session marker = 0 |
| backward compat | Regression: existing facade cases | `uv run pytest tests/agent/test_agent_session.py` | Unchanged |
| static | ruff / mypy / bandit / vulture | `uv run ruff check scripts/`; `uv run mypy scripts/`; `uv run bandit -r scripts/ -c pyproject.toml`; `uv run vulture scripts/` | Clean |

## Completion criteria

- `turn_boundary()` (new) is an async factory that captures the turn-start `message_id` marker (`0` when fresh), awaits a memory snapshot, and returns a TurnPersistence (seq 01) bound to the session.
- All existing `AgentSession` delegation methods pass unchanged; ruff/mypy/bandit/vulture clean.

## Out of Scope

- TurnPersistence body (`scripts/agent/turn_persistence.py`, seq 01).
- snapshot_messages/restore_messages (`scripts/agent/context.py`, seq 04).
- Orchestrator wiring (`scripts/agent/orchestrator.py`, seq 05).
- `/undo` interaction (`UNK-03`) — the marker is a raw `MAX(message_id)`, independent of `undo_floor`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `turn_boundary()` facade factory in `scripts/agent/session.py` | Complete | 2026-10-27 | 2026-10-27 | New async factory |
| 2 | Add or update tests per Validation plan | Complete | 2026-10-27 | 2026-10-27 | Extend `tests/agent/test_agent_session.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Complete | 2026-10-27 | 2026-10-27 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Complete | 2026-10-27 | 2026-10-27 | N/A |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `scripts/agent/session.py`
