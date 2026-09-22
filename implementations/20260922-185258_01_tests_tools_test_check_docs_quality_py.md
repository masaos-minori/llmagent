## Goal

Replace the exact-count assertion in `tests/tools/test_check_docs_quality.py` with a more robust approach that gives future editors actionable failure messages when the content-similarity baseline drifts.

## Scope

In scope: replacing/augmenting the exact-count assertion at line 292 with either a tolerance/trend check, diagnostic-on-failure output, or set-based snapshot (Approach 3 preferred per Plan). Out of scope: modifying `check_docs_quality.py`'s detection logic; reverting the already-applied baseline update (206→205); modifying the sibling test `test_no_new_false_positives_on_full_docs_tree` unless investigation finds it shares the same fragility.

## Assumptions

- The chosen approach (tolerance/trend check, diagnostic-on-failure, or set-based snapshot) best fits `check_docs_quality.py`'s actual output structure is an implementation-time investigation, not decided here.
- The already-applied baseline update (206→205) for the 2026-09-20 batch is correct and landed; this issue is about preventing the *next* occurrence of the same late-discovered, opaque failure.
- The sibling test `test_no_new_false_positives_on_full_docs_tree` does not share the same fragility unless investigation confirms it does.

## Design decisions

- Approach 3 (set-based snapshot) is preferred over Approaches 1 and 2 because: (1) it catches both increases and decreases in duplication (unlike Approach 1's trend-only check), (2) it provides clear per-pair diagnostics on failure (unlike Approach 2's verbose output), and (3) it naturally tolerates the count staying the same while the underlying pairs change (a blind spot the current count-only assertion has).
- The snapshot should use `frozenset[str]` for immutability and hashability, matching the pattern already used elsewhere in this test file (`EXPECTED_WITHIN_FILE_PAIRS`).
- On assertion failure, the error message should show added and removed pairs separately so a future editor can immediately see what changed without manually re-running `check_docs_quality.py`.

## Alternatives considered

- Approach 1 (tolerance/trend check): simpler but allows silent degradation if duplication decreases unexpectedly. Rejected in favor of Approach 3.
- Approach 2 (diagnostic-on-failure): keeps exact count but adds verbosity on failure. Less clean than Approach 3's set diff.

## Implementation

### Target file

tests/tools/test_check_docs_quality.py

### Procedure

1. Read `tools/check_docs_quality.py`'s content-similarity detection output format to determine how to extract file:section pairs from the output (REQ-002). Confirm the regex pattern used to parse lines like:
   ```
   [WARNING] <file>:<line> — Content similarity detected between sections '<heading_a>' and '<heading_b>'
   ```

2. Verify the sibling test `test_no_new_false_positives_on_full_docs_tree` does not share the same fragility by checking its assertion shape (UNK-01). If it also uses an exact-count assertion, note as a Plan Gap.

3. Replace the exact-count assertion at line 292 with a set-based snapshot comparison:
   ```python
   # Extract all file:section pairs from output
   current_pairs: set[str] = set()
   for line in output.split("\n"):
       m = re.search(
           r"\[WARNING\] ([^:]+):\d+ — Content similarity detected between "
           r"sections '([^']+)' and '([^']+)'",
           line,
       )
       if m:
           file_path = m.group(1)
           section_a = m.group(2)
           section_b = m.group(3)
           current_pairs.add(
               f"{file_path}:{repr(section_a)} <-> {repr(section_b)}"
           )

   EXPECTED_WITHIN_FILE_PAIRS: frozenset[str] = frozenset([
       # ... populate from post-2026-09-20-batch output ...
   ])

   assert current_pairs == EXPECTED_WITHIN_FILE_PAIRS, (
       f"Within-file content-similarity pairs changed:\n"
       f"Added: {current_pairs - EXPECTED_WITHIN_FILE_PAIRS}\n"
       f"Removed: {EXPECTED_WITHIN_FILE_PAIRS - current_pairs}"
   )
   ```

4. Generate and commit the current snapshot of file:section pairs (post-2026-09-20-batch) as the new baseline. Run:
   ```bash
   uv run python tools/check_docs_quality.py --only content_similarity | grep 'between sections'
   ```
   Then extract pairs from the output and populate `EXPECTED_WITHIN_FILE_PAIRS`.

### Method

Two separate `Edit` operations: (1) add the pair extraction loop and `EXPECTED_WITHIN_FILE_PAIRS` constant before the assertion, (2) replace the old `assert within_file_count == 205` assertion with the set equality comparison. Each is independently revertable.

### Details

Before finalizing, confirm the regex pattern used to parse `check_docs_quality.py` output lines. The pattern must match the exact format produced by the tool's `Content similarity detected between sections` message. If the output format differs from the assumed pattern, adjust the regex accordingly. Also confirm the expected pair count from the current `docs/` tree — if it differs from the Plan's original baseline number (206 or 205), update the expected count/pairs to match current reality rather than the Plan's original baseline number, and note the discrepancy in this document's Execution Status Notes.

## Compatibility considerations

Test-only change; no production code behavior affected. The `frozenset[str]` type annotation requires Python 3.9+ (already satisfied by this project's Python 3.13 target).

## Security considerations

N/A: test file only, no production code path affected.

## Rollback considerations

Revert via `git checkout` on this one file — no data migration or state change is involved. Both Edit operations are independently revertable.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/tools/test_check_docs_quality.py | Unit tests for TestRegressionFullDocsTree | `uv run pytest tests/tools/test_check_docs_quality.py -v` | All tests pass |
| tests/tools/test_check_docs_quality.py | Lint/type checks | `uv run ruff check tests/tools/test_check_docs_quality.py && uv run mypy tests/tools/test_check_docs_quality.py` | No errors |
| tests/tools/test_check_docs_quality.py | Synthetic regression test (temporarily introduce duplication) | Manual local test run | Assertion catches the duplication with clear diagnostic message |

## Completion criteria

The set-based snapshot assertion exists, passes against the current `docs/` tree, and produces a clear per-pair diff on mismatch; the 17 existing tests still pass unmodified.

## Out of scope

- The cross-file comparison pass itself — implemented in the sibling `tools/check_docs_quality.py` procedure document (REQ-001, REQ-003).
- Any change to the 17 existing tests' bodies or `_make_doc_file`'s default behavior.
- Modifying the sibling test `test_no_new_false_positives_on_full_docs_tree` unless investigation finds it shares the same fragility.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Pre-applied: set-based snapshot assertion already present in source |
| 2 | Add or update tests per Validation plan | Completed | — | — | No test changes needed beyond assertion replacement |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 17 existing tests pass unmodified |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | N/A: test-only change, no docs mapping |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260920-175221_docqtest01_hardcoded-content-similarity-baseline-test-is-fragile-to-docs-edits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-210722_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-185258
- **Related target files**: tests/tools/test_check_docs_quality.py
