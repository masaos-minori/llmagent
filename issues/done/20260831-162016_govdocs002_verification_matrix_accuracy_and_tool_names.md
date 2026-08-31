# Governance Verification Matrix overstates tool coverage; documented tool filenames don't match actual files

## Priority
Medium

## Summary
`docs/00_governance_04_documentation-checks.md`'s Governance Verification Matrix marks
several rules as `Existing` (auto-enforced by `tools/check_docs_quality.py`) with no
corresponding check function found in that script. The same document also names four tools
using filenames that don't match the actual files under `tools/`.

## Background
Discovered while validating a governance-policy change (Current-Specification-Only Policy)
that touched this document. `tools/check_docs_quality.py`'s actual registered core checks are:
`broken_headings`, a malformed-table check, `unclosed_inline_code`, `json_not_wrapped`,
`stale_patterns`, `resolved_in_active`, `duplicate_heading_numbers`, and
`migration_notes_in_active` (Evidence: Explicit in code — `@register_core_check` call sites in
`tools/check_docs_quality.py`).

## Problem
- The Governance Verification Matrix marks GV-001 (Required Front Matter), GV-002 (Valid
  Document Status), GV-003 (Unique ADR ID), GV-005 (Existence of Related Documents), GV-006
  (Self-reference prohibition), GV-007 (Duplicate Related Link prohibition), GV-008 (Known
  Issue required fields), GV-009 (Needs Confirmation owner and deadline), and GV-013
  (References to non-existent canonical documents) as `Auto` / `Existing`, attributing them to
  `check_doc_quality.py`. None of these have an obviously corresponding registered check in
  the actual `check_docs_quality.py` implementation (Evidence: Needs confirmation — the
  matching was done by comparing rule descriptions against registered check names/descriptions;
  a check could exist under a name that doesn't obviously map to its GV description).
- This directly conflicts with the same document's own GV-016 ("No unimplemented auto-checks
  documented as implemented") and with `skills/DESIGN.md`'s "Do not claim that a check is
  implemented if the corresponding tool does not implement it."
- Four tool names in this document do not match actual files under `tools/`:
  `check_doc_quality.py` (actual: `check_docs_quality.py`), `check_no_compat.py` (actual:
  `check_compat_shims.py`), `check_all_docstrings.py` (actual: `check_docstrings.py`), and
  `validate_docs_structure.py` (actual: `check_docs_structure.py`).

## Reason for Change
A verification matrix that claims automated coverage which doesn't exist gives a false sense
that those rules are being enforced on every PR, when in fact they may only ever be caught by
manual review (if at all). Incorrect tool filenames also cause anyone following the
document's own `Usage` examples to run a nonexistent command.

## Implementation Intent
For each of GV-001, 002, 003, 005, 006, 007, 008, 009, and 013: re-verify against the actual
current implementation of `check_docs_quality.py` (and any other relevant tool) whether a
corresponding check truly exists. Where it does not, change that row's Method/Tool/Status to
accurately reflect reality (e.g., `Manual` / `Human review` / `Missing`, matching the pattern
already used for GV-011, 012, 014, 015, 016, 018, 019) and add it to Follow-up Work Needed.
Where a check does exist under a different name or in a different tool, correct the Tool/Review
column instead. Separately, correct the four mismatched tool filenames throughout the document
to their actual names.

## Target Files or Areas
- `docs/00_governance_04_documentation-checks.md` — primary target
- `tools/check_docs_quality.py`, `tools/check_docs_consistency.py`, `tools/check_needs_confirmation_inventory.py`, `tools/check_compat_shims.py`, `tools/check_suppression_justification.py`, `tools/check_docstrings.py`, `tools/check_tool_descriptions_sync.py`, `tools/check_docs_structure.py` — read-only reference to verify actual implemented checks

## Required Changes
- Re-verify GV-001, 002, 003, 005, 006, 007, 008, 009, and 013 against actual tool
  implementations; correct their Method/Tool/Status/Follow-up columns to match reality.
- Replace `check_doc_quality.py` with `check_docs_quality.py`, `check_no_compat.py` with
  `check_compat_shims.py`, `check_all_docstrings.py` with `check_docstrings.py`, and
  `validate_docs_structure.py` with `check_docs_structure.py` everywhere they appear in this
  document (Automated Checks section headers, Usage examples, and the Governance Verification
  Matrix's Tool/Review column).
- Update the Follow-up Work Needed list to include any rule newly reclassified as `Missing`.

## Constraints
- Do not modify any tool script — this issue is a documentation-accuracy fix only.
- Do not remove a GV rule merely because its current enforcement is manual — only correct its
  documented enforcement method.
- Preserve existing GV rule IDs; do not renumber (per this repository's established practice
  of leaving gaps rather than renumbering, already applied when GV-004/010/017/020 were
  removed in the prior governance-policy task).

## Acceptance Criteria
- Every GV rule marked `Existing`/`Auto` in the matrix has a verifiable, named check function
  in the tool it cites.
- No tool filename referenced in this document differs from the actual filename under
  `tools/`.
- Any GV rule reclassified from `Existing` to `Missing` appears in Follow-up Work Needed with
  a corresponding action item, consistent with the existing entries for GV-011/012/014/015/016/018/019.

## Testing Expectations
Documentation-only change; not required. Manually re-run each corrected `Usage` command
example in the document to confirm it executes (not necessarily that it passes) against the
actual `tools/` scripts.

## Documentation Impact
This issue is itself the documentation-accuracy fix for `docs/00_governance_04_documentation-checks.md`.

## Out of Scope
- Implementing any new automated check to cover a rule found to be `Missing`.
- Modifying any script under `tools/`.
- Re-litigating which rules should exist at all (only their documented enforcement status is
  in scope).

## Dependencies
N/A: none

## Unresolved Questions
- Whether GV-001, 002, 003, 005, 006, 007, 008, 009, and 013 truly have no corresponding
  implementation, or whether the mapping between GV rule descriptions and registered check
  names/descriptions in `check_docs_quality.py` was simply not obvious from the check names
  alone — needs a careful per-rule code read before reclassifying anything.

## AI Implementation Instruction
- For each GV rule in question, read the actual tool source and trace through what it checks
  before deciding whether the rule is implemented, not implemented, or implemented elsewhere.
- Do not assume a check is missing just because its name doesn't obviously match — verify by
  reading the function body.
- Do not implement a missing check as part of this issue — only correct the documentation to
  state its actual status.
- Apply the same Method/Tool/Status/Follow-up pattern already used for the existing `Missing`
  rows (GV-011 etc.) for consistency.
