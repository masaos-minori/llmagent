# Implementation Procedure

## Goal

Add a per-session `message_count` (new) to each dict returned by `AgentSession.list_sessions()` (`REQ-001` / `AC-1`), computed with a `LEFT JOIN` on `messages` grouped by `session_id`.

## Scope

Modify only `list_sessions()` in `scripts/agent/session.py`: the `SELECT` query (current line 173), the returned dict keys (lines 176-183), and the method docstring (line 168). No other file is modified here.

## Assumptions

- `sessions.session_id` is `INTEGER PRIMARY KEY AUTOINCREMENT` (`scripts/db/schema_sql.py` line 96), so `ORDER BY session_id DESC` is strictly newest-first; ordering is unchanged.
- `messages` has `message_id` (PK, NOT NULL, line 101) and `session_id` FK `ON DELETE CASCADE` (line 102), so `COUNT(m.message_id)` counts real rows.
- The additive key is backward-compatible: the single production caller (`_session_list`) reads fields by name; tests call `list_sessions()` against a real in-memory DB.

## Design decisions

- Change the query to `SELECT s.session_id, s.created_at, s.title, COUNT(m.message_id) AS message_count FROM sessions s LEFT JOIN messages m ON m.session_id = s.session_id GROUP BY s.session_id, s.created_at, s.title ORDER BY s.session_id DESC LIMIT ?`. The `LEFT JOIN` keeps zero-message sessions; `COUNT` yields `0` for them.
- Add `"message_count": r["message_count"]` to the returned dict. `COUNT` returns an int; no type coercion needed.

## Alternatives considered

- Per-row scalar subquery `SELECT COUNT(...) WHERE session_id = s.session_id`: rejected — a single `LEFT JOIN` + `GROUP BY` is one pass and avoids N+1 queries.
- Counting `m.session_id` instead of `m.message_id`: rejected — `message_id` is the NOT NULL PK, guaranteeing an accurate count.

## Implementation

### Target file

`scripts/agent/session.py`

### Procedure

1. Update the `SELECT` in `list_sessions()` (line 173) to the `LEFT JOIN` query above.
2. Add `"message_count": r["message_count"]` to the dict comprehension (after `is_current`, line 181).
3. Update the docstring (line 168) to list `message_count` (new) among the returned keys.

### Method

Keep the change inside `list_sessions()` only. Preserve `ORDER BY session_id DESC`, the default `limit=20`, and the `is_current` marker. The non-positive-limit guard lives upstream in `_session_list` (read by name) and is untouched here.

### Details

- `GROUP BY s.session_id, s.created_at, s.title` — group by all non-aggregated selected columns (SQLite allows omitting, but listing them is explicit and correct).
- `r["message_count"]` resolves via `sqlite3.Row` (the method opens with `row_factory=True`, line 171).
- No new imports; the query uses the same `SQLiteHelper("session")` instance.

## Compatibility considerations

Additive key only. The single production caller maps dicts to `SessionRow` (extended in the sibling procedure for `scripts/agent/services/models.py`); no existing reader breaks. No import-boundary change (`lint-imports` unaffected).

## Security considerations

N/A: read-only query, no input injection beyond the existing parameterized `?` limit bind.

## Rollback considerations

Revert the commit touching `scripts/agent/session.py`.

## Validation plan

| Target/Module | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/session.py` | Unit — seed sessions with differing message counts, assert `message_count` (new) | `uv run pytest tests/agent/test_agent_session.py` | Counts match `messages` rows; zero-message sessions show `0` |

## Completion criteria

`list_sessions()` returns one dict per session carrying an integer `message_count` (new) equal to that session's `messages` row count, including `0` for sessions with no messages.

## Out of scope

Extending `SessionRow` (`scripts/agent/services/models.py`) and rendering the column (`scripts/agent/commands/cmd_session.py`) are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `message_count` (new) in `list_sessions()` (LEFT JOIN) | Completed | 20261014-191032 | 20261014-191032 | ruff/mypy/bandit clean; LEFT JOIN + message_count key added; single caller `_session_list` reads by name so additive key is safe |
| 2 | Add/update tests per Validation plan | Completed | 20261014-191032 | 20261014-191032 | existing `TestListSessions` pass; new `message_count` tests belong to test rows 04/05 (out of this batch) |
| 3 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261014-191032 | 20261014-191032 | full suite 8248 passed, 17 pre-existing eventbus/startup failures unrelated to `session.py`; diff-cover exit 0 |
| 4 | Update documentation | N/A | — | — | not in scope for this row |

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
- **Requirement ID**: `REQ-001` — add per-session message count to `/session list`
- **Source issue**: `issues/20261014-150311_sess001_finalize-session-list-command.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261014-160933_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-171726
- **Related target files**: `scripts/agent/session.py`
