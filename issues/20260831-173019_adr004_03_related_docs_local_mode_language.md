# Confirm related Specification/Operations documents don't still describe a Local-mode fail-open path

## Priority
Low

## Summary
`docs/adr/ADR-004-environment-profile-fail-fast-fail-open.md`'s revision removed the concept
of a Local execution mode and its Fail-Open/Degraded-startup behavior. One document listed
under ADR-004's own Related Documents section
(`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`) still
contains a "production or local mode" phrase describing startup failure classification. The
other two Related Documents were checked and contain no such language.

## Background
This is a targeted follow-up from the ADR-004 revision, which asked for a check of related
Specification/Operations documents for contradictions without modifying them during that
task. A grep for `required_in_local`/`required_in_production`/`failure_policy` across
`docs/*.md` found no other document referencing those specific identifiers, narrowing this
issue's scope to the one phrase found.

## Problem
`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md` states
(Evidence: Explicit in code): "Failure in `mcp_tool_discovery` is treated as FATAL regardless
of whether it is production or local mode." The conclusion (always FATAL) is still consistent
with ADR-004's current Fail-Fast-only model, but the phrase "production or local mode" implies
two modes exist, which ADR-004 now contradicts (Production is the only supported execution
mode).

## Reason for Change
Leaving a "local mode" reference in an Operations document that a troubleshooting reader might
consult creates a false impression that a local execution mode is still a supported,
documented concept, even though the conclusion it's attached to happens to still be correct.

## Implementation Intent
Reword the sentence to state the FATAL classification without implying multiple execution
modes exist (e.g., drop the "regardless of whether it is production or local mode" clause, or
replace it with language consistent with ADR-004's Production-only model). Do a final targeted
re-read of the sentence's surrounding context to confirm no other nearby text depends on the
production/local distinction before editing.

## Target Files or Areas
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md` — primary target

## Required Changes
- Reword the identified sentence to remove the "production or local mode" phrasing while preserving its FATAL-classification conclusion.
- Scan the same document's surrounding sections for any other implicit reliance on a production/local distinction before closing this issue.

## Constraints
- Do not change the FATAL classification itself — only the wording that implies multiple execution modes.
- Do not perform a broader rewrite of this document beyond the identified sentence and its immediate context.

## Acceptance Criteria
- The document no longer contains "local mode" or equivalent phrasing implying a non-Production execution mode.
- The FATAL classification for `mcp_tool_discovery` failure remains stated and correct.
- `uv run python tools/check_docs_quality.py docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md` shows no new issues.

## Testing Expectations
Documentation-only change; not required beyond the validation command listed above.

## Documentation Impact
This issue is itself the documentation fix.

## Out of Scope
- Any other content in this document unrelated to the identified sentence.
- Re-scanning the entire `docs/` tree for every possible indirect reference to a production/local distinction beyond this document (a full-tree grep for `required_in_local`/`required_in_production`/`failure_policy` and for the two Related Documents already checked found nothing further).

## Dependencies
Follows the ADR-004 revision to a Production-only model.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
- Read the full paragraph surrounding the identified sentence before editing, to confirm the fix doesn't leave a dangling reference.
- Do not change the FATAL classification's substance — only remove the multi-mode implication in the wording.
- Do not expand this into a broader edit of the document.
