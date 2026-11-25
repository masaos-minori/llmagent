## Goal

Pin the warning wording for a server that was terminated but whose exit could not be confirmed, so the new unconfirmed reporting stays a non-fatal, redacted warning line (REQ-010: termination bounded by the shutdown deadline; REQ-012: every step reported).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the warning-wording cases in this file.
- Out of scope: the terminator (row 12), the coordinator (row 11), and the step report (row 5).

## Assumptions

- Cleanup failures are non-fatal by policy (`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`), and today every collected error is written as a warning (`scripts/agent/resource_shutdown_coordinator.py:168-171`).
- The Plan keeps that behavior (Unknowns UNK-04): the warning line stays, with a redacted detail, and the step record is the durable answer.

Step 3b verification against the current source (20261125-122600):

- The `scripts/agent/resource_shutdown_coordinator.py:168-171` anchor is not what these cases read. The three cases assert the terminator's own console line, which is the no-pgid fallback warning at `scripts/agent/http_lifecycle_process_terminator.py:239-243`: `Lifecycle: %r pid=%s has no pgid; proc.terminate() fallback, exit not observed`.
- The assertions are shared through `_LineCapture` (`:18`), `_attach()` (`:38`), and `_assert_unconfirmed_termination_line()` (`:47`): exactly one `proc.terminate() fallback` warning naming the server key, containing `exit not observed`, containing no `/`, and nothing logged at ERROR or worse. The SIGKILL confirm line (`:315-320`) is an error line by design and is not what the cleanup warning policy covers.
- The three cases are unchanged in name: `test_terminate_warning_when_no_pgid`, `test_terminate_warning_when_killpg_fails`, `test_terminate_warning_integration_simulation`.

## Design decisions

- Assert the warning as a warning, not an error or a fatal line: the policy that cleanup failure must not mask the original failure is what these cases protect.
- Assert that the wording names the server key and the outcome, and that it contains no absolute path or raw exception text (REQ-013).
- Keep the existing three terminate-call expectations and only adjust the wording they produce.
- Compatibility impact: wording only; the outcome values are unchanged.

## Alternatives considered

- drop the warning and rely on the step record — rejected: UNK-04 is resolved as "keep today's behavior", and an operator who never reads the record must still see that a process may be orphaned.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_warning.py`

### Procedure
1. Update the warning-wording expectations to the unconfirmed-termination wording produced by row 11.
2. Add an assertion that the warning text names the server key and the outcome and contains no absolute path.
3. Keep the cases asserting the warning severity is non-fatal.

### Method

- Wording assertions on the emitted line, with the severity assertion kept from the existing cases.

### Details

- The case that a terminated-but-unconfirmed server produces exactly one warning line is what prevents the report and the console from duplicating it.

## Compatibility considerations

- Existing case structure is preserved; only the expected wording changes.

## Security considerations

- The no-path assertion is the REQ-013 check for this output path.

## Rollback considerations

- Revert this row's commit with rows 11 and 33.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/test_http_lifecycle_warning.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle_warning.py -q` | unconfirmed termination produces one non-fatal, path-free warning |

## Completion criteria

- A terminated-but-unconfirmed server produces exactly one non-fatal warning naming the server and the outcome, with no path in the text.

## Out of Scope

- The step record and the clamping implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-122329 | 20261125-122329 | _LineCapture (:18), _attach() (:38) and _assert_unconfirmed_termination_line() (:47) replace the per-case wording checks |
| 2 | Add or update tests per Validation plan | Completed | 20261125-122329 | 20261125-122329 | this row is the test row this row is the test row; the three existing cases now assert one warning naming the server key, `exit not observed`, no `/`, nothing at ERROR |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-122329 | 20261125-122329 | ruff format/check, pytest Pass; the asserted line is scripts/agent/http_lifecycle_process_terminator.py:239-243 |

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
- **Requirement ID**: REQ-010 (termination bounded by the shutdown deadline), REQ-012 (every step reported)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `tests/agent/test_http_lifecycle_warning.py`, `scripts/agent/http_lifecycle_shutdown_coordinator.py`