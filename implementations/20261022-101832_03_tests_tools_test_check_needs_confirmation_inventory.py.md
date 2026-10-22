## Goal
Add tests for the accepted `None` value and the retained warning, empty, and resolved-entry behavior, and extend the parser test for `**Blocking:** None` (REQ-005).

## Scope
- `TestCheckBlockingReference` and `TestParseInventoryMarkers` only.

## Assumptions
- `NcEntry(nc_id, source, status, blocking=...)` is the constructor used by the existing tests, and the parser test feeds bare `**Field:** value` lines through `_parse_inventory_entries(SimpleNamespace(lines=...))` (verified).
- The checker change of the sibling procedure accepts exactly `None`.

## Design decisions
- Add one test per behavior; keep the existing four tests unchanged.

## Alternatives considered
N/A: additive tests only.

## Implementation
### Target file
`tests/tools/test_check_needs_confirmation_inventory.py`

### Procedure
1. In `TestCheckBlockingReference` add: `None` yields no issue; lower-case `none` still yields one WARNING (exact spelling only); an unknown NC id still yields one WARNING (already covered, keep).
2. In `TestParseInventoryMarkers` add a case where `**Blocking:** None` is parsed to the string `None`.

### Method
- Follow the existing style (`NcEntry` objects, `check_blocking_reference([...])`, assertions on `issues`).

### Details
- Do not weaken or remove existing assertions.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit with the tool change.

## Validation plan
- `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py -q`; `uv run ruff format`/`check` on the file.

## Completion criteria
- The new tests pass and fail if the `None` condition is removed; the existing tests pass unchanged.

## Out of Scope
- Other test classes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `None`, exact-spelling, and parser tests | Pending | — | — | |
| 2 | Run the file's tests | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (tests for the `None` value and retained behavior)
- **Source issue**: `issues/20261021-104533_blockingdef_define-the-blocking-field-in-the-needs-confirmation-inventory.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094758_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101832
- **Related target files**: tests/tools/test_check_needs_confirmation_inventory.py
