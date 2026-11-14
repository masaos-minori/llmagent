"""Tests for the ccache wrapper, the canonical-header tool, and build_binaries.sh wiring."""

from __future__ import annotations

import os
import subprocess
import types
from pathlib import Path

import pytest

from tools import gen_nuitka_helpers_header as gen

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WRAPPER = REPO_ROOT / "deploy" / "nuitka_ccache_wrapper.sh"
BUILD_SCRIPT = REPO_ROOT / "deploy" / "build_binaries.sh"


def _executable(path: Path, body: str) -> Path:
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(0o755)
    return path


# -- deploy/nuitka_ccache_wrapper.sh -------------------------------------------------


def _run_wrapper(
    tmp_path: Path, header_text: str | None, *, canon: str | None, exit_code: int = 0
) -> tuple[subprocess.CompletedProcess[str], str, str]:
    """Run the wrapper against a fake ccache; return the result, the header the fake
    ccache saw, and the arguments it received."""
    build_dir = tmp_path / "x.build"
    build_dir.mkdir()
    if header_text is not None:
        (build_dir / "__helpers.h").write_text(header_text)
    source = build_dir / "module.a.c"
    source.write_text("int a;\n")
    seen = tmp_path / "seen"
    fake = _executable(
        tmp_path / "fake_ccache",
        f'cat "{build_dir}/__helpers.h" > "{seen}.header" 2>/dev/null\n'
        f'echo "$@" > "{seen}.args"\nexit {exit_code}',
    )
    env = {"PATH": "/usr/bin:/bin", "NUITKA_REAL_CCACHE": str(fake)}
    if canon is not None:
        canon_file = tmp_path / "canon.h"
        canon_file.write_text(canon)
        env["NUITKA_CANON_HELPERS"] = str(canon_file)
    result = subprocess.run(
        [str(WRAPPER), "gcc", "-c", str(source), f"-I{build_dir}"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    header = Path(f"{seen}.header")
    args = Path(f"{seen}.args")
    return (
        result,
        header.read_text() if header.exists() else "",
        args.read_text() if args.exists() else "",
    )


def test_wrapper_replaces_a_differing_header_before_delegating(tmp_path: Path) -> None:
    result, header_seen, args = _run_wrapper(tmp_path, "per-binary\n", canon="canon\n")
    assert result.returncode == 0
    assert header_seen == "canon\n"
    assert args.startswith("gcc -c ")
    assert not list((tmp_path / "x.build").glob("*.canon.*"))


def test_wrapper_passes_through_without_a_canonical_header(tmp_path: Path) -> None:
    result, header_seen, args = _run_wrapper(tmp_path, "per-binary\n", canon=None)
    assert result.returncode == 0
    assert header_seen == "per-binary\n"
    assert args.startswith("gcc -c ")


def test_wrapper_does_not_create_a_missing_header(tmp_path: Path) -> None:
    _, header_seen, _ = _run_wrapper(tmp_path, None, canon="canon\n")
    assert header_seen == ""
    assert not (tmp_path / "x.build" / "__helpers.h").exists()


def test_wrapper_propagates_the_ccache_exit_status(tmp_path: Path) -> None:
    result, _, _ = _run_wrapper(tmp_path, "h\n", canon="canon\n", exit_code=3)
    assert result.returncode == 3


# -- tools/gen_nuitka_helpers_header.py ----------------------------------------------


def _fake_call_codes() -> types.ModuleType:
    module = types.ModuleType("fake_call_codes")
    attributes: dict[str, object] = {
        "max_quick_call": 2,
        "template_header_guard": "G<\n%(header_body)s\n>%(header_guard_name)s",
        "getTemplateCodeDeclaredFunction": lambda code: f"extern {code};",
        "getQuickCallCode": lambda n, has_tuple_arg: f"call{n}t{int(has_tuple_arg)}",
        "getQuickMixedCallCode": lambda n, has_tuple_arg, has_dict_values: (
            f"mixed{n}t{int(has_tuple_arg)}d{int(has_dict_values)}"
        ),
        "getQuickMethodCallCode": lambda n: f"method{n}",
    }
    for name, value in attributes.items():
        setattr(module, name, value)
    return module


def test_build_header_declares_every_variant_above_the_quick_calls() -> None:
    header = gen.build_header(_fake_call_codes(), 4)
    body = header.split("\n")[1:-1]
    assert body == sorted(body)
    assert "extern call3t0;" in body
    assert "extern mixed4t1d1;" in body
    assert "extern method4;" in body
    assert not any(line.startswith("extern call2") for line in body)
    assert len(body) == 2 * (2 + 4 + 1)


def test_build_header_is_deterministic() -> None:
    codes = _fake_call_codes()
    assert gen.build_header(codes, 6) == gen.build_header(codes, 6)


def test_main_writes_the_header(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gen.importlib, "import_module", lambda _n: _fake_call_codes())
    out = tmp_path / "sub" / "h.h"
    assert gen.main(["--out", str(out), "--max-arity", "3"]) == gen.EXIT_OK
    assert "extern call3t0;" in out.read_text()


def test_main_reports_a_missing_nuitka(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def boom(_name: str) -> types.ModuleType:
        raise ImportError("no nuitka")

    monkeypatch.setattr(gen.importlib, "import_module", boom)
    out = tmp_path / "h.h"
    assert gen.main(["--out", str(out)]) == gen.EXIT_FAIL
    assert "no nuitka" in capsys.readouterr().err
    assert not out.exists()


# -- deploy/build_binaries.sh: parallel pool and canonical-header wiring --------------

_STUB_UV = r"""
case "$*" in
  *gen_nuitka_helpers_header.py*)
    [ -n "${GEN_FAIL:-}" ] && exit 1
    out=""; prev=""
    for a in "$@"; do [ "$prev" = "--out" ] && out="$a"; prev="$a"; done
    echo canon > "$out"
    exit 0 ;;
  *"python find"*|*"python dir"*) exit 0 ;;
  *--version*) exit 0 ;;
  *nuitka*)
    out_dir=""; launcher=""
    for a in "$@"; do
      case "$a" in --output-dir=*) out_dir="${a#--output-dir=}" ;; *.py) launcher="$a" ;; esac
    done
    name="$(basename "$launcher" .py)"
    echo "$PATH|${NUITKA_CCACHE_BINARY:-}|${NUITKA_CANON_HELPERS:-}" >> "$STUB_LOG/env_build"
    echo "start $name $(date +%s%N)" >> "$STUB_LOG/events"
    sleep 0.6
    if [ "$name" = "${FAIL_NAME:-}_launcher" ]; then echo "boom $name" >&2; exit 1; fi
    printf '\177ELF' > "$out_dir/$name.bin"
    echo "end $name $(date +%s%N)" >> "$STUB_LOG/events"
    exit 0 ;;
esac
exit 0
"""

_FOUR = "mcp_git mcp_shell mcp_cicd mcp_mdq"


def _run_build(
    tmp_path: Path, extra_env: dict[str, str], *, masquerade: bool = False
) -> tuple[subprocess.CompletedProcess[str], Path]:
    stub_dir = tmp_path / "stub"
    stub_dir.mkdir()
    _executable(stub_dir / "uv", _STUB_UV)
    _executable(stub_dir / "ccache", "exit 0")
    _executable(stub_dir / "gcc", "exit 0")
    path = f"{stub_dir}:/usr/bin:/bin"
    if masquerade:
        masq = tmp_path / "masq"
        masq.mkdir()
        (masq / "gcc").symlink_to(stub_dir / "ccache")
        path = f"{masq}:{path}"
    logs = tmp_path / "logs"
    logs.mkdir()
    env = {
        "PATH": path,
        "HOME": str(tmp_path),
        "CCACHE_DIR": str(tmp_path / "cc"),
        "BIN_DIR": str(tmp_path / "bin"),
        "OUTPUT_DIR": str(tmp_path / "dist"),
        "STUB_LOG": str(logs),
        "BUILD_ONLY": _FOUR,
        **extra_env,
    }
    result = subprocess.run(
        ["bash", str(BUILD_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return result, logs


def _max_concurrency(events_file: Path) -> int:
    events = sorted(
        (int(line.split()[2]), 1 if line.startswith("start") else -1)
        for line in events_file.read_text().splitlines()
    )
    running = peak = 0
    for _, delta in events:
        running += delta
        peak = max(peak, running)
    return peak


def test_parallel_one_builds_sequentially(tmp_path: Path) -> None:
    result, logs = _run_build(tmp_path, {"NUTKA_PARALLEL": "1"})
    assert result.returncode == 0, result.stderr
    assert _max_concurrency(logs / "events") == 1
    assert sorted(
        p.name for p in (tmp_path / "bin").iterdir() if "." not in p.name
    ) == (sorted(_FOUR.split()))


def test_parallel_two_overlaps_builds_and_installs_every_binary(
    tmp_path: Path,
) -> None:
    result, logs = _run_build(tmp_path, {"NUTKA_PARALLEL": "2"})
    assert result.returncode == 0, result.stderr
    assert _max_concurrency(logs / "events") == 2
    installed = sorted(
        p.name for p in (tmp_path / "bin").iterdir() if "." not in p.name
    )
    assert installed == sorted(_FOUR.split())
    assert result.stdout.count("  OK  ") == 4
    assert "壁時間" in result.stdout


def test_parallel_failure_leaves_the_bin_dir_untouched(tmp_path: Path) -> None:
    result, _ = _run_build(tmp_path, {"NUTKA_PARALLEL": "2", "FAIL_NAME": "mcp_shell"})
    assert result.returncode != 0
    assert "build failed: mcp_shell" in result.stderr
    assert "boom mcp_shell" in result.stderr
    assert not (tmp_path / "bin").exists()


def test_invalid_parallel_value_is_rejected(tmp_path: Path) -> None:
    result, _ = _run_build(tmp_path, {"NUTKA_PARALLEL": "0"})
    assert result.returncode != 0
    assert "NUTKA_PARALLEL" in result.stderr


def test_canonical_header_wiring_removes_the_ccache_masquerade(tmp_path: Path) -> None:
    result, logs = _run_build(
        tmp_path, {"NUTKA_PARALLEL": "1", "BUILD_ONLY": "mcp_git"}, masquerade=True
    )
    assert result.returncode == 0, result.stderr
    path, wrapper, canon = (logs / "env_build").read_text().splitlines()[0].split("|")
    assert "masq" not in path.split(":")
    assert wrapper == str(WRAPPER)
    assert Path(canon).read_text() == "canon\n"
    assert "HELPERS_CANON: on" in result.stdout


@pytest.mark.parametrize(
    "extra_env, state",
    [
        ({"NUTKA_HELPERS_CANON": "0"}, "off"),
        ({"CCACHE_DISABLE": "1"}, "off"),
        ({"GEN_FAIL": "1"}, "failed"),
    ],
)
def test_canonical_header_is_skipped_when_disabled_or_unavailable(
    tmp_path: Path, extra_env: dict[str, str], state: str
) -> None:
    env = {"NUTKA_PARALLEL": "1", "BUILD_ONLY": "mcp_git", **extra_env}
    result, logs = _run_build(tmp_path, env, masquerade=True)
    assert result.returncode == 0, result.stderr
    path, wrapper, canon = (logs / "env_build").read_text().splitlines()[0].split("|")
    assert (wrapper, canon) == ("", "")
    assert "masq" in path
    assert f"HELPERS_CANON: {state}" in result.stdout


def test_wrapper_script_is_executable_and_parses() -> None:
    assert os.access(WRAPPER, os.X_OK)
    parsed = subprocess.run(
        ["bash", "-n", str(WRAPPER)], capture_output=True, text=True, check=False
    )
    assert parsed.returncode == 0, parsed.stderr
