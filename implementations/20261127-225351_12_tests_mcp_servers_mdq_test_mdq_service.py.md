# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_service.py

## Goal

Rewrite the outcome-text assertions for `partial_success` (new) and the all-files-failed tool error,
move the size-limit tests onto the byte unit, and add the ASCII, Japanese, emoji, and BOM cases.

## Scope
**Release unit**: per-file-outcome-and-counters (the size-limit cases are the part that belongs to
release unit `byte-limit-key-rename`)

Requirements implemented: REQ-001 (a skipped or failed file is never counted as `indexed`), REQ-003
(`partial_success` (new) and the all-files-failed tool error), REQ-004 (the byte unit).
Acceptance criteria: AC-1, AC-2, AC-3.

## Assumptions
- The seven `text == "Indexing complete"` assertions split as the Plan records: two skip-only runs,
  two all-failed runs, three runs with committed work.
- The three runs with committed work keep the success text; the two skip-only runs report the skip
  unit; the two all-failed runs become the tool error.
- Eleven unpacking call sites of `parse_markdown()` in this file are rewritten when the parser return
  contract changes (procedure seq 04).

## Design decisions
- The outcome-text assertions are rewritten in Phase 1, before the production change, so the new text
  is pinned rather than inferred from the implementation.
- The size-limit tests assert the byte unit through the service attribute, not through the model
  field, so the unit is visible at the enforcement point.

## Alternatives considered
- Keeping the success-text assertions and adding new ones: rejected, because the existing assertions
  would fail once a mixed run reports `partial_success` (new).

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_service.py`

### Procedure
Rewrite the seven outcome-text assertions, move the size-limit assertions to the byte unit, and add
the encoding cases and the mixed and all-failed cases.

### Method
Assertion-level changes in existing tests plus new tests; the fixtures (`service`, `md_file`,
`md_dir`) are reused unchanged.

### Details
- `test_index_paths_skips_nonexistent` Line 505 and `test_index_paths_skips_non_md_file` Line 517:
  assert the skip unit and the skip status rather than the success text.
- `test_index_paths_records_failed_count_on_file_error` Line 548 and
  `test_index_paths_records_failed_count_on_directory_error` Line 565: assert the tool error for an
  all-failed run instead of the success text.
- `test_index_paths_md_file_returns_complete` Line 531, `test_index_paths_directory_returns_complete`
  Line 540, `test_index_paths_delegates` Line 808: keep the success text and add the file-level
  counters.
- Add `test_mixed_run_reports_partial_success` (new) for a directory with committed and skipped files.
- `test_oversized_file_is_skipped_with_warning` Line 118: the asserted message becomes the byte unit;
  add `test_byte_gate_and_character_limit_differ` (new) with ASCII, Japanese, emoji, and BOM content.

## Compatibility considerations
- These are the pinned assertions listed in the Plan's predictable fallout check; they change in the
  same release unit as the implementation.
- `tests/mcp_servers/test_mdq_audit.py` is not a row of this Plan and stays unaffected because the
  existing counter keys keep their path-level meaning (UNK-06).

## Security considerations
- N/A: test-only change; no path or authorization behavior.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py` — the outcome text, the tool error, the
  byte unit, and the encoding cases.
- Baseline before any change: 159 passed for the five-file subset, 416 passed and 1 skipped for the
  whole `tests/mcp_servers/mdq/` suite (re-run 20261127).

## Completion criteria
- A mixed run reports `partial_success` (new) and an all-failed run reports the tool error.
- The size-limit tests measure bytes, and the ASCII, Japanese, emoji, and BOM cases pass.
- No counter reports a skipped or failed file as committed.

## Out of Scope
- The implementation changes in `scripts/mcp_servers/mdq/indexer.py` (seq 02) and
  `scripts/mcp_servers/mdq/mdq_service.py` (seq 06).
- The mixed-success directory and retry-after-failure cases, which are in
  `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` (companion of seq 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pin the current counter unit and outcome text | Pending | — | — | Phase 1, before the production change |
| 2 | Rewrite the seven outcome-text assertions for `partial_success` (new) and the tool error | Pending | — | — | REQ-003, AC-2 |
| 3 | Move the size-limit tests onto the byte unit and add the encoding cases | Pending | — | — | REQ-004, AC-3 |
| 4 | Rewrite the eleven `parse_markdown()` unpacking call sites | Pending | — | — | seq 04 contract change |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (tally from the DTO status), REQ-003 (`partial_success` (new) and the
  all-files-failed tool error), REQ-004 (byte unit)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_service.py`
