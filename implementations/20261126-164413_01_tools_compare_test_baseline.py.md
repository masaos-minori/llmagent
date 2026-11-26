## Goal
- Create `tools/compare_test_baseline.py`, a read-only tool that classifies the failures of one pytest run (a JUnit XML file) against the baseline `tools/known_test_failures_baseline.txt`: new failures (exit 1), baseline entries that now pass (removal notice), entries that did not run, and the count of unchanged known failures (REQ-001, REQ-002, REQ-003, REQ-004, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new module and its companion test file.
- Out of scope: running pytest, any change to test selection, and wiring the tool into `tools/run_validation_gates.py`, a hook, or CI.

## Assumptions
- Verified in Step 3a: no tool or test mentions `junit` or `compare_test_baseline` (new) (`rg` over `tools/`, `tests/`, `scripts/`, `pyproject.toml`); `tools/check_skill_size.py` and `tools/check_module_size.py` are the model for baseline loading and exit codes; `tools/_atomic_write.py` provides `atomic_write_text`, `print_dry_run(path, old, new)`, and `add_dry_run_argument(parser)`.
- Measured JUnit shape (Plan Background, rechecked): a failing test is a `testcase` with a `failure` child, a fixture error a `testcase` with an `error` child, a collection error a `testcase` with empty `classname` and the dotted module path as `name`; a skipped test has a `skipped` child.
- The baseline path is the module constant `DEFAULT_BASELINE` (`tools/known_test_failures_baseline.txt`), overridable with `--baseline`, so the tests use a temporary file.
- The tool lives in `tools/` and is imported by the tests as `from tools import compare_test_baseline` (the convention of `tests/tools/test_check_skill_size.py`).
- Plan overlap check (Step 2): no other Frozen Plan targets these files. The Plan's prose dependency on `issues/20261126-151436_wfeff001_cmd-mcp-import-nameerror.md` is satisfied (that issue is archived and its fix is committed).
- UNK-01 of the Plan stays open: only failure, fixture error, and collection error shapes were measured; the companion tests cover those plus a teardown error built with a failing finalizer, and record any shape that cannot be built.

## Design decisions
- Test id is `classname::name`; a collection error (empty `classname`) is the bare `name`. A test with several children (for example a call failure and a teardown error) is one id and counts as failing.
- A run is classified only over the testcases in the XML: a baseline entry whose id is absent from the XML, or whose testcase is skipped, is `not run` and never `fixed`; an XML file that is missing, unparsable, or holds zero testcases is an input error (exit 2), so an interrupted run cannot read as clean.
- `--update` removes every entry that ran and passed; `--add ID --reason TEXT` appends one entry. Both are explicit, mutually exclusive, and refuse to write otherwise; `--add` is refused when `ID` did not fail in this run, when the reason names no issue path, or when `ID` is already listed. A plain run opens no file for writing. Writes go through `atomic_write_text`; `--dry-run` prints the diff with `print_dry_run` and writes nothing.
- Exit codes follow `tools/TOOL_DESCRIPTIONS.md` CLI convention: 0 no new failure, 1 at least one new failure, 2 usage or input error (including an invalid baseline). An update does not change the exit code of the classification.
- XML is read with stdlib `xml.etree.ElementTree` (Plan D-3): `import xml.etree.ElementTree as ET  # nosec B405 — reads local XML the caller's own pytest run wrote` and `ET.parse(...)  # nosec B314 — same local, trusted file`.
- Output is text only: sections `new failures`, `fixed (remove from the baseline)`, `not run`, then one summary line `known failures: N` (Plan D-8).

## Alternatives considered
- Parse the pytest terminal summary: fragile with `-n` and `-q`. A JSON report plugin: a new dependency. Both rejected (Plan D-1).
- `defusedxml`: only a transitive dependency; adding it changes `pyproject.toml` and `uv.lock`. Rejected (Plan D-3).

## Implementation
### Target file
`tools/compare_test_baseline.py` (new)

### Procedure
1. Write the companion tests first (below) and run them; confirm they fail because the module does not exist.
2. Create the module with the module docstring format of the sibling tools (`tools/check_skill_size.py`: file path line, purpose, usage, exit codes) and `from __future__ import annotations`.
3. Implement, in this order: `InputError` (new) and `BaselineError` (new) (both `Exception` subclasses; `BaselineError` (new) carries the line number), `read_junit` (new), `load_baseline`, `classify`, `render_report` (new), `update_baseline` and `add_entry` (pure functions returning the new text), `main`.
4. Run the companion tests until they pass, then ruff, mypy, and bandit on the file.

### Method
- Data: `RunResult(failing: frozenset[str], passed: frozenset[str], skipped: frozenset[str], total: int)` and `Classification(new: list[str], known: list[str], fixed: list[str], not_run: list[str])` as frozen dataclasses; lists are sorted for deterministic output.
- `read_junit(path: Path) -> RunResult`: parse; the root is `testsuites` or `testsuite`; iterate `testcase`; failing when a child tag is `failure` or `error`, skipped when it is `skipped` and nothing failed, else passed; an id seen twice merges with failing winning. Raise `InputError` (new) for an unreadable file, `ET.ParseError`, or `total == 0`.
- `load_baseline(path: Path) -> dict[str, str]`: one entry per line as id, a tab, reason; blank lines and lines starting with `#` are skipped; a missing baseline file is an `InputError` (new), so a typo cannot silently disable the check. The reason must match `issues/(done/)?<name>.md` (regex `ISSUE_PATH_RE = r"issues/(?:done/)?[\w.-]+\.md"`); a line without a tab, an empty id, a reason without an issue path, or a duplicate id raises `BaselineError` (new) with the 1-based line number.
- `classify(run, baseline)`: `new` = failing ids not in the baseline; `known` = failing ids in the baseline; `fixed` = baseline ids in `passed`; `not_run` = baseline ids in neither `failing` nor `passed`.
- Update helpers keep the header comments and unrelated lines byte-for-byte: `--update` drops only the lines of fixed entries; `--add` appends `id<TAB>reason` as a new last line.

### Details
- Real-run check (Plan T-06), not committed as a test: `uv run pytest tests/tools -n 2 -q -p no:randomly --junitxml=<scratch>/run.xml` then `uv run python tools/compare_test_baseline.py <scratch>/run.xml` exits 0.
- Keep the module under the 24576 B size gate of `tools/`.

### Companion test files
- `tests/tools/test_compare_test_baseline.py` (new)
  - Procedure: write synthetic JUnit XML to `tmp_path` and cover the cases of Plan T-01 to T-04: ids of a failure, fixture error, collection error (empty classname) and a failing test with a teardown error; known-only run (exit 0, known count); one new failing test (exit 1, named); new collection error (exit 1); fixed entry (exit 0, removal notice); entry absent or skipped (`not run`, never fixed); baseline line without issue path, without tab, and duplicate (exit 2 with the line number); missing baseline file and missing, unparsable, and zero-testcase XML (exit 2); `--update` removes only fixed entries and keeps comments; `--add` refuses an id that did not fail, a reason without an issue path, and a duplicate; a plain run leaves the baseline file byte-identical; `--dry-run` writes nothing; combine `--update` and `--add` is a usage error.
  - Validation: `uv run pytest tests/tools/test_compare_test_baseline.py` fails before the module exists and passes after.

## Compatibility considerations
- N/A: a new standalone tool with no importer; no existing behavior changes.

## Security considerations
- The XML is local input written by the caller's own pytest run; the two `nosec` comments carry that justification (`tools/check_suppression_justification.py` checks them). The tool writes only the baseline file, through `atomic_write_text`, and only with an explicit flag; the `--add` reason is stored as text and never executed.

## Rollback considerations
- N/A: revert the commit; no other file depends on the module until procedures 04 to 06 register it.

## Validation plan
- `uv run pytest tests/tools/test_compare_test_baseline.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit tools/compare_test_baseline.py -c pyproject.toml`; `uv run python tools/check_suppression_justification.py`; the real-run check above; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.
- The full suite once and diff-cover per `rules/toolchain.md` section 7 run at the end of the Plan batch (`skills/code-implementation/workflow.md` Step 4).

## Completion criteria
- The companion tests fail first and then pass for AC-01 to AC-06; the validators above pass; the real run exits 0.
- The module imports only the standard library and `tools/_atomic_write.py`, and the file stays under 24576 B.

## Out of Scope
- Registration in the documents (procedures 04 to 06), the baseline file content (procedure 02), and any gate or hook wiring.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add the companion test file first, then confirm it fails before and passes after | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-006`
- **Source issue**: issues/20261126-151437_wfeff002_test-failure-baseline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-161137_wfeff002_test-failure-baseline.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-164413
- **Related target files**: `tools/compare_test_baseline.py`, `tests/tools/test_compare_test_baseline.py`
