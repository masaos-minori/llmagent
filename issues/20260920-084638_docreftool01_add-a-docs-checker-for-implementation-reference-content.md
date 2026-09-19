# Add a docs checker for implementation-reference content

## Priority
Medium

## Summary
Add a repository tool (e.g. `tools/check_docs_implementation_reference.py`) that
scans `docs/*.md` for the implementation-reference patterns `skills/DESIGN.md`'s
"Avoid implementation-reference duplication" policy prohibits — TypedDict/DTO field
tables, method-signature catalogs, full JSON payload examples, CLI argument tables,
and per-exception handling tables — and reports which files violate the policy, so
this content can be found without a manual, ad hoc `grep` pass over every file.

## Background
No existing `routing.md`-listed tool checks for this. `tools/check_docs_quality.py`
and `tools/check_docs_structure.py` check structural/formatting concerns (headings,
front matter, links, size); neither inspects a document's content for embedded
implementation-reference material. A companion issue
(`issues/20260920-084526_docref01_isolate-implementation-reference-content-from-rag-design-docs.md`)
found this content by manual inspection in one file
(`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`) after a review raised the
concern that RAG design documents in general are affected by this pattern.

## Problem
There is currently no way to answer "which `docs/*.md` files violate the
Avoid-implementation-reference-duplication policy" other than manual review of every
file — impractical at the current scale of `docs/`, and impossible to enforce going
forward, since a new violation can land silently in any future doc edit with nothing
to catch it.

## Reason for Change
Without a detection tool, the companion issue's remediation can only ever cover the
files someone happens to inspect by hand, and any future doc edit can reintroduce the
same kind of violation with nothing to catch it before or after commit. Per
`AGENTS.md` Global Rule 7, a check that would otherwise be repeated by hand across
many files belongs in a script under `tools/`.

## Implementation Intent
Add a new tool under `tools/`, following the existing pattern of
`tools/check_docs_quality.py`/`tools/check_docs_structure.py` (read-only, reports
findings, does not edit files). For each `docs/*.md` file, detect indicators of the
categories `skills/DESIGN.md` Avoid implementation-reference duplication names (the
companion issue expands this wording to explicitly cover the categories below):
- a Markdown table whose header row matches a field/type/signature/parameter shape
  (e.g. columns named `Field`/`Type`/`Parameter`/`Signature`/`Argument`)
- a fenced code block containing a JSON object above a size threshold
- a table or list under a heading naming "CLI"/"Arguments"/"Options"
- a table under a heading naming "Error"/"Exception"/"Error Handling"

Treat this as a heuristic, best-effort detector, consistent with
`check_docs_quality.py`'s existing structural checks — false positives are
acceptable if flagged for human review, but false negatives should be minimized for
the categories above. Report the file path, the matched heading or table, and which
category it matched.

Add the new tool to `routing.md`'s "When to run which tool" table (situation: "Any
`docs/*.md` file was added or edited") alongside the existing doc checkers, per
`AGENTS.md` Global Rule 9.

## Target Files or Areas
- New file: `tools/check_docs_implementation_reference.py`
- `tools/TOOL_DESCRIPTIONS.md` (register the new tool)
- `routing.md` (add a row to "When to run which tool")

## Required Changes
- Implement the detection heuristics described in Implementation Intent.
- Add a report-only mode consistent with the other `check_docs_*.py` tools (no file
  mutation).
- Register the tool in `tools/TOOL_DESCRIPTIONS.md`.
- Add a row to `routing.md`'s "When to run which tool" table.
- Run the tool once against the current `docs/` tree as a smoke test and record the
  finding count (acting on every finding is out of scope for this issue).

## Constraints
Read-only tool — must not modify any `docs/*.md` file. Follow `routing.md`'s "Adding
a new tool" validation sequence (`ruff format`/`ruff check`, `mypy` with the explicit
file path, `bandit`, a manual smoke test against live `docs/` content, and
`tools/check_tool_descriptions_sync.py`).

## Acceptance Criteria
- `uv run python tools/check_docs_implementation_reference.py` runs against the
  current `docs/` tree and reports
  `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` as a finding (the confirmed
  violation from the companion issue).
- The tool is registered in `tools/TOOL_DESCRIPTIONS.md` and in `routing.md`'s "When
  to run which tool" table.
- `uv run python tools/check_tool_descriptions_sync.py` passes.
- `ruff check`, `mypy tools/check_docs_implementation_reference.py`, and `bandit
  tools/check_docs_implementation_reference.py` pass.

## Testing Expectations
Manual smoke test against live `docs/` content (per `routing.md`'s "Adding a new
tool" step 4) — confirm the tool's actual output on the current `docs/` tree, not
only a hand-crafted fixture. No `tests/` unit tests are required for a `tools/`
script, per existing repository convention (see `routing.md` "Adding a new tool").

## Documentation Impact
Register the new tool in `tools/TOOL_DESCRIPTIONS.md` and add it to `routing.md`'s
"When to run which tool" table — both are required updates, not optional, per
`AGENTS.md` Global Rule 9.

## Out of Scope
- Fixing any violation the tool finds — tracked by the companion issue and any
  follow-up issue the tool's full output motivates.
- Auto-fixing or auto-rewriting docs — this tool only detects and reports.
- Any change to `skills/DESIGN.md`'s policy wording — tracked by the companion issue.

## Dependencies
Complements
`issues/20260920-084526_docref01_isolate-implementation-reference-content-from-rag-design-docs.md`
— that issue's manual finding is this tool's first acceptance-criterion target; this
tool's full output can scope that issue's "Other files" row beyond what its own
manual `grep` found.

## Unresolved Questions
Exact heuristics/thresholds (e.g. how large a JSON code block must be to count as a
full payload example rather than a short illustrative snippet) are not fully
specified — left as an implementation-time judgment call, consistent with
`check_docs_quality.py`'s existing heuristic-based structural checks.

## AI Implementation Instruction
Follow the existing `check_docs_quality.py`/`check_docs_structure.py` pattern for
tool structure, CLI shape, and output format — do not invent a different reporting
convention. Keep the tool read-only. Do not also fix the companion issue's findings
in this issue — this issue is the detection tool only.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-084638
- **Related target files**: tools/check_docs_implementation_reference.py,
  tools/TOOL_DESCRIPTIONS.md, routing.md
