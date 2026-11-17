"""tools/generate_issue_batch.py

Batch issue generator: one Markdown spec of issue blocks becomes several
`issues/{timestamp}_{id}_{slug}.md` documents (plans/20261117-125502, REQ-001 to
REQ-006). The single-issue path of `tools/generate_workitem.py` is unchanged; this
tool imports its `issue_output_path`, `check_collision`, and `GenerationError`.

Spec format — each block starts with a delimiter line followed by a document in
the `templates/issue.md` shape:

    <!-- issue: {id} {slug} -->
    <issue document>

`{id}` matches `[a-z0-9]+` with at least one letter; `{slug}` matches `[a-z0-9_-]+`
with at most four words; ids are unique in the spec. A `{{issue:<id>}}` token in a
block is replaced by the repository-relative path of that id's issue; the
`Generated at` field is set to the block's allocated timestamp; no other content
changes.

Timestamps come from one clock read and advance in strictly increasing one-second
steps in spec order. Every allocated path is checked in `issues/` and
`issues/done/` before the first write. `--dry-run` prints the planned paths and
writes nothing. If a write fails midway the already-created files are reported
and deleted by nobody. After the writes, `tools/check_workitem_structure.py` runs
once over all created paths and its report is printed.

Usage:
    python tools/generate_issue_batch.py <spec.md> [--dry-run]

Exit codes: 0 success; 1 the checker reported findings; 2 usage, validation,
collision, write, or checker error.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 — fixed argv built from sys.executable and repo scripts, no shell
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import add_dry_run_argument, atomic_write_text
from tools.generate_workitem import GenerationError, check_collision, issue_output_path

ROOT_DIR = Path(__file__).resolve().parent.parent
CHECKER_SCRIPT = ROOT_DIR / "tools" / "check_workitem_structure.py"

_DELIM_RE = re.compile(r"^<!-- issue: (\S+) (\S+) -->$")
_DELIM_PREFIX = "<!-- issue:"
_ISSUE_ID_RE = re.compile(r"[a-z0-9]*[a-z][a-z0-9]*")
_SLUG_RE = re.compile(r"[a-z0-9]+(?:[_-][a-z0-9]+){0,3}")
_REF_TOKEN_RE = re.compile(r"\{\{issue:([^\s{}]+)\}\}")
_GENERATED_AT_PREFIX = "Generated at:"
_GENERATED_AT_PLACEHOLDER = "{{Generated at}}"


@dataclass(frozen=True)
class IssueBlock:
    """One parsed spec block: validated `id`, `slug`, and raw document body."""

    issue_id: str
    slug: str
    body: str


def _now() -> datetime:
    return datetime.now()


def _error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 2


def parse_spec(text: str) -> list[IssueBlock]:
    """Split the spec into validated blocks; raise GenerationError on any violation."""
    blocks: list[IssueBlock] = []
    pending: tuple[str, str] | None = None
    body_lines: list[str] = []

    def flush() -> None:
        nonlocal pending, body_lines
        if pending is not None:
            blocks.append(_validated_block(pending[0], pending[1], body_lines))
            pending, body_lines = None, []

    for line in text.splitlines():
        if line.startswith(_DELIM_PREFIX):
            match = _DELIM_RE.match(line)
            if match is None:
                raise GenerationError(f"malformed issue delimiter line: {line!r}")
            flush()
            pending = (match.group(1), match.group(2))
        elif pending is None:
            if line.strip():
                raise GenerationError(
                    "spec text found before the first issue delimiter"
                )
        else:
            body_lines.append(line)
    if pending is None:
        raise GenerationError("spec contains no issue blocks")
    flush()
    _check_unique_ids(blocks)
    return blocks


def _validated_block(issue_id: str, slug: str, body_lines: list[str]) -> IssueBlock:
    if _ISSUE_ID_RE.fullmatch(issue_id) is None:
        raise GenerationError(
            f"invalid issue id {issue_id!r}: must match [a-z0-9]+ with at least one letter"
        )
    if _SLUG_RE.fullmatch(slug) is None:
        raise GenerationError(
            f"invalid slug {slug!r} for issue {issue_id!r}: must match [a-z0-9_-]+ "
            "with at most four words"
        )
    body = "\n".join(body_lines).strip()
    if not body:
        raise GenerationError(f"empty issue block for id {issue_id!r}")
    return IssueBlock(issue_id=issue_id, slug=slug, body=body)


def _check_unique_ids(blocks: list[IssueBlock]) -> None:
    seen: set[str] = set()
    for block in blocks:
        if block.issue_id in seen:
            raise GenerationError(f"duplicate issue id {block.issue_id!r} in the spec")
        seen.add(block.issue_id)


def allocate_timestamps(count: int, base: datetime) -> list[str]:
    """One clock read, strictly increasing one-second steps in spec order."""
    return [
        (base + timedelta(seconds=i)).strftime("%Y%m%d-%H%M%S") for i in range(count)
    ]


def allocate_paths(blocks: list[IssueBlock], timestamps: list[str]) -> list[Path]:
    return [
        issue_output_path(ts, block.issue_id, block.slug)
        for block, ts in zip(blocks, timestamps)
    ]


def preflight_collisions(paths: list[Path]) -> None:
    for path in paths:
        clash = check_collision(path)
        if clash is not None:
            raise GenerationError(
                f"allocated path {clash} collides with an existing file"
            )


def reference_mapping(blocks: list[IssueBlock], paths: list[Path]) -> dict[str, str]:
    return {block.issue_id: f"issues/{path.name}" for block, path in zip(blocks, paths)}


def resolve_references(body: str, mapping: dict[str, str], issue_id: str) -> str:
    def replace(match: re.Match[str]) -> str:
        ref = match.group(1)
        if ref not in mapping:
            raise GenerationError(f"issue {issue_id!r} references unknown id {ref!r}")
        return mapping[ref]

    return _REF_TOKEN_RE.sub(replace, body)


def set_generated_at(body: str, timestamp: str) -> str:
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(_GENERATED_AT_PREFIX):
            lines[index] = f"Generated at: {timestamp}"
            return "\n".join(lines)
    if _GENERATED_AT_PLACEHOLDER in body:
        return body.replace(_GENERATED_AT_PLACEHOLDER, timestamp)
    return f"Generated at: {timestamp}\n\n{body}"


def render_document(block: IssueBlock, timestamp: str, mapping: dict[str, str]) -> str:
    body = resolve_references(block.body, mapping, block.issue_id)
    return set_generated_at(body, timestamp)


def _run_checker(paths: list[Path]) -> tuple[int, str]:
    result = subprocess.run(  # nosec B603 — fixed argv from sys.executable and the repo checker script, no shell
        [sys.executable, str(CHECKER_SCRIPT), "--file", *[str(path) for path in paths]],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        check=False,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate issue files from a batch spec."
    )
    parser.add_argument(
        "spec", type=Path, help="Markdown spec of `<!-- issue: {id} {slug} -->` blocks"
    )
    add_dry_run_argument(parser)
    return parser.parse_args(argv)


def _write_documents(paths: list[Path], documents: list[str]) -> int:
    created: list[Path] = []
    try:
        for path, document in zip(paths, documents):
            atomic_write_text(path, document + "\n")
            created.append(path)
            print(f"created: {path}")
    except OSError as exc:
        print(f"error: write failed: {exc}", file=sys.stderr)
        print("created before the failure (none will be deleted):", file=sys.stderr)
        for path in created:
            print(f"  {path}", file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        spec_text = args.spec.read_text(encoding="utf-8")
    except OSError as exc:
        return _error(f"cannot read spec {args.spec}: {exc}")
    try:
        blocks = parse_spec(spec_text)
        timestamps = allocate_timestamps(len(blocks), _now())
        paths = allocate_paths(blocks, timestamps)
        preflight_collisions(paths)
        mapping = reference_mapping(blocks, paths)
        documents = [
            render_document(block, ts, mapping) for block, ts in zip(blocks, timestamps)
        ]
    except GenerationError as exc:
        return _error(str(exc))
    if args.dry_run:
        for path in paths:
            print(f"planned: {path}")
        print("dry run: nothing written")
        return 0
    write_status = _write_documents(paths, documents)
    if write_status != 0:
        return write_status
    code, output = _run_checker(paths)
    if output:
        print(output)
    if code == 0:
        return 0
    if code == 1:
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
