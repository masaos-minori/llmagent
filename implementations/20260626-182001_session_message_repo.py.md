# Implementation: session_message_repo.py — replace_compressed_messages

Source plan: `plans/20260626-180401_plan.md` — Phase 1

---

## Goal

Add `replace_compressed_messages()` to `SessionMessageRepository` so that when `HistoryManager.compress()` fires, the DB `messages` table is updated to match the new compressed in-memory history: old messages from before the cutoff are deleted and the summary row + retained rows are inserted in a single transaction.

---

## Scope

**In-Scope**
- New method `replace_compressed_messages(session_id, cutoff_message_id, summary_content, retained_messages)` on `SessionMessageRepository`
- Atomic DB transaction: DELETE rows with `message_id < cutoff_message_id`, then INSERT summary row + retained rows
- Expose the method via `AgentSession.replace_compressed_messages()` delegation in `session.py`

**Out-of-Scope**
- Changes to compression logic in `history.py`
- Changes to call sites in orchestrator
- Any migration of pre-existing sessions

---

## Assumptions

1. `cutoff_message_id` is the `message_id` of the first message that was selected for compression (all rows with `message_id <= cutoff_message_id` for the compressed range are deleted).
2. `summary_content` is the `[Conversation summary]\n...` string produced by `HistoryManager._build_summary_msg()`.
3. `retained_messages` is `list[LLMMessage]` — the messages after the compressed window in the new history.
4. The method operates under the current `self.session_id`; if `session_id` is None it logs and returns without raising.
5. The summary row is inserted with `role="system"`, no `tool_calls`, no `tool_call_id`.

---

## Implementation

### Target file
`scripts/agent/session_message_repo.py`

### Procedure
1. Add import for `LLMMessage` (already imported).
2. Add new method `replace_compressed_messages` to `SessionMessageRepository`.
3. In `session.py`, add delegation method `AgentSession.replace_compressed_messages()`.

### Method

```python
def replace_compressed_messages(
    self,
    cutoff_message_id: int,
    summary_content: str,
    retained_messages: list[LLMMessage],
) -> None:
```

### Details

```python
def replace_compressed_messages(
    self,
    cutoff_message_id: int,
    summary_content: str,
    retained_messages: list[LLMMessage],
) -> None:
    """Delete compressed messages and persist summary + retained in one transaction.

    Deletes all messages in this session with message_id <= cutoff_message_id,
    then inserts the summary system message followed by retained_messages.
    No-op when session_id is None.
    """
    if self.session_id is None:
        logger.warning("replace_compressed_messages: no session_id; skipping")
        return
    retained_rows = [
        (
            self.session_id,
            msg["role"],
            str(msg.get("content") or ""),
            _json_dumps(msg["tool_calls"]) if msg.get("tool_calls") else None,
            msg.get("tool_call_id"),
        )
        for msg in retained_messages
        if msg["role"] in _VALID_ROLES
    ]
    with SQLiteHelper("session").open(write_mode=True) as db:
        db.execute(
            "DELETE FROM messages WHERE session_id = ? AND message_id <= ?",
            (self.session_id, cutoff_message_id),
        )
        db.execute(
            "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id)"
            " VALUES (?, 'system', ?, NULL, NULL)",
            (self.session_id, summary_content),
        )
        if retained_rows:
            db.executemany(
                "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id)"
                " VALUES (?, ?, ?, ?, ?)",
                retained_rows,
            )
        db.commit()
    logger.info(
        "Compression persisted: session=%s cutoff_id=%s summary+%d retained",
        self.session_id,
        cutoff_message_id,
        len(retained_rows),
    )
```

**Delegation in `session.py`** — add to `AgentSession`:

```python
def replace_compressed_messages(
    self,
    cutoff_message_id: int,
    summary_content: str,
    retained_messages: list[LLMMessage],
) -> None:
    """Persist a compression event to DB."""
    self._message_repo.replace_compressed_messages(
        cutoff_message_id, summary_content, retained_messages
    )
```

---

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/session_message_repo.py scripts/agent/session.py` | 0 errors |
| Type | `uv run mypy scripts/agent/session_message_repo.py scripts/agent/session.py` | no new errors |
| Unit test | `uv run pytest tests/test_agent_session.py -v` | all pass |
| Full suite | `uv run pytest -v` | all pass |
