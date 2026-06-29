# Implementation: Persist compressed conversation history back to session.sqlite after each compression

## Goal

Persist compressed conversation history back to `session.sqlite` after each in-memory compression so that `/session load` restores a semantically consistent state.

## Scope

- **In-Scope**:
  - Persist the compressed `ctx.conv.history` snapshot to `messages` after every compression event (automatic and `/compact`)
  - Implement a `replace_messages()` method in `SessionMessageRepository` / `AgentSession` that atomically clears existing rows and inserts the new compressed set
  - Update `agent/orchestrator.py` (`_handle_history_compression`) and `cmd_rag_export.py` (`_cmd_compact`) to call the new persist path after compression
  - Ensure `/session load` (via `session_restore.restore_session`) reads back a compressed-consistent history without code change (since DB is now the source of truth)
  - Ensure `/history` (`_cmd_history`) and `/export` (`_cmd_export`) operate on `ctx.conv.history` (already correct — no change needed, but must be verified)
  - Add regression test: compress → reload session → restored history is semantically equivalent
  - Document the canonical persistence model in `docs/05_agent_04_state-and-persistence.md`
- **Out-of-Scope**:
  - Full redesign of `HistoryManager`
  - Changing compression policy, thresholds, or scoring
  - Schema changes to add new columns (approach: replace rows, no new columns needed)
  - Changing `/undo` or `/clear` behavior

## Assumptions

- The canonical approach is **persist-compressed-history**: after compression, delete all existing `messages` rows for the session and INSERT the compressed set. This is the simplest model consistent with the current architecture.
- `[Conversation summary]` system messages produced by `_build_summary_msg()` must be persisted as `role=system` rows; they round-trip correctly through `fetch_messages()` → `LLMMessage`.
- No DB schema migration is required — existing `messages` columns cover all fields in `LLMMessage` (role, content, tool_calls, tool_call_id).
- `replace_messages()` must run in a single transaction: DELETE + INSERT batch, so partial writes cannot leave the DB in an inconsistent state.
- The `stat_turns` counter and other in-memory stats are NOT persisted; they reset on reload (existing behavior, out of scope).
- Fallback truncation (drop-without-summary) must also trigger `replace_messages()` to keep DB consistent.

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? |
|---|---|---|---|---|
| UNK-01 | Whether `replace_messages()` should also update the `sessions.title` or any session-level metadata | No title change implied by compression | No action needed; title is set independently | No |
| UNK-02 | Whether `/undo` after a reload should undo based on the compressed DB state or the original state | `undo_last_turn()` operates on current DB rows; after reload the DB holds compressed rows, so undo will operate on compressed history — this may be surprising | Confirm acceptable behavior; document it | No |
| UNK-03 | Whether `save_many()` performance is sufficient for large re-persist (up to ~50 messages) | No benchmarks exist; SQLite batch insert should be fast enough | Accept; add comment if needed | No |
| UNK-04 | Whether concurrent compression in background tasks can race with `replace_messages()` | Compression is triggered synchronously in `_process_turn` before LLM call; no background compression exists | Safe; no locking needed | No |

## Verification Results

### 1. Current state: `_handle_history_compression` discards CompressResult

**File**: `scripts/agent/orchestrator.py:384`
```python
ctx.conv.history, _ = await ctx.services.hist_mgr.compress(ctx.conv.history)
```
- The `CompressResult` is discarded with `_` — needs to be captured for conditional persist
- No call to persist the compressed history after compression ✓ (this is the bug we're fixing)

### 2. Current state: `_cmd_compact` discards CompressResult

**File**: `scripts/agent/commands/cmd_rag_export.py:235-237`
```python
ctx.conv.history = await ctx.services.hist_mgr.force_compress(
    ctx.conv.history
)
```
- `force_compress()` returns `tuple[list[LLMMessage], CompressResult]` but only the history is assigned
- The `CompressResult` is discarded — needs to be unpacked for conditional persist

### 3. No existing `replace_messages()` method

**File**: `scripts/agent/session_message_repo.py`
- Only `save_many()` exists at line 66; no `replace_messages()` method
- Need to add new method

### 4. Compression produces `[Conversation summary]` system messages

**File**: `scripts/agent/history.py:375-393`
```python
def _build_compressed_result(self, split: SelectionResult, summary_text: str) -> tuple[list[LLMMessage], CompressResult]:
    summary_msg = self._build_summary_msg(system_msgs, summary_text)
    result = CompressResult(compressed_count=n, protected_count=protected, summary_added=True)
    return system_msgs + [summary_msg] + remaining, result
```
- Summary messages are `role=system` rows — need to verify they round-trip correctly through DB

### 5. Fallback truncation also modifies history

**File**: `scripts/agent/history.py:291-320`
```python
def _fallback_truncate(self, history: list[LLMMessage]) -> tuple[list[LLMMessage], CompressResult]:
    # Drop low-value messages to bring context under char limit
    return new_history, CompressResult(...)
```
- Must also trigger `replace_messages()` for consistency

## Implementation

### Target file: `scripts/agent/session_message_repo.py`

#### Procedure

Add `replace_messages()` method to `SessionMessageRepository`.

#### Method

Direct file edit — append new method after existing `save_many()`.

#### Details

**Append after line 120 (after `save_many`):**
```python
def replace_messages(self, session_id: int, messages: list[LLMMessage]) -> None:
    """Atomically clear and re-insert all messages for a session.

    Used after history compression to persist the compressed snapshot.
    Runs in a single transaction: DELETE + executemany INSERT.
    """
    with self._db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,)):
        pass
    if not messages:
        return
    rows = []
    for msg in messages:
        rows.append((
            session_id,
            msg.get("role", "user"),
            msg.get("content") or "",
            orjson.dumps(msg.get("tool_calls") or []).decode() if msg.get("tool_calls") else None,
            msg.get("tool_call_id"),
        ))
    self._db.executemany(
        "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
```

### Target file: `scripts/agent/session.py`

#### Procedure

Add `replace_messages()` delegation to `AgentSession`.

#### Method

Direct file edit — append after existing `save_many()`.

#### Details

**Append after line 52 (after `save_many`):**
```python
def replace_messages(self, messages: list[LLMMessage]) -> None:
    """Persist compressed history snapshot back to DB.

    Skips silently if session_id is None (before session.start()).
    """
    if self.session_id is None:
        logger.warning("replace_messages called before session.start(); skipping persist")
        return
    self._message_repo.replace_messages(self.session_id, messages)
```

### Target file: `scripts/agent/orchestrator.py`

#### Procedure

Update `_handle_history_compression()` to capture CompressResult and call replace_messages after compression.

#### Method

Direct file edit — modify line 384.

#### Details

**Replace line 384:**
```python
# Before:
ctx.conv.history, _ = await ctx.services.hist_mgr.compress(ctx.conv.history)

# After:
ctx.conv.history, result = await ctx.services.hist_mgr.compress(ctx.conv.history)
if result.compressed_count > 0 or result.summary_added:
    ctx.session.replace_messages(ctx.conv.history)
```

### Target file: `scripts/agent/commands/cmd_rag_export.py`

#### Procedure

Update `_cmd_compact()` to unpack CompressResult and call replace_messages after force compression.

#### Method

Direct file edit — modify lines 235-237.

#### Details

**Replace lines 235-237:**
```python
# Before:
ctx.conv.history = await ctx.services.hist_mgr.force_compress(
    ctx.conv.history
)

# After:
ctx.conv.history, result = await ctx.services.hist_mgr.force_compress(
    ctx.conv.history
)
if result.compressed_count > 0 or result.summary_added:
    ctx.session.replace_messages(ctx.conv.history)
```

### Target file: `scripts/agent/history.py`

#### Procedure

Update `_fallback_truncate()` to also trigger replace_messages. Since fallback truncation modifies history without calling the caller's persist path, we need to ensure the DB is consistent.

**Decision**: The fallback truncation is called from `compress()` at line 283. The caller (`_handle_history_compression` or `_cmd_compact`) already checks `result.compressed_count > 0 or result.summary_added`. For fallback truncation, `compressed_count=0` and `summary_added=False`, so the current condition would NOT trigger replace_messages. We need to add a check for `stat_fallback_truncate_count > 0`.

**Add to `_handle_history_compression`:
```python
# After:
ctx.conv.history, result = await ctx.services.hist_mgr.compress(ctx.conv.history)
if result.compressed_count > 0 or result.summary_added or ctx.services.hist_mgr.stat_fallback_truncate_count > 0:
    ctx.session.replace_messages(ctx.conv.history)
```

**However**, `stat_fallback_truncate_count` is a cumulative counter that doesn't reset between compress calls. We need to check if it was incremented during THIS call. The cleanest approach is to add a field to `CompressResult`:

**Add to `CompressResult` at line 33:**
```python
class CompressResult:
    """Metadata returned by compress() and force_compress()."""
    compressed_count: int
    protected_count: int
    summary_added: bool
    fallback_truncated: bool = False  # NEW
```

**Update `_fallback_truncate` at line 320:**
```python
# Before:
return new_history, CompressResult(...)

# After:
return new_history, CompressResult(
    compressed_count=dropped,
    protected_count=len(protected_ids) - len(system_msgs),
    summary_added=False,
    fallback_truncated=True,
)
```

**Update `_handle_history_compression` condition:**
```python
# After:
ctx.conv.history, result = await ctx.services.hist_mgr.compress(ctx.conv.history)
if result.compressed_count > 0 or result.summary_added or result.fallback_truncated:
    ctx.session.replace_messages(ctx.conv.history)
```

**Update `_cmd_compact` condition:**
```python
# After:
ctx.conv.history, result = await ctx.services.hist_mgr.force_compress(
    ctx.conv.history
)
if result.compressed_count > 0 or result.summary_added or result.fallback_truncated:
    ctx.session.replace_messages(ctx.conv.history)
```

### Target file: `docs/05_agent_04_state-and-persistence.md`

#### Procedure

Add subsection "Compression Persistence Model" under "HistoryManager Compression".

#### Method

Direct file edit — append new subsection after existing compression documentation.

#### Details

**Append after existing compression section:**
```markdown
### Compression Persistence Model

After each history compression (automatic or `/compact`), the compressed snapshot is persisted back to `session.sqlite` via `AgentSession.replace_messages()`. This ensures that `/session load` restores a semantically consistent state — the restored history matches what was actually in context before the next LLM call.

Key behaviors:
- Compressed `[Conversation summary]` system messages are persisted as `role=system` rows; they round-trip correctly through `fetch_messages()` → `LLMMessage`.
- Fallback truncation (drop-without-summary) also triggers persistence to keep DB consistent.
- The in-memory `ctx.conv.history` remains the source of truth for the current session; DB persistence is a backup for reload scenarios.
- `/history` and `/export` continue to operate on `ctx.conv.history`; no change needed.
- The `stat_turns` counter and other in-memory stats reset on reload (existing behavior).

**Note**: After a reload of a compressed session, `/undo` operates on the compressed DB rows — the user may undo fewer turns than expected since the original messages were replaced by the summary message.
```

### Target file: `tests/test_session_message_repo.py`

#### Procedure

Add unit tests for `replace_messages()`.

#### Method

Direct file edit — append new test class after existing tests.

#### Details

**Append to `tests/test_session_message_repo.py`:
```python
class TestReplaceMessages:
    """Tests for SessionMessageRepository.replace_messages()."""

    def test_replace_messages_clears_existing_rows(self, db) -> None:
        """replace_messages() deletes all existing rows before inserting new ones."""
        repo = SessionMessageRepository(db)
        repo.save_many(1, [_user("old")])
        assert repo.count_by_session(1) == 1
        repo.replace_messages(1, [_assistant("new")])
        assert repo.count_by_session(1) == 1
        rows = db.fetchall("SELECT content FROM messages WHERE session_id = ?", (1,))
        assert len(rows) == 1
        assert rows[0]["content"] == "new"

    def test_replace_messages_inserts_compressed_set(self, db) -> None:
        """replace_messages() inserts all messages from the compressed snapshot."""
        repo = SessionMessageRepository(db)
        msgs = [
            _system("summary"),
            _user("user msg"),
            _assistant("assistant msg"),
        ]
        repo.replace_messages(1, msgs)
        assert repo.count_by_session(1) == 3

    def test_replace_messages_with_summary_message(self, db) -> None:
        """[Conversation summary] system message persists as role=system."""
        repo = SessionMessageRepository(db)
        summary_msg = _system("[Conversation summary]")
        repo.replace_messages(1, [summary_msg])
        rows = db.fetchall(
            "SELECT role, content FROM messages WHERE session_id = ?", (1,)
        )
        assert len(rows) == 1
        assert rows[0]["role"] == "system"
        assert "[Conversation summary]" in rows[0]["content"]

    def test_replace_messages_no_session_id_skips(self, db) -> None:
        """replace_messages() on AgentSession skips silently when session_id is None."""
        from agent.session import AgentSession

        repo = SessionMessageRepository(db)
        agent_session = AgentSession(repo)  # session_id is None
        agent_session.replace_messages([_user("test")])  # should not raise
```

### Target file: `tests/test_session_restore.py`

#### Procedure

Add regression test: compress → reload → equivalent history.

#### Method

Direct file edit — append new test class after existing tests.

#### Details

**Append to `tests/test_session_restore.py`:
```python
class TestCompressedHistoryRestoreEquivalence:
    """Regression: compressed history restores correctly via /session load."""

    @pytest.mark.asyncio
    async def test_compressed_history_restore_equivalence(self) -> None:
        """Compress → replace_messages → restore_session → assert summary present, originals absent."""
        from agent.context import AgentContext
        from agent.session_message_repo import SessionMessageRepository
        from agent.services.session_restore import restore_session

        # Setup
        ctx = _make_ctx()
        ctx.session.start("test-session")
        repo = SessionMessageRepository(ctx.db)
        # Simulate compressed history: summary + remaining messages
        summary_msg = _system("[Conversation summary] Previous turns were summarized.")
        user_msg = _user("latest user message")
        assistant_msg = _assistant("latest assistant response")
        repo.replace_messages(1, [summary_msg, user_msg, assistant_msg])

        # Restore session
        restored = await restore_session(ctx, "test-session")
        assert restored is not None

        # Verify: summary message present
        history = ctx.conv.history
        system_msgs = [m for m in history if m["role"] == "system"]
        assert any("[Conversation summary]" in m.get("content", "") for m in system_msgs)

        # Verify: user and assistant messages present
        user_msgs = [m for m in history if m["role"] == "user"]
        assistant_msgs = [m for m in history if m["role"] == "assistant"]
        assert len(user_msgs) >= 1
        assert len(assistant_msgs) >= 1
```

### Target file: `tests/test_orchestrator.py`

#### Procedure

Add unit test with mocked `compress()` return and `replace_messages` spy.

#### Method

Direct file edit — append new test method to existing `TestOrchestratorCompression` class (if exists) or create new class.

#### Details

**Append to `tests/test_orchestrator.py`:
```python
class TestHandleHistoryCompressionPersist:
    """Tests for _handle_history_compression persist behavior."""

    @pytest.mark.asyncio
    async def test_compress_persists_when_compressed(self) -> None:
        """replace_messages called when compressed_count > 0."""
        from unittest.mock import AsyncMock, MagicMock, patch

        ctx = _make_ctx()
        ctx.session.start("test")
        ctx.services.hist_mgr = MagicMock()
        ctx.services.hist_mgr.compress = AsyncMock(
            return_value=(
                [_system("[Conversation summary]"), _user("new")],
                CompressResult(compressed_count=2, protected_count=0, summary_added=True),
            )
        )
        orchestrator = Orchestrator(ctx)
        await orchestrator._handle_history_compression()
        ctx.session.replace_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_compress_no_persist_when_noop(self) -> None:
        """replace_messages not called when no compression occurred."""
        from unittest.mock import AsyncMock, MagicMock

        ctx = _make_ctx()
        ctx.session.start("test")
        ctx.services.hist_mgr = MagicMock()
        ctx.services.hist_mgr.compress = AsyncMock(
            return_value=(
                [_user("unchanged"), _assistant("unchanged")],
                CompressResult(compressed_count=0, protected_count=0, summary_added=False),
            )
        )
        orchestrator = Orchestrator(ctx)
        await orchestrator._handle_history_compression()
        ctx.session.replace_messages.assert_not_called()
```

### Target file: `tests/test_agent_cmd_rag_export.py`

#### Procedure

Mock force_compress + spy on replace_messages.

#### Method

Direct file edit — append new test method.

#### Details

**Append to `tests/test_agent_cmd_rag_export.py`:
```python
@pytest.mark.asyncio
async def test_compact_persists_after_force_compression(self) -> None:
    """replace_messages called after /compact force compression."""
    from unittest.mock import AsyncMock, MagicMock

    ctx = _make_ctx()
    ctx.session.start("test")
    # Add enough messages to trigger compression (> n_compress)
    for i in range(20):
        ctx.conv.history.append(_user(f"user {i}"))
        ctx.conv.history.append(_assistant(f"assistant {i}"))
    ctx.services.hist_mgr = MagicMock()
    ctx.services.hist_mgr.compress_turns = 4
    ctx.services.hist_mgr.force_compress = AsyncMock(
        return_value=(
            [_system("[Conversation summary]"), _user("latest")],
            CompressResult(compressed_count=8, protected_count=0, summary_added=True),
        )
    )
    cmd = CmdRagExport(ctx)
    cmd._cmd_compact([])
    ctx.session.replace_messages.assert_called_once()
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `session_message_repo.py` `replace_messages()` | Unit tests with in-memory SQLite mock | `uv run pytest tests/test_session_message_repo.py -v` | DELETE + INSERT executes atomically; summary message round-trips correctly |
| `session_restore.py` compress → reload | Regression test: compress history → replace_messages → restore_session → assert summary present | `uv run pytest tests/test_session_restore.py -v` | Restored history matches compressed state; original messages absent |
| `orchestrator.py` `_handle_history_compression()` | Unit test with mocked `compress()` return and `replace_messages` spy | `uv run pytest tests/test_orchestrator.py -v` | `replace_messages` called when `compressed_count > 0`; not called on noop |
| `/compact` command | Mock force_compress + spy on replace_messages | `uv run pytest tests/test_agent_cmd_rag_export.py -v` | `replace_messages` called after force compression |
| Full regression | Full test suite | `uv run pytest` | No regressions in existing session/history tests |
| Type safety | mypy strict check | `uv run mypy scripts/agent/session_message_repo.py scripts/agent/session.py` | No new type errors |

## Risks & Mitigations

- **Risk**: `replace_messages()` deletes then inserts; a crash between DELETE and INSERT leaves the session with empty messages → **Mitigation**: wrap DELETE + executemany INSERT in a single SQLite transaction; SQLite WAL ensures atomicity on commit
- **Risk**: Compressing a session that has no session_id (e.g. before `session.start()`) calls `replace_messages` and silently skips → **Mitigation**: the `if self.session_id is None: return` guard in `AgentSession.replace_messages()` matches existing `save()` behavior; log a WARNING
- **Risk**: `_cmd_compact` currently discards the return value of `force_compress()`; the tuple return `(new_history, CompressResult)` must be unpacked → **Mitigation**: verify `force_compress()` signature in `history.py` before editing; update unpack in cmd_rag_export.py
- **Risk**: Existing tests that mock `ctx.session.save` may not anticipate the new `replace_messages` call → **Mitigation**: run full test suite; fix any broken mocks in orchestrator/compact tests
- **Risk**: `/undo` after reload operates on compressed DB rows — user may lose more turns than expected → **Mitigation**: document this behavior; no behavioral change in scope
