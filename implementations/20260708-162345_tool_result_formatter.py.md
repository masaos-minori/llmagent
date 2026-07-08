# Implementation: H-3 — Replace TURN_LIMIT_HINT text (remove /tool show reference)

## Goal

Change the `TURN_LIMIT_HINT` constant so it no longer references `/tool show <id>` or any
`result_id`, as a prerequisite for the future removal of `ToolResultStore` and the
`/tool show` command (out of scope here).

## Scope

**Target**: `scripts/agent/tool_result_formatter.py`

**Out of scope**: `ToolResultStore` removal, `/tool show` command removal (`cmd_tooling.py`),
per-turn char-limit logic itself (`scripts/agent/tool_runner.py` — covered by a separate
implementation doc).

## Assumptions

1. `TURN_LIMIT_HINT` is a module-level constant, referenced by `tool_runner.py`'s
   `_apply_turn_char_limit()` via `TURN_LIMIT_HINT.replace("]", f"{id_hint}]")` (that call site
   is removed in the companion `tool_runner.py` implementation step).
2. No other module references `TURN_LIMIT_HINT` (verify with grep in Step 1 of Procedure).
3. The new text must not contain `/tool show` or `id=` substrings (validation plan requirement).

## Implementation

### Target file

`scripts/agent/tool_result_formatter.py`

### Procedure

#### Step 1: Confirm no other references

```bash
grep -rn "TURN_LIMIT_HINT" scripts/ tests/
```

Expect only the definition (this file) and the two call sites in `tool_runner.py` (removed by
the companion implementation step).

#### Step 2: Replace the constant

Current (lines 16-20):

```python
# Hint appended to history when a tool result is dropped due to the per-turn limit
TURN_LIMIT_HINT = (
    "[Result omitted: per-turn tool result limit reached."
    " Use /tool show <id> to retrieve the full output.]"
)
```

Replace with:

```python
# Hint appended to history when a tool result is dropped due to the per-turn limit
TURN_LIMIT_HINT = "[Result omitted: per-turn tool result limit reached.]"
```

### Method

- Single constant reassignment; no signature or behavior change in this file.
- The multi-line parenthesized string concatenation collapses to one line since the retrieval
  clause is gone.

### Details

- `TURN_LIMIT_HINT` keeps its type (`str`) and import surface unchanged — no import updates
  needed in this file.
- The trailing `.]` (period + closing bracket) must be preserved exactly, since `tool_runner.py`
  (pre-change) does a `.replace("]", ...)` on this string; after the companion change removes
  that `.replace()` call, the exact bracket placement no longer matters functionally, but keeping
  it consistent with the plan's Design section avoids a second unrelated diff.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/agent/tool_result_formatter.py` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Grep (no `/tool show`) | `grep -n "TURN_LIMIT_HINT" -A2 scripts/agent/tool_result_formatter.py \| grep -c "/tool show"` | `0` |
| Grep (no `id=`) | `python -c "from agent.tool_result_formatter import TURN_LIMIT_HINT; assert 'id=' not in TURN_LIMIT_HINT"` | no assertion error |
| Tests (targeted) | `uv run pytest tests/test_tool_result_formatter.py -v` | all pass |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
