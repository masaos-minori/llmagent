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
- target-file-mismatch: an `implementations/*.md` document's Traceability
  `Related target files` value does not exactly match its own body's
  `### Target file` value. `templates/implementation-procedure.md` guarantees
  these are the same single path for a given document — a mismatch means
  either a copy-paste error in Traceability (the field was carried over from
  a different row/document without updating), or something more serious: a
  concurrent write interleaved a different document's content into this
  file. Confirmed live in this repository (see
  implementations/done/20260911-065129_02_scripts_eventbus_broker.py.md,
  whose Traceability names a different Plan's target file, and
  implementations/20260911-073720_01_scripts_eventbus_db.py.md, whose body
  content switches partway through to an unrelated Plan's material) — both
  were only caught by a human reading the full document end-to-end.

A document may carry companion test files in a `### Companion test files`
section (`templates/implementation-procedure.md`): its `Related target files`
then lists the target first and each companion, and the equality check
compares that list with the body's target followed by its companions. A
document without a companion section is checked exactly as before.

`--plan-coverage PLAN` is an opt-in mode that checks one Plan's rows against
its procedure documents instead of running the default scan (a Plan mid-batch
legitimately has uncovered rows, so it is not part of the default scan or the
pre-commit hook). Findings: row-uncovered, path-covered-twice,
companion-multi-row, companion-not-eligible; exit 1 on any finding.

Never writes, renames, moves, or deletes anything under `issues/`, `plans/`,
or `implementations/`.

Usage:
    python tools/check_workitem_traceability.py
    python tools/check_workitem_traceability.py --format json
    python tools/check_workitem_traceability.py --format csv
    python tools/check_workitem_traceability.py --age-threshold-days 30
    python tools/check_workitem_traceability.py --plan-coverage plans/<plan>.md

Exit code: 0 when zero missing-source-file and zero target-file-mismatch
findings exist (the two categories that gate exit status —
no-plan-yet/no-procedure-yet/stale-target-heuristic are informational);
1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._report import (
    PROFILE_WORKITEM,
    ReportFinding,
    add_format_argument,
    render_csv,
    render_json,
    render_text,
)
from tools._tool_common import REPO_ROOT, run_git

ROOT_DIR = REPO_ROOT

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

# Deliberately NOT part of SOURCE_FIELD_NAMES / extract_traceability_fields:
# for `plan`-kind documents this field legitimately holds a multi-path list
# or prose (e.g. "see Target Files or Areas above", confirmed live in at
# least 2 processed plans), which would falsely read as a broken single
# path. It is only meaningful as a single-path equality check for
# `implementation`-kind documents, where the template guarantees a single
# target file — see find_target_file_mismatches().
RELATED_TARGET_FILES_FIELD_NAME = "Related target files"

_TARGET_FILE_HEADING_RE = re.compile(r"(?m)^### Target file\s*$")
_ANY_HEADING_RE = re.compile(r"(?m)^#+\s")
_BULLET_LEAD_RE = re.compile(r"^[-*+]\s+")
_COMPANION_HEADING_RE = re.compile(r"(?m)^### Companion test files\s*$")
_BACKTICK_PATH_RE = re.compile(r"`([^`\s]+)`")
_TOP_LEVEL_BULLET_RE = re.compile(r"^[-*+]\s+")
_TARGET_FILES_HEADING = "## Implementation Target Files"
_UNESCAPED_PIPE_RE = re.compile(r"(?<!\\)\|")
_SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")

COVERAGE_CATEGORIES = (
    "row-uncovered",
    "path-covered-twice",
    "companion-multi-row",
    "companion-not-eligible",
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
    # `templates/issue.md` writes N/A values inside backticks (`N/A: not filed
    # from a Plan`), so an opening backtick must not hide the marker.
    return value.strip().lstrip("`").lower().startswith("n/a")


def _clean_field_value(value: str) -> str:
    """Strip surrounding whitespace, a trailing prose annotation, and an
    optional matching backtick pair.

    Live Traceability sections mix backtick-quoted paths
    (`` `issues/x.md` ``) and bare paths (`issues/x.md`) — both are the same
    logical value. Some sampled sections (e.g.
    `plans/done/20260828-150100_plan.md`'s `Source requirement` line) append
    a prose annotation after the path (`` `path.md` ("description") — note
    ``); the path is always the whitespace-delimited first token, so only
    that token is kept. A backslash-escaped backtick pair (`` \\`path\\` ``) and
    sentence-ending punctuation after the token (`` `path.py`. ``) are the same
    logical value too and are normalized away.
    """
    cleaned = value.strip()
    first_token = cleaned.split(None, 1)[0] if cleaned else cleaned
    first_token = first_token.replace("\\`", "`").rstrip(".,;")
    if (
        len(first_token) >= 2
        and first_token.startswith("`")
        and first_token.endswith("`")
    ):
        first_token = first_token[1:-1].strip()
    return first_token


def _traceability_section_text(text: str) -> str | None:
    """Return the raw `## Traceability` section body, or None if absent."""
    heading_match = _HEADING_RE.search(text)
    if heading_match is None:
        return None

    section_start = heading_match.end()
    next_heading = _NEXT_HEADING_RE.search(text, section_start)
    section_end = next_heading.start() if next_heading else len(text)
    return text[section_start:section_end]


def extract_traceability_fields(text: str) -> tuple[bool, dict[str, str]]:
    """Return (heading_found, {source_field_name: cleaned_value}).

    Only the four `Source *` fields are extracted; a value starting with
    `N/A` (case-insensitive) is dropped, matching every sampled Traceability
    section's convention.
    """
    section_text = _traceability_section_text(text)
    if section_text is None:
        return False, {}

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


def extract_related_target_files_value(text: str) -> str | None:
    """Return the cleaned `Related target files` Traceability value, or None
    if the heading/field is absent or its value is `N/A`.

    Unlike extract_traceability_fields(), this does not drop values without
    a `/` — for `implementation`-kind documents this field is expected to be
    a single bare path, and a missing-path value here (e.g. accidentally
    left as prose) is itself evidence of a mismatch, not something to
    silently tolerate.
    """
    section_text = _traceability_section_text(text)
    if section_text is None:
        return None

    for line in section_text.splitlines():
        line_match = _FIELD_LINE_RE.match(line)
        if line_match is None:
            continue
        if line_match.group(1).strip() != RELATED_TARGET_FILES_FIELD_NAME:
            continue
        raw_value = line_match.group(2)
        if _is_na(raw_value):
            return None
        return _clean_field_value(raw_value)
    return None


def extract_target_file_value(text: str) -> str | None:
    """Return the cleaned value of the body's `### Target file` heading, or
    None if the heading is absent or nothing but another heading follows it.

    A body section may list the path as a markdown list item with a leading
    `-` bullet; that bullet is dropped before parsing so the parser reads the
    path rather than the `-` token, which would otherwise be read as a literal
    `-` and trip the target-file-mismatch check.
    """
    heading_match = _TARGET_FILE_HEADING_RE.search(text)
    if heading_match is None:
        return None

    remainder = text[heading_match.end() :]
    for line in remainder.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _ANY_HEADING_RE.match(line):
            return None
        # Tolerate a leading markdown list bullet (`-`, `*`, `+`) that some
        # procedures append to the target-file path; drop exactly one so the
        # first-token parse yields the path, not the bullet. A lone `-` (no
        # trailing whitespace) is left intact and still reported as a mismatch.
        stripped = _BULLET_LEAD_RE.sub("", stripped, count=1)
        return _clean_field_value(stripped)
    return None


def extract_related_target_files_list(text: str) -> list[str]:
    """Return the `Related target files` paths in order, or an empty list when
    the heading/field is absent or `N/A`.

    A list is read from its backticked tokens (target first, then companions);
    a value with no backticked token falls back to the single first-token path
    that extract_related_target_files_value() returns.
    """
    section_text = _traceability_section_text(text)
    if section_text is None:
        return []
    for line in section_text.splitlines():
        line_match = _FIELD_LINE_RE.match(line)
        if line_match is None:
            continue
        if line_match.group(1).strip() != RELATED_TARGET_FILES_FIELD_NAME:
            continue
        raw_value = line_match.group(2)
        if _is_na(raw_value):
            return []
        backticked = _BACKTICK_PATH_RE.findall(raw_value)
        if backticked:
            return backticked
        cleaned = _clean_field_value(raw_value)
        return [cleaned] if cleaned else []
    return []


def extract_companion_files(text: str) -> list[str]:
    """Return the companion test file paths of the body's
    `### Companion test files` section, or an empty list when it is absent.

    A companion is a top-level list item whose first backticked token is its
    path; indented lines (`Procedure:`, `Validation:`) are ignored and the
    section ends at the next heading.
    """
    heading_match = _COMPANION_HEADING_RE.search(text)
    if heading_match is None:
        return []
    companions: list[str] = []
    for line in text[heading_match.end() :].splitlines():
        if _ANY_HEADING_RE.match(line):
            break
        if not _TOP_LEVEL_BULLET_RE.match(line):
            continue
        path_match = _BACKTICK_PATH_RE.search(line)
        if path_match is not None:
            companions.append(path_match.group(1))
    return companions


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
        result = run_git(
            "log", "-1", "--format=%ct", "--", str(path), cwd=ROOT_DIR, timeout=10
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
        candidates = sorted(
            ROOT_DIR.glob(f"docs/10_adr/adr_02_??_{adr_match.group(1)}_*.md")
        )
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


def find_parse_errors(documents: list[WorkItemDocument]) -> list[ReportFinding]:
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
        ReportFinding(
            code="parse-error",
            file=doc.rel_path,
            message="no '## Traceability' heading found",
        )
        for doc in documents
        if not doc.traceability_found
    ]


def find_missing_source_files(
    documents: list[WorkItemDocument],
) -> list[ReportFinding]:
    findings: list[ReportFinding] = []
    for doc in documents:
        for field_name, value in doc.fields.items():
            if not _source_path_exists(value):
                findings.append(
                    ReportFinding(
                        code="missing-source-file",
                        file=doc.rel_path,
                        message=f"{field_name} target does not exist: {value}",
                    )
                )
    return findings


def find_no_plan_yet(
    documents: list[WorkItemDocument], age_threshold_days: int
) -> list[ReportFinding]:
    referenced_issues = {
        doc.fields["Source issue"]
        for doc in documents
        if doc.kind == "plan" and "Source issue" in doc.fields
    }

    findings: list[ReportFinding] = []
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
                ReportFinding(
                    code="no-plan-yet",
                    file=doc.rel_path,
                    message=f"no plan references this issue as Source issue "
                    f"(filed {age_days} day(s) ago)",
                )
            )
    return findings


def find_no_procedure_yet(
    documents: list[WorkItemDocument], age_threshold_days: int
) -> list[ReportFinding]:
    referenced_plans = {
        doc.fields["Source plan"]
        for doc in documents
        if doc.kind == "implementation" and "Source plan" in doc.fields
    }

    findings: list[ReportFinding] = []
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
                ReportFinding(
                    code="no-procedure-yet",
                    file=doc.rel_path,
                    message=f"no implementation procedure references this plan as "
                    f"Source plan (filed {age_days} day(s) ago)",
                )
            )
    return findings


def find_stale_targets(documents: list[WorkItemDocument]) -> list[ReportFinding]:
    findings: list[ReportFinding] = []
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
            # `docs/10_adr/ADR-008-....md` path) commonly resolve to the same
            # file within one document — report each target once, not once
            # per spelling.
            if resolved in reported_targets:
                continue
            modified = _git_or_mtime(resolved)
            if modified > filed:
                reported_targets.add(resolved)
                findings.append(
                    ReportFinding(
                        code="stale-target-heuristic",
                        file=doc.rel_path,
                        message=f"references {mention} "
                        f"({resolved.relative_to(ROOT_DIR).as_posix()}), "
                        f"modified after this issue was filed",
                    )
                )
    return findings


def find_target_file_mismatches(
    documents: list[WorkItemDocument],
) -> list[ReportFinding]:
    """`implementation`-kind documents only: the Traceability
    `Related target files` value must equal the body's `### Target file`
    value — the template's one-file-per-document contract guarantees these
    are the same single path. A mismatch means either a copy-paste error in
    Traceability, or something more serious: content interleaved from a
    different document (a corruption pattern confirmed live in this
    repository, see this function's module docstring).

    Deliberately restricted to `implementation`-kind documents: `plan`-kind
    documents legitimately use a multi-path list or prose value for the
    same field name, so the same equality check would misfire there.
    """
    findings: list[ReportFinding] = []
    for doc in documents:
        if doc.kind != "implementation":
            continue
        related = extract_related_target_files_value(doc.text)
        target = extract_target_file_value(doc.text)
        if related is None or target is None:
            continue
        companions = extract_companion_files(doc.text)
        if companions:
            declared = extract_related_target_files_list(doc.text)
            if declared[:1] != [target] or set(declared[1:]) != set(companions):
                findings.append(
                    ReportFinding(
                        code="target-file-mismatch",
                        file=doc.rel_path,
                        message=f"Traceability 'Related target files' "
                        f"({', '.join(declared)}) does not match body "
                        f"'### Target file' ({target}) followed by "
                        f"'### Companion test files' "
                        f"({', '.join(companions)}) -- the target must come "
                        f"first and every companion must be listed",
                    )
                )
            continue
        if related != target:
            findings.append(
                ReportFinding(
                    code="target-file-mismatch",
                    file=doc.rel_path,
                    message=f"Traceability 'Related target files' ({related}) does "
                    f"not match body '### Target file' ({target}) -- check "
                    f"for a copy-paste error or interleaved/corrupted "
                    f"content",
                )
            )
    return findings


def _split_table_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    inner = stripped[1:-1] if stripped.endswith("|") else stripped[1:]
    return [cell.strip() for cell in _UNESCAPED_PIPE_RE.split(inner)]


def _plan_target_rows(plan_text: str) -> list[tuple[str, str]]:
    """Return `(file_path, related_tests_cell)` per row of the Plan's
    `## Implementation Target Files` table, locating both columns by header
    text. The path is the first backticked token of its cell, else the cell's
    first token. A table without a `File Path` column yields no rows; a missing
    `Related Tests` column yields an empty cell.
    """
    in_section = False
    file_col: int | None = None
    tests_col: int | None = None
    header_seen = False
    rows: list[tuple[str, str]] = []
    for line in plan_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            in_section = stripped == _TARGET_FILES_HEADING
            continue
        if not in_section:
            continue
        cells = _split_table_cells(stripped)
        if not cells:
            continue
        if not header_seen:
            header_seen = True
            names = [cell.lower() for cell in cells]
            file_col = names.index("file path") if "file path" in names else None
            tests_col = (
                names.index("related tests") if "related tests" in names else None
            )
            continue
        if all(_SEPARATOR_CELL_RE.match(cell) for cell in cells if cell):
            continue
        if file_col is None or file_col >= len(cells):
            continue
        path_cell = cells[file_col]
        path_match = _BACKTICK_PATH_RE.search(path_cell)
        path = path_match.group(1) if path_match else _clean_field_value(path_cell)
        if not path:
            continue
        tests_cell = (
            cells[tests_col] if tests_col is not None and tests_col < len(cells) else ""
        )
        rows.append((path, tests_cell))
    return rows


def _resolve_plan_file(plan_path: Path) -> Path:
    return plan_path if plan_path.is_absolute() else ROOT_DIR / plan_path


def _procedures_of_plan(
    plan_path: Path, documents: list[WorkItemDocument]
) -> list[WorkItemDocument]:
    """Implementation documents whose `Source plan` is the checked Plan."""
    procedures: list[WorkItemDocument] = []
    for doc in documents:
        if doc.kind != "implementation":
            continue
        source_plan = doc.fields.get("Source plan")
        if source_plan is None or Path(source_plan).name != plan_path.name:
            continue
        procedures.append(doc)
    return procedures


def find_plan_coverage_findings(
    plan_path: Path, documents: list[WorkItemDocument]
) -> list[ReportFinding]:
    """Check one Plan's rows against its implementation procedure documents.

    A document covers its target and each companion. Reports a row covered by
    no document (row-uncovered), a path covered by two documents or twice in
    one (path-covered-twice), a companion named in the `Related Tests` cell of
    two or more rows (companion-multi-row), and a companion that is not a Plan
    row, is not under `tests/`, or is not named in the `Related Tests` cell of
    its own document's target row (companion-not-eligible). Paths are compared
    as written; no filesystem existence check is made.
    """
    plan_rel = plan_path.as_posix()
    rows = _plan_target_rows(_resolve_plan_file(plan_path).read_text(encoding="utf-8"))
    tests_by_path = dict(rows)
    row_paths = [path for path, _ in rows]

    covered_by: dict[str, list[str]] = {}
    findings: list[ReportFinding] = []
    procedures = _procedures_of_plan(plan_path, documents)
    for doc in procedures:
        target = extract_target_file_value(doc.text)
        companions = extract_companion_files(doc.text)
        covered = ([target] if target else []) + companions
        for path in covered:
            covered_by.setdefault(path, []).append(doc.rel_path)

        target_tests = tests_by_path.get(target or "", "")
        for companion in companions:
            if companion not in tests_by_path:
                reason = "is not a row of the Plan's Implementation Target Files"
            elif not companion.startswith("tests/"):
                reason = "is not under tests/"
            elif companion not in _BACKTICK_PATH_RE.findall(target_tests):
                reason = "is not named in the Related Tests cell of its target row"
            else:
                continue
            findings.append(
                ReportFinding(
                    code="companion-not-eligible",
                    file=doc.rel_path,
                    message=f"companion {companion} {reason} ({target})",
                )
            )

    for path in row_paths:
        if path not in covered_by:
            findings.append(
                ReportFinding(
                    code="row-uncovered",
                    file=plan_rel,
                    message=f"no procedure document covers row {path}",
                )
            )
    for path, doc_paths in covered_by.items():
        if len(doc_paths) > 1:
            findings.append(
                ReportFinding(
                    code="path-covered-twice",
                    file=doc_paths[0],
                    message=f"{path} is covered more than once: {', '.join(doc_paths)}",
                )
            )

    companion_candidates = {
        companion
        for doc in procedures
        for companion in extract_companion_files(doc.text)
    }
    for companion in sorted(companion_candidates):
        # Exclude the companion's own row: a companion legitimately lists its
        # own path in its own `Related Tests` cell (the canonical "itself"
        # pattern), and SKILL.md requires only "exactly one *other* row" to name
        # it. Counting the self-reference would flag every valid single-target
        # companion as multi-row.
        named_in = [
            path
            for path, tests_cell in rows
            if path != companion and companion in _BACKTICK_PATH_RE.findall(tests_cell)
        ]
        if len(named_in) > 1:
            findings.append(
                ReportFinding(
                    code="companion-multi-row",
                    file=plan_rel,
                    message=f"companion {companion} is named in Related Tests of "
                    f"{len(named_in)} rows: {', '.join(named_in)}",
                )
            )
    return findings


def collect_findings(
    documents: list[WorkItemDocument], age_threshold_days: int
) -> list[ReportFinding]:
    """Run all report categories over one shared parsed graph."""
    findings: list[ReportFinding] = []
    findings.extend(find_parse_errors(documents))
    findings.extend(find_missing_source_files(documents))
    findings.extend(find_no_plan_yet(documents, age_threshold_days))
    findings.extend(find_no_procedure_yet(documents, age_threshold_days))
    findings.extend(find_stale_targets(documents))
    findings.extend(find_target_file_mismatches(documents))
    return findings


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only cross-check of Traceability sections across issues/, "
            "plans/, and implementations/ (including done/ subdirectories). "
            "Reports missing-source-file, no-plan-yet, no-procedure-yet, "
            "stale-target-heuristic, and target-file-mismatch findings."
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
    add_format_argument(parser, choices=("json", "csv"), default=None)
    parser.add_argument(
        "--active-only",
        action="store_true",
        help=(
            "Report only findings for documents outside done/ subdirectories. "
            "Archived work items are still read as reference targets, but their "
            "historical findings (legacy formats, since-moved paths) are not "
            "reported or gating."
        ),
    )
    parser.add_argument(
        "--plan-coverage",
        metavar="PLAN",
        default=None,
        help=(
            "Opt-in mode: check that every Implementation Target Files row of "
            "PLAN is covered exactly once by a procedure document (as its "
            "target or a companion test file); only coverage findings are "
            "produced and the exit code is 1 on any finding."
        ),
    )
    return parser


def is_archived_finding(finding: ReportFinding) -> bool:
    """True when the finding's file lives under a `done/` directory."""
    return "done" in Path(finding.file).parts[:-1]


def _print_findings(findings: list[ReportFinding], output_format: str | None) -> None:
    if output_format == "json":
        print(render_json(findings, PROFILE_WORKITEM))
    elif output_format == "csv":
        print(render_csv(findings, PROFILE_WORKITEM), end="")
    else:
        print(render_text(findings), end="")


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    documents = discover_documents()
    if args.plan_coverage is not None:
        plan_path = Path(args.plan_coverage)
        if not _resolve_plan_file(plan_path).is_file():
            parser.error(f"--plan-coverage: no such plan file: {args.plan_coverage}")
        coverage = find_plan_coverage_findings(plan_path, documents)
        _print_findings(coverage, args.format)
        return 1 if coverage else 0

    findings = collect_findings(documents, args.age_threshold_days)
    if args.active_only:
        findings = [f for f in findings if not is_archived_finding(f)]

    _print_findings(findings, args.format)

    gating_categories = {"missing-source-file", "target-file-mismatch"}
    has_gating_finding = any(f.code in gating_categories for f in findings)
    return 1 if has_gating_finding else 0


if __name__ == "__main__":
    sys.exit(main())
