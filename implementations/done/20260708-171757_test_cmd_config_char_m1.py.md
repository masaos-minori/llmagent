# Implementation: M-1 — Remove use_tool_summarize snippet from /config snapshot test

## Goal

Remove the `"  use_tool_summarize  : False",` entry from `test_output_lines_match_snapshot`'s
`expected_snippets` list, matching the display-line removal in
`implementations/20260708-171350_cmd_config_display.py.md`.

## Scope

**Target**: `tests/test_cmd_config_char.py` — `test_output_lines_match_snapshot`'s
`expected_snippets` list only.

**Depends on**: `scripts/agent/commands/cmd_config_display.py`'s M-1 change already applied (or
applied together with this doc).

**Out of scope**: every other test in this file, and every other snippet in this same list
(`serial_tool_calls`, `use_semantic_cache`, etc.) — unchanged.

## Assumptions

1. `expected_snippets` is checked via `for snippet in expected_snippets: assert snippet in out`
   — a simple membership check per snippet, not an ordered or exhaustive line-by-line
   comparison. Removing one entry does not require reordering or renumbering anything else.
2. This list never included a `tool_summarize_thr` snippet in the first place (confirmed by
   reading the full list) — the production code writes that line too, but this test's coverage
   was never exhaustive of every single output line. No corresponding removal is needed for a
   snippet that was never present.

## Implementation

### Target file

`tests/test_cmd_config_char.py`

### Procedure

#### Step 1: Confirm the current entry

```bash
grep -n "use_tool_summarize" tests/test_cmd_config_char.py
```

Expected: one match, inside `expected_snippets`.

#### Step 2: Remove the entry

Current (within `expected_snippets`, between the `"Execution settings:"` and
`"Semantic cache:"` entries):

```python
            "Execution settings:",
            "  serial_tool_calls   : False",
            "  use_tool_summarize  : False",
            "Semantic cache:",
```

Replace with:

```python
            "Execution settings:",
            "  serial_tool_calls   : False",
            "Semantic cache:",
```

### Method

- Single list-entry deletion; no other snippet or assertion logic changes.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_cmd_config_char.py` | 0 errors |
| Grep (entry removed) | `grep -n "use_tool_summarize" tests/test_cmd_config_char.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_cmd_config_char.py -v` | all pass once the companion `cmd_config_display.py` doc is applied |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
