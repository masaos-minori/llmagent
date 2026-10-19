#!/usr/bin/env python3
"""manage_binaries.py — Build info, freshness, swap, and rollback for the binaries.

Production runs the agent and the MCP servers as Nuitka onefile binaries, so a
change under ``scripts/`` reaches production only after the affected binaries are
rebuilt. This tool keeps that logic out of the shell scripts so it is testable:

  write-info       write ``<binary>.build-info.json`` (checksum, source commit,
                   dirty flag, build time) next to a freshly built binary
  check            report each binary as ok, stale, unknown, mismatch, or invalid
  swap             replace binaries in the bin directory from a staging directory,
                   only after every staged binary passes, saving the previous set
  rollback         restore the previous set saved by ``swap``
  record-revision  write ``DEPLOYED_REV`` under the install root

A binary is stale when files under the source paths it embeds (``BINARY_SOURCES``)
changed between its recorded build commit and the revision being deployed, so a
documentation-only commit does not make every binary stale.

Usage:
    python3 tools/manage_binaries.py write-info --binary PATH --module NAME
    python3 tools/manage_binaries.py check --bin-dir DIR --rev auto [--strict]
    python3 tools/manage_binaries.py swap --stage-dir DIR --bin-dir DIR [--consume]
    python3 tools/manage_binaries.py rollback --bin-dir DIR
    python3 tools/manage_binaries.py record-revision --root DIR --rev auto

Exit codes:
    0  Success (stale or unknown binaries only warn unless --strict)
    1  Integrity failure, strict freshness failure, or a swap/rollback/write failure
    2  Usage error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess  # nosec B404 — only used to run git with list arguments and no shell
import sys
import tempfile
from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

INFO_SUFFIX = ".build-info.json"
REVISION_FILE = "DEPLOYED_REV"
_ELF_MAGIC = b"\x7fELF"

# Paths shared by every MCP server binary.
_MCP_COMMON: tuple[str, ...] = (
    "scripts/mcp_servers/*.py",
    "scripts/shared/",
    "pyproject.toml",
    "uv.lock",
)

# Repository paths each binary embeds. An entry ending in "/" matches by prefix; an
# entry with "*" matches only direct children of its directory; otherwise the path
# must be equal. This table is the single source of truth for staleness.
BINARY_SOURCES: dict[str, tuple[str, ...]] = {
    "agent": (
        "scripts/agent/",
        "scripts/db/",
        "scripts/shared/",
        "scripts/mcp_servers/",
        "pyproject.toml",
        "uv.lock",
    ),
    "mcp_shell": ("scripts/mcp_servers/shell/", *_MCP_COMMON),
    "mcp_git": ("scripts/mcp_servers/git/", *_MCP_COMMON),
    "mcp_web_search": ("scripts/mcp_servers/web_search/", *_MCP_COMMON),
    "mcp_file_delete": ("scripts/mcp_servers/file/", *_MCP_COMMON),
    "mcp_file_write": ("scripts/mcp_servers/file/", *_MCP_COMMON),
    "mcp_file_read": ("scripts/mcp_servers/file/", *_MCP_COMMON),
    "mcp_github": ("scripts/mcp_servers/github/", *_MCP_COMMON),
    "mcp_cicd": ("scripts/mcp_servers/cicd/", *_MCP_COMMON),
    "mcp_rag_pipeline": (
        "scripts/mcp_servers/rag_pipeline/",
        "scripts/db/",
        "scripts/rag/",
        *_MCP_COMMON,
    ),
    "mcp_mdq": ("scripts/mcp_servers/mdq/", "scripts/db/", *_MCP_COMMON),
}

# Statuses that mean the binary should be rebuilt.
_REBUILD_STATUSES = frozenset({"stale", "unknown", "mismatch", "invalid"})


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(repo: Path, *args: str) -> str:
    """Run git in ``repo`` and return stdout; raise RuntimeError on failure."""
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git executable not found")
    proc = subprocess.run(  # nosec B603 — fixed git executable, list arguments, no shell
        [git, "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD").strip()


def _dirty(repo: Path) -> bool:
    """Return True when tracked files differ from HEAD (untracked files ignored)."""
    return bool(_git(repo, "status", "--porcelain", "--untracked-files=no").strip())


def _changed_paths(repo: Path, old: str, new: str) -> list[str]:
    out = _git(repo, "diff", "--name-only", old, new)
    return [line for line in out.splitlines() if line]


def _resolve_rev(rev: str, repo: Path) -> str:
    return _head(repo) if rev == "auto" else rev


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _info_path(binary: Path) -> Path:
    return binary.with_name(binary.name + INFO_SUFFIX)


def _write_json_atomic(path: Path, data: dict[str, object]) -> None:
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def _matches(path: str, entry: str) -> bool:
    if entry.endswith("/"):
        return path.startswith(entry)
    if "*" in entry:
        p, e = PurePosixPath(path), PurePosixPath(entry)
        return p.parent == e.parent and fnmatch(p.name, e.name)
    return path == entry


def _structural_problems(path: Path) -> list[str]:
    """Return problems with a binary file: missing, empty, not executable, not ELF."""
    if not path.is_file():
        return ["missing or not a regular file"]
    problems: list[str] = []
    if path.stat().st_size == 0:
        problems.append("empty file")
    if not path.stat().st_mode & stat.S_IXUSR:
        problems.append("not executable by its owner")
    with path.open("rb") as handle:
        if handle.read(4) != _ELF_MAGIC:
            problems.append("not an ELF file")
    return problems


def _dir_problems(directory: Path) -> list[str]:
    """Reject a bin directory that is group or world writable."""
    if directory.is_dir() and directory.stat().st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        return [f"{directory} is group or world writable"]
    return []


def write_info(binary: Path, module: str, repo: Path) -> Path:
    """Write the build-info file next to ``binary`` and return its path."""
    if not binary.is_file():
        raise RuntimeError(f"binary not found: {binary}")
    info = _info_path(binary)
    _write_json_atomic(
        info,
        {
            "name": binary.name,
            "module": module,
            "sha256": _sha256(binary),
            "source_commit": _head(repo),
            "source_dirty": _dirty(repo),
            "built_at": _utc_now(),
        },
    )
    return info


def _check_binary(name: str, bin_dir: Path, rev: str, repo: Path) -> tuple[str, str]:
    path = bin_dir / name
    problems = _structural_problems(path)
    if problems:
        return "invalid", "; ".join(problems)
    info_file = _info_path(path)
    if not info_file.is_file():
        return "unknown", "no build info (rebuild to record the source commit)"
    info = json.loads(info_file.read_text(encoding="utf-8"))
    if info.get("sha256") != _sha256(path):
        return "mismatch", "checksum differs from the recorded build info"
    if info.get("source_dirty"):
        return "stale", "built from a dirty working tree"
    built = str(info.get("source_commit", ""))
    if built == rev:
        return "ok", f"built from {built[:12]}"
    try:
        changed = _changed_paths(repo, built, rev)
    except RuntimeError:
        return "stale", f"recorded commit {built[:12]} is not in the repository"
    hits = sorted(
        p for p in changed if any(_matches(p, e) for e in BINARY_SOURCES[name])
    )
    if hits:
        return "stale", f"{len(hits)} embedded path(s) changed, e.g. {hits[0]}"
    return "ok", f"no embedded path changed since {built[:12]}"


def check(
    bin_dir: Path,
    rev: str,
    repo: Path,
    names: list[str],
    strict: bool,
) -> tuple[dict[str, tuple[str, str]], int]:
    """Check each named binary; return the per-binary results and an exit code."""
    resolved = _resolve_rev(rev, repo)
    results = {n: _check_binary(n, bin_dir, resolved, repo) for n in names}
    code = EXIT_OK
    if _dir_problems(bin_dir):
        code = EXIT_FAIL
    for status, _ in results.values():
        if status in ("mismatch", "invalid"):
            code = EXIT_FAIL
        elif strict and status in ("stale", "unknown"):
            code = EXIT_FAIL
    return results, code


def _replace_files(src_dir: Path, dst_dir: Path, names: list[str]) -> list[str]:
    """Copy each binary (and its info) into ``dst_dir`` via a temporary name."""
    done: list[str] = []
    for name in names:
        for suffix in ("", INFO_SUFFIX):
            src = src_dir / (name + suffix)
            if not src.is_file():
                continue
            tmp = dst_dir / (name + suffix + ".new")
            try:
                shutil.copy2(src, tmp)
                if suffix == "":
                    os.chmod(tmp, 0o755)  # nosec B103 — binaries must be executable; not group or world writable
                os.replace(tmp, dst_dir / (name + suffix))
            except BaseException:
                tmp.unlink(missing_ok=True)
                raise
        done.append(name)
    return done


def _default_prev(bin_dir: Path) -> Path:
    return bin_dir.with_name(bin_dir.name + ".prev")


def _verify_binaries(directory: Path, names: list[str]) -> list[str]:
    problems: list[str] = []
    for name in names:
        path = directory / name
        issues = _structural_problems(path)
        info_file = _info_path(path)
        if not issues and info_file.is_file():
            recorded = json.loads(info_file.read_text(encoding="utf-8"))
            if recorded.get("sha256") != _sha256(path):
                issues.append("checksum differs from the recorded build info")
        problems.extend(f"{name}: {issue}" for issue in issues)
    return problems


def swap(
    stage_dir: Path,
    bin_dir: Path,
    prev_dir: Path,
    names: list[str],
    consume: bool,
) -> int:
    """Replace ``names`` in ``bin_dir`` from ``stage_dir`` all-or-nothing."""
    problems = _verify_binaries(stage_dir, names) + _dir_problems(bin_dir)
    if problems:
        for problem in problems:
            print(f"swap refused: {problem}", file=sys.stderr)
        return EXIT_FAIL
    bin_dir.mkdir(parents=True, exist_ok=True)
    prev_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(prev_dir, 0o755)  # nosec B103 — readable directory; not group or world writable
    existing = [n for n in names if (bin_dir / n).is_file()]
    _replace_files(bin_dir, prev_dir, existing)
    try:
        _replace_files(stage_dir, bin_dir, names)
    except OSError as exc:
        print(f"swap failed ({exc}); restoring the previous set", file=sys.stderr)
        _replace_files(prev_dir, bin_dir, existing)
        for name in names:
            if name not in existing:
                (bin_dir / name).unlink(missing_ok=True)
                _info_path(bin_dir / name).unlink(missing_ok=True)
        return EXIT_FAIL
    if consume and stage_dir.resolve() != bin_dir.resolve():
        for name in names:
            (stage_dir / name).unlink(missing_ok=True)
            _info_path(stage_dir / name).unlink(missing_ok=True)
    print(f"swapped {len(names)} binary(ies); previous set kept in {prev_dir}")
    return EXIT_OK


def rollback(bin_dir: Path, prev_dir: Path, names: list[str]) -> int:
    """Restore ``names`` from the previous set saved by ``swap``."""
    if not prev_dir.is_dir():
        print(f"rollback failed: no previous set at {prev_dir}", file=sys.stderr)
        return EXIT_FAIL
    selected = names or sorted(n for n in BINARY_SOURCES if (prev_dir / n).is_file())
    if not selected:
        print(f"rollback failed: {prev_dir} holds no binaries", file=sys.stderr)
        return EXIT_FAIL
    problems = _verify_binaries(prev_dir, selected)
    if problems:
        for problem in problems:
            print(f"rollback refused: {problem}", file=sys.stderr)
        return EXIT_FAIL
    _replace_files(prev_dir, bin_dir, selected)
    print(f"restored {len(selected)} binary(ies) from {prev_dir}")
    return EXIT_OK


def record_revision(root: Path, rev: str, repo: Path) -> Path:
    """Write ``DEPLOYED_REV`` under ``root`` and return its path."""
    binaries: dict[str, dict[str, str]] = {}
    for name in BINARY_SOURCES:
        path = root / "bin" / name
        if not path.is_file():
            continue
        info_file = _info_path(path)
        built = ""
        if info_file.is_file():
            built = str(
                json.loads(info_file.read_text(encoding="utf-8")).get(
                    "source_commit", ""
                )
            )
        binaries[name] = {"sha256": _sha256(path), "source_commit": built}
    target = root / REVISION_FILE
    _write_json_atomic(
        target,
        {
            "commit": _resolve_rev(rev, repo),
            "dirty": _dirty(repo),
            "deployed_at": _utc_now(),
            "binaries": binaries,
        },
    )
    return target


def _split_names(raw: str) -> list[str]:
    return [n for n in raw.replace(",", " ").split() if n]


def _validate_names(names: list[str]) -> None:
    unknown = [n for n in names if n not in BINARY_SOURCES]
    if unknown:
        raise ValueError(f"unknown binary name(s): {', '.join(unknown)}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Nuitka binaries.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("write-info", help="write build info next to a binary")
    p.add_argument("--binary", required=True, type=Path)
    p.add_argument("--module", required=True)
    p.add_argument("--repo", type=Path, default=Path("."))

    p = sub.add_parser("check", help="check freshness and integrity")
    p.add_argument("--bin-dir", required=True, type=Path)
    p.add_argument("--rev", default="auto")
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--names", default="")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--list-stale", action="store_true")

    p = sub.add_parser("swap", help="swap a staged set into the bin directory")
    p.add_argument("--stage-dir", required=True, type=Path)
    p.add_argument("--bin-dir", required=True, type=Path)
    p.add_argument("--prev-dir", type=Path)
    p.add_argument("--names", default="")
    p.add_argument("--consume", action="store_true")

    p = sub.add_parser("rollback", help="restore the previous set")
    p.add_argument("--bin-dir", required=True, type=Path)
    p.add_argument("--prev-dir", type=Path)
    p.add_argument("--names", default="")

    p = sub.add_parser("record-revision", help="write DEPLOYED_REV")
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--rev", default="auto")
    p.add_argument("--repo", type=Path, default=Path("."))
    return parser


def _run(args: argparse.Namespace) -> int:
    names = _split_names(getattr(args, "names", ""))
    _validate_names(names)
    if args.command == "write-info":
        print(write_info(args.binary, args.module, args.repo))
        return EXIT_OK
    if args.command == "check":
        results, code = check(
            args.bin_dir,
            args.rev,
            args.repo,
            names or list(BINARY_SOURCES),
            args.strict,
        )
        if args.list_stale:
            print(
                " ".join(n for n, (s, _) in results.items() if s in _REBUILD_STATUSES)
            )
            return EXIT_OK
        for name, (status, detail) in results.items():
            print(f"{name}: {status} - {detail}")
        for problem in _dir_problems(args.bin_dir):
            print(f"bin directory: {problem}", file=sys.stderr)
        return code
    if args.command == "swap":
        prev = args.prev_dir or _default_prev(args.bin_dir)
        selected = names or sorted(
            n for n in BINARY_SOURCES if (args.stage_dir / n).is_file()
        )
        if not selected:
            print("swap refused: no staged binaries found", file=sys.stderr)
            return EXIT_FAIL
        return swap(args.stage_dir, args.bin_dir, prev, selected, args.consume)
    if args.command == "rollback":
        prev = args.prev_dir or _default_prev(args.bin_dir)
        return rollback(args.bin_dir, prev, names)
    print(record_revision(args.root, args.rev, args.repo))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the selected subcommand."""
    args = _build_parser().parse_args(argv)
    try:
        return _run(args)
    except ValueError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
