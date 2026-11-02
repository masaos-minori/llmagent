## Goal
- Create `tools/scan_change_consumers.py`, a read-only tool that takes change seeds and prints a categorized list of candidate direct and indirect consumers in text and JSON (`REQ-001`: categorized candidate report; `REQ-002`: required categories; `REQ-003`: testmon state; `REQ-005`: read-only, no network).

## Scope
- In scope: the new module only: seed handling, file enumeration, the four text-based categories, the optional testmon source, text and JSON rendering, the `--report` option, and `main()`.
- Out of scope: tests (row 02), registration (rows 05 to 07), the skill step and template note (rows 03 and 04), blocking behavior, and running the test suite.

## Assumptions
- Source plan A2 and A3: files come from `git ls-files`; a seed resolves to its defining module by a text match of `def`, `class`, and line-start assignment names, not by AST parsing. A seed with no match is reported as a limit.
- Step 3a verification (2026-11-02): `tools/scan_change_consumers.py` does not exist and no consumer-scan tool is listed in `tools/TOOL_DESCRIPTIONS.md`; `tools/` and `deploy/` exist. Plan Design text corrected: `tools/check_mock_patch_targets.py` is AST-based (`extract_patch_targets`), `tools/check_plan_target_overlaps.py` is regex-based; this tool follows the latter and may borrow the former's idea of reading `patch(...)` string targets.
- Step 3a verification: of the three historical files, only `tools/check_db_separation.py` (`TABLE_OWNERSHIP`, line 78) contains a seed (`workflow_schema_version`) by plain text; `tests/deploy/test_init_db_eventbus_schema.py` and `tests/integration/test_orchestrator_integration.py` have no direct seed hit. Expected recall on that seed set is partial (`REQ-006`).
- Step 3a verification: no `.testmondata*` file exists; `pytest-testmon` is a declared dependency and `.gitignore` ignores the file. The testmon table layout is unconfirmed (`Needs confirmation`, Plan UNK-01, non-blocking): the implementation checks for the expected tables and reports an unrecognized layout as a limit rather than assuming it; if a sample file can be produced cheaply in a scratch directory, inspect its real schema before writing the query.
- The `REQ-006` recall record has no target file row: write it in this document's step 3 Notes and in the implementing commit message (non-blocking caveat; the Plan does not name a file for it).
- Overlap (Step 2, `tools/check_plan_target_overlaps.py`): this new file is not shared with another Plan. Its registration files overlap with sibling Plans; see rows 05 to 07.

## Design decisions
- Pure functions over an injected file list: `scan(root, files, seeds, testmon_path, now)` returns a report object; `main()` supplies `git ls-files` output, so tests need no git repository.
- Every result is a frozen `Candidate(category, seed, path, line_no, text)`; the report always carries a `notice` ("candidates only; a missing consumer is not evidence of absence"), a `limits` list, and a `testmon` state record. A category with no hit is omitted from the output.
- Exit code is always 0 for a completed scan (report-only, like `check_plan_target_overlaps.py`); argument errors exit 2 through `argparse`.

## Alternatives considered
- AST-based resolution of the defining module: rejected in the Plan (heavier; text match is enough for candidates, and a miss is printed as a limit).
- Importing `tools/check_adr_invariant_matrix.py` for ADR citations: rejected; a private copy of the one regex (`` `path.py::node` ``) keeps the tool standalone.
- Running the test suite to find consumers: out of scope in the Plan (7 to 8 minutes).

## Implementation
### Target file
`tools/scan_change_consumers.py` (new)

### Procedure
1. Create the module with a docstring in the style of `tools/check_plan_target_overlaps.py` (purpose, usage, exit code, read-only statement). Imports: `argparse`, `re`, `sqlite3`, `subprocess`, `sys`, `time`, `dataclasses`, `pathlib`, and `orjson` for JSON as the sibling tools do. Mark the subprocess import with `# nosec B404 — git is a trusted local CLI, argv is a fixed list` and the call with `# nosec B603 B607 — fixed git argv, no shell` (the justification format `tools/check_suppression_justification.py` requires).
2. Define the category constants, `Candidate`, `TestmonState` (new), and `Report` dataclasses.
3. Implement `list_tracked_files(root)`, `read_texts(root, files)` (new), the per-category finders, `testmon_state` (new), `scan`, `render_text`, `render_json`, `build_arg_parser`, and `main`.
4. Run the lint sequence of `routing.md` "Adding a new tool" (format, ruff, mypy with an explicit path, bandit) and the live run with the three seeds.

### Method
- `list_tracked_files(root: Path) -> list[str]`: `git ls-files -z` with `cwd=root`; a non-zero exit raises `SystemExit` with a message. Ignored and generated trees stay out because only tracked files are listed (Plan A2).
- `read_texts` (new): read each file once as UTF-8; skip a file that is over 1 MiB or fails to decode and count it in `limits` ("N files skipped: binary or oversized"). All finders work from this one in-memory map of `path -> list[str]` lines.
- Seed match: a seed is a symbol, constant, column or table name, or a file path. A name seed matches with `(?<![A-Za-z0-9_])seed(?![A-Za-z0-9_])`. A path seed (contains `/` or ends in `.py`) matches the path text and, for `.py`, its dotted module name.
- Category `direct:<dir>` (`scripts`, `tests`, `tools`, `deploy`, `docs`): every line in a file under that top-level directory that matches the seed, one candidate per line. A file outside those five directories is not reported in this category.
- Defining module: for each tracked `.py` file under `scripts/` or `tools/`, a line matching `^\s*(def|class)\s+seed\b` or `^seed\s*[:=]` marks it as defining. Dotted name: strip the leading `scripts/` and `.py`, replace `/` with `.`; for `tools/x.py` use `tools.x` (tests import it that way). No defining module found: add a limit "seed X has no defining Python module; patch/import category skipped for it" (column and table names land here).
- Category `patch-or-import`: for each file under `tests/`, flag a line that contains the defining module's dotted name inside a quoted string (a `patch("...")` or `patch.object` target) or in an `import`/`from ... import` statement.
- Category `inventory`: lines naming the seed or the defining module's path in `tools/check_*.py` files and in tracked files whose name contains `baseline` or `inventory`. This covers `TABLE_OWNERSHIP` in `tools/check_db_separation.py`. A line may appear in this category and in a direct category by design; the output says so.
- Category `adr-test-citation`: read `docs/10_adr/*.md`, extract citations with `` `([^`]+\.py)::([^`]+)` ``; when the cited test file's text contains the seed or the defining module name, report the ADR line and the cited node.
- `testmon_state(root, now, max_age_days)` (new): look for `root/.testmondata`. Absent: state `absent`. Older than `max_age_days` (default 7, option `--testmon-max-age-days`): state `stale`, file not opened. Otherwise open with `sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)`, check `sqlite_master` for the expected tables, and on a match list test names whose recorded file names include a defining module path (state `used`); a missing table, a query error, or a corrupt file is state `unrecognized` with a limit. The connection is closed in a `finally`; nothing is written.
- Render: text output has a header line stating the notice, the testmon state line, then one block per non-empty category (`path:line: text`, text trimmed to 160 characters), then the limits. JSON output has `notice`, `seeds`, `testmon` (`state`, `detail`), `limits`, `candidates`, and `categories` (counts). `--report PATH` writes the rendered text in the selected format to that file; nothing else is written.

### Details
- Argument parser: `--seed` (repeatable, required, `action="append"`), `--format {text,json}` (default `text`), `--report PATH`, `--root PATH` (default repository root, used by tests and for a scan of another checkout), `--testmon-max-age-days N`.
- Keep every function small enough that `uv run mypy tools/scan_change_consumers.py` passes without suppressions; type all signatures.
- Time target (Plan AC-5, UNK-03): the live run should finish in under 30 seconds on the 14,000-file repository; if it does not, restrict `read_texts` (new) to the file extensions the finders use and record the measured time in step 3 Notes.
- Live run (Plan AC-6 and `REQ-006`): `uv run python tools/scan_change_consumers.py --seed workflow_schema_version --seed WORKFLOW_SCHEMA_VERSION --seed begin_stage_if_new`; record for each of `tools/check_db_separation.py`, `tests/deploy/test_init_db_eventbus_schema.py`, and `tests/integration/test_orchestrator_integration.py` whether it was found and, if not, why (no direct seed hit; no patch or import path from the defining module; testmon absent).

## Compatibility considerations
- New file with no importers; no existing tool, rule, or Plan Freeze semantics change. JSON keys are new and carry no compatibility burden yet.

## Security considerations
- Read-only: no network, no writes except stdout and the optional `--report` path. `git` runs with a fixed argv and no shell. The testmon database is opened with `mode=ro&immutable=1` so it cannot be modified or locked. File contents are only printed, never executed.

## Rollback considerations
- Delete the new file (a single file, no data or config touched); rows 02 and 05 to 07 must be reverted with it.

## Validation plan
- `uv run pytest tests/tools/test_scan_change_consumers.py -v` (row 02).
- `uv run ruff format tools/scan_change_consumers.py`; `uv run ruff check tools/scan_change_consumers.py --fix`; `uv run mypy tools/scan_change_consumers.py`; `uv run bandit tools/scan_change_consumers.py`; `uv run python tools/check_suppression_justification.py`.
- Live smoke run with the three seeds, timed, with the recall record (`REQ-006`).

## Completion criteria
- The tool prints a categorized report in text and JSON for one or more seeds, with the candidates-only notice and the testmon state line in every report.
- An unrelated seed yields no candidates; an absent, stale, or fresh testmon file prints `absent`, `stale`, or `used`; the file is never opened for writing.
- The lint sequence is clean, the live run finishes under 30 seconds (or the miss is recorded), and the recall against the three historical files is recorded with a reason per file not found.

## Out of Scope
- Making the scan a blocking gate, detecting consumers by running tests, dependency ordering between Plans, and any `docs/*.md` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `tools/scan_change_consumers.py` per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the tool lint sequence of `routing.md` "Adding a new tool" (format, ruff, mypy, bandit, suppression check) | Pending | — | — | |
| 3 | Live run with the three seeds, time it, and record the recall (`REQ-006`) | Pending | — | — | Record in this Notes cell and the commit message |
| 4 | Confirm unit tests (row 02) and registration (rows 05 to 07) pass with this tool | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (categorized candidate report), `REQ-002` (required categories), `REQ-003` (testmon state), `REQ-005` (read-only, registered), `REQ-006` (recall record)
- **Source issue**: issues/20261030-191006_flowimp001_consumer-impact-scan.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080004_flowimp001_consumer-impact-scan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085054
- **Related target files**: tools/scan_change_consumers.py
