## Goal
- Create `tools/_workitem_citation_check.py`, the one definition of a "plain path citation" in a Plan, used by the structure checker (finding) and by the normalizer (repair) (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new module and its companion test file. Out of scope: the normalizer script (procedure 03), the checker hook (procedure 05), and any change to `close_procedures_batch.py` or `check_workitem_traceability.py`.

## Assumptions
- Verified in Step 3a: `tools/close_procedures_batch.py` reads the first column of `Implementation Target Files` and the steps through `_BACKTICKED = re.compile(r"`([^`]+)`")` (lines 76 and 235-260), and `tools/check_workitem_traceability.py` reads `Related Tests` through `_BACKTICK_PATH_RE` (line 120); `tools/_workitem_length_check.py` is the model of a helper shared by the structure checker (docstring, `from __future__ import annotations`, finding dicts with `category`, `file`, `detail`).
- Found in Step 3a, not changed here: `tools/check_plan_target_rows.py` compares the raw first cell with `startswith("tests/")` and counts a self-listed test row as a reference, so it reports 0 companion rows for a Plan with backticked paths (it printed `companion test rows: 0` for this Plan and for the wfeff002 Plan, which `check_workitem_traceability.py --plan-coverage` accepts). The authoritative companion check is `--plan-coverage`; the discrepancy goes in the final report.
- The Plan table pitfalls hold: a data row never contains a raw `|` inside a cell, and a header row starts with `| File Path |`.
- Plan overlap check (Step 2): no Frozen Plan targets these files. The prose dependency on `issues/20261126-151441_wfeff006_finalize-procedure-checks.md` is a blocked-by relation of that issue, not of this Plan.

## Design decisions
- Public API: `PlainCitation(kind, line_index, start, end, path)` (frozen dataclass; `kind` is `File Path`, `Related Tests`, or `Implementation steps`; line_index is 0-based into `text.split("\n")`; `start` and `end` are character offsets of the plain path inside that line); `find_plain_citations(text: str) -> list[PlainCitation]`; `wrap_plain_citations(text: str) -> str`; `find_plan_citation_findings(doc_path: Path, root: Path) -> list[dict[str, str]]`.
- What is plain: (a) a `File Path` data cell whose stripped text is a bare repository path (`^[\w.-]+(?:/[\w.-]+)+$`) without backticks; (b) in a `Related Tests` cell, every `tests/[\w./-]+\.py` occurrence outside a backtick span; (c) in the `## Implementation steps` section, every occurrence of a target path (the stripped, unbackticked `File Path` cells) outside a backtick span, matched with `(?<![\w/.-])PATH(?![\w/-]|\.\w)` and longest path first so a shorter path never matches inside a longer one. A cell with trailing text, a command, `N/A: ...`, or an empty cell is never reported or wrapped (Plan UNK-01).
- Backtick spans are blanked (replaced by spaces of equal length) before matching, so a path inside `` `uv run pytest tests/x.py` `` is not plain and offsets stay valid.
- The table is located by the `## Implementation Target Files` heading and its header row (`| File Path |`), with the `Related Tests` column index taken from that header; rows run until the first line that does not start with `|`; the separator row and empty placeholder rows are skipped. Other tables are never read.
- `find_plan_citation_findings` (new) reads the file, builds one finding per citation: `{"category": "plain-path-citation", "file": <doc_path relative to root, posix>, "detail": "<kind>: <path> is not in backticks (line <n>); run uv run python tools/backtick_plan_related_tests.py <file>"}` with `n` 1-based.
- `wrap_plain_citations` (new) applies the spans per line from the right, inserting a backtick before `start` and after `end`; it is the identity on a text with no plain citation (idempotent).

## Alternatives considered
- Two parsers, one in the checker and one in the normalizer: rejected, they could disagree (Plan D-2).
- A baseline for legacy Plans: not needed, the checker applies the finding to active Plans only (Plan D-3).

## Implementation
### Target file
`tools/_workitem_citation_check.py` (new)

### Procedure
1. Write the companion tests first and confirm they fail because the module does not exist.
2. Create the module with the docstring style of `tools/_workitem_length_check.py` and the API above; standard library only.
3. Implement, in order: the regex constants, `_blank_code_spans` (new), `_table_rows` (new) (data rows with the character offset of each cell), `_target_paths` (new), `find_plain_citations` (new), `wrap_plain_citations` (new), `find_plan_citation_findings` (new).
4. Run the companion tests, ruff, mypy, and bandit on the file.

### Method
- Pure functions over `text.split("\n")`; no I/O except in `find_plan_citation_findings` (new).
- Keep the module under 4 KB to stay far from the 24576 B gate.

### Details
- Section reading: a section starts at the line equal to `## <name>` and ends before the next line starting with `## `.

### Companion test files
- `tests/tools/test_workitem_citation_check.py` (new)
  - Procedure: build Plan texts in the test with a target table (header row, separator, rows) and steps; cover: plain and backticked `File Path` cells; a plain `tests/...py` in `Related Tests`, a backticked one, one inside a longer backticked command, `N/A: ...` text with a comma, a cell with trailing text; target paths plain, backticked, and inside a backticked command in the steps, and a shorter path that is a prefix of a longer one; other tables (an `Affected areas` row with a `tests/x.py` text, an `Execution Status` row) never reported; `wrap_plain_citations` (new) result has no remaining plain citation and a second call returns the identical text; offsets of two citations in one line; `find_plan_citation_findings` (new) on a file under `tmp_path` (file name relative to `root`, category, line number).
  - Validation: `uv run pytest tests/tools/test_workitem_citation_check.py` fails before the module exists and passes after.

## Compatibility considerations
- N/A: a new helper with no importer until procedures 03 and 05.

## Security considerations
- N/A: reads a local Markdown file; no input from outside the repository.

## Rollback considerations
- N/A: revert the commit; procedures 03 and 05 depend on it and revert together.

## Validation plan
- `uv run pytest tests/tools/test_workitem_citation_check.py`; ruff format and check; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit tools/_workitem_citation_check.py -c pyproject.toml`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.

## Completion criteria
- The tests fail first and then pass for AC-01; the validators pass; the module imports only the standard library.

## Out of Scope
- The normalizer, the checker hook, and the documents (procedures 03, 05, 07, 08, 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add the companion test file(s) first, then confirm they fail before and pass after | Pending | — | — | |
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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: issues/20261126-151438_wfeff003_plan-path-citations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-172913_wfeff003_plan-path-citations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-173805
- **Related target files**: `tools/_workitem_citation_check.py`, `tests/tools/test_workitem_citation_check.py`
