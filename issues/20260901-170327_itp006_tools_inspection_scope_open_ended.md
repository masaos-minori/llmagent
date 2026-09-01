# Repository Tool Usage's `tools/` inspection scope is open-ended

## Priority
Low

## Summary
`rules/ai-execution.md` Repository Tool Usage rule #1 requires that "`tools/` MUST
be inspected for a tool that already covers the need" before an ad hoc script or
generic command is used, but does not state whether that inspection is bounded to
the tools a workflow's own `Toolchain` section already names, or requires scanning
the entire `tools/` directory (currently 25+ scripts) each time a new "need"
arises during a cycle.

## Background
`rules/ai-execution.md` Repository Tool Usage:
1. "Before creating an ad hoc script or using an equivalent generic command,
   `tools/` MUST be inspected for a tool that already covers the need."
2. "Only tools relevant to the active workflow and its approved scope MAY be
   considered — every tool under `tools/` MUST NOT be run indiscriminately."

Rule 2 bounds *execution* ("MUST NOT be run indiscriminately") but rule 1's
*inspection* requirement has no stated bound — read literally, "MUST be inspected"
applies per-need, and a workflow like `issue-to-plan` that surfaces several
distinct one-off needs across Steps 2-6 (symbol search, dependency tracing,
validation-quality checks, scaffolding, archival) could re-trigger a full `tools/`
scan multiple times per cycle.

Separately, `skills/issue-to-plan/workflow.md`'s own `Toolchain` section now names
a specific, closed set of tools relevant to this workflow (`rg`/`fd`/`ast-grep`,
`radon`/`vulture`/`semgrep`/`bandit`/`diff-cover`/`pytest-testmon`,
`tools/generate_workitem.py`, `tools/manage_workitem_stage.py`) — but the
relationship between that closed list and `rules/ai-execution.md`'s open-ended
"tools/ MUST be inspected" rule is not stated: does the `Toolchain` section
*satisfy* rule 1 for this workflow (i.e. inspection is done once, at Step 0, by
reading that section), or does rule 1 still require a fresh `tools/` scan whenever
a need arises that the `Toolchain` section does not explicitly cover?

## Problem
Without a stated relationship, two readings both fit the current text:
1. The `Toolchain` section is the workflow's authoritative, closed answer to rule
   1 — no further `tools/` scanning is needed within this workflow.
2. Rule 1 is a standing, per-need obligation that the `Toolchain` section merely
   summarizes for convenience — a genuinely new need (not listed in `Toolchain`)
   still requires scanning all of `tools/` before falling back to an ad hoc
   command.

Reading 2 is the more literal reading of `rules/ai-execution.md`'s wording, but it
makes the inspection scope open-ended and re-triggerable an unbounded number of
times per cycle, which is inconsistent with the workflow's otherwise-scoped
`Toolchain` section.

## Reason for Change
Clarifying this removes ambiguity about how much repeated `tools/`-directory
inspection is actually required, and makes the `Toolchain` sections added to
`issue-to-plan`/`plan-to-implementation-procedure`/`code-implementation`'s
`workflow.md` files meaningfully authoritative rather than merely advisory.

## Implementation Intent
Add a short clarification to `rules/ai-execution.md` Repository Tool Usage stating
that a workflow's own `Toolchain` section (where one exists) satisfies rule 1 for
the needs it names; rule 1's "MUST be inspected" obligation applies in full only
when a need arises that the `Toolchain` section does not cover.

## Target Files or Areas
- `rules/ai-execution.md` (Repository Tool Usage)

## Required Changes
- Add one clarifying sentence (or short paragraph) to Repository Tool Usage stating
  the relationship between a workflow's `Toolchain` section and rule 1's inspection
  obligation.

## Constraints
Do not weaken rule 1 for needs genuinely outside a workflow's stated `Toolchain`
list — the clarification narrows *repeated* inspection for *already-covered* needs
only, not the general obligation to check `tools/` before writing an ad hoc script
for something new.

## Acceptance Criteria
- `rules/ai-execution.md` Repository Tool Usage states explicitly that a
  workflow's `Toolchain` section satisfies rule 1 for the needs it names.
- The clarification does not remove rule 1's obligation for needs not covered by
  a `Toolchain` section.

## Testing Expectations
Manual review: confirm the added sentence is consistent with rule 2's existing
"only tools relevant to the active workflow... MAY be considered" scoping.

## Documentation Impact
N/A: internal shared-rule fix; no `docs/*.md` file describes this mechanism.

## Out of Scope
- Changing which tools appear in any workflow's `Toolchain` section.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — this is a wording clarification, not a behavior change requiring
further investigation.

## AI Implementation Instruction
Read `rules/ai-execution.md` Repository Tool Usage in full, and the `Toolchain`
sections of `skills/issue-to-plan/workflow.md`,
`skills/plan-to-implementation-procedure/workflow.md`, and
`skills/code-implementation/workflow.md`, before wording the clarification. Keep
the change to the minimum needed to resolve the ambiguity — do not restructure the
existing 12-point Repository Tool Usage list.
