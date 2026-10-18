# Implementation Procedure — `scripts/agent/startup.py`

## Goal

Make a failure of `lifecycle.shutdown_all()` during startup rollback observable at a level
that reliably reaches the operator: when rollback fails, emit an operator-visible message via
the existing CLI view output channel in addition to the existing `logger.error(...)`, while
preserving the re-raise of the original startup exception (`REQ-001`, `REQ-002`).

## Scope

Modify only `scripts/agent/startup.py`. Add an operator-visible emit inside the
rollback-failure branch of `StartupOrchestrator.run()` (lines 76–85), alongside the existing
`logger.error(...)`. Do NOT alter or remove the final `raise setup_err` (line 85). Leave the
rollback-success path, normal startup logging, and the success path untouched.

## Assumptions

- The rollback-failure branch (lines 76–85): `except Exception as setup_err:` → try
  `shutdown_all()` → `except Exception as shutdown_err:` → `logger.error(...)` → `raise
  setup_err`.
- `self._view` is a `CLIView` (constructor requires it, lines 51–56) and is never `None` at
  rollback time.
- `CLIView` exposes two operator-output channels, both routing through the output port:
  `write_fatal(msg)` (cli_view.py:213 → `self._port.write_fatal(msg)`) and
  `write_stderr(text)` (cli_view.py:263 → `self._port.write_stderr(text)`).
- `write_fatal` is the established critical-startup-message channel (`startup_reporter.py:65`,
  `repl.py:141`).

## Adversarial verification findings (plan discrepancies)

- **No discrepancy.** Verified the rollback-failure branch, `self._view` typing, and both
  channel implementations against current source. The one genuine open question (UNK-01 —
  which channel reaches the console in every deployment mode) remains; recommend
  `write_fatal` as primary and confirm console routing before coding, falling back to
  `write_stderr` if needed.

## Design decisions

- Prefer approach (a) — `self._view.write_fatal("CRITICAL: Startup rollback FAILED —
  subprocesses may be orphaned")`. It semantically matches a CRITICAL rollback failure and is
  the established critical-startup channel.
- Approach (b) — `self._view.write_stderr(...)` — is acceptable if UNK-01 confirms direct
  stderr is more reliable across modes. Implement exactly one.
- Keep the console message concise and distinct from the logger line's structured
  `shutdown_err` detail (avoids log-aggregation confusion).
- Named boundary: only the rollback-failure branch changes; `raise setup_err` and the
  success path are untouched.

## Alternatives considered

- `write_stderr` vs `write_fatal`: both route through the output port; `write_fatal` chosen
  for semantic match and established usage. `write_stderr` kept as fallback (UNK-01).
- Raising a new exception instead of emitting: rejected — the plan preserves the verbatim
  re-raise of `setup_err` (REQ-002).

## Implementation

### Target file

`scripts/agent/startup.py`

### Procedure

1. In `StartupOrchestrator.run()`, inside the rollback-failure branch, add an emit AFTER the
   existing `logger.error(...)` block and BEFORE `raise setup_err`:
   ```python
   self._view.write_fatal(
       "CRITICAL: Startup rollback FAILED — subprocesses may be orphaned"
   )
   ```
   (or `self._view.write_stderr(...)` if UNK-01 favors direct stderr).
2. Confirm the `raise setup_err` statement is byte-for-byte unchanged.
3. Confirm the rollback-success path and normal paths are untouched.
4. Confirm the chosen channel reaches the console in all deployment modes (UNK-01) before
   finalizing; if uncertain, use `write_stderr`.

### Method

Edit the single branch inline; re-run the rollback test suite.

### Details

- Do not include the full `shutdown_err` in the console message (the logger line already has
  it); keep the console line concise.
- The emit is a pure side effect; it does not change `run()`'s return type or the exception
  it raises.

## Compatibility considerations

Only ADD a call in the rollback-failure branch; the success path and `raise setup_err` are
untouched (REQ-002, REQ-003). Existing rollback tests must still pass.

## Security considerations

Operational reliability: ensures orphaned-subprocess failures reach the operator rather than
being lost behind a possibly-unseen logger line.

## Rollback considerations

Revert the commit to `scripts/agent/startup.py`.

## Validation plan

- Unit (`tests/agent/test_startup_rollback.py`):
  - Extend `test_rollback_shutdown_failure_preserves_original_error` to assert the view emit
    (`write_fatal`/`write_stderr`) was called on rollback failure AND the original error is
    still raised (REQ-001, REQ-004).
  - Assert no operator-visible rollback emit occurs when `shutdown_all()` succeeds (REQ-003).
  - Confirm all existing rollback tests still pass (re-raise behavior locked, REQ-002).
- Command: `uv run pytest tests/agent/test_startup_rollback.py -q`.
- Lint/type: `uv run ruff check scripts/agent/startup.py` and `uv run mypy
  scripts/agent/startup.py` clean.

## Completion criteria

A failing `shutdown_all()` during startup emits an operator-visible console signal in addition
to the logger line, re-raises the original error unchanged, and produces no such emit on
rollback success.

## Out of scope

What `shutdown_all()` does/shuts down, other shutdown paths, normal startup logging, the
success path, the test file (separate row), and the doc update (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add operator-visible emit to rollback-failure branch | Completed | 20261018-103504 | 20261018-103504 | write_fatal recommended (confirm console routing) |
| 2 | Add or update tests per Validation plan | Completed | 20261018-103504 | 20261018-103504 | N/A: test file is a separate row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261018-103504 | 20261018-103504 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261018-103504 | 20261018-103504 | N/A: doc is a separate row |

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
- **Requirement ID**: `REQ-001` (operator-visible emit on rollback failure), `REQ-002`
  (preserve re-raise), `REQ-003` (success path unaffected)
- **Source issue**: `issues/20261017-123338_rollback01_surface-startup-rollback-failures-beyond-a-log-line.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-151428_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162051
- **Related target files**: `scripts/agent/startup.py`