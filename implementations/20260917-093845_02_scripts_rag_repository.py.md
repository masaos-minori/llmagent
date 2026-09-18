## Goal

Add an explicit "unvalidated heuristic, pending performance tuning" marker above `_MAX_FTS_TOKENS = 20` in `scripts/rag/repository.py` (line 31), extending its existing "prevents query explosion" comment rather than replacing it. Note: the source issue (`issues/done/20260915-200627_rag03_establish-rationale-for-undocumented-chunking-and-crawler-tuning-constants.md`) is under `issues/done/` — verify whether this specific marker has already been applied before executing. Per REQ-002; AC-1, AC-4.

## Scope

- Extend the existing comment on line 30 to include the heuristic marker
- No behavior change — comment-only addition

## Assumptions

- The constant's value (20) remains unchanged — this Plan does not alter any constant value
- The existing comment "prevents query explosion" is accurate and should be preserved alongside the new marker
- The prior investigation attempt (`git log -S"_MAX_FTS_TOKENS = 20"` earliest commit 2026-05-26 initial commit; `issues/done/20260802-080020_rag_02_08_usage_table_errors_and_fts_token_rationale.md` filed 2026-08-02) found no definitive rationale and remains unresolved
- The source issue is under `issues/done/`; if it was resolved by adding heuristic markers to ALL seven constants, this procedure may be redundant — verify before executing

## Design decisions

- Extend the existing comment on line 30 rather than adding a new comment block above the constant — this matches the pattern the source issue specifies ("extending its existing 'prevents query explosion' comment")

## Alternatives considered

- Adding a separate comment block above the constant: rejected because the source issue explicitly prefers extending the existing comment

## Implementation

### Target file

`scripts/rag/repository.py`

### Procedure

Extend the existing comment on line 30 to append the heuristic marker.

### Method

Edit line 30: modify the existing single-line comment to include the heuristic marker text after the existing content.

### Details

Current state (lines 30-31):
```python
# Maximum number of tokens to include in an FTS5 query (prevents query explosion)
_MAX_FTS_TOKENS = 20
```

After edit:
```python
# Maximum number of tokens to include in an FTS5 query (prevents query explosion);
# NOTE: unvalidated heuristic, pending performance tuning
_MAX_FTS_TOKENS = 20
```

Note: The simplified two-line format avoids dated references, removes non-ASCII characters, stays consistent with Python comment conventions, and makes the heuristic status clear without making unverifiable historical claims.

## Compatibility considerations

N/A: comment-only addition, no runtime behavior change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

If the comment text proves inaccurate later, the rollback is reverting the comment to its original form — no code revert needed.

## Risks

- **Risk**: Multi-line comment format has no precedent in this file — adjacent constant `_FTS_KEEP_POS` at line 32 uses single-line comments. Future maintainers may question whether the two lines should be consolidated → **Mitigation**: keep the two-line format minimal (original comment + one NOTE line) to reduce ambiguity.
- **Risk**: The phrase "no recorded rationale found" is itself a claim requiring evidence beyond `git log -S`. It doesn't mention searching `requires/`, `plans/`, or other directories → **Mitigation**: use qualified language ("no definitive rationale found") rather than absolute claims.
- **Risk**: Dated references in comments (e.g., `(2026-08-02 investigation also inconclusive)`) become stale over time → **Mitigation**: avoid specific dates in comment text; use timeless phrasing like "pending performance tuning".
- **Risk**: Non-ASCII characters (em dash `—`) in Python comments may cause issues with some editors/linters → **Mitigation**: use ASCII-safe punctuation (semicolon `;` instead of em dash).

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/repository.py | Lint/type check | `uv run ruff format`, `uv run ruff check`, `uv run mypy` | Pass with no new findings |
| scripts/rag/repository.py | Manual diff review | `git diff` | Only comment lines modified, no value line changed |

## Completion criteria

- [ ] AC-1: An explicit "unvalidated heuristic" marker exists above `_MAX_FTS_TOKENS` at its definition site, extending the existing comment
- [ ] AC-4: The constant value was not changed (verified by `git diff`)

## Out of scope

- Changing `_MAX_FTS_TOKENS`'s value
- Adding tests for this constant
- Editing other constants in this file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add heuristic marker above _MAX_FTS_TOKENS | Completed | 20260918-171254 | 20260918-171254 |  |
| 2 | Run validation sequence (ruff/mypy) | Completed | 20260918-171254 | 20260918-171254 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20260915-200627_rag03_establish-rationale-for-undocumented-chunking-and-crawler-tuning-constants.md (resolved — verify this specific marker hasn't already been applied)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20260916-153123_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260917-093845
- **Related target files**: scripts/rag/repository.py