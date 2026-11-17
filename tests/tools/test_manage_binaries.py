"""Tests for tools/manage_binaries.py."""

from __future__ import annotations

import ast
import hashlib
import json
import os
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


# -- MCP rebuild unit (ten mcp_<server> names as one freshness unit) --------------

_MCP_NAMES = [n for n in mod.BINARY_SOURCES if n != "agent"]
_ALL_NAMES = ["agent", *_MCP_NAMES]


@pytest.fixture
def built_unit(tmp_path: Path) -> tuple[Path, Path, str]:
    """A repo, a bin dir holding all eleven binaries with build info, and the commit."""
    repo = tmp_path / "repo"
    commit = _init_repo(repo)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in _ALL_NAMES:
        binary = _make_binary(bin_dir / name, name.encode())
        assert (
            mod.main(
                [
                    "write-info",
                    "--binary",
                    str(binary),
                    "--module",
                    f"mcp_servers.{name}" if name != "agent" else "agent.repl",
                    "--repo",
                    str(repo),
                ]
            )
            == 0
        )
    return repo, bin_dir, commit


def test_mcp_names_cover_every_non_agent_binary() -> None:
    assert mod._MCP_NAMES == tuple(_MCP_NAMES)
    assert "agent" not in mod._MCP_NAMES


def test_unit_sources_agent_is_its_own_and_mcp_share_the_union() -> None:
    assert mod._unit_sources("agent") == mod.BINARY_SOURCES["agent"]
    union = mod._unit_sources("mcp_shell")
    for name in _MCP_NAMES:
        assert mod._unit_sources(name) == union
        assert set(mod.BINARY_SOURCES[name]) <= set(union)
    assert "scripts/agent/" not in union


def test_unit_change_under_one_server_package_marks_all_ten_stale(
    built_unit: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built_unit
    _commit_file(repo, "scripts/mcp_servers/shell/s.py", "v2\n")
    assert _check(bin_dir, repo, names=" ".join(_ALL_NAMES)) == 0
    out = capsys.readouterr().out
    assert "agent: ok" in out
    for name in _MCP_NAMES:
        assert f"{name}: stale" in out


def test_unit_agent_only_change_leaves_the_ten_mcp_names_ok(
    built_unit: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built_unit
    _commit_file(repo, "scripts/agent/z.py", "z\n")
    assert _check(bin_dir, repo, names=" ".join(_ALL_NAMES)) == 0
    out = capsys.readouterr().out
    assert "agent: stale" in out
    for name in _MCP_NAMES:
        assert f"{name}: ok" in out


def test_unit_swap_and_rollback_move_the_ten_names_together(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bin_dir.chmod(0o755)
    for name in _MCP_NAMES:
        _make_binary(bin_dir / name, b"old-" + name.encode())
        assert (
            mod.main(
                [
                    "write-info",
                    "--binary",
                    str(bin_dir / name),
                    "--module",
                    "mcp_servers.x.x_server",
                    "--repo",
                    str(repo),
                ]
            )
            == 0
        )
    stage = _stage(tmp_path, {name: b"new" for name in _MCP_NAMES})
    for name in _MCP_NAMES:
        assert (
            mod.main(
                [
                    "write-info",
                    "--binary",
                    str(stage / name),
                    "--module",
                    "mcp_servers.x.x_server",
                    "--repo",
                    str(repo),
                ]
            )
            == 0
        )
    names_arg = " ".join(_MCP_NAMES)
    assert mod.main(["swap", "--stage-dir", str(stage), "--bin-dir", str(bin_dir), "--names", names_arg]) == 0
    prev = tmp_path / "bin.prev"
    for name in _MCP_NAMES:
        assert (bin_dir / name).read_bytes().endswith(b"new")
        assert (prev / name).read_bytes().endswith(b"old-" + name.encode())
    assert mod.main(["rollback", "--bin-dir", str(bin_dir), "--names", names_arg]) == 0
    for name in _MCP_NAMES:
        assert (bin_dir / name).read_bytes().endswith(b"old-" + name.encode())


def test_unit_swap_refused_when_one_staged_name_is_invalid(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bin_dir.chmod(0o755)
    for name in _MCP_NAMES:
        _make_binary(bin_dir / name, b"old")
    stage = _stage(tmp_path, {name: b"new" for name in _MCP_NAMES})
    (stage / "mcp_git").write_bytes(b"not an elf")
    code = mod.main(
        [
            "swap",
            "--stage-dir",
            str(stage),
            "--bin-dir",
            str(bin_dir),
            "--names",
            " ".join(_MCP_NAMES),
        ]
    )
    assert code == 1
    for name in _MCP_NAMES:
        assert (bin_dir / name).read_bytes().endswith(b"old")


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


def _mcp_servers_closure(entry: str) -> set[str]:
    """Return the ``mcp_servers`` modules reachable from ``entry`` by static imports."""
    scripts = REPO_ROOT / "scripts"
    seen: set[str] = set()

    def source_of(module: str) -> Path | None:
        base = scripts / module.replace(".", "/")
        for candidate in (base.with_suffix(".py"), base / "__init__.py"):
            if candidate.is_file():
                return candidate
        return None

    def visit(module: str) -> None:
        source = source_of(module)
        if module in seen or source is None:
            return
        seen.add(module)
        for node in ast.walk(ast.parse(source.read_text())):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            for name in names:
                parts = name.split(".")
                for end in range(1, len(parts) + 1):
                    visit(".".join(parts[:end]))

    visit(entry)
    return {m for m in seen if m.split(".")[0] == "mcp_servers"}


def test_agent_embeds_only_top_level_mcp_servers_modules() -> None:
    reached = _mcp_servers_closure("agent.repl")
    assert "mcp_servers.server" in reached
    nested = sorted(m for m in reached if m.count(".") > 1)
    assert not nested, (
        f"agent imports {nested}: widen the agent entry for scripts/mcp_servers/ "
        "in BINARY_SOURCES"
    )


def test_agent_ignores_mcp_server_package_change_but_not_top_level(
    built: tuple[Path, Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    repo, bin_dir, _ = built
    _commit_file(repo, "scripts/mcp_servers/shell/x.py", "x = 1\n")
    assert _check(bin_dir, repo) == 0
    assert "agent: ok" in capsys.readouterr().out
    _commit_file(repo, "scripts/mcp_servers/dispatch.py", "x = 1\n")
    assert _check(bin_dir, repo) == 0
    assert "agent: stale" in capsys.readouterr().out


def _run_build_recording_ccache_env(
    tmp_path: Path, ccache_dir: Path | None, xdg_cache_home: Path
) -> list[str]:
    """Run build_binaries.sh with stub uv/ccache and return the env at each uv call.

    Each recorded line is ``CCACHE_DIR|CCACHE_DISABLE``. The stub never produces a
    binary, so the script stops at its first build, after the ccache setup.
    """
    stub_dir = tmp_path / "stub"
    stub_dir.mkdir()
    seen = tmp_path / "seen"
    for name, body in (
        ("uv", f'echo "${{CCACHE_DIR:-}}|${{CCACHE_DISABLE:-}}" >> "{seen}"'),
        ("ccache", "true"),
        # The script rejects patchelf < 0.19; do not depend on the host's version.
        ("patchelf", 'echo "patchelf 0.19.0"'),
    ):
        stub = stub_dir / name
        stub.write_text(f"#!/bin/sh\n{body}\nexit 0\n")
        stub.chmod(0o755)
    env = {
        "PATH": f"{stub_dir}:/usr/bin:/bin",
        "BIN_DIR": str(tmp_path / "bin"),
        "OUTPUT_DIR": str(tmp_path / "dist"),
        "BUILD_ONLY": "agent",
        "XDG_CACHE_HOME": str(xdg_cache_home),
    }
    if ccache_dir is not None:
        env["CCACHE_DIR"] = str(ccache_dir)
    subprocess.run(
        ["bash", str(REPO_ROOT / "deploy" / "build_binaries.sh")],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return seen.read_text().splitlines()


def _unwritable_dir(path: Path) -> Path:
    path.mkdir()
    path.chmod(0o500)
    return path


@pytest.mark.skipif(os.geteuid() == 0, reason="root can write to any directory")
def test_build_binaries_falls_back_when_ccache_dir_unwritable(tmp_path: Path) -> None:
    blocked = _unwritable_dir(tmp_path / "blocked")
    xdg = tmp_path / "xdg"
    last = _run_build_recording_ccache_env(tmp_path, blocked / "ccache", xdg)[-1]
    assert last == f"{xdg}/ccache|"


def test_build_binaries_keeps_writable_ccache_dir(tmp_path: Path) -> None:
    chosen = tmp_path / "chosen"
    last = _run_build_recording_ccache_env(tmp_path, chosen, tmp_path / "xdg")[-1]
    assert last == f"{chosen}|"


@pytest.mark.skipif(os.geteuid() == 0, reason="root can write to any directory")
def test_build_binaries_disables_ccache_when_no_dir_writable(tmp_path: Path) -> None:
    blocked = _unwritable_dir(tmp_path / "blocked")
    last = _run_build_recording_ccache_env(tmp_path, blocked / "a", blocked / "b")[-1]
    assert last.endswith("|1")
