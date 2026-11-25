# Plan: Unify MCP process ownership, lifecycle state, shutdown, and restart safety

## Goal
- Establish one managed-process ownership contract across startup failure, normal shutdown, PGID failure, and restart: a record is released only on confirmed exit. Extend the lifecycle state machine with outcome states, reject invalid transitions without mutation, and make shutdown-time lifecycle calls raise typed suppression errors instead of returning silently.

## Priority
High

## Scope
- **In-Scope**:
  - `ManagedProcessRecord` ownership contract; delete records only on confirmed exit.
  - Remove the pre-termination process-entry deletion in normal shutdown.
  - Keep process/pgid tracking after a PGID failure unless exit is confirmed.
  - Require confirmed old-process exit before restart.
  - Add `STOPPING`, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED` to `LifecycleState`; set state per server outcome; never set `STOPPED` globally without confirmation.
  - Reject invalid transitions without mutating state.
  - Typed non-retryable suppression errors from `ensure_ready()` and `restart()` during shutdown.
  - Show retained unconfirmed processes in `/mcp status` (populate `last_shutdown_result`).
  - Repeated shutdown safety (idempotent second `shutdown_all()`).
- **Out-of-Scope**:
  - Launch-spec and credential work (cliplc006, archived).
  - Health semantics (cliplc008).
  - A new manual-cleanup command. Per the maintainer decision (2026-11-25), no new `/mcp` subcommand is added: retained unconfirmed records are surfaced through `/mcp status`, and the operator-side action remains the logged `kill -TERM -<pgid>` guidance.
- **Dependencies**:
  - Depends on cliplc004 (bounded shutdown machine, archived) and cliplc006 (launch spec, archived) — both satisfied; this Plan builds on the shutdown budget and the safe launch contract they established.
  - Blocks cliplc008 (health capability) and cliplc009 (redaction, stderr diagnostics).
  - **Depends on**: N/A: both dependency issues are already archived; no ordering constraint remains against an open Plan.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (memo-issue.md, Issue 6). The issue cited two archived predecessors (star001 subprocess-termination ownership, mcp001 double startup failure) and marked the path-dependent ownership claims as `Needs confirmation`. Step 2 re-verified every path-dependent claim against current source; results are in the Problem section.

## Problem
Per-claim verification against current source (2026-11-25):

| Issue claim | Status | Evidence |
|---|---|---|
| Startup failure keeps an unconfirmed process | Already implemented — no defect remains | `scripts/agent/http_lifecycle.py` `_raise_startup_failure_unconfirmed()` retains process/pgid/stderr tracking; `_reterminate_recorded_failed_start()` re-terminates only on confirmed exit |
| Normal shutdown removes the entry before confirmation | Defect confirmed | `http_lifecycle_shutdown_coordinator.py` calls `remove_process_entry()` before any signal, so an `EXIT_UNCONFIRMED` server is invisible to `list_processes()`/`get_process_info()` |
| PGID failure releases tracking regardless of outcome | Defect confirmed | `http_lifecycle_subprocess_launcher.py` `handle_getpgid_failure()` pops `_http_procs`/`_http_pgids` whatever the outcome |
| Restart over a possibly live process | Defect confirmed | `http_lifecycle.py` `restart()` logs an error on unconfirmed exit then still calls `start()` |
| Router marks every server `STOPPED` | Defect confirmed | `lifecycle_router.py` `shutdown_all()` sets `STOPPED` for every configured server regardless of outcome |
| Invalid transitions mutate state | Defect confirmed | `lifecycle_router.py` `_set_state()` logs a warning and still assigns the new state; `tests/agent/test_agent_factory.py::TestRouterInvalidTransitionLogging` asserts this behavior |
| Silent return from `ensure_ready()`/`restart()` during shutdown | Defect confirmed | `start_http_subprocess()` already raises typed `StartSuppressedError`; `ensure_ready()`/`restart()` return silently, so the contract is inconsistent |

`LifecycleState` has no `STOPPING`/`EXIT_UNCONFIRMED`/`SIGNAL_NOT_DELIVERED`; those exist only as `TerminationOutcome` values in `scripts/agent/http_lifecycle_errors.py`, so the caller-visible state cannot express an unconfirmed outcome.

## Reason for Change
Process-lifecycle correctness: a second live server for the same key (port conflict, duplicate server) or a lost unconfirmed process is hard to detect and recover. The current code releases ownership on paths where exit was never confirmed, and callers cannot distinguish "stopped" from "unconfirmed" through the state machine.

## Implementation Intent
A `ManagedProcessRecord` (dataclass) owns process, pid, pgid, stderr, and lifecycle state per server key. Only confirmed exit releases ownership; every path (startup failure, normal shutdown, PGID failure, restart) follows the same release rule. The state machine gains outcome states fed from `TerminationOutcome`; per-server state replaces the global `STOPPED` sweep. Shutdown-time start, ensure, and restart calls raise typed non-retryable suppression errors. `/mcp status` displays retained records and the last shutdown outcome.

## Requirements
- `REQ-001`: `ManagedProcessRecord` owns process, pid, pgid, stderr, and lifecycle state; a record is deleted only on confirmed exit. The already-implemented startup-failure retention path is locked by regression tests.
- `REQ-002`: Normal shutdown does not remove the process entry before termination is confirmed; ownership is kept for `EXIT_UNCONFIRMED` and `SIGNAL_NOT_DELIVERED`.
- `REQ-003`: A PGID failure keeps process/pgid tracking unless exit is confirmed.
- `REQ-004`: Restart requires confirmed exit of the old process; an unconfirmed exit refuses the restart instead of starting a replacement.
- `REQ-005`: `LifecycleState` gains `STOPPING`, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED`; state is set per server from the termination outcome; `STOPPED` is never set globally without per-server confirmation.
- `REQ-006`: Invalid transitions are rejected without mutating state.
- `REQ-007`: Shutdown-time `ensure_ready()` and `restart()` raise typed non-retryable suppression errors; no shutdown-time lifecycle call returns silent success.
- `REQ-008`: `/mcp status` shows retained unconfirmed processes and populates `last_shutdown_result` with the per-server outcome.
- `REQ-009`: Repeated `shutdown_all()` is safe: a second call re-terminates only retained unconfirmed records and does not re-release already-confirmed ones.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed 2026-11-25; every row `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/lifecycle.py` | State machine definition | Add `STOPPING`, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED` and their transitions in `_VALID_TRANSITIONS` | REQ-005 / AC-3 | `LifecycleState` currently has 5 members; outcome names exist only in `http_lifecycle_errors.py` | `tests/agent/test_lifecycle.py` | Verified |
| `scripts/agent/lifecycle_router.py` | Router state and call contract | `_set_state()` rejects invalid transitions without mutation; `shutdown_all()` sets per-server outcome state; `ensure_ready()`/`restart()` raise typed suppression errors during shutdown | REQ-005, REQ-006, REQ-007 / AC-3, AC-4 | `_set_state()` assigns after warning; `shutdown_all()` sets `STOPPED` for every key; `StartSuppressedError` already exists for start only | `tests/agent/test_agent_factory.py` | Verified |
| `scripts/agent/lifecycle_protocol.py` | Public protocol contract | Document the suppression-error exception in `ensure_ready()`; add per-server outcome access used by status display | REQ-007, REQ-008 | Protocol currently documents only `ServerCooldownError`/`OSError`/`RuntimeError` permitted exceptions | `tests/agent/test_agent_factory.py` | Verified |
| `scripts/agent/http_lifecycle.py` | Ownership contract | Introduce `ManagedProcessRecord`; release only on confirmed exit; `restart()` refuses on unconfirmed exit | REQ-001, REQ-003, REQ-004, REQ-009 / AC-1, AC-2 | `remove_process_entry()` pops before confirmation; `restart()` logs then still calls `start()` | `tests/agent/test_http_lifecycle.py`, `tests/agent/test_http_lifecycle_integration.py` | Verified |
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | Shutdown orchestration | Remove the pre-termination `remove_process_entry()` call; report per-server outcome without releasing ownership | REQ-002, REQ-009 / AC-1, AC-4 | Coordinator calls `remove_process_entry()` before the attempt for every server | `tests/agent/test_http_lifecycle_shutdown_coordinator.py` | Verified |
| `scripts/agent/services/mcp_status.py` | Status display | Show retained unconfirmed records; populate `last_shutdown_result` from the per-server outcome | REQ-008 / AC-1 | `last_shutdown_result` field exists in `services/models.py` but is never populated; status reads only `get_transport_state()` | `tests/agent/commands/test_cmd_mcp.py` | Verified |
| `tests/agent/test_lifecycle.py` | State machine tests | New transitions for the added states; fix `test_getpgid_failure_cleans_up_resources` and `test_shutdown_all_clears_http_procs` assertions that pin the release-on-unconfirmed behavior | REQ-003, REQ-005, REQ-009 | Existing tests assert tracking is released on unconfirmed paths | itself | Verified |
| `tests/agent/test_http_lifecycle.py` | Ownership tests | Fix `test_unconfirmed_exit_is_logged_with_pid_and_entries_are_released` to assert retention; add confirmed-release regression tests | REQ-001, REQ-002, REQ-003 / AC-1 | Existing test asserts entries are released on unconfirmed exit | itself | Verified |
| `tests/agent/test_http_lifecycle_integration.py` | Contract tests | Fix record-release-by-`remove_process_entry` test; add restart-refusal and repeated-shutdown tests | REQ-001, REQ-004, REQ-009 / AC-2 | `test_record_released_by_confirmed_paths` includes `remove_process_entry` as a release path | itself | Verified |
| `tests/agent/test_http_lifecycle_shutdown_coordinator.py` | Coordinator tests | Fix the test that asserts `remove_process_entry` is called on unconfirmed outcome; add per-server outcome tests | REQ-002, REQ-009 / AC-1, AC-4 | `test_unconfirmed_exit_removes_process_entry_but_keeps_other_tracking` asserts the pre-termination removal | itself | Verified |
| `tests/agent/test_agent_factory.py` | Router tests | Fix `TestRouterInvalidTransitionLogging` (asserts mutation); add per-server shutdown-state and shutdown-suppression tests | REQ-005, REQ-006, REQ-007 / AC-3, AC-4 | `test_set_state_logs_warning_and_stores_invalid_transition` asserts the state is stored | itself | Verified |
| `tests/agent/commands/test_cmd_mcp.py` | Status display tests | Assert unconfirmed processes and `last_shutdown_result` appear in the `/mcp status` row | REQ-008 / AC-1 | Status row rendering test exists for the current columns | itself | Verified |
| `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | Lifecycle documentation | Document the ownership rule (release only on confirmed exit) and the updated shutdown behavior | REQ-001, REQ-002, REQ-004 / Documentation Impact | Documents current shutdown behavior; mapped by `docs/00_index.md` to HttpServerLifecycleManager | N/A | Verified |
| `docs/23_agent/agent_02_runtime-architecture.md` | State machine documentation | Update the LifecycleState section with the added states and transitions | REQ-005 / Documentation Impact | LifecycleState section exists at line 139 | N/A | Verified |
| `docs/23_agent/agent_13_reference-api-generated.md` | Generated reference block | Regenerate via `tools/generate_reference_table.py` after the enum and protocol changes | REQ-005, REQ-007 / Documentation Impact | Generated rows for `LifecycleState`, `assert_valid_transition`, `StartSuppressedError` exist | N/A | Verified |

Rules note: every row is a single exact repository-relative path; test and documentation files are their own rows.

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/http_lifecycle_errors.py` | `TerminationOutcome` values and `termination_step_outcome()` are the source of the per-server outcome mapped into the new states; already correct, not modified | REQ-005 |
| `scripts/agent/http_lifecycle_subprocess_launcher.py` | `handle_getpgid_failure()` is the defect site for REQ-003; the fix lands in the ownership contract in `http_lifecycle.py`, so the launcher is read to confirm its release call is routed through the record | REQ-003 |
| `scripts/agent/startup_mcp_starter.py` | Already maps `StartSuppressedError` to `StartupInterrupted`; consumer-scan candidate, not affected | REQ-007 |
| `scripts/agent/startup.py` | Startup rollback consumes `shutdown_all()`'s unconfirmed list; must keep working when entries are retained | REQ-002, REQ-009 |
| `scripts/agent/resource_shutdown_coordinator.py` | Calls `shutdown_all(budget=...)`; caller-visible contract must not break | REQ-009 |
| `scripts/shared/tool_lifecycle.py` | `_PERMITTED_LIFECYCLE_EXCEPTIONS` already permits `RuntimeError`, so `StartSuppressedError` passes without modification; consumer-scan candidate, not affected | REQ-007 |
| `scripts/shared/tool_transport_invoker.py` | `_handle_lifecycle_error()` handles the new typed errors; confirms no retry loop treats them as retryable | REQ-007 |
| `scripts/agent/services/models.py` | `McpProbeResult.last_shutdown_result` field exists and is populated by `mcp_status.py`; the model itself is not modified | REQ-008 |
| `tests/integration/test_mcp_transport_crash.py` | ADR-007-cited consumer of the lifecycle termination path; read to confirm the D05 race test is not affected by entry retention | REQ-002 |
| `tools/generate_reference_table.py` | Regenerates the generated reference doc row set | Documentation Impact |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002, REQ-003, REQ-008): Every unconfirmed process remains owned and visible — a retained record is readable through the process-info interface and shown in `/mcp status` with its outcome.
- AC-2 (REQ-004): Restart cannot create a second live process for the same server: an unconfirmed exit refuses the restart with a typed error.
- AC-3 (REQ-005, REQ-006): Invalid transitions do not mutate state; per-server state reflects the actual outcome (`STOPPING`/`EXIT_UNCONFIRMED`/`SIGNAL_NOT_DELIVERED`/`STOPPED`).
- AC-4 (REQ-007, REQ-009): Shutdown-time lifecycle calls never return silent success; startup, shutdown, restart, and PGID failure follow one release contract; a repeated shutdown is safe.

## Tests
- Per-path exit-unconfirmed tests for startup failure (regression, REQ-001), normal shutdown (REQ-002), PGID failure (REQ-003), restart refusal (REQ-004), repeated shutdown (REQ-009).
- Invalid-transition tests asserting no mutation (REQ-006); shutdown-suppression tests for `ensure_ready()`/`restart()` (REQ-007).
- Status-display test for retained records and `last_shutdown_result` (REQ-008).
- Existing tests that pin the current release-on-unconfirmed behavior must be updated, not deleted (rows in Implementation Target Files).
- Run ruff, mypy, import-lint contracts, and the full test suite (`rules/toolchain.md` sequence).

## Documentation Impact
Yes. Target docs per `docs/00_index.md` task mapping: `22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` (HttpServerLifecycleManager row) for the ownership rule and shutdown behavior, and `23_agent/agent_02_runtime-architecture.md` for the LifecycleState section. `docs/23_agent/agent_13_reference-api-generated.md` is regenerated, not hand-edited. Driven by REQ-001, REQ-002, REQ-004, REQ-005, REQ-007.

## Assumptions
- The startup-failure retention path (star001/mcp001 work) is correct as implemented; this Plan locks it with regression tests rather than re-implementing it.
- `TerminationOutcome` values remain the single source of per-server outcome; the new `LifecycleState` members mirror them by name and are derived, not independently decided.
- No new manual-cleanup command is added (maintainer decision 2026-11-25); operator cleanup remains the logged `kill -TERM -<pgid>` guidance.
- `StartSuppressedError` being a `RuntimeError` subclass keeps it inside `_PERMITTED_LIFECYCLE_EXCEPTIONS`, so `shared/tool_lifecycle.py` needs no change.
- No ADR decision or invariant is changed: ADR-004 and ADR-007 were checked and neither pins the lifecycle state machine directly, so no maintainer approval record is required.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which reported ownership defects survive the archived star001/mcp001 work | — | Resolved by Step 2 verification: only the startup-failure claim is already implemented; the other six are confirmed defects | False |
| UNK-02 | Manual cleanup interface (command name and semantics) | — | Resolved by maintainer decision 2026-11-25: no new command; retained records are surfaced via `/mcp status`, operator action stays the logged pgid kill | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/lifecycle.py` | modify | fan_in 3 (protocol, router, mcp_status); enum growth affects status display | 34 | 2 | not applicable (rsynced) |
| `scripts/agent/lifecycle_router.py` | modify | fan_in 2 (startup, resource_shutdown_coordinator); public call contract changes | 4 | 2 | not applicable (rsynced) |
| `scripts/agent/lifecycle_protocol.py` | modify | fan_in 3; protocol consumers in shared tool executor path | 2 | 4 | not applicable (rsynced) |
| `scripts/agent/http_lifecycle.py` | modify | fan_in 3; shutdown coordinator and launcher call the release contract | 4 | 4 | not applicable (rsynced) |
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | modify | fan_in 1 (http_lifecycle); outcome reporting contract to startup rollback | 1 | 2 | not applicable (rsynced) |
| `scripts/agent/services/mcp_status.py` | modify | consumers: `cmd_mcp` status rendering | 6 | 4 | not applicable (rsynced) |
| `tests/agent/test_lifecycle.py` | modify | pins release-on-unconfirmed behavior | 3 | 2 | not applicable (rsynced) |
| `tests/agent/test_http_lifecycle.py` | modify | pins entry release on unconfirmed exit | 2 | 2 | not applicable (rsynced) |
| `tests/agent/test_http_lifecycle_integration.py` | modify | pins record-release paths | 4 | 2 | not applicable (rsynced) |
| `tests/agent/test_http_lifecycle_shutdown_coordinator.py` | modify | pins pre-termination removal | 1 | 2 | not applicable (rsynced) |
| `tests/agent/test_agent_factory.py` | modify | pins invalid-transition mutation | 8 | 2 | not applicable (rsynced) |
| `tests/agent/commands/test_cmd_mcp.py` | modify | pins status row rendering | 6 | 2 | not applicable (rsynced) |
| `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | modify | documentation only | 3 | 2 | not applicable (docs not synced by deploy.sh) |
| `docs/23_agent/agent_02_runtime-architecture.md` | modify | documentation only | 7 | 2 | not applicable (docs not synced by deploy.sh) |
| `docs/23_agent/agent_13_reference-api-generated.md` | regenerate | generated block | 34 | 2 | not applicable (docs not synced by deploy.sh) |

## Design
Architecture decisions grounded in Step 5 analysis:

- **Ownership record**: `ManagedProcessRecord` dataclass in `scripts/agent/http_lifecycle.py` (module 17,851 B, under the 24576 B gate; growth stays under the gate at current size — predictable fallout check: no split row needed). One record per server key owns process, pid, pgid, stderr, and state; `release_record()` is the only deletion path and is called only after a confirmed outcome.
- **Outcome mapping**: `TerminationOutcome` → `LifecycleState` mapping is derived in the router/coordinator; `http_lifecycle_errors.py` is not modified (reference row).
- **Import contracts**: `uv run lint-imports` reports 6 contracts KEPT with no cycles in `agent` (grimp: 0 cycles); the new mapping does not introduce a new import direction — `agent.lifecycle` keeps fan_out 0.
- **Consumer scan candidates** (`tools/scan_change_consumers.py`, seeds `LifecycleState`, `remove_process_entry`, `assert_valid_transition`, `StartSuppressedError`, `ManagedProcessRecord`, `cleanup_server_key`):
  - `scripts/agent/startup_mcp_starter.py` — reference row, not affected (already maps `StartSuppressedError` to `StartupInterrupted`).
  - `tests/integration/test_mcp_transport_crash.py` — reference row, not affected (D05 asserts the termination race, not entry release).
  - `scripts/shared/tool_lifecycle.py` — reference row, not affected (`RuntimeError` already permitted).
  - `docs/23_agent/agent_02_runtime-architecture.md`, `docs/23_agent/agent_13_reference-api-generated.md` — target rows.
- **Predictable fallout check**:
  - Module size: all target files pass the 24576 B gate at current size; largest target `scripts/agent/lifecycle_router.py` at 15,180 B. No split row.
  - Pinned counts: searched `tests/` for assertions on `LifecycleState` member count or `_VALID_TRANSITIONS` size — no hits; not affected.
  - Tool inventory: no `tools/*.py` added or removed; not affected.
  - Generated blocks: `docs/23_agent/agent_13_reference-api-generated.md` regenerated via `tools/generate_reference_table.py` — target row.
- **Static analysis baseline**: radon max grade A on every target source file; vulture reports no dead code in the release path; bandit flags 3 low-severity/high-confidence items in `http_lifecycle_shutdown_coordinator.py` (B404 subprocess imports x2, B101 assert at line 51) — pre-existing, out of scope, no suppression added. `diff-cover` baseline shows no diff-coverage lines yet; new tests must cover the changed lines.
- **Behavioral change flag**: `_set_state()` mutation rejection and shutdown-time typed errors are intentional behavior changes; the existing tests that assert the old behavior are characterization targets to be updated, not preserved.

## Implementation steps

1. **Phase 1: State machine extension and transition enforcement**
   - [ ] Add `STOPPING`, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED` and transitions (REQ-005; `scripts/agent/lifecycle.py`)
   - [ ] `_set_state()` rejects invalid transitions without mutation (REQ-006; `scripts/agent/lifecycle_router.py`)
   - [ ] Update and extend tests (REQ-005, REQ-006; `tests/agent/test_lifecycle.py`, `tests/agent/test_agent_factory.py`)
2. **Phase 2: Ownership record and shutdown path**
   - [ ] Introduce `ManagedProcessRecord` with confirmed-exit-only release (REQ-001; `scripts/agent/http_lifecycle.py`)
   - [ ] Remove pre-termination entry removal; per-server outcome reporting (REQ-002, REQ-009; `scripts/agent/http_lifecycle_shutdown_coordinator.py`)
   - [ ] Route PGID-failure release through the record (REQ-003; `scripts/agent/http_lifecycle.py`, verified against `scripts/agent/http_lifecycle_subprocess_launcher.py`)
   - [ ] Update and extend tests (REQ-001–REQ-003; `tests/agent/test_http_lifecycle.py`, `tests/agent/test_http_lifecycle_integration.py`, `tests/agent/test_http_lifecycle_shutdown_coordinator.py`)
3. **Phase 3: Restart gating**
   - [ ] Restart refuses on unconfirmed exit with a typed error (REQ-004; `scripts/agent/http_lifecycle.py`)
   - [ ] Restart-refusal and port-conflict tests (REQ-004; `tests/agent/test_http_lifecycle_integration.py`)
4. **Phase 4: Shutdown suppression contract**
   - [ ] `ensure_ready()`/`restart()` raise typed non-retryable suppression errors during shutdown (REQ-007; `scripts/agent/lifecycle_router.py`, `scripts/agent/lifecycle_protocol.py`)
   - [ ] Shutdown-suppression tests (REQ-007; `tests/agent/test_agent_factory.py`)
5. **Phase 5: Status display**
   - [ ] Show retained unconfirmed records; populate `last_shutdown_result` (REQ-008; `scripts/agent/services/mcp_status.py`)
   - [ ] Status-row tests (REQ-008; `tests/agent/commands/test_cmd_mcp.py`)
6. **Phase 6: Documentation and verification**
   - [ ] Update lifecycle docs (Documentation Impact; `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`, `docs/23_agent/agent_02_runtime-architecture.md`)
   - [ ] Regenerate the reference table (Documentation Impact; `docs/23_agent/agent_13_reference-api-generated.md`)
   - [ ] Full validation sequence per `rules/toolchain.md`; deploy.sh check: rsynced scripts, no `cp` line change needed (all requirements)

### Release units
N/A: no release unit — each phase includes its own test updates and passes validation alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/lifecycle.py` | Unit (transition table) | `uv run pytest tests/agent/test_lifecycle.py` | New states and transitions enforced; invalid transition raises without mutation |
| `scripts/agent/lifecycle_router.py` | Unit | `uv run pytest tests/agent/test_agent_factory.py` | Per-server outcome state; typed suppression errors |
| `scripts/agent/http_lifecycle.py` | Unit + integration | `uv run pytest tests/agent/test_http_lifecycle.py tests/agent/test_http_lifecycle_integration.py` | Record released only on confirmed exit; restart refusal |
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py` | No pre-termination removal; outcome reported per server |
| `scripts/agent/services/mcp_status.py` | Unit | `uv run pytest tests/agent/commands/test_cmd_mcp.py` | Unconfirmed process visible with `last_shutdown_result` |
| All changed `scripts/` files | Static | `uv run ruff check scripts/`, `uv run mypy scripts/`, `uv run lint-imports` | Clean; 6 contracts KEPT |
| Whole suite | Regression | `uv run pytest` | Pass; diff coverage on changed lines |
| Generated doc | Drift check | `uv run python tools/generate_reference_table.py` + `rules/tool-gates.md` checkers | Generated rows match source |

## Risks
- **Risk**: Updating tests that pin the old release-on-unconfirmed behavior could mask a regression if the new behavior is wrong. → **Mitigation**: Keep the characterization intent (assert the record survives, not just that the log changed); run the full suite before freeze of each phase.
- **Risk**: Retaining entries after unconfirmed shutdown changes `shutdown_all()`'s observable state for `startup.py` rollback and `resource_shutdown_coordinator.py`. → **Mitigation**: The unconfirmed-list return value is unchanged; reference-file consumers verified in Step 3 are not modified.
- **Risk**: New `LifecycleState` members change `/mcp status` display and `restart_recommended` logic. → **Mitigation**: Status test asserts the new display; `FAILED`-based recommendation is preserved.
- **Risk**: Rejecting invalid transitions without mutation may break callers that rely on the warning-and-assign path. → **Mitigation**: Consumer scan found no caller that depends on mutation; the only asserting consumer is the test being updated.
- **Risk**: Pre-existing bandit findings in the coordinator are in the diff scope. → **Mitigation**: Out of scope per `rules/toolchain.md` diff-scoped gate; no suppression added.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: State machine extension and transition enforcement | Pending | — | — | |
| 2 | Phase 2: Ownership record and shutdown path | Pending | — | — | |
| 3 | Phase 3: Restart gating | Pending | — | — | |
| 4 | Phase 4: Shutdown suppression contract | Pending | — | — | |
| 5 | Phase 5: Status display | Pending | — | — | |
| 6 | Phase 6: Documentation and verification | Pending | — | — | |

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
- **Source issue**: `issues/20261119-145305_cliplc007_mcp-process-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261125-233750
- **Related target files**: `scripts/agent/lifecycle.py`, `scripts/agent/lifecycle_router.py`, `scripts/agent/lifecycle_protocol.py`, `scripts/agent/http_lifecycle.py`, `scripts/agent/http_lifecycle_shutdown_coordinator.py`, `scripts/agent/services/mcp_status.py`, `tests/agent/test_lifecycle.py`, `tests/agent/test_http_lifecycle.py`, `tests/agent/test_http_lifecycle_integration.py`, `tests/agent/test_http_lifecycle_shutdown_coordinator.py`, `tests/agent/test_agent_factory.py`, `tests/agent/commands/test_cmd_mcp.py`, `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`, `docs/23_agent/agent_02_runtime-architecture.md`, `docs/23_agent/agent_13_reference-api-generated.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement | Acceptance Criterion | Target File Row | Test Row | Validation Status |
|---|---|---|---|---|
| REQ-001 | AC-1 | `scripts/agent/http_lifecycle.py` | `tests/agent/test_http_lifecycle.py`, `tests/agent/test_http_lifecycle_integration.py` | Verified |
| REQ-002 | AC-1, AC-4 | `scripts/agent/http_lifecycle_shutdown_coordinator.py` | `tests/agent/test_http_lifecycle_shutdown_coordinator.py` | Verified |
| REQ-003 | AC-1 | `scripts/agent/http_lifecycle.py` | `tests/agent/test_lifecycle.py` | Verified |
| REQ-004 | AC-2 | `scripts/agent/http_lifecycle.py` | `tests/agent/test_http_lifecycle_integration.py` | Verified |
| REQ-005 | AC-3 | `scripts/agent/lifecycle.py`, `scripts/agent/lifecycle_router.py` | `tests/agent/test_lifecycle.py`, `tests/agent/test_agent_factory.py` | Verified |
| REQ-006 | AC-3 | `scripts/agent/lifecycle_router.py` | `tests/agent/test_agent_factory.py` | Verified |
| REQ-007 | AC-4 | `scripts/agent/lifecycle_router.py`, `scripts/agent/lifecycle_protocol.py` | `tests/agent/test_agent_factory.py` | Verified |
| REQ-008 | AC-1 | `scripts/agent/services/mcp_status.py` | `tests/agent/commands/test_cmd_mcp.py` | Verified |
| REQ-009 | AC-4 | `scripts/agent/http_lifecycle.py`, `scripts/agent/http_lifecycle_shutdown_coordinator.py` | `tests/agent/test_http_lifecycle_integration.py`, `tests/agent/test_http_lifecycle_shutdown_coordinator.py` | Verified |
