## Goal

Add an explicit "unvalidated heuristic, pending performance tuning" marker as Python comments above `MIN_HEADING_LINES_FOR_MARKDOWN = 2` in `scripts/rag/ingestion/chunk_splitter.py` (line 36), since no definitive rationale was recoverable for this constant. Note: the source issue (`issues/done/20260915-200627_rag03_establish-rationale-for-undocumented-chunking-and-crawler-tuning-constants.md`) is under `issues/done/` — verify whether this specific marker has already been applied before executing. Unlike REQ-002 which extends an existing comment with a semicolon continuation, this constant has no existing comment to extend; a new standalone comment block will be added. Per REQ-001; AC-1, AC-4.

## Scope

- Add a comment immediately above the constant definition at line 36
- No behavior change — comment-only addition

## Assumptions

- The constant's value (2) remains unchanged — this Plan does not alter any constant value
- The two prior investigation attempts (`git log -S"MIN_HEADING_LINES_FOR_MARKDOWN"` earliest commit 2026-06-12 mechanical PLR2004 refactor; `issues/done/20260802-080020_rag_02_03_cleanup_and_heading_lines_rationale.md` filed 2026-08-02) found no definitive rationale and remain unresolved or resolved inconclusively
- The source issue is under `issues/done/`; if it was resolved by adding heuristic markers to ALL seven constants, this procedure may be redundant — verify before executing
- Both `MIN_HEADING_LINES_FOR_MARKDOWN` and `MARKDOWN_HEADING_RE` are defined together without comments; adding documentation to one without the other creates asymmetry, but only this constant is targeted by REQ-001

## Design decisions

- Add a new standalone Python comment block above the bare constant rather than extending an existing comment — this file has no existing comment above `MIN_HEADING_LINES_FOR_MARKDOWN`, unlike REQ-002 which extends an existing single-line comment with a semicolon continuation

## Alternatives considered

- Placing the marker in a separate docstring or config file: rejected because the source issue requires the marker at the definition site itself

## Implementation

### Target file

`scripts/rag/ingestion/chunk_splitter.py`

### Procedure

Insert a comment block immediately above `MIN_HEADING_LINES_FOR_MARKDOWN = 2`.

### Method

Edit line 36 region: add a Python-style comment block before the constant assignment.

### Details

Current state (lines 35-37):
```python
MIN_HEADING_LINES_FOR_MARKDOWN = 2
MARKDOWN_HEADING_RE = r"^#{1,6}"
```

After edit:
```python
# NOTE: unvalidated heuristic, pending performance tuning
MIN_HEADING_LINES_FOR_MARKDOWN = 2
MARKDOWN_HEADING_RE = r"^#{1,6}"
```

Note: The simplified one-line format avoids dated references, removes non-ASCII characters, stays consistent with Python comment conventions, and makes the heuristic status clear without making unverifiable historical claims.

## Compatibility considerations

N/A: comment-only addition, no runtime behavior change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

If the comment text proves inaccurate later, the rollback is removing the added comment lines — no code revert needed.

## Risks

- **Risk**: Cross-file pattern inconsistency between REQ-001 and REQ-002. REQ-001 adds a new standalone comment block above a bare constant. REQ-002 extends an existing comment with a semicolon continuation. These produce different visual patterns in the codebase. Future maintainers will see two different styles applied to the same concept ("unvalidated heuristic") across adjacent files → **Mitigation**: both use the same core phrase "unvalidated heuristic, pending performance tuning"; the structural difference reflects the actual state of each target file, not arbitrary design preference.
- **Risk**: The em dash character (`—`) in the original proposed comment text. While modern Python handles Unicode in comments fine, some editors/linters may flag this → **Mitigation**: use ASCII-safe punctuation (semicolon `;` instead of em dash), as REQ-002 correctly does.
- **Risk**: Dated references in comments (e.g., `(2026-08-02 investigation also inconclusive)`) become stale over time → **Mitigation**: avoid specific dates in comment text; use timeless phrasing like "pending performance tuning".
- **Risk**: Asymmetric treatment of `MIN_HEADING_LINES_FOR_MARKDOWN` and `MARKDOWN_HEADING_RE`. Both constants are defined together without comments; adding documentation to one without the other could mislead readers about which constant is "documented" vs "undocumented" → **Mitigation**: documented in Assumptions; outside the scope of this procedure since only REQ-001 targets this constant.
- **Risk**: The claim "no rationale was recoverable" is itself a claim requiring evidence beyond `git log -S`. It doesn't mention searching `requires/`, `plans/`, or other directories → **Mitigation**: use qualified language ("no definitive rationale found") rather than absolute claims.

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
- **Source issue**: issues/done/20260915-200627_rag03_establish-rationale-for-undocumented-chunking-and-crawler-tuning-constants.md (resolved — verify this specific marker hasn't already been applied)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20260916-153123_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260917-093845
- **Related target files**: scripts/rag/ingestion/chunk_splitter.py
