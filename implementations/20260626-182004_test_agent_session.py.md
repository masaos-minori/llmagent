# Implementation: test_agent_session.py — compress→reload regression test

Source plan: `plans/20260626-180401_plan.md` — Phase 3

---

## Goal

Add a regression test that verifies: after `HistoryManager.compress()` fires and the result is persisted via `replace_compressed_messages()`, calling `restore_session()` reconstructs a history that is semantically equivalent to the compressed in-memory history.

---

## Scope

**In-Scope**
- Test: create session → save N messages → trigger compression → call `replace_compressed_messages()` → call `restore_session()` → assert restored history has same structure as compressed history
- Use in-memory or temp SQLite for isolation

**Out-of-Scope**
- Testing compression algorithm correctness
- Testing orchestrator wiring (done by integration test)

---

## Assumptions

1. `tests/test_agent_session.py` exists with SQLite fixtures that can be reused.
2. The test mocks the LLM call in `HistoryManager._call_compress_llm()` to return a fixed summary string.
3. `restore_session()` is the function under test, not the full REPL.

---

## Implementation

### Target file
`tests/test_agent_session.py`

### Procedure
1. Read existing test fixtures in `test_agent_session.py` to understand DB setup pattern.
2. Add test function `test_compress_then_session_load_consistent`.

### Method

```python
def test_compress_then_session_load_consistent(tmp_path, monkeypatch):
    """Compress history, persist to DB, reload — result must match compressed state."""
    # Setup: patch SQLiteHelper to use tmp_path DB
    # ...existing fixture pattern...

    # Step 1: Create session and save 6 messages
    session = AgentSession()
    session.start()
    msgs = [
        ("user", "msg1", None, None),
        ("assistant", "resp1", None, None),
        ("user", "msg2", None, None),
        ("assistant", "resp2", None, None),
        ("user", "msg3", None, None),
        ("assistant", "resp3", None, None),
    ]
    session.save_many(msgs)

    # Step 2: Snapshot message_ids before compression
    msg_ids = session._message_repo.fetch_message_ids(session.session_id)
    assert len(msg_ids) == 6

    # Step 3: Build a fake compressed history (simulate HistoryManager output)
    summary = "[Conversation summary]\nmsg1-resp1-msg2-resp2 summarized"
    retained = [
        {"role": "user", "content": "msg3"},
        {"role": "assistant", "content": "resp3"},
    ]
    compressed_indices = [0, 1, 2, 3]  # first 4 messages compressed
    cutoff_id = msg_ids[compressed_indices[-1]]  # msg_ids[3]

    # Step 4: Persist compression
    session.replace_compressed_messages(cutoff_id, summary, retained)

    # Step 5: Restore session
    from agent.services.session_restore import restore_session
    ctx = make_test_ctx(session)  # helper that builds a minimal AgentContext
    result = restore_session(ctx, session.session_id)

    # Step 6: Assert restored history matches compressed history
    restored = ctx.conv.history
    system_msgs = [m for m in restored if m["role"] == "system"]
    non_system = [m for m in restored if m["role"] != "system"]
    assert any("[Conversation summary]" in str(m.get("content", "")) for m in system_msgs)
    assert non_system == retained
    assert result.n_messages == len(restored)
```

---

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check tests/test_agent_session.py` | 0 errors |
| Tests | `uv run pytest tests/test_agent_session.py::test_compress_then_session_load_consistent -v` | pass |
| Full suite | `uv run pytest -v` | all pass |
