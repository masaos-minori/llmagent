# Implementation: Resolve diagnostic persistence doc/code inconsistency

## Goal

Resolve the doc/code inconsistency around diagnostic persistence by removing the obsolete `role="diagnostic"` references from docs and aligning all documentation to the single canonical model: `DiagnosticStore` → `session_diagnostics` table.

## Scope

- **In-Scope**:
  - Fix `05_agent_09_data-layer.md`: remove `diagnostic` from `messages.role` enum; remove stale "excluded from fetch_messages" sentence; add `session_diagnostics` table reference
  - Fix `05_agent_04_state-and-persistence.md`: clarify `fetch_messages()` never sees diagnostic data (because it is in a separate table), remove the contradictory sentence at L131
  - Fix `05_agent_03_turn-processing-flow.md`: align Partial-Completion Model table to canonical model (already partially correct; minor clarification needed)
  - Add tests that verify: (1) `save_diagnostic()` writes to `session_diagnostics`, NOT to `messages`; (2) `fetch_messages()` returns only messages-table rows (no diagnostic bleed-through); (3) session restore (`restore_session`) never includes diagnostic data
  - Update `agent/session.py` docstring for `save_diagnostic()` to reference canonical store
- **Out-of-Scope**:
  - Full redesign of the observability subsystem
  - Changing what counts as a diagnostic event
  - Changing the `DiagnosticStore` API or `session_diagnostics` schema
  - Any RAG, MCP, or EventBus layer changes

## Assumptions

- The canonical persistence model is `DiagnosticStore` → `session_diagnostics` table (confirmed by code in `diagnostic_store.py`, `session.py`, `schema_sql.py`)
- The `messages` table has never had a `role="diagnostic"` row written in the current codebase; the column enum listing in `05_agent_09_data-layer.md` L39 is a doc artifact from an older design
- `fetch_messages()` (`session_message_repo.py`) issues no `WHERE role != 'diagnostic'` filter because there are no diagnostic rows in `messages` — the filter is unnecessary, not an oversight
- The `diagnostics.jsonl` sidecar written by `repl._persist_session_diagnostics()` is supplementary and does not need to be the primary documented path

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? |
|---|---|---|---|---|
| UNK-01 | Were diagnostic rows ever written to `messages` in any migration path or legacy code path? | No migration script checked; no git blame on schema | Run `git log --all -p -- scripts/db/schema_sql.py` and grep for `diagnostic` in old SQL | No |
| UNK-02 | Does `_persist_session_diagnostics` in `repl.py` need to be documented as a supplementary/deprecated path? | Doc `05_agent_04` mentions it as "may be deprecated" (L129) | Confirm intent with operator; for now doc as "supplementary, may be deprecated" | No |
| UNK-03 | Is `AgentSession.save_diagnostic()` still called anywhere besides `orchestrator.py`? | Not verified exhaustively | `rg 'save_diagnostic' scripts/` to confirm call sites | No |

## Verification Results

### 1. Code confirms diagnostics go to `session_diagnostics`, NOT `messages`

**File**: `scripts/agent/session.py:52-56`
```python
def save_diagnostic(self, content: str) -> None:
    """Persist a diagnostic-only message; not included in normal history retrieval."""
    self._diagnostic_store.save(
        self.session_id, kind="llm_transport_error", content=content
    )
```

**File**: `scripts/agent/diagnostic_store.py:35`
```python
"INSERT INTO session_diagnostics"
```

- No code writes diagnostic data to the `messages` table ✓

### 2. save_diagnostic() call sites

**File**: `scripts/agent/session.py:52` — only definition found in scripts/
- Only one caller needed; no legacy paths to worry about ✓

### 3. Docs incorrectly reference `role="diagnostic"` in messages

**File**: `docs/05_agent_09_data-layer.md:39`
```
| `role` | TEXT | `user` / `assistant` / `tool` / `system` / `diagnostic` |
```
- `diagnostic` is NOT a valid role in the `messages` table — needs removal

**File**: `docs/05_agent_09_data-layer.md:45`
```
diagnostic role messages are written by AgentSession.save_diagnostic() to persist
```
- Misleading — `save_diagnostic()` writes to `session_diagnostics`, not `messages` — needs correction

**File**: `docs/05_agent_09_data-layer.md:68`
```
role のバリデーション (user / assistant / tool / system / diagnostic)
```
- Role validation in `messages` does NOT include `diagnostic` — needs removal

**File**: `docs/05_agent_03_turn-processing-flow.md:123`
```
role "diagnostic", NOT added to ctx.conv.history
```
- The role doesn't exist in messages at all; this is misleading — needs correction

**File**: `docs/05_agent_03_turn-processing-flow.md:127`
```
DB queries on the messages table (role = "diagnostic")
```
- Diagnostics are queried from `session_diagnostics`, not `messages` — needs correction

**File**: `docs/05_agent_04_state-and-persistence.md:130`
```
fetch_messages() no longer filters out diagnostic role — diagnostic data is in its own table
```
- Contradictory — says "no longer filters" but also says "diagnostic data is in its own table"; should be rephrased

### 4. Partial-Completion Model table (line 160-163) is already correct

**File**: `docs/05_agent_03_turn-processing-flow.md:162`
```
| LLMTransportError with non-empty partial_text | tool_result_store (tool_name="llm_partial_completion") + session_diagnostics table |
```
- Correctly references `session_diagnostics`, not `messages` ✓

## Implementation

### Target file: `docs/05_agent_09_data-layer.md`

#### Procedure

Remove `diagnostic` from messages.role enum; correct misleading text; add session_diagnostics reference.

#### Method

Direct file edit — targeted replacements.

#### Details

**Change 1: Fix line 39 — remove diagnostic from role enum**
```markdown
# Before:
| `role` | TEXT | `user` / `assistant` / `tool` / `system` / `diagnostic` |

# After:
| `role` | TEXT | `user` / `assistant` / `tool` / `system` |
```

**Change 2: Fix line 45 — correct misleading text about diagnostic role**
```markdown
# Before:
diagnostic role messages are written by AgentSession.save_diagnostic() to persist

# After:
Diagnostic data is written by AgentSession.save_diagnostic() to the session_diagnostics table, NOT to the messages table.
```

**Change 3: Fix line 68 — remove diagnostic from role validation**
```markdown
# Before:
role のバリデーション (user / assistant / tool / system / diagnostic)

# After:
role のバリデーション (user / assistant / tool / system)
```

**Change 4: Add session_diagnostics table reference after messages section**
```markdown
### `session_diagnostics` table

Stores diagnostic events (LLM transport errors, guard hints, partial completions). Separate from the `messages` table — never queried by `fetch_messages()`.

Schema columns: `id`, `session_id`, `kind`, `content`, `workflow_id`, `task_id`, `created_at`.
```

### Target file: `docs/05_agent_04_state-and-persistence.md`

#### Procedure

Remove contradictory sentence at L131; replace with clear statement about diagnostics being in separate table.

#### Method

Direct file edit — targeted replacement.

#### Details

**Change 5: Fix line 130 — remove contradictory sentence**
```markdown
# Before:
fetch_messages() no longer filters out diagnostic role — diagnostic data is in its own table

# After:
Diagnostic data is stored in the session_diagnostics table via DiagnosticStore; it is never present in messages and therefore never returned by fetch_messages().
```

### Target file: `docs/05_agent_03_turn-processing-flow.md`

#### Procedure

Remove stale role="diagnostic" references at lines 123 and 127.

#### Method

Direct file edit — targeted replacements.

#### Details

**Change 6: Fix line 123 — remove misleading role reference**
```markdown
# Before:
role "diagnostic", NOT added to ctx.conv.history

# After:
NOT added to ctx.conv.history (stored in session_diagnostics table via DiagnosticStore)
```

**Change 7: Fix line 127 — correct DB query reference**
```markdown
# Before:
DB queries on the messages table (role = "diagnostic")

# After:
DB queries on the session_diagnostics table
```

### Target file: `scripts/agent/session.py`

#### Procedure

Update `save_diagnostic()` docstring to reference canonical store.

#### Method

Direct file edit — targeted replacement.

#### Details

**Change 8: Fix line 53 — update docstring**
```python
# Before:
"""Persist a diagnostic-only message; not included in normal history retrieval."""

# After:
"""Persist a diagnostic event to the session_diagnostics table via DiagnosticStore; never written to messages."""
```

### Target file: `tests/test_agent_session.py`

#### Procedure

Add tests for diagnostic isolation.

#### Method

Direct file edit — append new test class after existing tests.

#### Details

**Append to `tests/test_agent_session.py`:
```python
class TestAgentSessionDiagnosticIsolation:
    """Tests verifying diagnostic data is isolated from messages."""

    def test_save_diagnostic_does_not_write_to_messages(self, db) -> None:
        """save_diagnostic() writes to session_diagnostics, NOT to messages."""
        repo = SessionMessageRepository(db)
        diag_store = DiagnosticStore(db)
        agent_session = AgentSession(repo, diag_store, session_id=1)
        agent_session.save_diagnostic("test diagnostic")
        # Verify no row in messages
        msg_rows = db.fetchall("SELECT 1 FROM messages WHERE session_id = ?", (1,))
        assert len(msg_rows) == 0, "Diagnostic should not be written to messages"
        # Verify row in session_diagnostics
        diag_rows = db.fetchall(
            "SELECT 1 FROM session_diagnostics WHERE session_id = ?", (1,)
        )
        assert len(diag_rows) == 1, "Diagnostic should be written to session_diagnostics"

    def test_fetch_messages_never_returns_diagnostics(self, db) -> None:
        """fetch_messages() returns only messages-table rows; no diagnostic bleed-through."""
        repo = SessionMessageRepository(db)
        diag_store = DiagnosticStore(db)
        agent_session = AgentSession(repo, diag_store, session_id=1)
        # Insert a diagnostic row directly into session_diagnostics
        diag_store.save(1, kind="test", content="test diagnostic")
        # Insert a message row
        repo.save_many(1, [_user("test message")])
        # fetch_messages should return only the message, not diagnostic data
        messages = agent_session.fetch_messages(1)
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
```

### Target file: `tests/test_session_restore.py`

#### Procedure

Add test: restore never includes diagnostic data.

#### Method

Direct file edit — append new test method to existing class.

#### Details

**Append to `tests/test_session_restore.py`:
```python
@pytest.mark.asyncio
async def test_restore_does_not_include_diagnostics(self) -> None:
    """restore_session never includes diagnostic data in history."""
    from agent.context import AgentContext
    from agent.session_message_repo import SessionMessageRepository
    from agent.services.session_restore import restore_session

    ctx = _make_ctx()
    ctx.session.start("test")
    repo = SessionMessageRepository(ctx.db)
    # Insert a diagnostic row directly
    diag_store = DiagnosticStore(ctx.db)
    diag_store.save(1, kind="test", content="test diagnostic")
    # Insert a message row
    repo.save_many(1, [_user("test message")])

    restored = await restore_session(ctx, "test")
    assert restored is not None
    history = ctx.conv.history
    # Verify no diagnostic role in restored history
    for msg in history:
        assert msg.get("role") != "diagnostic", (
            f"Restored history should not contain diagnostic data; got {msg.get('role')}"
        )
```

### Target file: `tests/test_session_message_repo.py`

#### Procedure

Add test: fetch_messages returns all message roles except none.

#### Method

Direct file edit — append new test method.

#### Details

**Append to `tests/test_session_message_repo.py`:
```python
def test_fetch_messages_returns_all_message_roles(self, db) -> None:
    """fetch_messages returns user/assistant/tool/system roles; no diagnostic contamination assumed."""
    repo = SessionMessageRepository(db)
    # Insert rows with each valid role
    repo.save_many(1, [
        _user("user msg"),
        _assistant("assistant msg"),
        _tool("tool_name", "tool content"),
        _system("system msg"),
    ])
    messages = repo.fetch_messages(1)
    roles = {m["role"] for m in messages}
    assert roles == {"user", "assistant", "tool", "system"}
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_09_data-layer.md` | Manual review of role enum and new table section | Read + diff | `diagnostic` absent from messages.role; `session_diagnostics` table documented |
| `docs/05_agent_04_state-and-persistence.md` | Manual review of fetch_messages paragraph | Read + diff | No contradictory sentence; clear statement that diagnostics are in separate table |
| `docs/05_agent_03_turn-processing-flow.md` | Manual review of Partial-Completion table | Read + diff | Table references `session_diagnostics` via `DiagnosticStore`; no role="diagnostic" references |
| `scripts/agent/session.py` | Docstring review | Read | `save_diagnostic()` docstring references `session_diagnostics` table |
| New tests in `test_agent_session.py` | Unit test (in-memory SQLite, patch SQLiteHelper) | `uv run pytest tests/test_agent_session.py -v` | All new tests pass |
| New test in `test_session_restore.py` | Unit test (mock fetch_messages) | `uv run pytest tests/test_session_restore.py -v` | Passes |
| Regression | Full test suite | `uv run pytest` | No regressions |

## Risks & Mitigations

- **Risk**: Removing `diagnostic` from messages.role enum in docs could confuse readers who recall legacy behavior → **Mitigation**: Add an explicit note in `05_agent_09_data-layer.md` that the `messages` table never holds diagnostic rows; all diagnostics go to `session_diagnostics`.
- **Risk**: Tests added to `test_agent_session.py` may need to mock both `SQLiteHelper("session")` for messages and `SQLiteHelper("session")` for session_diagnostics simultaneously → **Mitigation**: Use the same pattern as `test_diagnostic_store.py` with a `_FakeSQLiteHelper` that supports both tables in one in-memory connection.
- **Risk**: `05_agent_04_state-and-persistence.md` L131 removal may leave references to `diagnostics.jsonl` unexplained → **Mitigation**: Keep the `diagnostics.jsonl` mention and mark it as "supplementary/may be deprecated" per existing doc language.
