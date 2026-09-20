## Goal

Add four new detection functions to `tools/check_docs_content_policy.py` —
`check_typed_dict_table`, `check_cli_argument_table`, `check_error_handling_table`,
and `check_full_json_example` — so the tool catches the four content shapes its
existing 11 check functions miss (satisfies `REQ-001` through `REQ-004`).

## Scope

- In scope: adding the four new `check_*(files: list[DocFile]) -> list[Issue]`
  functions to `tools/check_docs_content_policy.py`, and wiring all four into
  `main()`.
- Out of scope: any change to the 11 existing check functions' logic or their
  wiring order in `main()`; any change to `DocFile`, `discover_all_md_files`,
  `_is_guard_start`, `_is_guard_end`, or any other existing helper; fixing any
  violation the new functions detect (tracked by a separate companion Issue, not
  this document); adding tests (covered by
  `implementations/20260920-090331_02_tests_tools_test_check_docs_content_policy.py.md`
  in this same pass).

## Assumptions

- `chunksplitter.md`'s three violating tables use these exact header shapes,
  confirmed by reading `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`
  directly: `| TypedDict | Purpose |` (line 44), `| Argument | Description |
  Default |` (line 188), `| Case | Action |` (line 288). The new regexes are
  written to match these exact shapes plus the reasonable synonyms the Plan's
  Requirements name (`DTO` alongside `TypedDict`; `Parameter`/`Option`/`Flag`
  alongside `Argument`; `Error`/`Exception`/`Error Handling` heading text
  alongside a `Case`/`Action` header).
- `chunksplitter.md`'s full JSON payload example (lines 195-212, 18 lines inside
  the fence) is long enough to exceed any reasonable conservative threshold — the
  exact threshold value is UNK-01 in the source Plan (non-blocking); this document
  sets it to 15 lines, documented inline as a module-level constant, consistent
  with the existing `_MIN_MECHANICAL_TABLE_ROWS = 4` / `_MIN_CLI_BLOCKS = 3`
  pattern.

## Design decisions

- Each new function follows the existing module's one-function-per-category shape
  exactly (see `check_field_type_table`/`check_config_file_inventory_table` as the
  closest existing precedents) rather than a shared generic pattern-matching
  engine — this file is already the single canonical home for this policy's
  detection logic (`skills/DESIGN.md` File Split Rule "shared normalization"), and
  a differently-shaped addition would fragment that.
- `check_typed_dict_table` matches unconditionally on header shape (no minimum-row
  threshold), following `check_index_table`'s existing pattern — a
  `TypedDict`/`DTO`-labeled table header is already a strong, unambiguous signal
  on its own (unlike a generic `Field`/`Type` header, which `check_field_type_table`
  reasonably gates behind a row-count minimum to avoid flagging short, legitimate
  tables).
- `check_cli_argument_table` requires a heading-proximity check (reusing the
  existing `_CLI_HEADING_RE`/`_HEADINGS_WINDOW` constants) in addition to the table
  header match, following `check_config_file_inventory_table`'s existing
  heading-proximity pattern — this double-signal (CLI-labeled heading AND
  Argument/Parameter/Option/Flag column) keeps the check conservative without
  needing a separate row-count threshold.
- `check_error_handling_table` flags on either of two independent signals (a table
  under an Error/Exception/Error Handling heading, OR a table header shaped like
  `Case`/`Scenario` + ... + `Action`), matching the Plan's Requirement wording
  ("or with a Case/Action-shaped header") — the second signal catches an
  error-handling table that lacks a nearby heading naming the category explicitly.
- `check_full_json_example` counts lines strictly between a ` ```json ` fence and
  its closing ` ``` `, flagging when the count meets or exceeds
  `_MIN_JSON_EXAMPLE_LINES = 15` — chosen per UNK-01's Resolution Path, erring
  toward a higher threshold to avoid flagging a short illustrative snippet,
  consistent with the Plan's stated Risk mitigation.

## Alternatives considered

- A single generic "mechanical content" detector parameterized by pattern list,
  replacing several of the module's existing per-category functions: rejected —
  out of scope (Constraints below forbid touching the 11 existing functions), and
  would be a much larger, riskier change than four additive functions.
- Gating `check_typed_dict_table` behind the same `_MIN_MECHANICAL_TABLE_ROWS`
  threshold as `check_field_type_table`: rejected — `chunksplitter.md`'s own
  TypedDict table has only 3 data rows (`CrawlJsonPayload`, `ChunkJsonPayload`,
  `ChunkMetadata`), which would fail a `>= 4`-row gate and leave the confirmed
  violation undetected; the header-shape signal alone is specific enough to flag
  unconditionally, matching `check_index_table`'s existing precedent.

## Implementation

### Target file

tools/check_docs_content_policy.py

### Procedure

1. Add four new module-level regex/threshold constants near the existing pattern
   constants (after `_DDL_STATEMENT_RE`, current line 78): `_TYPED_DICT_TABLE_HEADER_RE`,
   `_CLI_ARG_TABLE_HEADER_RE`, `_ERROR_HEADING_RE`, `_ERROR_ACTION_TABLE_HEADER_RE`,
   `_MIN_JSON_EXAMPLE_LINES`.
2. Add `check_typed_dict_table` after `check_ddl_schema_block` (current lines
   516-554, ending just before `def main():` at current line 557).
3. Add `check_cli_argument_table` after `check_typed_dict_table`.
4. Add `check_error_handling_table` after `check_cli_argument_table`.
5. Add `check_full_json_example` after `check_error_handling_table`.
6. Wire all four new functions into `main()` (current lines 557-573), appending
   each `all_issues += check_*(files)` call after the existing 11.

### Method

New constants (insert after `_DDL_STATEMENT_RE = re.compile(...)`, current line
78) — **corrected during Step 3e** from the originally-drafted version: added a
dedicated `_CLI_ARG_HEADING_RE` (the shared `_CLI_HEADING_RE` lacks "Arguments"/
"Options" and neither it nor the original `_ERROR_HEADING_RE` tolerated a numbered
heading like `### 3.3 CLI Arguments`); widened `_ERROR_ACTION_TABLE_HEADER_RE` to
also match a plain 2-column `Case | Action` header; added `_TABLE_SEPARATOR_ROW_RE`:
```python
_TYPED_DICT_TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*(?:TypedDict|DTO)\s*\|", re.IGNORECASE
)
_CLI_ARG_TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*(?:Argument|Parameter|Option|Flag)\s*\|", re.IGNORECASE
)
_CLI_ARG_HEADING_RE = re.compile(
    r"^#{1,6}\s+(?:[\d.]+\s+)?(?:CLI|Arguments?|Options?)\b", re.IGNORECASE
)
_ERROR_HEADING_RE = re.compile(
    r"^#{1,6}\s+(?:[\d.]+\s+)?(?:Error|Exception|Error\s+Handling)\b", re.IGNORECASE
)
_ERROR_ACTION_TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*(?:Case|Scenario)\s*\|(?:.*\|)?\s*Action\s*\|", re.IGNORECASE
)
_TABLE_SEPARATOR_ROW_RE = re.compile(r"^\s*\|[\s:|-]*\|\s*$")
_MIN_JSON_EXAMPLE_LINES = 15
```

New function 1 (insert after `check_ddl_schema_block`, before `def main():`):
```python
def check_typed_dict_table(files: list[DocFile]) -> list[Issue]:
    """Flag a table header labeled TypedDict/DTO (e.g. `| TypedDict | Purpose |`).

    Unconditional on match, like `check_index_table` — a TypedDict/DTO-labeled
    header is specific enough that no minimum-row threshold is needed.
    """
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if _TYPED_DICT_TABLE_HEADER_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "TypedDict/DTO field table header — see "
                            "skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
    return issues
```

New function 2:
```python
def check_cli_argument_table(files: list[DocFile]) -> list[Issue]:
    """Flag a Markdown table (not a bash-block enumeration) under a CLI/Arguments/
    Options heading, with a header column named Argument/Parameter/Option/Flag."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if not _CLI_ARG_TABLE_HEADER_RE.search(line):
                continue
            has_cli_heading = False
            for j in range(max(0, i - _HEADINGS_WINDOW), i):
                if _CLI_ARG_HEADING_RE.search(doc.lines[j]):
                    has_cli_heading = True
                    break
            if not has_cli_heading:
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="WARNING",
                    message=(
                        "CLI argument table — see skills/DESIGN.md "
                        "Docs content policy — remove"
                    ),
                )
            )
    return issues
```

New function 3 — **corrected during Step 3e**: the originally-drafted version
flagged every `\|`-starting line under a matching heading (separator row and every
data row individually), not just the table's header row. The corrected version
below flags a candidate header line only when the *next* line is a Markdown table
separator row (`_TABLE_SEPARATOR_ROW_RE`):
```python
def check_error_handling_table(files: list[DocFile]) -> list[Issue]:
    """Flag a table under an Error/Exception/Error Handling heading, or a table
    with a Case/Scenario + Action-shaped header, independent of a nearby heading.

    Flags only the table's header row (identified by the next line being a
    Markdown table separator row), not every data row of a matching table.
    """
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        n = len(doc.lines)
        for idx in range(n):
            i = idx + 1
            line = doc.lines[idx]
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            if _ERROR_ACTION_TABLE_HEADER_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "error-handling table — see skills/DESIGN.md "
                            "Docs content policy — remove"
                        ),
                    )
                )
                continue
            if not line.lstrip().startswith("|"):
                continue
            if idx + 1 >= n or not _TABLE_SEPARATOR_ROW_RE.match(doc.lines[idx + 1]):
                continue
            has_error_heading = False
            for j in range(max(0, i - _HEADINGS_WINDOW), idx):
                if _ERROR_HEADING_RE.search(doc.lines[j]):
                    has_error_heading = True
                    break
            if not has_error_heading:
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="WARNING",
                    message=(
                        "error-handling table — see skills/DESIGN.md "
                        "Docs content policy — remove"
                    ),
                )
            )
    return issues
```

New function 4:
```python
def check_full_json_example(files: list[DocFile]) -> list[Issue]:
    """Flag a fenced JSON code block at or above `_MIN_JSON_EXAMPLE_LINES` lines."""
    issues: list[Issue] = []
    for doc in files:
        in_auto_generated = False
        in_json_block = False
        block_start = 0
        block_lines = 0
        for i, line in enumerate(doc.lines, 1):
            if _is_guard_start(line):
                in_auto_generated = True
                continue
            if _is_guard_end(line):
                in_auto_generated = False
                continue
            if in_auto_generated:
                continue
            stripped = line.strip()
            if stripped.startswith("```json"):
                in_json_block = True
                block_start = i
                block_lines = 0
                continue
            if in_json_block and stripped == "```":
                if block_lines >= _MIN_JSON_EXAMPLE_LINES:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=block_start,
                            severity="WARNING",
                            message=(
                                "full JSON payload example — see "
                                "skills/DESIGN.md Docs content policy — remove"
                            ),
                        )
                    )
                in_json_block = False
                continue
            if in_json_block:
                block_lines += 1
    return issues
```

`main()` wiring (replaces current lines 557-573's `all_issues += ...` block, adding
four lines after the existing eleven):
```python
def main() -> int:
    files = discover_all_md_files(DOCS_DIR)

    all_issues: list[Issue] = []
    all_issues += check_full_file_tree(files)
    all_issues += check_per_file_description(files)
    all_issues += check_index_table(files)
    all_issues += check_location_mapping(files)
    all_issues += check_literal_port_number(files)
    all_issues += check_default_value_restatement(files)
    all_issues += check_field_type_table(files)
    all_issues += check_config_file_inventory_table(files)
    all_issues += check_cli_command_enumeration(files)
    all_issues += check_environment_setup_sequence(files)
    all_issues += check_ddl_schema_block(files)
    all_issues += check_typed_dict_table(files)
    all_issues += check_cli_argument_table(files)
    all_issues += check_error_handling_table(files)
    all_issues += check_full_json_example(files)

    return report_and_exit(all_issues)
```

### Details

- No new imports required — `re`, `Issue`, and `report_and_exit` are already
  imported at the top of this file.
- All four new functions reuse the existing `_is_guard_start`/`_is_guard_end`
  guarded-block helpers so a documented, intentionally-illustrative example
  inside an `<!-- AUTO-GENERATED -->` block is not flagged, matching every
  existing check function's behavior.
- `check_cli_argument_table` and `check_error_handling_table`'s heading-proximity
  checks reuse the existing `_CLI_HEADING_RE` and `_HEADINGS_WINDOW` module
  constants rather than redefining them — `_CLI_HEADING_RE` is already used by
  `check_cli_command_enumeration`; `_HEADINGS_WINDOW` is already used by
  `check_full_file_tree` and `check_config_file_inventory_table`.
- `check_full_json_example` intentionally does not exempt a JSON block bearing an
  "illustrative" marker (unlike `check_literal_port_number`'s
  `_ILLUSTRATIVE_MARKERS` exemption) — the Plan's chosen 15-line threshold is
  itself the safeguard against flagging a short illustrative snippet; adding a
  second, marker-based exemption was not requested by the Plan and would widen
  scope beyond REQ-004.

## Compatibility considerations

Purely additive: four new functions plus four new lines in `main()`. No existing
function's signature, behavior, or call order changes. `check_docs_content_policy.py`
has no callers outside `tests/tools/test_check_docs_content_policy.py` and its own
`if __name__ == "__main__":` entry point (confirmed via `rg -l
"check_docs_content_policy" --type py`) — no other script imports from this module,
so this change cannot break an unrelated caller.

## Security considerations

N/A: no new external input, no new I/O, no new dynamic execution — the four new
functions only read already-loaded `DocFile.lines` (already-read `docs/*.md` text)
via `re.compile(...).search()`, the same operation every existing function in this
file already performs.

## Rollback considerations

Revert this file's diff. No other file depends on the four new functions until
`implementations/20260920-090331_02_tests_tools_test_check_docs_content_policy.py.md`
(this same pass, seq 02) is also applied — reverting this document's changes alone
does not break that document's tests if it has not yet been applied, but does break
its tests if it has (since the tests import the new function names). Apply seq 01
and seq 02 together if reverting either.

## Validation plan

- `uv run ruff format tools/check_docs_content_policy.py` and `uv run ruff check
  tools/check_docs_content_policy.py` — confirm formatting/lint compliance.
- `uv run mypy tools/check_docs_content_policy.py` — pass the file path explicitly
  (per `routing.md` "Adding a new tool": `pyproject.toml`'s mypy `files` scope
  covers `scripts/` by default, not `tools/`).
- `uv run bandit tools/check_docs_content_policy.py` — confirm no new findings
  (baseline: 0 issues across 525 lines).
- `uv run radon cc tools/check_docs_content_policy.py -s` — confirm the four new
  functions do not exceed the existing complexity ceiling (baseline: two existing
  functions at C-grade, `check_cli_command_enumeration` C(17) and
  `check_environment_setup_sequence` C(15); the rest A/B-grade).
- `uv run python tools/check_docs_content_policy.py` (full `docs/` tree) — confirm
  the pre-change 30 findings are unchanged and 4 new findings appear for
  `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` (one per new function).
- Unit tests are added and run in
  `implementations/20260920-090331_02_tests_tools_test_check_docs_content_policy.py.md`
  (this same pass, seq 02) — this document's own validation is limited to this
  file's own correctness (static analysis + the live full-tree smoke test above).

## Completion criteria

- `check_typed_dict_table`, `check_cli_argument_table`, `check_error_handling_table`,
  and `check_full_json_example` exist in `tools/check_docs_content_policy.py` with
  the signatures above, and all four are wired into `main()`.
- `uv run python tools/check_docs_content_policy.py` flags
  `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` for its TypedDict table
  (line 44), CLI argument table (line 188), error-handling table (line 288), and
  full JSON payload example (line 195).
- The tool's pre-change 30-warning baseline across the rest of `docs/` is
  unchanged.
- `uv run ruff check`, `uv run mypy tools/check_docs_content_policy.py`, and
  `uv run bandit tools/check_docs_content_policy.py` all pass with no new findings.

## Out of scope

- Any change to the 11 existing check functions' logic, or their order in
  `main()`.
- Fixing `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`'s violations —
  tracked by the companion Issue
  (`issues/20260920-084526_docref01_isolate-implementation-reference-content-from-rag-design-docs.md`),
  referenced in the source Plan's Reference Files.
- Any change to `skills/DESIGN.md`'s policy wording.
- Adding tests (covered by seq 02, this same pass) or updating
  `tools/TOOL_DESCRIPTIONS.md`/`routing.md` (covered by seq 03/seq 04, this same
  pass).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-091500 | 20260920-091500 | Implemented as specified. Step 3e's smoke test then found the as-written `check_cli_argument_table`/`check_error_handling_table` did not catch `chunksplitter.md`'s CLI/error tables at all (heading regexes required the keyword immediately after `#`/whitespace, but the actual headings are numbered — e.g. `### 3.3 CLI Arguments` — so `_CLI_HEADING_RE` never reused matched, and `_CLI_HEADING_RE` itself also lacks "Arguments"/"Options"). Also found `check_error_handling_table`'s heading-based path flagged every `\|`-starting line under a matching heading (separator + every data row), not just the table header, causing 5 spurious findings elsewhere. Fixed: added a dedicated `_CLI_ARG_HEADING_RE` (CLI/Arguments/Options, tolerating a numeric section prefix) instead of reusing the shared `_CLI_HEADING_RE`; added the same numeric-prefix tolerance to `_ERROR_HEADING_RE`; changed `check_error_handling_table`'s heading-based path to flag only a line immediately followed by a Markdown table separator row (new `_TABLE_SEPARATOR_ROW_RE`), not every subsequent table row; widened `_ERROR_ACTION_TABLE_HEADER_RE` to also match a plain 2-column `\| Case \| Action \|` header (was requiring 3+ columns). Re-verified via Step 3e re-run below. |
| 2 | Add or update tests per Validation plan | Completed | 20260920-091500 | 20260920-091500 | N/A: unit tests are added by seq 02 (`tests/tools/test_check_docs_content_policy.py`), not this document. Confirmed this document's change does not break seq 02's target: `uv run pytest tests/tools/test_check_docs_content_policy.py -v` (the 23 pre-existing tests, seq 02 not yet applied) — 23 passed, 0 failed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-091500 | 20260920-091500 | `tools/`-scope validation per `routing.md` "Adding a new tool": `ruff format`/`ruff check` clean; `mypy tools/check_docs_content_policy.py` clean; `bandit tools/check_docs_content_policy.py` clean (0 issues, 706 lines); `radon cc` — new functions B(7)-C(13), within the existing C(17) ceiling. Full-tree smoke test (post-fix): pre-change 30-warning baseline fully unchanged (confirmed via sorted diff, zero removed/modified lines) + 22 new findings (4 expected at `chunksplitter.md` lines 44/188/195/288, plus 18 genuine additional instances of the same patterns elsewhere in `docs/`, e.g. `docs/03_rag_02_02_ingestion_pipeline-crawler.md:39`'s TypedDict table for `WebCrawler` — spot-checked as a true positive, consistent with the source memo's claim that this pattern is widespread, not isolated to `chunksplitter.md`). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-091500 | 20260920-091500 | N/A: `tools/TOOL_DESCRIPTIONS.md`/`routing.md` updates are covered by seq 03/seq 04, this same pass |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (add the four new detection functions)
- **Source issue**: issues/done/20260920-084638_docreftool01_add-a-docs-checker-for-implementation-reference-content.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-085652_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-090331
- **Related target files**: tools/check_docs_content_policy.py
