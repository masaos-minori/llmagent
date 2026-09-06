## Goal
Confirm `gitpipeline`'s Plan's existing Known Issue entries (MCP-001, MCP-002) remain
the complete, correct record of this ADR-012 area's deviations, and register a new
entry only if Phase 1's dead-method removal (seq 01/02) surfaces a genuinely distinct,
still-unresolved gap (REQ-007, UNK-01) — do not file a duplicate of MCP-001/MCP-002.

## Scope
- In scope: read `docs/00_governance_03_issue-and-uncertainty-management.md`'s
  MCP-001/MCP-002 entries (currently lines 709-745) after Phase 1 has landed; if both
  remain an accurate, complete description of this area's deviations, no edit is
  required to this file — record that confirmation in this document's Execution
  Status Notes instead of a code diff. If Phase 1 surfaces a new, distinct gap, add
  one new `MCP-00N` entry (next available number) following the existing entries'
  format.
- Out of scope: MCP-001/MCP-002's own content — already correct and resolved per this
  cycle's read; do not re-edit them without new evidence.

## Assumptions
- This document's investigation runs after Phase 1 (seq 01/02) lands, per the Plan's
  own phase ordering — "no new gap" cannot be confirmed before the dead-method removal
  and its regression run complete.
- UNK-01 (this Plan's own Unknowns table) resolves based on this row's finding: if no
  new gap is found, UNK-01 closes with "no new Known Issue required"; if one is found,
  UNK-01 closes by pointing to the new `MCP-00N` entry.

## Design decisions
- Prefer "no edit" over adding a redundant entry when MCP-001/MCP-002 already cover the
  finding — the Plan's own Risk section flags that filing a duplicate entry would
  itself demonstrate the documentation-drift problem this issue exists to fix.

## Alternatives considered
- Always add a new entry regardless of overlap, for traceability to this specific
  Plan: rejected — `templates`/governance convention treats one Known Issue per
  distinct deviation, not one per Plan that happens to touch the area; REQ-007
  explicitly requires coordinating with, not duplicating, `gitpipeline`'s entry.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. After Phase 1 (seq 01/02) lands and its validation passes, re-read MCP-001 and
   MCP-002 (current lines 709-745) and re-run the invariant-mapping exercise from row
   03 (ADR-012) — confirm no invariant now lacks implementation/test evidence.
2. If confirmed complete: make no edit to this file; record in this document's
   Execution Status that MCP-001/MCP-002 were reconfirmed sufficient, with the date
   and the specific evidence checked.
3. If a genuinely distinct gap is found: add one new entry `#### MCP-00N` (N = next
   integer after the highest existing `MCP-` entry at edit time — re-count, do not
   assume `003` from this document's authoring-time snapshot) immediately after
   MCP-002 (currently ending line 745), following the exact field structure MCP-001/
   MCP-002 use (`ID`, `Title`, `Status`, `Severity`, `Area`, `Type`, `Source`, `Owner`,
   `First Found`, `Target`, `Related`, `Summary`, `Current Description`, `Observed
   Implementation`, `Impact`, `Recommended Action`), and update the "No other active
   Known Issues beyond..." summary line (currently line 747) to include the new ID.

### Method
Confirmed this cycle (2026-09-06) via direct read: MCP-001 (`Status: resolved`,
lines 709-726) covers `verify_postcondition()`'s placeholder; MCP-002
(`Status: resolved`, lines 728-745) covers `PipelineResult.post_state`. Both already
registered by `gitpipeline`'s Plan (per this Plan's own Background/Reference Files);
neither overlaps with this Plan's Phase 1 scope (dead duplicate-method removal), which
targets a different code region of the same file.

### Details
Whether an edit lands at all is conditional on Phase 1's outcome (Design decisions
above) — this document intentionally does not pre-write new-entry content, since doing
so before Phase 1 completes would risk exactly the kind of speculative/unconfirmed
documentation this Plan exists to prevent.

## Compatibility considerations
N/A: documentation-only; no code or API surface affected either way.

## Security considerations
N/A.

## Rollback considerations
If a new entry is added and later found to be a duplicate or inaccurate, revert via
`git checkout` on this file alone — no other file depends on this file's exact content
byte-for-byte (only on this Plan's ADR-012 row, seq 03, referencing it by name).

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md`
- `uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md`
- If a new entry is added: `uv run python tools/check_needs_confirmation_inventory.py`
  only if the new entry also introduces a "Needs confirmation" marker (not expected —
  Known Issue entries and NC markers are managed separately); otherwise this check
  does not apply.

## Completion criteria
- Either: no edit made, with the reconfirmation recorded in Execution Status Notes; or
  a new `MCP-00N` entry exists with all required fields populated and the summary line
  updated.
- `check_docs_quality.py`/`check_docs_structure.py` report no new finding (only
  applicable if an edit was made).

## Out of scope
- ADR-012 itself — tracked in seq 03.
- Any Known Issue entry unrelated to this Plan's git-mcp cleanup scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-06 | 2026-09-06 | MCP-001/MCP-002 reconfirmed sufficient; no edit required |
| 2 | Add or update tests per Validation plan | N/A | — | — | No code change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No edit made |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007 (register/confirm Known Issue), UNK-01 (resolution path)
- **Source issue**: issues/20260902-144914_gitcleanup_remove_placeholders_and_align_docs_with_verified_implementation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192746_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-135247
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
