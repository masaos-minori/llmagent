# Goal

Create four new foundation files in `scripts/agent/commands/` that define shared types,
enums, exceptions, and the OutputPort protocol used by all command mixins.

# Scope

New files only — no changes to existing code in this step:
- `scripts/agent/commands/enums.py`
- `scripts/agent/commands/exceptions.py`
- `scripts/agent/commands/models.py`
- `scripts/agent/commands/output_port.py`

# Assumptions

1. All four files are pure Python with no external imports beyond stdlib and existing project modules.
2. `CommandRequest` DTO is for built-in commands only; plugin command handlers keep their `(ctx, args: str)` signature.
3. `OutputPort` is a structural Protocol — no ABC, no registration.
4. `CliOutputPort` wraps `print()` only; no ANSI color or formatting library.
5. `ConfigReloadValidationError` referenced in `exceptions.py` will be provided by the 02_plan agent/services layer; import as a forward reference here.

# Implementation

## Target file

`scripts/agent/commands/enums.py`,
`scripts/agent/commands/exceptions.py`,
`scripts/agent/commands/models.py`,
`scripts/agent/commands/output_port.py`

## Procedure

1. Create `enums.py` with all command-domain StrEnum/Enum classes.
2. Create `exceptions.py` with all command-domain exception hierarchy.
3. Create `models.py` with frozen dataclasses for ViewModels/DTOs.
4. Create `output_port.py` with `OutputPort` Protocol and `CliOutputPort` implementation.
5. Run ruff + mypy on each file.

## Method

- Use `from __future__ import annotations` in all files.
- Use `class X(str, Enum)` pattern (StrEnum alternative for Python 3.11 compat, but project is 3.13 so `StrEnum` from `enum` is fine).
- Frozen dataclasses via `@dataclass(frozen=True)`.
- Protocol via `typing.Protocol`.

## Details

### enums.py

```python
from __future__ import annotations
from enum import StrEnum

class CommandKind(StrEnum):
    MEMORY = "memory"
    SESSION = "session"
    CONTEXT = "context"
    DB = "db"
    DEBUG = "debug"
    INGEST = "ingest"
    MCP = "mcp"
    NOTES = "notes"
    TOOLING = "tooling"
    CONFIG = "config"

class MemoryAction(StrEnum):
    LIST = "list"
    SEARCH = "search"
    SHOW = "show"
    ADD = "add"
    DELETE = "delete"
    PIN = "pin"
    UNPIN = "unpin"
    PRUNE = "prune"

class DbAction(StrEnum):
    STATS = "stats"
    HEALTH = "health"
    CHECKPOINT = "checkpoint"
    VACUUM = "vacuum"
    PURGE = "purge"
    RECOVER = "recover"
    LIST = "list"

class McpAction(StrEnum):
    STATUS = "status"
    INSTALL = "install"
    PROBE = "probe"

class SessionAction(StrEnum):
    LIST = "list"
    LOAD = "load"
    RENAME = "rename"
    DELETE = "delete"
```

### exceptions.py

```python
from __future__ import annotations

class CommandParseError(ValueError):
    """Raised when a command line cannot be parsed into a valid command."""

class CommandValidationError(ValueError):
    """Raised when parsed command arguments fail domain validation."""

class CommandDispatchError(RuntimeError):
    """Raised when a command cannot be dispatched (e.g. unknown command name)."""

class CommandRenderingError(RuntimeError):
    """Raised when rendering a command result fails."""

class UnknownSubcommandError(CommandDispatchError):
    def __init__(self, sub: str, valid: tuple[str, ...]) -> None:
        self.sub = sub
        self.valid = valid
        super().__init__(
            f"Unknown subcommand {sub!r}. Valid: {', '.join(valid)}"
        )

class UnknownPresetError(CommandValidationError):
    def __init__(self, preset: str, valid: tuple[str, ...]) -> None:
        super().__init__(
            f"Unknown preset {preset!r}. Valid: {', '.join(valid)}"
        )

class UnknownTierError(CommandValidationError):
    def __init__(self, tier: str) -> None:
        super().__init__(f"Unknown safety tier: {tier!r}")
```

### models.py

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class StatsViewModel:
    session_id: str
    turns: int
    tool_calls: int
    tool_errors: int
    llm_retries: int
    llm_reconnects: int
    llm_heartbeat_timeouts: int
    llm_partial_completions: int
    llm_parse_errors: int
    cache_hits: int
    compress_count: int
    semantic_cache_hits: int
    input_tokens: int | None
    output_tokens: int | None
    debug_mode: bool
    latency: dict[str, Any] | None  # presentation-only dict; intentional

@dataclass(frozen=True)
class ToolResultView:
    result_id: int
    tool_name: str
    summary: str | None
    args_masked: dict[str, Any]  # presentation-only
    is_error: bool

@dataclass(frozen=True)
class McpInstallRequest:
    server_name: str

@dataclass(frozen=True)
class McpInstallRenderModel:
    server_name: str
    config_path: str
    handler_path: str
    next_steps: list[str]
```

### output_port.py

```python
from __future__ import annotations
from typing import Protocol

class OutputPort(Protocol):
    def write(self, text: str) -> None: ...
    def write_table(self, headers: list[str], rows: list[list[str]]) -> None: ...
    def write_error(self, text: str) -> None: ...
    def write_success(self, text: str) -> None: ...
    def write_kv(self, pairs: list[tuple[str, str]], key_width: int = 22) -> None: ...

class CliOutputPort:
    """Concrete OutputPort that writes to stdout via print()."""

    def write(self, text: str) -> None:
        print(text)

    def write_success(self, text: str) -> None:
        print(f"  {text}")

    def write_error(self, text: str) -> None:
        print(f"  [error] {text}")

    def write_validation_error(self, text: str) -> None:
        print(f"  [usage] {text}")

    def write_no_data(self, text: str) -> None:
        print(f"  {text}")

    def write_table(self, headers: list[str], rows: list[list[str]]) -> None:
        if not rows:
            return
        widths = [
            max(len(h), max(len(r[i]) for r in rows))
            for i, h in enumerate(headers)
        ]
        header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_line)
        print("-" * len(header_line))
        for row in rows:
            print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))

    def write_kv(self, pairs: list[tuple[str, str]], key_width: int = 22) -> None:
        for k, v in pairs:
            print(f"  {k:<{key_width}}: {v}")
```

# Validation plan

- `uv run ruff check scripts/agent/commands/enums.py scripts/agent/commands/exceptions.py scripts/agent/commands/models.py scripts/agent/commands/output_port.py`
- `uv run mypy scripts/agent/commands/enums.py scripts/agent/commands/exceptions.py scripts/agent/commands/models.py scripts/agent/commands/output_port.py`
- No tests needed for this step (pure type definitions; tested indirectly by subsequent steps).
