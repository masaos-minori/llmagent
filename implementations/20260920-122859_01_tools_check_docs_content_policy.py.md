## Goal
Add `check_code_fallback_value_comparison` to
`tools/check_docs_content_policy.py` (REQ-001), detecting a design document
restating a "code default/fallback vs. operational/production value"
comparison — in a table-header shape and a prose/cell-phrase shape — and
wire it into `main()`.

## Scope
In scope: add 2 new module-level regex constants and 1 new `check_*`
function; add exactly one new `all_issues +=` line in `main()`. Out of
scope: any change to the existing 15 `check_*` functions, their regex
constants, or `main()`'s existing lines; any `docs/*.md` file edit.

## Assumptions
- Both detection paths are implemented inside one function
  (`check_code_fallback_value_comparison`), mirroring
  `check_error_handling_table`'s existing two-path structure — confirmed
  present at `tools/check_docs_content_policy.py:645-702` (Read,
  2026-09-20) — per the Plan's own Assumptions.
- `docs/03_rag_05_1-configuration-reference.md`'s "1.4" section will also
  be flagged by the phrase-shaped path; this is accepted per the Plan's
  Design ("Corrected understanding: config-reference.md exemption"), not a
  defect to fix in this row.

## Design decisions
- Header-shaped path: a table header row containing both a `Code
  Fallback`/`Fallback Value`-style column and a `Production Value`/
  `Operational Value`-style column, via regex
  `_CODE_FALLBACK_TABLE_HEADER_RE`.
- Phrase-shaped path: any line (table row or prose) containing both a
  `code default`/`code fallback` phrase and an `operational`/`production`
  phrase, in either order, via regex `_CODE_FALLBACK_PHRASE_RE`.
- If a line matches the header-shaped path, skip the phrase-shaped check
  for that same line (avoids double-reporting the same line once per
  path) — matches the observed behavior that
  `docs/03_rag_02_02_ingestion_pipeline-crawler.md`'s own header line
  ("| Parameter | Code Fallback Value | Production Value
  (config/crawler.toml) |") independently matches both candidate regexes.
- Both paths respect `_is_guard_start`/`_is_guard_end`, matching all 15
  existing checks.
- Use one shared message text for both paths (matching
  `check_error_handling_table`'s existing precedent of one message text
  for its two paths), rather than two different messages.

## Alternatives considered
- Two separate `check_*` functions (one per path) — rejected per the
  Plan's Assumptions: a single function avoids double work and matches the
  source Issue's own "one new check function" framing.
- Suppressing `docs/03_rag_05_1-configuration-reference.md`'s finding via a
  filename-based exemption — rejected per Plan Design: no existing check in
  this tool implements a filename-based exemption; the accepted precedent
  is `docs/03_rag_05_4-error-handling-reference.md`'s existing, unexempted
  `check_error_handling_table` finding.

## Implementation
### Target file
tools/check_docs_content_policy.py

### Procedure
1. Add two new module-level regex constants near the other
   `_CODE_*`/`_TYPED_DICT_*`-style constants (after `_TABLE_SEPARATOR_ROW_RE`
   and `_MIN_JSON_EXAMPLE_LINES`, i.e. after line 95):
   ```python
   _CODE_FALLBACK_TABLE_HEADER_RE = re.compile(
       r"^\s*\|.*\b(?:Code\s+Fallback|Fallback\s+Value)\b.*\|.*"
       r"\b(?:Production|Operational)\s+Value\b",
       re.IGNORECASE,
   )
   _CODE_FALLBACK_PHRASE_RE = re.compile(
       r"\b(?:code\s+default|code\s+fallback)\b.*\b(?:operational|production)\b"
       r"|\b(?:operational|production)\b.*\b(?:code\s+default|code\s+fallback)\b",
       re.IGNORECASE,
   )
   ```
2. Add the new function after `check_full_json_example` (after line 745)
   and before `main()`:
   ```python
   def check_code_fallback_value_comparison(files: list[DocFile]) -> list[Issue]:
       """Flag a table header or prose/cell line stating both a code-level
       default/fallback value and a separate operational/production value for
       the same parameter — a comparison that duplicates config already
       canonically documented in a configuration-reference doc, and risks the
       same staleness already observed once in this corpus (see
       skills/DESIGN.md "No concrete configuration values").

       Two independent detection paths: a header-shaped table (dedicated
       Code-Fallback/Production-Value columns) and a phrase-shaped line (a
       code-default/fallback phrase and an operational/production phrase
       together, in either order). If a line matches the header-shaped path,
       the phrase-shaped path is skipped for that same line to avoid
       double-reporting.

       Known, accepted false positive: a canonical configuration-reference
       doc that legitimately states this same comparison as part of its own
       role is not exempted here — no check in this tool uses a
       filename-based exemption; see this repository's Plan history for the
       accepted-outcome rationale (the same precedent already applies to
       check_error_handling_table's unexempted canonical-doc finding).
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
               if _CODE_FALLBACK_TABLE_HEADER_RE.search(line):
                   issues.append(
                       Issue(
                           file=doc.rel_path,
                           line_no=i,
                           severity="WARNING",
                           message=(
                               "code-fallback-vs-operational-value comparison — "
                               "see skills/DESIGN.md Docs content policy — remove"
                           ),
                       )
                   )
                   continue
               if _CODE_FALLBACK_PHRASE_RE.search(line):
                   issues.append(
                       Issue(
                           file=doc.rel_path,
                           line_no=i,
                           severity="WARNING",
                           message=(
                               "code-fallback-vs-operational-value comparison — "
                               "see skills/DESIGN.md Docs content policy — remove"
                           ),
                       )
                   )
       return issues
   ```
3. In `main()`, add one new line immediately after
   `all_issues += check_full_json_example(files)`:
   ```python
   all_issues += check_code_fallback_value_comparison(files)
   ```

### Method
Three separate `Edit` calls (old_string/new_string): (1) insert the two
regex constants, (2) insert the new function, (3) insert the one new
`main()` line. Each is independently revertable.

### Details
Do not reorder or modify any of the 15 existing regex constants, functions,
or `main()` lines. Preserve the exact `_is_guard_start`/`_is_guard_end`
pattern and `Issue(file=..., line_no=..., severity=..., message=...)`
keyword-argument style all 15 existing checks already use, for consistency.

## Compatibility considerations
Report-only (`WARNING` severity), consistent with all 15 existing checks.
No change to the tool's CLI, exit-code behavior, or any existing check's
output. This is not a public API in the runtime sense — it is a standalone
report-only script invoked via `uv run python tools/check_docs_content_policy.py`.

## Security considerations
N/A: pure regex-based text scanning of local Markdown files, no external
input, no code execution, no secret-handling path.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit reverting
the 3 Method edits — no data migration or state change is involved. Each
edit is independently revertable.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` (full-tree; confirm
  new findings appear for the 3 confirmed files in the Plan's Background,
  plus the accepted `docs/03_rag_05_1-configuration-reference.md` case) —
  see the sibling test-file procedure for the unit-test-level validation.
- `uv run ruff format tools/check_docs_content_policy.py`, `uv run ruff
  check tools/check_docs_content_policy.py`, `uv run mypy
  tools/check_docs_content_policy.py` — standard validation sequence.
- `uv run radon cc tools/check_docs_content_policy.py -s`, `uv run vulture
  tools/check_docs_content_policy.py --min-confidence 80`, `uv run bandit
  tools/check_docs_content_policy.py` — compare against the Plan's baseline
  (worst grade C pre-existing; 0 vulture/bandit findings).

## Completion criteria
`check_code_fallback_value_comparison` exists, follows the
`check_*(files: list[DocFile]) -> list[Issue]` signature, is wired into
`main()`; running the tool produces the expected new findings (Plan AC-1,
AC-2); `ruff`/`mypy`/`radon`/`vulture`/`bandit` report no new issue relative
to the Plan's baseline.

## Out of scope
- The 3 unit tests for this new function — tracked in the sibling
  `tests/tools/test_check_docs_content_policy.py` procedure document
  (REQ-002).
- The `tools/TOOL_DESCRIPTIONS.md` update — tracked in its own sibling
  procedure document (REQ-003).
- Any `docs/*.md` file edit.

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
- **Requirement ID**: `REQ-001` — add check_code_fallback_value_comparison and wire into main()
- **Source issue**: issues/20260920-102200_doccfgtool01_detect-code-fallback-vs-operational-value-duplication-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-114319_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-122859
- **Related target files**: tools/check_docs_content_policy.py
