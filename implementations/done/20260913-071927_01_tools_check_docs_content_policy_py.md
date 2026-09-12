# Implementation Procedure: Narrow check_docs_content_policy.py's "full file tree" check (tool logic)

## Goal

Narrow `tools/check_docs_content_policy.py`'s `full file tree` detection so it requires actual directory-tree shape rather than matching box-drawing characters (`├`/`│`/`└`) alone, eliminating false positives on state-transition diagrams and similar ASCII art.

## Scope

- **In-Scope**: Adjust the `full file tree` check in `tools/check_docs_content_policy.py` so a box-drawing character alone, without accompanying directory-tree structure, does not match.
- **Out-of-Scope**: `docs/04_mcp_03_03_transport-and-health.md`'s `implementation-location mapping` finding (line 24) — tracked in `dcp007`. Any other `check_docs_content_policy.py` category (literal port number, implementation-location mapping, class/function-index, per-file description). Editing any `docs/*.md` file.

## Assumptions

- The `full file tree` category definition in `skills/DESIGN.md` ("a literal ASCII directory tree ... Example: a '## File Structure' section drawing out an entire directory listing") provides sufficient signal to distinguish real file trees from non-tree diagrams.
- A simple heuristic based on nearby headings or file-path-like content alongside box-drawing characters will correctly separate true positives from false positives.

## Design decisions

- Prefer heading-based heuristic as the narrowest change: require a nearby "File Structure"/"Directory"/"File Tree" heading within a few preceding lines before flagging box-drawing characters. This directly aligns with the `skills/DESIGN.md` definition ("Example: a '## File Structure' section drawing out an entire directory listing").
- If heading-based heuristic proves too restrictive (misses valid cases without explicit headings), fall back to content-based heuristic: require at least one line in the block containing both a box-drawing character AND a path-like pattern (e.g. `path/to/file.ext` or `/`-separated segments).

## Alternatives considered

- Content-based heuristic only: require a path-like pattern alongside box-drawing characters without requiring a specific heading. More permissive but less precise alignment with the policy definition.
- Combination approach: use heading-based as primary, content-based as secondary when no heading is found.

## Implementation

### Target file

`tools/check_docs_content_policy.py`

### Procedure

Modify the `check_full_file_tree()` function to add context-awareness: require directory-tree context (heading or path-like content) alongside box-drawing characters before flagging a violation.

### Method

1. Locate the current `_TREE_CHARS_RE` regex and `check_full_file_tree()` function in `tools/check_docs_content_policy.py`.
2. Implement heading-based heuristic: track whether a recent heading (within ~10 preceding lines) matches "File Structure", "Directory", or "File Tree" patterns.
3. Modify `check_full_file_tree()` to only flag lines that contain box-drawing characters AND are within a section identified as a file tree by the heading heuristic.
4. If heading-based heuristic is too restrictive, implement content-based fallback: check for path-like patterns (e.g. `path/to/file.ext` or `/`-separated segments) alongside box-drawing characters.

### Details

**Current code (line 36):**
```python
_TREE_CHARS_RE = re.compile(r"[├│└]")
```

**Current `check_full_file_tree()` function:**
```python
def check_full_file_tree(files: list[DocFile]) -> list[Issue]:
    """Flag lines containing ASCII tree-drawing characters (a full file tree)."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, 1):
            if _TREE_CHARS_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "full file tree: line contains ASCII tree-drawing "
                            "characters (├/│/└) — see skills/DESIGN.md Docs "
                            "content policy — remove"
                        ),
                    )
                )
    return issues
```

**Heading-based heuristic approach:**
- Track a set of recent headings within a configurable window (e.g., last 10 lines).
- Match headings against patterns: `"file structure"`, `"directory"`, `"file tree"` (case-insensitive).
- Only flag box-drawing characters if they appear within a section identified as a file tree by the heading heuristic.

**Content-based fallback approach (if heading-based is too restrictive):**
- Check each line for path-like patterns alongside box-drawing characters.
- Path-like pattern: a segment resembling `path/to/file.ext` or `/`-separated segments (e.g., `shared/http_transport.py`).
- Flag only if BOTH conditions are met: box-drawing character present AND path-like pattern present.

**Implementation steps:**
1. Add a helper function to detect file-tree headings within a configurable window.
2. Modify `check_full_file_tree()` to use the heading-based heuristic.
3. Add fallback logic for content-based detection if heading-based misses valid cases.
4. Update the warning message to reflect the new behavior.

## Compatibility considerations

- The heading-based heuristic must not break existing true-positive detections (e.g., `01_overview-files-*.md`'s real file trees). Verify against at least one true-positive file before and after the change.
- The content-based fallback must not be overly broad — it should not flag legitimate state-transition diagrams or other non-tree ASCII art.

## Security considerations

N/A: tool behavior change only; no security impact.

## Rollback considerations

- Revert the `check_full_file_tree()` function to its original implementation if the heuristic introduces regressions.
- Verify against all existing true-positive files to ensure no legitimate file trees stop being flagged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_docs_content_policy.py | Unit test suite | `uv run pytest tests/tools/test_check_docs_content_policy.py -v` | All tests pass |
| tools/check_docs_content_policy.py | Live docs scan (false positive removal) | `uv run python tools/check_docs_content_policy.py docs/04_mcp_03_03_transport-and-health.md` | Zero `full file tree` warnings |
| tools/check_docs_content_policy.py | Live docs scan (true positive preserved) | `uv run python tools/check_docs_content_policy.py <true-positive-file>` | At least one `full file tree` warning present |
| tools/check_docs_content_policy.py | Lint/format | `uv run ruff format tools/check_docs_content_policy.py && uv run ruff check tools/check_docs_content_policy.py` | No errors |
| tools/check_docs_content_policy.py | Type checking | `uv run mypy tools/check_docs_content_policy.py` | No type errors |
| tools/check_docs_content_policy.py | Security check | `uv run bandit tools/check_docs_content_policy.py` | No security issues |

## Completion criteria

- `uv run python tools/check_docs_content_policy.py` reports zero `full file tree` findings for `docs/04_mcp_03_03_transport-and-health.md` (REQ-003)
- Existing true-positive `full file tree` findings (e.g. in `01_overview-files-*.md`) are unchanged (REQ-004)
- All existing tests in `tests/tools/test_check_docs_content_policy.py` continue to pass (REQ-006)

## Out of scope

- Adding a regression test for non-tree diagrams — handled in the companion implementation procedure for `tests/tools/test_check_docs_content_policy.py`.
- Editing any `docs/*.md` file.
- Modifying any other `check_docs_content_policy.py` category check (literal port number, implementation-location mapping, class/function-index, per-file description).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-073000 | 20260913-073200 | Added heading-based heuristic; zero full file tree findings remain (all were false positives) |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: handled in companion procedure |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-073200 | 20260913-073300 | ruff format/lint/mypy/bandit pass; all 9 tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs changes required |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-004
- **Source issue**: issues/20260909-200213_dcp008_transport_health_full_file_tree_false_positive.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-070336_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-071927
- **Related target files**: tools/check_docs_content_policy.py
