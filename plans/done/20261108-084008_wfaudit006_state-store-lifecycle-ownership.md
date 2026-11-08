## Goal
Define ownership of the workflow `StateStore`: the orchestrator owns its store and closes it through the existing shutdown coordinators, and the adapter's latent use-after-close path (the `_owns_state_store` flag leaking from a local store to the injected shared store) is removed.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/agent/workflow_engine_adapter.py` — remove the `_owns_state_store` flag and the execute-turn finally close branch (L104, L254-258); `_init_workflow_task`'s local-store path (L290-294, L321-323) keeps its own local close only.
  - `scripts/agent/orchestrator.py` — expose a close path for `self._state_store` (L91) wired to the shutdown coordinators.
  - `scripts/agent/resource_shutdown_coordinator.py` — register the workflow store close with the other shutdown resources (the validation section resolved the issue's `lifecycle.py` target to this file; the `http_lifecycle_shutdown_coordinator.py` candidate was demoted during procedure-pass verification — it terminates MCP server subprocesses only).
  - `scripts/agent/repl.py` — register the orchestrator close hook with the shutdown coordinator after startup (the coordinator is constructed before the orchestrator exists and cannot reach it through `ctx`).
  - Tests: adapter turn sequence after a store-less `init_workflow_task` no longer closes the injected store; orchestrator shutdown closes the store once.
- **Out-of-Scope**:
  - Introducing a connection pool or store-sharing redesign.
  - The direct CLI adapter path (`task-init` without an injected store) gaining its own shutdown wiring beyond the existing local-store finally — it already closes its own local store.
- **Dependencies**: Interacts with `wfaudit015` (facade routing over the same store) — land this plan before 015 so 015's facade methods do not have to consider an ownership-flag close path.

## Background
Verified facts (issue `## Adversarial Validation`): the orchestrator constructs `StateStore()` at `scripts/agent/orchestrator.py:91` with no close/shutdown reference anywhere in `orchestrator.py` (grep). The adapter's `_init_workflow_task` creates a new local `StateStore()` when its `store` argument is None and sets `self._owns_state_store = True` (`scripts/agent/workflow_engine_adapter.py:290-294`); the local store is closed by that method's own finally (L321-323), but the flag survives — the next `execute_turn` finally (L254-258) then closes `self._state_store`, the constructor-injected orchestrator store, before resetting the flag. Production always injects the orchestrator store (`orchestrator.py:141,147`), so the failure trigger is Speculative today, but one direct call arms a use-after-close on the following turn. Shutdown-hook sites exist: `resource_shutdown_coordinator.py`, `http_lifecycle_shutdown_coordinator.py`.

## Problem
Two ownership defects: the orchestrator's store is never closed (connection leak at shutdown), and a flag mechanism can close a store the adapter was injected with — a latent use-after-close on the next turn (failure trigger Speculative, code path real).

## Reason for Change
Ownership must be singular to be auditable: whoever constructs the store closes it. The current mechanism gives close authority to whichever method last flipped a flag, and the process-shutdown path leaks the connection.

## Implementation Intent
Ownership rule: the constructing component closes the store. Orchestrator-owned store -> closed by the orchestrator via the shutdown coordinators. Adapter never closes an injected store; adapter-local stores are closed only by the code that created them. The `_owns_state_store` flag is deleted outright rather than fixed.

## Requirements
- `REQ-001`: `WorkflowEngineAdapter` no longer contains `_owns_state_store`; `execute_turn`'s finally performs no store close.
- `REQ-002`: `_init_workflow_task` keeps closing only the store it created locally (its own finally, L321-323), independent of adapter state.
- `REQ-003`: The orchestrator gains a shutdown path that closes its `StateStore` exactly once, registered through the existing shutdown coordinator(s) used by the hosting service.
- `REQ-004`: A regression test proves the historical failure sequence is gone: call `init_workflow_task` without a store, then `execute_turn` — the injected store is still open and usable after the turn.
- `REQ-005`: Store close is idempotent-safe (double close does not raise) or guarded by a closed-flag in `StateStore` — pick one and test it.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | Delete flag (L104) and finally-close branch (L256-258); keep local-store finally (L321-323) | `REQ-001`/`REQ-002` | Flag mechanics verified in Step 2 | `tests/agent/test_orchestrator.py`, `tests/integration/test_orchestrator_integration.py` | `Verified` |
| `scripts/agent/orchestrator.py` | Modify | Add `close()` closing `self._state_store` (L91) | `REQ-003` | No close reference exists (grep) | `tests/agent/test_orchestrator.py` | `Verified` |
| `scripts/agent/resource_shutdown_coordinator.py` | Modify | Register the workflow store close with the other shutdown resources | `REQ-003` | Coordinator exists as shutdown hook site (verified); `close_resources()` ordering verified | `tests/agent/test_resource_shutdown_coordinator.py` | `Verified` |
| `scripts/agent/repl.py` | Modify | Register the orchestrator close hook after startup (`run()` L116-118; coordinator built at L88 before the orchestrator exists) | `REQ-003` | Wiring-path verification at HEAD `ad48bfa28` | `tests/agent/test_repl.py` | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/startup_component_init.py` | Where the orchestrator is constructed in the service (`Orchestrator(` at L121) — shutdown wiring must cover this lifecycle | `REQ-003` |
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | Confirmed no-change (verification): its `ShutdownCoordinator` terminates managed HTTP MCP server subprocesses only; no service path hosts the Orchestrator outside the REPL (`Orchestrator(` is constructed only at `startup_component_init.py` L121) | `REQ-003` |
| `scripts/agent/workflow/state_store.py` | Confirmed no-change (verification): `close()` (L54-56) delegates to `SQLiteHelper.close` (`scripts/db/helper.py` L232-241), which is already idempotent-safe (early return when `conn` is `None`, `OSError` swallowed) — the `REQ-005` idempotence requirement holds at HEAD; only a regression test is added (see Notes 2026-11-08) | `REQ-005` |
| `scripts/db/helper.py` (`SQLiteHelper.close`) | Underlying close semantics for the idempotence decision | `REQ-005` |

## Acceptance Criteria
- `REQ-001`: `grep -n "_owns_state_store" scripts/` returns nothing.
- `REQ-002`: Existing direct-`task-init` tests (local store closed) stay green.
- `REQ-003`: Shutdown test: orchestrator close -> store's connection closed exactly once; service shutdown test covers the coordinator wiring.
- `REQ-004`: Regression test executes the historical sequence and asserts the injected store survives and serves the next turn.
- `REQ-005`: Double-close test passes with the chosen guard.

## Tests
- Use-after-close regression test (historical sequence).
- Orchestrator shutdown test (close called once, store unusable after).
- Coordinator hook test (registered close hook runs once, after turn-processing/services shutdown steps) and REPL registration test.
- StateStore double-close regression test (pins the existing `SQLiteHelper.close` idempotence; no production code change).

## Documentation Impact
- Checked at HEAD `ad48bfa28`: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` has no StateStore lifecycle/close paragraph (the phrase "One instance per workflow engine lifecycle" exists only in the `StateStore` class docstring, not in the doc), and no existing claim becomes false. Per this plan's "no speculative docs" rule: no doc change. Sibling procedures `135741_03` (wfaudit007) and `141525_02` (wfaudit002) own the edits to this file.

## Assumptions
- Closing the orchestrator's store at process shutdown is safe because recovery/turn processing all precede shutdown (the store is "called once during process initialization" plus per-turn; no background threads use it).
- The failure trigger (flag-armed close) has not fired in production because production always injects the store — consistent with the issue's Speculative marker.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | exact coordinator registration point per service (agent REPL vs http service) | — resolved at procedure pass 2026-11-08 | Resolved: the REPL is the only orchestrator host (`Orchestrator(` constructed only at `startup_component_init.py` L121, reached only via `repl.py`); the http lifecycle coordinator owns MCP server subprocesses only. Registration point: `repl.py` after `startup.run()` | `False` (resolved) |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | turn execution finally path | 11 | N/A | not applicable (rsynced) |
| `scripts/agent/orchestrator.py` | Modify | service construction/shutdown | 8 | N/A | not applicable (rsynced) |
| `scripts/agent/resource_shutdown_coordinator.py` | Modify | shutdown wiring | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/repl.py` | Modify | shutdown hook registration after startup | N/A | N/A | not applicable (rsynced) |

## Design
**Ownership by construction, flag deletion.** The adapter keeps no close authority over injected stores; the only adapter-side close left is the method-local `finally` for a store that method itself created (already correct at L321-323). Deleting the flag (rather than resetting it earlier) removes the entire failure class: there is no state for a later turn to misread.

**Shutdown wiring.** The coordinators already own ordered resource shutdown; adding the workflow store as a registered resource keeps close ordering visible (store closed after turn-processing resources). The orchestrator exposes a narrow `close()` that the wiring calls.

**Close idempotence.** `REQ-005` takes the "idempotent-safe" side of its choice: `SQLiteHelper.close` (L232-241) already no-ops on a second close (early return when `conn` is `None`, `OSError` swallowed), so no closed-flag is added to `StateStore` — a double-close regression test pins the existing guarantee (see Notes 2026-11-08; the original closed-flag design is superseded).

## Implementation steps
1. **Phase 1: Adapter flag removal (`REQ-001`, `REQ-002`, `REQ-004`).** Delete flag/finally branch; regression test for the historical sequence.
2. **Phase 2: Orchestrator close + coordinator wiring (`REQ-003`).** `close()` method, coordinator registrations per hosting path, shutdown tests.
3. **Phase 3: Idempotence test (`REQ-005`).** Double-close regression test on `StateStore` (no production code change — `SQLiteHelper.close` is already idempotent-safe); docs verified no-change.

### Release units
**Unit**: wfaudit006-full | **Phases**: 1, 2, 3 | **Reason**: ownership transfer is one contract — removing the old authority without adding the new one would leak the connection worse than today.

## Validation plan
- `uv run pytest tests/agent/ -q` after each phase; full `uv run pytest tests/ -q` before completion.
- Regression test must fail on HEAD (injected store closed on second turn) and pass after.
- Service restart smoke test after deploy: clean shutdown, no "cannot operate on a closed database" errors in `/opt/llm/logs/agent.log`.
- Lint/type gates per `rules/toolchain.md`; docs checkers if docs edited.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Shutdown close ordering closes the store while a late turn is unwinding | Low | Medium | Coordinators shut down turn-processing resources before the store; tests pin ordering |
| Direct adapter users (scripts/CLI) relied on the flag-close to release their store | Low | Low | `_init_workflow_task`'s local finally still closes locally-created stores; grep finds no other close reliance |
| REPL path hosts the store differently than the http path (`UNK-01`) | Resolved | Low | Verified 2026-11-08: the REPL is the only orchestrator host; the http lifecycle coordinator owns MCP server subprocesses only |

## Execution Status
### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Phase 1: Adapter flag removal (REQ-001, REQ-002, REQ-004) | Completed | 20261109-120000 | 20261109-120000 | Procedure 20261108-155554_01 authored; code not yet implemented |
| 2 | Phase 2: Orchestrator close + coordinator wiring (REQ-003) | Completed | 20261109-120000 | 20261109-120000 | Procedures 20261108-155554_02/_03/_04 authored; code not yet implemented |
| 3 | Phase 3: Idempotence regression test (REQ-005) | Completed | 20261109-120000 | 20261109-120000 | Covered by test test_double_close_is_noop in procedure 20261108-155554_02; docs verified no-change |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| `implementations/20261108-155554_01_scripts_agent_workflow_engine_adapter.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261108-155554_02_scripts_agent_orchestrator.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-155554_03_scripts_agent_resource_shutdown_coordinator.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-155554_04_scripts_agent_repl.py.md` | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203219_wfaudit006_state-store-lifecycle-ownership.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084008
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem (ownership flag) | `scripts/agent/workflow_engine_adapter.py` | flag absent | grep + tests |
| `REQ-002` | Issue constraint (local path safe) | same | local close preserved | direct-init tests |
| `REQ-003` | Issue Required Changes (close path) | orchestrator + coordinators | closed once at shutdown | shutdown tests |
| `REQ-004` | Issue Problem (use-after-close) | adapter tests | injected store survives | regression test |
| `REQ-005` | Plan Design (idempotence) | `state_store.py` | double-close no-op | guard test |

## Notes
- Source verified against HEAD `926dbc109`; the issue's "flag becomes True only via direct task-init" claim was sharpened during validation (the flag survives the local close and arms the next turn) — see the issue's `## Adversarial Validation`.
- Sequence: this plan before `wfaudit015` (facade methods should not wrap an ownership-flag close path).
- 2026-11-08 procedure-pass re-verification (HEAD `ad48bfa28`):
  - `REQ-005` demotion: `SQLiteHelper.close` (`scripts/db/helper.py` L232-241) is already idempotent-safe (early return when `conn` is `None`; `OSError` swallowed with a warning), so the `StateStore` closed-flag row was moved to Reference Files as confirmed no-change; the original Design closed-flag choice is superseded and `REQ-005` is satisfied by a regression test only.
  - `scripts/agent/http_lifecycle_shutdown_coordinator.py` demotion: its `ShutdownCoordinator` terminates managed HTTP MCP server subprocesses only; `Orchestrator(` is constructed only at `startup_component_init.py` L121 (REPL path), so the conditional row required no change and moved to Reference Files (`UNK-01` resolved).
  - `scripts/agent/repl.py` added as a Modify row: the shutdown wiring cannot live in the coordinator alone — `ResourceShutdownCoordinator` is constructed at `repl.py` L88, before the orchestrator exists, and cannot reach it through `AgentContext`; the registration call must be made in `run()` after `startup.run()` returns the orchestrator.
  - Docs check: no StateStore lifecycle/close paragraph exists in `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`; per the plan's no-speculative-docs rule the Documentation Impact resolves to no-change.
  - Sibling overlap reconciliation (design references, not implemented code): `state_store.py` — `134201_01` (wfaudit001) and `135741_01` (wfaudit007) edit `recover_stale_attempts`/`_classify_running_attempts`/CRUD regions, disjoint from this plan's former `close()` region (now no-change); `orchestrator.py` — `134201_03` (wfaudit001) edits the L92 initialization region only, disjoint from the new `close()` method; `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` and the `tool_call_state` doc area — owned by `135741_03` and `141525_02`; this plan generates no doc procedure, so no collision. Line numbers in this plan and its procedures refer to HEAD `ad48bfa28` and shift if a sibling procedure lands first in the same file.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-155554 -->