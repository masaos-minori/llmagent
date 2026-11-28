#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/startup_config.py — Single validated startup-configuration result for mdq-mcp.

Single validated startup-configuration result for mdq-mcp (REQ-007).

`load_startup_config()` reads `mdq_mcp_server.toml` once and returns the immutable
result consumed by service construction, authentication, health, and the posture
gate. There is no fallback path: missing production configuration is a pre-bind
failure, so the caller sees the raised error before the server binds.

Policy-only: the single I/O is the loader call, no configured value is logged, and
errors name field paths only.

Dependency direction: startup_config → shared
Import from here:  from mcp_servers.mdq.startup_config import StartupConfig, load_startup_config
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from shared.config_errors import ConfigMissingError, ConfigParseError, ConfigReadError
from shared.config_field_types import strict_str
from shared.config_loader import ConfigLoader
from shared.config_utils import resolve_env_ref

MDQ_CONFIG_FILE = "mdq_mcp_server.toml"

# Keys whose value must not be carried in the shared result, so a `repr()` of the
# result cannot put a token into a log or an error message (AC-6).
_SECRET_KEYS: frozenset[str] = frozenset({"auth_token"})


def _field_path_message(field_path: str, outcome: str) -> str:
    """Build the startup message from the field path; never the resolved config path.

    `ConfigLoader` embeds the resolved filesystem path in its exception text, which
    AC-6 forbids in a startup error, so the message is rebuilt here from the field
    path. The exception class is the same one the loader raises, so callers that
    catch it keep working.
    """
    return f"config key {field_path!r} {outcome}"


@dataclass(frozen=True)
class StartupConfig:
    """Immutable validated startup configuration result.

    Attributes:
        values: The validated configuration keys, read-only. The secret keys are not
            carried here, so `repr` of the result cannot reach a log with a token.
        db_path: The declared database path; no implicit default.
        auth_token: The resolved Bearer token. Excluded from `repr` so the value
            cannot reach a log or an error message.
    """

    values: Mapping[str, object]
    db_path: str
    auth_token: str = field(repr=False)


def load_startup_config() -> StartupConfig:
    """Load and validate the production configuration once.

    Raises:
        ConfigMissingError: The production configuration file is absent.
        ConfigParseError: The file exists but cannot be parsed.
        ConfigReadError: The file exists but cannot be read.
        ConfigFieldTypeError: A key does not match its declared type rule; the
            message names the field path and never echoes the value.

    The three loader errors are not swallowed: they propagate so startup fails
    before bind. Only their message is rebuilt from the field path.
    """
    try:
        raw = ConfigLoader().load(MDQ_CONFIG_FILE)
    except ConfigMissingError:
        raise ConfigMissingError(
            _field_path_message(MDQ_CONFIG_FILE, "is missing")
        ) from None
    except ConfigParseError:
        raise ConfigParseError(
            _field_path_message(MDQ_CONFIG_FILE, "could not be parsed")
        ) from None
    except ConfigReadError:
        raise ConfigReadError(
            _field_path_message(MDQ_CONFIG_FILE, "could not be read")
        ) from None

    db_path = strict_str(raw.get("db_path"), f"{MDQ_CONFIG_FILE}.db_path")
    auth_token = strict_str(raw.get("auth_token"), f"{MDQ_CONFIG_FILE}.auth_token")

    return StartupConfig(
        values=MappingProxyType(
            {key: value for key, value in raw.items() if key not in _SECRET_KEYS}
        ),
        db_path=db_path,
        auth_token=resolve_env_ref(auth_token),
    )
