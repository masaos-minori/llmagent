# Plan: Unify MCP process ownership, lifecycle state, shutdown, and restart safety

## Goal
- Make one managed-process ownership contract govern every HTTP MCP subprocess path (startup failure, normal shutdown, process-group failure, restart, shutdown suppression): a process stays owned and visible until its exit is confirmed, restart cannot create a second live process for the same key, and no lifecycle call during shutdown returns silent success.

## Priority
High

## Scope
- **In-Scope**:
  - A `ManagedProcessRecord` that owns process, pid, pgid, stderr log, lifecycle state, and last termination outcome; records release only on confirmed exit.
  - Removal of pre-termination process-entry deletion in `shutdown_all`; per-server outcome drives cleanup and state.
  - PGID-failure tracking retention unless exit is confirmed.
  - Restart requires confirmed old-process exit; typed refusal otherwise.
  - New `LifecycleState` states `STOPPING`, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED`; per-server post-shutdown state; invalid transitions rejected without mutation.
  - Typed non-retryable suppression errors for `ensure_ready()` and `restart()` during shutdown.
  - Unconfirmed processes visible in the process snapshot and `/mcp status`; repeated shutdown re-terminates retained records; manual cleanup stays the logged `kill -TERM -<pgid>` against a retained, visible record.
  - Tests-first coverage of every confirmed defect; documentation and generated-artifact refresh; deployment hand-off.
- **Out-of-Scope**: Launch-spec and credential work (cliplc006); health semantics (cliplc008); redaction/stderr diagnostics (cliplc009); `ProcessTerminator` escalation semantics (already correct, unchanged); any change to an ADR decision or invariant (none identified; see Risks).
- **Dependencies**: builds on the bounded-shutdown machine (cliplc004, budget API already consumed by the lifecycle modules) and on the safe-launch work (cliplc006, still being implemented); blocks cliplc008 and cliplc009.
  - **Depends on**: plans/done/20261125-111909_cliplc006_mcp-launch-spec-credentials.md | phase all | this Plan's `scripts/agent/http_lifecycle_subprocess_launcher.py` and `tests/agent/test_http_lifecycle.py` rows overlap cliplc006's pending procedures (its Execution Status rows 1-4 are `In Progress`, row 5 `Pending`); land cliplc006 first so the launcher and its tests are not rewritten twice.

## Background
Source issue: consolidated CLI REPL and MCP lifecycle backlog (memo-issue.md, Issue 6). Related archived work: `issues/done/20261021-220228_star001_clarify-mcp-subprocess-termination-ownership-and-remove-unused-spawned-subprocess-list-return.md` and `issues/done/20261016-092822_mcp001_double_startup_failure_crashes_mcp_loop.md`; both were re-verified against current source (see Design → Issue Verification). The startup-failure path already follows the confirmed-exit contract; the shutdown, PGID-failure, restart, and router-state paths do not.

## Problem
Process ownership and lifecycle state depend on the code path: `shutdown_all` deletes the process entry before termination, a PGID failure releases tracking even when the exit is unconfirmed, `restart()` can start a replacement while the old process may still be live (port conflict, duplicate server), the router marks every server `STOPPED` regardless of outcome, invalid transitions still mutate state, and `ensure_ready()`/`restart()` return silently during shutdown. A lost or duplicated process is hard to detect and recover.

## Reason for Change
Process-lifecycle correctness: a second live server for the same key, or an untracked live process, is invisible to `/mcp status` and to repeated shutdown. The confirmed-exit vocabulary (`TerminationOutcome`) already exists; the ownership and state layers must follow it.

## Implementation Intent
One record type per managed process, held by the lifecycle manager for every path; release only on `TerminationOutcome.confirmed`. Lifecycle state becomes per-server and outcome-driven, with three new states and non-mutating transition rejection. Shutdown-time lifecycle calls raise typed suppression errors. Observability (snapshot, `/mcp status`) exposes retained unconfirmed records so manual cleanup names a visible process.

## Requirements
- `REQ-001`: A `ManagedProcessRecord` owns process, pid, pgid, stderr log, lifecycle state, and last termination outcome for each HTTP subprocess server, replacing the parallel `_http_procs` / `_http_pgids` / `_failed_start_procs` dictionaries (`scripts/agent/http_lifecycle.py:162-165,174-175,399-400,413`).
- `REQ-002`: A record is released only when the exit is confirmed (`TerminationOutcome.confirmed`, `scripts/agent/http_lifecycle_errors.py:58-61`); `EXIT_UNCONFIRMED` and `SIGNAL_NOT_DELIVERED` retain ownership on every path.
- `REQ-003`: `shutdown_all` does not remove the process entry before termination (`http_lifecycle_shutdown_coordinator.py:210-211`); per-server outcome drives cleanup and state, and unconfirmed servers stay in the registry and the returned list.
- `REQ-004`: A `getpgid()` failure keeps process tracking unless the termination is confirmed (`http_lifecycle_subprocess_launcher.py:165-166` releases unconditionally today); the retained record names the pid for manual cleanup.
- `REQ-005`: `restart()` requires a confirmed old-process exit; an unconfirmed exit raises a typed refusal, retains the record, and never starts a second process for the same key (`http_lifecycle.py:399-414`).
- `REQ-006`: `LifecycleState` gains `STOPPING`, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED` (`scripts/agent/lifecycle.py:26-30`); post-shutdown state is per-server from the termination outcome; `STOPPED` is never set globally without per-server confirmation (`lifecycle_router.py:281-282`).
- `REQ-007`: An invalid lifecycle transition fails without mutating state (`lifecycle_router.py:187-196` mutates today after logging).
- `REQ-008`: Shutdown-time `ensure_ready()` and `restart()` raise typed non-retryable suppression errors instead of returning silently (`lifecycle_router.py:240-244,314-318`); `start_http_subprocess` already raises `StartSuppressedError` (`:297-300`) and keeps it.
- `REQ-009`: Unconfirmed processes remain visible: retained records appear in `list_processes()`/`get_process_info()` snapshots and in `/mcp status` (`scripts/agent/services/mcp_status.py:146-151`).
- `REQ-010`: Repeated `shutdown_all` re-terminates retained unconfirmed records; manual cleanup remains the logged `kill -TERM -<pgid>` (`http_lifecycle_shutdown_coordinator.py:138-146`, `http_lifecycle.py:268-276`) against a retained, visible record.
- `REQ-011`: Each confirmed ownership defect is pinned by a test written before the implementation change (Issue AI Implementation Instruction).
- `REQ-012`: `docs/*.md` lifecycle documents and the generated reference artifacts reflect the state machine, ownership rules, and result codes.

## Implementation Target Files
**Freeze status**: Frozen (issue-to-plan Step 8's Implementation Target Files
Validation passed — see `rules/workflow-lifecycle.md` Implementation Target Files
Validation (Plan Freeze)).

Amended 2026-11-25 (fallout): added tests/agent/test_startup_mcp_lifecycle.py — REQ-001 removes _http_procs/_http_pgids/_failed_start_procs; this test drives a real HttpServerLifecycleManager and reads them directly
Amended 2026-11-25 (fallout, corrected 2026-11-26): tests/agent/test_http_lifecycle_warning.py — the _http_pgids patch at :97 is inert (the terminator resolves pgid via os.getpgid), so the row removes it and drives the killpg path through os.getpgid instead of retargeting it to the record registry
Amended 2026-11-25 (fallout): extended the tests/agent/test_lifecycle.py row — REQ-001 removes _http_procs/_http_pgids, which this test sets and asserts on real managers at :145,207,216,475-476,505-506,540-568,872,898-942,952,969
Amended 2026-11-25 (fallout): extended the tests/agent/test_http_lifecycle_integration.py row — REQ-001 removes the three tracking dicts, which this test sets and asserts on real managers at 114 sites

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/lifecycle.py | Modify: add `STOPPING`, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED` and extend `_VALID_TRANSITIONS` | The state vocabulary has no outcome states | REQ-006; AC-5 | 5 states only at `:26-30`; table at `:33-46` (checked in Step 3) | `tests/agent/test_lifecycle.py` | Verified |
| scripts/agent/http_lifecycle_process_record.py | Create (new file): `ManagedProcessRecord` owning process, pid, pgid, stderr log, state, last outcome | Ownership is split across three dicts that diverge per path | REQ-001, REQ-002; AC-5 | `_http_procs`/`_http_pgids`/`_failed_start_procs` popped independently at `http_lifecycle.py:162-165,174-175,399-400,413` (checked in Step 3) | `tests/agent/test_http_lifecycle.py` | Verified |
| scripts/agent/http_lifecycle.py | Modify: record registry replaces the three dicts; `restart()` refuses on unconfirmed exit; startup-failure retention re-expressed on the record | Restart can start a replacement over a live process; tracking is path-dependent | REQ-001, REQ-002, REQ-005, REQ-010; AC-1, AC-2 | `restart()` pops at `:399`, logs-only on unconfirmed `:406-412`, starts at `:414`; `_build_snapshot` returns None once the entry is popped `:191-193` (checked in Step 3) | `tests/agent/test_http_lifecycle.py`, `tests/agent/test_http_lifecycle_integration.py` | Verified |
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Modify: no pre-termination entry removal; per-server outcome settles cleanup and state; retained records re-terminated on repeated shutdown | Entry is deleted before termination; unconfirmed servers lose process visibility | REQ-002, REQ-003, REQ-010; AC-1, AC-5 | `remove_process_entry` called at `:210-211`; only confirmed exit calls `cleanup_server_key` `:134-147` (checked in Step 3) | `tests/agent/test_http_lifecycle_shutdown_coordinator.py` | Verified |
| scripts/agent/http_lifecycle_subprocess_launcher.py | Modify: retain process/pgid tracking after a `getpgid()` failure unless exit is confirmed; name the pid in the manual-cleanup log | Tracking is released regardless of termination outcome | REQ-002, REQ-004; AC-1 | `handle_getpgid_failure` pops `_http_procs`/`_http_pgids` at `:165-166`; cleanup hint reads an unset pgid at `:154` (checked in Step 3) | `tests/agent/test_http_lifecycle.py` | Verified |
| scripts/agent/lifecycle_router.py | Modify: per-server post-shutdown state from outcomes; `_set_state` rejects invalid transitions without mutation; typed suppression errors from `ensure_ready()`/`restart()` | Global `STOPPED`, mutating invalid transitions, silent returns | REQ-006, REQ-007, REQ-008; AC-3, AC-4 | `:281-282` marks every configured server `STOPPED`; `:187-196` sets state after the warning; `:240-244,314-318` return silently (checked in Step 3) | `tests/agent/test_lifecycle.py`, `tests/agent/test_agent_factory.py` | Verified |
| scripts/agent/lifecycle_protocol.py | Modify: contract docstrings for suppression errors, per-server outcome states, and record retention semantics | Protocol is the shared contract callers code against | REQ-008; AC-4 | `:35-88` documents `ensure_ready`/`restart`/`shutdown_all` without suppression or outcome-state semantics (checked in Step 3) | `tests/agent/test_lifecycle.py` | Verified |
| scripts/agent/http_lifecycle_errors.py | Modify: add the typed error family — `ShutdownSuppressedError(RuntimeError)` base with `EnsureSuppressedError`/`RestartSuppressedError`, and `RestartBlockedError` | Typed non-retryable refusals need a shared vocabulary module | REQ-005, REQ-008; AC-2, AC-4 | Module already owns `TerminationOutcome`/`HttpStartupError` (`:19-61`); `StartSuppressedError` stays in `lifecycle_router.py:45` for caller compatibility (checked in Step 3) | `tests/agent/test_lifecycle.py` | Verified |
| scripts/agent/services/models.py | Modify: `ProcessInfoSnapshot` gains a defaulted `termination_outcome` field | Snapshots cannot report an unconfirmed retained process | REQ-009; AC-1 | `ProcessInfoSnapshot` fields at `:38-47` carry no outcome (checked in Step 3) | `tests/agent/test_http_lifecycle_integration.py` | Verified |
| scripts/agent/services/mcp_status.py | Modify: map the new lifecycle states and retained snapshots into the status row (availability, restart recommendation) | `/mcp status` must show unconfirmed processes | REQ-009; AC-1 | `:146-151` reads `get_transport_state` and only treats `FAILED` as restart-recommended (checked in Step 3) | `tests/agent/commands/test_cmd_mcp.py` | Verified |
| tests/agent/test_lifecycle.py | Modify: new-state transition table tests, invalid-transition no-mutation tests, shutdown-suppression typed-error tests; retarget the private-dict assertions to the record registry | Pins REQ-006/007/008; also asserts the three tracking dicts on real managers | REQ-001, REQ-006, REQ-007, REQ-008, REQ-011; AC-1, AC-3, AC-4 | Imports `LifecycleState`, `assert_valid_transition`, and the router at `:29-30`; pins invalid pairs at `:685-696`; sets or asserts `_http_procs`/`_http_pgids` on real managers at `:145,207,216,475-476,505-506,540-545,568,600,612,635,872,898-942,952,969` (checked in Step 3a) | — | Verified |
| tests/agent/test_http_lifecycle.py | Modify: restart-refusal and port-conflict-prevention tests; PGID-failure retention tests; record-ownership tests | Pins REQ-001/004/005 defects | REQ-001, REQ-004, REQ-005, REQ-011; AC-1, AC-2 | Already imports the manager and launcher modules at `:14-19` (checked in Step 3) | — | Verified |
| tests/agent/test_http_lifecycle_shutdown_coordinator.py | Modify: no-pre-termination-removal, per-server outcome, and repeated-shutdown tests | Pins REQ-003/010 | REQ-003, REQ-010, REQ-011; AC-1, AC-5 | Imports the coordinator at `:7-8` (checked in Step 3) | — | Verified |
| tests/agent/test_http_lifecycle_integration.py | Modify: end-to-end unconfirmed-visibility and repeated-shutdown tests; retarget the private-dict sets and assertions to the record registry | Pins REQ-009/010 across real managers; also the largest consumer of the three tracking dicts | REQ-001, REQ-009, REQ-010, REQ-011; AC-1 | Exercises shutdown paths and the lifecycle logger at `:795,1371-1410`; sets or asserts `_http_procs`/`_http_pgids`/`_failed_start_procs` on real managers at 114 sites including `:83,192-207,327-328,430,450-451,486-487,540-557,1379-1380,1478-1695` (checked in Step 3a) | — | Verified |
| tests/agent/commands/test_cmd_mcp.py | Modify: `/mcp status` display of unconfirmed processes | Pins REQ-009 at the command surface | REQ-009, REQ-011; AC-1 | Command surface test for MCP status output (checked in Step 3) | — | Verified |
| tests/agent/test_agent_factory.py | Modify: `TestRouterInvalidTransitionLogging` asserts the current mutate-after-warning behavior and must be updated to assert no mutation | The characterization test pins the defect REQ-007 fixes | REQ-007, REQ-011; AC-3 | `test_set_state_logs_warning_and_stores_invalid_transition` at `:743-751` asserts `router._states["srv"]` is stored after an invalid transition (verified 2026-11-25) | — | Verified |
| docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md | Modify: lifecycle state machine and ownership rules | Docs must describe the new states and contract | REQ-012; AC-6 | Named by `docs/00_index.md:164` for `HttpServerLifecycleManager / http_lifecycle.py`; already describes `LifecycleState` (checked in Step 3) | — | Verified |
| docs/23_agent/agent_02_runtime-architecture.md | Modify: lifecycle ownership contract in the runtime architecture | Same mapping as above | REQ-012; AC-6 | Named by `docs/00_index.md:164`; already describes `LifecycleState` (checked in Step 3) | — | Verified |
| docs/23_agent/agent_13_reference-api-generated.md | Regenerate (never hand-edit) | New top-level public symbols in `scripts/agent/` | REQ-012; AC-6 | Guarded block generated from `registry/manifests/agent_api.yaml` (`tools/generate_reference_table.py:476`) (checked in Step 3) | — | Verified |
| docs/23_agent/agent_14_reference-api-subpackages-generated.md | Regenerate (never hand-edit) | `ProcessInfoSnapshot` and `services` symbol changes | REQ-012; AC-6 | Guarded block already lists `ProcessInfoSnapshot` at `:196` (checked in Step 3) | — | Verified |
| registry/manifests/agent_api.yaml | Regenerate (never hand-edit) | Manifest is the source of both reference blocks | REQ-012; AC-6 | Manifest lists `scripts/agent/http_lifecycle*.py` symbols (checked in Step 3) | — | Verified |
| tests/agent/test_startup_mcp_lifecycle.py | Modify: drive and assert the record registry instead of the three tracking dicts | REQ-001 removes _http_procs/_http_pgids/_failed_start_procs; this test drives a real HttpServerLifecycleManager and reads them directly | REQ-001 / AC-5 | tests/agent/test_startup_mcp_lifecycle.py:306-307,327,353-354 set and assert mgr._http_procs, mgr._http_pgids and mgr._failed_start_procs on a real HttpServerLifecycleManager (checked in plan-to-implementation-procedure Step 3a) | — | Verified |
| tests/agent/test_http_lifecycle_warning.py | Modify: remove the inert _http_pgids patch and drive the killpg-failure path through os.getpgid | REQ-001 removes _http_pgids, so patch.object at :97 raises AttributeError; the patch is inert today because the terminator resolves pgid through os.getpgid and never reads the dict | REQ-001, REQ-010 / AC-1, AC-5 | tests/agent/test_http_lifecycle_warning.py:97 patches mgr._http_pgids on a real HttpServerLifecycleManager built at :89; `ProcessTerminator._resolve_pgid` (`scripts/agent/http_lifecycle_process_terminator.py:57-73`) resolves through `os.getpgid(proc.pid)` and the module reads no manager dict (checked in plan-to-implementation-procedure Step 3a) | — | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/http_lifecycle_process_terminator.py | Confirmed-exit escalation semantics must not be weakened (Issue AI Instruction); verified unchanged this cycle — it already returns `TerminationOutcome` and clamps waits to the budget | REQ-002; scripts/agent/http_lifecycle.py |
| scripts/agent/http_lifecycle_health_checker.py | Startup-failure termination path `_terminate_for_startup_failure` (`:63-85`) delegates to the manager's terminator; the record refactor must keep its no-masking contract | REQ-002; scripts/agent/http_lifecycle.py |
| scripts/agent/startup_mcp_starter.py | Imports `StartSuppressedError` (`:23`) and handles it (`:188`); confirms the suppression-error family needs no caller change | REQ-008; scripts/agent/lifecycle_router.py |
| scripts/shared/tool_transport_invoker.py | Calls `ensure_ready` (`:359`) and reports `RuntimeError`-family failures (`:282`); confirms typed suppression errors are handled without a shared-layer change | REQ-008; scripts/agent/lifecycle_router.py |
| scripts/agent/http_lifecycle_stderr_log_manager.py | Stderr-log tracking becomes a record field; its `forget`/`read_tail` API is the record's stderr owner | REQ-001; scripts/agent/http_lifecycle_process_record.py |
| scripts/agent/shutdown_budget.py | Budget clamping and interrupt semantics the coordinator and terminator already consume; repeated shutdown must keep honoring them | REQ-003, REQ-010; scripts/agent/http_lifecycle_shutdown_coordinator.py |
| tests/agent/test_http_lifecycle_process_terminator.py | Pins the confirmed-exit semantics this Plan must preserve (`:133-187`) | REQ-002; scripts/agent/http_lifecycle_process_terminator.py |
| issues/done/20261021-220228_star001_clarify-mcp-subprocess-termination-ownership-and-remove-unused-spawned-subprocess-list-return.md | Archived work the Issue requires re-verifying against; source of the already-fixed startup-failure retention | REQ-002; Design → Issue Verification |
| issues/done/20261016-092822_mcp001_double_startup_failure_crashes_mcp_loop.md | Archived work the Issue requires re-verifying against | REQ-002; Design → Issue Verification |

## Acceptance Criteria
- AC-1 (REQ-002, REQ-004, REQ-009): Every unconfirmed process remains owned and visible — retained in the record registry after startup failure, shutdown, and PGID failure, and named by `list_processes()` and `/mcp status`.
- AC-2 (REQ-005): Restart cannot create a second live process for the same server — an unconfirmed old exit raises `RestartBlockedError` and no new process starts (port-conflict prevention test green).
- AC-3 (REQ-007): Invalid transitions do not mutate state — the state is unchanged and the rejection is logged.
- AC-4 (REQ-008): Shutdown-time lifecycle calls never return silent success — `start`, `ensure_ready`, and `restart` raise typed suppression errors after shutdown begins.
- AC-5 (REQ-001, REQ-003, REQ-006): Startup, shutdown, restart, and PGID failure follow one contract — one record type, no pre-termination entry deletion, per-server outcome states, no global `STOPPED`.
- AC-6 (REQ-012): `uv run python tools/generate_reference_table.py --check` passes and the lifecycle docs describe the new state machine and ownership rules.

## Tests
- Defect-pinning tests written first (REQ-011): restart over a live process (tests/agent/test_http_lifecycle.py), PGID-failure tracking release (tests/agent/test_http_lifecycle.py), pre-termination entry removal and global `STOPPED` (tests/agent/test_http_lifecycle_shutdown_coordinator.py, tests/agent/test_lifecycle.py), invalid-transition mutation (tests/agent/test_lifecycle.py, tests/agent/test_agent_factory.py), silent shutdown-time return (tests/agent/test_lifecycle.py), unconfirmed invisibility (tests/agent/test_http_lifecycle_integration.py, tests/agent/commands/test_cmd_mcp.py).
- Exit-unconfirmed behavior on every lifecycle path (REQ-002); restart refusal and port-conflict prevention (REQ-005); repeated shutdown and manual cleanup (REQ-010); invalid transition and shutdown-suppression tests (REQ-007, REQ-008).
- Preserve the confirmed-exit semantics pinned by tests/agent/test_http_lifecycle_process_terminator.py (REQ-002).
- Run ruff, mypy, and the full test suite; diff-cover at the `rules/toolchain.md` Completion-checklist threshold (REQ-011).

## Documentation Impact
Yes. Per `docs/00_index.md`'s "Document References by Task" row `HttpServerLifecycleManager / http_lifecycle.py`, the lifecycle state machine, ownership rules, and result codes are documented in `22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` and `23_agent/agent_02_runtime-architecture.md` (target rows). The generated reference artifacts (`docs/23_agent/agent_13_reference-api-generated.md`, `docs/23_agent/agent_14_reference-api-subpackages-generated.md`, `registry/manifests/agent_api.yaml`) must be regenerated because new public symbols appear in `scripts/agent/` (REQ-012).

## Assumptions
- Suppression errors stay `RuntimeError` subclasses, so existing callers handle them unchanged: `scripts/shared/tool_transport_invoker.py:282` already reports `ensure_ready` failures and `scripts/agent/startup_mcp_starter.py:188` already catches `StartSuppressedError` (verified in Step 3).
- `StartSuppressedError` remains defined in `lifecycle_router.py:45` (imported by `startup_mcp_starter.py:23`); the new error family lives in `http_lifecycle_errors.py`. Moving the existing class would touch a non-lifecycle consumer, against the Issue's "keep the change in the lifecycle modules" instruction.
- `ProcessInfoSnapshot` gains a defaulted field, which is compatible with its 19 importers (grimp graph, Step 5).
- The manual-cleanup interface is the existing logged `kill -TERM -<pgid>` against a retained, visible record; no new CLI command is added (maintainer decision 2026-11-25, confirmed).
- No ADR decision or invariant changes: ADR-007 INV-07/INV-08 and the ADR-004 retry-policy citations describe behavior this Plan preserves (checked in Step 3). If implementation reaches ADR-pinned behavior, a maintainer approval record is required in the same change (governance_01, governance_05) and must not be simulated.
- `ProcessTerminator` needs no modification: its confirmed-exit semantics are already correct and pinned by tests; the Issue lists it as a target area, but current evidence makes it a reference row.
- Overlap judgment (`tools/check_plan_target_overlaps.py`, run after the freeze): no other active Frozen Plan in `plans/` lists these files; the overlap with the archived cliplc006 Plan (launcher, `test_http_lifecycle.py`) is a sequencing dependency recorded as the `Depends on` bullet, not a conflict.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Resolved in this cycle: which reported ownership defects still exist after the archived star001 and mcp001 work | None: every claim re-checked against current source (Design → Issue Verification) | Startup-failure retention is already fixed; shutdown, PGID-failure, restart, router-state, and silent-return defects are confirmed and carried as REQ-002..REQ-008 | False |
| UNK-02 | Resolved in this cycle: the manual cleanup interface (command name and semantics) | None: current code already logs `kill -TERM -<pgid>` with the retained pgid (`http_lifecycle_shutdown_coordinator.py:138-146`, `http_lifecycle.py:268-276`) | Formalize the existing semantics: retained record + `/mcp status` visibility + logged pgid kill; no new command (maintainer decision 2026-11-25) | False |
| UNK-03 | cliplc004's Plan still has its Phase 1 row `In Progress` (its R1 release unit is recorded complete) | None for this Plan's needs: the budget API it builds on is already in source (`budget` kwargs on `shutdown_all`/`terminate_with_timeout`, coordinator clamping) | No wait required; if cliplc004's remaining rows change the budget API, re-verify before Phase 3 (`plans/done/20261124-095950_cliplc004_bounded-shutdown-machine.md`) | False |
| UNK-04 | cliplc006's Plan rows 1-4 are `In Progress` and row 5 `Pending`; its pending procedures target `scripts/agent/http_lifecycle_subprocess_launcher.py` and `tests/agent/test_http_lifecycle.py`, both rows of this Plan | None: rows read from `plans/done/20261125-111909_cliplc006_mcp-launch-spec-credentials.md` Execution Status | Sequencing dependency recorded as the `Depends on` bullet; `plan-to-implementation-procedure` Step 2 re-runs the overlap check against `implementations/` before generating this Plan's procedures | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/lifecycle.py | Modify | Medium (imported by lifecycle_protocol, lifecycle_router, services.mcp_status — grimp) | 1 | 2 | not applicable (rsynced) |
| scripts/agent/http_lifecycle_process_record.py | Create | Low (new module, imported by the lifecycle cluster only) | N/A (new file) | N/A (new file) | not applicable (rsynced) |
| scripts/agent/http_lifecycle.py | Modify | Medium (imported by lifecycle_router; owns the internal cluster — grimp) | 4 | 2 | not applicable (rsynced) |
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Modify | Low (imported by http_lifecycle only — grimp) | 1 | 2 | not applicable (rsynced) |
| scripts/agent/http_lifecycle_subprocess_launcher.py | Modify | Low (imported by http_lifecycle only — grimp) | 1 | 2 | not applicable (rsynced) |
| scripts/agent/lifecycle_router.py | Modify | Medium (imported by factory, startup_mcp_starter — grimp) | 4 | 2 | not applicable (rsynced) |
| scripts/agent/lifecycle_protocol.py | Modify | Medium (imported by context, factory, lifecycle_router — grimp) | 2 | 2 | not applicable (rsynced) |
| scripts/agent/http_lifecycle_errors.py | Modify | Medium (imported by the whole lifecycle cluster and protocol — grimp) | 2 | 2 | not applicable (rsynced) |
| scripts/agent/services/models.py | Modify | Medium (19 importers — grimp; defaulted field is additive) | 9 | 2 | not applicable (rsynced) |
| scripts/agent/services/mcp_status.py | Modify | Medium (imported by commands.cmd_mcp — grimp) | 6 | 2 | not applicable (rsynced) |
| tests/agent/test_lifecycle.py | Modify | Low | 3 | 2 | not applicable (rsynced) |
| tests/agent/test_http_lifecycle.py | Modify | Low | 2 | 2 | not applicable (rsynced) |
| tests/agent/test_http_lifecycle_shutdown_coordinator.py | Modify | Low | 1 | 2 | not applicable (rsynced) |
| tests/agent/test_http_lifecycle_integration.py | Modify | Low | 4 | 2 | not applicable (rsynced) |
| tests/agent/commands/test_cmd_mcp.py | Modify | Low | 6 | 2 | not applicable (rsynced) |
| tests/agent/test_agent_factory.py | Modify | Low | 8 | 2 | not applicable (rsynced) |
| docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md | Modify | Low | 3 | 2 | not applicable (rsynced) |
| docs/23_agent/agent_02_runtime-architecture.md | Modify | Low | 7 | 2 | not applicable (rsynced) |
| docs/23_agent/agent_13_reference-api-generated.md | Regenerate | Low | 33 | 2 | not applicable (rsynced) |
| docs/23_agent/agent_14_reference-api-subpackages-generated.md | Regenerate | Low | 14 | 2 | not applicable (rsynced) |
| registry/manifests/agent_api.yaml | Regenerate | Low | 38 | 2 | not applicable (rsynced) |
| tests/agent/test_startup_mcp_lifecycle.py` | Modify | Not assessed (amendment 2026-11-25) | N/A | N/A | Not assessed (amendment 2026-11-25) |
| tests/agent/test_http_lifecycle_warning.py` | Modify | Not assessed (amendment 2026-11-25) | N/A | N/A | Not assessed (amendment 2026-11-25) |

## Design
- **Path classification**: Path B (six-plus source modules, new states and a new dataclass, protocol contract changes, cross-layer consumers, tests and docs). Loaded `skills/issue-to-plan/workflow-path-b.md`; all four analyses ran once (architecture via grimp, dependency graphing via grimp chains/pydeps v3.0.6, historical via git churn and author counts, operational via pip-audit).
- **Plan consolidation** (2026-11-25): two plans were generated for this issue in parallel sessions (`20261125-232847` and `20261125-233750`). Consolidated into this document; the duplicate was deleted. The consolidation adds the `tests/agent/test_agent_factory.py` target row — `TestRouterInvalidTransitionLogging` (`:743-751`) is the existing characterization test that asserts the mutate-after-warning behavior REQ-007 fixes, and it was missing from the other plan's table. Both plans' Step 2 verifications agree on every claim; the manual-cleanup decision (no new command, maintainer 2026-11-25) is recorded in Assumptions.

- **Issue Verification** (each claim re-checked against current source; Step 2):

| Issue claim | Verdict | Evidence |
|---|---|---|
| Startup failure keeps an unconfirmed process untracked | Already fixed (star001/mcp001 work) | `_raise_startup_failure_unconfirmed` retains process/pgid/stderr and records `_failed_start_procs` (`http_lifecycle.py:254-281`); `start()` re-terminates the recorded process (`:332-341,363-394`) |
| Normal shutdown removes the entry before termination | Confirmed, partially mitigated | Coordinator pops via `remove_process_entry` at `:210-211`; only a confirmed exit clears pgid/stderr (`:134-147`), but the process entry is gone, so `_build_snapshot` returns None (`http_lifecycle.py:191-193`) and the live process is invisible to snapshots and `/mcp status` |
| PGID failure releases tracking even when exit is unconfirmed | Confirmed | `handle_getpgid_failure` pops `_http_procs` and `_http_pgids` regardless of outcome (`http_lifecycle_subprocess_launcher.py:165-166`); the manual-cleanup log prints `pgid=None` because the failed `getpgid` never populated the dict (`:114,154`) |
| Restart may start over a live process | Confirmed | `restart()` pops the entry at `:399`, logs only on unconfirmed exit (`:406-412`), then calls `start()` (`:414`) — a second live process for the same key is possible |
| Router marks every server `STOPPED` | Confirmed | `shutdown_all` loops over all `server_configs` and sets `STOPPED` regardless of the returned unconfirmed outcomes (`lifecycle_router.py:281-282`) |
| Invalid transitions mutate state | Confirmed | `_set_state` logs a warning and then assigns the new state (`lifecycle_router.py:187-196`) |
| `ensure_ready()`/`restart()` return silently during shutdown | Confirmed, partially fixed | `ensure_ready` returns after a debug log (`:240-244`); `restart` returns after a warning (`:314-318`); `start_http_subprocess` already raises `StartSuppressedError` (`:297-300`) |
| States `STOPPING`/`EXIT_UNCONFIRMED`/`SIGNAL_NOT_DELIVERED` missing | Confirmed | `LifecycleState` has 5 members (`lifecycle.py:26-30`); the outcome vocabulary already exists in `TerminationOutcome` (`http_lifecycle_errors.py:46-56`) — only the transport-state layer lacks it |
| Target-file correction | Corrected | The PGID-failure defect lives in `http_lifecycle_subprocess_launcher.py` (extracted from `http_lifecycle.py`), which the Issue's target list predates; `http_lifecycle_process_terminator.py` needs no change and became a reference row |

- **Record ownership**: `ManagedProcessRecord` is a small mutable dataclass in a new `scripts/agent/http_lifecycle_process_record.py` (agent layer; imports stdlib plus `agent.http_lifecycle_errors` only, consistent with the import-layer contract). `HttpServerLifecycleManager` holds one `_records: dict[str, ManagedProcessRecord]`; the three parallel dicts disappear. Alternatives rejected: a fourth dict alongside the existing three (the defect is exactly dict divergence per path), and a frozen record (outcome and state update in place during termination). Keeping the record in a new module also holds `http_lifecycle.py` (17851 B today) clear of the 24576 B module-size gate as the contract grows.
- **State vocabulary**: add `STOPPING`, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED` to `LifecycleState` and extend `_VALID_TRANSITIONS` so `RUNNING -> STOPPING`, `STOPPING -> {STOPPED, EXIT_UNCONFIRMED, SIGNAL_NOT_DELIVERED}`, and the unconfirmed states can return to `STARTING` (re-termination) or `STOPPED` (confirmed on a later pass). The pairs pinned invalid by `tests/agent/test_lifecycle.py:685-696` (`FAILED -> RUNNING`, `STOPPED -> RUNNING`) stay invalid.
- **Transition enforcement**: `_set_state` rejects an invalid transition by logging and leaving the state unchanged (no raise). Alternative rejected: raising — it would propagate into `shutdown_all`'s per-server loop and turn a reporting step into a failure path. The rejection is observable (log + unchanged state), which is what AC-3 tests.
- **Suppression and refusal errors**: `ShutdownSuppressedError(RuntimeError)` base with `EnsureSuppressedError` and `RestartSuppressedError`, plus `RestartBlockedError`, live in `http_lifecycle_errors.py`, the module that already owns the lifecycle error vocabulary. `StartSuppressedError` stays in `lifecycle_router.py` because `startup_mcp_starter.py:23` imports it from there; moving it would touch a non-lifecycle consumer. All are `RuntimeError` subclasses, so `tool_transport_invoker.py:282` and `startup_mcp_starter.py:188` handle them with no change.
- **Restart contract**: `http_lifecycle.py::restart()` terminates the old process, and on an unconfirmed outcome retains the record, sets the server state to `EXIT_UNCONFIRMED`, and raises `RestartBlockedError` without starting a replacement — the port-conflict prevention of AC-2. The router maps the refusal to state and cooldown handling unchanged.
- **Shutdown contract**: the coordinator no longer pops entries before termination; each record stays in the registry until its outcome is confirmed, then is cleaned up. Per-server state after shutdown is `STOPPED` (confirmed), `EXIT_UNCONFIRMED`, or `SIGNAL_NOT_DELIVERED`. A repeated `shutdown_all` sees the retained records and re-terminates them, mirroring the existing `_reterminate_recorded_failed_start` pattern (`http_lifecycle.py:363-394`). Budget clamping and SIGINT forwarding (`OD-05`, REQ-010/011 of cliplc004) are untouched.
- **Manual cleanup**: formalize the existing semantics — a retained record is named by `list_processes()`/`/mcp status` with its pid, pgid, and last outcome, and the termination log carries `kill -TERM -<pgid>`. No new command; a maintainer who wants a REPL cleanup command files it separately (falsifiable assumption).
- **Visibility**: `ProcessInfoSnapshot` gains `termination_outcome: str | None = None` (defaulted, so the 19 importers are unaffected); `mcp_status.py` maps the new states and retained snapshots into the status row (`:146-151` today treats only `FAILED` as restart-recommended).
- **Consumer scan** (`tools/scan_change_consumers.py`, seeds `LifecycleState`, `remove_process_entry`, `TerminationOutcome`, `ProcessInfoSnapshot`, `get_transport_state`): `LifecycleState`/`get_transport_state` → `scripts/agent/services/mcp_status.py:146,150` is affected (target row); `remove_process_entry` → only `http_lifecycle_shutdown_coordinator.py:211` (both already targets); `TerminationOutcome` → `http_lifecycle_health_checker.py:68,85` not affected: the outcome vocabulary is unchanged; `ProcessInfoSnapshot` → `docs/23_agent/agent_14_reference-api-subpackages-generated.md:196` (regenerate row) and `services/models.py` (target). Testmon state: absent (no `.testmondata`), so the report lists candidates only.
- **Predictable fallout**: module size — every target is under the 24576 B gate today (measured: largest target `http_lifecycle.py` 17851 B); the record lives in a new module, so no split row is needed. Pinned counts — no test pins the `LifecycleState` member count; `tests/agent/test_lifecycle.py:685-717` pins invalid pairs (design constraint above) and `tests/agent/commands/test_cmd_mcp.py:242` pins a stopped-state status row (target row to keep green). Tool inventory — no tool added or removed: not affected. Generated blocks — `scripts/agent/` is a generated-reference domain (ADR-015 INV-01): the three regenerate rows cover it (`generate_reference_table.py --check` gates drift). Amended 2026-11-25 (fallout): REQ-001 removes the three tracking dicts, which `tests/agent/test_lifecycle.py` (43 sites), `tests/agent/test_http_lifecycle_integration.py` (114 sites), `tests/agent/test_startup_mcp_lifecycle.py` (5 sites) and `tests/agent/test_http_lifecycle_warning.py` (the inert `_http_pgids` patch at `:97`) read directly on real managers; each is a target row.
- **Validation quality baseline** (Step 5): `radon cc` — all targets A except pre-existing C blocks: `ShutdownCoordinator.shutdown_all` (C), `ProcessTerminator.terminate_with_timeout` (C), two `McpStatusService` methods (C); the refactor must not raise any of them (record extraction shrinks `shutdown_all`). `vulture scripts/ --min-confidence 80` — two 100%-confidence findings inside a target (`http_lifecycle_shutdown_coordinator.py:57,79` unused `signum` — signal-handler signature, false positive) plus unrelated repo findings. `bandit -r scripts/ -c pyproject.toml` — 48 Low / 0 Medium / 0 High, all pre-existing (`assert_used` class). `pip-audit` — pre-existing dev-dependency advisories (virtualenv, wcmatch, werkzeug, …); this Plan adds no dependencies. diff-cover — `N/A` in this document-only phase (no diff exists); recorded at implementation with the `rules/toolchain.md` §7 sequence and the Completion-checklist threshold (90).
- **Architecture** (grimp, Step 5): `agent.lifecycle` is imported by `lifecycle_protocol`, `lifecycle_router`, `services.mcp_status`; `lifecycle_router` by `factory` and `startup_mcp_starter`; `services.models` by 19 modules; `http_lifecycle` ↔ `http_lifecycle_shutdown_coordinator` import each other directly (the coordinator side is type-only). No new import cycle is introduced: the record module is a leaf imported by the lifecycle cluster.
- **Historical** (Step 5): churn over 30 days and authors over 90 days are in `Affected areas` (git log; `git-fame` unavailable → Bus Factor from author counts). The lifecycle cluster was last restructured by the cliplc004 R6 termination work (2026-11-25), which this Plan extends rather than reworks.
- **Operational dependencies** (Step 5): pip-audit findings are pre-existing dev-dependency advisories unrelated to the lifecycle modules; no new package is required.

## Implementation steps
1. **Phase 1: Tests first (REQ-011)**
   - [ ] Add defect-pinning tests expecting failure: restart over a live process and PGID-failure tracking release (tests/agent/test_http_lifecycle.py); pre-termination removal and repeated shutdown (tests/agent/test_http_lifecycle_shutdown_coordinator.py); global `STOPPED`, invalid-transition mutation, silent shutdown-time return (tests/agent/test_lifecycle.py, tests/agent/test_agent_factory.py); unconfirmed visibility end to end (tests/agent/test_http_lifecycle_integration.py); `/mcp status` unconfirmed display (tests/agent/commands/test_cmd_mcp.py)
2. **Phase 2: State vocabulary and transition enforcement (REQ-006, REQ-007)**
   - [ ] Add `STOPPING`, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED` and extend the transition table (scripts/agent/lifecycle.py)
   - [ ] `_set_state` rejects invalid transitions without mutation (scripts/agent/lifecycle_router.py)
3. **Phase 3: Record ownership across shutdown, PGID failure, and repeated shutdown (REQ-001, REQ-002, REQ-003, REQ-004, REQ-010)**
   - [ ] `ManagedProcessRecord` (scripts/agent/http_lifecycle_process_record.py)
   - [ ] Record registry replaces the three dicts; startup-failure retention re-expressed on the record (scripts/agent/http_lifecycle.py)
   - [ ] No pre-termination entry removal; per-server outcome settles cleanup and state; retained records re-terminated on repeated shutdown (scripts/agent/http_lifecycle_shutdown_coordinator.py)
   - [ ] PGID-failure retention unless exit is confirmed; cleanup log names the pid (scripts/agent/http_lifecycle_subprocess_launcher.py)
   - [ ] Per-server outcome states replace the global `STOPPED` loop (scripts/agent/lifecycle_router.py)
   - [ ] Retarget the private-dict assertions to the record registry (REQ-001; tests/agent/test_lifecycle.py) — amendment 2026-11-25
   - [ ] Retarget the private-dict sets and assertions to the record registry (REQ-001; tests/agent/test_http_lifecycle_integration.py) — amendment 2026-11-25
   - [ ] Drive and assert the record registry instead of the three tracking dicts (REQ-001; tests/agent/test_startup_mcp_lifecycle.py) — amendment 2026-11-25
   - [ ] Remove the inert _http_pgids patch and drive the killpg-failure path through os.getpgid (REQ-001, REQ-010; tests/agent/test_http_lifecycle_warning.py) — amendment 2026-11-25, corrected 2026-11-26
4. **Phase 4: Restart confirmation and shutdown suppression (REQ-005, REQ-008)**
   - [ ] Typed error family `ShutdownSuppressedError`/`EnsureSuppressedError`/`RestartSuppressedError`/`RestartBlockedError` (scripts/agent/http_lifecycle_errors.py)
   - [ ] `restart()` refuses on unconfirmed old exit and retains the record (scripts/agent/http_lifecycle.py)
   - [ ] `ensure_ready()`/`restart()` raise suppression errors during shutdown (scripts/agent/lifecycle_router.py)
   - [ ] Protocol contract updated (scripts/agent/lifecycle_protocol.py)
5. **Phase 5: Observability (REQ-009)**
   - [ ] `ProcessInfoSnapshot.termination_outcome` defaulted field (scripts/agent/services/models.py)
   - [ ] New-state mapping and retained-snapshot display in the status row (scripts/agent/services/mcp_status.py)
6. **Phase 6: Documentation and generated artifacts (REQ-012)**
   - [ ] Update docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md and docs/23_agent/agent_02_runtime-architecture.md; regenerate docs/23_agent/agent_13_reference-api-generated.md, docs/23_agent/agent_14_reference-api-subpackages-generated.md, and registry/manifests/agent_api.yaml
7. **Phase 7: Deployment & Verification**
   - [ ] Run `uv run ruff format`, `uv run ruff check`, `uv run mypy`, the full `uv run pytest`, and the `rules/toolchain.md` §7 diff-cover sequence at the Completion-checklist threshold; hand off to `skills/deploy/SKILL.md` after the change is committed and pushed (deploying is the user's decision) (REQ-011; scripts/agent/http_lifecycle.py, scripts/agent/lifecycle_router.py)

### Release units
**Unit**: R3-ownership | **Phases**: 3, 4 | **Reason**: the record registry and the restart/suppression contract rewrite the same shutdown and restart call paths and their tests; neither phase passes the lifecycle suite alone, and the tests-first Phase 1 is expected to fail until both land.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/lifecycle.py + lifecycle_router.py | Unit: transition table, rejection without mutation, per-server shutdown states, suppression errors | `uv run pytest tests/agent/test_lifecycle.py` | New-state and no-mutation tests green; pinned invalid pairs still rejected (REQ-006, REQ-007, REQ-008) |
| scripts/agent/http_lifecycle.py + http_lifecycle_process_record.py + subprocess_launcher.py | Unit: record ownership, restart refusal, PGID-failure retention | `uv run pytest tests/agent/test_http_lifecycle.py` | No second live process; unconfirmed records retained (REQ-001, REQ-004, REQ-005) |
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Unit: no pre-termination removal, per-server outcomes, repeated shutdown | `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py` | Entries live until confirmed; repeated shutdown re-terminates (REQ-003, REQ-010) |
| scripts/agent/services/models.py + mcp_status.py + commands surface | Integration: retained snapshot visible in status output | `uv run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/commands/test_cmd_mcp.py` | Unconfirmed process named in `/mcp status` (REQ-009) |
| Confirmed-exit semantics (unchanged) | Regression | `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py` | Unchanged green (REQ-002) |
| Generated artifacts | Gate | `uv run python tools/generate_reference_table.py --check` | No drift after regeneration (REQ-012) |
| Whole suite and coverage | Full | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`; `uv run coverage xml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | Green; new lines at or above the threshold (REQ-011) |

## Risks
- **Risk**: the record refactor touches the same launcher and test files cliplc006's pending procedures modify → **Mitigation**: `Depends on` bullet sequences this Plan after cliplc006; `plan-to-implementation-procedure` Step 2 re-runs the overlap check against `implementations/` before generating procedures (UNK-04).
- **Risk**: changing `ensure_ready`/`restart` from silent return to raising could break callers that never expected an exception → **Mitigation**: errors are `RuntimeError` subclasses and the two known callers already handle that family (`tool_transport_invoker.py:282`, `startup_mcp_starter.py:188`, verified in Step 3); impact-radius grep over `ensure_ready`/`restart` callers precedes Phase 4.
- **Risk**: new states leak into `/mcp status` and command output tests (`test_cmd_mcp.py:242`) → **Mitigation**: states only appear after Phase 3/4 sets them; Phase 1 pins the display, Phase 5 implements it; the cmd_mcp test row keeps the old rows green.
- **Risk**: `ProcessInfoSnapshot` has 19 importers (grimp) → **Mitigation**: additive defaulted field only; no field removed or renamed; full-suite run in Phase 7.
- **Risk**: pre-existing C-complexity in `ShutdownCoordinator.shutdown_all` grows during the ownership rewrite → **Mitigation**: record extraction moves per-server settling into the record module; `radon cc` re-run at Phase 7 must show no block worse than C.
- **Risk**: the change could reach behavior pinned by an ADR (ADR-007 INV-07/INV-08, ADR-004 retry policy) → **Mitigation**: no ADR decision or invariant change is planned (verified in Step 3); if implementation finds one, stop and obtain a maintainer approval record in the same change (governance_01, governance_05) — never simulate it.
- **Risk**: repeated shutdown re-terminating retained records could clash with the cliplc004 budget semantics → **Mitigation**: re-termination runs inside the same budget clamping as first termination (coordinator already honors `budget.remaining()` and the interrupt event); tests pin that a spent budget still signals and reports, never waits.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first pinning every confirmed defect | In Progress | — | — | Expected to fail until Phases 3-4 land (release unit R3-ownership) |
| 2 | Phase 2: state vocabulary and transition enforcement | In Progress | — | — | scripts/agent/lifecycle.py, scripts/agent/lifecycle_router.py |
| 3 | Phase 3: record ownership across shutdown, PGID failure, repeated shutdown | In Progress | — | — | scripts/agent/http_lifecycle_process_record.py, scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_shutdown_coordinator.py, scripts/agent/http_lifecycle_subprocess_launcher.py, scripts/agent/lifecycle_router.py |
| 4 | Phase 4: restart confirmation and shutdown suppression | In Progress | — | — | scripts/agent/http_lifecycle_errors.py, scripts/agent/http_lifecycle.py, scripts/agent/lifecycle_router.py, scripts/agent/lifecycle_protocol.py |
| 5 | Phase 5: observability (snapshot field, /mcp status mapping) | In Progress | — | — | scripts/agent/services/models.py, scripts/agent/services/mcp_status.py |
| 6 | Phase 6: documentation and generated artifacts | In Progress | — | — | docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md, docs/23_agent/agent_02_runtime-architecture.md, docs/23_agent/agent_13_reference-api-generated.md, docs/23_agent/agent_14_reference-api-subpackages-generated.md, registry/manifests/agent_api.yaml |
| 7 | Phase 7: Deployment & Verification | Pending | — | — | Hand-off to `skills/deploy/SKILL.md` after commit+push; deploying is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |
| 20261125-235436_01_scripts_agent_lifecycle.py.md | 2 | Procedure | Pending | — | — |
| 20261125-235436_02_scripts_agent_http_lifecycle_process_record.py.md | 3 | Procedure | Pending | — | — |
| 20261125-235436_03_scripts_agent_http_lifecycle.py.md | 3, 4 | Procedure | Pending | — | — |
| 20261125-235436_04_scripts_agent_http_lifecycle_shutdown_coordinator.py.md | 3 | Procedure | Pending | — | — |
| 20261125-235436_05_scripts_agent_http_lifecycle_subprocess_launcher.py.md | 3 | Procedure | Pending | — | — |
| 20261125-235436_06_scripts_agent_lifecycle_router.py.md | 2, 3, 4 | Procedure | Pending | — | — |
| 20261125-235436_07_scripts_agent_lifecycle_protocol.py.md | 4 | Procedure | Pending | — | — |
| 20261125-235436_08_scripts_agent_http_lifecycle_errors.py.md | 4 | Procedure | Pending | — | — |
| 20261125-235436_09_scripts_agent_services_models.py.md | 5 | Procedure | Pending | — | — |
| 20261125-235436_10_scripts_agent_services_mcp_status.py.md | 5 | Procedure | Pending | — | — |
| 20261125-235436_11_tests_agent_test_lifecycle.py.md | 1 | Procedure | Pending | — | — |
| 20261125-235436_12_tests_agent_test_http_lifecycle.py.md | 1 | Procedure | Pending | — | — |
| 20261125-235436_14_tests_agent_test_http_lifecycle_integration.py.md | 1 | Procedure | Pending | — | — |
| 20261125-235436_19_docs_22_mcp_mcp_03_04_tool-call-tracing-and-lifecycle.md.md | 6 | Procedure | Pending | — | — |
| 20261125-235436_20_docs_23_agent_agent_02_runtime-architecture.md.md | 6 | Procedure | Pending | — | — |
| 20261125-235436_21_docs_23_agent_agent_13_reference-api-generated.md.md | 6 | Procedure | Pending | — | — |
| 20261125-235436_22_docs_23_agent_agent_14_reference-api-subpackages-generated.md.md | 6 | Procedure | Pending | — | — |
| 20261125-235436_23_registry_manifests_agent_api.yaml.md | 6 | Procedure | Pending | — | — |
| 20261126-000128_22_tests_agent_test_startup_mcp_lifecycle.py.md | 3 | Procedure | Pending | — | — |
| 20261126-000128_23_tests_agent_test_http_lifecycle_warning.py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261125-232847
- **Related target files**: scripts/agent/lifecycle.py, scripts/agent/http_lifecycle_process_record.py, scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_shutdown_coordinator.py, scripts/agent/http_lifecycle_subprocess_launcher.py, scripts/agent/lifecycle_router.py, scripts/agent/lifecycle_protocol.py, scripts/agent/http_lifecycle_errors.py, scripts/agent/services/models.py, scripts/agent/services/mcp_status.py, tests/agent/test_lifecycle.py, tests/agent/test_http_lifecycle.py, tests/agent/test_http_lifecycle_shutdown_coordinator.py, tests/agent/test_http_lifecycle_integration.py, tests/agent/commands/test_cmd_mcp.py, tests/agent/test_agent_factory.py, docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md, docs/23_agent/agent_02_runtime-architecture.md, docs/23_agent/agent_13_reference-api-generated.md, docs/23_agent/agent_14_reference-api-subpackages-generated.md, registry/manifests/agent_api.yaml

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (ManagedProcessRecord); split-dict evidence `http_lifecycle.py:162-165,174-175,399-400,413` | scripts/agent/http_lifecycle_process_record.py, scripts/agent/http_lifecycle.py | Phase 3 | AC-5 | tests/agent/test_http_lifecycle.py | Confirmed by repository evidence |
| REQ-002 | Required Changes (release only on confirmed exit); `http_lifecycle_errors.py:58-61` | scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_shutdown_coordinator.py, scripts/agent/http_lifecycle_subprocess_launcher.py | Phase 3 | AC-1 | tests/agent/test_http_lifecycle_shutdown_coordinator.py, tests/agent/test_http_lifecycle_process_terminator.py (regression) | Confirmed by repository evidence |
| REQ-003 | Required Changes (remove pre-termination deletion); coordinator `:210-211` | scripts/agent/http_lifecycle_shutdown_coordinator.py | Phase 3 | AC-1, AC-5 | tests/agent/test_http_lifecycle_shutdown_coordinator.py | Confirmed by repository evidence |
| REQ-004 | Required Changes (keep records after PGID failure); launcher `:165-166` | scripts/agent/http_lifecycle_subprocess_launcher.py | Phase 3 | AC-1 | tests/agent/test_http_lifecycle.py | Confirmed by repository evidence |
| REQ-005 | Required Changes (restart requires confirmed exit); `http_lifecycle.py:399-414` | scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_errors.py | Phase 4 | AC-2 | tests/agent/test_http_lifecycle.py | Confirmed by repository evidence |
| REQ-006 | Required Changes (new states, no global STOPPED); `lifecycle.py:26-30`, `lifecycle_router.py:281-282` | scripts/agent/lifecycle.py, scripts/agent/lifecycle_router.py | Phase 2, Phase 3 | AC-5 | tests/agent/test_lifecycle.py | Confirmed by repository evidence |
| REQ-007 | Required Changes (reject invalid transitions without mutation); `lifecycle_router.py:187-196` | scripts/agent/lifecycle_router.py | Phase 2 | AC-3 | tests/agent/test_lifecycle.py, tests/agent/test_agent_factory.py | Confirmed by repository evidence |
| REQ-008 | Required Changes (typed suppression errors); `lifecycle_router.py:240-244,314-318` | scripts/agent/lifecycle_router.py, scripts/agent/lifecycle_protocol.py, scripts/agent/http_lifecycle_errors.py | Phase 4 | AC-4 | tests/agent/test_lifecycle.py | Confirmed by repository evidence |
| REQ-009 | Required Changes (show unconfirmed processes in `/mcp status`); `mcp_status.py:146-151`, `http_lifecycle.py:191-193` | scripts/agent/services/models.py, scripts/agent/services/mcp_status.py | Phase 5 | AC-1 | tests/agent/test_http_lifecycle_integration.py, tests/agent/commands/test_cmd_mcp.py | Derived from confirmed evidence |
| REQ-010 | Required Changes (repeated shutdown, manual cleanup); coordinator `:138-146`, `http_lifecycle.py:268-276,363-394` | scripts/agent/http_lifecycle_shutdown_coordinator.py, scripts/agent/http_lifecycle.py | Phase 3 | AC-1 | tests/agent/test_http_lifecycle_shutdown_coordinator.py, tests/agent/test_http_lifecycle_integration.py | Derived from confirmed evidence |
| REQ-011 | AI Implementation Instruction (re-verify each defect with a test first) | tests/agent/test_lifecycle.py, tests/agent/test_http_lifecycle.py, tests/agent/test_http_lifecycle_shutdown_coordinator.py, tests/agent/test_http_lifecycle_integration.py, tests/agent/commands/test_cmd_mcp.py, tests/agent/test_agent_factory.py | Phase 1 | AC-1..AC-5 | Phase 1 defect-pinning tests | Confirmed by repository evidence |
| REQ-012 | Documentation Impact (state machine, ownership rules, result codes) | docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md, docs/23_agent/agent_02_runtime-architecture.md, docs/23_agent/agent_13_reference-api-generated.md, docs/23_agent/agent_14_reference-api-subpackages-generated.md, registry/manifests/agent_api.yaml | Phase 6 | AC-6 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-25: REQ-001 removes _http_procs/_http_pgids/_failed_start_procs; this test drives a real HttpServerLifecycleManager and reads them directly | tests/agent/test_startup_mcp_lifecycle.py | Phase 3 | AC-5 | — | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-25: REQ-001 removes _http_procs/_http_pgids, which this test sets and asserts on real managers | tests/agent/test_lifecycle.py | Phase 3 | AC-1 | tests/agent/test_lifecycle.py | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-25: REQ-001 removes the three tracking dicts, which this test sets and asserts on real managers at 114 sites | tests/agent/test_http_lifecycle_integration.py | Phase 3 | AC-1 | tests/agent/test_http_lifecycle_integration.py | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-25, corrected 2026-11-26: the inert _http_pgids patch at :97 breaks once the dict is removed; the terminator resolves pgid through os.getpgid | tests/agent/test_http_lifecycle_warning.py | Phase 3 | AC-1, AC-5 | tests/agent/test_http_lifecycle_warning.py | Confirmed by repository evidence |
