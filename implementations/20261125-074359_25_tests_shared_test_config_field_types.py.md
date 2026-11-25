## Goal

Cover the shared strict primitives: type rejection, bool-for-number rejection, empty and
whitespace-only strings, non-string mapping values, unknown-key rejection, and error text that never
contains the raw value (REQ-001, shared strict type rules; REQ-011, structured config error).

## Scope
**Release unit**: R1-strict-primitives

## Assumptions
- The primitives are created by row 1; this file is written before the implementation, per the Plan's
  Phase 1 order (tests first).
- The error text assertions must fail against the current coercive behavior, so the tests define the
  contract before the module exists.

## Design decisions
- One test per rule rather than a table, so a failure names the rule that regressed.
- Every rejection test asserts the message contains the field path and not the value.

## Alternatives considered
- Testing the primitives through the delegating validators — rejected: that would not prove the leaf
  module itself is correct.

## Implementation
### Target file
`tests/shared/test_config_field_types.py` (new)

### Procedure
Write the strict-primitive tests listed in the Plan's Phase 1.

### Method
- Cases: non-bool to `strict_bool`; `bool` and strings to `strict_int` and `strict_float`; non-string to
  `strict_str`; sequence element checks; empty and whitespace-only strings; non-string mapping values;
  unknown-key rejection.
- A message-shape test asserts the raw value is absent from every raised message.

### Details
- The `allow_empty` flag is exercised both ways so the registry decision (row 4, UNK-05) has coverage on
  both branches.

## Compatibility considerations
- New file; no existing coverage for a shared strict layer.

## Security considerations
- The no-value assertion is the security check for this file.

## Rollback considerations
- Revert the Phase 1 commit.

## Validation plan
- `uv run pytest tests/shared/test_config_field_types.py -q`
- `uv run ruff check tests`

## Completion criteria
- Every rule in row 1 has a failing-before and passing-after case, and no test asserts a message that
  contains a configuration value.

## Out of Scope
- The parity table that runs the same values through both paths (row 27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | tests written before row 1 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-011 (structured config error); AC-1
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `tests/shared/test_config_field_types.py`
