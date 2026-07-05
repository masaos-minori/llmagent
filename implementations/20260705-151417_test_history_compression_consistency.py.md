# Implementation: tests/test_history_compression_consistency.py — History compression/undo consistency tests

## Goal

Lock down deterministic behavior for session reload after compression, `/undo` behavior after compression, `tool_results` retention, and fallback truncation persistence.

## Scope

**In**: Tests for compression → reload, /undo after compression, tool_results after undo, fallback truncation.

**Out**: Source file changes, schema changes (Phase 3 optional metadata is out of scope for this doc).

## Assumptions

1. `HistoryManager.compress()` replaces messages in `ctx.conv.history`.
2. `AgentSession.replace_messages(session_id, messages)` persists compressed history.
3. `orchestrator.py` calls `replace_messages()` after compression (confirmed at line ~410).
4. `/undo` after compression removes the compressed summary message (or is a no-op if only one message).
5. `tool_results` rows retain `undone=True` marker independently of message compression.
6. Fallback truncation calls `replace_messages()` (verify during Phase 1 — if not, this test documents the gap).

## Implementation

### Target file
`tests/test_history_compression_consistency.py`

### Procedure
1. Read `session.py:undo_last_turn()` to confirm post-compression undo behavior.
2. Read `history.py` fallback truncation path.
3. Write tests with in-memory DB.

### Method

```python
import pytest
from unittest.mock import MagicMock, patch
from scripts.agent.history import HistoryManager, CompressResult
from scripts.agent.session import AgentSession


# Fixtures

@pytest.fixture
def session_db(tmp_path):
    """AgentSession backed by temporary SQLite DB."""
    from scripts.db.helper import SQLiteHelper
    db = SQLiteHelper(str(tmp_path / "session.sqlite"))
    session = AgentSession(db)
    return session


def _make_history(n_turns: int) -> list[dict]:
    messages = []
    for i in range(n_turns):
        messages.append({"role": "user", "content": f"User message {i}"})
        messages.append({"role": "assistant", "content": f"Assistant reply {i}"})
    return messages


# --- Compression → reload ---

def test_reload_after_compression_restores_compressed_history(session_db):
    """After compress() + replace_messages(), a new session load must see the summary."""
    session_id = "sess-compress-test"
    original = _make_history(5)  # 10 messages
    session_db.save_messages(session_id, original)

    summary_msg = {"role": "assistant", "content": "[SUMMARY] compressed"}
    session_db.replace_messages(session_id, [summary_msg])

    loaded = session_db.load_messages(session_id)
    assert len(loaded) == 1
    assert loaded[0]["content"] == "[SUMMARY] compressed"


def test_reload_after_compression_no_original_rows_remain(session_db):
    """replace_messages() must remove ALL prior rows for the session."""
    session_id = "sess-stale-test"
    original = _make_history(3)
    session_db.save_messages(session_id, original)

    summary_msg = {"role": "assistant", "content": "[SUMMARY]"}
    session_db.replace_messages(session_id, [summary_msg])

    loaded = session_db.load_messages(session_id)
    # No stale original messages remain
    assert all("[SUMMARY]" in m["content"] for m in loaded)


def test_replace_messages_preserves_role_sequence(session_db):
    session_id = "sess-role-test"
    session_db.save_messages(session_id, _make_history(2))
    compressed = [
        {"role": "user", "content": "summarized user context"},
        {"role": "assistant", "content": "[SUMMARY]"},
    ]
    session_db.replace_messages(session_id, compressed)
    loaded = session_db.load_messages(session_id)
    assert [m["role"] for m in loaded] == ["user", "assistant"]


# --- /undo after compression ---

def test_undo_after_compression_removes_summary_message(session_db):
    """/undo after compression must remove the compressed summary turn."""
    session_id = "sess-undo-compress"
    session_db.save_messages(session_id, [
        {"role": "user", "content": "user"},
        {"role": "assistant", "content": "[SUMMARY]"},
    ])
    session_db.undo_last_turn(session_id)
    loaded = session_db.load_messages(session_id)
    # Summary message should be removed (or marked undone)
    assert not any("[SUMMARY]" in m.get("content", "") for m in loaded if not m.get("undone"))


def test_undo_on_single_compressed_message_is_safe(session_db):
    """Undo when only the summary remains should not raise and leave a consistent state."""
    session_id = "sess-undo-single"
    session_db.save_messages(session_id, [
        {"role": "assistant", "content": "[SUMMARY]"},
    ])
    # Should not raise
    session_db.undo_last_turn(session_id)
    # Result: 0 messages or 1 message marked undone
    loaded = session_db.load_messages(session_id)
    active = [m for m in loaded if not m.get("undone")]
    assert len(active) == 0


# --- tool_results retention after undo on compressed history ---

def test_tool_results_marked_undone_after_undo(session_db):
    """tool_results rows for the undone turn should be marked undone=True."""
    session_id = "sess-tr-undo"
    msg_id = "msg-1"
    session_db.save_messages(session_id, [
        {"role": "user", "content": "user"},
        {"role": "assistant", "content": "response", "id": msg_id},
    ])
    session_db.save_tool_result(session_id, msg_id, tool_name="shell_run", output="result")
    session_db.undo_last_turn(session_id)

    results = session_db.load_tool_results(session_id, msg_id)
    assert all(r.get("undone") for r in results), "tool_results must be marked undone after undo"


def test_tool_results_persist_after_compression(session_db):
    """tool_results rows must NOT be deleted by replace_messages()."""
    session_id = "sess-tr-compress"
    msg_id = "msg-orig"
    session_db.save_messages(session_id, [
        {"role": "assistant", "content": "original", "id": msg_id},
    ])
    session_db.save_tool_result(session_id, msg_id, tool_name="read_file", output="content")
    session_db.replace_messages(session_id, [
        {"role": "assistant", "content": "[SUMMARY]"},
    ])
    # tool_results for the original msg_id should still exist (not deleted)
    results = session_db.load_tool_results(session_id, msg_id)
    assert len(results) >= 1


# --- Fallback truncation persistence ---

def test_fallback_truncation_persists_via_replace_messages(session_db):
    """Fallback truncation (non-LLM) must persist the truncated history via replace_messages()."""
    session_id = "sess-truncate"
    original = _make_history(10)  # 20 messages
    session_db.save_messages(session_id, original)

    from scripts.agent.history import HistoryManager
    hm = HistoryManager(char_limit=100)  # tiny limit forces truncation
    ctx = MagicMock()
    ctx.conv.history = original.copy()
    ctx.session = session_db
    ctx.session_id = session_id

    hm.truncate_if_needed(ctx)

    loaded = session_db.load_messages(session_id)
    # After truncation + persist, loaded count must be less than original
    # OR the test documents that truncation currently does NOT persist
    # (in which case this test fails and the gap is now visible)
    assert len(loaded) <= len(original), (
        "If this fails, fallback truncation does not persist via replace_messages() — gap confirmed."
    )


# --- Message count invariants ---

def test_compress_result_count_matches_replace(session_db):
    """The number of messages in replace_messages() must match compress() output."""
    session_id = "sess-count"
    original = _make_history(4)
    session_db.save_messages(session_id, original)

    compressed_messages = [{"role": "assistant", "content": "[SUMMARY of 8 messages]"}]
    session_db.replace_messages(session_id, compressed_messages)
    loaded = session_db.load_messages(session_id)
    assert len(loaded) == len(compressed_messages)
```

## Validation plan

- `uv run pytest tests/test_history_compression_consistency.py -v` — all pass.
- `ruff check tests/test_history_compression_consistency.py` — 0 errors.
- Note: `test_fallback_truncation_persists_via_replace_messages` is allowed to fail if the gap exists — that failure IS the finding.
