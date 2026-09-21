# Implementation Procedure: Reduce stale_detector.py false positives on docs-target procedures

## Goal

Reduce false-positive stale detection results in `scripts/agent/stale_detector.py`'s symbol and line-reference checks when processing docs-target implementation procedures, without weakening genuine stale reference detection.

## Scope

Extend `_check_symbol_refs()` filtering (lines 347-389) and extend `_check_line_refs()` (lines 301-344) to resolve file scoping for line citations. Specifically:
1. Add a minimum symbol shape heuristic to `_check_symbol_refs()` to reduce matches on single common words (e.g., `y`, `a`, `i`)
2. Ensure `_check_line_refs()` properly handles line citations scoped to Reference Files

## Assumptions

- The existing `_NON_SYMBOL_ALLOWLIST` already covers tool-vocabulary terms, CLI tool names, front-matter keys, and workflow status values identified in REQ-001 through REQ-004
- The `_find_scoped_path()` and `_load_scoped_source()` functions correctly identify and load Reference File content for scoped citations
- The "any single mismatch constitutes stale" policy remains unchanged
- The tool's design decision to use simple regex/string matching (not AST parsing) remains valid

## Design decisions

- **Minimum symbol shape heuristic**: Require symbols to match at least one of: `_`-prefixed (e.g., `_llm_runner`), `CamelCase` (e.g., `LLMTurnRunner`), or `snake_case` with 2+ underscore-separated segments (e.g., `chunk_id`). Single common words like `y`, `a`, `i` won't match any of these patterns and will be skipped.
- **Fallback handling for scoped files**: When `_find_scoped_path()` finds a scoped path but `_load_scoped_source()` returns None, treat the citation as unverified rather than flagging it as out-of-bounds. This prevents false positives when the scoped file cannot be read.

## Alternatives considered

- **Full allowlist expansion**: Adding every possible prose token to `_NON_SYMBOL_ALLOWLIST`. Not scalable — new tokens would keep appearing.
- **AST-based parsing**: Would require significant complexity increase and dependency on Python's AST module. Per REQ-002 constraint, the regex-based design is preferred.
- **Suppressing all single-character symbols**: Too aggressive — some legitimate symbols are single characters (e.g., `x`, `y` in coordinate systems). The minimum shape heuristic is more precise.

## Implementation

### Target file

`scripts/agent/stale_detector.py`

### Procedure

#### Part A: Extend `_check_symbol_refs()` filtering

1. After the existing allowlist check (line 364) and the existing filters (lines 366-373), add a minimum symbol shape check:
   - Skip symbols that don't match any of:
     - `_`-prefixed identifiers: `^_[a-zA-Z0-9_]+$`
     - CamelCase identifiers: `^[A-Z][a-z]+[A-Z]` (at least two uppercase letters indicating camelCase)
     - snake_case with 2+ segments: `^[a-z]+_[a-z]+` (underscore followed by lowercase letters)
   - Symbols that don't match any pattern are assumed to be prose tokens and are skipped

2. Update the docstring to mention the minimum shape heuristic.

#### Part B: Extend `_check_line_refs()` scoping

1. In the fallback case where `_find_scoped_path()` finds a scoped path but `_load_scoped_source()` returns None, change the behavior:
   - Current: Falls back to validating against the target file's line count (producing false positives)
   - New: Skip the line-out-of-bounds check for this citation (treat as unverified rather than stale)

2. Update the docstring to clarify the fallback behavior.

### Method

Edit `scripts/agent/stale_detector.py` using the Edit tool to modify the two functions.

### Details

**Part A: Symbol shape heuristic**

Current code around lines 362-373:
```python
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
```

Add after the existing filters (after line 373):
```python
    # Minimum symbol shape: skip single common words that are unlikely to be
    # actual source-code symbols. Matches: _-prefixed, CamelCase, or snake_case
    # with 2+ underscore-separated segments.
    if not (
        re.match(r"^_[a-zA-Z0-9_]+$", sym)           # _-prefixed
        or re.search(r"[A-Z]", sym)                    # CamelCase (has uppercase)
        or "_" in sym                                    # snake_case with segment
    ):
        continue
```

**Part B: Line ref fallback handling**

Current code around lines 324-342:
```python
scoped_path = _find_scoped_path(proc_text, match.start(), target_file)
if scoped_path is not None:
    scoped_content = _load_scoped_source(source_dir, scoped_path, file_cache)
    if scoped_content is not None:
        lines_to_check = scoped_content.split("\n")
        label = scoped_path
```

Change to:
```python
scoped_path = _find_scoped_path(proc_text, match.start(), target_file)
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
```

## Compatibility considerations

- The minimum symbol shape heuristic may cause some legitimate single-word symbols (e.g., `x`, `y` in coordinate contexts) to no longer be detected as stale references. This is an acceptable trade-off given the high false-positive rate observed in the batch.
- The line ref fallback change means that when a scoped file can't be read, the citation won't be validated at all. This reduces false positives but slightly weakens the check for those specific cases.

## Security considerations

N/A: This is a tooling accuracy fix with no security impact.

## Rollback considerations

To rollback, restore the original function implementations from git history:
```bash
git checkout HEAD~1 -- scripts/agent/stale_detector.py
```
No data migration or configuration changes are involved.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| scripts/agent/stale_detector.py | Unit tests for false-positive scenarios | uv run pytest tests/agent/ -k stale_detector -v | All new tests pass |
| scripts/agent/stale_detector.py | Unit tests for true-positive detection | uv run pytest tests/agent/ -k stale_detector -v | Existing behavior preserved |
| scripts/agent/stale_detector.py | Lint check | uv run ruff check scripts/agent/stale_detector.py | No errors |
| scripts/agent/stale_detector.py | Type check | uv run mypy scripts/agent/stale_detector.py | No errors |

## Completion criteria

- `_check_symbol_refs()` skips single common words that don't match any known symbol shape pattern (REQ-001 through REQ-004).
- `_check_line_refs()` does not flag line citations scoped to Reference Files as `line_out_of_bounds` when the scoped file exists (REQ-005).
- `_check_symbol_refs()` still detects genuinely stale references to the Target file's own symbols (REQ-006).
- `_check_line_refs()` still detects genuinely out-of-bounds line ranges for the Target file itself (REQ-007).
- The file passes `ruff check` with no errors.
- The file passes `mypy` with no type errors.
- All unit tests pass.

## Out of scope

- Modifying `code-implementation` Step 2.5's abort-on-any-mismatch policy.
- Introducing AST-based parsing.
- Modifying archived implementation procedure documents.
- Updating documentation (`docs/*.md`) — per Documentation Impact section of the Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend _check_symbol_refs() filtering (minimum symbol shape heuristic) | Pending | — | — | |
| 2 | Extend _check_line_refs() fallback handling | Pending | — | — | |
| 3 | Run lint/type checks on scripts/agent/stale_detector.py | Pending | — | — | |
| 4 | Add unit tests for all four acceptance criterion cases | Pending | — | — | |
| 5 | Run pytest tests/agent/ -k stale_detector -v | Pending | — | — | |

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
- **Requirement ID**: REQ-001 through REQ-007
- **Source issue**: issues/20260920-175023_staledet01_reduce-stale_detector.py-false-positives-on-docs-target-procedures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-220911_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-062601
- **Related target files**: scripts/agent/stale_detector.py
