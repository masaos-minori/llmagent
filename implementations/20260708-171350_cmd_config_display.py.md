# Implementation: M-1 — Remove tool-summarize lines from /config display

## Goal

Remove the `use_tool_summarize`/`tool_summarize_thr` display lines from
`_print_execution_settings()`, matching the field removal from `ToolConfig`.

## Scope

**Target**: `scripts/agent/commands/cmd_config_display.py`

**Depends on / must land together with**: `implementations/20260708-171057_config_dataclasses.py.md`
(the `ToolConfig` fields these lines read).

**Out of scope**: `_print_semantic_cache_settings()` and every other `_print_*` method in this
file — unchanged.

## Assumptions

1. `_print_execution_settings()` is the only method in this file referencing either field
   (confirmed by the earlier grep: exactly two matches, both inside this one method).

## Implementation

### Target file

`scripts/agent/commands/cmd_config_display.py`

### Procedure

#### Step 1: Confirm the current lines

```bash
grep -n "use_tool_summarize\|tool_summarize_thr" scripts/agent/commands/cmd_config_display.py
```

Expected: two matches inside `_print_execution_settings()`.

#### Step 2: Remove both display lines

Current:

```python
    def _print_execution_settings(self, ctx: AgentContext) -> None:
        self._out.write("Execution settings:")
        self._out.write(f"  serial_tool_calls   : {ctx.cfg.tool.serial_tool_calls}")
        self._out.write(f"  use_tool_summarize  : {ctx.cfg.tool.use_tool_summarize}")
        self._out.write(
            f"  tool_summarize_thr  : {ctx.cfg.tool.tool_summarize_threshold}"
        )
```

Replace with:

```python
    def _print_execution_settings(self, ctx: AgentContext) -> None:
        self._out.write("Execution settings:")
        self._out.write(f"  serial_tool_calls   : {ctx.cfg.tool.serial_tool_calls}")
```

### Method

- Two-line deletion (one single-line `write`, one multi-line `write` call); the
  `"Execution settings:"` header and the `serial_tool_calls` line stay unchanged.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/agent/commands/cmd_config_display.py` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Grep (lines removed) | `grep -n "use_tool_summarize\|tool_summarize_thr" scripts/agent/commands/cmd_config_display.py` | no matches |
| Manual check | run `/config` | output no longer contains `use_tool_summarize` or `tool_summarize_thr` |
| Tests (targeted) | `uv run pytest tests/test_cmd_config_char.py -v` | pass once the companion test doc's changes are applied |
| Tests (full) | `uv run pytest -v` | no new failures once every M-1 companion doc lands together |
| Pre-commit | `pre-commit run --all-files` | pass |
