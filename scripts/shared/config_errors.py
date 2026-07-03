#!/usr/bin/env python3
"""shared/config_errors.py — Configuration loading error classes."""


class ConfigMissingError(ValueError):
    """Config file does not exist."""


class ConfigParseError(ValueError):
    """Config file exists but cannot be parsed."""


class ConfigReadError(ValueError):
    """Config file exists but cannot be read (permission, I/O)."""
