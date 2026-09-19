# Extend check_docs_content_policy.py with additional mechanical-content checks instead of a new tool

## Priority
Medium

## Summary
A proposed documentation-slimming policy plans a new `check_docs_mechanical.py` tool
to detect mechanical/duplicated content in `docs/*.md`, but `tools/check_docs_content_policy.py`
already exists, is registered as `GV-021` in the Governance Verification Matrix, and
already detects several of the proposed categories (full file trees, class/function/
method index-table headers, implementation-location mappings, literal port numbers).
Extend this existing tool instead of adding a second one.

## Background
N/A: covered by Summary.

## Problem
Confirmed by reading `tools/check_docs_content_policy.py`: its `check_index_table`
only matches a table header naming Function/Method/Class alongside
Signature/Description — it does not match a plain field/type/default-value table (e.g.
a config dataclass's field list) that names none of those header words. Its
`check_full_file_tree` only fires near a "File Structure"/"Directory"/"File Tree"
heading. Neither this tool nor any other existing `tools/check_docs_*.py` script
detects: default-value restatement outside a table, a configuration-file-to-doc
correspondence table, a CLI-command enumeration, environment-setup command sequences,
or a DDL/schema block restated in prose.

## Reason for Change
A second, separately-registered tool covering overlapping ground duplicates
`GV-021`'s existing role in the Governance Verification Matrix and its existing
Warning/`report_and_exit` conventions, which is exactly the kind of redundancy the
underlying policy is meant to eliminate.

## Implementation Intent
Add new check functions to `tools/check_docs_content_policy.py`, following its
existing pattern (one `check_*(files: list[DocFile]) -> list[Issue]` function per
category, each appended to `main()`), for: default-value restatement, plain
field/type/default tables not caught by the existing Function/Method/Class-specific
header regex, configuration-file inventory correspondence tables, CLI-command
enumerations, environment-setup command sequences, and DDL/schema blocks. Keep each
new check's severity `WARNING` (report-only), matching the existing checks and
`GV-021`'s current "Partial" rollout status.

## Target Files or Areas
`tools/check_docs_content_policy.py`; `docs/00_governance_04_documentation-checks.md`
(update `GV-021`'s description); `tests/tools/` (new/extended test coverage — exact
file to be confirmed at implementation time)

## Required Changes
- Add one check function per new category listed in Implementation Intent, each
  returning `Issue` objects with `severity="WARNING"` and a message citing the same
  `skills/DESIGN.md` Docs content policy reference the existing checks use.
- Append each new function's call to `main()`.
- Update `GV-021`'s row in `docs/00_governance_04_documentation-checks.md`'s
  Governance Verification Matrix to describe the expanded category coverage (still
  Warning/Partial — do not change its blocking status in this issue).
- Add unit tests for each new check covering a true-positive and a plausible
  false-positive case (e.g. a legitimately short, non-mechanical table must not be
  flagged).

## Constraints
Do not change any existing check function's behavior or the tool's `WARNING`/
report-only severity; do not promote `GV-021` to blocking as part of this issue.

## Acceptance Criteria
- Each new check function flags a constructed true-positive example and does not
  flag a constructed false-positive example.
- `tools/check_docs_content_policy.py` continues to run cleanly (exit reflects only
  WARNING findings, no crash) against the full `docs/` tree.
- `GV-021`'s Governance Verification Matrix description reflects the new category
  coverage.

## Testing Expectations
Add unit tests for each new check function (true-positive and false-positive cases).
Run `uv run pytest` on the new/updated test file, plus `uv run python
tools/check_docs_content_policy.py` against the full `docs/` tree to confirm no
unexpected new-finding noise beyond what is expected.

## Documentation Impact
Update `GV-021`'s row in `docs/00_governance_04_documentation-checks.md` (see Required
Changes) — no other `docs/*.md` change is required.

## Out of Scope
Fixing any violation the new checks surface in existing `docs/*.md` content — that is
separate content-migration work, scoped once the docs-inventory re-baseline and the
metadata-guidelines consolidation issues land.

## Dependencies
Benefits from the metadata-guidelines consolidation issue landing first (so new
checks cite a single, consolidated rule location), but is not strictly blocked by it.

## Unresolved Questions
The exact test file location for `check_docs_content_policy.py`'s own tests was not
confirmed during this issue's drafting — locate or create it during implementation
(likely `tests/tools/test_check_docs_content_policy.py`, following the naming
convention of neighboring test files).

## AI Implementation Instruction
Follow the existing file's exact function/registration pattern — do not introduce a
decorator-based registry (that pattern belongs to `check_docs_quality.py`, a different
tool) or otherwise restructure the file beyond adding new functions and their `main()`
calls. Keep new checks conservative (favor missing a real case over flagging a false
positive), consistent with this tool's current "Partial" rollout status.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260918-130159
- **Related target files**: tools/check_docs_content_policy.py, docs/00_governance_04_documentation-checks.md
