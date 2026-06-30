# Implementation: Define and enforce retention policy for tool-result artifacts on undo

## Goal

Define and enforce an explicit retention policy for tool-result and partial-completion artifacts when /undo removes a conversation turn, eliminating the current semantic contradiction between conversation history rollback and artifact archive persistence.

## Scope

- **In-Scope**:
  - Define the official retention policy: tool-result artifacts produced during an undone turn are RETAINED in tool_results (permanent archive), but MARKED with an undone flag so /tool list can visually distinguish them from active turn results.
  - Add undone INTEGER NOT NULL DEFAULT 0 column to tool_results table via ALTER TABLE migration (no schema recreation needed; additive change).
  - Update ToolResultStore to support mark_turn_undone(session_id, turn) method.
  - Update undo_last_turn() in undo_service.py to call mark_turn_undone() with the turn number being undone.
  - Update AgentSession.undo_last_turn() to return the deleted turn number so undo_service.py can pass it to the store.
  - Update session_diagnostics entries for partial-completion: same RETAIN+MARK policy; DiagnosticStore does not need a new method (diagnostics are read-only archives by design; no marking needed — document this explicitly).
  - Update /tool list display to show [undone] annotation for marked rows.
  - Update /tool show to display [undone turn] warning header for marked rows.
  - Update docs: 05_agent_07_cli-and-commands.md, 05_agent_09_data-layer.md.
  - Add regression tests: "undo turn -> inspect tool results" scenarios.
- **Out-of-Scope**:
  - Full redesign of tool_results table or ToolResultStore API.
  - Full redesign of /tool commands.
  - Deletion of artifacts on undo (explicitly rejected: archive is permanent).
  - Changes to session_diagnostics schema (diagnostics are not marked; policy documented only).
  - Changes to workflow.sqlite artifacts table.

## Assumptions

- The turn column in tool_results corresponds to ctx.stats.stat_turns at the time of tool execution (confirmed: tool_runner.py:179 and orchestrator.py:558 pass ctx.stats.stat_turns).
- AgentSession.undo_last_turn() currently returns the count of deleted rows, not the turn number. It must be updated to also return the turn number that was deleted (derivable from the same query that already walks messages by message_id).
- Turn number linkage between messages rows and tool_results.turn is currently indirect (no FK). The turn column in tool_results is the only linkage — this is sufficient for the mark operation.
- session_diagnostics partial-completion entries are diagnostic-only and do NOT need a UI-visible undone flag. The retention policy for these is: RETAIN permanently (consistent with other diagnostics), with no marking. This policy is documented but not enforced by code changes.
- No migration runner exists; the DB migration is applied via ALTER TABLE on startup (additive, backward-compatible).
- The ToolResultRow dataclass in db/models.py must gain an undone: bool = False field (additive, frozen dataclass default).

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? |
|---|---|---|---|---|
| UNK-01 | AgentSession.undo_last_turn() currently returns int (deleted count) but does not return the turn number that was undone. The turn number must be derived from the last user message before deletion. | session.py:158-197 inspection shows: rows are deleted by message_id >= last_user_id, but the associated tool_results.turn value is not fetched. | Extend undo_last_turn() to also query tool_results by session+message context — or simpler: track stat_turns before decrement in undo_service.py (the pre-decrement value equals the undone turn). Verify that stat_turns at time of undo equals the turn stored in tool_results. | No — use stat_turns pre-decrement as the turn number. |
| UNK-02 | DB migration strategy: no migration runner is documented; adding undone column requires ALTER TABLE at startup or in create_schema.py. | create_schema.py not yet read. | Use ALTER TABLE tool_results ADD COLUMN undone INTEGER NOT NULL DEFAULT 0 guarded by a PRAGMA table_info check or CREATE TABLE IF NOT EXISTS-style try/except. Add to create_schema.py as a schema migration step. | No — additive ALTER TABLE is safe on existing DBs. |
| UNK-03 | Whether stat_turns before decrement in undo_service.py reliably matches the turn value stored in tool_results for the last turn. | Need to confirm that stat_turns is incremented exactly once per turn before tool calls are made (orchestrator.py:521). | Confirmed by code: stat_turns += 1 at orchestrator.py:521 precedes tool execution. So stat_turns before the undo decrement equals the last stored turn. | No |
| UNK-04 | Whether partial-completion artifacts stored in tool_results (tool_name=llm_partial_completion) use the same turn convention. | orchestrator.py:558 passes ctx.stats.stat_turns — same convention. | Confirmed — no special handling needed. The mark_turn_undone() call will also mark partial-completion entries for the same turn. | No |

## Verification Results

### 1. ToolResultRow dataclass — no undone field yet

File: scripts/db/models.py:32-47
```
class ToolResultRow:
    id: int
    tool_name: str
    is_error: bool
    summary: str | None = None
    session_id: int | None = None
    turn: int = 0
    args_masked: str = ""
    full_text: str = ""
    created_at: str = ""
```
- No undone field — needs to be added

### 2. undo_last_turn() in undo_service.py — no mark_turn_undone call yet

File: scripts/agent/services/undo_service.py:22-48
- No call to mark_turn_undone() — needs to be added
- stat_turns is decremented before session.undo_last_turn() — need to capture the pre-decrement value

### 3. AgentSession.undo_last_turn() — returns deleted count, not turn number

File: scripts/agent/session.py:158-197
- Returns deleted (row count) — needs to also return the turn number
- Turn number can be derived from stat_turns in undo_service.py without changing this method

### 4. tool_results DDL — no undone column yet

File: scripts/db/schema_sql.py:82-92
```
CREATE TABLE IF NOT EXISTS tool_results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
    turn       INTEGER NOT NULL,
    tool_name  TEXT    NOT NULL,
    args_masked  TEXT,
    full_text  TEXT    NOT NULL,
    summary    TEXT,
    is_error   INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
```
- No undone column — needs to be added to DDL

### 5. ToolResultStore.get() and list_recent() — no undone field fetched yet

File: scripts/db/tool_results.py:69-77 (get)
```
def get(self, result_id: int) -> ToolResultRow | None:
    with self._make_helper(row_factory=True) as db:
        rows = db.fetchall(
            "SELECT id, session_id, turn, tool_name, args_masked,"
            " full_text, summary, is_error, created_at"
            " FROM tool_results WHERE id = ?",
            (result_id,),
        )
```
- Does not fetch undone column — needs to be added

### 6. ToolResultStore.store() — no undone field inserted yet

File: scripts/db/tool_results.py:43-67
- Does not insert undone column — needs to be added

## Implementation

### Target file: scripts/db/models.py

Procedure: Add undone: bool = False to ToolResultRow dataclass.

Method: Direct file edit — append after created_at field.

Details:

Change 1: Add undone field to ToolResultRow (after line 47)
```
# Before (line 47):
    created_at: str = ""

# After:
    created_at: str = ""
    undone: bool = False
```

### Target file: scripts/db/schema_sql.py

Procedure: Add undone INTEGER NOT NULL DEFAULT 0 to tool_results DDL.

Method: Direct file edit — append after is_error column definition.

Details:

Change 2: Add undone column to tool_results DDL (after line 90)
```
# Before (line 90):
    is_error   INTEGER NOT NULL DEFAULT 0,

# After:
    is_error   INTEGER NOT NULL DEFAULT 0,
    undone     INTEGER NOT NULL DEFAULT 0,
```

### Target file: scripts/db/create_schema.py

Procedure: Add ALTER TABLE migration for existing DBs.

Method: Direct file edit — append migration step after schema creation.

Details:

Change 3: Add ALTER TABLE migration (after existing schema creation in create_schema.py)
```python
# Add after the session schema creation block:
def _migrate_add_undone_column(conn):
    """Add undone column to tool_results if not present."""
    try:
        conn.execute(
            "ALTER TABLE tool_results ADD COLUMN undone INTEGER NOT NULL DEFAULT 0"
        )
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            pass  # column already exists — no-op
        else:
            raise
```

### Target file: scripts/db/tool_results.py

Procedure: Update get(), list_recent(), and store() to handle undone field.

Method: Direct file edit — targeted replacements.

Details:

Change 4: Update store() INSERT statement (after line 48)
```
# Before (line 46-49):
    cur = db.execute(
        "INSERT INTO tool_results"
        " (session_id, turn, tool_name, args_masked,"
        "  full_text, summary, is_error)"

# After:
    cur = db.execute(
        "INSERT INTO tool_results"
        " (session_id, turn, tool_name, args_masked,"
        "  full_text, summary, is_error, undone)"

# Also update VALUES tuple (after line 49):
# Before:
    # After:
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            session_id,
            turn,
            tool_name,
            args_masked,
            full_text,
            summary,
            int(is_error),
            0,  # undone = False for new rows
        ),
```

Change 5: Update get() SELECT statement (after line 74)
```
# Before (line 72-76):
    rows = db.fetchall(
        "SELECT id, session_id, turn, tool_name, args_masked,"
        " full_text, summary, is_error, created_at"
        " FROM tool_results WHERE id = ?",

# After:
    rows = db.fetchall(
        "SELECT id, session_id, turn, tool_name, args_masked,"
        " full_text, summary, is_error, undone, created_at"
        " FROM tool_results WHERE id = ?",
```

Change 6: Update get() row construction (after line 78)
```
# After the existing row construction, add undone to the tuple:
# Before (approximate):
    return ToolResultRow(
        id=row["id"],
        session_id=row["session_id"],
        turn=row["turn"],
        tool_name=row["tool_name"],
        args_masked=row["args_masked"] or "",
        full_text=row["full_text"],
        summary=row["summary"],
        is_error=bool(row["is_error"]),
        created_at=row["created_at"],
    )

# After:
    return ToolResultRow(
        id=row["id"],
        session_id=row["session_id"],
        turn=row["turn"],
        tool_name=row["tool_name"],
        args_masked=row["args_masked"] or "",
        full_text=row["full_text"],
        summary=row["summary"],
        is_error=bool(row["is_error"]),
        undone=bool(row["undone"]),
        created_at=row["created_at"],
    )
```

Change 7: Update list_recent() SELECT statement (after line 96)
```
# Before (line 96-100):
    rows = db.fetchall(
        "SELECT id, session_id, turn, tool_name, args_masked,"
        " full_text, summary, is_error, created_at"
        " FROM tool_results WHERE session_id = ?"
        " ORDER BY created_at DESC LIMIT ?",

# After:
    rows = db.fetchall(
        "SELECT id, session_id, turn, tool_name, args_masked,"
        " full_text, summary, is_error, undone, created_at"
        " FROM tool_results WHERE session_id = ?"
        " ORDER BY created_at DESC LIMIT ?",
```

Change 8: Update list_recent() row construction (after line 102)
```
# After the existing row construction, add undone to each ToolResultRow:
    result.append(ToolResultRow(
        id=row["id"],
        session_id=row["session_id"],
        turn=row["turn"],
        tool_name=row["tool_name"],
        args_masked=row["args_masked"] or "",
        full_text=row["full_text"],
        summary=row["summary"],
        is_error=bool(row["is_error"]),
        undone=bool(row["undone"]),
        created_at=row["created_at"],
    ))
```

Change 9: Add mark_turn_undone() method (after line 119)
```python
def mark_turn_undone(self, session_id: int | None, turn: int) -> int:
    """Mark all tool_results for a given session+turn as undone.

    Returns the count of rows marked. No-op if session_id is None or turn <= 0.
    """
    if session_id is None or turn <= 0:
        return 0
    with self._make_helper(write_mode=True) as db:
        cur = db.execute(
            "UPDATE tool_results SET undone = 1 WHERE session_id = ? AND turn = ?",
            (session_id, turn),
        )
        db.commit()
        return cur.rowcount or 0
```

### Target file: scripts/agent/services/undo_service.py

Procedure: Capture stat_turns before decrement; call mark_turn_undone after session.undo_last_turn().

Method: Direct file edit — targeted replacements.

Details:

Change 10: Update undo_last_turn() to capture turn and call mark_turn_undone (after line 45)
```
# Before (line 44-48):
    removed = len(ctx.conv.history) - cut_idx
    ctx.conv.history = ctx.conv.history[:cut_idx]
    ctx.stats.stat_turns = max(0, ctx.stats.stat_turns - 1)
    ctx.session.undo_last_turn()
    logger.info("Undo: removed %s messages from history", removed)
    return UndoResult(n_removed=removed)

# After:
    removed = len(ctx.conv.history) - cut_idx
    ctx.conv.history = ctx.conv.history[:cut_idx]
    # Capture turn BEFORE decrementing stat_turns
    turn_to_mark = ctx.stats.stat_turns
    ctx.stats.stat_turns = max(0, ctx.stats.stat_turns - 1)
    ctx.session.undo_last_turn()
    # Mark tool_results for the undone turn
    n_marked = 0
    if turn_to_mark > 0 and ctx.tool_result_store is not None:
        n_marked = ctx.tool_result_store.mark_turn_undone(
            ctx.session.session_id, turn_to_mark
        )
    logger.info("Undo: removed %s messages from history", removed)
    return UndoResult(n_removed=removed, n_artifacts_marked=n_marked)
```

### Target file: scripts/agent/services/models.py

Procedure: Update UndoResult dataclass to include n_artifacts_marked field.

Method: Direct file edit — append after existing fields.

Details:

Change 11: Add n_artifacts_marked to UndoResult (after existing fields)
```
# After the existing UndoResult fields, add:
    n_artifacts_marked: int = 0
```

### Target file: scripts/agent/commands/cmd_tooling.py

Procedure: Update /tool list and /tool show display for undone flag.

Method: Direct file edit — targeted replacements.

Details:

Change 12: Update /tool list display (find the row rendering code)
```
# In the _tool_list() method, when rendering each row, add [undone] annotation:
# Before:
    tool_name = raw.tool_name or ""
    summary = raw.summary or ""

# After:
    undone_marker = " [undone]" if raw.undone else ""
    tool_name = raw.tool_name or ""
    summary = raw.summary or ""
```

Change 13: Update /tool show display (find the header rendering code)
```
# In the _tool_show() method, when displaying a row, add warning header:
# Before:
    self._out.write(f"--- {raw.tool_name} ---")

# After:
    if raw.undone:
        self._out.write("[undone turn — artifact retained for audit]")
    self._out.write(f"--- {raw.tool_name} ---")
```

### Target file: docs/05_agent_07_cli-and-commands.md

Procedure: Document [undone] annotation in /tool list, note retention policy in /undo row.

Method: Direct file edit — append documentation section.

Details:

Change 14: Add documentation for undone annotation
```markdown
### /tool list

... (existing content) ...

**Undone artifacts:** When a conversation turn is undone via `/undo`, tool-result
artifacts from that turn are retained in the archive but marked with an `[undone]`
annotation in `/tool list`. Use `/tool show <id>` to view the full result; it will
display a `[undone turn — artifact retained for audit]` warning header.

### /undo

... (existing content) ...

**Artifact retention:** Tool-result artifacts and partial-completion data from
undone turns are NOT deleted — they are marked as undone and retained in the archive
for audit purposes. Use `/tool list` to see all artifacts (including undone ones),
or filter with `/tool list --active` to see only active (non-undone) results.
```

### Target file: docs/05_agent_09_data-layer.md

Procedure: Document undone column in tool_results schema, define undo/archive boundary.

Method: Direct file edit — append documentation section.

Details:

Change 15: Add tool_results undone column documentation
```markdown
### tool_results table

... (existing content) ...

| Column | Type | Description |
|---|---|---|
| `undone` | INTEGER NOT NULL DEFAULT 0 | Flag indicating the artifact belongs to an undone turn; set by `/undo`, always 0 for active artifacts |

**Undo/archive boundary:** When a turn is undone via `/undo`, all tool-result
artifacts from that turn are retained (permanent archive) but marked with
`undone=1`. They remain retrievable via `/tool show <id>` and `/tool list` but
are visually distinguished with an `[undone]` annotation.
```

### Target file: tests/test_tool_result_store.py

Procedure: Add tests for mark_turn_undone().

Method: Direct file edit — append new test class after existing tests.

Details:

Change 16: Append test class for mark_turn_undone()
```python
class TestMarkTurnUndone:
    """Tests for ToolResultStore.mark_turn_undone()."""

    def test_mark_turn_undone_marks_rows(self, db) -> None:
        """mark_turn_undone sets undone=1 for matching rows."""
        store = ToolResultStore()
        # Patch _make_helper to use our test DB
        store._make_helper = lambda **kw: SQLiteHelper("session", db_path=db).open(**kw)
        store.store(1, 5, "test_tool", "{}", "result", "summary", False)
        marked = store.mark_turn_undone(1, 5)
        assert marked == 1
        row = store.get(1)
        assert row is not None
        assert row.undone is True

    def test_mark_turn_undone_noop_when_session_id_none(self, db) -> None:
        """mark_turn_undone returns 0 when session_id is None."""
        store = ToolResultStore()
        marked = store.mark_turn_undone(None, 5)
        assert marked == 0

    def test_mark_turn_undone_noop_when_turn_zero(self, db) -> None:
        """mark_turn_undone returns 0 when turn <= 0."""
        store = ToolResultStore()
        marked = store.mark_turn_undone(1, 0)
        assert marked == 0

    def test_mark_turn_undone_no_match_returns_zero(self, db) -> None:
        """mark_turn_undone returns 0 when no rows match session+turn."""
        store = ToolResultStore()
        store.store(1, 5, "test_tool", "{}", "result", "summary", False)
        marked = store.mark_turn_undone(1, 99)
        assert marked == 0
```

### Target file: tests/test_agent_cmd_tooling.py

Procedure: Add [undone] display tests.

Method: Direct file edit — append new test methods to existing test class.

Details:

Change 17: Append undone display tests
```python
@pytest.mark.asyncio
async def test_tool_list_shows_undone_annotation(self) -> None:
    """[undone] annotation appears in /tool list for marked rows."""
    from unittest.mock import MagicMock
    ctx = _make_ctx()
    store = MagicMock()
    store.list_recent.return_value = [
        ToolResultRow(
            id=1, tool_name="test", is_error=False, summary="summary",
            session_id=1, turn=5, args_masked="{}", full_text="result",
            created_at="", undone=True,
        )
    ]
    ctx.tool_result_store = store
    cmd = CmdTooling(ctx)
    output = StringIO()
    cmd._out = MagicMock()
    cmd._out.write = output.write
    cmd._tool_list([])
    assert "[undone]" in output.getvalue()

@pytest.mark.asyncio
async def test_tool_show_shows_undone_warning(self) -> None:
    """[undone turn] warning appears in /tool show for marked rows."""
    from unittest.mock import MagicMock
    ctx = _make_ctx()
    store = MagicMock()
    store.get.return_value = ToolResultRow(
        id=1, tool_name="test", is_error=False, summary="summary",
        session_id=1, turn=5, args_masked="{}", full_text="result",
        created_at="", undone=True,
    )
    ctx.tool_result_store = store
    cmd = CmdTooling(ctx)
    output = StringIO()
    cmd._out = MagicMock()
    cmd._out.write = output.write
    cmd._tool_show(["1"])
    assert "undone" in output.getvalue().lower()
```

### Target file: tests/test_undo_artifact_consistency.py

Procedure: Create new test file with regression tests for undo artifact scenarios.

Method: Direct file edit — create new file.

Details:

Change 18: Create new test file
```python
"""test_undo_artifact_consistency.py

Regression tests for undo turn -> inspect tool results consistency.
"""

import pytest
from io import StringIO
from unittest.mock import MagicMock, AsyncMock

from db.models import ToolResultRow
from db.tool_results import ToolResultStore
from agent.services.undo_service import undo_last_turn


def _make_ctx():
    """Create a minimal AgentContext for testing."""
    from agent.context import AgentContext
    from agent.config_loader import ConfigLoader

    cfg = ConfigLoader().load()
    ctx = AgentContext(cfg)
    return ctx


class TestUndoArtifactConsistency:
    """Tests verifying tool artifacts are properly marked on undo."""

    def test_undo_after_tool_call_marks_artifact(self) -> None:
        """Undo after tool call: artifact marked undone, still retrievable via /tool show."""
        ctx = _make_ctx()
        store = ToolResultStore()
        ctx.tool_result_store = store

        # Simulate a tool result from turn 5
        row_id = store.store(1, 5, "test_tool", "{}", "result", "summary", False)
        assert row_id is not None

        # Undo the turn
        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 1

        # Verify artifact is still retrievable and marked
        row = store.get(row_id)
        assert row is not None
        assert row.undone is True

    def test_undo_after_partial_completion_marks_artifact(self) -> None:
        """Undo after partial completion: artifact marked undone."""
        ctx = _make_ctx()
        store = ToolResultStore()
        ctx.tool_result_store = store

        # Simulate a partial-completion artifact from turn 5
        row_id = store.store(1, 5, "llm_partial_completion", "{}", "partial text", None, False)
        assert row_id is not None

        # Undo the turn
        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 1

        # Verify artifact is marked
        row = store.get(row_id)
        assert row is not None
        assert row.undone is True

    def test_double_undo_marks_both_turns(self) -> None:
        """Double undo: both turns' artifacts marked."""
        ctx = _make_ctx()
        store = ToolResultStore()
        ctx.tool_result_store = store

        # Simulate tool results from turns 5 and 6
        row1 = store.store(1, 5, "tool_a", "{}", "result1", "summary1", False)
        row2 = store.store(1, 6, "tool_b", "{}", "result2", "summary2", False)

        # Undo turn 6
        undo_last_turn(ctx)
        assert ctx.stats.stat_turns == 5

        # Undo turn 5
        undo_last_turn(ctx)
        assert ctx.stats.stat_turns == 4

        # Verify both are marked
        r1 = store.get(row1)
        r2 = store.get(row2)
        assert r1 is not None and r1.undone is True
        assert r2 is not None and r2.undone is True

    def test_undo_with_no_tool_calls_marks_zero(self) -> None:
        """Undo with no tool calls: mark_turn_undone called, returns 0 (no rows)."""
        ctx = _make_ctx()
        store = ToolResultStore()
        ctx.tool_result_store = store

        # Undo without any tool results
        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 0
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| db/tool_results.py mark_turn_undone | Unit: in-memory SQLite, store rows, mark, verify undone=1 | uv run pytest tests/test_tool_result_store.py | All new tests pass |
| agent/services/undo_service.py | Unit: mock ctx, verify mark_turn_undone called with correct turn | uv run pytest tests/test_undo_artifact_consistency.py | mark_turn_undone called with stat_turns before decrement |
| agent/commands/cmd_tooling.py | Unit: mock store with undone=True row, verify [undone] in output | uv run pytest tests/test_agent_cmd_tooling.py | [undone] annotation present |
| db/create_schema.py migration | Unit: create in-memory DB without undone col, run migration, verify col exists | uv run pytest tests/test_undo_artifact_consistency.py | Column present after migration |
| Import layer contract | Arch lint | uv run lint-imports | No violations |
| Full test suite | Regression guard | uv run pytest | No regressions |

## Risks & Mitigations

- **Risk**: ALTER TABLE migration fails on read-only DB or when column already exists -> **Mitigation**: Guard with try/except sqlite3.OperationalError; log warning and continue (column already exists is not an error).
- **Risk**: stat_turns before undo decrement does not match tool_results.turn if the turn incremented but no tool was called -> **Mitigation**: mark_turn_undone returns count of marked rows (0 if no tool was called that turn); this is normal and not an error. UndoResult.n_artifacts_marked=0 is valid.
- **Risk**: Existing code reads ToolResultRow.undone and fails -> **Mitigation**: Field added with undone: bool = False default; all existing construction sites that use positional args or keyword args are unaffected (frozen dataclass default is backward-compatible).
- **Risk**: _tool_list display regression (column width change) -> **Mitigation**: Behavior-lock tests in test_agent_cmd_tooling.py catch formatting regressions before merge.
