"""tests/mcp_servers/mdq/_startup.py

Shared explicit startup result for the MDQ tests.

`MdqService.__init__()` consumes the validated startup-configuration result (seq 02), so the
fixtures supply an explicit result instead of relying on model defaults or a production
configuration read. The keys below are the ones `config/mdq_mcp_server.toml` declares today,
passed explicitly: no test reads a host path, and no test depends on an implicit default.

A fixture overrides only the key its test is about, so a failure names the key under test rather
than a missing one.
"""

from __future__ import annotations

from types import MappingProxyType

from mcp_servers.mdq.startup_config import StartupConfig

# `db_path` and `auth_token` are result fields, not `MdqConfig` keys, so they are not part of the
# values mapping. `allowed_dirs` stays empty here because the deny-all case is a configured state;
# a fixture that needs access supplies its own directory.
EXPLICIT_VALUES: dict[str, object] = {
    "allowed_dirs": [],
    "include_globs": ["*.md"],
    "exclude_globs": [".git/**", "__pycache__/**"],
    "max_snippet_chars": 500,
    "max_chunk_chars": 10000,
    "max_file_bytes": 100000,
    "search_timeout_sec": 30,
    "max_results_limit": 100,
    "max_chars_per_chunk": 10000,
    "max_total_result_chars": 100000,
    "max_outline_items": 500,
    "max_grep_matches": 200,
    "max_chars_per_match": 500,
    "context_before": 2,
    "context_after": 2,
    "enable_grep": True,
    "max_outline_depth": 6,
    "sqlite_busy_timeout": 5000,
}


def make_startup(db_path: str, **overrides: object) -> StartupConfig:
    """Build the startup result with every declared key supplied explicitly."""
    values = dict(EXPLICIT_VALUES)
    values.update(overrides)
    return StartupConfig(
        values=MappingProxyType(values), db_path=db_path, auth_token="test-token"
    )
