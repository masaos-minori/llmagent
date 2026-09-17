## Goal

Add an explicit "unvalidated heuristic, pending performance tuning" marker above `MIN_HEADING_LINES_FOR_MARKDOWN = 2` in `scripts/rag/ingestion/chunk_splitter.py` (line 36), since no rationale was recoverable for this constant. Per REQ-001; AC-1, AC-4.

## Scope

- Add a comment immediately above the constant definition at line 36
- No behavior change — comment-only addition

## Assumptions

- The constant's value (2) remains unchanged — this Plan does not alter any constant value
- The two prior investigation attempts (`git log -S"MIN_HEADING_LINES_FOR_MARKDOWN"` earliest commit 2026-06-12 mechanical PLR2004 refactor; `issues/done/20260802-080020_rag_02_03_cleanup_and_heading_lines_rationale.md` filed 2026-08-02) found no rationale and remain unresolved

## Design decisions

- Append to the existing "prevents query explosion" comment style rather than replacing it — the new marker extends the existing convention used by `_MAX_FTS_TOKENS` (REQ-002)

## Alternatives considered

- Placing the marker in a separate docstring or config file: rejected because the source issue requires the marker at the definition site itself

## Implementation

### Target file

`scripts/rag/ingestion/chunk_splitter.py`

### Procedure

Insert a comment block immediately above `MIN_HEADING_LINES_FOR_MARKDOWN = 2`.

### Method

Edit line 36 region: add a TOML-style comment block before the constant assignment.

### Details

Current state (lines 35-37):
```python
MIN_HEADING_LINES_FOR_MARKDOWN = 2
MARKDOWN_HEADING_RE = r"^#{1,6}"
```

After edit:
```python
# Unvalidated heuristic, pending performance tuning — no recorded rationale found
# via git history or originating issues (2026-08-02 investigation also inconclusive).
MIN_HEADING_LINES_FOR_MARKDOWN = 2
MARKDOWN_HEADING_RE = r"^#{1,6}"
```

## Compatibility considerations

N/A: comment-only addition, no runtime behavior change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

If the comment text proves inaccurate later, the rollback is removing the added comment lines — no code revert needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/ingestion/chunk_splitter.py | Lint/type check | `uv run ruff format`, `uv run ruff check`, `uv run mypy` | Pass with no new findings |
| scripts/rag/ingestion/chunk_splitter.py | Manual diff review | `git diff` | Only comment lines added, no value line changed |

## Completion criteria

- [ ] AC-1: An explicit "unvalidated heuristic" marker exists above `MIN_HEADING_LINES_FOR_MARKDOWN` at its definition site
- [ ] AC-4: The constant value was not changed (verified by `git diff`)

## Out of scope

- Changing `MIN_HEADING_LINES_FOR_MARKDOWN`'s value
- Adding tests for this constant
- Editing other constants in this file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add heuristic marker above MIN_HEADING_LINES_FOR_MARKDOWN | Pending | — | — | |
| 2 | Run validation sequence (ruff/mypy) | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260915-200627_rag03_establish-rationale-for-undocumented-chunking-and-crawler-tuning-constants.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-153123_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260917-093845
- **Related target files**: scripts/rag/ingestion/chunk_splitter.py
