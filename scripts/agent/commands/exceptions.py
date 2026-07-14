"""agent/commands/exceptions.py

Domain exceptions for built-in slash-command handlers.
"""

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
        super().__init__(f"Unknown subcommand {sub!r}. Valid: {', '.join(valid)}")


class UnknownPresetError(CommandValidationError):
    def __init__(self, preset: str, valid: tuple[str, ...]) -> None:
        super().__init__(f"Unknown preset {preset!r}. Valid: {', '.join(valid)}")


class UnknownTierError(CommandValidationError):
    def __init__(self, tier: str) -> None:
        super().__init__(f"Unknown safety tier: {tier!r}")
