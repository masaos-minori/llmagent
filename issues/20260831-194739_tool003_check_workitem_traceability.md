# Add `tools/check_workitem_traceability.py` to detect orphaned or stale links across issues/plans/implementations

## Priority
Medium

## Summary
The issue → plan → implementation-procedure → implementation pipeline links each stage back to
the previous one via Traceability fields (`Source issue`, `Source plan`,
`Source implementation procedure`), but nothing currently checks that these links stay valid:
that a referenced source file still exists, that its content hasn't since made the downstream
document obsolete, or that every `issues/*.md`/`plans/*.md` file has actually progressed to its
next stage (or a recorded reason it hasn't). Add a script that walks `issues/`, `plans/`, and
`implementations/` (including their `done/` subdirectories) and reports these gaps.

## Background
During the 2026-08-31 ADR-004 rewrite, `issues/20260831-173019_adr004_01_mcp_config_failure_model_alignment.md`
was found to instruct the opposite of what the (later-revised) current ADR-004 requires — a
downstream consumer following that issue without re-checking its premise would implement the
wrong thing. This class of drift (a stage-N document whose upstream source has since changed
underneath it) is currently only caught by an agent noticing it during unrelated work, not by any
automated check.

## Problem
(Evidence: Explicit in docs) `skills/issue-to-plan`'s Step 1.5 duplicate detection and
`skills/plan-to-implementation-procedure`'s Step 3 duplicate-work check both rely on Traceability
fields being accurate, but no tool verifies the fields themselves stay accurate over time as
referenced files change, move to `done/`, or are superseded by a later issue.

## Reason for Change
Without this check, staleness like the `adr004_01` case is found only by chance during unrelated
work. A dedicated checker turns "an agent happened to notice" into a repeatable, on-demand
verification step.

## Implementation Intent
Add `tools/check_workitem_traceability.py` that: (1) parses every `issues/*.md`, `plans/*.md`,
and `implementations/*.md` file (plus `done/` subdirectories) and extracts each `Source issue`/
`Source plan`/`Source implementation procedure`/`Source requirement` value from its Traceability
section; (2) reports any referenced source path that does not exist; (3) reports any `issues/*.md`
file (not in `done/`) that has no plan referencing it as `Source issue` and has been present
longer than a configurable age, as a "no plan yet" signal (informational, not necessarily a
problem); (4) reports any `plans/*.md` file (not in `plans/done/`) with no implementation
procedure referencing it; (5) flags — as a best-effort heuristic, not a hard rule — any issue file
whose title/summary keywords suggest it targets a document (e.g., an ADR by number) that has
since been substantially edited or deleted, prompting manual review rather than an automatic
verdict.

## Target Files or Areas
- `tools/check_workitem_traceability.py` — new file
- `issues/`, `plans/`, `implementations/` (including `done/` subdirectories) — read-only input
- `tools/TOOL_DESCRIPTIONS.md` — must document the new tool

## Required Changes
- Implement the traceability graph walk and the four report categories above (missing source
  file, issue with no plan yet, plan with no procedure yet, and the best-effort
  stale-target heuristic).
- Provide a machine-readable output mode (e.g., `--format json`) alongside a human-readable
  summary, consistent with `generate_mcp_inventory.py`'s `--format json|csv` precedent.
- Add an entry to `tools/TOOL_DESCRIPTIONS.md`'s checker table.

## Constraints
- The stale-target heuristic (item 5) must not auto-resolve or auto-close anything — it only
  surfaces a candidate for human/agent review, since determining whether an issue's premise is
  actually invalidated requires reading both documents in context (as this session's `adr004_05`
  issue did manually).
- Do not modify any `issues/`, `plans/`, or `implementations/` file — this tool only reports.
- Do not treat "no plan yet" or "no procedure yet" as an error by default — these are normal,
  expected states for recently-filed work; make the age threshold configurable and default to a
  generous value.

## Acceptance Criteria
- Running the tool against the current repository state reports zero missing-source-file
  findings (a true negative baseline) and correctly identifies known cases when a source
  file is deliberately removed in a test fixture.
- `tools/TOOL_DESCRIPTIONS.md` documents the new tool; `check_tool_descriptions_sync.py` passes.

## Testing Expectations
Add `tests/tools/test_check_workitem_traceability.py` using fixture directories (not the live
`issues/`/`plans/`/`implementations/` trees) covering: a valid chain (issue → plan → procedure,
all present), a missing-source-file case, an issue with no plan yet, and a plan with no procedure
yet. Apply the standard validation sequence in `rules/toolchain.md`.

## Documentation Impact
Add the new tool to `tools/TOOL_DESCRIPTIONS.md`.

## Out of Scope
- Automatically fixing, closing, or superseding any stale issue/plan/procedure.
- The other four tools proposed alongside this one, tracked as separate issues.

## Dependencies
N/A: none — independently buildable, though most useful once
`tools/generate_workitem.py` (tracked separately) standardizes Traceability field formatting.

## Unresolved Questions
What default "age" threshold should trigger a "no plan yet" / "no procedure yet" report — needs
an owner decision on a reasonable default (e.g., 7 days, matching
`00_governance_01_documentation-policy.md`'s "New ADRs must be created within one week"
precedent, though that rule is about a different artifact).

## AI Implementation Instruction
Read a representative sample of existing `issues/*.md`, `plans/*.md`, and
`implementations/*.md` Traceability sections before writing the parser, to confirm the exact
field names and formatting in current use — do not assume a rigid schema without checking real
examples first.
