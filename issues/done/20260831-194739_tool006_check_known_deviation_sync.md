# Add `tools/check_known_deviation_sync.py` to detect Status mismatches between an ADR's Known Deviations and the canonical Known Issues document

## Priority
Medium

## Summary
An ADR's own Known Deviations section and the area's canonical Known Issues document
(`docs/{area}_90_inconsistencies_and_known_issues.md`) both describe the same underlying gaps by
Known Issue ID, but nothing currently checks that their Status fields agree. This session found
multiple cases where they had drifted apart (e.g., an ADR's Known Deviations already removed an
entry as resolved while the canonical Known Issues document still listed the same ID as `open`,
and vice versa). Add a script that cross-references the two and reports disagreements.

## Background
During this session's ADR-008/ADR-012 work, direct code and test inspection found: MCP-005
(audit repository-identity fix) marked `open`/"pending confirmation" in
`docs/04_mcp_90_inconsistencies_and_known_issues.md` while already resolved in code and covered
by a passing test; MCP-003's Resolution Notes already pointed to GIT-001/GIT-002 as its actual
resolution, but the parent entry's own Status field was never updated to `resolved`; MCP-004's
Resolution Notes listed a "config floor check" as still outstanding when it was already
implemented. Each of these was found only by an agent happening to cross-check code, tests, and
two separate documents by hand.

## Problem
(Evidence: Explicit in docs — this session's own findings, recorded in
`issues/20260831-192510_...` and prior ADR-008/ADR-012 evaluation work) No existing tool in
`tools/` cross-references an ADR's Known Deviations section against the corresponding canonical
Known Issues document's Status field for the same Known Issue ID. `check_docs_consistency.py`
checks documentation against source code per domain, and
`check_needs_confirmation_inventory.py` checks Needs-Confirmation markers against their central
inventory, but neither covers ADR-Known-Issues Status agreement.

## Reason for Change
Without this check, an ADR can silently drift out of sync with the canonical Known Issues record
in either direction — describing something as an open gap that code has already fixed, or vice
versa — and the only way to catch it currently is an agent noticing during unrelated work, as
happened repeatedly this session.

## Implementation Intent
Add `tools/check_known_deviation_sync.py` that: (1) scans every `docs/adr/*.md` file's Known
Deviations section for Known Issue IDs it references (both entries kept as active deviations and,
where determinable, IDs mentioned in Related Documents → Known Issues); (2) scans each area's
canonical `docs/{area}_90_inconsistencies_and_known_issues.md` (and
`docs/adr-index.md`'s cross-ADR Known Issues, if applicable) for the same IDs' current Status
field; (3) reports any ID present in both places with disagreeing Status (e.g., an ADR treats it
as resolved/removed while the canonical document still shows `open`, or the reverse); (4) reports
any Known Issue ID an ADR's Known Deviations references that no longer exists in the canonical
document at all (a dangling reference, distinct from a Status mismatch).

## Target Files or Areas
- `tools/check_known_deviation_sync.py` — new file
- `docs/adr/*.md`, `docs/*_90_inconsistencies_and_known_issues.md`, `docs/adr-index.md` —
  read-only input
- `tools/TOOL_DESCRIPTIONS.md` — must document the new tool

## Required Changes
- Implement the ID extraction and cross-reference described above for at least the `04_mcp_90`,
  `05_agent_90`, and `90_shared_90` canonical documents plus every current `docs/adr/*.md` file.
- Reuse `_docs_consistency_lib.py`'s existing DocFile/Issue discovery helpers where applicable,
  consistent with how `check_docs_consistency.py` and
  `check_needs_confirmation_inventory.py` already share that library, rather than re-implementing
  Markdown/front-matter parsing from scratch.
- Provide a `--format json` output mode alongside a human-readable summary.

## Constraints
- This tool only reports; it must not edit any ADR or Known Issues document.
- Do not assume every Known Issue ID mentioned near an ADR's prose is a Known Deviations entry —
  scope extraction to the actual Known Deviations section (and the Related Documents → Known
  Issues subsection) to avoid false positives from IDs mentioned only in passing narrative text.
- Status comparison should tolerate the known variety of Status vocabularies already in use
  across canonical documents (e.g., `open`/`resolved`/`partially resolved` in
  `90_shared_90_inconsistencies_and_known_issues.md` vs. the 5-tier scheme documented as an
  intentional exception in `05_agent_90_inconsistencies_and_known_issues.md`) rather than
  assuming one fixed vocabulary.

## Acceptance Criteria
- Running the tool against the current repository reports the specific Status mismatches already
  known from this session's manual findings (or confirms they have since been corrected), as a
  validation that the tool's logic is sound.
- `tools/TOOL_DESCRIPTIONS.md` documents the new tool; `check_tool_descriptions_sync.py` passes.

## Testing Expectations
Add `tests/tools/test_check_known_deviation_sync.py` using fixture ADR and Known Issues documents
(not the live `docs/` tree) covering: an ID with matching Status (no report), an ID with
disagreeing Status (reported), and an ID referenced by an ADR but absent from the canonical
document (reported as dangling). Apply the standard validation sequence in `rules/toolchain.md`.

## Documentation Impact
Add the new tool to `tools/TOOL_DESCRIPTIONS.md`, in the domain-consistency-checker table
alongside `check_docs_consistency.py` and `check_needs_confirmation_inventory.py`.

## Out of Scope
- Automatically resolving any detected mismatch — a human/agent must read both documents and
  code evidence to decide the correct current Status, as this session did manually.
- Checking Known Issue content accuracy beyond the Status field (e.g., whether the Summary text
  itself is stale) — that remains a manual review task.
- The other four tools proposed alongside this one, tracked as separate issues.

## Dependencies
N/A: none — independently buildable, though it shares parsing infrastructure with the existing
`_docs_consistency_lib.py`.

## Unresolved Questions
Whether the 5-tier classification scheme documents (like `05_agent_90`) should be compared using
a mapped equivalence table against the more common `open`/`resolved`/`partially resolved`
vocabulary, or treated as a separate comparison mode entirely — needs an owner decision on how
strictly to unify the two schemes for comparison purposes, given
`05_agent_90_inconsistencies_and_known_issues.md`'s own stated rationale for keeping its scheme
distinct.

## AI Implementation Instruction
Read `_docs_consistency_lib.py` in full before implementing new parsing logic, to reuse its
existing DocFile/Issue discovery rather than duplicating it. Read at least one full canonical
Known Issues document per area (`04_mcp_90`, `05_agent_90`, `90_shared_90`) to confirm the actual
Status vocabulary and field layout in current use before hardcoding a comparison rule.
