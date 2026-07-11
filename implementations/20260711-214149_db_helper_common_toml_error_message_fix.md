# Implementation Procedure: db/helper.py — fix stale `common.toml` error message

Source plan: `plans/20260711-173032_plan.md` — Design §4 / Implementation step 4

## Goal

Fix `SQLiteHelper._connect()`'s error message, which currently tells operators a missing DB path is "not configured in `common.toml`" — a config file confirmed to no longer exist (superseded by the consolidated `agent.toml`).

## Scope

**In:**
- `scripts/db/helper.py::_connect()` (line ~111): change the `ValueError` message text only.

**Out:**
- No change to the surrounding control flow, exception type, or when the error fires — this is purely a wording fix.
- `scripts/agent/commands/cmd_config_display.py:217` and `scripts/rag/ingestion/ingester.py:198` — both also reference `common.toml` but are explicitly out-of-scope per the plan (not DB-error messages; see plan's Out-of-Scope section for the exact reasoning).

## Assumptions

1. Confirmed via the plan's Assumption 1: `config/agent.toml`'s own header comment states it consolidates what was "previously split across: common, llm, http, rag, context, tools, memory, otel, security, system_prompts, tools_definitions, and *_mcp_server transport sections" — `common.toml` is confirmed historical, not present in `config/*.toml` today.
2. `scripts/db/helper.py::_connect()` line 111 currently raises `ValueError(f"{self._target}_db_path is not configured in common.toml")` — confirmed by direct read cited in the plan.

## Implementation

### Target file

`scripts/db/helper.py`

### Procedure

1. Locate the `ValueError` raised in `_connect()` when `{self._target}_db_path` is not configured.
2. Replace the message text exactly as specified in the plan's Design §4:
   ```python
   raise ValueError(f"{self._target}_db_path is not configured in agent.toml or DB config")
   ```
3. Do not alter the f-string's `{self._target}` interpolation or any other part of the exception construction.

### Method

Single-line string literal replacement inside an existing `raise ValueError(...)` statement. No logic change.

### Details

- Match the exact wording from the plan's Design §4 (`"...is not configured in agent.toml or DB config"`) so the companion test (see test doc) can assert on it precisely.
- Confirm via `grep -n "common.toml" scripts/db/helper.py` before and after the edit — before: 1 match; after: 0 matches.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/db/helper.py` | 0 errors |
| Type check | `uv run mypy scripts/db/` | No new errors |
| Tests | `uv run pytest tests/test_sqlite_helper.py -v` | All pass, including the new message-content assertion (see companion test doc) |
| Manual grep | `grep -rn "common\.toml" scripts/db/` | No matches remain |
