## Goal
Add unit tests for the 6 new check functions (true-positive + false-positive
each) and a guard-detection regression test using the real
`GUARD_START_MCP`/`GUARD_START_DEPLOYMENT`-shaped format (`REQ-006`).

## Scope
In scope: new test functions in this one file, following its existing
`_doc()`-fixture pattern. Out of scope: modifying the 2 pre-existing guard tests
(they must keep passing unmodified); testing any check function not added by
this Plan.

## Assumptions
- File structure unchanged since the Plan was written — re-confirmed: `_doc()`
  helper (lines 22-23), one test per existing check function (lines 26-108+),
  2 existing guard-exemption tests using the synthetic bare-string format
  (lines 109-132).
- **Correction carried from Step 3a** (recorded in `plans/done/20260919-104809_plan.md`'s
  Blocker Log): the 2 existing guard tests (`test_literal_port_number_exempted_inside_auto_generated_block`,
  `test_literal_port_number_flagged_outside_auto_generated_block`) do NOT
  exercise the real guard format and must not be treated as already satisfying
  REQ-006 — this document's new regression test is required in addition to
  them, not a duplicate of them.

## Design decisions
Add exactly 13 new test functions: 2 per new check function (true-positive +
false-positive) × 6 checks = 12, plus 1 new guard-format regression test using
the real `GUARD_START_MCP` string verbatim (imported from
`tools.generate_reference_table` rather than hand-typed, so the test breaks if
that module's constant ever changes shape) — following the existing file's
one-function-per-behavior naming convention (`test_<check>_detected` /
`test_<check>_not_flagged_<reason>`).

## Alternatives considered
Parametrizing all 6 new checks' true/false-positive pairs into a single
`pytest.mark.parametrize` table was considered, but rejected — the existing
file uses one plain function per case throughout (no parametrization anywhere),
and matching that convention keeps this addition consistent with the file's
established style rather than introducing a new one.

## Implementation
### Target file
tests/tools/test_check_docs_content_policy.py

### Procedure
1. Add the `from tools.check_docs_content_policy import (...)` import line's 6
   new function names (extending the existing import block, lines 12-19).
2. Add `import` of `GUARD_START_MCP` from `tools.generate_reference_table` for
   the new regression test.
3. Add 12 new test functions (2 per new check), placed after the existing
   `check_literal_port_number` tests (after line 204, matching this file's
   append-at-end convention).
4. Add 1 new guard-format regression test
   (`test_guard_detection_recognizes_real_generator_format`), asserting that a
   doc using the real `GUARD_START_MCP` string (not the synthetic bare one) is
   exempted by every guard-aware check function (the 3 newly guard-aware ones
   plus `check_literal_port_number`).

### Method
Direct code edit (`Edit` tool), extending the existing file's plain-function
test pattern — no new fixtures beyond the existing `_doc()` helper.

### Details
- True-positive/false-positive fixture content for each of the 6 new checks
  must match seq 01's actual implementation exactly (read that document's
  Details section, and the actual committed function bodies, before writing
  each fixture) — do not guess a pattern that the implementation does not
  actually match.
- `test_guard_detection_recognizes_real_generator_format`: construct a doc
  containing `GUARD_START_MCP` (imported, not hand-typed) followed by content
  that would trip `check_full_file_tree`, `check_index_table`, and
  `check_location_mapping` if unguarded, then assert all three (plus
  `check_literal_port_number`) return no issues for that content.
- Do not modify `test_literal_port_number_exempted_inside_auto_generated_block`
  or `test_literal_port_number_flagged_outside_auto_generated_block` (lines
  109-132) — they must pass unmodified, verifying the prefix-based fix does not
  regress the synthetic-format case.
- Each false-positive fixture must be a "legitimately short, non-mechanical"
  example per the source issue's own caution (e.g. a 2-row table for
  `check_field_type_table`'s false-positive case, matching seq 01's stated
  false-positive-avoidance threshold).

## Compatibility considerations
Additive test-only change — no existing test function is modified or removed
(beyond the import-line extension, which only adds names).

## Security considerations
N/A: test code only, no credentials or runtime behavior.

## Rollback considerations
`git checkout -- tests/tools/test_check_docs_content_policy.py` reverts this
row independently; since it only adds tests (imports new names that must exist
in seq 01's target), reverting this file alone without reverting seq 01 would
leave the new tests simply absent (no breakage), and reverting seq 01 alone
without this file would break these new tests' imports — the two rows should be
rolled back together if either is reverted.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v` — all tests
  (existing + new) pass.
- `uv run ruff check tests/tools/test_check_docs_content_policy.py`
- `uv run mypy tests/tools/test_check_docs_content_policy.py`

## Completion criteria
- 12 new true/false-positive tests (2 per new check) and 1 new guard-format
  regression test exist and pass.
- The 2 pre-existing guard-exemption tests pass unmodified.
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v` is fully
  green.

## Out of scope
Testing any pre-existing check function's behavior beyond the guard-format
regression test; parametrized test restructuring.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260919-121244 | 20260919-121244 | Depends on seq 01's actual function implementations |
| 2 | Add or update tests per Validation plan | Completed | 20260919-121244 | 20260919-121244 | This document's own Target file IS the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260919-121244 | 20260919-121244 | `uv run pytest tests/tools/test_check_docs_content_policy.py -v` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260919-121244 | 20260919-121244 | N/A: test file only |

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
- **Requirement ID**: REQ-006 (unit tests for each new check + guard-format regression test)
- **Source issue**: issues/done/20260918-130159_docschk01_extend-check_docs_content_policy-instead-of-new-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-104809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114519
- **Related target files**: tests/tools/test_check_docs_content_policy.py