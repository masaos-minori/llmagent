## Goal
Add "Part 3: Canonical Source Conflict" and "Part 4: Configuration Drift" sections to
`docs/00_governance_03_issue-and-uncertainty-management.md`, following the existing
Known Issues/Needs Confirmation pattern. Document the 5 resolution rules and the
evidence-required/documentation-only-cannot-close rules per REQ-002, REQ-003, REQ-005,
REQ-006, REQ-007.

## Scope
- **In-Scope**: adding Part 3 (Canonical Source Conflict Entry Template with 12 fields,
  Status Values, Lifecycle); adding Part 4 (Configuration Drift minimal template);
  documenting the 5 resolution rules and the evidence-required/documentation-only-cannot-
  close rules.
- **Out-of-Scope**: every other change to this file; modifying existing Parts 1/2.

## Assumptions
- M-01-01 through M-01-06 are all implemented before this procedure executes (Phase 0
  prerequisite check).
- The existing Part 1 (Known Issues, line 17) and Part 2 (Needs Confirmation Inventory,
  line 751) patterns define Severity Values (`High`/`Medium`/`Low`), Owner Values
  (reused from Known Issues), and Lifecycle wording ("An item is removed from this active
  inventory once it is resolved or no longer applies to the current system").
- Part 3 goes between Part 2 and "## Keywords"; Part 4 follows immediately after Part 3.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Part 3 uses the same Severity/Owner Values as Known Issues rather than inventing new
  vocabularies — consistency with existing lifecycle reduces cognitive load.
- Part 4 deliberately smaller than Part 3 since Configuration Drift concerns exactly one
  dimension (deployed-vs-approved value), not the fuller canonical-source-conflict shape.
- Both Parts use the `Related` field (matching Known Issues' existing `Related` field)
  for cross-referencing any existing entry for the same underlying discrepancy — this
  implements REQ-002's duplicate-active-record prevention constraint.
- Part 3 status values: `open`/`investigating`/`resolved` (where `resolved` means exactly
  one normative source remains and the entry is then removed per Current-Specification-Only
  Policy, matching Known Issues' own Lifecycle wording).

## Alternatives considered
N/A: straightforward addition of tracking sections following existing pattern; no
alternative approach applies.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Insert Part 3 after Part 2 (before "## Keywords") with:
   - Heading: "## Part 3: Canonical Source Conflict"
   - Entry Template with 12 required fields: Conflict ID (`CSC-{NNN}`), Decision target,
     Claim type, Canonical source, Conflicting source or evidence, Conflict category,
     Impact, Severity (`High`/`Medium`/`Low`), Blocking status (`Blocking`/`Non-blocking`),
     Required action, Owner, Validation evidence
   - Status Values: `open`/`investigating`/`resolved`
   - Lifecycle: "A `resolved` entry is removed from this active inventory once exactly
     one normative source remains and validation evidence confirms the conflict is closed."
   - Resolution rule: "Canonical Source Conflict resolved only when exactly one normative
     source remains registered."
   - Evidence-required rule: "Evidence is required before any discrepancy is reclassified
     or removed; a documentation-only edit cannot close a design-vs-code conflict unless
     required implementation evidence exists."

2. Insert Part 4 after Part 3 with:
   - Heading: "## Part 4: Configuration Drift"
   - Minimal Entry Template with 6 fields: Drift ID (`CD-{NNN}`), Decision target,
     Deployed value description, Approved operational value description, Severity, Status
   - Status Values: `open`/`investigating`/`resolved`
   - Lifecycle: "A `resolved` entry is removed from this active inventory once deployed
     and approved values agree, or the approved value is formally changed."
   - Resolution rule: "Configuration Drift resolved only when deployed and approved values
     agree, or approved value is formally changed."
   - Evidence-required rule: "Evidence is required before any discrepancy is reclassified
     or removed."

3. Add the 5 resolution rules alongside Part 3/Part 4:
   - Known Issue resolved only when implementation and design agree, or design is formally changed
   - Configuration Drift resolved only when deployed and approved values agree, or approved value is formally changed
   - Needs Confirmation removed only after evidence establishes intent and the canonical source is updated
   - Canonical Source Conflict resolved only when exactly one normative source remains registered
   - Documentation correction complete only when validation shows no stale statement remains

4. Add the documentation-only-cannot-close rule:
   - "A documentation-only edit cannot close a design-vs-code conflict unless required
     implementation evidence exists."

5. Add the Current-Specification-Only policy reference:
   - "Resolved-item handling for Canonical Source Conflict and Configuration Drift follows
     the existing Current-Specification-Only Policy: resolved entries are removed from the
     active inventory, not retained with a closed-out status."

### Method
Edit via exact string insertion using Edit tool, inserting between Part 2 and "## Keywords".

### Details
- The insertion point is after the last Part 2 entry and before "## Keywords".
- Part 3 Entry Template format mirrors Part 1's Known Issues template structure.
- Part 4 Entry Template format mirrors Part 2's Needs Confirmation template structure but
  with fewer fields (deliberately lighter since Configuration Drift concerns exactly one
  dimension).

## Compatibility considerations
N/A: governance-class document; consumed by `tools/check_needs_confirmation_inventory.py`.

## Security considerations
N/A.

## Rollback considerations
- Revert the edits to restore the original document without Part 3/Part 4.

## Validation plan
- `uv run python tools/check_needs_confirmation_inventory.py` passes — confirms the new
  Part 3/Part 4 sections do not break the existing NC-inventory-sync check.
- `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` passes.
- Manual diff review confirming changes scoped to canonical-source declarations only (AC9).
- Confirm Part 3 has exactly 12 fields in its Entry Template.
- Confirm Part 4 has exactly 6 fields in its Entry Template.
- Confirm the 5 resolution rules are present.
- Confirm the evidence-required and documentation-only-cannot-close rules are present.

## Completion criteria
- Part 3 Entry Template covers the 12 required fields (AC10).
- Part 4 Entry Template covers the 6 required fields (AC10).
- Duplicate active records are prohibited or detected (AC6).
- Resolution criteria require evidence for every one of the 5 categories (AC7).
- Documentation-only changes cannot improperly close implementation conflicts (AC8).
- Resolved-item handling complies with the Current-Specification-Only policy (AC9).
- Templates and Merge Conditions validator text are updated (AC10).
- Documentation structural/quality validation passes (AC12).

## Out of scope
- Every other change to this file.
- Modifying existing Parts 1/2.
- Updating `docs/00_governance_01_documentation-policy.md` (REQ-001, REQ-004, separate procedure).
- Extending `tools/check_canonical_source_conflicts.py` (REQ-008, separate procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-002` (add Part 3: Canonical Source Conflict section with Entry Template covering 12 required fields), `REQ-003` (define Configuration Drift record location as Part 4), `REQ-005` (document the 5 resolution rules), `REQ-006` (state evidence-required and documentation-only-cannot-close rules), `REQ-007` (Current-Specification-Only policy for resolved items)
- **Source issue**: issues/20260903-103030_m0107_integrate-canonical-source-conflicts-with-issue-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-185612_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185612
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
