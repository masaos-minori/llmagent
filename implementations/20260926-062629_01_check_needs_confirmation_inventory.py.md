## Goal

Extend `check_needs_confirmation_inventory.py` to validate that active NC items have both an assigned owner and a resolution target/deadline set, enforcing GV-009 from the Governance Verification Matrix.

## Scope

- Extend `_parse_inventory_entries()` to capture `Assigned To` and `Resolution Target` fields
- Add `check_missing_nc_fields()` function to validate required fields for active NC items
- Wire the new validation into `main()`
- Add unit tests for the new validation logic

## Assumptions

- `Unassigned` is considered a violation of the "Owner review" requirement stated in the Required Action field
- The error message format follows the existing pattern: `{nc_id}: missing required field '{field_name}'`
- Active NC items are those with `Status: open` (not `resolved`, `fixed`, or removed)
- The NC inventory uses the same bullet-point format with `**Field Name**: value` structure throughout

## Design decisions

- Extend the existing `_parse_inventory_entries()` function rather than creating a separate parser — keeps NC-related checks in one place
- Use the existing `Issue` class from `_docs_consistency_lib` for reporting findings — consistent with existing code style
- Treat `Unassigned` as equivalent to missing owner — aligns with the governance policy's intent that every item needs an owner

## Alternatives considered

- Creating a separate script for NC field validation: rejected because the plan explicitly states extending the existing script keeps NC-related checks in one place
- Making the check opt-in via CLI flag initially: noted as a risk in the plan but deferred — the check can be made opt-in later if widespread failures occur
- Using severity level different from `Warning`: rejected because GV-009 specifies Warning-level

## Implementation

### Target file

`tools/check_needs_confirmation_inventory.py`

### Procedure

1. Extend `_parse_inventory_entries()` to capture `Assigned To` and `Resolution Target` fields alongside existing `source_file` and `status`.
2. Add `check_missing_nc_fields()` function to validate required fields for active NC items.
3. Wire `check_missing_nc_fields()` call into `main()`.

### Method

Use Edit tool to modify existing functions and add new ones.

### Details

**Phase 1: Extend `_parse_inventory_entries()` (REQ-001)**

Modify the `NcEntry` class and `_parse_inventory_entries()` function:

1. Add `assigned_to` and `resolution_target` attributes to the `NcEntry` class (around line 103).
2. Add regex patterns for the new fields near line 72:
   ```python
   _ASSIGNED_TO_RE = re.compile(r"\*\*Assigned To\*\*:\s*(\S+)")
   _RESOLUTION_TARGET_RE = re.compile(r"\*\*Resolution Target\*\*:\s*(.+)$")
   ```
3. In `_parse_inventory_entries()`, update the `flush()` function to include the new fields, and add parsing logic for `assigned_to` and `resolution_target` similar to how `source_file` and `status` are parsed (around line 138-143).

**Phase 2: Add `check_missing_nc_fields()` function (REQ-002, REQ-003)**

Add a new function after `check_declared_field_count()` (after line 230):

```python
def check_missing_nc_fields(entries: list[NcEntry]) -> list[Issue]:
    """Flag active NC items missing required 'Assigned To' or 'Resolution Target' fields."""
    issues: list[Issue] = []
    for entry in entries:
        if entry.status != "open":
            continue
        if not entry.assigned_to or entry.assigned_to == "Unassigned":
            issues.append(
                Issue(
                    file=INVENTORY_DOC_NAME,
                    line_no=0,
                    severity="WARNING",
                    message=(
                        f"{entry.nc_id}: missing required field 'Assigned To'"
                    ),
                )
            )
        if not entry.resolution_target:
            issues.append(
                Issue(
                    file=INVENTORY_DOC_NAME,
                    line_no=0,
                    severity="WARNING",
                    message=(
                        f"{entry.nc_id}: missing required field 'Resolution Target'"
                    ),
                )
            )
    return issues
```

**Phase 3: Wire into `main()` (REQ-007)**

In `main()`, after the existing check calls (around line 265), add:

```python
all_issues += check_missing_nc_fields(entries)
```

## Compatibility considerations

No compatibility impact. This change only adds new validation logic to an existing script. The existing checks remain unchanged. The new warnings will appear alongside existing warnings when the script runs.

## Security considerations

N/A: No security-relevant changes.

## Rollback considerations

Revert the edits to `_parse_inventory_entries()`, remove `check_missing_nc_fields()`, and remove the call in `main()`. No data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_needs_confirmation_inventory.py | Unit tests for NC field validation | `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py` | All new and existing tests pass |

## Completion criteria

- `_parse_inventory_entries()` captures `Assigned To` and `Resolution Target` fields for each NC entry
- `check_missing_nc_fields()` correctly flags active NC items missing either required field
- Items with `Unassigned` as owner are flagged as violations
- Resolved/removed NC items are excluded from validation
- New unit tests cover complete entries, missing fields, Unassigned owner, and resolved item exclusion
- Existing tests continue to pass

## Out of scope

- Modifying any files outside `Implementation Target Files` (additional target file discovery must be reported separately)
- Auto-assigning owners or setting deadlines for incomplete NC entries
- Changing the NC inventory format beyond what the governance policy specifies
- Validating Known Issue entries (Part 1) — only Part 2 Needs Confirmation items

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Extend `_parse_inventory_entries()` for field capture | Pending | — | — | |
| 2 | Phase 2a: Add `check_missing_nc_fields()` validation function | Pending | — | — | |
| 3 | Phase 2b: Wire `check_missing_nc_fields()` into `main()` | Pending | — | — | |
| 4 | Add or update tests per Validation plan | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 through REQ-006 — Validate NC inventory field completeness for active items
- **Source issue**: issues/20260925-220411_gv009_needs_confirmation_owner_and_deadline_validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-053537_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260926-062629
- **Related target files**: tools/check_needs_confirmation_inventory.py
