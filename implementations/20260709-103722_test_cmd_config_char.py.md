# Implementation: H-10 — test_cmd_config_char.py remove display assertion

Source plan: `plans/20260709-100244_plan.md` (H-10, Implementation step 7, part 2).

## Goal

Remove the expected `github_server_url` output snippet, matching the
removal of that display line from `cmd_config_display.py`.

## Scope

**Target**: `tests/test_cmd_config_char.py`, line 134 (inside the
`expected_snippets` list, immediately after
`test_reload_shows_source_files`-style print test — verify exact
surrounding test name at implementation time).

Depends on `implementations/20260709-103718_cmd_config_display.py.md`
landing first.

## Assumptions

1. Line 134 is the only reference to `github_server_url` in this file —
   verified by `grep -n "github_server_url" tests/test_cmd_config_char.py`
   (1 match) while planning H-10.

## Implementation

### Target file

`tests/test_cmd_config_char.py`

### Procedure

#### Step 1: Delete the expected snippet line

Current (`expected_snippets` list, lines 131-136):
```python
        expected_snippets = [
            "Settings:",
            "  llm_url             : ",
            "  github_server_url   : http://127.0.0.1:8006",
            "  max_tool_turns      : 5",
            "  http_timeout        : 30.0s",
```
→
```python
        expected_snippets = [
            "Settings:",
            "  llm_url             : ",
            "  max_tool_turns      : 5",
            "  http_timeout        : 30.0s",
```

### Method

- Single-line deletion from a list literal.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Snippet removed | `grep -n "github_server_url" tests/test_cmd_config_char.py` | no matches |
| Test run | `uv run pytest tests/test_cmd_config_char.py -v` | all pass |
