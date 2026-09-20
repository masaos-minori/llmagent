# Extend check_docs_content_policy.py to catch TypedDict/CLI-argument/exception/JSON-example content

## Priority
Medium

## Summary
`tools/check_docs_content_policy.py` already exists and already detects most of
`skills/DESIGN.md`'s "Docs content policy — remove" implementation-detail
categories (file trees, per-file descriptions, method/class index tables, field/type
tables, config-inventory tables, CLI-command enumerations, DDL blocks), but its
existing detection patterns do not match a TypedDict-labeled table, a CLI
argument/parameter table (as opposed to a repeated command enumeration), a generic
Case/Action-style exception-handling table, or a full JSON payload example — so it
did not flag the confirmed violation in
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` (see companion issue).
Extend the existing tool with detectors for these four gaps, and register it in
`routing.md`'s "When to run which tool" table, where it is currently missing
entirely.

## Background
An earlier draft of this issue proposed creating a brand-new tool
(`tools/check_docs_implementation_reference.py`). Verified during adversarial
review that this was incorrect: `tools/check_docs_content_policy.py` already exists,
is already registered in `tools/TOOL_DESCRIPTIONS.md`, and already implements 11
distinct check functions covering most of the target behavior. Running it against
the full `docs/` tree (`uv run python tools/check_docs_content_policy.py`) produces
30 warnings across many files, confirming it is live and working — but it does not
flag `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` at all, despite that
file's confirmed TypedDict field table, CLI argument table, error-handling table, and
full JSON payload example (see the companion issue,
`issues/20260920-084526_docref01_isolate-implementation-reference-content-from-rag-design-docs.md`).
Inspection of the tool's source explains why:
- `check_index_table`'s header regex requires a `Function`/`Method`/`Class` column —
  `chunksplitter.md`'s TypedDict table header is `| TypedDict | Purpose |`, which
  matches neither this nor `check_field_type_table`'s `Field`/`Key` +
  `Type`/`Default` requirement.
- `check_cli_command_enumeration` only flags 3+ fenced `bash` blocks under a CLI
  heading (a *command enumeration*) — it does not inspect Markdown tables at all, so
  `chunksplitter.md`'s `| Argument | Description | Default |` table is invisible to
  it.
- No existing check function inspects a table under an "Error"/"Exception"/"Error
  Handling" heading — `chunksplitter.md`'s `| Case | Action |` table matches no
  existing header regex.
- No existing check function flags a full JSON payload example at all (distinct from
  `tools/check_docs_quality.py`'s `check_json_not_wrapped`, which only verifies a JSON
  block is fenced, not whether the block itself is implementation-detail content that
  should be removed).

Separately, `routing.md`'s "When to run which tool" table lists
`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_consistency.py`,
`check_needs_confirmation_inventory.py`, `check_tool_descriptions_sync.py`, and
`check_skills_references.py` for a `docs/*.md` edit, but does not list
`check_docs_content_policy.py` at all — confirmed via `grep -n
"check_docs_content_policy" routing.md`, which returns no match. This is a
documentation gap independent of the detection-pattern gaps above: the tool exists
and runs cleanly, but nothing in the routing table tells an implementer to run it.

## Problem
Two independent, compounding gaps mean the implementation-detail content this issue
and its companion issue care about is neither reliably detected nor discoverable as
a check to run: (1) the existing detector's patterns miss four content shapes that
do occur in practice, and (2) even the checks that do exist are not listed in the
routing table an implementer is expected to consult before finishing a `docs/*.md`
edit.

## Reason for Change
Without the four new detectors, `check_docs_content_policy.py` gives a false sense
of coverage — it reports 30 findings but silently misses the exact file the
companion issue confirmed by hand. Without the `routing.md` registration, an
implementer following the routing table's own stated process ("Run the applicable
checker below instead of relying on manual review alone") has no way to know this
tool exists at all.

## Implementation Intent
Extend `tools/check_docs_content_policy.py` in place — do not create a new file;
the existing module's structure (one `check_*(files) -> list[Issue]` function per
category, wired into `main()`, following the existing regex-and-line-scan style) is
the correct home for these additions per `skills/DESIGN.md` File Split Rule's
"shared normalization" principle. Add:
- `check_typed_dict_table` — a table header matching a `TypedDict`/`DTO`-labeled
  first column (e.g. `| TypedDict | Purpose |`), independent of
  `check_field_type_table`'s `Field`/`Key` requirement.
- `check_cli_argument_table` — a Markdown table (not a bash-block enumeration) under
  a CLI/Arguments/Options heading, with a header column named
  `Argument`/`Parameter`/`Option`/`Flag`.
- `check_error_handling_table` — a table under a heading naming
  `Error`/`Exception`/`Error Handling`, or with a `Case`/`Action`-shaped header.
- `check_full_json_example` — a fenced JSON code block above a line-count threshold
  (mirroring `check_docs_content_policy.py`'s existing `_MIN_MECHANICAL_TABLE_ROWS`/
  `_MIN_CLI_BLOCKS` conservative-threshold pattern, so a short illustrative snippet
  is not flagged).

Wire all four into `main()` alongside the existing 11 checks. Update
`tools/TOOL_DESCRIPTIONS.md`'s two existing `check_docs_content_policy.py` entries —
both currently describe only the original five `skills/DESIGN.md`-named categories,
which is already stale relative to the module's actual 11 check functions even before
this issue's four additions; correct both entries to reflect the full, current check
list. Add a `routing.md` "When to run which tool" row: situation "Any `docs/*.md`
file was added or edited" (matching the existing `check_docs_quality.py`/
`check_docs_structure.py` rows), command
`uv run python tools/check_docs_content_policy.py`, notes summarizing report-only
Warning behavior.

The companion issue's `skills/DESIGN.md` wording expansion (naming TypedDict field
lists, HTTP request/response examples, CLI argument tables, and per-exception
handling tables explicitly) gives these new detectors an unambiguous policy source to
cite in their `Issue` messages, the same way the existing 11 checks each cite a named
`skills/DESIGN.md` category.

## Target Files or Areas
- `tools/check_docs_content_policy.py` (extend with four new check functions; wire
  into `main()`)
- `tools/TOOL_DESCRIPTIONS.md` (correct both existing entries to list the full,
  current check set)
- `routing.md` (add the missing "When to run which tool" row)

## Required Changes
- Implement `check_typed_dict_table`, `check_cli_argument_table`,
  `check_error_handling_table`, and `check_full_json_example` in
  `tools/check_docs_content_policy.py`, following the existing functions' style
  (guarded-block awareness via `_is_guard_start`/`_is_guard_end`, a conservative
  minimum-rows/lines threshold, an `Issue` citing the relevant `skills/DESIGN.md`
  category).
- Wire all four into `main()`.
- Update both `tools/TOOL_DESCRIPTIONS.md` entries for `check_docs_content_policy.py`
  to list the module's full, current check set (not just the original five
  `skills/DESIGN.md`-named categories).
- Add the missing `routing.md` "When to run which tool" row for
  `check_docs_content_policy.py`.
- Re-run `uv run python tools/check_docs_content_policy.py` against the full `docs/`
  tree and confirm it now flags
  `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` (the confirmed violation).

## Constraints
Read-only tool — must not modify any `docs/*.md` file; this issue only extends the
detector, per the existing module's report-only (Warning) design. Follow
`routing.md`'s "Adding a new tool" validation sequence, which also covers a modified
`tools/*.py` script (`ruff format`/`ruff check`, `mypy` with the explicit file path,
`bandit`, a manual smoke test against live `docs/` content, and
`tools/check_tool_descriptions_sync.py`). Do not change any of the 11 existing check
functions' behavior — this issue is additive only.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` flags
  `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` for its TypedDict table,
  CLI argument table, error-handling table, and full JSON payload example.
- The tool's existing 30 findings (pre-change baseline) still all appear unchanged —
  confirm no existing check function's behavior regressed.
- `routing.md`'s "When to run which tool" table lists `check_docs_content_policy.py`.
- `tools/TOOL_DESCRIPTIONS.md`'s two `check_docs_content_policy.py` entries list the
  module's full, current check set.
- `uv run python tools/check_tool_descriptions_sync.py` passes.
- `ruff check`, `mypy tools/check_docs_content_policy.py`, and `bandit
  tools/check_docs_content_policy.py` pass.

## Testing Expectations
Manual smoke test against live `docs/` content (per `routing.md`'s "Adding a new
tool" step 4) — confirm the tool's actual output on the current `docs/` tree
before/after the change, per Acceptance Criteria above. No `tests/` unit tests are
required for a `tools/` script, per existing repository convention (see `routing.md`
"Adding a new tool").

## Documentation Impact
Update `tools/TOOL_DESCRIPTIONS.md` (both existing entries) and `routing.md`'s "When
to run which tool" table — both are required updates, not optional, per `AGENTS.md`
Global Rule 9.

## Out of Scope
- Fixing any violation the extended tool finds, including the confirmed
  `chunksplitter.md` case — tracked by the companion issue.
- Auto-fixing or auto-rewriting docs — this tool only detects and reports.
- Any change to `skills/DESIGN.md`'s policy wording — tracked by the companion issue.
- Changing the behavior of any of the tool's 11 existing check functions.

## Dependencies
Complements
`issues/20260920-084526_docref01_isolate-implementation-reference-content-from-rag-design-docs.md`
— that issue's manual finding is this issue's first acceptance-criterion target, and
that issue's `skills/DESIGN.md` wording expansion gives the new detectors added here
an explicit policy citation. This issue's extended tool output can scope that issue's
"Other files" row beyond what its own manual `grep` found.

## Unresolved Questions
Exact thresholds for `check_full_json_example` (how many lines/keys before a JSON
block counts as a full payload example rather than a short illustrative snippet) are
not fully specified — left as an implementation-time judgment call, consistent with
the existing module's own conservative-threshold pattern
(`_MIN_MECHANICAL_TABLE_ROWS = 4`, `_MIN_CLI_BLOCKS = 3`).

## AI Implementation Instruction
Extend `tools/check_docs_content_policy.py` in place — do not create a new file, and
do not modify any of its 11 existing check functions' behavior. Match the existing
module's style exactly (function naming, `Issue` construction, guarded-block
handling, conservative minimum-threshold pattern) for the four new functions. Run the
full `docs/` tree smoke test before and after the change and diff the output to
confirm only new findings were added, not that existing findings changed or
disappeared.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-084638
- **Related target files**: tools/check_docs_content_policy.py,
  tools/TOOL_DESCRIPTIONS.md, routing.md
