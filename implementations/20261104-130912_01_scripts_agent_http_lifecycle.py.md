## Goal
Add the unconfirmed startup-failure raise path to `HttpServerLifecycleManager` so tracking
removal becomes gated on `TerminationOutcome`: `REQ-003` (unconfirmed exit keeps the live
process tracked) and `REQ-005` (the raise still carries the original reason and full stderr).
The confirmed path (`_raise_startup_failure`) stays byte-for-byte compatible for the
early-exit branch (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- Only one new method on `HttpServerLifecycleManager`; no existing method's behavior changes.
- This row must land before `20261104-130912_02_scripts_agent_http_lifecycle_health_checker.py`
  — that document's poll branches call the method created here.

## Assumptions
- Plan A-1: a process kept in `_http_procs`/`_http_pgids` is picked up by
  `ShutdownCoordinator.shutdown_all` (verified: it iterates `manager.iter_processes()`).
- `check_plan_target_overlaps.py` reports no overlap naming this Plan.
- `HttpStartupError`, `StartupFailure`, and `TerminationOutcome` are already imported in
  the target file (line 46); no new import is required.

## Design decisions
- Sibling method `_raise_startup_failure_unconfirmed` (new) implements the unconfirmed path:
  it builds and raises `HttpStartupError(StartupFailure(...))` without touching
  `_http_procs`, `_http_pgids`, `_stderr_files`, `_stderr_log_manager`, or
  `_last_health_check` (Plan Design "Tracking helper split", option (a)).
- Its error log mirrors `ShutdownCoordinator._terminate_one`'s retained-tracking wording
  (server_key, pid, pgid, outcome, manual `kill -TERM -{pgid}` hint) so operators see one
  consistent signal from both paths.
- `_raise_startup_failure` keeps its exact behavior; only its docstring is extended to state
  it is the confirmed path (drop + raise) and must not be called for an unconfirmed outcome.

## Alternatives considered
- (b) Inline raise inside each poll branch (`http_lifecycle_health_checker.py`): rejected —
  the gated decision would be duplicated across two files and invisible from the manager API.
- Adding an `outcome` keyword to `_raise_startup_failure`: rejected — a `None` default would
  silently keep the drop-on-unconfirmed misuse the Plan is eliminating.

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`

### Procedure
Insert one new method directly after `_raise_startup_failure` (lines 239-249) in
`HttpServerLifecycleManager`; extend `_raise_startup_failure`'s docstring. No other edits.

### Method
- Add `_raise_startup_failure_unconfirmed(self, server_key: str, reason: str, stderr_full: str) -> NoReturn` (new):
  - `proc = self._http_procs.get(server_key)`; `pid = getattr(proc, "pid", None)`;
    `pgid = self._http_pgids.get(server_key)`.
  - `logger.error("Lifecycle: %r pid=%s pgid=%s startup failure with exit not confirmed; process, pgid and stderr-log tracking retained, stop it manually with: kill -TERM -%s", server_key, pid, pgid, pgid)`.
  - Raise `HttpStartupError(StartupFailure(server_key=server_key, reason=reason, stderr_full=stderr_full))`
    — identical failure payload to the confirmed path (`REQ-005`).
- Docstring of `_raise_startup_failure`: append one sentence marking it the confirmed path
  (tracking already dropped); unconfirmed outcomes use the sibling.

### Details
- The new method MUST NOT pop, clear, close, or forget anything — REQ-003's whole point is
  that the still-live child keeps its process/pgid entries and its stderr log handle open.
- Reason strings ("shutdown requested", "did not become healthy within {N}s") are composed by
  the caller (`http_lifecycle_health_checker.py`, row 02); this method stays reason-agnostic.
- No masking added here: stderr content is masked at the existing report sites; this method
  logs only pid/pgid.

## Compatibility considerations
- No public signature changes; `start()`, `poll_until_ready()`, `shutdown_all()` contracts are
  unchanged (`REQ-008` respected by not touching the terminator/coordinator).
- `start()` idempotency (`existing.poll() is None` reuse) intentionally lets a kept-tracked
  survivor be re-terminated by the next `shutdown_all()`; the startup-failure path aborts the
  run, so no in-run reuse happens (Plan Risks mitigation, verified in row 03's T-2).

## Security considerations
- The error log names pid/pgid only — no secrets, no raw stderr — consistent with
  `python-code-review` masking policy.

## Rollback considerations
- N/A: revert the commit (one new method plus one docstring sentence).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Row-03 tests for this helper | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | T-2/T-5 pass; existing tests unmodified in behavior |
| Static gates | `uv run ruff check scripts/agent/http_lifecycle.py` ; `uv run mypy --no-namespace-packages scripts/agent/http_lifecycle.py` | Clean |
| Module-size/ref-table drift | `radon cc -nc scripts/agent/http_lifecycle.py` ; `uv run python tools/generate_reference_table.py --check` | no new B+ block; first-docstring lines unchanged → no drift |

## Completion criteria
- `_raise_startup_failure_unconfirmed` (new) exists and raises without touching any tracking
  dict or stderr handle; the unconfirmed-branch tests in row 03 confirm the process stays
  tracked and `shutdown_all()` names it.
- Confirmed/early-exit behavior is unchanged (`AC-3`); all static gates pass.

## Out of Scope
- The poll-branch wiring (row 02 document), the terminator, `ShutdownCoordinator`, the
  launcher's `handle_getpgid_failure` (Plan Reference Files), and the
  `StartupInterrupted` classification question (Plan UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests live in the row-03 document; this row is verified by them |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation | Pending | — | — | N/A per Plan Documentation Impact: no doc states startup-failure tracking behavior |

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
- **Requirement ID**: `REQ-003` (keep unconfirmed process tracked), `REQ-005` (no error masking)
- **Source issue**: `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-072204_mcporphan001_subprocess-orphaned-startup-interrupt.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-130912
- **Related target files**: `scripts/agent/http_lifecycle.py`
