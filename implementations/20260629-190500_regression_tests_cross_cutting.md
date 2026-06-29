# Implementation: Regression tests for cross-cutting inconsistencies — Current behavior vs Known discrepancy

## Goal

Add regression tests that lock down five cross-cutting design inconsistencies by documenting current behavior in test assertions, preventing future regressions when these areas are modified.

## Scope

- **In-Scope**:
  - New test file: `tests/test_regression_history_compress_reload.py` — compression → session reload consistency
  - New test file: `tests/test_regression_diagnostic_persist.py` — diagnostic persistence and restore-path
  - New test file: `tests/test_regression_undo_artifact.py` — `/undo` + `/tool show` artifact consistency
  - New test file: `tests/test_regression_memory_branch.py` — branch-aware memory retrieval
  - New test file: `tests/test_regression_jsonl_config.py` — JSONL config resolution and naming

- **Out-of-Scope**:
  - General performance / load testing
  - Broad unrelated CLI test expansion
  - Modifying any production source file

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether compressed history (summary message) is faithfully stored/reloaded via `session.save()` → `fetch_messages()` | Resolved: `HistoryManager.compress()` returns `CompressResult(summary_added=True/False)`; summary message is appended to history before `save_many()`. The summary message format is a system message with role="system" containing the compressed text. |
| UNK-02 | Whether `DiagnosticStore.fetch()` excludes diagnostics from a different session when `session_id` is NULL | Not resolved — needs confirmation; test will document current behavior and mark with `# Needs confirmation` |
| UNK-03 | Whether `session.undo_last_turn()` and `undo_last_turn(ctx)` delete the same set of messages | Resolved: `undo_service.py:46` calls `ctx.session.undo_last_turn()`, which deletes from DB rows where `message_id >= last_user_id`. History trimming in `undo_service.py:44` removes `ctx.conv.history[cut_idx:]` where `cut_idx = last_user_idx - memory_injected_block_count`. These are different scopes (DB vs in-memory history) but coordinated via the same service. |
| UNK-04 | Whether `top_semantic()` branch filter `(? = '' OR branch = '' OR branch = ?)` returns entries with `branch=''` even when a non-empty branch is passed | Resolved: YES — untagged (`branch=''`) entries always match regardless of the requested branch. This is the "untagged always matches" policy, not a bug. Documented in `retriever.py:334`. |
| UNK-05 | JSONL config: whether `memory_jsonl_dir` is used as a directory or as a full file path | Resolved: `memory_jsonl_dir` is a directory. Factory wires it as `{ctx.cfg.memory.memory_jsonl_dir}/memories.jsonl` (verified at `factory.py:286`). Config field is named `memory_jsonl_dir` in `config_dataclasses.py:297`. |

## Implementation Steps

### Target file: `tests/test_regression_history_compress_reload.py`

#### Procedure
Create new test file with two scenarios for compression → reload consistency.

#### Method
Direct file creation — new test file following existing patterns from `test_history_manager.py`.

#### Details

**Scenario A: Successful compression → reload includes summary**

```python
async def test_compress_then_reload_includes_summary(
    tmp_path: pathlib.Path,
) -> None:
    """Verify that after compression, the summary message is persisted and reloaded."""
    # 1. Create in-memory session with messages
    db_path = tmp_path / "test.db"
    session = AgentSession(session_id=1, db_path=str(db_path))
    
    # Insert user + assistant messages
    await session.save_many([
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi there"),
    ])
    
    # 2. Compress with mocked LLM
    manager = HistoryManager(session=session, llm_client=AsyncMock())
    result = await manager.compress()
    
    assert result.summary_added is True
    
    # 3. Reload and verify summary is present
    reloaded = session.fetch_messages(1)
    assert any(m.role == "system" and "compressed" in m.content.lower() for m in reloaded)
```

**Scenario B: Failed compression → fallback truncation still produces valid history**

```python
async def test_compress_failure_fallback_reload_valid(
    tmp_path: pathlib.Path,
) -> None:
    """Verify that LLM failure during compression doesn't corrupt history."""
    db_path = tmp_path / "test.db"
    session = AgentSession(session_id=1, db_path=str(db_path))
    
    # Insert messages
    await session.save_many([
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi there"),
    ])
    
    # Compress with LLM that fails
    manager = HistoryManager(session=session, llm_client=AsyncMock(side_effect=Exception("LLM fail")))
    result = await manager.compress()
    
    assert result.summary_added is False
    # Reload should not raise or return empty
    reloaded = session.fetch_messages(1)
    assert len(reloaded) > 0
```

### Target file: `tests/test_regression_diagnostic_persist.py`

#### Procedure
Create new test file with three scenarios for diagnostic persistence.

#### Method
Direct file creation — new test file following `_FakeSQLiteHelper` pattern from `test_diagnostic_store.py`.

#### Details

**Scenario A: Cross-session isolation**

```python
def test_diagnostic_cross_session_isolation(
    tmp_path: pathlib.Path,
) -> None:
    """Verify that DiagnosticStore.fetch() excludes diagnostics from different sessions."""
    db_path = tmp_path / "test.db"
    
    # Create two sessions with diagnostic stores
    store1 = DiagnosticStore(db_path=str(db_path), session_id=1)
    store2 = DiagnosticStore(db_path=str(db_path), session_id=2)
    
    # Save diagnostics to session 1 only
    store1.save(kind="session_summary", content="summary for session 1")
    
    # Fetch from session 2 should return empty
    results = store2.fetch()
    assert results == []
    
    # Fetch from session 1 should return the entry
    results = store1.fetch()
    assert len(results) == 1
```

**Scenario B: NULL session_id — entry exists and is retrievable**

```python
def test_diagnostic_null_session_id(
    tmp_path: pathlib.Path,
) -> None:
    """Verify that diagnostics saved with session_id=None are still stored."""
    db_path = tmp_path / "test.db"
    
    # Save diagnostic without session_id
    store = DiagnosticStore(db_path=str(db_path), session_id=None)
    store.save(kind="llm_transport_error", content="connection error")
    
    # Should be retrievable via fetch_all()
    results = store.fetch_all()
    assert len(results) == 1
```

**Scenario C: AgentSession.save_diagnostic() writes to DiagnosticStore, not messages table**

```python
def test_save_diagnostic_uses_diagnostics_store(
    tmp_path: pathlib.Path,
    mocker: pytest.MockFixture,
) -> None:
    """Verify that AgentSession.save_diagnostic() routes to DiagnosticStore."""
    db_path = tmp_path / "test.db"
    mock_helper = mocker.patch("agent.session.SQLiteHelper")
    
    session = AgentSession(session_id=1, db_path=str(db_path))
    session.save_diagnostic("transport error")
    
    # Should have called DiagnosticStore.save(), NOT messages table insert
    mock_helper.return_value.__enter__.return_value.execute.assert_any_call(
        mocker.ANY,  # INSERT into session_diagnostics
        mocker.ANY,
    )
```

### Target file: `tests/test_regression_undo_artifact.py`

#### Procedure
Create new test file with four scenarios for undo + artifact consistency.

#### Method
Direct file creation — new test file using in-memory SQLite and MagicMock patterns.

#### Details

**Scenario A: session.undo_last_turn() deletes from DB**

```python
def test_undo_last_turn_deletes_from_db(
    tmp_path: pathlib.Path,
) -> None:
    """Verify that AgentSession.undo_last_turn() deletes messages from DB."""
    db_path = tmp_path / "test.db"
    
    session = AgentSession(session_id=1, db_path=str(db_path))
    
    # Insert user + assistant messages
    await session.save_many([
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi there"),
    ])
    
    deleted = session.undo_last_turn()
    
    assert deleted == 2  # Both user and assistant messages deleted
    # Verify DB is empty for this session
    rows = session._message_repo._db.fetchall(
        "SELECT COUNT(*) FROM messages WHERE session_id = ?", (1,)
    )
    assert rows[0][0] == 0
```

**Scenario B: undo_service.undo_last_turn() coordinates history + DB**

```python
def test_undo_last_turn_service_coordinates_history_and_db(
    tmp_path: pathlib.Path,
) -> None:
    """Verify that undo_last_turn(ctx) trims both history and DB."""
    db_path = tmp_path / "test.db"
    
    session = AgentSession(session_id=1, db_path=str(db_path))
    await session.save_many([
        LLMMessage(role="system", content="system prompt"),
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi there"),
    ])
    
    # Build context mock
    ctx = MagicMock()
    ctx.session = session
    ctx.conv.history = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]
    ctx.stats = MagicMock()
    ctx.stats.stat_turns = 1
    
    from agent.services.undo_service import undo_last_turn
    
    result = undo_last_turn(ctx)
    
    assert result.n_removed == 3  # user + assistant + memory_injected blocks
    assert len(ctx.conv.history) == 1  # only system message remains
    ctx.session.undo_last_turn.assert_called_once()
```

**Scenario C: History length after undo matches DB row count**

```python
def test_undo_history_db_parity(
    tmp_path: pathlib.Path,
) -> None:
    """Verify that history length after undo matches DB row count."""
    db_path = tmp_path / "test.db"
    
    session = AgentSession(session_id=1, db_path=str(db_path))
    
    # Insert 3 messages (system + user + assistant)
    await session.save_many([
        LLMMessage(role="system", content="system"),
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi"),
    ])
    
    # Undo the last turn (user + assistant)
    session.undo_last_turn()
    
    # History should have 1 message (system only)
    assert len(session.fetch_messages(1)) == 1
```

**Scenario D: Tool results survive undo**

```python
def test_tool_results_survive_undo(
    tmp_path: pathlib.Path,
) -> None:
    """Verify that /tool show artifacts are not deleted by undo."""
    db_path = tmp_path / "test.db"
    
    # Insert tool result into tool_results table
    with SQLiteHelper("session").open(write_mode=True) as db:
        db.execute(
            "INSERT INTO tool_results (turn, content, format) VALUES (?, ?, ?)",
            (1, '{"tool": "read_file"}', "json"),
        )
    
    # Undo the turn
    session = AgentSession(session_id=1, db_path=str(db_path))
    session.undo_last_turn()
    
    # Tool result should still exist (undo only deletes from messages table)
    with SQLiteHelper("session").open(write_mode=True) as db:
        rows = db.fetchall(
            "SELECT COUNT(*) FROM tool_results WHERE turn = ?", (1,)
        )
        assert rows[0][0] == 1
```

### Target file: `tests/test_regression_memory_branch.py`

#### Procedure
Create new test file with four scenarios for branch-aware memory retrieval.

#### Method
Direct file creation — new test file using in-memory SQLite with `_SCHEMA_SQL` pattern from `test_memory_retriever.py`.

#### Details

**Scenario A: top_semantic includes same-branch entries**

```python
def test_top_semantic_includes_same_branch(
    tmp_path: pathlib.Path,
) -> None:
    """top_semantic(branch='feat-x') returns entries with branch='feat-x'."""
    db_path = tmp_path / "test.db"
    
    # Create schema
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(_SCHEMA_SQL)
        _insert_memories(conn, [
            {
                "memory_id": "feat-x-id",
                "memory_type": "semantic",
                "branch": "feat-x",
                "importance": 0.9,
                "content": "feat-x rule",
            },
        ])
    
    retriever = HybridRetriever()
    entries = retriever.top_semantic(branch="feat-x", limit=10, db_path=str(db_path))
    
    assert any(e.memory_id == "feat-x-id" for e in entries)
```

**Scenario B: top_semantic includes untagged entries regardless of branch (documents current policy)**

```python
def test_top_semantic_includes_untagged_entries(
    tmp_path: pathlib.Path,
) -> None:
    """top_semantic(branch='feat-x') ALSO returns entries with branch='' (untagged always matches)."""
    db_path = tmp_path / "test.db"
    
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(_SCHEMA_SQL)
        _insert_memories(conn, [
            {
                "memory_id": "untagged-id",
                "memory_type": "semantic",
                "branch": "",  # untagged
                "importance": 0.9,
                "content": "global rule",
            },
        ])
    
    retriever = HybridRetriever()
    entries = retriever.top_semantic(branch="feat-x", limit=10, db_path=str(db_path))
    
    # Current behavior: untagged entries are always included
    # This is the "untagged always matches" policy — documented by this test
    assert any(e.memory_id == "untagged-id" for e in entries)
```

**Scenario C: top_semantic excludes different-branch entries but includes untagged**

```python
def test_top_semantic_excludes_other_branch_includes_untagged(
    tmp_path: pathlib.Path,
) -> None:
    """top_semantic(branch='feat-x') excludes feat-y but includes untagged."""
    db_path = tmp_path / "test.db"
    
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(_SCHEMA_SQL)
        _insert_memories(conn, [
            {
                "memory_id": "feat-y-id",
                "memory_type": "semantic",
                "branch": "feat-y",
                "importance": 0.9,
                "content": "feat-y rule",
            },
            {
                "memory_id": "untagged-id",
                "memory_type": "semantic",
                "branch": "",
                "importance": 0.9,
                "content": "global rule",
            },
        ])
    
    retriever = HybridRetriever()
    entries = retriever.top_semantic(branch="feat-x", limit=10, db_path=str(db_path))
    
    assert not any(e.memory_id == "feat-y-id" for e in entries)
    assert any(e.memory_id == "untagged-id" for e in entries)
```

**Scenario D: HybridRetriever.search() applies branch context boost**

```python
def test_hybrid_search_branch_context_boost(
    tmp_path: pathlib.Path,
) -> None:
    """HybridRetriever.search(branch='feat-x') applies _context_boost for matching branch."""
    db_path = tmp_path / "test.db"
    
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(_SCHEMA_SQL)
        _insert_memories(conn, [
            {
                "memory_id": "feat-x-hit",
                "memory_type": "semantic",
                "branch": "feat-x",
                "importance": 0.5,
                "content": "feature-specific content",
            },
            {
                "memory_id": "no-branch-hit",
                "memory_type": "semantic",
                "branch": "",
                "importance": 0.5,
                "content": "feature-specific content",
            },
        ])
    
    retriever = HybridRetriever()
    
    # Search with branch='feat-x' — feat-x entry should have context boost
    hits_with_branch = retriever.search(
        MemoryQuery(query="feature-specific", memory_type="semantic"),
        branch="feat-x",
        db_path=str(db_path),
    )
    
    # feat-x entry score should be higher than no-branch entry (context_boost adds +0.15)
    feat_x_hit = next((h for h in hits_with_branch if h.entry.memory_id == "feat-x-hit"), None)
    no_branch_hit = next((h for h in hits_with_branch if h.entry.memory_id == "no-branch-hit"), None)
    
    # Both should be present (untagged always matches), but feat-x should score higher
    assert feat_x_hit is not None
    assert no_branch_hit is not None
    assert feat_x_hit.score > no_branch_hit.score
```

### Target file: `tests/test_regression_jsonl_config.py`

#### Procedure
Create new test file with four scenarios for JSONL config resolution and naming.

#### Method
Direct file creation — new test file using `tmp_path` pytest fixture.

#### Details

**Scenario A: JSONL roundtrip via factory wiring**

```python
def test_jsonl_roundtrip_via_factory_wiring(
    tmp_path: pathlib.Path,
) -> None:
    """JsonlMemoryStore at {memory_jsonl_dir}/memories.jsonl roundtrips correctly."""
    jsonl_dir = tmp_path / "memory"
    jsonl_dir.mkdir()
    
    store = JsonlMemoryStore(f"{jsonl_dir}/memories.jsonl")
    
    entry = MemoryEntry(
        memory_id="roundtrip-id",
        memory_type="semantic",
        source_type="rule",
        session_id=None,
        turn_id=None,
        project="proj",
        repo="repo",
        branch="main",
        content="test content",
        summary="test summary",
        tags=["test"],
        importance=0.5,
        pinned=False,
        created_at="2020-01-01T00:00:00Z",
        updated_at="2020-01-01T00:00:00Z",
    )
    
    store.write([entry])
    read_entries = store.read_all()
    
    assert len(read_entries) == 1
    assert read_entries[0].memory_id == entry.memory_id
```

**Scenario B: Missing memory_type raises JsonlFormatError**

```python
def test_jsonl_missing_memory_type_raises(
    tmp_path: pathlib.Path,
) -> None:
    """_entry_from_dict raises JsonlFormatError when memory_type is missing."""
    jsonl_dir = tmp_path / "memory"
    jsonl_dir.mkdir()
    
    store = JsonlMemoryStore(f"{jsonl_dir}/memories.jsonl")
    
    # Write a JSONL entry without memory_type
    with open(store._path, "w") as f:
        f.write(json.dumps({
            "memory_id": "bad-id",
            "content": "no type",
            "branch": "",
            "importance": 0.5,
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
        }) + "\n")
    
    with pytest.raises(JsonlFormatError):
        store.read_all()
```

**Scenario C: Empty memory_jsonl_dir with use_memory_layer=True raises ConfigValidationError**

```python
def test_jsonl_config_validation_empty_dir(
    tmp_path: pathlib.Path,
) -> None:
    """AgentConfig with use_memory_layer=True and empty memory_jsonl_dir raises ConfigValidationError."""
    # Simulate config validation
    cfg = AgentConfig(
        memory=MemoryConfig(
            use_memory_layer=True,
            memory_jsonl_dir="",  # Empty — should fail validation
        ),
    )
    
    with pytest.raises(ConfigValidationError):
        cfg._validate_memory_jsonl_dir()
```

**Scenario D: JSONL filename is memories.jsonl (regression guard against naming drift)**

```python
def test_jsonl_filename_is_memories_jsonl(
    tmp_path: pathlib.Path,
) -> None:
    """Factory wires {memory_jsonl_dir}/memories.jsonl — not memory.jsonl or archive.jsonl."""
    jsonl_dir = tmp_path / "memory"
    jsonl_dir.mkdir()
    
    # Write to the factory-wired path
    expected_path = f"{jsonl_dir}/memories.jsonl"
    store = JsonlMemoryStore(expected_path)
    
    entry = MemoryEntry(
        memory_id="naming-id",
        memory_type="semantic",
        source_type="rule",
        session_id=None,
        turn_id=None,
        project="",
        repo="",
        branch="",
        content="test",
        summary="test",
        tags=[],
        importance=0.5,
        pinned=False,
        created_at="2020-01-01T00:00:00Z",
        updated_at="2020-01-01T00:00:00Z",
    )
    
    store.write([entry])
    
    # Read back from the same path — should succeed
    read_entries = JsonlMemoryStore(expected_path).read_all()
    assert len(read_entries) == 1
    assert read_entries[0].memory_id == "naming-id"
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `test_regression_history_compress_reload.py` | Unit — mock LLM HTTP, in-memory history list | `uv run pytest tests/test_regression_history_compress_reload.py -v` | All scenarios pass; `CompressResult.summary_added` is asserted |
| `test_regression_diagnostic_persist.py` | Unit — in-memory SQLite, `_FakeSQLiteHelper` pattern | `uv run pytest tests/test_regression_diagnostic_persist.py -v` | Cross-session isolation and NULL session_id cases pass |
| `test_regression_undo_artifact.py` | Unit — in-memory SQLite for DB side; `MagicMock` for context side | `uv run pytest tests/test_regression_undo_artifact.py -v` | DB count and history length match; tool results survive undo |
| `test_regression_memory_branch.py` | Unit — in-memory SQLite with `_SCHEMA_SQL` | `uv run pytest tests/test_regression_memory_branch.py -v` | Branch filter behavior documented; UNK-04 cases marked |
| `test_regression_jsonl_config.py` | Unit — `tmp_path` fixture | `uv run pytest tests/test_regression_jsonl_config.py -v` | Roundtrip, validation constraint, and naming regression tests pass |
| Full suite | Regression guard | `uv run pytest` | Zero new failures introduced |
| Lint | Style | `uv run ruff check tests/test_regression_*.py` | No violations |
| Type check | Correctness | `uv run mypy tests/test_regression_*.py --ignore-missing-imports` | No errors |

## Risks & Mitigations

- **Risk**: UNK-02 (NULL session_id cross-session isolation) — current behavior may be incorrect → test documents wrong expectation → **Mitigation**: Mark Scenario B with `# Needs confirmation` comment; use `pytest.mark.xfail(strict=False)` if behavior is ambiguous; update after design decision.
- **Risk**: `HistoryManager.compress()` requires an async LLM call → test complexity → **Mitigation**: Use `AsyncMock` as in `test_history_manager.py`; reuse `_make_manager()` helper pattern.
- **Risk**: `AgentSession.undo_last_turn()` uses real SQLiteHelper → test needs full DB setup → **Mitigation**: Use in-memory SQLite with `tmp_path`; no need for `_FakeSQLiteHelper` since we control the DB path directly.
- **Risk**: JSONL filename wiring (UNK-05) is in `factory.py` which has complexity C (11) and is frequently modified → **Mitigation**: Read factory before writing test; do not hard-code internal path logic; test only the public contract (config field → file path segment).

## Files Changed

- `tests/test_regression_history_compress_reload.py` — new: compression → session reload consistency tests
- `tests/test_regression_diagnostic_persist.py` — new: diagnostic persistence and restore-path tests
- `tests/test_regression_undo_artifact.py` — new: `/undo` + `/tool show` artifact consistency tests
- `tests/test_regression_memory_branch.py` — new: branch-aware memory retrieval tests
- `tests/test_regression_jsonl_config.py` — new: JSONL config resolution and naming regression tests
