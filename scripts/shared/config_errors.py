#!/usr/bin/env python3
"""scripts/shared/config_errors.py — Configuration loading error classes."""


class ConfigMissingError(ValueError):
    """Config file does not exist.

    Raised by:
        ConfigLoader.load()
        ConfigLoader.load_all()
    """


class ConfigParseError(ValueError):
    """Config file exists but cannot be parsed.

    Raised by:
        ConfigLoader.load()
        ConfigLoader.load_all()
    """


class ConfigReadError(ValueError):
    """Config file exists but cannot be read (permission, I/O).

    Raised by:
        ConfigLoader.load()
        ConfigLoader.load_all()
    """


class ConfigPermissionError(RuntimeError):
    """Process attempted to load a config file it is not permitted to access.

    Raised by:
        ConfigLoader.load()
        ConfigLoader.load_all()
        ConfigLoader.restrict_to()
    """


class ConfigLoadError(RuntimeError):
    """Raised when configuration files cannot be loaded.

    Raised by:
        AgentContext.__init__()
    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize with an optional chained exception cause."""
        if cause is not None:
            full_message = (
                f"Config load failed ({type(cause).__name__}: {cause}): {message}"
            )
        else:
            full_message = message
        super().__init__(full_message)
