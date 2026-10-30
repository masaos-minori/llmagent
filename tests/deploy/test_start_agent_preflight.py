"""tests/deploy/test_start_agent_preflight.py

Behavior tests for the compiled-agent pre-flight in deploy/start_agent.sh:
the presence/executable check that fails fast before launch.
"""

import os
import pathlib
import subprocess

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "deploy" / "start_agent.sh"
_AGENT = "agent"


def _write_driver(tmp_path: pathlib.Path, *, binary_present: bool) -> pathlib.Path:
    """Isolated bin dir plus a driver that sources the real script."""
    bin_dir = tmp_path / "bin"
    agent = bin_dir / _AGENT
    if binary_present:
        bin_dir.mkdir(parents=True)
        agent.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
        agent.chmod(0o755)
    driver_path = tmp_path / "driver.sh"
    driver_path.write_text(
        "\n".join(
            [
                "set -euo pipefail",
                f'source "{_SCRIPT}"',
                f'check_agent_binary "{agent}"',
                "echo PRESENT_OK",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return driver_path


def _run(driver_path: pathlib.Path) -> subprocess.CompletedProcess[str]:
    env: dict[str, str] = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")
    }
    return subprocess.run(
        ["bash", str(driver_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


def test_missing_binary_aborts_and_names_recovery(tmp_path: pathlib.Path) -> None:
    driver = _write_driver(tmp_path, binary_present=False)
    result = _run(driver)
    assert result.returncode == 1
    assert "[FATAL]" in result.stderr
    assert "Agent binary not found or not executable" in result.stderr
    assert "deploy/build_binaries.sh" in result.stderr
    assert "deploy/deploy.sh" in result.stderr
    assert "PRESENT_OK" not in result.stdout


def test_present_binary_proceeds(tmp_path: pathlib.Path) -> None:
    driver = _write_driver(tmp_path, binary_present=True)
    result = _run(driver)
    assert result.returncode == 0
    assert result.stdout.strip().endswith("PRESENT_OK")
