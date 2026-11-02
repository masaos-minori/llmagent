"""tools/stale_detector.py

Lightweight stale detection for implementation procedures.

Before executing a procedure, verify that the code constructs it references
(line numbers, symbol names, import paths) still exist in the current source.
If they do not, mark the procedure as stale and skip execution.

Uses simple regex/string matching against the cited line ranges specified in
the procedure document — avoids AST parsing as specified in the issue.
Any single mismatch constitutes "stale"; the procedure cannot be reliably
executed if even one referenced construct is missing.

An import is recognized only as a statement at the start of a line (after an
optional list marker and backtick); a sentence that merely mentions an import is
not a citation. A symbol or import statement written followed by the marker
(new) is declared by the procedure as something it creates and is not checked.
A target path followed by (new) in the Target file section declares the file as
created by the procedure: the existence check is skipped, the containing directory
must exist, a file that already exists is reported, and line citations that resolve
to that target are skipped.
Names that cannot appear in Python source are not reported as missing symbols:
built-in and dunder names, lint rule codes, sibling-procedure numbers, chapter ids
that prefix a docs file name, and configuration keys in key position (a mention
in a comment is never a key).
A name or import marked (new) by an earlier sibling procedure of the same Plan (same
Traceability Source plan, lower sequence number in the file name) is resolved from
that sibling and reported on its own line instead of as a mismatch.

A document may carry companion test files in a "### Companion test files" section (see
templates/implementation-procedure.md): top-level list items whose first backticked
token is the companion path, optionally followed by (new). The section is removed from
the text checked against the primary target; each companion's block is checked against
its own file (existence, or the (new) rules above), so its line citations, symbols,
imports and "Before:" blocks resolve against the companion. A mismatch found there keeps
its usual detail and ends with " (companion {path})". A document without the section is
checked exactly as before.

Design decisions:
- Report all failures in a single pass; this is simpler and provides more
  information to the operator.
- Any single mismatch constitutes "stale" — the procedure cannot be reliably
  executed if even one referenced construct is missing.
"""

from __future__ import annotations

import builtins
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Regex patterns for extracting cited constructs from procedure documents.

# Line number references: "Line 49", "Lines 15-17", "lines 120-124"
_LINE_REF_RE = re.compile(
    r"(?i)"
    r"(?:line[s]?)\s+"
    r"(\d+)(?:\s*-\s*(\d+))?"
)

# Symbol name references: backtick-quoted identifiers like `_llm_runner`,
# `LLMTurnRunner`, `ToolLoopGuard`, etc.
_SYMBOL_RE = re.compile(r"`([^`\s]+)`")

# Import path references: a statement such as
# "from agent.llm_turn_runner import LLMTurnRunner" that starts a line (after
# indentation, an optional list marker and one optional opening backtick), so a
# sentence that merely mentions an import is not a citation. Groups: module,
# imported names (without a closing backtick) and an optional " (new)" marker.
_IMPORT_RE = re.compile(
    r"(?i)"
    r"(?:^|\n)[ \t]*(?:[-*][ \t]+|\d+\.[ \t]+)?`?"
    r"from\s+(\S+)\s+import\s+(.+?)`?([ \t]*\(new\))?"
    r"(?:\s*$|\s+#)"
)

# Sibling resolution: the Traceability Source plan line, the sequence number in a
# procedure file name ({timestamp}_{seq}_{slug}.md), and the name or import that a
# symbol_missing / import_missing mismatch detail carries.
_SOURCE_PLAN_RE = re.compile(
    r"(?im)^[ \t]*(?:[-*][ \t]+)?\*\*Source plan\*\*:[ \t]*(.+?)[ \t]*$"
)
_SEQ_RE = re.compile(r"^\d{8}-\d{6}_(\d+)_")
_MISSING_NAME_RE = re.compile(r"^Symbol '(.+)' not found in source")
_MISSING_IMPORT_RE = re.compile(r"^Import 'from (\S+) import (.+)' not found in source")

_SIBLING_DIRS = ("implementations", "implementations/done")

# Marker a procedure writes after a backticked name it will create: " (new)".
_NEW_MARKER_RE = re.compile(r" ?\(new\)")


def _is_marked_new(text: str, pos: int) -> bool:
    """True when the text at `pos` starts with the (new) marker (one optional space)."""
    return _NEW_MARKER_RE.match(text, pos) is not None


# Code block content between "# Before:" and "# After:" markers
# Optimized with negated character class to avoid catastrophic backtracking
_BEFORE_AFTER_RE = re.compile(
    r"#\s*Before:\s*\n([^\n]*(?:\n[^\n]*)*?)#\s*After:",
    re.DOTALL,
)

# Target file path references: "`scripts/agent/orchestrator.py`"
_TARGET_FILE_RE = re.compile(r"`(/[^`]+)`")

# Extract target file from the "### Target file" section of the procedure document
_TARGET_FILE_SECTION_RE = re.compile(
    r"###\s*Target\s+file\s*\n\s*`([^`]+)`",
    re.IGNORECASE,
)

# "### Companion test files" section: heading through the line before the next heading
# (or the end of the text). Group 1 is the section body.
_COMPANION_SECTION_RE = re.compile(
    r"^###[ \t]*Companion[ \t]+test[ \t]+files[ \t]*\n(.*?)(?=^#{1,6}[ \t]|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)

# A companion entry: a top-level list item starting with the backticked path.
_COMPANION_BULLET_RE = re.compile(r"^[-*+][ \t]+`([^`\s]+)`", re.MULTILINE)

# Non-symbol allowlist: tokens that look like code but are actually tool vocabulary
_NON_SYMBOL_ALLOWLIST = frozenset(
    {
        # Repository workflow tool vocabulary
        "Edit",
        "Write",
        "Read",
        "Bash",
        "old_string",
        "new_string",
        "replace_all",
        # Common CLI tool names
        "ruff",
        "mypy",
        "pytest",
        "pyright",
        "bandit",
        # Common Markdown front-matter keys
        "title",
        "area",
        "tags",
        "related",
        "source",
        # Workflow status values
        "Pending",
        "In Progress",
        "Blocked",
        "Completed",
    }
)

# Names that cannot appear in a .py file but are cited correctly (see
# _is_non_python_name): dunder names, lint rule codes (RUF100), sibling-procedure
# numbers (_01), and documentation chapter ids (agent_04).
_DUNDER_RE = re.compile(r"__\w+__")
_RULE_CODE_RE = re.compile(r"[A-Z]{1,4}\d{2,4}")
_SIBLING_NUMBER_RE = re.compile(r"_\d+")
_CHAPTER_ID_RE = re.compile(r"[a-z]+(?:_\d+)+")

# Locations whose keys count as existing configuration, and the key positions
# recognized on a non-comment line: an assignment at the start of a line, a
# bracketed table header, a JSON key, and a created table name.
_CONFIG_GLOBS = (
    "config/**/*",
    "conf.d/**/*",
    "schemas/**/*",
    "deploy/**/*",
    "init.d/**/*",
    "pyproject.toml",
    "tox.ini",
)
_CONFIG_ASSIGNMENT_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_]\w*)\s*=")
_CONFIG_TABLE_HEADER_RE = re.compile(r"^\s*\[+([^\]]+)\]+")
_CONFIG_JSON_KEY_RE = re.compile(r'"([A-Za-z_]\w*)"\s*:')
_CONFIG_CREATE_TABLE_RE = re.compile(
    r"(?i)create\s+(?:virtual\s+)?table\s+(?:if\s+not\s+exists\s+)?(\w+)"
)

# A backtick-quoted relative .py/.md path other than a leading-slash absolute one
# (see _TARGET_FILE_RE above), used to scope a nearby symbol/line citation.
# An optional "::Symbol.method()"-style suffix is allowed inside the same
# backtick span (e.g. `rag_pipeline_service.py::RagPipelineMCPService.start()`)
# without being captured as part of the path.
_SCOPED_PATH_RE = re.compile(r"`([\w./-]+\.(?:py|md))(?:::[^`]*)?`")

# Directories to skip when resolving a bare filename citation to a unique
# source file — build artifacts and vendored/virtualenv trees routinely
# contain same-named files that would otherwise make the match ambiguous.
_NOISE_DIR_NAMES = frozenset({".venv", ".tox", ".git", "__pycache__", "node_modules"})

# Start-of-line marker for a numbered ("1. ") or bulleted ("- "/"* ") list item.
# A citation's scoping is bounded by these in addition to blank lines: adjacent
# numbered/bulleted Procedure steps are logically separate citations even
# though Markdown puts no blank line between them.
_LIST_ITEM_BOUNDARY_RE = re.compile(r"\n(?:\d+\.|[-*])\s")


def _citation_bounds(proc_text: str, pos: int) -> tuple[int, int]:
    """Return the (start, end) offsets of the citation unit containing `pos`:
    bounded by the nearest blank line or list-item marker on either side."""
    start = 0
    blank_before = proc_text.rfind("\n\n", 0, pos)
    if blank_before != -1:
        start = max(start, blank_before + 2)
    for m in _LIST_ITEM_BOUNDARY_RE.finditer(proc_text, 0, pos):
        start = max(start, m.end())

    end = len(proc_text)
    blank_after = proc_text.find("\n\n", pos)
    if blank_after != -1:
        end = min(end, blank_after)
    list_after = _LIST_ITEM_BOUNDARY_RE.search(proc_text, pos)
    if list_after is not None:
        end = min(end, list_after.start())
    return start, end


def _find_scoped_path(proc_text: str, pos: int, target_file: str) -> str | None:
    """Return the backtick-quoted .py/.md path (other than target_file) that
    scopes the citation at `pos`, searching the same citation unit (see
    `_citation_bounds`).

    Prefers the nearest *preceding* path; if none precedes the citation,
    falls back to the nearest *following* one in the same unit — a symbol is
    sometimes described with its scoping file named later in the same
    sentence, e.g. "`scripts/rag/`'s `RagPipeline` (confirmed via
    `rag_pipeline_service.py::RagPipelineMCPService.start()`...)"."""
    unit_start, unit_end = _citation_bounds(proc_text, pos)

    paths_before = _SCOPED_PATH_RE.findall(proc_text[unit_start:pos])
    for path in reversed(paths_before):
        if path != target_file:
            return str(path)

    for match in _SCOPED_PATH_RE.finditer(proc_text[pos:unit_end]):
        path = match.group(1)
        if path != target_file:
            return str(path)
    return None


def _load_scoped_source(
    source_dir: Path,
    path: str,
    cache: dict[str, str | None],
) -> str | None:
    """Read `path` relative to source_dir once, memoizing hits and misses.

    Falls back to a repository-wide search by basename when `path` does not
    resolve directly — a citation sometimes names only the file (e.g.
    `rag_pipeline_service.py`), not its full relative path. The fallback is
    used only when it resolves to exactly one candidate outside known noise
    directories (venvs, tox envs, vendored/build trees); an ambiguous or
    absent basename match is treated the same as "not found" rather than
    guessing.
    """
    if path in cache:
        return cache[path]
    candidate = source_dir / path.lstrip("/")
    if not candidate.exists():
        basename = Path(path).name
        candidates = [
            p
            for p in source_dir.rglob(basename)
            if not _NOISE_DIR_NAMES & set(p.relative_to(source_dir).parts[:-1])
        ]
        if len(candidates) == 1:
            candidate = candidates[0]
        else:
            cache[path] = None
            return None
    content = candidate.read_text(encoding="utf-8")
    cache[path] = content
    return content


def _docs_file_names(source_dir: Path) -> set[str]:
    """Base names of the files under the docs directory of `source_dir`."""
    docs = source_dir / "docs"
    if not docs.is_dir():
        return set()
    return {p.name for p in docs.rglob("*") if p.is_file()}


def _configuration_keys(source_dir: Path) -> set[str]:
    """Names in key position in the configuration-like files of `source_dir`.

    Comment lines are skipped, so a setting that is only mentioned in a comment
    (for example one recorded as removed) is not a key.
    """
    keys: set[str] = set()
    for pattern in _CONFIG_GLOBS:
        for path in source_dir.glob(pattern):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for line in text.splitlines():
                if line.lstrip().startswith("#"):
                    continue
                for regex in (
                    _CONFIG_ASSIGNMENT_RE,
                    _CONFIG_JSON_KEY_RE,
                    _CONFIG_CREATE_TABLE_RE,
                ):
                    keys.update(regex.findall(line))
                header = _CONFIG_TABLE_HEADER_RE.match(line)
                if header:
                    keys.update(
                        part.strip("\"' ")
                        for part in re.split(r"[.,\s]+", header.group(1))
                        if part.strip("\"' ")
                    )
    return keys


def _is_non_python_name(
    sym: str,
    source_dir: Path,
    cache: dict[str, set[str]],
) -> bool:
    """True when `sym` is a name that cannot appear in Python source but is a
    legitimate citation: a built-in or dunder name, a lint rule code, a
    sibling-procedure number, a chapter id that prefixes a docs file name, or a
    configuration key. Called only for a symbol already absent from every .py
    file; the docs file names and the keys are read lazily, once, into `cache`.
    """
    if hasattr(builtins, sym) or _DUNDER_RE.fullmatch(sym):
        return True
    if _RULE_CODE_RE.fullmatch(sym) or _SIBLING_NUMBER_RE.fullmatch(sym):
        return True
    if _CHAPTER_ID_RE.fullmatch(sym):
        if "docs" not in cache:
            cache["docs"] = _docs_file_names(source_dir)
        if any(name.startswith((f"{sym}_", f"{sym}.")) for name in cache["docs"]):
            return True
    if "config" not in cache:
        cache["config"] = _configuration_keys(source_dir)
    return sym in cache["config"]


def _symbol_present_somewhere(
    source_dir: Path,
    sym: str,
    cache: dict[str, bool],
) -> bool:
    """Return True if `sym` appears as a whole word in any ``.py`` file under
    `source_dir` outside noise directories. Memoized by symbol.

    Narrow guard against false-positive ``symbol_missing`` findings: an
    unscoped symbol absent from the target/scoped file may still live in a
    different file and only be discussed as a cross-reference, not verified
    against the target. A symbol genuinely absent from every ``.py`` file is
    still reported missing.
    """
    if sym in cache:
        return cache[sym]
    pattern = re.compile(rf"\b{re.escape(sym)}\b")
    found = False
    for py_file in source_dir.rglob("*.py"):
        ancestors = set(py_file.relative_to(source_dir).parts[:-1])
        if ancestors & _NOISE_DIR_NAMES:
            continue
        try:
            if pattern.search(py_file.read_text(encoding="utf-8")):
                found = True
                break
        except (OSError, UnicodeDecodeError):
            continue
    cache[sym] = found
    return found


@dataclass
class StaleResult:
    """Structured result of a stale detection check."""

    is_stale: bool
    target_file: str | None = None
    mismatches: list[dict[str, Any]] = field(default_factory=list)
    resolved: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sibling_rule: str | None = None

    @property
    def summary(self) -> str:
        """Human-readable summary of the stale check result."""
        lines: list[str] = []
        if self.sibling_rule is not None:
            lines.append(f"Sibling resolution: order rule = {self.sibling_rule}")
            for r in self.resolved:
                lines.append(
                    f"resolved from sibling: {r['name']} declared (new) in {r['document']}"
                )
            lines.extend(f"warning: {w}" for w in self.warnings)
        if not self.is_stale:
            lines.append("Procedure is not stale — all referenced constructs found.")
        else:
            lines.append(f"Stale: {len(self.mismatches)} mismatch(es) detected.")
            for m in self.mismatches:
                lines.append(f"  - {m['type']}: {m['detail']}")
        return "\n".join(lines)

    @property
    def abort_execution(self) -> bool:
        """Whether execution should be aborted based on this result."""
        return self.is_stale

    def add_mismatch(self, mismatch_type: str, detail: str) -> None:
        """Record a single mismatch finding."""
        self.mismatches.append({"type": mismatch_type, "detail": detail})
        self.is_stale = True

    def merge(self, other: StaleResult) -> None:
        """Merge another StaleResult into this one."""
        if other.is_stale:
            self.is_stale = True
            self.mismatches.extend(other.mismatches)
        self.resolved.extend(other.resolved)
        self.warnings.extend(other.warnings)
        if other.target_file and not self.target_file:
            self.target_file = other.target_file

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON/logging."""
        return {
            "is_stale": self.is_stale,
            "target_file": self.target_file,
            "mismatches": self.mismatches,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StaleResult:
        """Deserialize from dictionary."""
        result = cls(is_stale=d.get("is_stale", False))
        result.target_file = d.get("target_file")
        result.mismatches = d.get("mismatches", [])
        return result

    @classmethod
    def clean(cls) -> StaleResult:
        """Return a clean (non-stale) result."""
        return cls(is_stale=False)

    @classmethod
    def stale(cls, target_file: str | None = None) -> StaleResult:
        """Return a stale result with optional target file."""
        return cls(is_stale=True, target_file=target_file)

    @classmethod
    def with_mismatch(
        cls,
        mismatch_type: str,
        detail: str,
        target_file: str | None = None,
    ) -> StaleResult:
        """Return a stale result with a specific mismatch."""
        result = cls(is_stale=True, target_file=target_file)
        result.add_mismatch(mismatch_type, detail)
        return result

    @classmethod
    def with_mismatches(
        cls,
        mismatches: list[tuple[str, str]],
        target_file: str | None = None,
    ) -> StaleResult:
        """Return a stale result with multiple mismatches."""
        result = cls(is_stale=True, target_file=target_file)
        for mt, detail in mismatches:
            result.add_mismatch(mt, detail)
        return result

    @classmethod
    def empty(cls) -> StaleResult:
        """Return an empty (clean) result."""
        return cls(is_stale=False)

    @classmethod
    def from_procedure(
        cls,
        proc_path: str | Path,
        source_dir: str | Path | None = None,
        *,
        sibling_mode: str = "earlier",
    ) -> StaleResult:
        """Run stale detection on a procedure document.

        Args:
            proc_path: Path to the implementation procedure document.
            source_dir: Directory containing the source files referenced by
                the procedure. Defaults to the repository root.
            sibling_mode: How a name marked (new) by a sibling procedure of the
                same Plan is treated: "earlier" (only a lower sequence number
                declares), "any", or "off" (no sibling pass).

        Returns:
            StaleResult with the detection outcome.
        """
        proc_path = Path(proc_path)
        if not proc_path.exists():
            return cls.with_mismatch(
                "file_not_found",
                f"Procedure file not found: {proc_path}",
            )

        text = proc_path.read_text(encoding="utf-8")
        result = cls.clean()

        # Extract target file path from the "### Target file" section
        target_match = _TARGET_FILE_SECTION_RE.search(text)
        declared_new = False
        if target_match:
            result.target_file = target_match.group(1)
            declared_new = _is_marked_new(text, target_match.end())
        else:
            # Fallback: try to find any backtick-quoted path starting with "/"
            target_matches = _TARGET_FILE_RE.findall(text)
            if target_matches:
                result.target_file = target_matches[
                    0
                ]  # First match is typically the primary target

        if not result.target_file:
            # No target file found — cannot perform stale detection
            return cls.clean()

        # Read the current source file
        if source_dir is None:
            source_dir = Path.cwd()
        else:
            source_dir = Path(source_dir)

        source_path = source_dir / result.target_file.lstrip("/")
        if declared_new:
            if not _new_target_acceptable(result, source_path):
                return result
            source_content = ""
        elif not source_path.exists():
            result.add_mismatch(
                "source_missing",
                f"Source file does not exist: {result.target_file}",
            )
            return result
        else:
            source_content = source_path.read_text(encoding="utf-8")
        source_lines = source_content.split("\n")
        file_cache: dict[str, str | None] = {}
        full_text = text
        text, companions = _parse_companions(full_text)

        # Check line number references
        _check_line_refs(
            result,
            text,
            source_lines,
            source_dir,
            result.target_file,
            file_cache,
            skip_unscoped=declared_new,
        )

        # Check symbol references
        _check_symbol_refs(
            result, text, source_content, source_dir, result.target_file, file_cache
        )

        # Check import references
        _check_import_refs(result, text, source_content)

        # Check "Before:" code block content
        _check_before_blocks(result, text, source_content)

        # Check each companion test file against its own block of the document
        for companion_path, companion_new, block in companions:
            result.merge(
                _check_companion(
                    companion_path, companion_new, block, source_dir, file_cache
                )
            )

        if sibling_mode != "off":
            _resolve_from_siblings(
                result, proc_path, full_text, source_dir, sibling_mode
            )

        return result


def _parse_companions(text: str) -> tuple[str, list[tuple[str, bool, str]]]:
    """Split the "### Companion test files" section from a procedure document.

    Returns the text without the section (what is checked against the primary
    target) and, per companion entry, `(path, declared_new, block_text)`, where
    the block runs from the entry's list item to the next entry. Without the
    section the text is returned unchanged with no companions. An entry with no
    backticked path is not recognized as a companion.
    """
    section = _COMPANION_SECTION_RE.search(text)
    if section is None:
        return text, []
    body = section.group(1)
    entries = list(_COMPANION_BULLET_RE.finditer(body))
    companions: list[tuple[str, bool, str]] = []
    for index, entry in enumerate(entries):
        end = entries[index + 1].start() if index + 1 < len(entries) else len(body)
        companions.append(
            (
                entry.group(1),
                _is_marked_new(body, entry.end()),
                body[entry.start() : end],
            )
        )
    return text[: section.start()] + text[section.end() :], companions


def _check_companion(
    path: str,
    declared_new: bool,
    block: str,
    source_dir: Path,
    file_cache: dict[str, str | None],
) -> StaleResult:
    """Check one companion's block against the companion file.

    A companion marked (new) must have an existing directory and no file, and its
    unscoped line citations are skipped; any other companion must exist. Every
    mismatch detail ends with " (companion {path})".
    """
    sub = StaleResult.clean()
    sub.target_file = path
    source_path = source_dir / path.lstrip("/")
    if declared_new:
        if _new_target_acceptable(sub, source_path):
            content = ""
        else:
            return _suffix_companion(sub, path)
    elif not source_path.exists():
        sub.add_mismatch("source_missing", f"Source file does not exist: {path}")
        return _suffix_companion(sub, path)
    else:
        content = source_path.read_text(encoding="utf-8")

    _check_line_refs(
        sub,
        block,
        content.split("\n"),
        source_dir,
        path,
        file_cache,
        skip_unscoped=declared_new,
    )
    _check_symbol_refs(sub, block, content, source_dir, path, file_cache)
    _check_import_refs(sub, block, content)
    _check_before_blocks(sub, block, content)
    return _suffix_companion(sub, path)


def _suffix_companion(result: StaleResult, path: str) -> StaleResult:
    """Append " (companion {path})" to every mismatch detail of `result`."""
    for mismatch in result.mismatches:
        mismatch["detail"] = f"{mismatch['detail']} (companion {path})"
    return result


def _source_plan_basename(text: str) -> str | None:
    """File name of the Plan named on the Traceability Source plan line, or None
    when the line is missing, empty, or starts with N/A."""
    match = _SOURCE_PLAN_RE.search(text)
    if match is None:
        return None
    value = match.group(1).strip().strip("`").strip()
    if not value or value.upper().startswith("N/A"):
        return None
    return Path(value.split()[0].strip("`")).name


def _procedure_seq(path: Path) -> int | None:
    """Sequence number in a procedure file name, or None when it has none."""
    match = _SEQ_RE.match(path.name)
    return int(match.group(1)) if match else None


def _find_siblings(
    source_dir: Path,
    plan_name: str,
    self_path: Path,
    warnings: list[str],
) -> list[tuple[Path, str]]:
    """Procedure documents of the same Plan other than `self_path`, as
    (path, text). An unreadable document is skipped with a warning."""
    siblings: list[tuple[Path, str]] = []
    for rel in _SIBLING_DIRS:
        directory = source_dir / rel
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            if path.resolve() == self_path:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                warnings.append(
                    f"sibling {path.name} skipped: {exc.__class__.__name__}"
                )
                continue
            if _source_plan_basename(text) != plan_name:
                continue
            siblings.append((path, text))
    return siblings


def _collect_new_declarations(
    text: str,
) -> tuple[set[str], set[tuple[str, str]]]:
    """Names and (module, names) imports that `text` marks (new)."""
    names = {
        m.group(1) for m in _SYMBOL_RE.finditer(text) if _is_marked_new(text, m.end())
    }
    imports = {
        (module, imported)
        for module, imported, marker in _IMPORT_RE.findall(text)
        if marker
    }
    return names, imports


def _resolve_from_siblings(
    result: StaleResult,
    proc_path: Path,
    text: str,
    source_dir: Path,
    sibling_mode: str,
) -> None:
    """Resolve symbol_missing / import_missing mismatches against (new)
    declarations in sibling procedures of the same Plan.

    A resolved mismatch moves to `result.resolved`. A name declared only by an
    ineligible later sibling stays a mismatch, with the sibling named after the
    original detail. Nothing here can turn a clean result stale.
    """
    plan_name = _source_plan_basename(text)
    if plan_name is None:
        return
    result.sibling_rule = "any" if sibling_mode == "any" else "earlier"
    if not any(
        m["type"] in ("symbol_missing", "import_missing") for m in result.mismatches
    ):
        siblings: list[tuple[Path, str]] = []
    else:
        siblings = _find_siblings(
            source_dir, plan_name, proc_path.resolve(), result.warnings
        )
    own_seq = _procedure_seq(proc_path)
    if siblings and sibling_mode == "earlier" and own_seq is None:
        result.warnings.append(
            f"{proc_path.name} has no sequence number; no sibling is eligible"
        )

    declarations: list[tuple[str, bool, set[str], set[tuple[str, str]]]] = []
    for path, sib_text in siblings:
        seq = _procedure_seq(path)
        eligible = sibling_mode == "any" or (
            own_seq is not None and seq is not None and seq < own_seq
        )
        names, imports = _collect_new_declarations(sib_text)
        declarations.append((path.name, eligible, names, imports))

    remaining: list[dict[str, Any]] = []
    for mismatch in result.mismatches:
        key: str | tuple[str, str] | None = None
        label = ""
        if mismatch["type"] == "symbol_missing":
            found = _MISSING_NAME_RE.match(mismatch["detail"])
            if found:
                key, label = found.group(1), found.group(1)
        elif mismatch["type"] == "import_missing":
            found_import = _MISSING_IMPORT_RE.match(mismatch["detail"])
            if found_import:
                key = (found_import.group(1), found_import.group(2))
                label = f"from {key[0]} import {key[1]}"
        declaring = [
            (doc, eligible)
            for doc, eligible, names, imports in declarations
            if key is not None and (key in names or key in imports)
        ]
        eligible_docs = [doc for doc, eligible in declaring if eligible]
        if eligible_docs:
            entry = {"name": label, "document": eligible_docs[0]}
            if entry not in result.resolved:
                result.resolved.append(entry)
            continue
        if declaring:
            mismatch = {
                **mismatch,
                "detail": (
                    f"{mismatch['detail']} (declared (new) only by a later sibling: "
                    f"{declaring[0][0]}; order rule: earlier)"
                ),
            }
        remaining.append(mismatch)
    result.mismatches = remaining
    result.is_stale = bool(remaining)


def _new_target_acceptable(result: StaleResult, source_path: Path) -> bool:
    """Validate a target declared new; record a mismatch and return False if not.

    The containing directory must exist, and the file itself must not: a file the
    procedure says it creates that is already present contradicts its premise.
    """
    if not source_path.parent.is_dir():
        result.add_mismatch(
            "new_target_dir_missing",
            f"Directory for new target file does not exist: {source_path.parent}",
        )
        return False
    if source_path.exists():
        result.add_mismatch(
            "new_target_exists",
            f"Target file declared new already exists: {result.target_file}",
        )
        return False
    return True


def _check_line_refs(
    result: StaleResult,
    proc_text: str,
    source_lines: list[str],
    source_dir: Path,
    target_file: str,
    file_cache: dict[str, str | None],
    *,
    skip_unscoped: bool = False,
) -> None:
    """Check whether cited line ranges still exist in the source file.

    For each "Line N" or "Lines N-M" reference, verify the line numbers
    are within the source file bounds. Out-of-bounds references indicate
    the procedure may be stale. When a scoped path is resolved via
    _find_scoped_path(), validate against that file's line count instead
    of the target file's. If the scoped file cannot be loaded, skip the
    citation (prevents false positives when the scoped file is inaccessible).
    With skip_unscoped (a target declared new has no lines yet), a citation with no
    scoped path is skipped instead of being checked against the target.
    """
    for match in _LINE_REF_RE.finditer(proc_text):
        start = int(match.group(1))  # Keep 1-indexed for comparison
        end_str = match.group(2)
        end = int(end_str) if end_str else start

        lines_to_check = source_lines
        label = "source file"
        scoped_path = _find_scoped_path(proc_text, match.start(), target_file)
        if scoped_path is None and skip_unscoped:
            continue
        if scoped_path is not None:
            scoped_content = _load_scoped_source(source_dir, scoped_path, file_cache)
            if scoped_content is not None:
                lines_to_check = scoped_content.split("\n")
                label = scoped_path
            else:
                # Scoped path found but file couldn't be loaded — skip this
                # citation instead of falling back to the target file (which
                # would produce a false positive).
                continue

        if start > len(lines_to_check):
            result.add_mismatch(
                "line_out_of_bounds",
                f"Line {start} exceeds {label} length ({len(lines_to_check)})"
                if not end_str
                else f"Lines {start}-{end} exceed {label} length ({len(lines_to_check)})",
            )
        elif end > len(lines_to_check):
            result.add_mismatch(
                "line_out_of_bounds",
                f"Line {end} exceeds {label} length ({len(lines_to_check)})",
            )

    return None


def _check_symbol_refs(
    result: StaleResult,
    proc_text: str,
    source_content: str,
    source_dir: Path,
    target_file: str,
    file_cache: dict[str, str | None],
) -> None:
    """Check whether cited symbol names still exist in the current source.

    Symbols matching _NON_SYMBOL_ALLOWLIST are skipped. Single common words
    that don't match any known symbol shape (_-prefixed, CamelCase, or
    snake_case with 2+ segments) are also skipped. When a scoped path
    is resolved via _find_scoped_path(), validate the symbol against that
    file's content instead of the target file's. Each occurrence is checked
    independently (no de-duplication).

    An unscoped symbol absent from the target/scoped file is reported missing
    only when it is absent from every .py file under source_dir. Existence is
    checked repo-wide rather than by location, so a symbol that merely lives in
    a different file (discussed here as a cross-reference) is not flagged —
    even when the citation names that other file. This trades the ability to
    catch a symbol that moved files for eliminating cross-reference false
    positives.
    """
    symbol_presence_cache: dict[str, bool] = {}
    lookup_cache: dict[str, set[str]] = {}
    for match in _SYMBOL_RE.finditer(proc_text):
        sym = match.group(1)
        if sym in _NON_SYMBOL_ALLOWLIST:
            continue
        if sym.startswith("http"):
            continue
        if sym.startswith("/") and "/" in sym[1:]:
            continue
        if sym.startswith(".") or sym.startswith("~"):
            continue
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", sym):
            continue
        # Minimum symbol shape: skip single common words that are unlikely to be
        # actual source-code symbols. Matches: _-prefixed, CamelCase, or snake_case
        # with 2+ underscore-separated segments.
        if not (
            re.match(r"^_[a-zA-Z0-9_]+$", sym)  # _-prefixed
            or re.search(r"[A-Z]", sym)  # CamelCase (has uppercase)
            or "_" in sym  # snake_case with segment
        ):
            continue

        if _is_marked_new(proc_text, match.end()):
            continue

        content_to_check = source_content
        scoped_path = _find_scoped_path(proc_text, match.start(), target_file)
        if scoped_path is not None:
            scoped_content = _load_scoped_source(source_dir, scoped_path, file_cache)
            if scoped_content is not None:
                content_to_check = scoped_content

        pattern = rf"\b{re.escape(sym)}\b"
        if not re.search(pattern, content_to_check):
            # Narrow false-positive guard (Option A): a symbol absent from the
            # target/scoped file may still exist elsewhere in the repo — cited
            # here as a cross-reference rather than a construct verified against
            # the target. Flag it missing only when it is absent from every
            # .py file under source_dir. Existence is checked repo-wide, not by
            # location, so a symbol that merely lives in another file (even one
            # named by the citation) is not reported stale.
            if not _symbol_present_somewhere(
                source_dir, sym, symbol_presence_cache
            ) and not _is_non_python_name(sym, source_dir, lookup_cache):
                result.add_mismatch(
                    "symbol_missing",
                    f"Symbol '{sym}' not found in source",
                )

    return None


def _check_import_refs(
    result: StaleResult,
    proc_text: str,
    source_content: str,
) -> None:
    """Check whether cited import paths still exist in the current source."""
    imports = _IMPORT_RE.findall(proc_text)

    for module, names, new_marker in imports:
        if new_marker:
            continue
        # Check if the import statement exists in the source
        import_pattern = rf"from\s+{re.escape(module)}\s+import\s+{re.escape(names)}"
        if not re.search(import_pattern, source_content):
            result.add_mismatch(
                "import_missing",
                f"Import 'from {module} import {names}' not found in source",
            )

    return None


def _check_before_blocks(
    result: StaleResult,
    proc_text: str,
    source_content: str,
) -> None:
    """Check whether "Before:" code blocks still match the current source.

    For each "# Before:" block, check if its content appears in the source file.
    If it doesn't, the procedure is likely stale.
    """
    before_blocks = _BEFORE_AFTER_RE.findall(proc_text)

    for block_content in before_blocks:
        # Normalize whitespace for comparison
        normalized_block = "\n".join(
            line.strip() for line in block_content.split("\n") if line.strip()
        )

        if not normalized_block:
            continue

        # Check if any significant portion of the block appears in the source
        lines = [line for line in block_content.split("\n") if line.strip()]
        found_any = False

        for line in lines[:5]:  # Check first 5 lines (heuristic limit)
            stripped_line = line.strip()
            if not stripped_line:
                continue
            # Try to find the line in the source (allowing for minor differences)
            if stripped_line in source_content:
                found_any = True
                break
            # Also try with leading/trailing whitespace variations
            for ws in [" ", "\t"]:
                if stripped_line.lstrip(ws) in source_content:
                    found_any = True
                    break
            if found_any:
                break

        if not found_any:
            result.add_mismatch(
                "before_block_missing",
                f"'Before:' code block not found in source:\n{block_content[:200]}",
            )

    return None


def main(argv=None):
    """CLI entry point for stale detection."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check implementation procedure for stale references",
    )
    parser.add_argument(
        "proc_path", help="Path to the implementation procedure document"
    )
    parser.add_argument(
        "--source-dir",
        default=None,
        help="Directory containing the source files",
    )
    parser.add_argument(
        "--sibling-order",
        choices=("earlier", "any"),
        default="earlier",
        help="which sibling procedures of the same Plan may declare a (new) name "
        "(default: earlier sequence numbers only)",
    )
    parser.add_argument(
        "--no-siblings",
        action="store_true",
        help="do not resolve names against sibling procedures of the same Plan",
    )
    args = parser.parse_args(argv)

    result = StaleResult.from_procedure(
        args.proc_path,
        args.source_dir,
        sibling_mode="off" if args.no_siblings else args.sibling_order,
    )
    print(result.summary)
    return 1 if result.abort_execution else 0


if __name__ == "__main__":
    sys.exit(main())
