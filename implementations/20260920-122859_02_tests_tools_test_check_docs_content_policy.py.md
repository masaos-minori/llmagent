## Goal
Add unit tests for `check_code_fallback_value_comparison` (REQ-002) to
`tests/tools/test_check_docs_content_policy.py`: one positive case per
detection path (header-shaped, phrase-shaped) and one negative case (an
unrelated table).

## Scope
In scope: add exactly 1 new import name
(`check_code_fallback_value_comparison`) to the existing multi-line
`from tools.check_docs_content_policy import (...)` block, and 3 new test
functions. Out of scope: any change to the 32 existing tests or the
`_doc()` fixture helper.

## Assumptions
The sibling implementation procedure
(`implementations/20260920-122859_01_tools_check_docs_content_policy.py.md`)
has already added `check_code_fallback_value_comparison` to
`tools/check_docs_content_policy.py` before this row is implemented — per
`skills/plan-to-implementation-procedure/workflow.md` Step 3c, rows are
processed in table order (this is `seq` 02, after `seq` 01).

## Design decisions
Follow the existing file's naming convention exactly:
`test_{feature}_detected` / `test_{feature}_not_flagged_for_unrelated_table`
(matching `test_typed_dict_table_detected`/
`test_typed_dict_table_not_flagged_for_unrelated_table`, and
`test_error_handling_table_detected_by_heading`/
`test_error_handling_table_detected_by_header_shape_without_heading` for
the two-path naming precedent). Use two positive tests (one per path) named
`test_code_fallback_value_comparison_header_shaped_detected` and
`test_code_fallback_value_comparison_phrase_shaped_detected`, plus one
negative test
`test_code_fallback_value_comparison_not_flagged_for_unrelated_table`.

## Alternatives considered
A single positive test combining both paths in one fixture doc — rejected:
the existing file's convention (e.g. `check_error_handling_table`'s two
`test_error_handling_table_detected_by_*` tests) keeps each detection path
in its own test, making a future regression in one path distinguishable
from the other.

## Implementation
### Target file
tests/tools/test_check_docs_content_policy.py

### Procedure
1. Add `check_code_fallback_value_comparison` to the existing
   `from tools.check_docs_content_policy import (...)` block (alphabetical
   position: after `check_cli_command_enumeration` and before
   `check_config_file_inventory_table`, matching the block's existing
   alphabetical ordering).
2. Append 3 new test functions at the end of the file (after
   `test_full_json_example_not_flagged_for_short_snippet`):
   ```python
   def test_code_fallback_value_comparison_header_shaped_detected() -> None:
       doc = _doc(
           "| Parameter | Code Fallback Value | Production Value (config/x.toml) |\n"
           "|---|---|---|\n"
           "| max_depth | None | 3 |\n"
       )
       issues = check_code_fallback_value_comparison([doc])
       assert len(issues) == 1
       assert "code-fallback-vs-operational-value comparison" in issues[0].message


   def test_code_fallback_value_comparison_phrase_shaped_detected() -> None:
       doc = _doc(
           "| Crawl Depth | Operational value is 3. Differs from code fallback; "
           "use operational config | `config/crawler.toml` |\n"
       )
       issues = check_code_fallback_value_comparison([doc])
       assert len(issues) == 1
       assert "code-fallback-vs-operational-value comparison" in issues[0].message


   def test_code_fallback_value_comparison_not_flagged_for_unrelated_table() -> None:
       doc = _doc("| Component | Owner |\n|---|---|\n| RAG | rag-team |\n")
       issues = check_code_fallback_value_comparison([doc])
       assert issues == []
   ```

### Method
Two separate `Edit` calls (old_string/new_string): (1) the import-block
addition, (2) the 3 new test functions appended at end of file. Each is
independently revertable.

### Details
Confirm the header-shaped positive test's fixture line does NOT also
independently satisfy the phrase-shaped regex in a way that would make the
`== 1` assertion fail due to a second, unwanted match on the same
line — per the sibling procedure's Design decisions, the implementation's
`continue` after a header-shaped match already prevents this; this test
verifies that guarantee holds. If the assertion fails during
implementation, treat it as a Step 3e validation failure to fix in the
sibling procedure's function, not by loosening this test's assertion.

## Compatibility considerations
Test-only change; no production code behavior affected.

## Security considerations
N/A: test file, no production code path affected.

## Rollback considerations
Revert via `git checkout` on this one file — no data migration or state
change is involved.

## Validation plan
`uv run pytest tests/tools/test_check_docs_content_policy.py -v` — confirm
35 passed (32 existing + 3 new), 0 failed.

## Completion criteria
The 3 new tests exist, follow the file's naming and fixture conventions,
and pass; the 32 existing tests still pass unmodified.

## Out of scope
- The `check_code_fallback_value_comparison` function itself — implemented
  in the sibling `tools/check_docs_content_policy.py` procedure document
  (REQ-001).
- Any change to the `_doc()` fixture or any existing test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` — add unit tests for check_code_fallback_value_comparison
- **Source issue**: issues/20260920-102200_doccfgtool01_detect-code-fallback-vs-operational-value-duplication-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-114319_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-122859
- **Related target files**: tests/tools/test_check_docs_content_policy.py
