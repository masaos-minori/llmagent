# Implementation: utils.py ParsedArgs + mixin_base.py service delegation

## Goal

1. Add `ParsedArgs` dataclass and `parse_command_args()` to `utils.py` as the structured
   replacement for `parse_flag_int` / `parse_flag_str`. Old functions are kept for now.
2. In `mixin_base.py`, keep `reset_session_stats` as-is but add a note that it should be
   moved to a dedicated service. No breaking changes.

## Scope

- `scripts/agent/commands/utils.py` — add `ParsedArgs`, `parse_command_args()`
- `scripts/agent/commands/mixin_base.py` — comment-only update noting planned service move

## Assumptions

1. `parse_command_args(tokens, subcommands, flags_spec)` is a lightweight structured parser,
   not a full argparse replacement. It handles the subset needed by command mixins:
   - positional arguments
   - `--flag value` pairs
   - `--bool-flag` (no value)
2. Unknown flags are stored in `flags` without error (permissive mode for now).
3. `parse_flag_int` / `parse_flag_str` are NOT removed here. Callers will migrate gradually.

## Implementation

### Target file

`scripts/agent/commands/utils.py`

### Procedure

1. Add `ParsedArgs` dataclass after the existing imports.
2. Add `parse_command_args(tokens: list[str]) -> ParsedArgs` function.
3. Add `ParsedArgs` and `parse_command_args` to `__all__`.

### Method

Direct textual edit.

### Details

```python
from dataclasses import dataclass, field

@dataclass
class ParsedArgs:
    """Structured result of command argument parsing."""
    subcommand: str | None = None
    positional: list[str] = field(default_factory=list)
    flags: dict[str, str | bool] = field(default_factory=dict)
    error: str | None = None  # None = parse success


def parse_command_args(tokens: list[str]) -> ParsedArgs:
    """Parse command tokens into a structured ParsedArgs.

    First non-flag token is the subcommand; subsequent non-flag tokens are positional.
    --flag value pairs populate flags dict; bare --flag sets flag to True.
    """
    result = ParsedArgs()
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.startswith("--"):
            key = t[2:]
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                result.flags[key] = tokens[i + 1]
                i += 2
            else:
                result.flags[key] = True
                i += 1
        elif result.subcommand is None:
            result.subcommand = t
            i += 1
        else:
            result.positional.append(t)
            i += 1
    return result
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/utils.py` | 0 errors |
| Type | `uv run mypy scripts/agent/commands/utils.py` | no new errors |
| Tests | `uv run pytest tests/test_agent_cmd_*.py -x -q` | 128 passed |
