# Goal

Add five new frozen dataclass DTOs to `scripts/agent/services/models.py` to replace
raw `dict[str, int]` / `dict` return values in maintenance, tool_results, and session layers.

# Scope

- `scripts/agent/services/models.py` — append DTOs only; no changes to existing classes

# Assumptions

1. All five DTOs are `@dataclass(frozen=True)` — no mutation after construction.
2. `ToolResultRow` covers the full schema of `tool_results` table rows returned by `get()`.
   `list_recent()` returns only `id, tool_name, summary, is_error` — use the same class
   with remaining fields defaulting to `""` / `0` (see Procedure note in Step 4 doc).
3. `DocumentRow.lang` is `str | None` because the DB column is nullable.
4. `SessionRow.title` is `str | None` because the DB column is nullable.
5. `WalCheckpointCounts` field names match the keys returned by `SQLiteHelper.checkpoint()`:
   `busy`, `log_size` (= `pages_in_wal`), `pages_checkpointed`.
6. `ContextBudget` replaces the `dict[str, int]` return of `budget_breakdown()` in
   `context_view.py` (Step 6 prerequisite). Fields: `system`, `history`, `tool_results`.

# Implementation

## Target file

`scripts/agent/services/models.py`

## Procedure

1. Append the following six frozen dataclasses after the existing declarations.
2. Run `uv run ruff check` and `uv run mypy` on the file.

## Method

Append-only. No existing code is modified.

## Details

```python
@dataclass(frozen=True)
class WalCheckpointCounts:
    """Result of a WAL checkpoint operation (matches SQLiteHelper.checkpoint() keys)."""
    busy: int
    log_size: int           # pages_in_wal
    pages_checkpointed: int


@dataclass(frozen=True)
class PurgeCounts:
    """Result of a session purge operation."""
    age_deleted: int
    count_deleted: int


@dataclass(frozen=True)
class ToolResultRow:
    """One row from the tool_results table (full schema for get(); partial for list_recent)."""
    id: int
    tool_name: str
    is_error: bool
    summary: str | None = None
    session_id: int | None = None
    turn: int = 0
    args_masked: str = ""
    full_text: str = ""
    created_at: str = ""


@dataclass(frozen=True)
class DocumentRow:
    """One row from the documents table as returned by session.list_documents()."""
    url: str
    lang: str | None
    chunk_count: int
    fetched_at: str


@dataclass(frozen=True)
class SessionRow:
    """One row from the sessions table as returned by session.list_sessions()."""
    session_id: int
    title: str | None
    created_at: str
    is_current: bool


@dataclass(frozen=True)
class ContextBudget:
    """Per-category character counts for /context budget breakdown display."""
    system: int
    history: int
    tool_results: int
```

# Validation plan

- `uv run ruff check scripts/agent/services/models.py`
- `uv run mypy scripts/agent/services/models.py`
- No tests needed (pure type definitions tested indirectly by subsequent steps).
