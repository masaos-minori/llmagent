## Goal

Create the single turn-persistence boundary module `scripts/agent/turn_persistence.py` that makes session-DB persistence for one agent turn all-or-nothing (`REQ-001`). It defines `ConversationPersistenceError (new)` (new) — the exception every turn-path failure surfaces through — and `TurnPersistence (new)` (new), the object that owns the turn-start marker, per-phase writes on a reused connection, compensation, and memory restore. On any persistence failure inside a turn the boundary deletes the turn's partial DB rows, restores `ConversationState` memory to its turn-start snapshot, and raises `ConversationPersistenceError (new)` wrapping the underlying `sqlite3.Error` (`REQ-002`, `REQ-003`, `REQ-004`).

### Adversarial verification corrections

The implementation below deviates from this document's literal pseudo-code in two ways, both required to satisfy the Plan's acceptance criteria. Both deviations are pinned by tests.

- **Compensation operator is `> marker`, not `>= marker`.** The turn-start marker is `MAX(message_id)` — the largest `message_id` of the *last pre-turn row*. A `DELETE ... WHERE message_id >= marker` would therefore also delete that prior turn's row. The correct compensation is `DELETE ... WHERE message_id > marker`, which deletes exactly this turn's rows and never an earlier turn's row (`AC-002`: "zero message rows from that turn"; seq 02's stated intent "deletes exactly the turn's rows, never earlier rows"). This document's `_compensate` pseudo-code (`message_id >= marker`) is corrected to `> marker`.
- **`fail_from_error` is `async`.** `restore_messages` (`context.py`, seq 04) is lock-guarded and `async`, so the boundary's failure path must `await` it; `fail_from_error` (renamed `_fail_from_error` in the implementation) is therefore `async` and `NoReturn`.

## Scope

- **In-Scope** (`scripts/agent/turn_persistence.py` only):
  - Define `ConversationPersistenceError (new)` (new): `class ConversationPersistenceError(Exception)` that chains the wrapped `sqlite3.Error` via `from` (`REQ-003`).
  - Define `TurnPersistence (new)` (new): holds the turn-start `turn_start_message_id (new)` marker, a `ConversationState` memory snapshot, and one reused `SQLiteHelper("session")` write connection; expose per-phase write entry points, a `_compensate` (new) helper, and a `fail_from_error (new)` (new) that compensates + restores + raises (`REQ-001`, `REQ-002`, `REQ-004`).
  - Capture the turn-start marker as `MAX(message_id)` for the session at turn start (`0` for a fresh session); no schema change (`UNK-02`).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - Transaction-grouped / error-wrapped repository variants and `scripts/agent/session_message_repo.py::delete_messages_from` (seq 02).
  - `AgentSession.turn_boundary()` (`scripts/agent/session.py`, seq 03).
  - `ConversationState.snapshot_messages()` / `restore_messages()` (`scripts/agent/context.py`, seq 04).
  - Orchestrator boundary wiring (`scripts/agent/orchestrator.py`, seq 05).

## Assumptions

- `SQLiteHelper.begin_immediate()` (`scripts/db/helper.py`, L239) rolls back the open transaction on any exception and re-raises; the boundary relies on this primitive and MUST NOT modify it (reference file).
- The reused write connection is created with `reuse_connection=True` so successive phases share one `sqlite3.Connection` and one WAL lock.
- `TurnPersistence (new)` is created once per turn by the orchestrator and owns the turn for its whole lifetime; no other component writes `messages` rows for the same session during the turn (plan assumption, enforced by AC-001).
- The boundary calls `scripts/agent/context.py::restore_messages` and `scripts/agent/context.py::snapshot_messages` (seq 04) once that row is implemented, and `scripts/agent/session_message_repo.py::delete_messages_from` (seq 02). These cross-row symbols are absent from source at planning time and are cited here as plan-internal dependencies.
- `ConversationPersistenceError (new)` subclasses the plain `Exception` base, matching the project's subsystem-local error convention (`shared.llm_exceptions.LLMTransportError(Exception)`); it stores the cause, not a copy.

## Design decisions

- **Per-phase transactions + turn compensation, not one long transaction.** A single SQLite transaction held across the whole turn would hold the WAL write lock across LLM calls and tool execution (seconds to minutes; bash/subagent tools can run minutes), blocking concurrent writers to `session.sqlite` and losing already-completed rounds on crash. Per-phase `begin_immediate` preserves per-phase durability while turn-level all-or-nothing is guaranteed on the failure path by compensation (`UNK-01`, plan Design).
- **Marker computed from `message_id`, not stored.** The turn-start boundary is the largest `message_id` for the session at turn start (`0` when fresh), so no schema change is needed (`UNK-02`, `scripts/db/schema_sql.py` unchanged). Compensation deletes `messages` rows `WHERE session_id = ? AND message_id >= ?` with that marker.
- **Error object defined at the boundary.** `ConversationPersistenceError (new)` lives in this module (the layer that owns the turn contract) rather than a shared package, so every turn-path failure surfaces through one recognizable type (`REQ-003`, `llm_transport_errors.py` convention).

## Alternatives considered

- **One deferred transaction per turn committed at phase points.** Chosen trade-off (`UNK-01`) is runtime lock-hold time under real tool execution; the per-phase + compensation model was selected because it never holds the WAL lock across an `await` on an LLM/tool call. Phase 1 tests pin this granularity.
- **Compensation via the existing `AgentSession.undo_last_turn`.** Rejected as the primary mechanism: the `undo_floor_message_id` gate interacts with `/undo` (`UNK-03`); the boundary uses a direct `message_id >= marker` delete instead and leaves `/undo` semantics untouched.

## Implementation

### Target file

`scripts/agent/turn_persistence.py` (new)

### Procedure

1. Add module docstring + imports: `sqlite3`, `logging`, and `SQLiteHelper` from `db.helper` (all new to this file).
2. Define `ConversationPersistenceError (new)` (new): `class ConversationPersistenceError(Exception)` with an `__init__` that stores a human message and chains `raise ... from sqlite_exc`.
3. Define `TurnPersistence.__init__` (new): store `session_id`, the turn-start `turn_start_message_id` (new), the `ConversationState` snapshot copy, and lazily open the reused write connection.
4. Add `_compensate` (new): DELETE the turn's rows in one transaction via the repository's `scripts/agent/session_message_repo.py::delete_messages_from` helper (seq 02) on the reused connection.
5. Add `fail_from_error (new)` (new): call `_compensate()`, restore the turn-start memory snapshot (seq 04), then raise `ConversationPersistenceError (new)` from the underlying error.
6. Run the validation sequence.

### Method

`scripts/db/helper.py` exposes `begin_immediate()` (helper.py:239) as a context manager that begins an IMMEDIATE transaction on a connection and rolls back on exception; `open(reuse_connection=True)` (helper.py:172-204) keeps one connection open across uses. `SessionMessageRepository` (`scripts/agent/session_message_repo.py`) already opens its own connection per `save`/`save_many`/`replace_messages` and propagates raw `sqlite3.Error`; the boundary reuses ONE connection and groups phases. `ConversationState` (`scripts/agent/context.py`) holds `history: list[LLMMessage]` guarded by an async `_history_lock`; its `scripts/agent/context.py::snapshot_messages` / `scripts/agent/context.py::restore_messages` (seq 04) provide memory rollback.

```python
# turn_persistence.py — exception (REQ-003)  (new)
class ConversationPersistenceError(Exception):
    """Raised when a turn's session-DB persistence fails and is compensated.

    Wraps the underlying sqlite3.Error; the original is preserved on __cause__.
    """

    def __init__(self, message: str, *, cause: sqlite3.Error) -> None:
        super().__init__(f"{message}: {cause}")
        self.cause = cause


# turn_persistence.py — TurnPersistence boundary (REQ-001, REQ-002, REQ-004)  (new)
class TurnPersistence:
    """Owns all session-DB writes of one agent turn (all-or-nothing)."""

    def __init__(
        self,
        session: AgentSession,              # (new) provides session_id + turn_boundary()
        turn_start_message_id: int,         # (new) MAX(message_id) at turn start (0 fresh)
        snapshot: list[LLMMessage],
    ) -> None:
        self.session_id = session.session_id
        self.turn_start_message_id = turn_start_message_id
        self._snapshot = snapshot
        self._conv = session.conv          # (new) ConversationState for restore
        self._conn = None

    @property
    def _db(self) -> SQLiteHelper:        # (new) reused write connection
        if self._conn is None:
            self._conn = SQLiteHelper("session").open(reuse_connection=True)
        return self._conn

    def _compensate(self) -> None:        # (new) REQ-002
        # DELETE messages WHERE session_id=? AND message_id>marker in one txn.
        delete_messages_from(self.session_id, self.turn_start_message_id)

    def fail_from_error(self, exc: sqlite3.Error) -> None:   # (new) REQ-002, REQ-004, REQ-003
        self._compensate()
        self._conv.restore_messages(self._snapshot)   # seq 04
        raise ConversationPersistenceError(
            "turn not persisted; history rolled back", cause=exc
        ) from exc
```

### Details

- **`REQ-001` (one boundary per turn):** the boundary is constructed by the orchestrator (seq 05) via `scripts/agent/session.py::turn_boundary` (seq 03) with the turn-start marker and a pre-taken memory snapshot; it is the only object permitted to persist turn writes.
- **`REQ-002` (turn all-or-nothing):** `_compensate()` deletes exactly the turn's rows (`message_id > turn_start_message_id`) in one transaction, so completed earlier phases leave no residue on failure. Marker is the largest `message_id` at turn start (`0` fresh) — `UNK-02`. `> marker` (strictly greater) preserves the last pre-turn row; `>= marker` would wrongly delete it.
- **`REQ-003` (single error type):** `fail_from_error (new)` raises `ConversationPersistenceError (new)` (new) chaining the raw `sqlite3.Error` via `from exc`; no raw error escapes the turn path. Base class is `Exception`, matching `LLMTransportError`'s placement convention.
- **`REQ-004` (memory == DB after compensation):** `fail_from_error (new)` restores the turn-start snapshot so `ConversationState.history` equals the turn-start snapshot element-wise (AC-004).
- **`UNK-03` (`/undo` untouched):** compensation uses a direct `message_id >= marker` delete, not `undo_last_turn`, so the `undo_floor_message_id` gate is not bypassed; documented alongside the boundary contract (seq 20).

## Compatibility considerations

- New module imported only by the orchestrator (seq 05) and `session.py` (seq 03); no existing caller exists yet.
- `ConversationPersistenceError (new)` is a new exception type; the REPL (seq 10) gains a dedicated except branch so existing generic-error behavior is unchanged for non-persistence failures.

## Security considerations

- No new credentials, secrets, or injection surface. The error message names the failure, not any sensitive value; `cause` carries the DB error only.

## Rollback considerations

- Revert the `turn_persistence.py` edit (`git checkout scripts/agent/turn_persistence.py` — or delete the new file) removes the boundary. Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `ConversationPersistenceError (new)` | Unit: exception type, cause chaining | `uv run pytest tests/agent/test_turn_persistence.py` | Raised on injected DB failure; `__cause__` is the `sqlite3.Error` |
| `TurnPersistence (new)` construction + marker | Unit: fresh-session marker = 0, reused connection | `uv run pytest tests/agent/test_turn_persistence.py` | `turn_start_message_id == 0` on fresh session |
| `turn_persistence.py` static | Dead code / security | `uv run vulture scripts/agent/`; `uv run bandit scripts/agent/ -c pyproject.toml` | Clean |
| Import boundary | Architecture | `PYTHONPATH=scripts uv run lint-imports` | Contract kept |

## Completion criteria

- `ConversationPersistenceError (new)` exists, subclasses `Exception`, and chains the underlying `sqlite3.Error` on `__cause__`.
- `TurnPersistence (new)` holds the turn-start `message_id` marker (`0` fresh), a memory snapshot, and one reused `SQLiteHelper("session")` write connection; `fail_from_error (new)` compensates (deletes `message_id >= marker`), restores memory, and raises `ConversationPersistenceError (new)`.
- `scripts/db/helper.py` is unmodified.
- ruff, mypy, bandit, vulture pass; `test_turn_persistence.py` asserts the exception type and fresh-session marker.

## Out of Scope

- Repository transaction-grouping and `scripts/agent/session_message_repo.py::delete_messages_from` (seq 02).
- `AgentSession.turn_boundary()` (`scripts/agent/session.py`, seq 03).
- `ConversationState.snapshot_messages()` / `restore_messages()` (`scripts/agent/context.py`, seq 04).
- Orchestrator wiring (`scripts/agent/orchestrator.py`, seq 05).
- `/undo` interaction semantics (`UNK-03`) — recorded, implemented via the direct delete; documented in seq 20.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `TurnPersistence (new)` boundary + `ConversationPersistenceError (new)` in `scripts/agent/turn_persistence.py` | Complete | 2026-10-27 | 2026-10-27 | New module |
| 2 | Add or update tests per Validation plan | Complete | 2026-10-27 | 2026-10-27 | `tests/agent/test_turn_persistence.py` (new) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Complete | 2026-10-27 | 2026-10-27 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Complete | 2026-10-27 | 2026-10-27 | N/A: contract doc is seq 20 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261026-224643_turn001_atomic-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-070403_turn001_atomic-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-094147
- **Related target files**: `scripts/agent/turn_persistence.py`
