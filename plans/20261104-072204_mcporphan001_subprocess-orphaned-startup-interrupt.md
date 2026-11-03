## Goal
- Eliminate the MCP-subprocess orphan created on the startup-failure paths of the HTTP subprocess readiness poll: a live child must either be terminated before its tracking entry is dropped, or — when its exit cannot be confirmed — be left tracked so the existing `shutdown_all()` reporting names it. Termination and tracking removal become one gated decision on every startup-failure path.

## Priority
High

## Scope
- **In-Scope**:
  - In `HealthChecker.poll_until_ready`, the "shutdown requested" branch terminates the live child through `ProcessTerminator.terminate_with_timeout` before the startup failure is raised.
  - In the same method, the readiness-timeout branch consumes the returned `TerminationOutcome`: tracking is dropped only on a confirmed exit; an unconfirmed exit keeps the process and pgid tracked.
  - `_raise_startup_failure` (or a sibling helper) drops tracking on a confirmed exit and keeps tracking on an unconfirmed exit without clearing the still-live child's stderr handles.
  - Update `tests/agent/test_http_lifecycle_integration.py`: make the existing shutdown-during-poll test assert termination, and add tests for the unconfirmed-termination branch.
  - Review `SubprocessLauncher.handle_getpgid_failure` for consistency with the new rule (see Reference Files).
- **Out-of-Scope**:
  - `ShutdownCoordinator.shutdown_all` internals and its return contract.
  - `ProcessTerminator.terminate_with_timeout` internals and the `TerminationOutcome` definition.
  - The early-exit branch of the poll loop (process already dead).
  - Converting a "shutdown requested" `HttpStartupError` into `StartupInterrupted` (shared with the retry issue).
  - Orphan prevention when the agent process itself is force-killed.
  - The startup retry cooldown path.

- **Dependencies**: [The Issue's Dependencies, including fix order against sibling issues or plans; `N/A: none` if there are none]
  - **Depends on**: `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md` | phase all | a "shutdown requested" `HttpStartupError` is a `RuntimeError` and currently enters the retry path; either issue can be fixed first — sequencing-only, no blocking.
  - **Depends on**: `issues/20261031-135634_validorder001_config-validation-after-spawn.md` | phase all | moving config-only validation before server start shrinks the orphan window but does not remove it; independent fix order.
  - **Depends on**: `issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md` | phase all | touches modules in the same area but is independent.

## Background
Found during an adversarial review (`python-code-review`) of the agent startup path. Related archived work `plans/done/20261022-082349_plan.md` made `shutdown_all()` report unconfirmed terminations on the *tracked-process* shutdown path; it does not cover the *startup-failure* path described here. The subprocess is launched with `start_new_session=True`, so it does not die with the agent process.

## Problem
`HealthChecker.poll_until_ready` ends in three ways, and all three call `HttpServerLifecycleManager._raise_startup_failure`, which pops the process and pgid entries and raises `HttpStartupError`:
- Process exited early: the process is already gone. No defect.
- Shutdown requested during the poll sleep: the process is alive, and nothing terminates it before the tracking entry is dropped.
- Readiness timeout: `terminate_with_timeout` is called, but its `TerminationOutcome` is ignored. An unconfirmed exit is dropped from tracking as if it were confirmed.

`ShutdownCoordinator.shutdown_all` iterates only the tracked processes, so an untracked survivor is invisible to the rollback in `StartupOrchestrator._rollback_servers` and to `ResourceShutdownCoordinator.close_resources`.

## Reason for Change
An orphaned MCP server keeps its configured port and keeps running after the agent has exited. A shutdown request during startup is exactly when an operator restarts the service, so the orphan is created in the situation where it is most likely to be hit again. The shutdown path already treats "exit not confirmed" as a reportable error; the startup-failure path silently does the opposite.

## Implementation Intent
Make process termination and tracking removal one decision on the startup-failure path: terminate first, drop the tracking entry only for a confirmed exit, and keep an unconfirmed process tracked so the existing `shutdown_all()` reporting names it. Keep the early-exit behavior unchanged. Reuse the existing `ProcessTerminator` and `TerminationOutcome` semantics instead of adding a second termination mechanism.

## Requirements
- `REQ-001`: On the "shutdown requested" branch of `poll_until_ready`, the live child is terminated through `ProcessTerminator.terminate_with_timeout` before the startup failure is raised.
- `REQ-002`: On the readiness-timeout branch, the returned `TerminationOutcome` is consumed: tracking is removed only when `confirmed` is true; otherwise the process and pgid stay tracked.
- `REQ-003`: For any startup-failure path that leaves a live process with an unconfirmed exit, the process (and its pgid) remain in the manager's tracking dicts and the unconfirmed outcome is logged; the still-live child's stderr handles are not cleared.
- `REQ-004`: The early-exit branch behavior is unchanged (process already dead → tracking dropped, `HttpStartupError` raised).
- `REQ-005`: A termination attempt that raises must not mask the original `HttpStartupError`; the original reason and full stderr still propagate.
- `REQ-006`: Subprocesses are still started in their own session (`start_new_session=True`) and termination still goes through the process group.
- `REQ-007`: The existing shutdown-during-poll test is updated to assert termination, and tests for the unconfirmed-termination branch are added.
- `REQ-008`: `TerminationOutcome` semantics and `ShutdownCoordinator.shutdown_all()`'s return contract are unchanged.

## Implementation Target Files
**Freeze status**: `Frozen` (Step 8 validation passed: all three rows `Verified` — exists, requires modification, supporting evidence, linked to a Plan requirement; no file path in both Target and Reference tables; no directory/glob/group rows).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/http_lifecycle_health_checker.py` | Modify `poll_until_ready`: add termination + outcome gating to the "shutdown requested" and readiness-timeout branches | Both branches currently leave a live child untracked; terminate-first and gate tracking drop on `TerminationOutcome.confirmed` | REQ-001, REQ-002 / AC-1, AC-2 | Step 2 verified: lines 174-188 drop tracking before/without consuming the outcome; `_cleanup_server_resources` pops tracking | `tests/agent/test_http_lifecycle_integration.py` | Verified |
| `scripts/agent/http_lifecycle.py` | Modify `_raise_startup_failure` (or add an unconfirmed variant) so confirmed exits drop tracking and unconfirmed exits keep tracking without clearing stderr handles | `_raise_startup_failure` unconditionally pops tracking; the unconfirmed path must keep the process tracked | REQ-003, REQ-005 / AC-3, AC-5 | Step 2 verified: `_raise_startup_failure` (lines 239-249) pops both dicts then raises; `_cleanup_server_resources` (lines 151-157) clears handles | `tests/agent/test_http_lifecycle_integration.py` | Verified |
| `tests/agent/test_http_lifecycle_integration.py` | Update `test_shutdown_event_set_before_poll_raises_promptly` and add unconfirmed-branch tests | Existing test pins only tracking removal, not termination; new behavior needs explicit coverage | REQ-007 / AC-4 | Step 2 verified: lines 1081-1110 assert `_http_procs`/`_http_pgids` empty but never that the child was terminated | `tests/agent/test_http_lifecycle_integration.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/http_lifecycle_subprocess_launcher.py` (`handle_getpgid_failure`) | Issue names it for consistency; verify it does not leave a *trackable* live process unreported. The child is never added to `_http_procs` (getpgid runs before registration) and has no pgid, so no tracking entry exists to keep — the existing terminate-and-log-unconfirmed handling is the correct behavior | Target `http_lifecycle_health_checker.py`; REQ-004 review |
| `scripts/agent/http_lifecycle_process_terminator.py` (`terminate_with_timeout`, `TerminationOutcome`) | Reuse the existing outcome vocabulary (`ALREADY_EXITED`/`EXITED`/`EXIT_UNCONFIRMED`/`SIGNAL_NOT_DELIVERED`); do not redefine it | Target `http_lifecycle_health_checker.py`; REQ-002, REQ-008 |
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` (`shutdown_all`) | Confirm it iterates the tracked dicts and therefore picks up a process kept tracked on an unconfirmed startup-failure; its return contract is unchanged | Target `http_lifecycle.py`; REQ-003, REQ-008 |
| `scripts/agent/startup.py` (`_rollback_servers`) | Confirm the kept-tracked orphan surfaces as an unconfirmed entry in the rollback fatal report | Target `http_lifecycle.py`; REQ-003 |

## Acceptance Criteria
- `AC-1`: After a shutdown request during the readiness poll, the spawned process is terminated (confirmed exit) or remains tracked with an unconfirmed outcome that `shutdown_all()` returns. (`REQ-001`, `REQ-003`)
- `AC-2`: After a readiness timeout with an unconfirmed termination, the process stays tracked and `shutdown_all()` reports its server key. (`REQ-002`, `REQ-003`)
- `AC-3`: The early-exit behavior is unchanged. (`REQ-004`)
- `AC-4`: No test relies on the removed behavior of dropping a live process from tracking on a startup-failure path. (`REQ-007`)
- `AC-5`: A termination failure does not mask the original `HttpStartupError` reason or stderr. (`REQ-005`)
- `AC-6`: `TerminationOutcome` semantics and `shutdown_all()`'s return contract are unchanged. (`REQ-008`)

## Tests
- `T-1` (integration, `REQ-001`/`REQ-003`): a real harmless child (`sleep`) that sets the shutdown event before the poll; assert the child is gone afterward (kill the child in teardown).
- `T-2` (unit, `REQ-002`/`REQ-003`): a fake terminator returning `EXIT_UNCONFIRMED` on the readiness-timeout branch; assert the tracking entry is kept and reported by `shutdown_all()`.
- `T-3` (unit, `REQ-001`): a fake terminator returning `EXITED` on the "shutdown requested" branch; assert `terminate_with_timeout` was called and tracking was dropped.
- `T-4` (update existing, `REQ-007`): `test_shutdown_event_set_before_poll_raises_promptly` asserts termination was attempted and the reason is unchanged.
- `T-5` (unit, `REQ-005`): a terminator that raises; assert the original `HttpStartupError` (reason + stderr) is still raised.

## Documentation Impact
`N/A: no document under `docs/22_mcp/` states what happens to a process whose startup fails` (verified with `rg` over `docs/22_mcp/` in Step 5). Per the issue's conditional, no documentation update is required.

## Assumptions
- A-1: A process kept tracked on an unconfirmed startup-failure is picked up by `shutdown_all()` because it remains in `_http_procs`/`_http_pgids`, which `ShutdownCoordinator.shutdown_all` iterates. (Verified in `http_lifecycle_shutdown_coordinator.py`.)
- A-2: `terminate_with_timeout` on a mock/fake pid whose group does not exist returns `ALREADY_EXITED` via the `ProcessLookupError` path, so the updated unit test with a fake pid does not hang. (Verified in `http_lifecycle_process_terminator.py` lines 194-197.)
- A-3: `start_new_session=True` is retained so process-group termination resolves a real pgid. (Constraint.)

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a "shutdown requested" startup failure should be converted to `StartupInterrupted` at this layer or at the caller. Shared with the retry issue. | End-to-end classification of the exception at the `StartupOrchestrator.run` boundary. | Defer to the retry issue; out of scope here. Log the decision point for `plan-to-implementation-procedure`. | False |
| UNK-02 | Whether a surviving orphan actually holds the configured port, so the next agent start fails to bind or health-polls a stale server. | Server-specific port-bind behavior. | Informational; not required to close the orphan-tracking defect. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/http_lifecycle_health_checker.py` | Add terminate-first + outcome-gated tracking drop to two poll-loop branches | Startup readiness poll → orphan survivor → rollback reporting via `shutdown_all()` | 3 | 1 | N/A: library code, no deploy script |
| `scripts/agent/http_lifecycle.py` | Split tracking-drop vs keep-on-`TerminationOutcome` in `_raise_startup_failure` | All startup-failure paths raise through this method; affects every MCP subprocess | 11 | 1 | N/A: library code, no deploy script |
| `tests/agent/test_http_lifecycle_integration.py` | Update one test, add two unit tests | Test coverage only; no runtime blast radius | 2 | 1 | N/A: test-only |

## Design
- **Single gated decision.** Both startup-failure branches ("shutdown requested" and "readiness timeout") funnel through one rule: call `terminate_with_timeout`, then drop the tracking entries only when `outcome.confirmed` is true; otherwise keep `(server_key, proc)` in `_http_procs` and the pgid in `_http_pgids`, log the `EXIT_UNCONFIRMED` outcome, and raise the original `HttpStartupError`. The early-exit branch is untouched (the child is already dead).
- **Tracking helper split.** `_raise_startup_failure` currently pops both dicts unconditionally. The confirmed path keeps using it (drop + raise). The unconfirmed path must raise *without* popping and without clearing the still-live child's stderr handles or health-check timestamps — it only needs the stderr tail text for the report. The implementation procedure chooses between (a) a sibling `_raise_startup_failure_unconfirmed` that builds and raises `HttpStartupError` without touching tracking, or (b) reading the stderr tail directly and raising a fresh `HttpStartupError`. Either way the confirmed and unconfirmed paths must not share a handle-clearing step.
- **Reuse, do not redefine.** `ProcessTerminator.terminate_with_timeout` and the `TerminationOutcome` vocabulary are reused as-is; no new termination mechanism and no change to `TerminationOutcome`.
- **No masking.** If `terminate_with_timeout` raises, the original `HttpStartupError` (reason + stderr) is still raised; the termination error is logged, not propagated.
- **Interface stability.** `poll_until_ready`'s signature, `start()`'s signature, and `shutdown_all()`'s return contract are unchanged.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit (see `### Release units` below) when a phase breaks existing callers or tests until another phase lands (for example a `NOT NULL` column added before its write path): one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be validated alone}`.

1. **Phase 1: Core logic — outcome-gated tracking on the startup-failure path**
   - [ ] `REQ-002`; `scripts/agent/http_lifecycle_health_checker.py` — in the readiness-timeout branch, capture the `TerminationOutcome` from `terminate_with_timeout` instead of discarding it.
   - [ ] `REQ-001`; `scripts/agent/http_lifecycle_health_checker.py` — in the "shutdown requested" branch, call `terminate_with_timeout` on the live child before the startup failure is raised.
   - [ ] `REQ-003`, `REQ-005`; `scripts/agent/http_lifecycle.py` — split `_raise_startup_failure` into a confirmed path (drop tracking + raise) and an unconfirmed path (keep tracking + log + raise without clearing handles); guard termination so a raise there does not mask the original error.
2. **Phase 2: Tests**
   - [ ] `REQ-007`; `tests/agent/test_http_lifecycle_integration.py` — update `test_shutdown_event_set_before_poll_raises_promptly` to assert termination was attempted; add the unconfirmed-branch test (`T-2`), the confirmed-shutdown test (`T-3`), and the no-mask test (`T-5`).
   - [ ] `REQ-001`/`REQ-003`; `tests/agent/test_http_lifecycle_integration.py` — add the integration test with a real `sleep` child (`T-1`), killing it in teardown.
3. **Phase 3: Verification & consistency review**
   - [ ] `REQ-004`; `scripts/agent/http_lifecycle_subprocess_launcher.py` — review `handle_getpgid_failure` for consistency; confirm no trackable live process is left unreported (expected: no change).
   - [ ] `REQ-008`; run `tests/agent/test_http_lifecycle_integration.py`, `tests/agent/test_startup_rollback.py`, `ruff`, and `mypy --no-namespace-packages`.

### Release units
N/A: no release unit. The `HttpStartupError` contract and `shutdown_all()` return type are unchanged, so no phase holds back a change behind another.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle_health_checker.py` | Unit: fake terminator outcomes drive both branches; Integration: real `sleep` child | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | New/updated tests pass; orphan terminated or reported |
| `scripts/agent/http_lifecycle.py` | Unit: confirmed vs unconfirmed raise paths | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | Confirmed drops tracking; unconfirmed keeps it and is reported |
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | Integration: `shutdown_all()` returns kept-tracked server key | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | Unconfirmed server key present in return value |
| Whole module | Static gates | `uv run ruff check` ; `uv run mypy --no-namespace-packages scripts/agent/http_lifecycle*.py` | Clean (baseline already clean) |

## Risks
- **Risk**: Keeping a process tracked on an unconfirmed exit could interact with `start()`'s idempotency reuse (`_http_procs.get(key)` alive) if the same key is started again in the same run. **Mitigation**: the startup-failure path raises and aborts `StartupOrchestrator.run`, so no in-run retry reuses the key; verify in `T-2`/`T-3` that a kept-tracked process is not reused.
- **Risk**: The updated integration test with a real `sleep` child adds wall-clock time to the suite (baseline ~30 s). **Mitigation**: use `AsyncMock` terminator outcomes for deterministic unit tests (`T-2`/`T-3`/`T-5`); keep one real-child integration test (`T-1`) with a guaranteed teardown kill.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`. Default rows for a freshly generated Plan (replace with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-072204
- **Related target files**: `scripts/agent/http_lifecycle_health_checker.py`, `scripts/agent/http_lifecycle.py`, `tests/agent/test_http_lifecycle_integration.py`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes / Acceptance Criteria | `scripts/agent/http_lifecycle_health_checker.py` | Step 1 | AC-1 | T-3, T-1 | Confirmed by repository evidence |
| REQ-002 | Required Changes / Acceptance Criteria | `scripts/agent/http_lifecycle_health_checker.py` | Step 1 | AC-2 | T-2 | Confirmed by repository evidence |
| REQ-003 | Implementation Intent / Acceptance Criteria | `scripts/agent/http_lifecycle.py` | Step 1 | AC-1, AC-2 | T-1, T-2 | Derived from confirmed evidence |
| REQ-004 | Constraints | `scripts/agent/http_lifecycle_health_checker.py` (early-exit branch, no change) | Step 3 | AC-3 | Existing tests pass | Explicit in issue |
| REQ-005 | Constraints / AI Implementation Instruction | `scripts/agent/http_lifecycle.py` | Step 1 | AC-5 | T-5 | Explicit in issue |
| REQ-006 | Constraints | N/A: enforced by not modifying the launcher/terminator (reference files) | Step 1 | N/A: non-functional constraint | ruff/mypy gate | Explicit in issue |
| REQ-007 | Required Changes / Testing Expectations | `tests/agent/test_http_lifecycle_integration.py` | Step 2 | AC-4 | T-4, T-5, T-1, T-2, T-3 | Explicit in issue |
| REQ-008 | Constraints | N/A: enforced by not modifying the terminator/coordinator (reference files) | Step 3 | AC-6 | ruff/mypy + existing tests | Explicit in issue |

