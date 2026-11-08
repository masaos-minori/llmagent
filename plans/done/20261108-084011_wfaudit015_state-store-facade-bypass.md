## Goal
Route the three raw-connection call-outs (engine stage-start guard, engine artifact recorder, orchestrator recovery) through `StateStore` facade methods so the persistence boundary stays auditable and `get_connection()` loses its production users.

## Priority
Low

## Scope
- **In-Scope**:
  - `scripts/agent/workflow/state_store.py` — add facade methods `begin_stage_if_new(...)` and `record_artifact(...)` wrapping the ops functions with `self._db`; make `recover_stale_attempts()` take no db argument (internal `self._db`), keeping the explicit-arg form only where callers genuinely own a different transaction.
  - `scripts/agent/workflow/workflow_engine.py` — replace `self._store.get_connection()` call sites (L313-314, L373-374) with facade calls.
  - `scripts/agent/orchestrator.py` — `recover_stale_attempts(self._state_store.get_connection())` (L92) becomes `self._state_store.recover_stale_attempts()`.
  - Tests: retarget the 31 `recover_stale_attempts(...)` test call sites (`test_state_store.py` 12, `test_workflow_state_store.py` 11, `test_stale_recovery_lease.py` 8) to no-arg calls; new routing assertion tests in `tests/agent/workflow/test_workflow_engine.py` and `tests/agent/test_orchestrator.py`; existing transaction-semantics regression (begin_immediate still spans check-then-insert; duplicate-event skip tests) stays green unchanged.
  - `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` — the Startup Recovery sentence "is called with the store's connection" (L165) becomes a no-argument call. `agent_04_03` confirmed no-change (verification): no facade/connection boundary row exists in it (grep for `get_connection` across `docs/` returns zero matches).
- **Out-of-Scope**:
  - Deleting `get_connection()` itself — keep it (documented escape hatch) unless the grep shows zero remaining users, in which case deletion is a follow-up recorded as `UNK-01`.
  - Changing the ops functions' signatures (`begin_stage_if_new`, `record_artifact` keep their `(db, ...)` shape).
  - The ownership/close contract (planned as `wfaudit006`, landed first).
- **Dependencies**: After `wfaudit006` (no ownership-flag close path to consider in new facade methods) and after `wfaudit001`/`wfaudit007` (their extensions to `recover_stale_attempts` are folded in, not reworked). After `wfaudit009` (`find_stale_running_attempts` deletion simplifies the facade surface being cleaned), coordinated with `wfaudit008` (`tests/agent/test_orchestrator.py` edits land first). Note: `wfaudit001`'s landed orchestrator procedure adds a second production `get_connection()` use (its `purge_finished_workflow_events` call) that this plan does not convert; recorded in `Notes`/`UNK-01`.

## Background
`StateStore` documents itself as the CRUD facade (`scripts/agent/workflow/state_store.py:46`); `get_connection()` (L58-65) is explicitly "use this only when necessary". Production uses it exactly three times: engine `begin_stage_if_new(self._store.get_connection(), ...)` (`workflow_engine.py:313-314`), engine `record_artifact(self._store.get_connection(), ...)` (L373-374), and orchestrator `self._state_store.recover_stale_attempts(self._state_store.get_connection())` (`orchestrator.py:92`) — the last one feeds the store's own connection back into its own method. These sites are the sanctioned output of `dee33ce7b fix(wfreview004)` (private-attribute access cleanup); this plan is the next step its own precedent anticipates. Verified in the issue's `## Adversarial Validation`.

## Problem
Callers pass the store's private connection back into the store's own operation functions, so the persistence boundary is no longer a single auditable surface: a reader of `StateStore` cannot enumerate all workflow.sqlite writes.

## Reason for Change
The facade exists to make writes enumerable; three raw-connection call-outs defeat it, and the orchestrator self-feed is the clearest signal the API shape (db-argument methods) is wrong for these call sites.

## Implementation Intent
Add thin facade methods that call the same ops functions with `self._db`; convert the db-argument facade methods that always receive the store's own connection to no-argument methods. Transaction semantics are unchanged — the wrappers pass `self._db` straight through, so `begin_immediate` and the recovery transaction behave identically.

## Requirements
- `REQ-001`: `StateStore.begin_stage_if_new(...)` and `StateStore.record_artifact(...)` exist and delegate to the ops functions with `self._db`, preserving return semantics (`AttemptRecord | None`).
- `REQ-002`: `recover_stale_attempts()` takes no required db argument and uses `self._db`.
- `REQ-003`: Zero `get_connection()` calls remain from this plan's three sites (engine L314/L374 and orchestrator L92 converted). The only remaining production user is the `purge_finished_workflow_events` call `wfaudit001`'s orchestrator procedure adds (its design passes the connection explicitly); converting it is out of this plan's scope and carried in `UNK-01`.
- `REQ-004`: Behavior is byte-identical: same SQL, same transaction boundaries (begin_immediate still wraps check-then-insert; recovery compare-and-swap unchanged).
- `REQ-005`: Tests pin the routing (engine/orchestrator no longer fetch raw connections) and the transaction regression (concurrent begin_stage_if_new duplicate check) stays green.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Modify | Add `begin_stage_if_new`/`record_artifact` facade methods; `recover_stale_attempts()` drops its db argument (internal `self._db`) | `REQ-001`/`REQ-002` | Facade docstring L46; get_connection L58-65; recover_stale_attempts L189-254 | `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py` | `Verified` |
| `scripts/agent/workflow/workflow_engine.py` | Modify | Replace two `get_connection()` call sites with facade calls (L313-314, L373-374); drop the then-unused ops imports (L20-21) | `REQ-003` | Call sites verified at `ad48bfa28` | `tests/agent/workflow/test_workflow_engine.py` | `Verified` |
| `scripts/agent/orchestrator.py` | Modify | L92 becomes a no-arg facade call | `REQ-003` | Call site verified at `ad48bfa28` | `tests/agent/test_orchestrator.py` | `Verified` |
| `tests/agent/workflow/test_state_store.py` | Modify | 12 `store.recover_stale_attempts(store.get_connection())` sites → no-arg calls | `REQ-002`/`REQ-005` | Call sites verified (L122, L136, L150, L167, L181, L182, L192, L201, L208, L217, L227, L250) | self | `Verified` |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | 11 `recover_stale_attempts` sites (10 `s._db`, 1 `s.get_connection()`) → no-arg; add facade delegation tests for the new methods | `REQ-001`/`REQ-002`/`REQ-005` | Call sites verified (L328, L347, L365, L389, L416, L438, L498, L544, L586, L625, L674) | self | `Verified` |
| `tests/agent/workflow/test_stale_recovery_lease.py` | Modify | 8 `store.recover_stale_attempts(store.get_connection())` sites → no-arg calls | `REQ-002`/`REQ-005` | Call sites verified (L143, L168, L169, L196, L233, L260, L279, L299) | self | `Verified` |
| `tests/agent/workflow/test_workflow_engine.py` | Modify | Add routing assertion tests (facade interception; engine never fetches a raw connection) | `REQ-005` | Real-`store` fixture verified (L78-85) | self | `Verified` |
| `tests/agent/test_orchestrator.py` | Modify | Add startup routing test (no-arg recovery call) | `REQ-002`/`REQ-005` | `patch("agent.orchestrator.StateStore")` pattern verified (L189) | self | `Verified` |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Startup Recovery sentence (L165): "is called with the store's connection" → no-argument facade call | `REQ-002`/`REQ-003` | Sentence verified verbatim at `ad48bfa28` | n/a | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/idempotency_ops.py` | `begin_stage_if_new` transaction contract (begin_immediate, no explicit commit) the wrapper must preserve. Confirmed no-change (verification): signature and transaction discipline unchanged; the facade passes `self._db` | `REQ-004` |
| `scripts/agent/workflow/artifact_ops.py` | `record_artifact` signature/semantics to wrap. Confirmed no-change (verification): signature and commit behavior unchanged; the facade passes `self._db` | `REQ-001` |
| `plans/done/20261105-085959_wfreview004_workflow-adapter-and-engine-private-attribute-access.md` | Precedent boundary this plan continues | Design |
| `plans/done/20261108-084003_wfaudit001_processed-events-never-pruned.md` / `plans/done/20261108-084004_wfaudit007_task-status-never-reconciled.md` | Final `recover_stale_attempts` body shape this plan re-signatures (they extend the body; this plan only internalizes the connection) | Dependencies |
| `plans/done/20261108-084010_wfaudit009_test-only-state-helpers.md` | Its landed procedures delete facade `pending_tool_calls`/`find_stale_running_attempts` and retarget `recover_stale_attempts` test call sites this plan re-anchors (landing order: 009 → this plan) | Dependencies |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Checked for `recover_stale_attempts` db-argument wording. Confirmed no-change (verification): grep finds no such wording | `REQ-003` |

## Acceptance Criteria
- `REQ-001`: Facade methods delegate; engine's skip-path behavior on duplicate events unchanged (`AttemptRecord | None` semantics tested).
- `REQ-002`: `recover_stale_attempts()` callable with no arguments; recovery counts identical to HEAD for the same fixture database.
- `REQ-003`: `grep -rn "get_connection()" scripts/` shows no match from this plan's three converted sites; the only remaining production match is the `wfaudit001` purge call site (`UNK-01` follow-up). Test usage of `get_connection()` is allowed while the method exists (target zero, `UNK-01`).
- `REQ-004`: SQL-level test (or log capture) shows identical statements; concurrency/idempotency test green.
- `REQ-005`: Full `tests/agent/` green; new routing assertions pass.

## Tests
- Routing test: patching `StateStore.begin_stage_if_new` now intercepts engine stage start (mirrors wfaudit008's interception discipline); a side-effect test patching `StateStore.get_connection` to raise proves the engine no longer fetches raw connections.
- Retarget tests: mechanical no-arg rewrite of the 31 `recover_stale_attempts` call sites in `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py` (behavior-preserving).
- Delegation tests (new) in `tests/agent/workflow/test_workflow_state_store.py`: the facade `begin_stage_if_new`/`record_artifact` produce the same rows as the ops functions.
- Existing idempotency duplicate-insert and recovery lease tests stay green (regression lock on semantics).
- Orchestrator startup test (new): recovery invoked via no-arg facade call; `get_connection` never called during startup.

## Documentation Impact
- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` — Startup Recovery section (L165): "called with the store's connection" must state the no-argument call (resolved 2026-11-08: such a row exists; target row 9).
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — confirmed no-change (verification): grep for `get_connection` across `docs/` returns zero matches; no facade/connection boundary row to update (no speculative docs).
- Run docs checkers for domain agent (triggered: row 9 edits a domain-agent doc).

## Assumptions
- Wrapping with `self._db` preserves the exact transaction semantics because the ops functions take `SQLiteHelper` and manage their own begin/commit patterns (verified in Step 2 reads).
- No caller today passes a foreign connection into these ops (the three sites all pass the store's own connection), so no true caller-owns-transaction use case exists for these methods.
- `recover_stale_attempts` drops its db argument entirely; the method body binds `db = self._db` so statements added by `wfaudit001`/`wfaudit007` (which reference `db` inside the body) route through the store unchanged. The 31 test call sites are retargeted in the same release unit (partial landing would break the suite mid-unit; the plan's Release unit is already all-or-nothing).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | delete `get_connection()` once production users hit zero: after this plan the production count is one (`wfaudit001`'s purge call site, out of this plan's scope) plus remaining test usage | decision owner for the purge site | follow-up plan after this plan converts or internalizes the purge call; test usage retargets with it | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Modify | facade surface + recovery entry | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_engine.py` | Modify | stage-start + artifact recording paths | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/orchestrator.py` | Modify | startup recovery call | 8 | N/A | not applicable (rsynced) |
| `tests/agent/workflow/test_state_store.py` | Modify | recovery test call sites | N/A | N/A | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | recovery test call sites + facade delegation tests | N/A | N/A | not applicable (rsynced) |
| `tests/agent/workflow/test_stale_recovery_lease.py` | Modify | recovery test call sites | N/A | N/A | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_engine.py` | Modify | routing assertion tests | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_orchestrator.py` | Modify | startup routing test | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Startup Recovery wording | N/A | N/A | not applicable (docs) |

## Design
**Thin delegation, no logic movement.** The facade methods are one-liners calling the same ops functions with `self._db`; all SQL and transaction discipline stays in the ops modules (`idempotency_ops.py`, `artifact_ops.py`). This keeps the change mechanical and reviewable — a pure routing fix.

**No-argument recovery.** `recover_stale_attempts(self._db)` internalizes the connection because its only caller is the store itself via the orchestrator; the explicit-db convention is kept only where multi-store transaction ownership is real (none in the current call graph for these methods).

**Ordering with the recovery cluster**: `wfaudit001`/`wfaudit007` shape the recovery body; this plan changes only how it is invoked, so landing after them avoids merge churn in the same method.

## Implementation steps
1. **Phase 1: Facade methods (`REQ-001`, `REQ-002`).** Add wrappers, change `recover_stale_attempts` signature; unit tests for delegation.
2. **Phase 2: Call-site conversion (`REQ-003`, `REQ-004`, `REQ-005`).** Engine + orchestrator sites converted; 31 test call sites retargeted; routing tests.
3. **Phase 3: Boundary check (`REQ-003` grep, `UNK-01`) + docs.** Grep-clean this plan's sites; decide `get_connection()` follow-up; Startup Recovery doc sentence updated to the no-arg call.

### Release units
**Unit**: wfaudit015-full | **Phases**: 1, 2, 3 | **Reason**: routing change is only safe as a complete switch of the three production sites plus the no-arg signature and its 31 test call sites; a partial switch leaves the boundary half-auditable or the suite broken mid-unit.

## Validation plan
- `uv run pytest tests/agent/workflow/ tests/agent/test_orchestrator.py -q` after each phase; full `uv run pytest tests/ -q` before completion.
- Idempotency semantics regression (duplicate event skip, begin_immediate behavior) must pass unchanged.
- Lint/type gates per `rules/toolchain.md`; docs checkers if docs edited.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Facade wrapper hides a transaction nuance (e.g. caller-expected commit timing) | Low | Medium | Delegation-only design + existing transaction-semantics tests as regression lock |
| Merge churn with `wfaudit001`/`wfaudit007` edits to `recover_stale_attempts` | Medium | Low | Explicit landing order (this plan last on that method); `db = self._db` binding absorbs their body additions |
| Signature change breaks unretargeted test call sites if the unit lands partially | Medium | Low | All 31 sites are target rows; Release unit is all-or-nothing (suite validated only after the full unit) |

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Phase 1: facade methods | Completed | 20261109 | 20261109 | Facade methods + no-arg recover_stale_attempts landed; unit archived |
| 2 | Phase 2: call-site conversion | Completed | 20261109 | 20261109 | Engine/orchestrator sites + 31 test sites converted; routing tests added; unit archived |
| 3 | Phase 3: boundary check + docs | Completed | 20261109 | 20261109 | grep-clean on this plan's three sites; Startup Recovery doc updated; unit archived |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261108-175155_01_scripts_agent_workflow_state_store.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261108-175155_02_scripts_agent_workflow_workflow_engine.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-175155_03_scripts_agent_orchestrator.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-175155_04_tests_agent_workflow_test_state_store.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-175155_05_tests_agent_workflow_test_workflow_state_store.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-175155_06_tests_agent_workflow_test_stale_recovery_lease.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-175155_07_tests_agent_workflow_test_workflow_engine.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-175155_08_tests_agent_test_orchestrator.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-175155_09_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md` | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203228_wfaudit015_state-store-facade-bypass.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084011
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Required Changes (facade routing) | `scripts/agent/workflow/state_store.py` | delegating methods exist | delegation tests |
| `REQ-002` | Issue Evidence (self-feed call) | same | no-arg recovery | orchestrator test |
| `REQ-003` | Issue Problem | engine + orchestrator + docs row 9 | no grep match from this plan's three sites | grep |
| `REQ-004` | Plan Design (semantics preserved) | ops unchanged | identical SQL/transactions | regression tests |
| `REQ-005` | Issue Testing Expectations | tests | routing asserted | routing tests |

## Notes
- Source verified against HEAD `926dbc109`; the three bypass sites and the wfreview004 provenance are recorded in the issue's `## Adversarial Validation`.
- Sequence: `wfaudit006` -> `wfaudit001` -> `wfaudit007` -> `wfaudit009` -> this plan.
- Adversarial re-verification at HEAD `ad48bfa28` (2026-11-08):
  - Citation fix: `get_connection` is L58-65 (was L58-64).
  - Signature-change blast radius was undercounted: `recover_stale_attempts` has 31 test call sites passing the store's own connection (`test_state_store.py` 12, `test_workflow_state_store.py` 11 — ten pass `s._db` directly, one `s.get_connection()` — `test_stale_recovery_lease.py` 8). All pass the store's own connection, so the no-arg conversion is behavior-preserving; the 3 files became explicit Modify target rows (the original `tests/agent/workflow/` row was directory-granularity and cannot host a file-level procedure).
  - Missing test row added: `tests/agent/test_orchestrator.py` (the plan's own Tests requirement "recovery invoked via no-arg facade call" modifies this file).
  - Docs discovery: the facade/connection boundary row exists in `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` (L165 "is called with the store's connection"), not in `agent_04_03` (grep `get_connection` across `docs/`: zero matches). Row 9 added; `agent_04_03` confirmed no-change.
  - `wfaudit001` interaction: its landed procedure `implementations/20261108-134201_03_scripts_agent_orchestrator.py.md` adds `purge_finished_workflow_events(self._state_store.get_connection())` after the recovery call — a production `get_connection()` user this plan must not silently convert (out of scope). `REQ-003` reworded to scope the grep to this plan's three sites; the remaining match is carried in `UNK-01`. Its row-1 procedure also adds `db`-referencing statements inside `recover_stale_attempts`; this plan's `db = self._db` binding absorbs them (landing order: 001 -> 007 -> 009 -> this plan).
- Sibling overlap reconciliation (disjoint regions, explicit sequencing; these plans are landed design references, not implemented code): `state_store.py` rows — `wfaudit001` (`134201_01`), `wfaudit007` (`135741_01`) and `wfaudit009` (`170505_02`) edit `RecoveryReport`/`recover_stale_attempts` body/`_classify_running_attempts` and delete `find_stale_running_attempts`/`pending_tool_calls`; this plan edits only the `recover_stale_attempts` signature line plus the new facade methods — symbol-anchored, lands after all three, and calls the direct op modules through the new facades instead of re-adding the deleted ones. `tests/agent/workflow/test_state_store.py` / `test_workflow_state_store.py` — `170505_04/05` retargets land first and add further `recover_stale_attempts` call sites (with connection args, valid at their landing time); this plan's procedures convert every call site present at execution time, pattern-anchored, including those additions. `tests/agent/workflow/test_workflow_engine.py` — `170505_06` edits the count asserts/pending site (disjoint; this plan appends new test classes). `tests/agent/test_orchestrator.py` — `162804_02` (wfaudit008) patch retargets land first; this plan only adds a new test. `scripts/agent/orchestrator.py` — `155554_02` (wfaudit006) adds `close` after `workflow_status` (disjoint region); `134201_03` edits the L92 region first (this plan's edit is anchored on the recovery call symbol). `docs/23_agent/agent_03_03...` — `151141_03` edits the Loader Validation Rules section (disjoint from the Startup Recovery section); the "repairs attempt records only" half of the L165 sentence belongs to `wfaudit007`'s doc scope, not this plan.
- Procedure pass (2026-11-08): nine procedure documents generated (target-table rows 1-9); no `agent_04_03` procedure (grep no-op confirmed). `tools/check_plan_target_overlaps.py` reports "No findings" across active Frozen plans; `tools/plan_dependency_order.py` reports this plan `ready`.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-175155 -->
