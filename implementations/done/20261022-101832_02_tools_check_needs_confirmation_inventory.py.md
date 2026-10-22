## Goal
Make `check_blocking_reference` accept the explicit "blocks nothing" value `None` without a warning, keeping the warning for an unknown NC id and the acceptance of an empty value (REQ-004).

## Scope
- One extra condition and the docstring of `check_blocking_reference`; no change to the other checks, parsing, or exit-code contract.

## Assumptions
- Today the function skips an unset/empty `blocking`, and warns (WARNING, exit 0) for any non-empty value that is not a known NC id; so `None` would warn (verified in the function).
- The `Blocking` regex needs at least one character after the label, so an empty label parses as `None` (Python) and is skipped (verified).
- Warnings do not fail the run (exit-code contract of the tool), so the existing corpus cannot newly fail.

## Design decisions
- Accept only the exact spelling `None` (matching `Related NC: None`); other values stay subject to the known-NC-id check (Plan UNK-03).
- Docstring states the allowed values: a known NC id or `None`; empty means not yet assessed.

## Alternatives considered
- Case-insensitive acceptance: rejected, no convention beyond the exact `None` spelling.

## Implementation
### Target file
`tools/check_needs_confirmation_inventory.py`

### Procedure
1. In `check_blocking_reference`, after the empty-value skip and before the known-id comparison, skip a value whose stripped text equals `None`.
2. Update the docstring accordingly.

### Method
- Minimal edit; keep `known_ids`, the message text, and the `WARNING` severity.
- Follow `routing.md` "Adding a new tool": `uv run ruff format`/`check`, `uv run mypy tools/check_needs_confirmation_inventory.py`, `uv run bandit tools/check_needs_confirmation_inventory.py`, a smoke run on the live inventory, and `uv run python tools/check_tool_descriptions_sync.py`.

### Details
- `tools/TOOL_DESCRIPTIONS.md` rows do not mention `Blocking`, so no description change is needed.

## Compatibility considerations
Report-only checker; the only behavior change is one fewer warning for the value `None`.

## Security considerations
N/A: read-only checker.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py -q` (after the test procedure).
- Live: `uv run python tools/check_needs_confirmation_inventory.py` reports no issues once NC-041 holds `None`.

## Completion criteria
- `None` produces no finding; an unknown NC id still produces one warning; an empty value and a resolved entry still produce none; tool validation passes.

## Out of Scope
- Empty-value findings and other inventory schemas.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Accept `None` in `check_blocking_reference` and update the docstring | Completed | 20261022-115454 | 20261022-115454 | Changed: tools/check_needs_confirmation_inventory.py |
| 2 | Tests are covered by the test-file procedure | Completed | 20261022-115454 | 20261022-115454 | validated; full suite 9689 passed, 14 skipped; ruff, mypy, bandit on edited tools pass; docs checkers pass; tool tests 32 passed; live smoke run clean |
| 3 | Run the tool validation sequence per `routing.md` | Completed | 20261022-115454 | 20261022-115454 | validated; full suite 9689 passed, 14 skipped; ruff, mypy, bandit on edited tools pass; docs checkers pass; tool tests 32 passed; live smoke run clean |

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
- **Requirement ID**: `REQ-004` (accept `None` in the checker)
- **Source issue**: `issues/20261021-104533_blockingdef_define-the-blocking-field-in-the-needs-confirmation-inventory.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094758_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101832
- **Related target files**: tools/check_needs_confirmation_inventory.py