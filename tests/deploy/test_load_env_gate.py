"""tests/deploy/test_load_env_gate.py

Behavior tests for deploy/load_env.sh: the .env parser and the required-variable gate.
"""

import os
import pathlib
import subprocess

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_LIBRARY = _REPO_ROOT / "deploy" / "load_env.sh"
_SHARED_TOKEN = "EVENTBUS_AUTH_TOKEN"


def _write_driver(
    tmp_path: pathlib.Path, *, config_text: str, with_env_file: bool
) -> pathlib.Path:
    """Fixture configuration plus a driver script that sources the real library."""
    config_path = tmp_path / "eventbus.toml"
    config_path.write_text(config_text, encoding="utf-8")
    env_path = tmp_path / ".env"
    if with_env_file:
        env_path.write_text("", encoding="utf-8")
        # Default to a tight mode so the permission warning stays out of the cases that
        # are not about permissions.
        env_path.chmod(0o600)
    driver_path = tmp_path / "driver.sh"
    driver_path.write_text(
        "\n".join(
            [
                "set -euo pipefail",
                f'REPO_ROOT="{tmp_path}"',
                f'source "{_LIBRARY}"',
                f'if [[ -f "{env_path}" ]]; then',
                f'    ENV_FILE="{env_path}"',
                '    parse_env_file "${ENV_FILE}"',
                "fi",
                f'require_env_vars "Event Bus" "bash deploy/setup_services.sh" "{config_path}"',
                'echo "GATE_OK ${EVENTBUS_AUTH_TOKEN:-unset}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return driver_path


def _run(
    driver_path: pathlib.Path, *, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env: dict[str, str] = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")
    }
    env.update(extra_env or {})
    return subprocess.run(
        ["bash", str(driver_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


_SHARED_TOKEN_REF = 'auth_token = "${ENV:EVENTBUS_AUTH_TOKEN}"\n'


def test_missing_variable_aborts_and_names_it(tmp_path: pathlib.Path) -> None:
    driver = _write_driver(tmp_path, config_text=_SHARED_TOKEN_REF, with_env_file=False)
    result = _run(driver)
    assert result.returncode == 1
    assert "[FATAL]" in result.stderr
    assert _SHARED_TOKEN in result.stderr
    assert "openssl rand -hex 32" in result.stderr
    assert "Then re-run: bash deploy/setup_services.sh" in result.stderr
    assert "GATE_OK" not in result.stdout


def test_exported_variable_satisfies_the_gate(tmp_path: pathlib.Path) -> None:
    driver = _write_driver(tmp_path, config_text=_SHARED_TOKEN_REF, with_env_file=False)
    result = _run(driver, extra_env={_SHARED_TOKEN: "exported-value"})
    assert result.returncode == 0
    assert result.stdout.strip().endswith("exported-value")


def test_exported_variable_is_not_overridden_by_the_env_file(
    tmp_path: pathlib.Path,
) -> None:
    driver = _write_driver(tmp_path, config_text=_SHARED_TOKEN_REF, with_env_file=True)
    (tmp_path / ".env").write_text("EVENTBUS_AUTH_TOKEN=from-file\n", encoding="utf-8")
    result = _run(driver, extra_env={_SHARED_TOKEN: "exported-wins"})
    assert result.returncode == 0
    assert "exported-wins" in result.stdout
    assert "from-file" not in result.stdout


def test_empty_value_in_the_env_file_counts_as_missing(tmp_path: pathlib.Path) -> None:
    driver = _write_driver(tmp_path, config_text=_SHARED_TOKEN_REF, with_env_file=True)
    (tmp_path / ".env").write_text("EVENTBUS_AUTH_TOKEN=\n", encoding="utf-8")
    result = _run(driver)
    assert result.returncode == 1
    assert _SHARED_TOKEN in result.stderr


def test_command_substitution_in_a_value_is_not_executed(
    tmp_path: pathlib.Path,
) -> None:
    driver = _write_driver(tmp_path, config_text=_SHARED_TOKEN_REF, with_env_file=True)
    (tmp_path / ".env").write_text(
        f"EVENTBUS_AUTH_TOKEN=$(touch {tmp_path}/pwned)\nSECOND_VAR=plain-value\n",
        encoding="utf-8",
    )
    result = _run(driver)
    assert result.returncode == 0
    assert not (tmp_path / "pwned").exists()
    assert "$(touch" in result.stdout


def test_unsafe_line_is_skipped_with_a_warning(tmp_path: pathlib.Path) -> None:
    driver = _write_driver(tmp_path, config_text=_SHARED_TOKEN_REF, with_env_file=True)
    (tmp_path / ".env").write_text(
        "export BAD=1\nEVENTBUS_AUTH_TOKEN=valid-token\n", encoding="utf-8"
    )
    result = _run(driver)
    assert result.returncode == 0
    assert "Skipping unsafe .env line" in result.stderr
    assert "BAD" not in result.stdout


def test_loose_permissions_are_warned_and_tight_ones_are_not(
    tmp_path: pathlib.Path,
) -> None:
    driver = _write_driver(tmp_path, config_text=_SHARED_TOKEN_REF, with_env_file=True)
    env_path = tmp_path / ".env"
    extra = {_SHARED_TOKEN: "exported-value"}

    env_path.chmod(0o644)
    loose = _run(driver, extra_env=extra)
    assert loose.returncode == 0
    assert "permissions are 644" in loose.stderr
    assert "chmod 600" in loose.stderr

    env_path.chmod(0o600)
    tight = _run(driver, extra_env=extra)
    assert tight.returncode == 0
    assert "permissions are" not in tight.stderr
    assert "chmod 600" not in tight.stderr


def test_gate_only_scans_the_files_it_is_given(tmp_path: pathlib.Path) -> None:
    # A configuration the driver is never given must not widen the gate's scope:
    # deploy/start_agent.sh scans only agent.toml and *_mcp_server.toml, so a
    # variable that appears only in the Event Bus configuration cannot make the
    # agent refuse to start.
    (tmp_path / "other.toml").write_text(
        'another_key = "${ENV:SOME_OTHER_VARIABLE}"\n', encoding="utf-8"
    )
    driver = _write_driver(tmp_path, config_text=_SHARED_TOKEN_REF, with_env_file=False)
    result = _run(driver, extra_env={_SHARED_TOKEN: "exported-value"})
    assert result.returncode == 0
    assert "SOME_OTHER_VARIABLE" not in result.stderr
