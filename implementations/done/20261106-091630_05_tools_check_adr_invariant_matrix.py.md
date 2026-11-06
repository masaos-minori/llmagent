## Goal
Make `tools/check_adr_invariant_matrix.py` render its JSON output and declare its `--format` option through the shared module, with byte-identical output, unchanged exit codes, and the symbols that `tools/generate_reference_table.py` imports kept (`REQ-005`; `REQ-006`: batch 1).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `render_json`, the `--format` argument, and the import block.
- Out of scope: the matrix and body checks, `collect_issues`, the default text path (`report_and_exit`).

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file has the guarded bootstrap and imports `Issue, report_and_exit` from `tools._docs_consistency_lib`; its `render_json` and `main` are identical in shape to those of `tools/check_adr_reference.py` (keys `file`, `line_no`, `severity`, `message`, sorted by `(file, line_no)`, `choices=["json"]`, `default=None`, return `1` when any issue is `ERROR`). `tools/generate_reference_table.py` imports `ADR_INDEX`, `_matrix_rows`, `_read_lines`, and `_split_row` from this module inside `_invariant_coverage_entries`, and `tests/tools/test_generate_reference_table.py` patches `ADR_INDEX` on it; those names, `REPO_ROOT`, and `collect_issues` MUST stay.
- `tests/tools/test_check_adr_invariant_matrix.py` calls `collect_issues()` and `main(["--format", "json"])` and asserts `"severity": "ERROR"` in the output; it does not import `render_json`, so no test edit is needed. Pre-commit runs it as `uv run python -m tools.check_adr_invariant_matrix`.
- Overlap judgment: no other open Plan targets this file.
- The shared symbols come from the earlier-`seq` sibling procedure for `tools/_report.py`.

## Design decisions
- Same migration shape as `tools/check_adr_reference.py`: delete the local `render_json`, call the shared one with `PROFILE_ISSUE` over converted issues, declare `--format` through `add_format_argument`.

## Alternatives considered
- N/A: identical to the sibling migration.

## Implementation
### Target file
`tools/check_adr_invariant_matrix.py`

### Procedure
1. Add `from tools._report import PROFILE_ISSUE, add_format_argument, from_issue, render_json` after the existing `tools._docs_consistency_lib` import.
2. Delete the local `render_json`; remove the `orjson` import only if nothing else in the file uses it.
3. Replace the `--format` `add_argument` call with `add_format_argument(parser, choices=("json",), default=None)`.
4. In `main`, replace `print(render_json(issues))` with `print(render_json([from_issue(i) for i in issues], PROFILE_ISSUE))`.

### Method
- Same key order and sort as before, so the string is byte-identical.

### Details
- Keep `ADR_INDEX`, `_matrix_rows`, `_read_lines`, `_split_row`, `REPO_ROOT`, and every other module-level name; run `tests/tools/test_generate_reference_table.py` to prove the lazy importer still works.

## Compatibility considerations
- Output, exit codes, `--help`, and the symbols imported by `generate_reference_table.py` are unchanged.

## Security considerations
- N/A: output formatting only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_tool_report_output.py tests/tools/test_check_adr_invariant_matrix.py tests/tools/test_generate_reference_table.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: `uv run python tools/check_adr_invariant_matrix.py` and `... --format json` (exit code, output, and `--help` identical).
- `routing.md` "Adding a new tool" steps 1-3, then `uv run python tools/run_validation_gates.py` and `uv run python tools/generate_reference_table.py --check`.

## Completion criteria
- No local `render_json` remains; the lazy importer's four names still resolve; golden tests, existing tests, and the live-data comparison are identical before and after.

## Out of Scope
- Check logic, the other three tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the before-run (text, JSON, help) on live data, then apply Implementation > Procedure | Completed | 20261106-113907 | 20261106-113907 | Changed: tools/check_adr_invariant_matrix.py (shared render_json, add_format_argument) |
| 2 | Run the golden, existing, and `generate_reference_table` tests per Validation plan | Completed | 20261106-113907 | 20261106-113907 | golden, existing, and generate_reference_table tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the after-run comparison | Completed | 20261106-113907 | 20261106-113907 | ruff, mypy, bandit clean; live output identical; generate_reference_table --check OK |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-113907 | 20261106-113907 | N/A: documentation is another procedure of this Plan |

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
- **Requirement ID**: `REQ-005` (use the shared renderers), `REQ-006` (batch 1 comparison)
- **Source issue**: issues/20261104-152906_toolreport001_share-report-model-and-renderers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110046_toolreport001_share-report-model-and-renderers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-091630
- **Related target files**: `tools/check_adr_invariant_matrix.py`
