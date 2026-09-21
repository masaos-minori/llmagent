## Goal
Add a non-symbol allowlist to `_check_symbol_refs()`, and extend both
`_check_symbol_refs()` and `_check_line_refs()` to resolve which file a citation is
actually scoped to (the nearest preceding backtick-quoted `.py`/`.md` path in the same
paragraph), validating against that file's real content/line count instead of always
the Target file's.

## Scope
In scope: `_check_symbol_refs()`, `_check_line_refs()`, a new `_resolve_scoped_path()`
helper, and `from_procedure()`'s call sites for both (REQ-001, REQ-002, REQ-003 of
`plans/20260920-221706_plan.md`).
Out of scope: `_check_import_refs()`, `_check_before_blocks()` (no false positive
reported against them); any change to `StaleResult`'s public shape or `main()`'s CLI
contract.

## Assumptions
- The Plan's own Design section's "paragraph" granularity (text between blank lines)
  is used as the scoping boundary — resolved as UNK-01's simplest-sufficient choice,
  confirmed applicable here since the concrete historical false-positive case (Row's
  Reference File) cites the Reference File path and its line range in the same
  sentence/bullet, well within a single paragraph.
- `_find_scoped_path()`'s file-existence check resolves relative to the repository
  root passed to `from_procedure()` as `source_dir` (already a parameter, confirmed at
  line 200-203) — the same base every other path resolution in this module already
  uses.

## Design decisions
- Add one new regex, `_SCOPED_PATH_RE = re.compile(r"`([\w./-]+\.(?:py|md))`")`,
  matching a backtick-quoted relative path ending in `.py` or `.md` (distinct from the
  existing `_TARGET_FILE_RE`, which only matches paths starting with `/`).
- Add `_find_scoped_path(proc_text, pos, target_file) -> str | None`: locate the
  paragraph containing position `pos` (text between the nearest preceding `"\n\n"` and
  `pos`), find every `_SCOPED_PATH_RE` match within it, and return the last one that is
  not equal to `target_file` (i.e. the nearest preceding *other* file path), or `None`
  if none found.
- Add `_load_scoped_source(source_dir, path, cache) -> str | None`: read `path`
  relative to `source_dir` once, memoizing hits and misses in `cache` (a
  `dict[str, str | None]` passed in from `from_procedure()`) so a Reference File cited
  multiple times in one procedure is read from disk only once per `from_procedure()`
  call (Design's own stated cache-per-call rationale, matching the Plan's Risks
  mitigation).
- Both `_check_symbol_refs()` and `_check_line_refs()` change from
  `_SYMBOL_RE.findall(...)`/iterating a pre-extracted match list to `.finditer(...)`,
  so each match's `.start()` position is available for `_find_scoped_path()` — this
  also means `_check_symbol_refs()` no longer de-duplicates symbols via `set(...)`
  before checking (a symbol appearing twice, once correctly scoped to a Reference File
  and once not, is now checked independently at each occurrence, which is strictly
  more accurate than checking a single de-duplicated occurrence).
- Add `_NON_SYMBOL_ALLOWLIST` (REQ-001), checked first in `_check_symbol_refs()`'s
  existing filtering, before the `http`/path/dotted-prefix checks.

## Alternatives considered
- Restricting symbol extraction to backtick spans only inside `### Target file` /
  `### Procedure` / `### Method` / `### Details` sections (the Issue's first-listed
  Implementation Intent option): rejected in favor of the Plan's chosen file-scoping
  approach — the allowlist alone does not resolve the Reference-File-citation case
  (REQ-002/REQ-003), and file-scoping subsumes the section-restriction idea without
  needing to special-case which document sections are "citation contexts."
- Requiring a minimum symbol shape (CamelCase / `_`-prefixed / multi-segment
  `snake_case`) to reduce single-common-word matches (Issue's suggested extra
  heuristic): not implemented — the allowlist (REQ-001) already covers every concrete
  false positive the Issue and Plan cite; adding a shape heuristic on top is
  unrequested scope not needed to satisfy any Requirement or Acceptance Criterion.

## Implementation
### Target file
`scripts/agent/stale_detector.py`

### Procedure
1. Add `_NON_SYMBOL_ALLOWLIST`, `_SCOPED_PATH_RE`, `_find_scoped_path()`, and
   `_load_scoped_source()` near the existing module-level regexes/helpers (after
   `_TARGET_FILE_SECTION_RE`, before the `StaleResult` dataclass, i.e. around line
   64).
2. In `StaleResult.from_procedure()`, add a `file_cache: dict[str, str | None] = {}`
   local variable and pass `source_dir` and `result.target_file` (already computed
   locally) plus `file_cache` into both `_check_line_refs()` and
   `_check_symbol_refs()` calls (lines 217, 220).
3. Update `_check_line_refs()`'s signature to accept `source_dir: Path, target_file:
   str, file_cache: dict[str, str | None]`; inside its loop, resolve the scoped file
   per citation via `_find_scoped_path()`/`_load_scoped_source()` and validate against
   that file's line count (falling back to `source_lines`/`target_file` when
   unresolved).
4. Update `_check_symbol_refs()`'s signature the same way; check the
   `_NON_SYMBOL_ALLOWLIST` first, then resolve the scoped file per candidate symbol
   and validate against that file's content (falling back to `source_content` when
   unresolved).

### Method
Direct file edit (`Edit` tool) — add 4 module-level helpers, extend 2 existing
function signatures and bodies, update 2 call sites in `from_procedure()`; no change
to `StaleResult`'s dataclass fields, `main()`, or the CLI contract.

### Details
Current module-level regexes/helpers (confirmed via Read, lines 56-64):
```python
# Target file path references: "`scripts/agent/orchestrator.py`"
_TARGET_FILE_RE = re.compile(r"`(/[^`]+)`")

# Extract target file from the "### Target file" section of the procedure document
_TARGET_FILE_SECTION_RE = re.compile(
    r"###\s*Target\s+file\s*\n\s*`([^`]+)`",
    re.IGNORECASE,
)
```

New helpers to add after them (illustrative — write exact final code during
implementation):
```python
_NON_SYMBOL_ALLOWLIST = frozenset(
    {
        # Repository workflow tool vocabulary
        "Edit", "Write", "Read", "Bash", "old_string", "new_string", "replace_all",
        # Common CLI tool names
        "ruff", "mypy", "pytest", "pyright", "bandit",
        # Common Markdown front-matter keys
        "title", "area", "tags", "related", "source",
        # Workflow status values
        "Pending", "In Progress", "Blocked", "Completed",
    }
)

# A backtick-quoted relative .py/.md path other than a leading-slash absolute one
# (see _TARGET_FILE_RE above), used to scope a nearby symbol/line citation.
_SCOPED_PATH_RE = re.compile(r"`([\w./-]+\.(?:py|md))`")


def _find_scoped_path(proc_text: str, pos: int, target_file: str) -> str | None:
    """Return the nearest preceding backtick-quoted .py/.md path (other than
    target_file) in the same paragraph as the citation at `pos`, or None."""
    para_start = proc_text.rfind("\n\n", 0, pos)
    para_start = 0 if para_start == -1 else para_start + 2
    paragraph_before = proc_text[para_start:pos]
    paths = _SCOPED_PATH_RE.findall(paragraph_before)
    for path in reversed(paths):
        if path != target_file:
            return path
    return None


def _load_scoped_source(
    source_dir: Path,
    path: str,
    cache: dict[str, str | None],
) -> str | None:
    """Read `path` relative to source_dir once, memoizing hits and misses."""
    if path in cache:
        return cache[path]
    candidate = source_dir / path.lstrip("/")
    if not candidate.exists():
        cache[path] = None
        return None
    content = candidate.read_text(encoding="utf-8")
    cache[path] = content
    return content
```

Current `from_procedure()` call sites (confirmed via Read, lines 213-223):
```python
        source_content = source_path.read_text(encoding="utf-8")
        source_lines = source_content.split("\n")

        # Check line number references
        _check_line_refs(result, text, source_lines)

        # Check symbol references
        _check_symbol_refs(result, text, source_content)
```
Target replacement:
```python
        source_content = source_path.read_text(encoding="utf-8")
        source_lines = source_content.split("\n")
        file_cache: dict[str, str | None] = {}

        # Check line number references
        _check_line_refs(
            result, text, source_lines, source_dir, result.target_file, file_cache
        )

        # Check symbol references
        _check_symbol_refs(
            result, text, source_content, source_dir, result.target_file, file_cache
        )
```

Current `_check_line_refs()` (confirmed via Read, lines 231-264):
```python
def _check_line_refs(
    result: StaleResult,
    proc_text: str,
    source_lines: list[str],
) -> None:
    """..."""
    for match in _LINE_REF_RE.finditer(proc_text):
        start = int(match.group(1))
        end_str = match.group(2)
        if end_str:
            end = int(end_str)
        else:
            end = start

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
```
Target replacement (behavior for an unresolved/Target-file citation is byte-for-byte
identical to today — only the resolved-Reference-File branch is new):
```python
def _check_line_refs(
    result: StaleResult,
    proc_text: str,
    source_lines: list[str],
    source_dir: Path,
    target_file: str,
    file_cache: dict[str, str | None],
) -> None:
    """..."""
    for match in _LINE_REF_RE.finditer(proc_text):
        start = int(match.group(1))
        end_str = match.group(2)
        end = int(end_str) if end_str else start

        lines_to_check = source_lines
        label = "source file"
        scoped_path = _find_scoped_path(proc_text, match.start(), target_file)
        if scoped_path is not None:
            scoped_content = _load_scoped_source(source_dir, scoped_path, file_cache)
            if scoped_content is not None:
                lines_to_check = scoped_content.split("\n")
                label = scoped_path

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
```

Current `_check_symbol_refs()` (confirmed via Read, lines 267-299):
```python
def _check_symbol_refs(
    result: StaleResult,
    proc_text: str,
    source_content: str,
) -> None:
    """..."""
    symbols = set(_SYMBOL_RE.findall(proc_text))

    code_symbols = set()
    for sym in symbols:
        if sym.startswith("http"):
            continue
        if sym.startswith("/") and "/" in sym[1:]:
            continue
        if sym.startswith(".") or sym.startswith("~"):
            continue
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", sym):
            code_symbols.add(sym)

    for sym in code_symbols:
        pattern = rf"\b{re.escape(sym)}\b"
        if not re.search(pattern, source_content):
            result.add_mismatch(
                "symbol_missing",
                f"Symbol '{sym}' not found in source",
            )

    return None
```
Target replacement:
```python
def _check_symbol_refs(
    result: StaleResult,
    proc_text: str,
    source_content: str,
    source_dir: Path,
    target_file: str,
    file_cache: dict[str, str | None],
) -> None:
    """..."""
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

        content_to_check = source_content
        scoped_path = _find_scoped_path(proc_text, match.start(), target_file)
        if scoped_path is not None:
            scoped_content = _load_scoped_source(source_dir, scoped_path, file_cache)
            if scoped_content is not None:
                content_to_check = scoped_content

        pattern = rf"\b{re.escape(sym)}\b"
        if not re.search(pattern, content_to_check):
            result.add_mismatch(
                "symbol_missing",
                f"Symbol '{sym}' not found in source",
            )

    return None
```
Confirm `Path` is already imported at module level (confirmed: `from pathlib import
Path`, line 26) — no new import needed for the type hints above.

## Compatibility considerations
No change to `StaleResult`'s public fields/methods, `from_procedure()`'s public
signature, or `main()`'s CLI contract — `_check_line_refs()`/`_check_symbol_refs()`
are private (underscore-prefixed) module functions with no external caller besides
`from_procedure()` and their own unit tests (this Plan's Row 2 updates those tests to
match the new signatures). The only externally-observable change is fewer
`symbol_missing`/`line_out_of_bounds` findings for correctly-scoped citations — no new
finding type, and Target-file-scoped citations behave identically to today.

## Security considerations
N/A: `_load_scoped_source()` reads a `.py`/`.md` file path already confirmed to be
extracted from repository-controlled implementation procedure documents, resolved
relative to `source_dir` (the repository root already trusted by every other file
read in this module) — no path traversal beyond what `_TARGET_FILE_RE`'s existing
absolute-path resolution already allows, and a nonexistent/unreadable path safely
falls back to the Target-file behavior rather than raising.

## Rollback considerations
Trivially revertable: reverting the two function signatures/bodies, the two
`from_procedure()` call sites, and removing the four new module-level helpers
restores the exact prior window-only, Target-file-only behavior.

## Validation plan
- `uv run ruff check scripts/agent/stale_detector.py` /
  `uv run mypy scripts/agent/stale_detector.py`.
- `uv run pytest tests/agent/test_stale_detector.py -v` — the companion procedure
  (`implementations/20260921-062324_02_tests_agent_test_stale_detector.py.md`, this
  Plan's Row 2) updates the existing calls to `_check_symbol_refs()`/
  `_check_line_refs()` to match the new signatures and adds the new regression tests;
  run once after both rows land, per the Plan's own Tests section.
- Spot-check: re-run `uv run python scripts/agent/stale_detector.py
  implementations/done/20260920-163055_01_docs_05_agent_05_llm-and-streaming.md.md`
  (the archived procedure the Plan cites as the concrete historical Reference-File
  false-positive case) and confirm no `line_out_of_bounds`/`symbol_missing` finding
  remains for that citation.

## Completion criteria
- `_check_symbol_refs()` never flags an `_NON_SYMBOL_ALLOWLIST` token.
- A symbol/line citation correctly scoped (via the nearest preceding backtick-quoted
  path in the same paragraph) to an existing Reference File is validated against that
  file, not the Target file.
- A citation with no resolvable scoped path, or scoped to the Target file itself,
  behaves identically to before this change.
- `uv run ruff check` / `uv run mypy` pass clean on this file.

## Out of scope
- Writing/updating the tests themselves — covered by this Plan's Row 2
  (`tests/agent/test_stale_detector.py`), a separate implementation procedure
  document.
- `_check_import_refs()`, `_check_before_blocks()`, `main()`, `StaleResult`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_NON_SYMBOL_ALLOWLIST`, `_SCOPED_PATH_RE`, `_find_scoped_path()`, `_load_scoped_source()` | Completed | — | 20260921-192353 |  |
| 2 | Update `_check_line_refs()` and `_check_symbol_refs()` signatures/bodies and their `from_procedure()` call sites | Completed | — | 20260921-192353 |  |
| 3 | Run `ruff check` / `mypy`, then `tests/agent/test_stale_detector.py` and the archived-procedure spot-check (after Row 2's tests also land) | Completed | — | 20260921-192353 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (non-symbol allowlist; file-scoped citation resolution for symbols and line ranges)
- **Source issue**: issues/20260920-175023_staledet01_reduce-stale_detector.py-false-positives-on-docs-target-procedures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-221706_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260921-062324
- **Related target files**: scripts/agent/stale_detector.py