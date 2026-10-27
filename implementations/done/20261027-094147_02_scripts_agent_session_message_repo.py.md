## Goal

Extend `scripts/agent/session_message_repo.py` with the three repository-level primitives the turn-persistence boundary (seq 01) needs: a compensation delete (`delete_messages_from` (new)), a transaction-grouped persist variant that writes a whole round's messages in one `begin_immediate` transaction on one connection, and `sqlite3.Error` → `scripts/agent/turn_persistence.py::ConversationPersistenceError` wrapping (`REQ-002`, `REQ-003`, `REQ-005`, `REQ-006`). Existing per-method `save`/`save_many`/`replace_messages` behavior stays backward compatible for `cmd_rag_export*` and stats consumers.

### Adversarial verification corrections

This document's implementation deviates from its literal text in two ways, both required by the Plan's acceptance criteria and pinned by tests.

- **Compensation operator is `> marker`, not `>= marker`.** The marker is `MAX(message_id)` — the last pre-turn row. `DELETE ... WHERE message_id >= marker` would delete that prior turn's row; the correct compensation is `> marker`, deleting exactly this turn's rows and never an earlier turn's (`AC-002`; seq 01's off-by-one correction). Every `>= marker` below is corrected to `> marker`.
- **The repo raises native `sqlite3.Error`; the boundary wraps.** The original text asked the repo to wrap `sqlite3.Error` into `ConversationPersistenceError` at the new entry points. That is wrong for the boundary design: the boundary's write methods catch `except sqlite3.Error` to compensate + restore + raise. A repo-raised `ConversationPersistenceError` (which subclasses `Exception`, not `sqlite3.Error`) would bypass that handler, so a failing write would raise without ever compensating. The repo therefore propagates the raw `sqlite3.Error` (consistent with all its other methods), and the boundary (seq 01) performs the single wrap.

## Scope

- **In-Scope** (`scripts/agent/session_message_repo.py` only):
  - Add `delete_messages_from` (new): DELETE `messages` rows `WHERE session_id = ? AND message_id > ?` in one transaction; mirrors `AgentSession.undo_last_turn`'s `message_id`-based delete (`session.py`, seq 03). Used by the boundary's compensation (seq 01).
  - Add a transaction-grouped persist variant (new): persist a phase-group of messages in a single `SQLiteHelper.begin_immediate` transaction on a single connection, so a tool round's assistant + tool-result rows land atomically (`AC-005`).
  - Wrap raw `sqlite3.Error` from the new grouped/compensation paths into `scripts/agent/turn_persistence.py::ConversationPersistenceError` (seq 01); existing `save`/`save_many`/`replace_messages` keep propagating the raw error unchanged (backward compatibility).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The boundary that owns the reused connection and calls these helpers (`scripts/agent/turn_persistence.py`, seq 01).
  - The `AgentSession.turn_boundary()` facade (`scripts/agent/session.py`, seq 03).
  - Callers that route writes through the boundary (`scripts/agent/llm_turn_runner.py`, seq 07; `scripts/agent/tool_round_completion.py`, seq 08; `scripts/agent/workflow_engine_adapter.py`, seq 09).

## Assumptions

- `SQLiteHelper.begin_immediate()` (`scripts/db/helper.py`, L239) rolls back and re-raises on any exception; the grouped variant relies on it for atomicity.
- `delete_messages_from` (new) deletes exactly the turn's rows (`message_id >= turn_start`), never earlier rows — the marker is supplied by the boundary (seq 01), computed as `MAX(message_id)` at turn start (`UNK-02`).
- `scripts/agent/turn_persistence.py::ConversationPersistenceError` (seq 01) subclasses `Exception` and chains the underlying `sqlite3.Error` on `__cause__`; the repo only constructs it, never catches-and-swallows it.
- The current public `save`/`save_many`/`replace_messages` contract (return values, invalid-role skipping, `undo_floor_message_id` handling in `replace_messages`) is preserved for `cmd_rag_export*` and stats consumers.

## Design decisions

- **Compensation as a dedicated delete, not a reuse of `undo_last_turn`.** `undo_last_turn` (`session.py`, seq 03) is gated by `undo_floor_message_id` and interacts with `/undo` (`UNK-03`); the boundary must bypass that gate. `delete_messages_from` (new) performs a plain `message_id >= marker` delete so `/undo` semantics are untouched.
- **Grouped variant uses `begin_immediate`, not the default connection.** `save_many` already writes many messages in one transaction, but with the connection's default lock mode. The round needs the whole assistant + tool-group under one IMMEDIATE lock on one connection so a mid-round failure leaves either all or none of the round's rows (`AC-005`, `UNK-01`).
- **Error wrapping scoped to the new paths only.** Existing methods already document "sqlite3.Error propagates to caller"; wrapping is added only to the grouped/compensation entry points the boundary calls, so unrelated callers still see the raw error.

## Alternatives considered

- **Reuse `save_many` for grouping.** Rejected: `save_many` opens its own default-mode connection per call and cannot be told to share the boundary's reused connection or to hold an IMMEDIATE lock across the round. A dedicated grouped variant is required for `AC-005`.
- **Compensation via `replace_messages`.** Rejected: `replace_messages` clears ALL rows for the session (it is the compression primitive); compensation must remove only the turn's rows, so a targeted `message_id >= marker` delete is needed.

## Implementation

### Target file

`scripts/agent/session_message_repo.py` (existing; extended)

### Procedure

1. Add `delete_messages_from(session_id, start_message_id)` (new): open one `SQLiteHelper("session")` write connection, `DELETE FROM messages WHERE session_id = ? AND message_id >= ?`, commit, return the deleted row count. Raise `scripts/agent/turn_persistence.py::ConversationPersistenceError` (seq 01) if the DB call fails.
2. Add the transaction-grouped persist variant (new): accept a list of message tuples (or `LLMMessage` dicts) for one phase group and run a single `begin_immediate` transaction on one connection — `executemany(_INSERT_MESSAGE_SQL, rows)` then commit — so the round's assistant + tool rows are atomic.
3. Add `sqlite3.Error` wrapping at the two new entry points, constructing `scripts/agent/turn_persistence.py::ConversationPersistenceError` (seq 01) with the cause; leave `save`/`save_many`/`replace_messages` propagating the raw error.
4. Run the validation sequence.

### Method

`save` (session_message_repo.py:56-89) and `save_many` (session_message_repo.py:91-138) each open their own connection per call; `save_many` already batches many messages in one transaction. `replace_messages` (session_message_repo.py:140-174) runs an atomic DELETE + executemany INSERT + `UPDATE sessions SET undo_floor_message_id` and returns the new `MAX(message_id)` boundary. No delete-from method exists today; the closest pattern is `AgentSession.undo_last_turn` (`session.py`, seq 03, L235-242), which deletes `message_id >= last_user_id`. The boundary (seq 01) owns the reused connection and will drive these helpers.

```python
# session_message_repo.py — compensation delete (REQ-002)  (new)
def delete_messages_from(self, session_id: int, start_message_id: int) -> int:
    """Delete messages rows for a session strictly after start_message_id in one txn."""
    with SQLiteHelper("session").open(write_mode=True) as db:
        cur = db.execute(
            "DELETE FROM messages WHERE session_id = ? AND message_id > ?",
            (session_id, start_message_id),
        )
        db.commit()
    return cur.rowcount


# session_message_repo.py — grouped round persist (REQ-005)  (new)
def save_phase_grouped(
    self, messages: list[tuple[str, str | None, list[dict] | None, str | None]]
) -> None:
    """Persist one phase-group (e.g. assistant + its tool results) in one IMMEDIATE txn.

    Opens one write connection and runs the whole group under begin_immediate(), so a
    mid-round failure leaves either all or none of the round's rows (AC-005). The exact
    wiring to the boundary's reused connection (seq 01) is a Phase 1 design detail (UNK-01).
    """
    if self.session_id is None or not messages:
        return
    rows = [
        (self.session_id, role, content or "", _tool_calls_json(tc), tc_id)
        for role, content, tc, tc_id in messages
        if role in self._valid_roles
    ]
    if not rows:
        return
    with SQLiteHelper("session").open(write_mode=True) as db:
        with db.begin_immediate():
            db.executemany(_INSERT_MESSAGE_SQL, rows)
            # commit happens on begin_immediate() context exit
```

### Details

- **`REQ-002` / `AC-002` (compensation):** `delete_messages_from` (new) removes exactly the turn's rows (`message_id > turn_start`), leaving earlier/completed rows intact. The boundary (seq 01) supplies the marker; this method never computes it. `> marker` (strictly greater) preserves the last pre-turn row.
- **`REQ-005` / `AC-005` (grouped atomic round):** `save_phase_grouped` (new) writes the round's assistant + tool-result rows in one `begin_immediate` transaction on one connection, so a single injected failure leaves either all or none of the round's rows.
- **`REQ-003` / `AC-003` (single error type):** the repo propagates the native `sqlite3.Error` from both new paths (consistent with its other methods); the boundary (seq 01) catches it and wraps it into `scripts/agent/turn_persistence.py::ConversationPersistenceError` via `from`. No raw error escapes the turn path.
- **`REQ-006` (compression untouched):** `replace_messages` keeps its existing atomic DELETE + INSERT + `undo_floor_message_id` update; unchanged here.
- **Backward compatibility:** `save`/`save_many`/`replace_messages` signatures, return values, and invalid-role skipping are unchanged; `cmd_rag_export*` and stats consumers unaffected.

## Compatibility considerations

- New methods are additive; no existing public signature changes.
- The grouped variant name/signature is a Phase 1 design detail (`UNK-01`); the boundary (seq 01) and callers (seq 07/08/09) are written against it, so keep the public shape stable across this Plan.

## Security considerations

- The delete is parameterized (`WHERE session_id = ? AND message_id >= ?`); no string concatenation. Compensation removes only the caller-supplied marker's rows or later — the marker is owned by the boundary, never attacker-controlled.

## Rollback considerations

- Revert the `session_message_repo.py` edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `delete_messages_from` (new) | Unit: deletes only `message_id >= marker` rows, returns row count | `uv run pytest tests/agent/test_session_message_repo.py` | Earlier rows retained; turn rows gone |
| grouped variant | Unit: one txn, all-or-none on injected failure | `uv run pytest tests/agent/test_session_message_repo.py` | Either all round rows or none (`AC-005`) |
| error wrapping | Unit: `sqlite3.Error` → `scripts/agent/turn_persistence.py::ConversationPersistenceError` with `__cause__` | `uv run pytest tests/agent/test_session_message_repo.py` | Type is `scripts/agent/turn_persistence.py::ConversationPersistenceError` (`AC-003`) |
| backward compat | Regression: existing save/save_many/replace cases | `uv run pytest tests/agent/test_session_message_repo.py` | Unchanged |
| static | ruff / mypy / bandit / vulture | `uv run ruff check scripts/`; `uv run mypy scripts/`; `uv run bandit -r scripts/ -c pyproject.toml`; `uv run vulture scripts/` | Clean |

## Completion criteria

- `delete_messages_from(session_id, start_message_id)` deletes `message_id >= marker` rows in one transaction and returns the row count.
- The grouped variant persists a phase-group in one `begin_immediate` transaction on one connection.
- Both new paths raise `scripts/agent/turn_persistence.py::ConversationPersistenceError` (seq 01) wrapping the `sqlite3.Error`; existing methods still propagate the raw error.
- Existing `save`/`save_many`/`replace_messages` cases pass unchanged; ruff/mypy/bandit/vulture clean.

## Out of Scope

- Boundary connection ownership (`scripts/agent/turn_persistence.py`, seq 01).
- `AgentSession.turn_boundary()` (`scripts/agent/session.py`, seq 03).
- Write-routing callers (`scripts/agent/llm_turn_runner.py`, seq 07; `scripts/agent/tool_round_completion.py`, seq 08; `scripts/agent/workflow_engine_adapter.py`, seq 09).
- `/undo` interaction (`UNK-03`) — the targeted delete deliberately bypasses `undo_last_turn`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `delete_messages_from` (new), grouped variant, error wrapping in `scripts/agent/session_message_repo.py` | Complete | 2026-10-27 | 2026-10-27 | Extends existing repo |
| 2 | Add or update tests per Validation plan | Complete | 2026-10-27 | 2026-10-27 | Extend `tests/agent/test_session_message_repo.py` |
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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-005`, `REQ-006`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `scripts/agent/session_message_repo.py`
