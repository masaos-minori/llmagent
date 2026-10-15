#!/usr/bin/env python3
"""check_adr_preservation.py — Compare ADR files against a Git base to prove a size reduction kept their content.

A lightweight-ADR change (removing duplicated wording) must not alter an ADR's
decisions, invariants, exceptions, references, or approval evidence. This check
compares each changed `docs/10_adr/*.md` file with its version at a Git ref
(default `HEAD`) and reports:

ERROR (exit 1):
  - front matter differs
  - the H2 heading sequence differs
  - an `INV-NN` invariant is missing, added, or reworded
  - a Related ADR item, Implementation Reference item, or backtick-quoted
    `path.py::test` citation was removed or added
  - the `## Known Deviations` or `## Approval` section text differs

WARNING (exit 0, requires a sentence-level mapping in the change report):
  - the `## Decision`, `## Failure Policy`, `## Data Ownership and Persistence`,
    or `## Invariants` section text differs
  - the count of an uppercase normative keyword (MUST NOT, MUST, SHOULD, MAY)
    decreased

Non-ADR documents (for example `docs/24_eventbus/*.md`) are compared with a
generic rule set instead:

ERROR: front matter differs, an `AUTO-GENERATED` block was edited or removed, or a
fenced code block is unbalanced.
WARNING: the H2 heading sequence differs; an HTTP `METHOD /path` pair, an HTTP
status code, or a backtick-quoted path/symbol that appeared before no longer
appears anywhere in the compared set of files (so content moved between the
compared files is not reported); a normative keyword count decreased.

It always prints the before/after byte and character counts. Token counts are not
computed (no tokenizer is bundled); report them as unmeasured.

Usage:
    python tools/check_adr_preservation.py                 # changed ADRs vs HEAD
    python tools/check_adr_preservation.py --base <ref>    # compare against another ref
    python tools/check_adr_preservation.py docs/10_adr/adr_02_008_sqlite-4db-separation.md
    python tools/check_adr_preservation.py --dir docs/24_eventbus
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 — git is a trusted local CLI, argv is a fixed list
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import Issue, report_and_exit

REPO_ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = REPO_ROOT / "docs" / "10_adr"

_H2_RE = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
_INV_RE = re.compile(r"^- (INV-\d+): (.+)$", re.MULTILINE)
_TEST_REF_RE = re.compile(r"`([^`\s]+\.py::[^`\s]+)`")
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_NORMATIVE_RES = {
    "MUST NOT": re.compile(r"\bMUST NOT\b"),
    "MUST": re.compile(r"\bMUST\b(?! NOT)"),
    "SHOULD": re.compile(r"\bSHOULD\b"),
    "MAY": re.compile(r"\bMAY\b"),
}
_ERROR_SECTIONS = ("Known Deviations", "Approval")
_WARNING_SECTIONS = (
    "Decision",
    "Failure Policy",
    "Data Ownership and Persistence",
    "Invariants",
)


@dataclass(frozen=True)
class Sizes:
    """Byte and character counts of one file version."""

    bytes_: int
    chars: int


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_front_matter(text: str) -> tuple[str, str]:
    """Return (front matter block, body) for a document starting with `---`."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[: end + 4], text[end + 4 :]


def sections(body: str) -> dict[str, str]:
    """Map each H2 heading to its normalized body text (up to the next H2)."""
    matches = list(_H2_RE.finditer(body))
    result: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        result[m.group(1)] = _norm(body[m.end() : end])
    return result


def h2_sequence(body: str) -> list[str]:
    return [m.group(1) for m in _H2_RE.finditer(body)]


def invariants(body: str) -> dict[str, str]:
    return {m.group(1): _norm(m.group(2)) for m in _INV_RE.finditer(body)}


def _list_items(section_text: str) -> set[str]:
    return {_norm(i) for i in re.split(r"\s-\s", " " + section_text) if i.strip()}


def compare(name: str, old: str, new: str) -> list[Issue]:
    """Return the preservation issues between two versions of one ADR."""
    issues: list[Issue] = []

    def add(sev: str, msg: str) -> None:
        issues.append(Issue(file=name, line_no=0, severity=sev, message=msg))

    old_fm, old_body = split_front_matter(old)
    new_fm, new_body = split_front_matter(new)
    if old_fm != new_fm:
        add("ERROR", "front matter changed")
    if h2_sequence(old_body) != h2_sequence(new_body):
        add("ERROR", "H2 heading sequence changed")

    old_inv, new_inv = invariants(old_body), invariants(new_body)
    for inv_id in sorted(old_inv.keys() - new_inv.keys()):
        add("ERROR", f"{inv_id} removed")
    for inv_id in sorted(new_inv.keys() - old_inv.keys()):
        add("ERROR", f"{inv_id} added")
    for inv_id in sorted(old_inv.keys() & new_inv.keys()):
        if old_inv[inv_id] != new_inv[inv_id]:
            add("ERROR", f"{inv_id} text changed")

    old_sec, new_sec = sections(old_body), sections(new_body)
    for title in ("Related ADRs", "Implementation References"):
        before = _list_items(old_sec.get(title, ""))
        after = _list_items(new_sec.get(title, ""))
        for item in sorted(before - after):
            add("ERROR", f"{title}: removed or changed item: {item}")
        for item in sorted(after - before):
            add("ERROR", f"{title}: added or changed item: {item}")

    old_tests = set(_TEST_REF_RE.findall(old_body))
    new_tests = set(_TEST_REF_RE.findall(new_body))
    for ref in sorted(old_tests - new_tests):
        add("ERROR", f"test citation removed: {ref}")
    for ref in sorted(new_tests - old_tests):
        add("ERROR", f"test citation added: {ref}")

    for title in _ERROR_SECTIONS:
        if old_sec.get(title) != new_sec.get(title):
            add("ERROR", f"section '{title}' text changed")
    for title in _WARNING_SECTIONS:
        if old_sec.get(title) != new_sec.get(title):
            add(
                "WARNING",
                f"section '{title}' text changed; provide a sentence-level mapping",
            )

    for keyword, pattern in _NORMATIVE_RES.items():
        before_n, after_n = (
            len(pattern.findall(old_body)),
            len(pattern.findall(new_body)),
        )
        if after_n < before_n:
            add("WARNING", f"{keyword} count decreased: {before_n} -> {after_n}")

    old_ticks = set(_BACKTICK_RE.findall(old_body))
    new_ticks = set(_BACKTICK_RE.findall(new_body))
    lost = sorted(t for t in old_ticks - new_ticks if "/" in t or "::" in t)
    for token in lost:
        add("WARNING", f"backtick-quoted path/symbol no longer present: {token}")
    return issues


_ENDPOINT_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/{}.:-]*)")
_STATUS_RE = re.compile(
    r"\b(200|201|202|204|400|401|403|404|409|412|422|429|500|503)\b"
)
_AUTOGEN_RE = re.compile(
    r"(<!--\s*AUTO-GENERATED[^>]*-->)(.*?)(<!--\s*END[^>]*-->)", re.DOTALL
)


def _is_code_token(token: str) -> bool:
    return "/" in token or "::" in token or "(" in token or "_" in token


def tokens(text: str) -> set[str]:
    """Collect endpoint pairs, status codes, and backtick-quoted path/symbol tokens."""
    found = {f"{m} {p}" for m, p in _ENDPOINT_RE.findall(text)}
    found |= {f"status {c}" for c in _STATUS_RE.findall(text)}
    prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    found |= {t for t in _INLINE_CODE_RE.findall(prose) if _is_code_token(t)}
    return found


def compare_generic(name: str, old: str, new: str) -> list[Issue]:
    """Return the per-file preservation issues for a non-ADR document."""
    issues: list[Issue] = []

    def add(sev: str, msg: str) -> None:
        issues.append(Issue(file=name, line_no=0, severity=sev, message=msg))

    old_fm, old_body = split_front_matter(old)
    new_fm, new_body = split_front_matter(new)
    if old_fm != new_fm:
        add("ERROR", "front matter changed")
    if new_body.count("```") % 2:
        add("ERROR", "unbalanced fenced code block")
    if h2_sequence(old_body) != h2_sequence(new_body):
        add("WARNING", "H2 heading sequence changed")
    if _AUTOGEN_RE.findall(old) != _AUTOGEN_RE.findall(new) or old.count(
        "AUTO-GENERATED"
    ) != new.count("AUTO-GENERATED"):
        add("ERROR", "AUTO-GENERATED block changed")
    for keyword, pattern in _NORMATIVE_RES.items():
        before_n, after_n = (
            len(pattern.findall(old_body)),
            len(pattern.findall(new_body)),
        )
        if after_n < before_n:
            add("WARNING", f"{keyword} count decreased: {before_n} -> {after_n}")
    return issues


def _git(*args: str) -> str:
    result = subprocess.run(  # nosec B603 B607 — fixed git argv, no shell, no user-built command
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def changed_docs(base: str, directory: str = "docs/10_adr") -> list[Path]:
    """Return Markdown files under `directory` whose content differs from `base`."""
    out = _git("diff", "--name-only", base, "--", directory)
    return [REPO_ROOT / line for line in out.splitlines() if line.endswith(".md")]


def sizes(text: str) -> Sizes:
    return Sizes(len(text.encode("utf-8")), len(text))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--base", default="HEAD", help="Git ref to compare against")
    parser.add_argument(
        "--dir",
        default="docs/10_adr",
        help="Directory of changed files to compare (default: docs/10_adr)",
    )
    args = parser.parse_args(argv)

    paths = [p.resolve() for p in args.files] or changed_docs(args.base, args.dir)
    if not paths:
        print("No changed ADR files.")
        return 0

    all_issues: list[Issue] = []
    total_before = total_after = 0
    old_tokens: set[str] = set()
    new_tokens: set[str] = set()
    print(f"{'File':<58} {'Before':>8} {'After':>8} {'Reduction':>10}")
    for path in sorted(paths):
        rel = path.relative_to(REPO_ROOT).as_posix()
        old = _git("show", f"{args.base}:{rel}")
        new = path.read_text(encoding="utf-8")
        before, after = sizes(old), sizes(new)
        total_before += before.bytes_
        total_after += after.bytes_
        pct = (before.bytes_ - after.bytes_) * 100 / before.bytes_
        print(f"{path.name[:58]:<58} {before.bytes_:>8} {after.bytes_:>8} {pct:>9.1f}%")
        if path.parent == ADR_DIR:
            all_issues.extend(compare(path.name, old, new))
        else:
            all_issues.extend(compare_generic(path.name, old, new))
            old_tokens |= tokens(old)
            new_tokens |= tokens(new)
    for token in sorted(old_tokens - new_tokens):
        all_issues.append(
            Issue(
                file="(compared set)",
                line_no=0,
                severity="WARNING",
                message=f"no longer appears in any compared file: {token}",
            )
        )
    if total_before:
        pct = (total_before - total_after) * 100 / total_before
        print(f"{'TOTAL':<58} {total_before:>8} {total_after:>8} {pct:>9.1f}%")
    print("Tokens: unmeasured (no tokenizer bundled)\n")
    return report_and_exit(all_issues)


if __name__ == "__main__":
    sys.exit(main())
