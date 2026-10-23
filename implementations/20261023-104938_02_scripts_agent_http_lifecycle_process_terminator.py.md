## Goal

Convert `ProcessTerminator.terminate_with_timeout` from a `bool` return into the
`TerminationOutcome` vocabulary introduced in row 1 (REQ-002), and state the four-way
evidence mapping in its docstring (REQ-003). Every one of the method's nine return arms
becomes a concrete outcome instead of `True`/`False`, so "not stopped" is observable
(REQ-004). This is the Plan's highest-risk row: the change is behavioral across the whole
method, and the coordinator (row 3) consumes the new type.

## Scope

Only `terminate_with_timeout` in `scripts/agent/http_lifecycle_process_terminator.py`.
No helper, field, or signature changes. Reference reads: `_resolve_pgid` (`:24`),
`_already_exited` (`:43`), `_reap` (`:54`), `wait_exited` (`:83`) — unchanged. Consumer:
`scripts/agent/http_lifecycle_shutdown_coordinator.py` (row 3). Dependent test:
`tests/agent/test_http_lifecycle_process_terminator.py` (row 12).

## Assumptions

- The nine `return True`/`return False` arms of `terminate_with_timeout` map one-to-one
  onto the four `TerminationOutcome` members; the mapping below is exhaustive.
- `wait_exited` keeps returning `bool`: it is a liveness probe, not a termination
  verdict, and the Plan marks only `terminate_with_timeout` as changing (REQ-002).
- Callers that currently treat the result as a truthy bool must switch to comparing the
  `TerminationOutcome` member (the coordinator, row 3).

## Design decisions

- **Map each return arm by the evidence actually gathered**, not by intent:
  - Line `:132` (no pgid, already exited) → `ALREADY_EXITED`.
  - Line `:144` (no pgid, `proc.terminate()` fallback sent, no confirmation) →
    `EXIT_UNCONFIRMED`.
  - Line `:149` (already exited before any signal) → `ALREADY_EXITED`.
  - Line `:167` (`ProcessLookupError` on SIGTERM — group already gone) → `EXITED`.
  - Line `:180` (`OSError` on SIGTERM, `proc.terminate()` fallback, no confirmation) →
    `EXIT_UNCONFIRMED`.
  - Line `:198` (group exited within the timeout, confirmed via `ProcessLookupError`) →
    `EXITED`.
  - Line `:204` (SIGKILL escalated) → `EXIT_UNCONFIRMED` (REQ-004).
  - Line `:206` (`ProcessLookupError` after SIGKILL — already gone) → `EXITED`.
  - Line `:211` (SIGKILL raised `OSError`, process still running) → `SIGNAL_NOT_DELIVERED`.
- **Docstring `Returns:` lists all four outcomes** with their evidence line, matching
  row 1's member docstrings (REQ-003). The existing `Raises: HttpStartupError` note stays.
- **No signature change.** The `timeout` parameter and the method name are unchanged;
  only the return annotation flips to `TerminationOutcome`.

## Alternatives considered

- Returning a richer dataclass instead of the enum — rejected: the Plan requires the
  exact `TerminationOutcome` vocabulary (REQ-001/002), and the enum carries the evidence
  inline.
- Mapping SIGKILL escalation to `SIGNAL_NOT_DELIVERED` — rejected by REQ-004: the signal
  *was* delivered and executed; the process simply did not die, which is `EXIT_UNCONFIRMED`.

## Implementation

### Target file

`scripts/agent/http_lifecycle_process_terminator.py`

### Procedure

1. Read `scripts/agent/http_lifecycle_process_terminator.py` around `:115-211`.
2. Change the return annotation of `terminate_with_timeout` (`:117`) to
   `-> TerminationOutcome` and import `TerminationOutcome` from
   `http_lifecycle_errors` (row 1).
3. Replace the docstring `Returns:` block (`:125-126`) with the four-way mapping table
   from the Design decisions above, keeping the `Raises: HttpStartupError` line.
4. Rewrite each of the nine return statements to return the mapped member, e.g.
   `return TerminationOutcome.ALREADY_EXITED`, `return TerminationOutcome.EXITED`,
   `return TerminationOutcome.EXIT_UNCONFIRMED`, `return TerminationOutcome.SIGNAL_NOT_DELIVERED`.
5. Leave `wait_exited` (`:83-113`) and the three helpers untouched.

### Method

Edit in place; do not restructure the method. Swap only the return expressions and the
annotation/docstring. Keep the `# nosec` comments and logging intact.

### Details

- REQ-004 is satisfied solely by the line `:204` arm returning `EXIT_UNCONFIRMED`.
- mypy flags the coordinator (row 3) until it compares against `TerminationOutcome`,
  which is the cross-check that the conversion propagated.
- The `# nosec B603` comments on the `os.killpg` lines (`:156`, `:202`) are unrelated to
  this change; do not touch them.

## Compatibility considerations

- Behavioral: callers must compare the returned `TerminationOutcome`, not test truthiness.
  The coordinator (row 3) is the only caller and is updated in the same commit.
- No public API surface beyond the return type changes; the method name, args, and
  side effects (signals sent) are identical.

## Security considerations

- N/A: no auth, secret, or permission change. The `# nosec B603` annotations on the
  process-group signals remain; this row does not alter signaling behavior.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/http_lifecycle_process_terminator.py`
  restores HEAD. Reversible; touches no config or DB. Because this is the highest-risk
  row, keep the diff reviewable: one method, nine return swaps, one annotation, one
  docstring.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py` (row 12) — the
  new test asserts each of the four outcomes for the corresponding process state.
- `uv run mypy --no-namespace-packages scripts/agent` (the new return type resolves at the
  coordinator call site, row 3).
- `uv run ruff check scripts/agent/http_lifecycle_process_terminator.py`.

## Completion criteria

`terminate_with_timeout` returns exactly the four `TerminationOutcome` members per the
mapping above, its docstring states the mapping (REQ-003), SIGKILL escalation returns
`EXIT_UNCONFIRMED` (REQ-004), `wait_exited` and the helpers are unchanged, and the
behavioral tests plus mypy pass.

## Out of Scope

- The vocabulary definition (row 1), the coordinator branch (row 3), the chain return
  (rows 4-9), the tests (row 12), and the docstring corrections (rows 5, 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Convert `terminate_with_timeout` returns to `TerminationOutcome` (nine arms, REQ-002/003/004) | Pending | — | — | High risk |
| 2 | Add/update behavioral tests (row 12) | Pending | — | — | REQ-001 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | AC-9 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `scripts/agent/http_lifecycle_process_terminator.py`
