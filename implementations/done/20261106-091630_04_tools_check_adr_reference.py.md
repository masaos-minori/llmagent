## Goal
Make `tools/check_adr_reference.py` render its JSON output and declare its `--format` option through the shared module, with byte-identical output and unchanged exit codes (`REQ-005`; `REQ-006`: batch 1).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `render_json`, the `--format` argument, and the import block.
- Out of scope: `collect_issues`, the matrix and front matter checks, the default text path (`report_and_exit` in `tools/_docs_consistency_lib.py`).

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file has the guarded bootstrap and imports `Issue, report_and_exit` from `tools._docs_consistency_lib`; `render_json(issues)` emits `file`, `line_no`, `severity`, `message` sorted by `(file, line_no)` with `OPT_INDENT_2`; `main` declares `--format` with `choices=["json"]`, `default=None`, and the help text `Machine-readable output format (default: human-readable text)`, prints `render_json(issues)` and returns `1` if any issue has severity `ERROR`, otherwise returns `report_and_exit(issues)`. Pre-commit runs it as `uv run python -m tools.check_adr_reference`; no caller requests `--format json`.
- `tests/tools/test_check_adr_reference.py` imports `collect_issues` only and does not use `render_json`; no test edit is needed. The golden file `tests/tools/test_tool_report_output.py` (earlier-`seq` procedure) guards the output.
- Overlap judgment: no other open Plan targets this file.
- `ReportFinding`, `PROFILE_ISSUE`, `from_issue`, `render_json`, and `add_format_argument` are created by the earlier-`seq` sibling procedure for `tools/_report.py`.

## Design decisions
- Keep `render_json` out of this file: `main` calls the shared `render_json` with `PROFILE_ISSUE` over `[from_issue(i) for i in issues]`.
- Keep the `ERROR`-based exit logic and the `report_and_exit` text path in this tool.

## Alternatives considered
- Keep a one-line local wrapper `render_json(issues)`: rejected, REQ-005 requires no local copy.

## Implementation
### Target file
`tools/check_adr_reference.py`

### Procedure
1. Add `from tools._report import PROFILE_ISSUE, add_format_argument, from_issue, render_json` after the existing `tools._docs_consistency_lib` import.
2. Delete the local `render_json` function; if `orjson` is no longer used elsewhere in the file, remove its import.
3. Replace the `parser.add_argument("--format", choices=["json"], default=None, help=...)` call with `add_format_argument(parser, choices=("json",), default=None)`.
4. In `main`, replace `print(render_json(issues))` with `print(render_json([from_issue(i) for i in issues], PROFILE_ISSUE))`.

### Method
- The profile reproduces key order and the `(file, line_no)` sort, so the output string is unchanged.

### Details
- `--help` text must stay identical (the helper writes the same help string).
- Keep `collect_issues`, `MatrixSourceRef`, and every other public symbol.

## Compatibility considerations
- Exit codes, stdout, and JSON keys are unchanged; `-m` form (pre-commit) and by-path form keep working through the existing bootstrap.

## Security considerations
- N/A: output formatting only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_tool_report_output.py tests/tools/test_check_adr_reference.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: `uv run python tools/check_adr_reference.py` and `... --format json` — compare exit code and output byte for byte; compare `--help` output.
- `routing.md` "Adding a new tool" steps 1-3, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- No local `render_json` remains; golden tests, existing tests, and the live-data comparison are identical before and after.

## Out of Scope
- Check logic, severity model, the other three tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the before-run (text, JSON, help) on live data, then apply Implementation > Procedure | Completed | 20261106-113821 | 20261106-113906 | Changed: tools/check_adr_reference.py (shared render_json, add_format_argument; local render_json removed) |
| 2 | Run the golden and existing tests per Validation plan | Completed | 20261106-113906 | 20261106-113906 | golden and existing tests pass; no test edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the after-run comparison | Completed | 20261106-113906 | 20261106-113906 | ruff, mypy, bandit clean; live text, JSON, help byte-identical before/after |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-113906 | 20261106-113906 | N/A: documentation is another procedure of this Plan |

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
- **Related target files**: `tools/check_adr_reference.py`
