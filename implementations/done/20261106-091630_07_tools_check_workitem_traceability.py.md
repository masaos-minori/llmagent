## Goal
Make `tools/check_workitem_traceability.py` use the shared finding record, renderers, and `--format` helper in place of its local `make_finding`, `render_text`, `render_json`, and `render_csv`, with identical output, exit codes, and JSON key set, and adapt its tests to the new record (`REQ-005`; `REQ-006`: batch 2).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `make_finding` and its call sites, the `find_*` return types, `is_archived_finding`, the three renderers, `_print_findings`, the `--format` argument, and the import block of this file; the companion test file's finding assertions.
- Out of scope: check logic, categories, the git and root changes of the `toolcommon001` Plan (different code), companion-candidate scoping.

## Assumptions
- Verified on 2026-11-06 (Step 3a): findings are `dict[str, str]` with keys `category`, `file`, `detail`, built by `make_finding` at twelve call sites inside the `find_*` functions; `render_text` groups by category (`[category] (n)`, `  file: detail`, blank line, `N finding(s) total.`, or `No findings.` when empty); `render_json` uses `OPT_INDENT_2 | OPT_SORT_KEYS` and keeps input order; `render_csv` uses `csv.DictWriter` with header `category,file,detail` (the `\r\n` default); `_print_findings` prints JSON, CSV (`end=""`), or text (`end=""`); `build_arg_parser` declares `--format` with `choices=["json", "csv"]`, `default=None`. Pre-commit runs it as `uv run python -m tools.check_workitem_traceability --active-only`; `tools/run_validation_gates.py` calls it by path; `tests/tools/test_generate_workitem.py` imports only `extract_*` functions from it.
- The companion test file subscripts finding dicts in 19 lines (`findings[0]["category"]`, `["file"]`, `["detail"]`, `finding["category"]` in a `_categories` helper, `multi["detail"]`): they are a Plan amendment (2026-11-06, fallout) and are covered here. It is a valid companion: only this row names it in `Related Tests`, and no design decision is needed beyond the field mapping below. It patches `cwt.ROOT_DIR`, which stays (or is the alias set by the `toolcommon001` procedure).
- Sequencing: the `toolcommon001` procedure for this file (git call, root alias, bootstrap, helper import) is expected to land first; this procedure edits different functions, so the two are compatible. If the bootstrap is absent when this runs, add it as described in that procedure.
- Shared symbols (`ReportFinding`, `PROFILE_WORKITEM`, `render_text`, `render_json`, `render_csv`, `add_format_argument`) come from the earlier-`seq` sibling procedure for `tools/_report.py`.

## Design decisions
- Field mapping (Plan Design 2a): `category` becomes `code`, `file` stays `file`, `detail` becomes `message`; `PROFILE_WORKITEM` maps the output keys back to `category`, `file`, `detail`, keeps input order, and sorts output keys, so JSON and CSV stay byte-identical.
- Findings become `ReportFinding` instances; `list[dict[str, str]]` annotations become `list[ReportFinding]`.

## Alternatives considered
- Keep dict findings and wrap them only at render time: rejected, REQ-005 removes the local `make_finding`, and a dict-to-record conversion layer would leave two finding shapes in one file.

## Implementation
### Target file
`tools/check_workitem_traceability.py`

### Procedure
1. Add `from tools._report import PROFILE_WORKITEM, ReportFinding, add_format_argument, render_csv, render_json, render_text` next to the other first-party imports.
2. Delete `make_finding`; replace each `make_finding(category, file_path, detail)` call with `ReportFinding(code=category, file=file_path, message=detail)`.
3. Change every `list[dict[str, str]]` finding annotation (`find_*`, `collect_findings`, `is_archived_finding`, `_print_findings`) to `list[ReportFinding]` / `ReportFinding`; `is_archived_finding` reads `finding.file`.
4. Delete the local `render_text`, `render_json`, and `render_csv`; in `_print_findings` call the shared `render_json(findings, PROFILE_WORKITEM)`, `render_csv(findings, PROFILE_WORKITEM)` (`end=""`), and `render_text(findings)` (`end=""`).
5. In `build_arg_parser` replace the `--format` `add_argument` call with `add_format_argument(parser, choices=("json", "csv"), default=None)`.
6. Remove the `csv` import if unused.

### Method
- The renderers' output is fixed by `PROFILE_WORKITEM` and the grouped text layout of `render_text`; no call site changes what it reports.

### Details
- Grouping order in text is first-seen category order; the shared `render_text` MUST preserve that (`dict.fromkeys`).
- Run the golden tests before and after; compare live `--active-only`, `--format json`, and `--format csv` output byte for byte.

### Companion test files
- `tests/tools/test_check_workitem_traceability.py`
  - Procedure: replace the dict subscripts with attribute reads: `["category"]` becomes `.code`, `["file"]` becomes `.file`, `["detail"]` becomes `.message` in the 19 assertions and in the `_categories` helper; update any local type annotation of a finding.
  - Validation: `uv run pytest tests/tools/test_check_workitem_traceability.py -q`.

## Compatibility considerations
- stdout bytes for text, JSON, and CSV, exit codes, and `--help` are unchanged; the importers (`tests/tools/test_generate_workitem.py` imports only `extract_*`) are unaffected; pre-commit `-m` and by-path forms keep working.

## Security considerations
- N/A: output formatting only.

## Rollback considerations
- N/A: revert the commit (source and tests change together).

## Validation plan
- `uv run pytest tests/tools/test_tool_report_output.py tests/tools/test_check_workitem_traceability.py tests/tools/test_generate_workitem.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: `uv run python tools/check_workitem_traceability.py --active-only` in text, `--format json`, and `--format csv` — exit code and output byte for byte; `--plan-coverage` on one existing plan as well.
- `routing.md` "Adding a new tool" steps 1-3, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- No local `make_finding`, `render_text`, `render_json`, or `render_csv` remains; golden, existing, and live-data comparisons are identical before and after.

## Out of Scope
- Check logic, new categories, the other three tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the before-run (text, JSON, CSV, `--plan-coverage`) on live data, then apply Implementation > Procedure | Completed | 20261106-113919 | 20261106-114225 | Changed: tools/check_workitem_traceability.py (ReportFinding, shared renderers and --format helper; make_finding, render_* removed); tests/tools/test_check_workitem_traceability.py (attribute reads) |
| 2 | Update the companion test assertions per Companion test files and run them with the golden tests | Completed | 20261106-114225 | 20261106-114225 | tests/tools 1744 passed, golden tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the after-run comparison | Completed | 20261106-114225 | 20261106-114225 | ruff, mypy, bandit clean; live text, JSON, CSV, --plan-coverage output byte-identical; radon unchanged |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-114225 | 20261106-114225 | N/A: documentation is another procedure of this Plan |

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
- **Requirement ID**: `REQ-005` (use the shared renderers and record), `REQ-006` (batch 2 comparison)
- **Source issue**: issues/20261104-152906_toolreport001_share-report-model-and-renderers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110046_toolreport001_share-report-model-and-renderers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-091630
- **Related target files**: `tools/check_workitem_traceability.py`, `tests/tools/test_check_workitem_traceability.py`
