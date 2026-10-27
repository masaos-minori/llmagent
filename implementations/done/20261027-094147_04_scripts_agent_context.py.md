## Goal

Add `snapshot_messages` (new) (new) and `restore_messages` (new) (new) to `ConversationState` in `scripts/agent/context.py` so the turn-persistence boundary (seq 01) can capture a stable turn-start memory image and, on a compensated failure, restore history to exactly that image (`REQ-004`). Both methods follow the existing async, `_history_lock`-guarded access pattern used by `append_message`/`extend_messages`/`replace_history`.

## Scope

- **In-Scope** (`scripts/agent/context.py` only):
  - Add `snapshot_messages` (new) (new): return a defensive deep-ish copy of `ConversationState.history` under the async lock.
  - Add `restore_messages` (new) (new): replace `history` element-wise with a previously captured snapshot under the async lock.
  - Preserve all existing `ConversationState` fields and methods (`append_message`, `extend_messages`, `replace_history`, `undo_floor`, sanitization behavior).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The TurnPersistence boundary that takes/restores the snapshot (`scripts/agent/turn_persistence.py`, seq 01).
  - Callers that route writes through the boundary (`scripts/agent/orchestrator.py`, seq 05; `scripts/agent/conversation_state_manager.py`, seq 06; `scripts/agent/llm_turn_runner.py`, seq 07; `scripts/agent/tool_round_completion.py`, seq 08; `scripts/agent/workflow_engine_adapter.py`, seq 09).

## Assumptions

- `ConversationState.history` (`context.py:L100`) is the single source of truth for turn memory; `snapshot_messages` (new)/`restore_messages` (new) operate on it.
- History access is serialized by the async `_history_lock` (`context.py:L99`) via the `_ensure_lock` property (`context.py:L118-122`); snapshots/restores must hold that same lock.
- The orchestrator's single-threaded async model means coroutines interleave only at `await` points, so holding the lock across the copy/extend is sufficient for consistency.
- TurnPersistence (seq 01) holds the snapshot for the turn's lifetime and calls `restore_messages` (new) only on the failure path.

## Design decisions

- **Defensive copy on snapshot.** The boundary holds the snapshot across `await`s (LLM calls, tool execution); a shallow reference would observe later appends. `snapshot_messages` (new) returns `[dict(msg) for msg in self.history]` so the snapshot is independent of subsequent mutations.
- **Direct element-wise restore, no re-validation.** `restore_messages` (new) does `history.clear(); history.extend(snapshot)` rather than routing through `replace_history`/`_append_message_locked`. The snapshot was captured from already-trusted history; re-validating on restore would be redundant and could alter messages. This guarantees `AC-004` (memory equals the turn-start snapshot element-wise).
- **Async, matching siblings.** All `ConversationState` mutators are `async` and lock-guarded; these follow suit so callers (the async boundary) await them uniformly.

## Alternatives considered

- **Reuse `replace_history` for restore.** Rejected: `replace_history` (`context.py:L177-191`) re-validates every message as untrusted (`_UNTRUSTED_RESTORE_SOURCE`), which is correct for DB-restored rows but wrong for an in-memory trusted snapshot, and it would re-run sanitization that could change content.
- **Snapshot without a copy (return `self.history`).** Rejected: the boundary awaits across the turn; a live reference would see mid-turn appends, breaking the "turn-start" semantics required for compensation.

## Implementation

### Target file

`scripts/agent/context.py` (existing; extended)

### Procedure

1. Add `async def snapshot_messages(self) -> list[LLMMessage]` (new): `async with self._ensure_lock:` return `[dict(msg) for msg in self.history]`.
2. Add `async def restore_messages(self, snapshot: list[LLMMessage]) -> None` (new): `async with self._ensure_lock:` do `self.history.clear()` then `self.history.extend(snapshot)`.
3. Place both methods adjacent to `extend_messages`/`replace_history` for cohesion.
4. Run the validation sequence.

### Method

`ConversationState` (`scripts/agent/context.py`) is a dataclass (`context.py:L90-116`) whose history is guarded by an async `_history_lock` (`context.py:L99`) exposed through the `_ensure_lock` property (`context.py:L118-122`). Existing mutators all follow the identical shape:

```python
async def append_message(self, msg, *, source=""):      # context.py:124
    async with self._ensure_lock:
        await self._append_message_locked(msg, source=source)

async def extend_messages(self, msgs, *, source=""):     # context.py:165
    async with self._ensure_lock:
        for msg in msgs:
            await self._append_message_locked(msg, source=source)

async def replace_history(self, msgs, *, source=""):     # context.py:177
    async with self._ensure_lock:
        self.history = []
        for msg in msgs:
            await self._append_message_locked(msg, source=_UNTRUSTED_RESTORE_SOURCE)
```

`snapshot_messages` (new)/`restore_messages` (new) mirror this pattern.

```python
# context.py — memory snapshot/restore (REQ-004)  (new)
async def snapshot_messages(self) -> list[LLMMessage]:
    """Return a defensive copy of history, independent of later mutations."""
    async with self._ensure_lock:
        return [dict(msg) for msg in self.history]

async def restore_messages(self, snapshot: list[LLMMessage]) -> None:
    """Restore history to a previously captured snapshot, element-wise."""
    async with self._ensure_lock:
        self.history.clear()
        self.history.extend(snapshot)
```

### Details

- **`REQ-004` / `AC-004` (memory == DB after compensation):** `restore_messages` (new) sets `history` to exactly the snapshot, so after a compensated failure `ConversationState.history` equals the turn-start snapshot element-wise and matches `fetch_messages()` output.
- **Lock safety (`UNK-04`-adjacent):** both methods hold `_history_lock` for the whole copy/extend, so a concurrent `append_message` cannot interleave mid-snapshot.
- **Backward compatibility:** purely additive; no existing field or method changes. TurnPersistence (seq 01) is the sole intended caller.

## Compatibility considerations

- New async API on `ConversationState`, used by nearly all agent modules in read/restore roles; additive only.
- Import boundary: `context.py` stays below the import contract; TurnPersistence (seq 01) imports `ConversationState`, not vice versa.

## Security considerations

- No new input; `restore_messages` (new) trusts its argument, which is the boundary's own turn-start snapshot (trusted, not attacker-controlled). Do not expose `restore_messages` (new) to untrusted DB-restore paths — those keep using `replace_history`.

## Rollback considerations

- Revert the `context.py` edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `snapshot_messages` (new) | Unit: returns independent copy; unaffected by later appends | `uv run pytest tests/agent/test_context.py` | Snapshot stable across subsequent appends |
| `restore_messages` (new) | Unit: history equals snapshot element-wise after restore | `uv run pytest tests/agent/test_context.py` | `history == snapshot` (`AC-004`) |
| lock safety | Concurrency: snapshot/restore under concurrent append | `uv run pytest tests/agent/test_context.py` | No torn snapshot / interleaving |
| backward compat | Regression: existing append/replace cases | `uv run pytest tests/agent/test_context.py` | Unchanged |
| static | ruff / mypy / bandit / vulture | `uv run ruff check scripts/`; `uv run mypy scripts/`; `uv run bandit -r scripts/ -c pyproject.toml`; `uv run vulture scripts/` | Clean |

## Completion criteria

- `snapshot_messages` (new) returns a defensive copy of `history` under the async lock.
- `restore_messages` (new) replaces `history` element-wise with a snapshot under the async lock, without re-validating.
- Existing `ConversationState` methods pass unchanged; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary that consumes the snapshot (`scripts/agent/turn_persistence.py`, seq 01).
- Write-routing callers (`scripts/agent/orchestrator.py`, seq 05; `scripts/agent/llm_turn_runner.py`, seq 07; `scripts/agent/tool_round_completion.py`, seq 08; `scripts/agent/workflow_engine_adapter.py`, seq 09).
- `/undo` interaction (`UNK-03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `snapshot_messages` (new)/`restore_messages` (new) to `ConversationState` in `scripts/agent/context.py` | Pending | — | — | New async API |
| 2 | Add or update tests per Validation plan | Pending | — | — | Extend `tests/agent/test_context.py` |
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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `scripts/agent/context.py`
