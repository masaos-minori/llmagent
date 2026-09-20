## Goal

Add 8 new unit tests (one positive + one negative per new check function) to
`tests/tools/test_check_docs_content_policy.py`, matching the file's existing
one-test-per-category pattern (satisfies `REQ-001` through `REQ-004`'s test
coverage).

## Scope

- In scope: 8 new test functions in `tests/tools/test_check_docs_content_policy.py`,
  and the corresponding import additions from `tools.check_docs_content_policy`.
- Out of scope: any change to the existing 20 tests in this file, or to the
  `_doc()` fixture helper; the actual detection-function implementation (covered by
  `implementations/20260920-090331_01_tools_check_docs_content_policy.py.md` in
  this same pass, which this document assumes is already applied).

## Assumptions

- `implementations/20260920-090331_01_tools_check_docs_content_policy.py.md`
  (seq 01, this same pass) has already added `check_typed_dict_table`,
  `check_cli_argument_table`, `check_error_handling_table`, and
  `check_full_json_example` to `tools/check_docs_content_policy.py` — this
  document's new tests import and call those four functions directly.

## Design decisions

- Each new test pair follows the file's existing convention exactly: a
  `test_<category>_detected` test asserting `len(issues) == 1` (or the expected
  count) and a message substring, paired with a `test_<category>_not_flagged_*`
  test asserting `issues == []` for a case that should not match — see
  `test_field_type_table_detected`/`test_field_type_table_not_flagged_when_short`
  as the closest existing precedent pair.
- Each fixture uses the existing `_doc()` helper with an inline Markdown string,
  matching every existing test in this file — no new fixture helper is introduced.

## Alternatives considered

- Parametrizing the 8 new tests into a single `@pytest.mark.parametrize` test
  function instead of 8 separate functions: rejected — the existing file uses one
  function per test case throughout (no parametrization anywhere in this file),
  and introducing a different test-authoring style for only the new cases would
  make the file inconsistent rather than more concise.

## Implementation

### Target file

tests/tools/test_check_docs_content_policy.py

### Procedure

1. Add `check_typed_dict_table`, `check_cli_argument_table`,
   `check_error_handling_table`, and `check_full_json_example` to the existing
   `from tools.check_docs_content_policy import (...)` block (current lines
   12-25).
2. Append 8 new test functions after `test_guard_detection_recognizes_real_generator_format`
   (current lines 249-269, end of file).

### Method

Import block (replaces current lines 12-25):
```python
from tools.check_docs_content_policy import (
    DocFile,
    check_cli_argument_table,
    check_cli_command_enumeration,
    check_config_file_inventory_table,
    check_ddl_schema_block,
    check_default_value_restatement,
    check_environment_setup_sequence,
    check_error_handling_table,
    check_field_type_table,
    check_full_file_tree,
    check_full_json_example,
    check_index_table,
    check_literal_port_number,
    check_location_mapping,
    check_per_file_description,
    check_typed_dict_table,
)
```

New tests (append at end of file, after `test_guard_detection_recognizes_real_generator_format`):
```python
def test_typed_dict_table_detected() -> None:
    doc = _doc(
        "**Typed dict**\n"
        "\n"
        "| TypedDict | Purpose |\n"
        "|---|---|\n"
        "| CrawlJsonPayload | Typed dictionary for crawl output JSON files |\n"
    )
    issues = check_typed_dict_table([doc])
    assert len(issues) == 1
    assert "TypedDict/DTO field table" in issues[0].message


def test_typed_dict_table_not_flagged_for_unrelated_table() -> None:
    doc = _doc(
        "| Component | Owner |\n"
        "|---|---|\n"
        "| RAG | rag-team |\n"
    )
    issues = check_typed_dict_table([doc])
    assert issues == []


def test_cli_argument_table_detected() -> None:
    doc = _doc(
        "### CLI Arguments\n"
        "\n"
        "| Argument | Description | Default |\n"
        "|---|---|---|\n"
        "| `--file PATH` | Process only one file | all files |\n"
    )
    issues = check_cli_argument_table([doc])
    assert len(issues) == 1
    assert "CLI argument table" in issues[0].message


def test_cli_argument_table_not_flagged_without_cli_heading() -> None:
    doc = _doc(
        "## Notes\n"
        "\n"
        "| Argument | Description | Default |\n"
        "|---|---|---|\n"
        "| `--file PATH` | Process only one file | all files |\n"
    )
    issues = check_cli_argument_table([doc])
    assert issues == []


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


def test_error_handling_table_detected_by_header_shape_without_heading() -> None:
    doc = _doc(
        "## Notes\n"
        "\n"
        "| Case | Action |\n"
        "|---|---|\n"
        "| Tokenization error | Raises TokenizationError |\n"
    )
    issues = check_error_handling_table([doc])
    assert len(issues) == 1
    assert "error-handling table" in issues[0].message


def test_error_handling_table_not_flagged_for_unrelated_table() -> None:
    doc = _doc(
        "## Notes\n"
        "\n"
        "| Component | Owner |\n"
        "|---|---|\n"
        "| RAG | rag-team |\n"
    )
    issues = check_error_handling_table([doc])
    assert issues == []


def test_full_json_example_detected() -> None:
    lines = "\n".join(f'  "field{i}": {i},' for i in range(16))
    doc = _doc(f"```json\n{{\n{lines}\n}}\n```\n")
    issues = check_full_json_example([doc])
    assert len(issues) == 1
    assert "full JSON payload example" in issues[0].message


def test_full_json_example_not_flagged_for_short_snippet() -> None:
    doc = _doc('```json\n{"status": "ok"}\n```\n')
    issues = check_full_json_example([doc])
    assert issues == []
```

### Details

- No new fixture helper — all 8 new tests reuse the existing `_doc()` function
  (current lines 29-30), unchanged.
- `test_error_handling_table_detected_by_heading` and
  `test_error_handling_table_detected_by_header_shape_without_heading` both cover
  `check_error_handling_table`'s two independent signals (heading-based and
  header-shape-based), per that function's Design decisions in seq 01's procedure
  document.
- `test_full_json_example_detected`'s fixture builds a 16-line JSON body
  programmatically (via a generator expression) rather than a hand-typed 16-line
  literal, to make the "above `_MIN_JSON_EXAMPLE_LINES = 15`" boundary condition
  obvious from the test itself rather than requiring the reader to count literal
  lines.

## Compatibility considerations

Purely additive: 4 new imports and 8 new test functions. No existing test's
behavior, fixture, or assertion changes.

## Security considerations

N/A: test file only, no external input or credentials involved.

## Rollback considerations

Revert this file's diff. This document's tests depend on
`implementations/20260920-090331_01_tools_check_docs_content_policy.py.md` (seq 01,
this same pass) already being applied — if seq 01 is reverted, this document's new
tests will fail on import (`ImportError`) rather than on assertion, since the four
functions they import will no longer exist. Revert seq 01 and seq 02 together.

## Validation plan

- `uv run ruff check tests/tools/test_check_docs_content_policy.py` — confirm lint
  compliance (import ordering in particular, since the import block is
  alphabetized).
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v` — confirm all
  20 existing tests still pass and all 8 new tests pass (28 total).

## Completion criteria

- `tests/tools/test_check_docs_content_policy.py` contains the 9 new test
  functions listed above (corrected count — `check_error_handling_table` needs 3
  tests to cover its two independent detection paths plus one negative case, not
  2 like the other three functions; the Goal/Scope's "8 new tests" was an
  undercounting of what the Method section itself already lists), importing the
  four new check functions from `tools.check_docs_content_policy`.
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v` reports 32
  passed (23 existing + 9 new), 0 failed.

## Out of scope

- Any change to the 20 existing tests in this file.
- The detection-function implementation itself (covered by seq 01, this same
  pass).
- Updating `tools/TOOL_DESCRIPTIONS.md` or `routing.md` (covered by seq 03/seq 04,
  this same pass).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-091800 | 20260920-091800 | Added 4 imports + 9 test functions (corrected count — see Completion criteria correction). Depends on seq 01 (already applied). |
| 2 | Add or update tests per Validation plan | Completed | 20260920-091800 | 20260920-091800 | N/A: this document's Implementation step 1 is itself the test addition |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-091800 | 20260920-091800 | `uv run ruff format`/`ruff check` clean (import block correctly alphabetized after `ruff --fix`). `uv run pytest tests/tools/test_check_docs_content_policy.py -v`: 32 passed (23 existing + 9 new), 0 failed. No mypy/bandit required for a test file per this repository's convention. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-091800 | 20260920-091800 | N/A: test-only file, no documentation update in scope |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (unit test coverage for the four new detection functions)
- **Source issue**: issues/done/20260920-084638_docreftool01_add-a-docs-checker-for-implementation-reference-content.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-085652_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-090331
- **Related target files**: tests/tools/test_check_docs_content_policy.py
