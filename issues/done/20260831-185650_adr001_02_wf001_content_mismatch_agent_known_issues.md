# WF-001 in Agent Known Issues describes invariant text that does not match current ADR-001

## Priority
Medium

## Summary
`docs/05_agent_90_inconsistencies_and_known_issues.md`'s WF-001 entry describes INV-01 and
INV-05 as asserting "all execution paths must flow through the Workflow Engine" and "the
Workflow Engine is the sole orchestrator of tool execution" respectively. The current
`docs/adr/ADR-001-workflow-engine-mandatory.md` INV-01 and INV-05 say something different
("workflow definition file missing → abort startup" and "workflow definition validation
failure → abort startup"). The two documents describe the same invariant IDs with unrelated
content.

## Background
Discovered while updating ADR-001 to Accepted status (2026-08-31) and cross-checking its own
embedded Known Deviations (which already tracked and resolved a WF-001/WF-002/WF-003 set
distinct from, but same-named as, the entries in `05_agent_90_inconsistencies_and_known_issues.md`).
ADR-001's own Known Deviations WF-001 described a citation-format issue between two
line-numbered ADR-001 references and was resolved by a docstring correction (confirmed
current INV-01/INV-05 text is already distinct); it did not describe the same invariant
content that `05_agent_90`'s WF-001 attributes to INV-01/INV-05.

## Problem
(Evidence: Needs confirmation) `05_agent_90_inconsistencies_and_known_issues.md`'s WF-001
entry's "Summary" and "Current Description" fields quote INV-01/INV-05 wording that does not
appear anywhere in the current `docs/adr/ADR-001-workflow-engine-mandatory.md`. It is unclear
whether this entry describes an earlier draft of ADR-001 that was later rewritten, a
transcription error, or a conflation with a different document.

## Reason for Change
A canonical Known Issues document (per this repository's Document Classification, Known
Issues documents are meant to track confirmed discrepancies against current documents) that
quotes invariant text not present in the ADR it cites undermines trust in the rest of its
entries and could send an investigator looking for a mismatch that does not exist as described.

## Implementation Intent
Re-investigate WF-001 (and, while inspecting the same file, WF-002/WF-003, whose status as
"open" was also found to be stale during the 2026-08-31 ADR-001 update — see Dependencies)
against the current `docs/adr/ADR-001-workflow-engine-mandatory.md` text. Determine whether
WF-001 describes a real, still-open issue (in which case correct its quoted invariant text to
match current ADR-001 wording) or is itself obsolete/superseded (in which case remove it per
this repository's Current-Specification-Only Policy for resolved entries).

## Target Files or Areas
- `docs/05_agent_90_inconsistencies_and_known_issues.md` (WF-001, and re-verify WF-002/WF-003)
- `docs/adr/ADR-001-workflow-engine-mandatory.md` — read-only reference for current INV text

## Required Changes
- Compare `05_agent_90`'s WF-001/WF-002/WF-003 entries against the current ADR-001 text and the
  test evidence already gathered during the 2026-08-31 ADR-001 update (see Dependencies).
- Correct or remove each entry based on that comparison, following this document's own
  5-tier classification scheme (Design Decision / Implementation Bug / Documentation Gap /
  Needs Confirmation / Operational Observation).
- If WF-001's original intent cannot be reconstructed, mark it Needs Confirmation rather than
  guessing at a corrected invariant quote.

## Constraints
- Do not modify `docs/adr/ADR-001-workflow-engine-mandatory.md` in this issue — it was already
  updated on 2026-08-31 and its own Known Deviations are already current.
- Do not remove WF-002/WF-003 without re-verifying them against current code/tests, even though
  the 2026-08-31 ADR-001 update found evidence suggesting both are stale (see Dependencies) —
  this document's own "Key Constraints" require verifying an inconsistency still exists before
  deleting an entry.

## Acceptance Criteria
- WF-001's quoted invariant text matches current `docs/adr/ADR-001-workflow-engine-mandatory.md`
  wording, or the entry is removed with justification.
- WF-002 and WF-003 are re-verified against current code/tests and their Status fields updated
  to match (both were found likely-resolved during the 2026-08-31 ADR-001 update).
- This document's "Operational Notes" claim ("There are currently no open items") is made
  consistent with whatever entries remain after this correction.

## Testing Expectations
Documentation-only change; not required beyond re-reading the cited source/tests.

## Documentation Impact
This issue is itself the documentation-accuracy fix for `05_agent_90_inconsistencies_and_known_issues.md`.

## Out of Scope
- Any entry in this document unrelated to WF-001/WF-002/WF-003.
- Re-editing ADR-001 itself.

## Dependencies
Follows the 2026-08-31 ADR-001 update, during which:
- INV-01/INV-05 in the current ADR-001 were confirmed already textually distinct (WF-001's
  premise, as stated in ADR-001's own now-resolved Known Deviation, no longer holds).
- `tests/agent/workflow/test_workflow_engine.py::test_execute_success_verify_failure_marks_task_failed`
  was found to directly verify INV-03 (execution success vs. verification success), suggesting
  `05_agent_90`'s WF-002 ("no test verifies... INV-03") is stale.
- ADR-001 Decision Details #5 (the single-stage Q&A workflow statement) was replaced per an
  explicit approved decision, suggesting `05_agent_90`'s WF-003 ("feature gap identified") is
  now moot rather than an open gap.

## Unresolved Questions
Whether `05_agent_90`'s WF-001 ever matched an actual past version of ADR-001, or was
miswritten from the start — needs investigation, not assumption.

## AI Implementation Instruction
Read the current `docs/adr/ADR-001-workflow-engine-mandatory.md` in full before correcting any
entry. Do not invent a plausible-sounding invariant quote for WF-001 — if the original intent
cannot be reconstructed from history or context, mark it Needs Confirmation instead of guessing.
