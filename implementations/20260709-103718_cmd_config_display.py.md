# Implementation: H-10 — cmd_config_display.py remove display line

Source plan: `plans/20260709-100244_plan.md` (H-10, Implementation step 4).

## Goal

Stop `/config` from displaying the removed `github_server_url` field.

## Scope

**Target**: `scripts/agent/commands/cmd_config_display.py`, line 38
(`_ConfigDisplayMixin._print_llm_settings`).

## Assumptions

1. This is the only display reference to `github_server_url` —
   `scripts/agent/commands/cmd_config_display.py:38` is the sole match for
   `grep -n "github_server_url" scripts/agent/commands/cmd_config*.py`.

## Implementation

### Target file

`scripts/agent/commands/cmd_config_display.py`

### Procedure

#### Step 1: Delete the line

Current (`_print_llm_settings`, line 34-38):
```python
    def _print_llm_settings(self, ctx: AgentContext) -> None:
        self._out.write("Settings:")
        self._out.write(f"  llm_url             : {ctx.cfg.llm.llm_url}")
        self._out.write(f"  web_search_url      : {ctx.cfg.rag.web_search_url}")
        self._out.write(f"  github_server_url   : {ctx.cfg.mcp.github_server_url}")
```

Delete the `github_server_url` line only; `llm_url` and `web_search_url`
lines (and everything after) unchanged.

### Method

- Single-line deletion. Must land together with
  `implementations/20260709-103722_test_cmd_config_char.py.md` (which
  removes the corresponding expected output snippet) or that test will fail.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Line removed | `grep -n "github_server_url" scripts/agent/commands/cmd_config_display.py` | no matches |
| Display test (after test doc lands) | `uv run pytest tests/test_cmd_config_char.py -v` | all pass |
