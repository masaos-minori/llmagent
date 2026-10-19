"""Tests for tools/manage_binaries.py."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

from tools import manage_binaries as mod


def _make_binary(path: Path, payload: bytes = b"x") -> Path:
    path.write_bytes(b"\x7fELF" + payload)
    path.chmod(0o755)
    return path


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.invalid",
            "-C",
            str(root),
            *args,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def _init_repo(root: Path) -> str:
    """Create a repository with one commit and return its commit id."""
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q")
    (root / "scripts" / "agent").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "scripts" / "agent" / "a.py").write_text("x = 1\n")
    (root / "docs" / "d.md").write_text("doc\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return _git(root, "rev-parse", "HEAD")


def _commit_file(root: Path, rel: str, text: str) -> None:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"change {rel}")


@pytest.fixture
def built(tmp_path: Path) -> tuple[Path, Path, str]:
    """A repo, a bin dir holding an agent binary with build info, and the commit."""
    repo = tmp_path / "repo"
    commit = _init_repo(repo)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    binary = _make_binary(bin_dir / "agent")
    assert (
        mod.main(
            [
                "write-info",
                "--binary",
                str(binary),
                "--module",
                "agent.repl",
                "--repo",
                str(repo),
            ]
        )
        == 0
    )
    return repo, bin_dir, commit


def _check(bin_dir: Path, repo: Path, *extra: str, names: str = "agent") -> int:
    return mod.main(
        [
            "check",
            "--bin-dir",
            str(bin_dir),
            "--rev",
            "auto",
            "--repo",
            str(repo),
            "--names",
            names,
            *extra,
        ]
    )


def test_write_info_records_checksum_and_commit(
    built: tuple[Path, Path, str],
) -> None:
    _, bin_dir, commit = built
    info = json.loads((bin_dir / "agent.build-info.json").read_text())
    assert (
        info["sha256"] == hashlib.sha256((bin_dir / "agent").read_bytes()).hexdigest()
    )
    assert info["source_commit"] == commit
    assert info["source_dirty"] is False


def test_check_reports_ok_when_no_relevant_change(
    built: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built
    assert _check(bin_dir, repo) == 0
    assert "agent: ok" in capsys.readouterr().out


def test_check_reports_stale_when_relevant_path_changed(
    built: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built
    _commit_file(repo, "scripts/agent/a.py", "x = 2\n")
    assert _check(bin_dir, repo) == 0
    assert "agent: stale" in capsys.readouterr().out


def test_check_ignores_unrelated_commit(
    built: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built
    _commit_file(repo, "docs/d.md", "changed\n")
    assert _check(bin_dir, repo, "--strict") == 0
    assert "agent: ok" in capsys.readouterr().out


def test_check_unknown_without_build_info(
    built: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built
    (bin_dir / "agent.build-info.json").unlink()
    assert _check(bin_dir, repo) == 0
    assert "agent: unknown" in capsys.readouterr().out


def test_check_mismatch_when_checksum_differs(
    built: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built
    _make_binary(bin_dir / "agent", b"different")
    assert _check(bin_dir, repo) == 1
    assert "agent: mismatch" in capsys.readouterr().out


def test_check_invalid_for_non_elf(
    built: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built
    (bin_dir / "agent").write_bytes(b"not an elf")
    assert _check(bin_dir, repo) == 1
    assert "agent: invalid" in capsys.readouterr().out


def test_check_default_warns_only(
    built: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built
    _commit_file(repo, "pyproject.toml", "[project]\n")
    assert _check(bin_dir, repo) == 0
    assert "agent: stale" in capsys.readouterr().out


def test_check_strict_fails_on_stale_and_unknown(
    built: tuple[Path, Path, str],
) -> None:
    repo, bin_dir, _ = built
    _commit_file(repo, "scripts/agent/a.py", "x = 3\n")
    assert _check(bin_dir, repo, "--strict") == 1
    (bin_dir / "agent.build-info.json").unlink()
    assert _check(bin_dir, repo, "--strict") == 1


def test_list_stale_prints_names(
    built: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built
    _commit_file(repo, "scripts/agent/a.py", "x = 4\n")
    assert _check(bin_dir, repo, "--list-stale") == 0
    assert capsys.readouterr().out.strip() == "agent"


def _stage(tmp_path: Path, names: dict[str, bytes]) -> Path:
    stage = tmp_path / "stage"
    stage.mkdir()
    for name, payload in names.items():
        _make_binary(stage / name, payload)
    return stage


def test_swap_success_saves_previous_set(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bin_dir.chmod(0o755)
    _make_binary(bin_dir / "agent", b"old")
    stage = _stage(tmp_path, {"agent": b"new"})
    code = mod.main(
        ["swap", "--stage-dir", str(stage), "--bin-dir", str(bin_dir), "--consume"]
    )
    assert code == 0
    assert (bin_dir / "agent").read_bytes().endswith(b"new")
    assert (tmp_path / "bin.prev" / "agent").read_bytes().endswith(b"old")
    assert not (stage / "agent").exists()


def test_swap_failure_leaves_bin_dir_unchanged(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bin_dir.chmod(0o755)
    _make_binary(bin_dir / "agent", b"old")
    stage = _stage(tmp_path, {"agent": b"new"})
    (stage / "mcp_shell").write_bytes(b"not an elf")
    code = mod.main(
        [
            "swap",
            "--stage-dir",
            str(stage),
            "--bin-dir",
            str(bin_dir),
            "--names",
            "agent mcp_shell",
        ]
    )
    assert code == 1
    assert (bin_dir / "agent").read_bytes().endswith(b"old")
    assert not (bin_dir / "mcp_shell").exists()
    assert not (tmp_path / "bin.prev").exists()


def test_rollback_restores_previous_set(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bin_dir.chmod(0o755)
    _make_binary(bin_dir / "agent", b"old")
    stage = _stage(tmp_path, {"agent": b"new"})
    assert mod.main(["swap", "--stage-dir", str(stage), "--bin-dir", str(bin_dir)]) == 0
    assert mod.main(["rollback", "--bin-dir", str(bin_dir)]) == 0
    assert (bin_dir / "agent").read_bytes().endswith(b"old")


def test_record_revision_writes_file(
    built: tuple[Path, Path, str], tmp_path: Path
) -> None:
    repo, bin_dir, commit = built
    root = tmp_path / "root"
    (root / "bin").mkdir(parents=True)
    for item in bin_dir.iterdir():
        (root / "bin" / item.name).write_bytes(item.read_bytes())
        (root / "bin" / item.name).chmod(0o755)
    code = mod.main(
        ["record-revision", "--root", str(root), "--rev", "auto", "--repo", str(repo)]
    )
    assert code == 0
    record = json.loads((root / "DEPLOYED_REV").read_text())
    assert record["commit"] == commit
    assert record["binaries"]["agent"]["source_commit"] == commit


def _script_binary_names() -> tuple[set[str], set[str]]:
    build = (REPO_ROOT / "deploy" / "build_binaries.sh").read_text()
    entries = set(re.findall(r'^\s+"[a-z_.]+:([a-z_]+):', build, re.M))
    deploy = (REPO_ROOT / "deploy" / "deploy.sh").read_text()
    block = deploy[deploy.index("BINARY_NAMES=(") :].split("\n)", 1)[0]
    names = set(re.findall(r"\b(agent|mcp_[a-z_]+)\b", block))
    return entries, names


def test_binary_sources_cover_entries_and_binary_names() -> None:
    entries, names = _script_binary_names()
    assert entries == set(mod.BINARY_SOURCES)
    assert names == set(mod.BINARY_SOURCES)


def _imported_packages(directory: Path) -> set[str]:
    tops = {"agent", "db", "rag", "shared", "eventbus", "mcp_servers"}
    found: set[str] = set()
    for path in directory.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.add(node.module.split(".")[0])
            elif isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
    return found & tops


def test_binary_sources_cover_imported_packages() -> None:
    scripts = REPO_ROOT / "scripts"
    package_dirs = {
        "agent": scripts / "agent",
        "mcp_shell": scripts / "mcp_servers" / "shell",
        "mcp_git": scripts / "mcp_servers" / "git",
        "mcp_web_search": scripts / "mcp_servers" / "web_search",
        "mcp_file_delete": scripts / "mcp_servers" / "file",
        "mcp_file_write": scripts / "mcp_servers" / "file",
        "mcp_file_read": scripts / "mcp_servers" / "file",
        "mcp_github": scripts / "mcp_servers" / "github",
        "mcp_cicd": scripts / "mcp_servers" / "cicd",
        "mcp_rag_pipeline": scripts / "mcp_servers" / "rag_pipeline",
        "mcp_mdq": scripts / "mcp_servers" / "mdq",
    }
    assert set(package_dirs) == set(mod.BINARY_SOURCES)
    for name, directory in package_dirs.items():
        covered = {
            entry.split("/")[1]
            for entry in mod.BINARY_SOURCES[name]
            if entry.startswith("scripts/")
        }
        missing = _imported_packages(directory) - covered - {"eventbus"}
        assert not missing, f"{name} imports {sorted(missing)} not in BINARY_SOURCES"


@pytest.mark.parametrize("script", ["build_binaries.sh", "deploy.sh"])
def test_shell_scripts_parse(script: str) -> None:
    result = subprocess.run(
        ["bash", "-n", str(REPO_ROOT / "deploy" / script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_build_binaries_rollback_option(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bin_dir.chmod(0o755)
    _make_binary(bin_dir / "agent", b"new")
    prev = tmp_path / "bin.prev"
    prev.mkdir()
    _make_binary(prev / "agent", b"old")
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "deploy" / "build_binaries.sh"), "--rollback"],
        capture_output=True,
        text=True,
        check=False,
        env={
            "PATH": "/usr/bin:/bin",
            "BIN_DIR": str(bin_dir),
            "OUTPUT_DIR": str(tmp_path / "dist"),
        },
    )
    assert result.returncode == 0, result.stderr
    assert (bin_dir / "agent").read_bytes().endswith(b"old")


def _run_build_with_stub_uv(
    tmp_path: Path, extra_env: dict[str, str]
) -> tuple[int, set[str], bool]:
    """Run build_binaries.sh with a stub uv that records UV_SYSTEM_CERTS and fails.

    Returns the return code, the values the stub recorded, and whether OUTPUT_DIR
    was created. The script stops at its nuitka resolution, so neither Nuitka nor
    the network is reached.
    """
    stub_dir = tmp_path / "stub"
    stub_dir.mkdir()
    seen = tmp_path / "seen"
    stub = stub_dir / "uv"
    stub.write_text(f'#!/bin/sh\necho "$UV_SYSTEM_CERTS" >> "{seen}"\nexit 1\n')
    stub.chmod(0o755)
    output_dir = tmp_path / "dist"
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "deploy" / "build_binaries.sh")],
        capture_output=True,
        text=True,
        check=False,
        env={
            "PATH": f"{stub_dir}:/usr/bin:/bin",
            "BIN_DIR": str(tmp_path / "bin"),
            "OUTPUT_DIR": str(output_dir),
            **extra_env,
        },
    )
    values = set(seen.read_text().splitlines()) if seen.exists() else set()
    return result.returncode, values, output_dir.exists()


def test_build_binaries_exports_system_certs_by_default(tmp_path: Path) -> None:
    code, values, created = _run_build_with_stub_uv(tmp_path, {})
    assert code != 0
    assert values == {"true"}
    assert not created


def test_build_binaries_keeps_explicit_system_certs(tmp_path: Path) -> None:
    code, values, _ = _run_build_with_stub_uv(tmp_path, {"UV_SYSTEM_CERTS": "false"})
    assert code != 0
    assert values == {"false"}
