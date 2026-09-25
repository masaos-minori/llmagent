# [Governance] Implement Needs Confirmation owner and deadline validation

## Priority
High

## Summary
Add automated validation that all active Needs Confirmation items in the inventory have both an assigned owner and a resolution target/deadline set, enforcing GV-009 from the Governance Verification Matrix.

## Background
GV-009 requires that every active Needs Confirmation item has an owner and a deadline. The current `check_needs_confirmation_inventory.py` verifies that NC mentions in docs are registered in the centralized inventory and that resolved items don't leave markers, but it does not validate that individual NC entries have their required fields populated. Looking at the actual inventory in `governance_03_issue-and-uncertainty-management.md`, several NC items have `Assigned To: Unassigned` and/or missing `Resolution Target` values, confirming the gap.

## Problem
NC items without owners may never be investigated, and items without deadlines may remain open indefinitely. This undermines the purpose of the Needs Confirmation inventory — tracking unverified claims so they become actionable. Without validation, incomplete NC entries accumulate silently.

Examining the current inventory reveals concrete examples:
- NC-021 through NC-039 have varying completeness: some have `Unassigned` as owner, some lack explicit Resolution Targets
- The inventory template specifies fifteen required fields including "Assigned To" and "Resolution Target", but no tool enforces this

## Reason for Change
The governance policy defines specific required fields for NC entries. Without validation, incomplete entries go undetected, reducing the effectiveness of the entire Needs Confirmation tracking system.

## Implementation Intent
Create or extend a validation script that parses the Needs Confirmation inventory section of `governance_03_issue-and-uncertainty-management.md` and validates each active NC item's required fields. Two approaches are viable:

1. **Extend existing `check_needs_confirmation_inventory.py`** (preferred): Add a new validation step that iterates over active NC items and checks for required fields. This keeps NC-related checks in one place.

2. **New dedicated script**: Create `check_nc_item_fields.py` following the pattern of other governance checkers.

Either way, the validation should:
- Parse the markdown-formatted NC inventory (items under "Part 2: Needs Confirmation Inventory")
- Identify active items (those not removed/resolved)
- Check each item for required fields: `Assigned To` (must not be empty/unassigned), `Resolution Target` (must be set)
- Report findings with severity based on the gate column (Warning per GV-009)

## Target Files or Areas
- `tools/check_needs_confirmation_inventory.py` (or new `tools/check_nc_item_fields.py`)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `.github/workflows/governance-docs-consistency.yml` (CI wiring)

## Required Changes
- Add validation logic to parse NC inventory entries from `governance_03_issue-and-uncertainty-management.md`
- For each active NC item, verify:
  - `Assigned To` field exists and is not empty / `Unassigned` (depending on policy interpretation)
  - `Resolution Target` field exists and is not empty
- Report findings with format: `{nc_id}: missing required field '{field_name}'`
- Integrate into CI pipeline as a Warning-level finding (per GV-009 gate column)
- Consider whether `Unassigned` is acceptable or constitutes a violation (policy says "Owner review" is required action, suggesting assignment is expected)

## Constraints
- Must parse the markdown bullet-point format used in the inventory (not YAML/front-matter)
- Must distinguish between active items and resolved/removed items
- Cannot change the required fields — they are defined by the governance policy
- Error messages must match the style of existing validation messages

## Acceptance Criteria
- Running the checker reports an error for any NC item missing `Assigned To` or `Resolution Target`
- NC items with both fields populated pass validation
- Resolved/removed NC items are excluded from validation
- The check is included in the CI pipeline alongside other Warning-level checks

## Testing Expectations
- Unit test for validation with complete NC entry (should pass)
- Unit test for validation with missing `Assigned To` field (should fail)
- Unit test for validation with missing `Resolution Target` field (should fail)
- Unit test for validation with `Unassigned` as owner (behavior depends on policy decision)
- Integration test confirming the check runs in CI flow

## Documentation Impact
Update `docs/00_governance/governance_04_documentation-checks.md` to update GV-009 status from "Missing" to "Existing" in the Governance Verification Matrix table. Also consider updating `governance_03_issue-and-uncertainty-management.md` to ensure all active NC items have these fields populated before the check is enabled.

## Out of Scope
- Adding new required fields beyond what the governance policy specifies
- Changing the NC inventory format (would require governance policy change first)
- Auto-assigning owners or setting deadlines
- Validating Known Issue entries (separate concern, covered by different rules)

## Dependencies
- Depends on understanding of existing `check_needs_confirmation_inventory.py` patterns (needs investigation)
- May depend on the decision about whether `Unassigned` is acceptable or constitutes a violation

## Unresolved Questions
- Is `Unassigned` considered a valid value for `Assigned To`, or does it constitute a missing owner? The policy states "Owner review" is required action, which suggests assignment is expected. This needs clarification from the governance team.
- Should the check also validate other required fields (Status, Priority, Evidence, etc.), or only Owner and Deadline as specified by GV-009?
- What is the exact list of required fields per the NC inventory template? The document mentions fifteen fields but the exact list needs confirmation.

## AI Implementation Instruction
First investigate `tools/check_needs_confirmation_inventory.py` to understand its existing parsing approach. Then either extend it or create a new script that validates NC inventory entries. Parse the markdown bullet-point format, identify active items, and check for required fields (`Assigned To` and `Resolution Target`). Report findings with clear error messages. Do not modify any existing document files.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-220411
- **Related target files**: tools/check_needs_confirmation_inventory.py, docs/00_governance/governance_03_issue-and-uncertainty-management.md
