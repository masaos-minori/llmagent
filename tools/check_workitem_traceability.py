#!/usr/bin/env python3
"""tools/check_workitem_traceability.py — Cross-check work-item Traceability sections.

Read-only checker over `issues/`, `plans/`, and `implementations/` (each
including its `done/` subdirectory). Parses every document's `## Traceability`
section (per `templates/traceability.md`) and reports four independent
finding categories, all computed from one shared parsed graph (no directory
is walked more than once):

- missing-source-file: a non-`N/A` `Source *` field points to a path that
  does not exist in the repository.
- no-plan-yet: an open `issues/*.md` file has no `plans/*.md` (or
  `plans/done/*.md`) document whose `Source issue` field references it back,
  and the issue is older than `--age-threshold-days`.
- no-procedure-yet: symmetric to no-plan-yet, for `plans/*.md` (excluding
  `plans/done/`) against `implementations/*.md`/`implementations/done/*.md`'s
  `Source plan` field.
- stale-target-heuristic: an issue mentions a document (`ADR-\\d+` or a
  `docs/....md` path) that was modified (via `git log`, falling back to file
  mtime) after the issue's own filename timestamp — surfaced as a candidate
  only, never a verdict.

Never writes, renames, moves, or deletes anything under `issues/`, `plans/`,
or `implementations/`.

Usage:
    python tools/check_workitem_traceability.py
    python tools/check_workitem_traceability.py --format json
    python tools/check_workitem_traceability.py --format csv
    python tools/check_workitem_traceability.py --age-threshold-days 30

Exit code: 0 when zero missing-source-file findings exist (the only category
that gates exit status — no-plan-yet/no-procedure-yet/stale-target-heuristic
are informational); 1 otherwise.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import orjson

ROOT_DIR = Path(__file__).resolve().parent.parent

# No repository precedent ties a specific number to this exact use case
# (UNK-01, see implementations/20260901-114312_01_tools_check_workitem_traceability_py.md
# Assumptions) — 30 days is a generous default chosen to avoid flagging
# normal, recently-filed work while still surfacing genuinely stale items.
DEFAULT_AGE_THRESHOLD_DAYS = 30

_HEADING_RE = re.compile(r"(?m)^## Traceability\s*$")
_NEXT_HEADING_RE = re.compile(r"(?m)^## ")
_FIELD_LINE_RE = re.compile(r"^-\s+\*\*([^*]+)\*\*:\s*(.+?)\s*$")
_FILENAME_TIMESTAMP_RE = re.compile(r"^(\d{8}-\d{6})_")
_DOC_MENTION_RE = re.compile(r"ADR-\d+|docs/[\w./-]+\.md")

SOURCE_FIELD_NAMES = (
    "Source issue",
    "Source plan",
    "Source implementation procedure",
    "Source requirement",
)

# (kind, directory relative to ROOT_DIR, is_done)
_WORK_ITEM_DIRS: tuple[tuple[str, str, bool], ...] = (
    ("issue", "issues", False),
    ("issue", "issues/done", True),
    ("plan", "plans", False),
    ("plan", "plans/done", True),
    ("implementation", "implementations", False),
    ("implementation", "implementations/done", True),
)


@dataclass
class WorkItemDocument:
    """One parsed `issues/`, `plans/`, or `implementations/` Markdown file."""

    path: Path
    rel_path: str
    kind: str
    is_done: bool
    text: str
    traceability_found: bool
    fields: dict[str, str] = field(default_factory=dict)


def _is_na(value: str) -> bool:
    return value.strip().lower().startswith("n/a")


def _clean_field_value(value: str) -> str:
    """Strip surrounding whitespace, a trailing prose annotation, and an
    optional matching backtick pair.

    Live Traceability sections mix backtick-quoted paths
    (`` `issues/x.md` ``) and bare paths (`issues/x.md`) — both are the same
    logical value. Some sampled sections (e.g.
    `plans/done/20260828-150100_plan.md`'s `Source requirement` line) append
    a prose annotation after the path (`` `path.md` ("description") — note
    ``); the path is always the whitespace-delimited first token, so only
    that token is kept.
    """
    cleaned = value.strip()
    first_token = cleaned.split(None, 1)[0] if cleaned else cleaned
    if (
        len(first_token) >= 2
        and first_token.startswith("`")
        and first_token.endswith("`")
    ):
        first_token = first_token[1:-1].strip()
    return first_token


def extract_traceability_fields(text: str) -> tuple[bool, dict[str, str]]:
    """Return (heading_found, {source_field_name: cleaned_value}).

    Only the four `Source *` fields are extracted; a value starting with
    `N/A` (case-insensitive) is dropped, matching every sampled Traceability
    section's convention.
    """
    heading_match = _HEADING_RE.search(text)
    if heading_match is None:
        return False, {}

    section_start = heading_match.end()
    next_heading = _NEXT_HEADING_RE.search(text, section_start)
    section_end = next_heading.start() if next_heading else len(text)
    section_text = text[section_start:section_end]

    fields: dict[str, str] = {}
    for line in section_text.splitlines():
        line_match = _FIELD_LINE_RE.match(line)
        if line_match is None:
            continue
        field_name = line_match.group(1).strip()
        if field_name not in SOURCE_FIELD_NAMES:
            continue
        raw_value = line_match.group(2)
        if _is_na(raw_value):
            continue
        cleaned_value = _clean_field_value(raw_value)
        # A handful of live sections (e.g. an implementation procedure's
        # `Source implementation procedure` line recording a multi-line
        # "supersedes {path}, {path}, ..." list) put prose, not a path, on
        # the matched bullet line itself and continue the real paths on
        # unindented continuation lines this parser does not join. Such a
        # value never contains a path separator — skip it as not a source
        # reference to validate, rather than reporting bare prose as a
        # missing file.
        if "/" not in cleaned_value:
            continue
        fields[field_name] = cleaned_value
    return True, fields


def discover_documents() -> list[WorkItemDocument]:
    """Walk the six work-item directories and parse each file's Traceability."""
    documents: list[WorkItemDocument] = []
    for kind, rel_dir, is_done in _WORK_ITEM_DIRS:
        dir_path = ROOT_DIR / rel_dir
        if not dir_path.is_dir():
            continue
        for md_path in sorted(dir_path.glob("*.md")):
            text = md_path.read_text(encoding="utf-8")
            traceability_found, fields = extract_traceability_fields(text)
            documents.append(
                WorkItemDocument(
                    path=md_path,
                    rel_path=md_path.relative_to(ROOT_DIR).as_posix(),
                    kind=kind,
                    is_done=is_done,
                    text=text,
                    traceability_found=traceability_found,
                    fields=fields,
                )
            )
    return documents


def _filename_timestamp(path: Path) -> datetime | None:
    """Parse the leading `YYYYMMDD-HHMMSS_` timestamp from a filename, if any.

    Several legacy work-item files (see confirmed evidence at implementation
    time, e.g. `issues/LLM_agent_improve_summary.md`) do not carry this
    prefix — callers must tolerate `None`.
    """
    match = _FILENAME_TIMESTAMP_RE.match(path.name)
    if match is None:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d-%H%M%S")
    except ValueError:
        return None


def _effective_filed_time(path: Path) -> datetime:
    """Filename timestamp when parseable, else file mtime as a best-effort
    fallback (age-threshold gating only — the stale-target heuristic uses
    the strict filename timestamp and skips files without one instead).
    """
    timestamp = _filename_timestamp(path)
    if timestamp is not None:
        return timestamp
    return datetime.fromtimestamp(path.stat().st_mtime)


def _git_or_mtime(path: Path) -> datetime:
    """Last-modified time via `git log`, falling back to file mtime."""
    try:
        # bandit: B404/B603/B607 (Low) are expected here per
        # rules/coding.md Bandit priority findings ("B603 ... Preferred;
        # document if shell=True needed") — shell=False with this fixed
        # argument list never interpolates `path` into a shell string, and
        # PATH-based `git` resolution (not a hardcoded absolute path) is the
        # portable, intended behavior across this repository's dev/CI
        # environments.
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(path)],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except OSError:
        return datetime.fromtimestamp(path.stat().st_mtime)

    output = result.stdout.strip()
    if result.returncode == 0 and output.isdigit():
        return datetime.fromtimestamp(int(output))
    return datetime.fromtimestamp(path.stat().st_mtime)


def _resolve_doc_mention(mention: str) -> Path | None:
    """Resolve an `ADR-\\d+` or `docs/....md` mention to an existing file."""
    if mention.startswith("ADR-"):
        adr_match = re.match(r"ADR-(\d+)", mention)
        if adr_match is None:
            return None
        candidates = sorted(ROOT_DIR.glob(f"docs/adr/ADR-{adr_match.group(1)}-*.md"))
        return candidates[0] if candidates else None

    candidate = ROOT_DIR / mention
    return candidate if candidate.is_file() else None


_WORKITEM_TOP_DIRS = frozenset({"issues", "plans", "implementations", "requires"})


def _source_path_exists(value: str) -> bool:
    """Return whether a `Source *` field value resolves to an existing file.

    A path recorded in a Traceability section is a snapshot taken when the
    referencing document was generated; the referenced document normally
    keeps moving through its own lifecycle afterward (`issues/` ->
    `issues/done/`, `plans/` -> `plans/done/`, `implementations/` ->
    `implementations/done/`, `requires/` -> `requires/done/`). Confirmed
    against the live repository: of 550 literal-path misses sampled at
    verification time, 544 resolved once a sibling `done/` segment was
    inserted or removed — that lifecycle move, not a broken reference, so
    it must not be reported as missing-source-file.
    """
    candidate = Path(value)
    resolved = candidate if candidate.is_absolute() else ROOT_DIR / candidate
    if resolved.exists():
        return True

    parts = candidate.parts
    if len(parts) >= 2 and parts[0] in _WORKITEM_TOP_DIRS:
        if parts[1] == "done":
            alt_parts = (parts[0], *parts[2:])
        else:
            alt_parts = (parts[0], "done", *parts[1:])
        alt_resolved = ROOT_DIR / Path(*alt_parts)
        if alt_resolved.exists():
            return True
    return False


def make_finding(category: str, file_path: str, detail: str) -> dict[str, str]:
    return {"category": category, "file": file_path, "detail": detail}


def find_parse_errors(documents: list[WorkItemDocument]) -> list[dict[str, str]]:
    """Files without a `## Traceability` heading at all.

    Informational only — most `issues/*.md` files are raw, manually-filed
    issues that legitimately predate (or never require) a generated
    Traceability section (confirmed against the live repository: dozens of
    files in `issues/` and thousands under `plans/done/`/`implementations/done/`
    predate the template's introduction). This category exists so a genuinely
    malformed heading in a workflow-generated document is still visible, not
    silently skipped or crashed on.
    """
    return [
        make_finding(
            "parse-error",
            doc.rel_path,
            "no '## Traceability' heading found",
        )
        for doc in documents
        if not doc.traceability_found
    ]


def find_missing_source_files(
    documents: list[WorkItemDocument],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for doc in documents:
        for field_name, value in doc.fields.items():
            if not _source_path_exists(value):
                findings.append(
                    make_finding(
                        "missing-source-file",
                        doc.rel_path,
                        f"{field_name} target does not exist: {value}",
                    )
                )
    return findings


def find_no_plan_yet(
    documents: list[WorkItemDocument], age_threshold_days: int
) -> list[dict[str, str]]:
    referenced_issues = {
        doc.fields["Source issue"]
        for doc in documents
        if doc.kind == "plan" and "Source issue" in doc.fields
    }

    findings: list[dict[str, str]] = []
    now = datetime.now()
    for doc in documents:
        if doc.kind != "issue" or doc.is_done:
            continue
        if doc.rel_path in referenced_issues:
            continue
        filed = _effective_filed_time(doc.path)
        age_days = (now - filed).days
        if age_days >= age_threshold_days:
            findings.append(
                make_finding(
                    "no-plan-yet",
                    doc.rel_path,
                    f"no plan references this issue as Source issue "
                    f"(filed {age_days} day(s) ago)",
                )
            )
    return findings


def find_no_procedure_yet(
    documents: list[WorkItemDocument], age_threshold_days: int
) -> list[dict[str, str]]:
    referenced_plans = {
        doc.fields["Source plan"]
        for doc in documents
        if doc.kind == "implementation" and "Source plan" in doc.fields
    }

    findings: list[dict[str, str]] = []
    now = datetime.now()
    for doc in documents:
        if doc.kind != "plan" or doc.is_done:
            continue
        if doc.rel_path in referenced_plans:
            continue
        filed = _effective_filed_time(doc.path)
        age_days = (now - filed).days
        if age_days >= age_threshold_days:
            findings.append(
                make_finding(
                    "no-procedure-yet",
                    doc.rel_path,
                    f"no implementation procedure references this plan as "
                    f"Source plan (filed {age_days} day(s) ago)",
                )
            )
    return findings


def find_stale_targets(documents: list[WorkItemDocument]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for doc in documents:
        if doc.kind != "issue":
            continue
        filed = _filename_timestamp(doc.path)
        if filed is None:
            continue
        mentions = dict.fromkeys(_DOC_MENTION_RE.findall(doc.text))
        reported_targets: set[Path] = set()
        for mention in mentions:
            resolved = _resolve_doc_mention(mention)
            if resolved is None:
                continue
            # Two distinct textual mentions (e.g. `ADR-008` and the full
            # `docs/adr/ADR-008-....md` path) commonly resolve to the same
            # file within one document — report each target once, not once
            # per spelling.
            if resolved in reported_targets:
                continue
            modified = _git_or_mtime(resolved)
            if modified > filed:
                reported_targets.add(resolved)
                findings.append(
                    make_finding(
                        "stale-target-heuristic",
                        doc.rel_path,
                        f"references {mention} "
                        f"({resolved.relative_to(ROOT_DIR).as_posix()}), "
                        f"modified after this issue was filed",
                    )
                )
    return findings


def collect_findings(
    documents: list[WorkItemDocument], age_threshold_days: int
) -> list[dict[str, str]]:
    """Run all report categories over one shared parsed graph."""
    findings: list[dict[str, str]] = []
    findings.extend(find_parse_errors(documents))
    findings.extend(find_missing_source_files(documents))
    findings.extend(find_no_plan_yet(documents, age_threshold_days))
    findings.extend(find_no_procedure_yet(documents, age_threshold_days))
    findings.extend(find_stale_targets(documents))
    return findings


def render_text(findings: list[dict[str, str]]) -> str:
    if not findings:
        return "No findings.\n"

    lines: list[str] = []
    categories = dict.fromkeys(f["category"] for f in findings)
    for category in categories:
        category_findings = [f for f in findings if f["category"] == category]
        lines.append(f"[{category}] ({len(category_findings)})")
        for finding in category_findings:
            lines.append(f"  {finding['file']}: {finding['detail']}")
    lines.append(f"\n{len(findings)} finding(s) total.")
    return "\n".join(lines) + "\n"


def render_json(findings: list[dict[str, str]]) -> str:
    return orjson.dumps(
        findings, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
    ).decode()


def render_csv(findings: list[dict[str, str]]) -> str:
    import io

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["category", "file", "detail"])
    writer.writeheader()
    writer.writerows(findings)
    return buffer.getvalue()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only cross-check of Traceability sections across issues/, "
            "plans/, and implementations/ (including done/ subdirectories). "
            "Reports missing-source-file, no-plan-yet, no-procedure-yet, and "
            "stale-target-heuristic findings."
        )
    )
    parser.add_argument(
        "--age-threshold-days",
        type=int,
        default=DEFAULT_AGE_THRESHOLD_DAYS,
        help=(
            "Minimum age (in days, by filename timestamp) before an "
            "unreferenced issue/plan is reported as no-plan-yet/"
            f"no-procedure-yet (default: {DEFAULT_AGE_THRESHOLD_DAYS})"
        ),
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default=None,
        help="Machine-readable output format (default: human-readable text)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    documents = discover_documents()
    findings = collect_findings(documents, args.age_threshold_days)

    if args.format == "json":
        print(render_json(findings))
    elif args.format == "csv":
        print(render_csv(findings), end="")
    else:
        print(render_text(findings), end="")

    has_missing_source_file = any(
        f["category"] == "missing-source-file" for f in findings
    )
    return 1 if has_missing_source_file else 0


if __name__ == "__main__":
    sys.exit(main())
