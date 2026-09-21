#!/usr/bin/env python3
"""check_docs_content_policy.py — Scan docs/*.md for implementation-detail content.

`skills/DESIGN.md`'s "Docs content policy — remove" names five categories of
implementation-detail content a `docs/*.md` document should not contain: full
file trees, per-file descriptions embedded in a tree or table, class/function/
method index tables, implementation-location mappings, and literal port
numbers. This is a report-only (Warning) check — it never blocks CI; see
`docs/00_governance_04_documentation-checks.md`'s Governance Verification
Matrix for its registered entry.

Scans the full `docs/` tree recursively (including `docs/adr/`,
`docs/databases/`, etc.) — deliberately does not reuse
`tools/_docs_consistency_lib.py`'s `discover_md_files()`, which globs
non-recursively and requires a domain `prefix`.

Usage:
    python tools/check_docs_content_policy.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import Issue, report_and_exit

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

_TREE_CHARS_RE = re.compile(r"[├│└]")
_FILE_TREE_HEADING_RE = re.compile(
    r"^#{1,6}\s+(?:file\s+structure|directory|file\s+tree)\b",
    re.IGNORECASE,
)
_HEADINGS_WINDOW = 10
_INLINE_COMMENT_DESCRIPTION_RE = re.compile(r"[├│└].*#\s*\S")
_TABLE_DESCRIPTION_RE = re.compile(r"^\s*\|.*\|.*\|.*\|\s*$")
_INDEX_TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*(?:Function|Method|Class)\s*\|.*\|\s*(?:Signature|Description)\s*\|",
    re.IGNORECASE,
)
_LOCATION_MAPPING_RE = re.compile(
    r"\b(?:moved|implemented|handled)\s+by\s+`?[\w./-]+\.py`?", re.IGNORECASE
)
_PORT_NUMBER_RE = re.compile(r"\bPort\s+\d{2,5}\b", re.IGNORECASE)
_ILLUSTRATIVE_MARKERS = frozenset(
    {"illustrative", "worked example", "for example", "e.g."}
)
_DEFAULT_VALUE_RE = re.compile(
    r"`[\w.]+`\s+defaults?\s+to\s+`?[\w.\"']+`?", re.IGNORECASE
)
_RATIONALE_MARKERS = frozenset(
    {
        "because",
        "since",
        "in order to",
        "so that",
        "rationale",
        "to avoid",
        "to ensure",
        "fail-safe",
        "fail-closed",
        "fail-open",
    }
)
_FIELD_TYPE_TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*(?:Field|Key)\s*\|.*\|\s*(?:Type|Default)\s*\|", re.IGNORECASE
)
_MIN_MECHANICAL_TABLE_ROWS = 4
_CONFIG_BULLET_RE = re.compile(r"^\s*-\s+`\w+`\s+—")
_CONFIG_HEADING_RE = re.compile(
    r"^#{1,6}\s+(?:Configuration\s+Fields|Config(?:uration)?\s+Reference)\b",
    re.IGNORECASE,
)
_CLI_HEADING_RE = re.compile(r"^#{1,6}\s+(?:CLI|Commands?|Usage)\b", re.IGNORECASE)
_MIN_CLI_BLOCKS = 3
_SETUP_HEADING_RE = re.compile(
    r"^#{1,6}\s+(?:Setup|Installation|Getting\s+Started|Environment)\b",
    re.IGNORECASE,
)
_ORDERED_LIST_ITEM_RE = re.compile(r"^\s*\d+\.\s+\S")
_MIN_SETUP_STEPS = 3
_DDL_STATEMENT_RE = re.compile(r"\bCREATE\s+(?:TABLE|INDEX)\b", re.IGNORECASE)
_TYPED_DICT_TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*(?:TypedDict|DTO)\s*\|", re.IGNORECASE
)
_CLI_ARG_TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*(?:Argument|Parameter|Option|Flag)\s*\|", re.IGNORECASE
)
_CLI_ARG_HEADING_RE = re.compile(
    r"^#{1,6}\s+(?:[\d.]+\s+)?(?:CLI|Arguments?|Options?)\b", re.IGNORECASE
)
_ERROR_HEADING_RE = re.compile(
    r"^#{1,6}\s+(?:[\d.]+\s+)?(?:Error|Exception|Error\s+Handling)\b", re.IGNORECASE
)
_SECTION_BOUNDARY_HEADING_RE = re.compile(r"^#{1,6}\s+")
_ERROR_ACTION_TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*(?:Case|Scenario)\s*\|(?:.*\|)?\s*Action\s*\|", re.IGNORECASE
)
_TABLE_SEPARATOR_ROW_RE = re.compile(r"^\s*\|[\s:|-]*\|\s*$")
_MIN_JSON_EXAMPLE_LINES = 15
_CODE_FALLBACK_TABLE_HEADER_RE = re.compile(
    r"^\s*\|.*\b(?:Code\s+Fallback|Fallback\s+Value)\b.*\|.*"
    r"\b(?:Production|Operational)\s+Value\b",
    re.IGNORECASE,
)
_CODE_FALLBACK_PHRASE_RE = re.compile(
    r"\b(?:code\s+default|code\s+fallback)\b.*\b(?:operational|production)\b"
    r"|\b(?:operational|production)\b.*\b(?:code\s+default|code\s+fallback)\b",
    re.IGNORECASE,
)


def _is_guard_start(line: str) -> bool:
    """Return True if *line* opens an auto-generated guarded block.

    Recognizes any line starting with `<!-- AUTO-GENERATED` — not only the
    exact bare `<!-- AUTO-GENERATED -->` string — so the real guard-comment
    format `tools/generate_reference_table.py` emits (e.g. `<!--
    AUTO-GENERATED: gen_mcp_reference.py port-tool-reference -->`) is
    recognized.
    """
    return line.strip().startswith("<!-- AUTO-GENERATED")


def _is_guard_end(line: str) -> bool:
    """Return True if *line* closes an auto-generated guarded block."""
    return line.strip().startswith("<!-- END AUTO-GENERATED")


@dataclass(frozen=True)
class DocFile:
    """A single documentation file with its contents."""

    path: Path
    rel_path: str  # relative to docs/
    lines: list[str] = field(default_factory=list)


def discover_all_md_files(docs_dir: Path) -> list[DocFile]:
    """Return every `.md` file under *docs_dir*, recursively, sorted for determinism."""
    result: list[DocFile] = []
    for p in sorted(docs_dir.rglob("*.md")):
        rel = str(p.relative_to(docs_dir))
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        result.append(DocFile(path=p, rel_path=rel, lines=lines))
    return result


def check_full_file_tree(files: list[DocFile]) -> list[Issue]:
    """Flag lines containing ASCII tree-drawing characters inside a true file-tree section.

    A true file-tree section is identified by a nearby heading matching
    'File Structure', 'Directory', or 'File Tree' (case-insensitive).
    Box-drawing characters outside such sections (e.g. state-transition diagrams)
    are not flagged.
    """
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if not _TREE_CHARS_RE.search(line):
                continue
            # Check for a file-tree heading within the last HEADINGS_WINDOW lines.
            has_file_tree_heading = False
            for j in range(max(0, i - _HEADINGS_WINDOW), i):
                candidate = doc.lines[j]
                if _FILE_TREE_HEADING_RE.search(candidate):
                    has_file_tree_heading = True
                    break
            if not has_file_tree_heading:
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="WARNING",
                    message=(
                        "full file tree: line contains ASCII tree-drawing "
                        "characters (├/│/└) inside a file-tree section — see "
                        "skills/DESIGN.md Docs content policy — remove"
                    ),
                )
            )
    return issues


def check_per_file_description(files: list[DocFile]) -> list[Issue]:
    """Flag a tree line carrying an inline `#`-style per-file description."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, 1):
            if _INLINE_COMMENT_DESCRIPTION_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "per-file one-line description embedded in a tree — "
                            "see skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
    return issues


def check_index_table(files: list[DocFile]) -> list[Issue]:
    """Flag a Markdown table header naming a Function/Method/Class + Signature/Description."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if _INDEX_TABLE_HEADER_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "class/function/method index table header — see "
                            "skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
    return issues


def check_location_mapping(files: list[DocFile]) -> list[Issue]:
    """Flag an inline statement naming which `.py` file implements a behavior."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if _LOCATION_MAPPING_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "implementation-location mapping — see "
                            "skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
    return issues


def check_literal_port_number(files: list[DocFile]) -> list[Issue]:
    """Flag a literal port number, unless the line is explicitly labeled illustrative or inside an auto-generated block."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if not _PORT_NUMBER_RE.search(line):
                continue
            lowered = line.lower()
            if any(marker in lowered for marker in _ILLUSTRATIVE_MARKERS):
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="WARNING",
                    message=(
                        "literal port number — see skills/DESIGN.md Docs "
                        "content policy — remove"
                    ),
                )
            )
    return issues


def check_default_value_restatement(files: list[DocFile]) -> list[Issue]:
    """Flag a default-value restatement outside a table row (e.g. "`x` defaults to `y`").

    Conservative: skips a line carrying a rationale marker (e.g. "because"),
    since explaining *why* a default was chosen is retain-category content,
    not a mechanical restatement — see `docs/00_governance_02_documentation-metadata.md`'s
    Guidelines.
    """
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if line.lstrip().startswith("|"):
                continue
            if not _DEFAULT_VALUE_RE.search(line):
                continue
            lowered = line.lower()
            if any(marker in lowered for marker in _RATIONALE_MARKERS):
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="WARNING",
                    message=(
                        "default-value restatement outside a table — see "
                        "skills/DESIGN.md Docs content policy — remove"
                    ),
                )
            )
    return issues


def check_field_type_table(files: list[DocFile]) -> list[Issue]:
    """Flag a plain field/type/default table not caught by `check_index_table`'s
    narrower Function/Method/Class-specific header regex.

    Conservative: only flags a table with at least `_MIN_MECHANICAL_TABLE_ROWS`
    data rows, so a legitimately short, non-mechanical table is not flagged.
    """
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        i = 1
        n = len(doc.lines)
        while i <= n:
            line = doc.lines[i - 1]
            if _is_guard_start(line):
                in_auto_generated = True
                i += 1
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                i += 1
                continue
            if in_auto_generated:
                i += 1
                continue
            if not _FIELD_TYPE_TABLE_HEADER_RE.search(line):
                i += 1
                continue
            header_line_no = i
            j = i + 1
            data_rows = 0
            while j <= n and doc.lines[j - 1].lstrip().startswith("|"):
                if not re.match(r"^\s*\|[\s:|-]*\|\s*$", doc.lines[j - 1]):
                    data_rows += 1
                j += 1
            if data_rows >= _MIN_MECHANICAL_TABLE_ROWS - 1:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=header_line_no,
                        severity="WARNING",
                        message=(
                            "plain field/type/default table header — see "
                            "skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
            i = j
    return issues


def check_config_file_inventory_table(files: list[DocFile]) -> list[Issue]:
    """Flag a config-field bullet list near a "Configuration Fields"/"Config
    Reference" heading (the config-file inventory correspondence pattern)."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if not _CONFIG_BULLET_RE.match(line):
                continue
            has_config_heading = False
            for j in range(i - 1, max(0, i - _HEADINGS_WINDOW) - 1, -1):
                if _CONFIG_HEADING_RE.search(doc.lines[j]):
                    has_config_heading = True
                    break
                if _SECTION_BOUNDARY_HEADING_RE.search(doc.lines[j]):
                    break
            if not has_config_heading:
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="WARNING",
                    message=(
                        "config-file inventory correspondence entry — see "
                        "skills/DESIGN.md Docs content policy — remove"
                    ),
                )
            )
    return issues


def check_cli_command_enumeration(files: list[DocFile]) -> list[Issue]:
    """Flag 3+ fenced `bash` blocks under a CLI/Commands/Usage heading (a CLI-command
    enumeration), not a single illustrative command example."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        section_active = False
        block_starts: list[int] = []
        in_block = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if line.startswith("#"):
                if section_active and len(block_starts) >= _MIN_CLI_BLOCKS:
                    for start in block_starts:
                        issues.append(
                            Issue(
                                file=doc.rel_path,
                                line_no=start,
                                severity="WARNING",
                                message=(
                                    "CLI-command enumeration — see "
                                    "skills/DESIGN.md Docs content policy — remove"
                                ),
                            )
                        )
                section_active = bool(_CLI_HEADING_RE.match(line))
                block_starts = []
                in_block = False
                continue
            if section_active:
                stripped = line.strip()
                if stripped.startswith("```bash"):
                    in_block = True
                    block_starts.append(i)
                elif in_block and stripped == "```":
                    in_block = False
        if section_active and len(block_starts) >= _MIN_CLI_BLOCKS:
            for start in block_starts:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=start,
                        severity="WARNING",
                        message=(
                            "CLI-command enumeration — see skills/DESIGN.md "
                            "Docs content policy — remove"
                        ),
                    )
                )
    return issues


def check_environment_setup_sequence(files: list[DocFile]) -> list[Issue]:
    """Flag a 3+ item ordered list under a Setup/Installation/Getting Started/
    Environment heading (an environment-setup command sequence)."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        section_active = False
        step_lines: list[int] = []
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if line.startswith("#"):
                if section_active and len(step_lines) >= _MIN_SETUP_STEPS:
                    for start in step_lines:
                        issues.append(
                            Issue(
                                file=doc.rel_path,
                                line_no=start,
                                severity="WARNING",
                                message=(
                                    "environment-setup command sequence — see "
                                    "skills/DESIGN.md Docs content policy — remove"
                                ),
                            )
                        )
                section_active = bool(_SETUP_HEADING_RE.match(line))
                step_lines = []
                continue
            if section_active and _ORDERED_LIST_ITEM_RE.match(line):
                step_lines.append(i)
        if section_active and len(step_lines) >= _MIN_SETUP_STEPS:
            for start in step_lines:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=start,
                        severity="WARNING",
                        message=(
                            "environment-setup command sequence — see "
                            "skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
    return issues


def check_ddl_schema_block(files: list[DocFile]) -> list[Issue]:
    """Flag a `sql` fenced block containing a `CREATE TABLE`/`CREATE INDEX`
    statement (a DDL/schema block restated in prose), corpus-wide."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        in_sql_block = False
        block_start = 0
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            stripped = line.strip()
            if stripped.startswith("```sql"):
                in_sql_block = True
                block_start = i
                continue
            if in_sql_block and stripped == "```":
                in_sql_block = False
                continue
            if in_sql_block and _DDL_STATEMENT_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=block_start,
                        severity="WARNING",
                        message=(
                            "DDL/schema block restated in prose — see "
                            "skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
                in_sql_block = False
    return issues


def check_typed_dict_table(files: list[DocFile]) -> list[Issue]:
    """Flag a table header labeled TypedDict/DTO (e.g. `| TypedDict | Purpose |`).

    Unconditional on match, like `check_index_table` — a TypedDict/DTO-labeled
    header is specific enough that no minimum-row threshold is needed.
    """
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if _TYPED_DICT_TABLE_HEADER_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "TypedDict/DTO field table header — see "
                            "skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
    return issues


def check_cli_argument_table(files: list[DocFile]) -> list[Issue]:
    """Flag a Markdown table (not a bash-block enumeration) under a CLI/Arguments/
    Options heading, with a header column named Argument/Parameter/Option/Flag."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if not _CLI_ARG_TABLE_HEADER_RE.search(line):
                continue
            has_cli_heading = False
            for j in range(max(0, i - _HEADINGS_WINDOW), i):
                if _CLI_ARG_HEADING_RE.search(doc.lines[j]):
                    has_cli_heading = True
                    break
            if not has_cli_heading:
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="WARNING",
                    message=(
                        "CLI argument table — see skills/DESIGN.md "
                        "Docs content policy — remove"
                    ),
                )
            )
    return issues


def check_error_handling_table(files: list[DocFile]) -> list[Issue]:
    """Flag a table under an Error/Exception/Error Handling heading, or a table
    with a Case/Scenario + Action-shaped header, independent of a nearby heading.

    Flags only the table's header row (identified by the next line being a
    Markdown table separator row), not every data row of a matching table.
    """
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        n = len(doc.lines)
        for idx in range(n):
            i = idx + 1
            line = doc.lines[idx]
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if _ERROR_ACTION_TABLE_HEADER_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "error-handling table — see skills/DESIGN.md "
                            "Docs content policy — remove"
                        ),
                    )
                )
                continue
            if not line.lstrip().startswith("|"):
                continue
            if idx + 1 >= n or not _TABLE_SEPARATOR_ROW_RE.match(doc.lines[idx + 1]):
                continue
            has_error_heading = False
            for j in range(idx - 1, max(0, i - _HEADINGS_WINDOW) - 1, -1):
                if _ERROR_HEADING_RE.search(doc.lines[j]):
                    has_error_heading = True
                    break
                if _SECTION_BOUNDARY_HEADING_RE.search(doc.lines[j]):
                    break
            if not has_error_heading:
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="WARNING",
                    message=(
                        "error-handling table — see skills/DESIGN.md "
                        "Docs content policy — remove"
                    ),
                )
            )
    return issues


def check_full_json_example(files: list[DocFile]) -> list[Issue]:
    """Flag a fenced JSON code block at or above `_MIN_JSON_EXAMPLE_LINES` lines."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        in_json_block = False
        block_start = 0
        block_lines = 0
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            stripped = line.strip()
            if stripped.startswith("```json"):
                in_json_block = True
                block_start = i
                block_lines = 0
                continue
            if in_json_block and stripped == "```":
                if block_lines >= _MIN_JSON_EXAMPLE_LINES:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=block_start,
                            severity="WARNING",
                            message=(
                                "full JSON payload example — see "
                                "skills/DESIGN.md Docs content policy — remove"
                            ),
                        )
                    )
                in_json_block = False
                continue
            if in_json_block:
                block_lines += 1
    return issues


def check_code_fallback_value_comparison(files: list[DocFile]) -> list[Issue]:
    """Flag a table header or prose/cell line stating both a code-level
    default/fallback value and a separate operational/production value for
    the same parameter — a comparison that duplicates config already
    canonically documented in a configuration-reference doc, and risks the
    same staleness already observed once in this corpus (see
    skills/DESIGN.md "No concrete configuration values").

    Two independent detection paths: a header-shaped table (dedicated
    Code-Fallback/Production-Value columns) and a phrase-shaped line (a
    code-default/fallback phrase and an operational/production phrase
    together, in either order). If a line matches the header-shaped path,
    the phrase-shaped path is skipped for that same line to avoid
    double-reporting.

    Known, accepted false positive: a canonical configuration-reference
    doc that legitimately states this same comparison as part of its own
    role is not exempted here — no check in this tool uses a
    filename-based exemption; see this repository's Plan history for the
    accepted-outcome rationale (the same precedent already applies to
    check_error_handling_table's unexempted canonical-doc finding).
    """
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if _CODE_FALLBACK_TABLE_HEADER_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "code-fallback-vs-operational-value comparison — "
                            "see skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
                continue
            if _CODE_FALLBACK_PHRASE_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "code-fallback-vs-operational-value comparison — "
                            "see skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
    return issues


def main() -> int:
    files = discover_all_md_files(DOCS_DIR)

    all_issues: list[Issue] = []
    all_issues += check_full_file_tree(files)
    all_issues += check_per_file_description(files)
    all_issues += check_index_table(files)
    all_issues += check_location_mapping(files)
    all_issues += check_literal_port_number(files)
    all_issues += check_default_value_restatement(files)
    all_issues += check_field_type_table(files)
    all_issues += check_config_file_inventory_table(files)
    all_issues += check_cli_command_enumeration(files)
    all_issues += check_environment_setup_sequence(files)
    all_issues += check_ddl_schema_block(files)
    all_issues += check_typed_dict_table(files)
    all_issues += check_cli_argument_table(files)
    all_issues += check_error_handling_table(files)
    all_issues += check_full_json_example(files)
    all_issues += check_code_fallback_value_comparison(files)

    return report_and_exit(all_issues)


if __name__ == "__main__":
    raise SystemExit(main())
