# Add completion criteria to Phase 2/Phase 5 and link Phase 5's tool list to Phase 3's classification table

## Priority
Medium

## Summary
`skills/python-debug-root-cause/workflow.md` Phase 5 (Runtime/Trace Inspection) lists 7 tools with no stated selection logic and no completion condition; Phase 2 (Initial Observability) already has clear tool-selection logic but also lacks a completion condition. Phase 3's existing classification table (Reproducibility/Execution model/Failure domain → tool implications) already answers "which tool for Phase 5" but Phase 5 itself never references it.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session. Re-verified during this issue's drafting: Phase 2 (lines 60-68) already states clear priority logic ("Use structlog+jq first... reach for lnav only when... reach for multitail only when... use sentry-sdk only if SENTRY_DSN configured") — the review's initial framing of Phase 2 as lacking tool-selection logic was inaccurate; Phase 2's actual gap is only the missing completion condition. Phase 5 (183-260) genuinely lacks both a selection rule and a completion condition. Phase 3's table (109-120) already maps Execution model/Failure domain to specific Phase 5/6 tools (e.g. "Performance → py-spy, viztracer, tracemalloc") but Phase 5's own section never points back to it.

## Problem
An agent reaching Phase 5 sees 7 tools (viztracer, py-spy, OpenTelemetry, strace, tracemalloc, aiomonitor, ipdb, rich+stackprinter) listed as parallel subsections with no stated rule for which to reach for first, even though Phase 3's table already contains that answer for several of them (Sync → ipdb/stackprinter/py-spy; Performance → py-spy/viztracer/tracemalloc; I/O → strace).

## Reason for Change
Without an explicit link, an agent must either re-derive the tool choice from Phase 3's table on its own initiative (inconsistent across sessions) or fall back to trying tools in the order listed (which is not the file's intended selection principle, per Phase 2's own precedent of stating explicit priority logic).

## Implementation Intent
Add a short lead-in to Phase 5 pointing back to Phase 3's classification table as the tool-selection basis (mirroring Phase 2's own explicit-priority style), and add a "Completed when" line to both Phase 2 and Phase 5.

## Target Files or Areas
- `skills/python-debug-root-cause/workflow.md`

## Required Changes
- Add a lead-in sentence to Phase 5 (before the tool subsections): "Select the tool(s) using Phase 3's classification table (Execution model / Failure domain columns) — do not try tools in the order listed below without that basis."
- Add to Phase 2: "**Completed when**: at least one observability source above has surfaced enough signal to inform Phase 3's classification, or all applicable sources were checked and none did."
- Add to Phase 5: "**Completed when**: the tool(s) selected via Phase 3's table have been run and produced either a concrete lead for Phase 6's hypothesis table or a confirmed absence of signal from that tool."

## Constraints
Do not restate Phase 3's table inside Phase 5 — reference it by name, since the table already exists and duplicating it risks the two drifting apart.

## Acceptance Criteria
- Phase 5 explicitly references Phase 3's classification table as its tool-selection basis.
- Phase 2 and Phase 5 each have an explicit "Completed when" line.
- Phase 3's table is not duplicated inside Phase 5.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only workflow file. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `skills/python-debug-root-cause/workflow.md`.

## Out of Scope
- Sub-splitting Phase 5 into lettered sub-steps (5a/5b/...) — the review's initial suggestion, but not pursued here since Phase 3's table already provides the selection structure once referenced; re-splitting on top of that would be redundant.
- Any other Phase in this file — already reviewed and found adequate (Phase 1, 6, 9 already have completion conditions per this same review).
- Any other evaluation criterion from the same review — tracked in separate issues.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — Phase 3's table was directly re-read during this issue's drafting and confirmed to already cover the tool-selection answer this issue links to.

## AI Implementation Instruction
Add only the lead-in sentence and two completion-condition lines described in Required Changes; do not duplicate Phase 3's table content inside Phase 5, and do not sub-split Phase 5 into lettered sub-steps.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115344
- **Related target files**: skills/python-debug-root-cause/workflow.md
