# Implementation Procedure — tests/mcp_servers/mdq/test_db_grep.py

## Goal

Pin the grep behavior that REQ-006 changes: the reported line definition, the returned context,
multiple matches per chunk, multiline semantics, explicit zero context, and the limit applied to the
context-inclusive text.

## Scope
**Release unit**: grep-context-and-line-numbers

Requirement implemented: REQ-006 (grep returns the requested context and reports the documented line
definition). Acceptance criterion: AC-5.

## Assumptions
- The reported line is the first stored content line, `start_line + 1 + k` (UNK-03, resolved by the
  owner on 20261127).
- `test_line_number_for_match_on_later_line` (Line 108) asserts `match.line_number == 4` at Line 119.
  With the fixture's default `start_line = 1` (`_insert_chunk`, Line 38) the new definition gives the
  same number, so the assertion is not wrong — it is rewritten to state the definition, and a case
  where the two definitions differ is added.
- No test currently asserts returned context because none is returned, so those cases are new.

## Design decisions
- The characterization of the current behavior is written first (Plan Phase 1) and then replaced, so
  the change is pinned by tests rather than inferred.
- The new cases use an explicit `start_line` argument so the definition is exercised independently of
  the fixture default.

## Alternatives considered
- Leaving Line 119 as-is because it still passes: rejected, because it pins the chunk-relative formula
  by coincidence and would not detect a regression to that formula.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_db_grep.py`

### Procedure
Rewrite the line-number assertion to the documented definition and add the context, multiple-match,
multiline, zero-context, and context-inclusive-limit cases.

### Method
Addition to `TestFindGrepMatch` (Line 55) and `TestGrepDocs` (Line 122); the existing fixture and
helper are reused unchanged.

### Details
- `test_line_number_for_match_on_later_line` Line 108: assert `start_line + 1 + k` and add
  `test_line_number_from_stored_start_line` (new) with an explicit `start_line` and content whose
  first stored line is not the file line.
- `test_only_first_match_in_row_is_returned` Line 97: replaced by
  `test_multiple_matches_in_one_chunk_are_returned` (new).
- Add `test_context_before_and_after_are_returned` (new) — the requested context is returned,
  including an explicit zero.
- Add `test_explicit_zero_context_is_honored` (new) — zero is not replaced by the configured default.
- Add `test_limit_applies_to_context_inclusive_text` (new) — `max_chars` bounds the context-inclusive
  text, not the match alone.
- Add `test_multiline_pattern_semantics` (new) — the documented line-anchored semantics.

## Compatibility considerations
- The file is a characterization suite; the assertions that change are listed in the Plan's
  predictable fallout check. No other test file asserts the grep line number.

## Security considerations
- N/A: test-only change; no path or authorization behavior.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_db_grep.py` — the new cases pass against the Phase 5
  implementation and the rewritten line-number assertion states the definition.
- Baseline before any change: 159 passed for the five-file subset (re-run 20261127).

## Completion criteria
- The reported line matches the source file for a section whose stored content begins at its first
  content line, and matches the documented definition for a section stored with stripping.
- Returned context, multiple matches, multiline semantics, explicit zero, and the
  context-inclusive limit are each pinned by a test.

## Out of Scope
- The implementation change in `scripts/mcp_servers/mdq/db_grep.py` (procedure seq 05).
- The context default resolution in `scripts/mcp_servers/mdq/mdq_service.py` (procedure seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pin the current chunk-relative line number, missing context, and one-match-per-chunk behavior | Pending | — | — | Phase 1, before the production change |
| 2 | Rewrite the line-number assertion to `start_line + 1 + k` | Pending | — | — | REQ-006, AC-5 |
| 3 | Add the returned-context, multiple-match, multiline, and zero-context cases | Pending | — | — | REQ-006, AC-5 |
| 4 | Assert the limit applies to the context-inclusive text | Pending | — | — | REQ-006, AC-5 |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | UNK-03: the line-number offset for a section whose content had leading blank lines stripped at index time is not recoverable from the stored row. Resolved by the owner on 20261127 with the first-stored-content-line definition. | Yes | 20261127 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006 (grep context, line definition, multiple matches, explicit zero,
  context-inclusive limit)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `tests/mcp_servers/mdq/test_db_grep.py`
