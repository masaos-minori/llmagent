"""scripts/agent/stale_detector.py

Lightweight stale detection for implementation procedures.

Before executing a procedure, verify that the code constructs it references
(line numbers, symbol names, import paths) still exist in the current source.
If they do not, mark the procedure as stale and skip execution.

Uses simple regex/string matching against the cited line ranges specified in
the procedure document — avoids AST parsing as specified in the issue.
Any single mismatch constitutes "stale"; the procedure cannot be reliably
executed if even one referenced construct is missing.

Design decisions:
- Report all failures in a single pass; this is simpler and provides more
  information to the operator.
- Any single mismatch constitutes "stale" — the procedure cannot be reliably
  executed if even one referenced construct is missing.
"""

from __future__ import annotations

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

# Import path references: "from agent.llm_turn_runner import LLMTurnRunner"
_IMPORT_RE = re.compile(
    r"(?i)"
    r"from\s+(\S+)\s+import\s+(.+?)"
    r"(?:\s*$|\s+#)"
)

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


@dataclass
class StaleResult:
    """Structured result of a stale detection check."""

    is_stale: bool
    target_file: str | None = None
    mismatches: list[dict[str, Any]] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """Human-readable summary of the stale check result."""
        if not self.is_stale:
            return "Procedure is not stale — all referenced constructs found."
        parts = [f"Stale: {len(self.mismatches)} mismatch(es) detected."]
        for m in self.mismatches:
            parts.append(f"  - {m['type']}: {m['detail']}")
        return "\n".join(parts)

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
    ) -> StaleResult:
        """Run stale detection on a procedure document.

        Args:
            proc_path: Path to the implementation procedure document.
            source_dir: Directory containing the source files referenced by
                the procedure. Defaults to the repository root.

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
        if target_match:
            result.target_file = target_match.group(1)
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
        if not source_path.exists():
            result.add_mismatch(
                "source_missing",
                f"Source file does not exist: {result.target_file}",
            )
            return result

        source_content = source_path.read_text(encoding="utf-8")
        source_lines = source_content.split("\n")

        # Check line number references
        _check_line_refs(result, text, source_lines)

        # Check symbol references
        _check_symbol_refs(result, text, source_content)

        # Check import references
        _check_import_refs(result, text, source_content)

        # Check "Before:" code block content
        _check_before_blocks(result, text, source_content)

        return result


def _check_line_refs(
    result: StaleResult,
    proc_text: str,
    source_lines: list[str],
) -> None:
    """Check whether cited line ranges still exist in the source file.

    For each "Line N" or "Lines N-M" reference, verify the line numbers
    are within the source file bounds. Out-of-bounds references indicate
    the procedure may be stale.
    """
    for match in _LINE_REF_RE.finditer(proc_text):
        start = int(match.group(1))  # Keep 1-indexed for comparison
        end_str = match.group(2)
        if end_str:
            end = int(end_str)
        else:
            end = start

        # Check if the line range exceeds the source file length
        if start > len(source_lines):
            result.add_mismatch(
                "line_out_of_bounds",
                f"Line {start} exceeds source file length ({len(source_lines)})"
                if not end_str
                else f"Lines {start}-{end} exceed source file length ({len(source_lines)})",
            )
        elif end > len(source_lines):
            result.add_mismatch(
                "line_out_of_bounds",
                f"Line {end} exceeds source file length ({len(source_lines)})",
            )

    return None


def _check_symbol_refs(
    result: StaleResult,
    proc_text: str,
    source_content: str,
) -> None:
    """Check whether cited symbol names still exist in the current source."""
    # Extract symbols from the procedure document
    symbols = set(_SYMBOL_RE.findall(proc_text))

    # Filter out common non-code tokens (backtick-quoted text that isn't a code symbol)
    code_symbols = set()
    for sym in symbols:
        # Skip common non-code patterns
        if sym.startswith("http"):
            continue
        if sym.startswith("/") and "/" in sym[1:]:
            continue
        if sym.startswith(".") or sym.startswith("~"):
            continue
        # Keep only plausible code symbols (alphanumeric + underscores)
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", sym):
            code_symbols.add(sym)

    for sym in code_symbols:
        # Use word boundary matching to avoid false positives
        pattern = rf"\b{re.escape(sym)}\b"
        if not re.search(pattern, source_content):
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

    for module, names in imports:
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
    args = parser.parse_args(argv)

    result = StaleResult.from_procedure(args.proc_path, args.source_dir)
    print(result.summary)
    return 1 if result.abort_execution else 0


if __name__ == "__main__":
    sys.exit(main())
