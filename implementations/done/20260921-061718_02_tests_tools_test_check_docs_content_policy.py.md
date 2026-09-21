## Goal
Add three regression tests to `tests/tools/test_check_docs_content_policy.py`: two
false-positive regression guards reproducing the confirmed cross-section cases, and
one true-positive regression guard confirming `check_error_handling_table()`'s
section-scoping still detects a genuinely same-section table (the existing test
originally cited for this purpose was found, during adversarial verification, to
bypass the heading-window path entirely).

## Scope
In scope: three new test functions in `tests/tools/test_check_docs_content_policy.py`
(REQ-004 of `plans/20260920-205406_plan.md`, as corrected during this Plan's own
Step 3a investigation).
Out of scope: modifying `tools/check_docs_content_policy.py` itself (covered by this
Plan's Row 1, a separate implementation procedure document); modifying any existing
test.

## Assumptions
- Row 1 (`tools/check_docs_content_policy.py`) is implemented before or alongside
  this row, since all three new tests depend on the section-scoping fix Row 1 adds —
  without it, the two false-positive regression tests ((a) and (b)) would fail.
- `test_error_handling_table_detected_by_heading` (confirmed at lines 329-339) and
  `test_config_file_inventory_table_detected` (confirmed at lines 193-197) are left
  unmodified — per the source Plan's correction, only the former's claimed purpose
  (an AC-2 true-positive guard) was found inaccurate; the test itself is not wrong or
  redundant and must keep passing unchanged.

## Design decisions
- Reuse the existing `_doc(text, rel_path="fixture.md")` helper (confirmed at line
  34-35) for all three new tests, consistent with every other test in this file.
- For regression test (c) (the corrected true-positive guard), use a table header
  shaped `| Field | Description |` — deliberately NOT matching
  `_ERROR_ACTION_TABLE_HEADER_RE` (`^\s*\|\s*(?:Case|Scenario)\s*\|(?:.*\|)?\s*Action\s*\|`)
  so the test actually exercises `check_error_handling_table()`'s heading-window/
  section-scoping backward-search path (lines 705-711), not the unconditional
  Case/Action-shape path (line 688) that made the original test misleading.

## Alternatives considered
- Renaming or rewriting the existing `test_error_handling_table_detected_by_heading`
  to use a non-Case/Action table shape instead of adding a new test: rejected — that
  test is itself a valid, passing regression guard for the unconditional
  `_ERROR_ACTION_TABLE_HEADER_RE` path (a real, separate detection rule this Plan does
  not touch); repurposing it would remove coverage for that unconditional path while
  only incidentally adding heading-window coverage. Adding a new, correctly-scoped
  test keeps both code paths independently covered.

## Implementation
### Target file
`tests/tools/test_check_docs_content_policy.py`

### Procedure
1. Add `test_error_handling_cross_section_false_positive` (near
   `test_error_handling_table_detected_by_heading`, lines 329-339, to group with the
   other `check_error_handling_table()` tests): a document with `### Error Type
   Design` immediately followed by `### Runtime Parameter Generation` and then a
   plain (non-Case/Action) table within 10 lines of the `Error Type Design` heading
   but directly under `Runtime Parameter Generation` — assert `issues == []`.
2. Add `test_error_handling_table_still_detected_within_same_section` immediately
   after it: a document with a matching `### Error Handling` heading directly above a
   plain `| Field | Description |`-shaped table (no intervening heading, no
   Case/Action shape) — assert the table is still flagged.
3. Add `test_config_file_inventory_cross_section_false_positive` (near
   `test_config_file_inventory_table_detected`/`test_config_file_inventory_table_not_flagged_without_heading`,
   lines 193-203): a document with `### Configuration Fields` immediately followed by
   an unrelated `### Notes` heading and then a config-shaped bullet within 10 lines of
   `Configuration Fields` but directly under `Notes` — assert `issues == []`.

### Method
Direct file edit (`Edit` tool) — append three new test functions near their
respective existing sibling tests; no change to any existing test or the `_doc()`
helper.

### Details
Existing sibling tests for placement reference (confirmed via Read):
```python
def test_config_file_inventory_table_detected() -> None:
    doc = _doc("### Configuration Fields\n\n- `port` — HTTP listening port\n")
    issues = check_config_file_inventory_table([doc])
    assert len(issues) == 1
    assert "config-file inventory" in issues[0].message


def test_config_file_inventory_table_not_flagged_without_heading() -> None:
    doc = _doc("## Notes\n\n- `port` — an example field name mentioned in passing\n")
    issues = check_config_file_inventory_table([doc])
    assert issues == []
```
```python
def test_error_handling_table_detected_by_heading() -> None:
    doc = _doc(
        "### Error Handling\n"
        "\n"
        "| Case | Action |\n"
        "|---|---|\n"
        "| Tokenization error | Raises TokenizationError |\n"
    )
    issues = check_error_handling_table([doc])
    assert len(issues) == 1
    assert "error-handling table" in issues[0].message
```

New tests to add (illustrative structure — write exact final code during
implementation, confirming line counts stay within `_HEADINGS_WINDOW` (10) for the
"nearby" heading in each case):
```python
def test_error_handling_cross_section_false_positive() -> None:
    doc = _doc(
        "### Error Type Design\n"
        "\n"
        "### Runtime Parameter Generation\n"
        "\n"
        "| Field | Description |\n"
        "|---|---|\n"
        "| temperature | Sampling temperature |\n"
    )
    issues = check_error_handling_table([doc])
    assert issues == []


def test_error_handling_table_still_detected_within_same_section() -> None:
    doc = _doc(
        "### Error Handling\n"
        "\n"
        "| Field | Description |\n"
        "|---|---|\n"
        "| error_code | Numeric error code |\n"
    )
    issues = check_error_handling_table([doc])
    assert len(issues) == 1
    assert "error-handling table" in issues[0].message


def test_config_file_inventory_cross_section_false_positive() -> None:
    doc = _doc(
        "### Configuration Fields\n"
        "\n"
        "### Notes\n"
        "\n"
        "- `port` — an example field name mentioned in passing\n"
    )
    issues = check_config_file_inventory_table([doc])
    assert issues == []
```
Confirm each fixture's line count places the "nearby" heading within
`_HEADINGS_WINDOW` (10 lines) of the table/bullet row during implementation — the
illustrative fixtures above are short enough by construction, but re-count exact line
numbers against the actual `_HEADINGS_WINDOW` value (confirmed as `10` at line 41 of
`tools/check_docs_content_policy.py`) before finalizing.

## Compatibility considerations
Additive only — no existing test is modified, so no existing test's pass/fail outcome
changes.

## Security considerations
N/A: test-only change, no production code path affected.

## Rollback considerations
Trivially revertable: removing the three new test functions leaves every existing
test in this file unaffected.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v` — full file
  (REQ-004, REQ-005; AC-1, AC-2, AC-3 of `plans/20260920-205406_plan.md`), run once
  Row 1 has also landed.
- `uv run ruff check tests/tools/test_check_docs_content_policy.py` /
  `uv run mypy tests/tools/test_check_docs_content_policy.py`.

## Completion criteria
- `test_error_handling_cross_section_false_positive` passes, proving AC-1 for
  `check_error_handling_table()`.
- `test_config_file_inventory_cross_section_false_positive` passes, proving AC-1 for
  `check_config_file_inventory_table()`.
- `test_error_handling_table_still_detected_within_same_section` passes, proving AC-2
  for `check_error_handling_table()` via a test that actually exercises the
  heading-window path (unlike the pre-existing, misleadingly-named test).
- Every pre-existing test in this file (including
  `test_error_handling_table_detected_by_heading` and
  `test_config_file_inventory_table_detected`, unmodified) still passes.

## Out of scope
- Implementing the section-scoping fix itself — covered by this Plan's Row 1
  (`tools/check_docs_content_policy.py`), a separate implementation procedure
  document.
- Renaming or otherwise modifying `test_error_handling_table_detected_by_heading` —
  left as-is per Design decisions/Alternatives considered.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_error_handling_cross_section_false_positive` and `test_error_handling_table_still_detected_within_same_section` | Completed | — | 20260921-194455 |  |
| 2 | Add `test_config_file_inventory_cross_section_false_positive` | Completed | — | 20260921-194455 |  |
| 3 | Run `uv run pytest tests/tools/test_check_docs_content_policy.py -v` (after Row 1 lands) and lint/type checks | Completed | — | 20260921-194455 |  |

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
- **Requirement ID**: REQ-004 (false-positive and true-positive regression tests, corrected during this Plan's Step 3a)
- **Source issue**: issues/20260920-175121_dcpwin01_heading-window-heuristic-causes-false-positives-after-edits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-205406_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260921-061718
- **Related target files**: tests/tools/test_check_docs_content_policy.py