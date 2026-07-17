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
    """Raised when a slash-command subcommand name is not recognized."""

    def __init__(self, sub: str, valid: tuple[str, ...]) -> None:
        """Initialize with the unknown subcommand name and list of valid alternatives.

        Args:
            sub: The unrecognized subcommand name.
            valid: Tuple of valid subcommand names.
        """
        self.sub = sub
        self.valid = valid
        super().__init__(f"Unknown subcommand {sub!r}. Valid: {', '.join(valid)}")


class UnknownPresetError(CommandValidationError):
    """Raised when a command preset name is not recognized."""

    def __init__(self, preset: str, valid: tuple[str, ...]) -> None:
        """Initialize with the unknown preset name and list of valid alternatives.

        Args:
            preset: The unrecognized preset name.
            valid: Tuple of valid preset names.
        """
        super().__init__(f"Unknown preset {preset!r}. Valid: {', '.join(valid)}")


class UnknownTierError(CommandValidationError):
    """Raised when a tool safety tier name is not recognized."""

    def __init__(self, tier: str) -> None:
        """Initialize with the unknown tier name.

        Args:
            tier: The unrecognized safety tier name.
        """
        super().__init__(f"Unknown safety tier: {tier!r}")
