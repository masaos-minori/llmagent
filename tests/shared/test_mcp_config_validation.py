"""Tests for McpServerConfig value validation constraints."""

import pytest
from shared.mcp_config import (
    McpServerConfig,
    StartupMode,
    TransportType,
    _build_mcp_servers,
)


def _http_cfg(**kwargs):
    defaults = dict(
        transport=TransportType.HTTP,
        url="http://localhost:8080",
        call_timeout_sec=60.0,
        health_timeout=None,
        startup_timeout_sec=30,
        auth_token="test-token",
        env={},
        key="test_server",
    )
    defaults.update(kwargs)
    return McpServerConfig(**defaults)


def _subprocess_cfg(**kwargs):
    defaults = dict(
        transport=TransportType.HTTP,
        url="http://localhost:8080",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["./run.sh"],
        call_timeout_sec=60.0,
        health_timeout=None,
        startup_timeout_sec=30,
        auth_token="test-token",
        env={},
        key="sub_server",
    )
    defaults.update(kwargs)
    return McpServerConfig(**defaults)


# --- valid configs ---


def test_valid_http_config():
    cfg = _http_cfg()
    assert cfg.transport == TransportType.HTTP


def test_valid_subprocess_config():
    cfg = _subprocess_cfg()
    assert cfg.startup_mode == StartupMode.SUBPROCESS


# --- existing checks preserved ---


def test_http_missing_url_raises():
    with pytest.raises(ValueError, match="url"):
        _http_cfg(url="")


def test_subprocess_missing_cmd_raises():
    with pytest.raises(ValueError, match="cmd"):
        McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            startup_mode=StartupMode.SUBPROCESS,
            key="s",
        )


# --- new: timeout checks ---


def test_call_timeout_zero_is_valid():
    cfg = _http_cfg(call_timeout_sec=0)
    assert cfg.call_timeout_sec == 0


def test_call_timeout_negative_raises():
    with pytest.raises(ValueError, match="call_timeout_sec"):
        _http_cfg(call_timeout_sec=-1.0)


def test_startup_timeout_zero_is_valid():
    cfg = _http_cfg(startup_timeout_sec=0)
    assert cfg.startup_timeout_sec == 0


def test_startup_timeout_negative_raises():
    with pytest.raises(ValueError, match="startup_timeout_sec"):
        _http_cfg(startup_timeout_sec=-1)


def test_startup_timeout_positive_is_valid():
    cfg = _http_cfg(startup_timeout_sec=1)
    assert cfg.startup_timeout_sec == 1


# --- new: auth_token check ---


def test_auth_token_non_string_raises():
    with pytest.raises(ValueError, match="auth_token"):
        _http_cfg(auth_token=123)  # type: ignore[arg-type]


def test_auth_token_empty_string_raises():
    with pytest.raises(ValueError, match="auth_token"):
        _http_cfg(auth_token="", startup_mode=StartupMode.PERSISTENT)


def test_auth_token_env_ref_resolved(monkeypatch):
    """`${ENV:VAR_NAME}` auth_token values resolve via the
    _build_single_server() factory path (McpServerConfig's own constructor,
    used directly by _http_cfg(), does not itself perform resolution)."""
    from shared.mcp_config import _build_single_server

    monkeypatch.setenv("TEST_MCP_AUTH_TOKEN_VAR", "resolved-value")
    cfg = _build_single_server(
        "test_server",
        {
            "transport": "http",
            "url": "http://localhost:8080",
            "auth_token": "${ENV:TEST_MCP_AUTH_TOKEN_VAR}",
        },
    )
    assert cfg.auth_token == "resolved-value"


# --- new: env check ---


def test_env_non_string_value_raises():
    with pytest.raises(ValueError, match="env"):
        _http_cfg(env={"KEY": 123})  # type: ignore[arg-type]


def test_env_non_string_key_raises():
    with pytest.raises(ValueError, match="env"):
        _http_cfg(env={1: "val"})  # type: ignore[arg-type]


def test_env_valid():
    cfg = _http_cfg(env={"KEY": "val"})
    assert cfg.env == {"KEY": "val"}


# --- new: HTTP URL scheme check ---


def test_ftp_url_raises():
    with pytest.raises(ValueError, match="url must be a valid HTTP"):
        _http_cfg(url="ftp://badscheme.example.com")


def test_no_scheme_url_raises():
    with pytest.raises(ValueError, match="url must be a valid HTTP"):
        _http_cfg(url="//no-scheme.example.com")


def test_https_url_valid():
    cfg = _http_cfg(url="https://secure.example.com/api")
    assert "https" in cfg.url


# --- error message includes server key ---


def test_error_includes_server_key():
    with pytest.raises(ValueError, match="my_special_server"):
        _http_cfg(key="my_special_server", call_timeout_sec=-1.0)


# --- new: env denylist checks ---


def test_env_denylisted_key_ld_preload_raises():
    with pytest.raises(ValueError, match="denylisted"):
        _http_cfg(env={"LD_PRELOAD": "/tmp/evil.so"})


def test_env_denylisted_key_ld_library_path_raises():
    with pytest.raises(ValueError, match="denylisted"):
        _http_cfg(env={"LD_LIBRARY_PATH": "/tmp/evil"})


def test_env_denylisted_key_pythonpath_raises():
    with pytest.raises(ValueError, match="denylisted"):
        _http_cfg(env={"PYTHONPATH": "/tmp/evil"})


# --- new: startup_stagger_delay_sec / stderr log rotation checks ---


def test_startup_stagger_delay_negative_raises():
    with pytest.raises(ValueError, match="startup_stagger_delay_sec"):
        _http_cfg(startup_stagger_delay_sec=-1.0)


def test_startup_stagger_delay_zero_is_valid():
    cfg = _http_cfg(startup_stagger_delay_sec=0.0)
    assert cfg.startup_stagger_delay_sec == 0.0


def test_max_stderr_log_size_mb_zero_raises():
    with pytest.raises(ValueError, match="max_stderr_log_size_mb"):
        _http_cfg(max_stderr_log_size_mb=0)


def test_max_stderr_log_size_mb_negative_raises():
    with pytest.raises(ValueError, match="max_stderr_log_size_mb"):
        _http_cfg(max_stderr_log_size_mb=-1.0)


def test_max_stderr_log_size_mb_positive_is_valid():
    cfg = _http_cfg(max_stderr_log_size_mb=50.0)
    assert cfg.max_stderr_log_size_mb == 50.0


def test_max_stderr_log_files_zero_raises():
    with pytest.raises(ValueError, match="max_stderr_log_files"):
        _http_cfg(max_stderr_log_files=0)


def test_max_stderr_log_files_one_is_valid():
    cfg = _http_cfg(max_stderr_log_files=1)
    assert cfg.max_stderr_log_files == 1


# --- health_timeout checks ---


def test_health_timeout_default_none():
    cfg = _http_cfg()
    assert cfg.health_timeout is None


def test_health_timeout_zero_is_rejected():
    with pytest.raises(ValueError, match="health_timeout must be > 0"):
        _http_cfg(health_timeout=0.0)


def test_health_timeout_positive_is_valid():
    cfg = _http_cfg(health_timeout=10.0)
    assert cfg.health_timeout == 10.0


def test_health_timeout_negative_raises():
    with pytest.raises(ValueError, match="health_timeout"):
        _http_cfg(health_timeout=-1.0)


def test_health_timeout_none_returns_default():
    from shared.mcp_config import get_effective_health_timeout

    cfg = _http_cfg(health_timeout=None)
    assert get_effective_health_timeout(cfg) == 5.0


def test_health_timeout_positive_returns_value():
    from shared.mcp_config import get_effective_health_timeout

    cfg = _http_cfg(health_timeout=15.0)
    assert get_effective_health_timeout(cfg) == 15.0


def test_effective_timeout_is_always_a_positive_float():
    from shared.mcp_config import get_effective_health_timeout

    for value in (None, 15.0):
        effective = get_effective_health_timeout(_http_cfg(health_timeout=value))
        assert isinstance(effective, float)
        assert effective > 0


# --- cliplc006: server-identifier rule, `fields` removal, `credential_env` ---

# Invalid key forms from AC-4: traversal, separators, uppercase, whitespace,
# control characters, and the 64-character length boundary.
_INVALID_KEYS = [
    "..",
    "a/b",
    "a.b",
    "A",
    "a b",
    "a\n",
    "a" * 65,
    "a\x01",
]

_VALID_KEYS = ["a", "a0", "a_b", "a-b", "a" * 64]


def _server_dict(**overrides):
    """Minimal TOML-shaped `[mcp_servers.<key>]` section for parser cases."""
    v = {
        "transport": "http",
        "url": "http://localhost:8080",
        "startup_mode": "persistent",
        "auth_token": "test-token",
    }
    v.update(overrides)
    return v


@pytest.mark.parametrize("bad_key", _INVALID_KEYS)
def test_invalid_server_key_rejected_by_dataclass(bad_key):
    with pytest.raises(ValueError, match="server identifier"):
        _http_cfg(key=bad_key)


@pytest.mark.parametrize("bad_key", _INVALID_KEYS)
def test_invalid_server_key_rejected_by_parser(bad_key):
    with pytest.raises(ValueError, match="server identifier"):
        _build_mcp_servers({"mcp_servers": {bad_key: _server_dict()}})


@pytest.mark.parametrize("good_key", _VALID_KEYS)
def test_valid_server_key_accepted_at_both_points(good_key):
    assert _http_cfg(key=good_key).key == good_key
    built = _build_mcp_servers({"mcp_servers": {good_key: _server_dict()}})
    assert built[good_key].key == good_key


def test_default_empty_key_still_valid():
    assert _http_cfg(key="").key == ""


def test_config_fields_kwarg_rejected():
    with pytest.raises(TypeError):
        McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            fields={"cwd": "/tmp/opencode"},
        )


def test_credential_env_parses_to_tuple():
    built = _build_mcp_servers(
        {"mcp_servers": {"github": _server_dict(credential_env=["GITHUB_TOKEN"])}}
    )
    assert built["github"].credential_env == ("GITHUB_TOKEN",)


def test_credential_env_default_is_empty_tuple():
    built = _build_mcp_servers({"mcp_servers": {"git": _server_dict()}})
    assert built["git"].credential_env == ()


def test_credential_env_non_list_rejected():
    with pytest.raises(ValueError, match="credential_env.*must be list"):
        _build_mcp_servers(
            {"mcp_servers": {"git": _server_dict(credential_env="GITHUB_TOKEN")}}
        )


def test_credential_env_non_string_item_rejected():
    with pytest.raises(ValueError, match=r"credential_env\[0\]"):
        _build_mcp_servers({"mcp_servers": {"git": _server_dict(credential_env=[7])}})


def test_credential_env_wildcard_rejected():
    with pytest.raises(ValueError, match="credential_env.*not patterns"):
        _build_mcp_servers(
            {"mcp_servers": {"git": _server_dict(credential_env=["GITHUB_*"])}}
        )


def test_credential_env_denylisted_name_rejected():
    with pytest.raises(ValueError, match="credential_env.*denylisted"):
        _build_mcp_servers(
            {"mcp_servers": {"git": _server_dict(credential_env=["LD_PRELOAD"])}}
        )
