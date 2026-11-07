## Goal
Route the three raw-connection call-outs (engine stage-start guard, engine artifact recorder, orchestrator recovery) through `StateStore` facade methods so the persistence boundary stays auditable and `get_connection()` loses its production users.

## Priority
Low

## Scope
- **In-Scope**:
  - `scripts/agent/workflow/state_store.py` — add facade methods `begin_stage_if_new(...)` and `record_artifact(...)` wrapping the ops functions with `self._db`; make `recover_stale_attempts()` take no db argument (internal `self._db`), keeping the explicit-arg form only where callers genuinely own a different transaction.
  - `scripts/agent/workflow/workflow_engine.py` — replace `self._store.get_connection()` call sites (L313-314, L373-374) with facade calls.
  - `scripts/agent/orchestrator.py` — `recover_stale_attempts(self._state_store.get_connection())` (L92) becomes `self._state_store.recover_stale_attempts()`.
  - Tests: transaction-semantics regression (begin_immediate still spans check-then-insert) and facade routing assertions.
- **Out-of-Scope**:
  - Deleting `get_connection()` itself — keep it (documented escape hatch) unless the grep shows zero remaining users, in which case deletion is a follow-up recorded as `UNK-01`.
  - Changing the ops functions' signatures (`begin_stage_if_new`, `record_artifact` keep their `(db, ...)` shape).
  - The ownership/close contract (planned as `wfaudit006`, landed first).
- **Dependencies**: After `wfaudit006` (no ownership-flag close path to consider in new facade methods) and after `wfaudit001`/`wfaudit007` (their extensions to `recover_stale_attempts` are folded in, not reworked). After `wfaudit009` (`find_stale_running_attempts` deletion simplifies the facade surface being cleaned).

## Background
`StateStore` documents itself as the CRUD facade (`scripts/agent/workflow/state_store.py:46`); `get_connection()` (L58-64) is explicitly "use this only when necessary". Production uses it exactly three times: engine `begin_stage_if_new(self._store.get_connection(), ...)` (`workflow_engine.py:313-314`), engine `record_artifact(self._store.get_connection(), ...)` (L373-374), and orchestrator `self._state_store.recover_stale_attempts(self._state_store.get_connection())` (`orchestrator.py:92`) — the last one feeds the store's own connection back into its own method. These sites are the sanctioned output of `dee33ce7b fix(wfreview004)` (private-attribute access cleanup); this plan is the next step its own precedent anticipates. Verified in the issue's `## Adversarial Validation`.

## Problem
Callers pass the store's private connection back into the store's own operation functions, so the persistence boundary is no longer a single auditable surface: a reader of `StateStore` cannot enumerate all workflow.sqlite writes.

## Reason for Change
The facade exists to make writes enumerable; three raw-connection call-outs defeat it, and the orchestrator self-feed is the clearest signal the API shape (db-argument methods) is wrong for these call sites.

## Implementation Intent
Add thin facade methods that call the same ops functions with `self._db`; convert the db-argument facade methods that always receive the store's own connection to no-argument methods. Transaction semantics are unchanged — the wrappers pass `self._db` straight through, so `begin_immediate` and the recovery transaction behave identically.

## Requirements
- `REQ-001`: `StateStore.begin_stage_if_new(...)` and `StateStore.record_artifact(...)` exist and delegate to the ops functions with `self._db`, preserving return semantics (`AttemptRecord | None`).
- `REQ-002`: `recover_stale_attempts()` takes no required db argument and uses `self._db`.
- `REQ-003`: Zero `get_connection()` calls remain in `scripts/` production paths (engine L314/L374 and orchestrator L92 converted).
- `REQ-004`: Behavior is byte-identical: same SQL, same transaction boundaries (begin_immediate still wraps check-then-insert; recovery compare-and-swap unchanged).
- `REQ-005`: Tests pin the routing (engine/orchestrator no longer fetch raw connections) and the transaction regression (concurrent begin_stage_if_new duplicate check) stays green.

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Modify | Add `begin_stage_if_new`/`record_artifact` facade methods; `recover_stale_attempts()` signature change | `REQ-001`/`REQ-002` | Facade docstring L46; get_connection L58-64 | `tests/agent/workflow/` | `Verified` |
| `scripts/agent/workflow/workflow_engine.py` | Modify | Replace two `get_connection()` call sites with facade calls (L313-314, L373-374) | `REQ-003` | Call sites verified | engine tests | `Verified` |
| `scripts/agent/orchestrator.py` | Modify | L92 becomes a no-arg facade call | `REQ-003` | Call site verified | orchestrator tests | `Verified` |
| `tests/agent/workflow/` | Modify | Routing assertions + keep existing transaction-semantics tests green | `REQ-005` | Existing recovery/idempotency tests in these files | self | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/idempotency_ops.py` | `begin_stage_if_new` transaction contract (begin_immediate, no explicit commit) the wrapper must preserve | `REQ-004` |
| `scripts/agent/workflow/artifact_ops.py` | `record_artifact` signature/semantics to wrap | `REQ-001` |
| `plans/done/20261105-085959_wfreview004_workflow-adapter-and-engine-private-attribute-access.md` | Precedent boundary this plan continues | Design |
| `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md` / `plans/20261108-084004_wfaudit007_task-status-never-reconciled.md` | Final `recover_stale_attempts` body shape this plan re-signatures | Dependencies |

## Acceptance Criteria
- `REQ-001`: Facade methods delegate; engine's skip-path behavior on duplicate events unchanged (`AttemptRecord | None` semantics tested).
- `REQ-002`: `recover_stale_attempts()` callable with no arguments; recovery counts identical to HEAD for the same fixture database.
- `REQ-003`: `grep -rn "get_connection()" scripts/` -> no matches (test usage allowed only if unavoidable; target zero).
- `REQ-004`: SQL-level test (or log capture) shows identical statements; concurrency/idempotency test green.
- `REQ-005`: Full `tests/agent/` green; new routing assertions pass.

## Tests
- Routing test: patching `StateStore.begin_stage_if_new` now intercepts engine stage start (mirrors wfaudit008's interception discipline).
- Existing idempotency duplicate-insert and recovery lease tests stay green (regression lock on semantics).
- Orchestrator startup test: recovery invoked via no-arg facade call.

## Documentation Impact
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — if it describes the facade/connection boundary, state that production writes flow through facade methods. Only update if such a row exists (no speculative docs).
- Run docs checkers for domain agent if edited.

## Assumptions
- Wrapping with `self._db` preserves the exact transaction semantics because the ops functions take `SQLiteHelper` and manage their own begin/commit patterns (verified in Step 2 reads).
- No caller today passes a foreign connection into these ops (the three sites all pass the store's own connection), so no true caller-owns-transaction use case exists for these methods.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | delete `get_connection()` once production users hit zero (tests may still use it) | remaining test usage count | follow-up deletion after this plan if grep shows test-only usage | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Modify | facade surface + recovery entry | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_engine.py` | Modify | stage-start + artifact recording paths | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/orchestrator.py` | Modify | startup recovery call | 8 | N/A | not applicable (rsynced) |
| `tests/agent/workflow/` | Modify | tests only | N/A | N/A | not applicable (rsynced) |

## Design
**Thin delegation, no logic movement.** The facade methods are one-liners calling the same ops functions with `self._db`; all SQL and transaction discipline stays in the ops modules (`idempotency_ops.py`, `artifact_ops.py`). This keeps the change mechanical and reviewable — a pure routing fix.

**No-argument recovery.** `recover_stale_attempts(self._db)` internalizes the connection because its only caller is the store itself via the orchestrator; the explicit-db convention is kept only where multi-store transaction ownership is real (none in the current call graph for these methods).

**Ordering with the recovery cluster**: `wfaudit001`/`wfaudit007` shape the recovery body; this plan changes only how it is invoked, so landing after them avoids merge churn in the same method.

## Implementation steps
1. **Phase 1: Facade methods (`REQ-001`, `REQ-002`).** Add wrappers, change `recover_stale_attempts` signature; unit tests for delegation.
2. **Phase 2: Call-site conversion (`REQ-003`, `REQ-004`).** Engine + orchestrator sites converted; routing + semantics tests.
3. **Phase 3: Boundary check (`REQ-003` grep, `UNK-01`).** Grep-clean production; decide `get_connection()` follow-up; docs row if applicable.

### Release units
**Unit**: wfaudit015-full | **Phases**: 1, 2, 3 | **Reason**: routing change is only safe as a complete switch of the three sites; a partial switch leaves the boundary half-auditable.

## Validation plan
- `uv run pytest tests/agent/workflow/ tests/agent/test_orchestrator.py -q` after each phase; full `uv run pytest tests/ -q` before completion.
- Idempotency semantics regression (duplicate event skip, begin_immediate behavior) must pass unchanged.
- Lint/type gates per `rules/toolchain.md`; docs checkers if docs edited.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Facade wrapper hides a transaction nuance (e.g. caller-expected commit timing) | Low | Medium | Delegation-only design + existing transaction-semantics tests as regression lock |
| Merge churn with `wfaudit001`/`wfaudit007` edits to `recover_stale_attempts` | Medium | Low | Explicit landing order (this plan last on that method) |

## Execution Status
### Execution Status
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: facade methods | Planned | engineer | | | |
| Phase 2: call-site conversion | Planned | engineer | | | |
| Phase 3: boundary check | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

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
| `REQ-003` | Issue Problem | engine + orchestrator | zero production get_connection | grep |
| `REQ-004` | Plan Design (semantics preserved) | ops unchanged | identical SQL/transactions | regression tests |
| `REQ-005` | Issue Testing Expectations | tests | routing asserted | routing tests |

## Notes
- Source verified against HEAD `926dbc109`; the three bypass sites and the wfreview004 provenance are recorded in the issue's `## Adversarial Validation`.
- Sequence: `wfaudit006` -> `wfaudit001` -> `wfaudit007` -> `wfaudit009` -> this plan.
