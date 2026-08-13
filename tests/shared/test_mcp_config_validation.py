"""Tests for McpServerConfig value validation constraints."""

import pytest
from shared.mcp_config import McpServerConfig, StartupMode, TransportType


def _http_cfg(**kwargs):
    defaults = dict(
        transport=TransportType.HTTP,
        url="http://localhost:8080",
        tool_names=["tool_a"],
        call_timeout_sec=60.0,
        startup_timeout_sec=30,
        auth_token="",
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
        tool_names=["tool_b"],
        call_timeout_sec=60.0,
        startup_timeout_sec=30,
        auth_token="",
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
            tool_names=[],
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


# --- new: tool_names checks ---


def test_empty_tool_name_raises():
    with pytest.raises(ValueError, match="tool_names"):
        _http_cfg(tool_names=[""])


def test_duplicate_tool_names_raises():
    with pytest.raises(ValueError, match="duplicate"):
        _http_cfg(tool_names=["tool_a", "tool_a"])


def test_empty_tool_names_list_is_valid():
    cfg = _http_cfg(tool_names=[])
    assert cfg.tool_names == []


# --- new: auth_token check ---


def test_auth_token_non_string_raises():
    with pytest.raises(ValueError, match="auth_token"):
        _http_cfg(auth_token=123)  # type: ignore[arg-type]


def test_auth_token_empty_string_is_valid():
    cfg = _http_cfg(auth_token="")
    assert cfg.auth_token == ""


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
