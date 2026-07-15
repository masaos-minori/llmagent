#!/usr/bin/env python3
"""shared/config_errors.py — Configuration loading error classes."""


class ConfigMissingError(ValueError):
    """Config file does not exist."""


class ConfigParseError(ValueError):
    """Config file exists but cannot be parsed."""


class ConfigReadError(ValueError):
    """Config file exists but cannot be read (permission, I/O)."""


class ConfigPermissionError(RuntimeError):
    """Process attempted to load a config file it is not permitted to access."""


class ConfigLoadError(RuntimeError):
    """Raised when configuration files cannot be loaded."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        if cause is not None:
            full_message = (
                f"Config load failed ({type(cause).__name__}: {cause}): {message}"
            )
        else:
            full_message = message
        super().__init__(full_message)
