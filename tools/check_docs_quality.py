#!/usr/bin/env python3
"""Unified document quality checker — merges check_docs_consistency.py + check_mcp_docs_consistency.py.

Checks are split into two categories:
    Core checks   — domain-independent structural/formatting checks
    Custom rules  — domain-specific pattern checks loaded from config files

Usage:
    python tools/check_docs_quality.py                          # run all core + custom
    python tools/check_docs_quality.py --core-only              # only core checks
    python tools/check_docs_quality.py --custom-only            # only custom rules
    python tools/check_docs_quality.py --skip broken_headings   # skip specific check
    python tools/check_docs_quality.py --only stale_patterns    # only specific check
    python tools/check_docs_quality.py docs/*.md                # check specific files
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
CUSTOM_RULES_FILE = ROOT_DIR / "config" / "doc_quality_rules.json"

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DocFile:
    path: Path
    rel_path: str
    lines: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Issue:
    file: str
    line_no: int
    severity: str
    message: str


def discover_md_files(docs_dir: Path) -> list[DocFile]:
    result: list[DocFile] = []
    for p in sorted(docs_dir.rglob("*.md")):
        rel = str(p.relative_to(docs_dir))
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        result.append(DocFile(path=p, rel_path=rel, lines=lines))
    return result


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_HISTORICAL_MARKERS: frozenset[str] = frozenset(
    {"legacy", "historical", "archive only", "resolved", "was:", "removed"}
)

# Minimum tokenized-word count for a section to be eligible for cross-file
# similarity comparison. Empirically justified: full-corpus review found the
# dominant noise source was templated placeholder bodies (e.g. a "Keywords"
# section containing only "configuration", or an "Operational Notes"/"Known
# Limitations" section containing only "- Unknown") trivially matching any
# other section sharing that single word at 100% Jaccard similarity. Within-
# file comparison is unaffected by this threshold (see check_content_similarity).
_MIN_CROSS_FILE_TOKEN_COUNT = 10

_SENTENCE_BOUNDARY = re.compile(r"[.!?:]")


def _is_historical_context(lines: list[str], line_idx: int) -> bool:
    start = max(0, line_idx - 10)
    for i in range(start, line_idx):
        if any(marker in lines[i].lower() for marker in _HISTORICAL_MARKERS):
            return True
    return False


def _count_table_cols(row: str) -> int:
    # Count pipe characters that are not escaped (preceded by backslash)
    count = 0
    i = 0
    while i < len(row):
        if row[i] == "|" and (i == 0 or row[i - 1] != "\\"):
            count += 1
        i += 1
    return count - 1


def _is_separator_row(row: str) -> bool:
    return bool(re.match(r"^\|[-| :]+\|$", row))


def _find_sentences(line: str) -> list[str]:
    parts = _SENTENCE_BOUNDARY.split(line)
    return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# Content similarity helpers
# ---------------------------------------------------------------------------


def _tokenize_for_similarity(text: str) -> set[str]:
    """Tokenize section body text for Jaccard similarity comparison: strip
    fenced and inline code, then lowercase alphanumeric words."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    words = re.findall(r"[a-z0-9]+", text.lower())
    return set(words)


def _jaccard_similarity_above(
    set_a: set[str], set_b: set[str], *, threshold: float = 0.85
) -> bool:
    """Return True if the two pre-tokenized word sets overlap above threshold."""
    if not set_a or not set_b:
        return False

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    if union == 0:
        return False

    return (intersection / union) >= threshold


def _compute_section_similarity(
    section_a_text: str, section_b_text: str, *, threshold: float = 0.85
) -> bool:
    """Return True if the two section texts overlap above the given threshold."""
    set_a = _tokenize_for_similarity(section_a_text)
    set_b = _tokenize_for_similarity(section_b_text)
    return _jaccard_similarity_above(set_a, set_b, threshold=threshold)


def _extract_sections(content: str) -> list[dict]:
    """Extract sections from markdown content, returning list of dicts with 'heading', 'body', 'line' keys."""
    sections = []
    lines = content.split("\n")
    current_heading = None
    current_body_lines: list[str] = []
    current_line: int | None = None

    for idx, line in enumerate(lines, start=1):
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            if current_heading is not None:
                sections.append(
                    {
                        "heading": current_heading.strip(),
                        "body": "\n".join(current_body_lines).strip(),
                        "line": current_line,
                    }
                )
            current_heading = match.group(2)
            current_line = idx
            current_body_lines = []
        else:
            current_body_lines.append(line)

    if current_heading is not None:
        sections.append(
            {
                "heading": current_heading.strip(),
                "body": "\n".join(current_body_lines).strip(),
                "line": current_line,
            }
        )

    return sections


# ---------------------------------------------------------------------------
# Check registry — both core and custom rules use the same mechanism
# ---------------------------------------------------------------------------

_CORE_CHECKS: dict[str, tuple[str, Callable[[Path, list[DocFile]], list[Issue]]]] = {}
_CUSTOM_RULES: dict[str, Callable[[Path, list[DocFile]], list[Issue]]] = {}


def register_core_check(name: str, description: str):
    def decorator(fn):
        _CORE_CHECKS[name] = (description, fn)
        return fn

    return decorator


# ---------------------------------------------------------------------------
# Core checks — domain-independent structural/formatting checks
# ---------------------------------------------------------------------------


@register_core_check("broken_headings", "Malformed heading markers (# without space)")
def check_broken_headings(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("##"):
                if re.match(r"^#+[^# ]", stripped):
                    issues.append(
                        Issue(
                            doc.rel_path,
                            i,
                            "ERROR",
                            f"'#' without space after heading: '{stripped}'",
                        )
                    )
            elif stripped.startswith("##") and not stripped.startswith("###"):
                if re.match(r"^##[^# ]", stripped):
                    issues.append(
                        Issue(
                            doc.rel_path,
                            i,
                            "ERROR",
                            f"'##' without space after heading: '{stripped}'",
                        )
                    )
            elif stripped.startswith("###") and not stripped.startswith("####"):
                if re.match(r"^###[^# ]", stripped):
                    issues.append(
                        Issue(
                            doc.rel_path,
                            i,
                            "ERROR",
                            f"'###' without space after heading: '{stripped}'",
                        )
                    )
    return issues


@register_core_check(
    "malformed_tables", "Markdown tables with mismatched column counts"
)
def check_malformed_tables(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    issues: list[Issue] = []
    for doc in files:
        in_fenced_block = False
        in_table = False
        header_pending = False
        expected_cols = 0
        pending_header_line = ""
        for i, line in enumerate(doc.lines, 1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fenced_block = not in_fenced_block
                in_table = False
                header_pending = False
                continue
            if in_fenced_block:
                continue
            if stripped.startswith("|"):
                if _is_separator_row(stripped):
                    if header_pending:
                        sep_cols = _count_table_cols(stripped)
                        header_cols = _count_table_cols(pending_header_line)
                        if sep_cols != header_cols:
                            issues.append(
                                Issue(
                                    doc.rel_path,
                                    i,
                                    "ERROR",
                                    f"expected {header_cols} columns, got {sep_cols}",
                                )
                            )
                        in_table = True
                        expected_cols = header_cols
                    header_pending = False
                    continue
                if in_table:
                    cols = _count_table_cols(stripped)
                    if cols != expected_cols:
                        issues.append(
                            Issue(
                                doc.rel_path,
                                i,
                                "ERROR",
                                f"expected {expected_cols} columns, got {cols}",
                            )
                        )
                elif header_pending:
                    # No separator row found — treat first data row as header
                    header_pending = False
                    pending_header_line = stripped
                    expected_cols = _count_table_cols(stripped)
                    in_table = True
                else:
                    # First row without a preceding separator — treat as header
                    header_pending = True
                    pending_header_line = stripped
                    expected_cols = _count_table_cols(stripped)
                    in_table = True
            else:
                in_table = False
                header_pending = False
                expected_cols = 0
    return issues


@register_core_check("unclosed_inline_code", "Odd number of backticks per line")
def check_unclosed_inline_code(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    issues: list[Issue] = []
    for doc in files:
        in_fenced_block = False
        for i, line in enumerate(doc.lines, 1):
            stripped = line.strip()
            inner = re.sub(r"^(>\s*)+", "", stripped)
            if inner.startswith("```") or inner.startswith("~~~"):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block:
                continue
            if re.match(r"^\|[-| ]+\|$", stripped):
                continue
            if "```" in stripped:
                continue
            # Skip lines where backticks appear mid-sentence (likely multi-line inline code)
            # Only flag when backticks are at the start/end of a logical segment
            backtick_count = inner.count("`")
            if backtick_count % 2 != 0:
                # Check if this looks like a continuation line (starts with whitespace or is part of a sentence)
                original_line = doc.lines[i - 1] if i > 0 else ""
                if original_line and original_line.lstrip().startswith(("-", "*", "|")):
                    # List item — likely multi-line content; skip
                    continue
                if any(c.isalpha() for c in inner[: inner.find("`")] if "`" in inner):
                    # Backtick appears after text on same line — likely multi-line
                    continue
                # Also skip if backtick is not at the start of the line (multi-line continuation)
                first_backtick_pos = inner.find("`")
                if first_backtick_pos > 0:
                    # Backtick appears after some text — likely multi-line
                    continue
                # Also skip if previous line ends with a backtick (continuation)
                if original_line.rstrip().endswith("`"):
                    # Previous line ended with backtick — this is a continuation
                    continue
                issues.append(
                    Issue(
                        doc.rel_path,
                        i,
                        "ERROR",
                        f"unclosed inline code: '{stripped[:80]}'",
                    )
                )
    return issues


@register_core_check("json_not_wrapped", "JSON examples not in fenced code blocks")
def check_json_not_wrapped(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    issues: list[Issue] = []
    for doc in files:
        in_fenced_block = False
        for i, line in enumerate(doc.lines, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block:
                continue
            if stripped.startswith("{") and "```" not in stripped:
                issues.append(
                    Issue(
                        doc.rel_path,
                        i,
                        "ERROR",
                        f"JSON example not wrapped in fenced code block: '{stripped[:80]}'",
                    )
                )
    return issues


@register_core_check("stale_patterns", "Stale artifact paths / non-canonical commands")
def check_stale_patterns(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    issues: list[Issue] = []
    # Default stale patterns — can be overridden by custom rules
    default_patterns: dict[str, str] = {}
    for doc in files:
        for i, line in enumerate(doc.lines, 1):
            stripped = line.strip()
            is_historical = any(
                m.lower() in stripped.lower() for m in _HISTORICAL_MARKERS
            )
            for pattern_name, pattern in default_patterns.items():
                if re.search(pattern, stripped) and not is_historical:
                    issues.append(
                        Issue(
                            doc.rel_path,
                            i,
                            "ERROR",
                            f"stale reference: '{pattern_name}'",
                        )
                    )
    return issues


@register_core_check("resolved_in_active", "Resolved items under active sections")
def check_resolved_in_active(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    issues: list[Issue] = []
    for doc in files:
        in_active = False
        for i, line in enumerate(doc.lines, 1):
            stripped = line.strip()
            if stripped.startswith("## Active Issues"):
                in_active = True
                continue
            if stripped.startswith("## ") and not stripped.startswith(
                "## Active Issues"
            ):
                in_active = False
                continue
            if in_active and (
                "[Resolved]" in stripped or "resolved" in stripped.lower()
            ):
                issues.append(
                    Issue(
                        doc.rel_path,
                        i,
                        "ERROR",
                        f"resolved item under active issues: '{stripped[:80]}'",
                    )
                )
    return issues


@register_core_check(
    "duplicate_heading_numbers", "Duplicate numbered headings at same level"
)
def check_duplicate_heading_numbers(
    docs_dir: Path, files: list[DocFile]
) -> list[Issue]:
    issues: list[Issue] = []
    for doc in files:
        in_fenced_block = False
        # Purely-numeric: exact duplicate detection
        numeric_seen: dict[tuple[int, str], int] = {}
        # Alphabetic-suffix: near-duplicate detection (base number matching)
        alpha_groups: dict[tuple[int, int], list[tuple[int, str]]] = {}
        for i, line in enumerate(doc.lines, 1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block:
                continue
            # Purely-numeric pattern: ## 2.1, ## 3.2.1, etc.
            m = re.match(r"^(#{1,6})\s+(\d[\d.]*\.)\s+", stripped)
            if m:
                level = len(m.group(1))
                number = m.group(2)
                key = (level, number)
                if key in numeric_seen:
                    issues.append(
                        Issue(
                            doc.rel_path,
                            i,
                            "ERROR",
                            f"duplicate heading number: '#{level} {number}' also at line {numeric_seen[key]}: '{stripped}'",
                        )
                    )
                else:
                    numeric_seen[key] = i
            # Alphabetic-suffix pattern: ## 2a., ## 7c., etc.
            am = re.match(r"^(#{1,6})\s+(\d+[a-z]+)\.\s+", stripped)
            if am:
                level = len(am.group(1))
                heading_number = am.group(2)
                base_match = re.match(r"(\d+)[a-z]+", heading_number)
                if base_match:
                    base_number = int(base_match.group(1))
                    key = (level, base_number)
                    if key not in alpha_groups:
                        alpha_groups[key] = []
                    alpha_groups[key].append((i, heading_number))
        # Report near-duplicates among alphabetic-suffix headings
        for key, entries in alpha_groups.items():
            if len(entries) > 1:
                for ii in range(len(entries)):
                    for jj in range(ii + 1, len(entries)):
                        _, num_i = entries[ii]
                        _, num_j = entries[jj]
                        if num_i != num_j:
                            issues.append(
                                Issue(
                                    doc.rel_path,
                                    entries[jj][0],
                                    "WARNING",
                                    f"Probable near-duplicate heading: '{num_i}' and '{num_j}' at same level {key[0]}",
                                )
                            )
    return issues


@register_core_check(
    "content_similarity",
    "Sections within the same document with overlapping body text above threshold",
)
def check_content_similarity(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Flag sections within the same document whose body text overlaps above
    threshold. Also flags sections across different documents whose body text
    overlaps above the same threshold (e.g. a governance rule copied
    verbatim into a second document — see
    docs/00_governance_01_documentation-policy.md's 'Merge Conditions' vs.
    docs/00_governance_04_documentation-checks.md's 'Merge Condition
    Validation' for a confirmed real-world example)."""
    issues: list[Issue] = []
    for doc in files:
        try:
            content = doc.path.read_text(encoding="utf-8")
        except OSError:
            continue
        sections = _extract_sections(content)
        for i in range(len(sections)):
            for j in range(i + 1, len(sections)):
                body_a = sections[i]["body"]
                body_b = sections[j]["body"]
                if not body_a or not body_b:
                    continue
                if _compute_section_similarity(body_a, body_b):
                    issues.append(
                        Issue(
                            doc.rel_path,
                            sections[j]["line"],
                            "WARNING",
                            f"Content similarity detected between sections '{sections[i]['heading']}' and '{sections[j]['heading']}'",
                        )
                    )

    # Pre-tokenize each non-empty section exactly once (instead of inside the
    # O(files^2 * sections^2) comparison loop below) — re-tokenizing on every
    # pairwise comparison made a full-corpus run take ~2.5 minutes instead of
    # ~2 seconds; tokenizing once per section and comparing cached word sets
    # keeps the same Jaccard-similarity semantics at a fraction of the cost.
    doc_tokenized_sections: list[tuple[DocFile, list[tuple[dict, set[str]]]]] = []
    for doc in files:
        try:
            content = doc.path.read_text(encoding="utf-8")
        except OSError:
            continue
        sections = _extract_sections(content)
        tokenized = []
        for sec in sections:
            if not sec["body"]:
                continue
            tokens = _tokenize_for_similarity(sec["body"])
            if len(tokens) < _MIN_CROSS_FILE_TOKEN_COUNT:
                continue
            tokenized.append((sec, tokens))
        doc_tokenized_sections.append((doc, tokenized))

    for a in range(len(doc_tokenized_sections)):
        doc_a, sections_a = doc_tokenized_sections[a]
        for b in range(a + 1, len(doc_tokenized_sections)):
            doc_b, sections_b = doc_tokenized_sections[b]
            for sec_a, tokens_a in sections_a:
                for sec_b, tokens_b in sections_b:
                    if _jaccard_similarity_above(tokens_a, tokens_b):
                        issues.append(
                            Issue(
                                doc_b.rel_path,
                                sec_b["line"],
                                "WARNING",
                                f"Content similarity detected between "
                                f"{doc_a.rel_path}#'{sec_a['heading']}' and "
                                f"{doc_b.rel_path}#'{sec_b['heading']}'",
                            )
                        )
    return issues


@register_core_check("migration_notes_in_active", "Migration Notes in active sections")
def check_migration_notes_in_active(
    docs_dir: Path, files: list[DocFile]
) -> list[Issue]:
    issues: list[Issue] = []
    for doc in files:
        in_active = False
        for i, line in enumerate(doc.lines, 1):
            stripped = line.strip()
            if stripped.startswith("##"):
                section_name = stripped.replace("#", "").strip().lower()
                is_historical_section = any(
                    h in section_name for h in ["legacy", "archive", "historical"]
                )
                in_active = not is_historical_section
                if "migration notes" in section_name and not is_historical_section:
                    issues.append(
                        Issue(
                            doc.rel_path,
                            i,
                            "WARNING",
                            f"Migration Notes in active section: '{stripped}'",
                        )
                    )
                continue
            if not in_active:
                continue
    return issues


# ---------------------------------------------------------------------------
# Custom rules — loaded from config JSON
# ---------------------------------------------------------------------------


def load_custom_rules(docs_dir: Path) -> None:
    """Load domain-specific checks from config/doc_quality_rules.json."""
    if not CUSTOM_RULES_FILE.exists():
        return
    try:
        with open(CUSTOM_RULES_FILE) as f:
            rules = json.load(f)
    except (json.JSONDecodeError, OSError):
        return
    for name, rule in rules.get("rules", {}).items():
        pattern_str = rule.get("pattern")
        severity = rule.get("severity", "ERROR")
        description = rule.get("description", "")
        if not pattern_str:
            continue
        compiled = re.compile(pattern_str)

        def make_checker(pat, sev, desc):
            def checker(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
                issues: list[Issue] = []
                for doc in files:
                    for i, line in enumerate(doc.lines, 1):
                        stripped = line.strip()
                        is_historical = any(
                            m.lower() in stripped.lower() for m in _HISTORICAL_MARKERS
                        )
                        # A line pairing the stale form with its current "/session ..."
                        # replacement (e.g. a migration-notes mapping table row) is
                        # documenting the rename, not repeating stale guidance.
                        is_paired_with_replacement = "/session " in stripped
                        if (
                            pat.search(stripped)
                            and not is_historical
                            and not is_paired_with_replacement
                        ):
                            issues.append(
                                Issue(
                                    doc.rel_path, i, sev, f"{desc}: '{stripped[:80]}'"
                                )
                            )
                return issues

            return checker

        _CUSTOM_RULES[name] = make_checker(compiled, severity, description)


# ---------------------------------------------------------------------------
# Main — CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Document quality checker")
    parser.add_argument(
        "files", nargs="*", type=Path, help="Files to check (default: all docs/*.md)"
    )
    parser.add_argument("--core-only", action="store_true", help="Run only core checks")
    parser.add_argument(
        "--custom-only", action="store_true", help="Run only custom rules"
    )
    parser.add_argument("--skip", nargs="+", default=[], help="Check names to skip")
    parser.add_argument(
        "--only", nargs="+", default=[], help="Only run specific checks by name"
    )
    args = parser.parse_args(argv)

    # Discover files
    if args.files:
        files = [
            DocFile(
                path=f,
                rel_path=str(f),
                lines=f.read_text(encoding="utf-8").splitlines(),
            )
            for f in args.files
        ]
    else:
        files = discover_md_files(DOCS_DIR)

    # Load custom rules
    if not args.core_only:
        load_custom_rules(DOCS_DIR)

    # Select checks
    checks_to_run: dict[
        str, tuple[str, Callable[[Path, list[DocFile]], list[Issue]]]
    ] = {}
    if args.core_only or not args.custom_only:
        checks_to_run.update(_CORE_CHECKS)
    if args.custom_only or not args.core_only:
        checks_to_run.update({name: ("", fn) for name, fn in _CUSTOM_RULES.items()})

    # Apply --skip / --only filters
    if args.skip:
        checks_to_run = {k: v for k, v in checks_to_run.items() if k not in args.skip}
    if args.only:
        checks_to_run = {k: v for k, v in checks_to_run.items() if k in args.only}

    # Run checks
    all_issues: list[Issue] = []
    for name, (_, fn) in sorted(checks_to_run.items()):
        issues = fn(DOCS_DIR, files)
        all_issues.extend(issues)

    # Sort and display results
    all_issues.sort(key=lambda x: (x.file, x.line_no))
    errors = sum(1 for i in all_issues if i.severity == "ERROR")
    warnings = sum(1 for i in all_issues if i.severity == "WARNING")

    print(f"\n{'=' * 60}")
    print(f"Document Quality Report — {len(files)} files checked")
    print(f"{'=' * 60}")
    if all_issues:
        print(f"\n{errors} error(s), {warnings} warning(s)\n")
        for issue in all_issues:
            print(f"[{issue.severity}] {issue.file}:{issue.line_no} — {issue.message}")
    else:
        print("\n✓ No issues found.\n")
    print(f"{'=' * 60}\n")
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
