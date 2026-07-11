# Implementation Procedure: db/maintenance.py + db/config.py — fix stale `common.toml` docstrings

Source plan: `plans/20260711-173032_plan.md` — Design §5 / Implementation step 5

## Goal

Fix two stale docstrings in the DB layer that still describe construction "from `common.toml`" — a config file confirmed to no longer exist — even though the underlying code already correctly calls `ConfigLoader().load("agent.toml")`.

## Scope

**In:**
- `scripts/db/maintenance.py` (line ~66): fix the docstring text only.
- `scripts/db/config.py` (line ~59): fix the docstring text only.

**Out:**
- No code/logic change in either file — both already call `ConfigLoader().load("agent.toml")` correctly (plan Assumption 6: "the code is already correct; only the docstring text above each is wrong").
- These two files were not explicitly named in the requirement's original file list, but are included per the plan's Out-of-Scope section reasoning: they make the identical stale `common.toml` claim as `db/helper.py`'s error message and directly match the requirement's instruction to search for other stale `common.toml` references within the DB layer.

## Assumptions

1. Confirmed via the plan's Assumption 6: both `scripts/db/maintenance.py:67` and `scripts/db/config.py:60` already call `ConfigLoader().load("agent.toml")` — the runtime behavior is correct; only the docstring immediately above each call is wrong (still says "common.toml").
2. This is a documentation/docstring-only fix — no test assertions are needed for docstring text itself (no test in the plan's Design §6 targets these docstrings), but the `common.toml` grep sanity check in the Validation plan covers both files.

## Implementation

### Target file

`scripts/db/maintenance.py` and `scripts/db/config.py`

### Procedure

1. In `scripts/db/maintenance.py`, locate the docstring above the `ConfigLoader().load("agent.toml")` call (around line 66) and replace it with:
   ```python
   """Construct from agent.toml values; raises on config load failure."""
   ```
2. In `scripts/db/config.py`, locate the analogous docstring (around line 59) and replace it with:
   ```python
   """Construct DbConfig from agent.toml; raises ValueError if agent.toml is missing or malformed."""
   ```
3. Do not touch any other part of either docstring or the surrounding function/class body.

### Method

Two independent, single-docstring text replacements in two files. No control-flow or signature changes.

### Details

- Confirm via `grep -n "common.toml" scripts/db/maintenance.py scripts/db/config.py` before and after: before, 1 match each; after, 0 matches in both.
- Keep each docstring's existing raise-behavior description (`"raises on config load failure"` / `"raises ValueError if agent.toml is missing or malformed"`) — only the file-name reference changes from `common.toml` to `agent.toml`.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to these files:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/db/maintenance.py scripts/db/config.py` | 0 errors |
| Type check | `uv run mypy scripts/db/` | No new errors |
| Manual grep | `grep -rn "common\.toml" scripts/db/` | No matches remain (covers this item plus the companion `db/helper.py` fix) |
