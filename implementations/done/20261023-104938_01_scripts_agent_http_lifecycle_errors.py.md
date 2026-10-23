## Goal

Add the `TerminationOutcome` vocabulary this Plan's behavior change returns (REQ-001):
a `StrEnum` with four members, each named for the evidence that produces it, placed
beside the HTTP-lifecycle failure types it joins.

## Scope

New public class in `scripts/agent/http_lifecycle_errors.py` only. No existing member,
field, or `__all__` entry changes. Reference read:
`scripts/agent/http_lifecycle_process_terminator.py` (the consumer, row 2). Dependent
test: `tests/agent/test_http_lifecycle_process_terminator.py` (row 12).

## Assumptions

- `http_lifecycle_errors.py` is the home of this subsystem's failure vocabulary
  (`StartupFailure` at `:20`, `HttpStartupError` at `:28`); the new type joins it there
  so the terminator and coordinator import one module (Design → Import layer).
- The four members map one-to-one onto the nine current `return True` arms of
  `terminate_with_timeout` (row 2), so every exit has exactly one value.

## Design decisions

- **`StrEnum`, four members, one evidence line each.** `EXITED` (exit observed within
  the confirmation bound), `ALREADY_EXITED` (observed before any signal),
  `SIGNAL_NOT_DELIVERED` (no signal call succeeded), `EXIT_UNCONFIRMED` (a signal call
  succeeded, exit not observed within the bound). One docstring line per member states
  the evidence — the same prose the terminator's `Returns:` section cites (REQ-001).
- **No change to existing members.** `StartupFailure` and `HttpStartupError` keep their
  members and docstrings; the new class is additive only.

## Alternatives considered

- A plain `enum.Enum` — rejected: callers format the member into the `http_termination`
  string (`resource_shutdown_coordinator.py`, row 9), and `StrEnum` gives a stable
  string form without a `.value` lookup.
- Reusing a bool or raising `HttpStartupError` — rejected in the Plan's Design (why
  returned, not raised); the four-way split is what makes "not stopped" observable.

## Implementation

### Target file

`scripts/agent/http_lifecycle_errors.py`

### Procedure

1. Read `scripts/agent/http_lifecycle_errors.py` around `:19-30` to place the new class
   immediately after `HttpStartupError` (`:28`).
2. Add the class:
   ```python
   class TerminationOutcome(StrEnum):
       """Outcome of one MCP server's termination attempt (see
       terminate_with_timeout)."""

       EXITED = "exited"
       """Exit observed within the confirmation bound."""
       ALREADY_EXITED = "already_exited"
       """Exit observed before any signal was sent."""
       SIGNAL_NOT_DELIVERED = "signal_not_delivered"
       """No signal call succeeded."""
       EXIT_UNCONFIRMED = "exit_unconfirmed"
       """A signal call succeeded; exit was not observed within the bound."""
   ```
3. Confirm no `__all__` or other module references the new names.

### Method

Place the class after `HttpStartupError` (`:28`) beside `StartupFailure` (`:20`), the
existing failure vocabulary. Keep it a `StrEnum`; the four members are the only additions.

### Details

- REQ-001 requires the mapping to be stated in `terminate_with_timeout`'s docstring
  (row 2); this row supplies the vocabulary it cites.
- mypy across the five `shutdown_all` definitions (rows 3-8) is what proves the new type
  is imported everywhere the return value flows.

## Compatibility considerations

### Corrections found while implementing

- `TerminationOutcome` added after `HttpStartupError` with the four members as written, plus a `confirmed` property (True for EXITED/ALREADY_EXITED) so the single settle rule lives in one place. `StrEnum` import added.


- N/A: purely additive. No member, field, or signature anywhere else changes; the type
  is imported by the terminator (row 2) and the coordinator (row 3) only.

## Security considerations

- N/A: no auth, secret, or permission change. A new enum is data, not a privilege.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/http_lifecycle_errors.py`
  restores HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run mypy --no-namespace-packages scripts/agent` (the new import resolves at every
  call site, rows 2-8).
- `uv run ruff check scripts/agent/http_lifecycle_errors.py`.
- `uv run python tools/generate_reference_table.py --type agent` then `--check --type
  agent` (AC-9): the new public class adds one row to
  `docs/23_agent/agent_13_reference-api-generated.md` (row 21).

## Completion criteria

`TerminationOutcome` exists as a `StrEnum` with exactly the four members above, each
with a one-line evidence docstring, beside the existing failure types; mypy and the
reference-table check pass; no existing member changed.

## Out of Scope

- The return-type conversion (row 2), the coordinator branch (row 3), the chain return
  (rows 4-9), the tests (rows 12-17), and the docstring/doc corrections (rows 5, 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TerminationOutcome` StrEnum (four members, one evidence line each) | Completed | 20261023-152936 | 20261023-152936 | REQ-001 implemented; full suite passed |
| 2 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-152936 | 20261023-152936 | AC-9 |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `scripts/agent/http_lifecycle_errors.py`