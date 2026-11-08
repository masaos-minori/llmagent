## Goal

Retarget the inert public-name test patches in `tests/agent/test_orchestrator.py` to the private methods the exercised flows actually call, verified per test through a HEAD interception experiment rather than bulk renaming (`REQ-003`), while preserving every test's observable pass/fail semantics (`REQ-004`).

## Scope
**Release unit**: wfaudit008-full

- Covers Plan `plans/20261108-084009_wfaudit008_dead-alias-test-patches.md` row 2 only: `tests/agent/test_orchestrator.py`.
- Executes the Plan's Phases 1-2 (interception experiment + retargeting). The alias deletion itself is sibling document `implementations/20261108-162804_01_scripts_agent_workflow_engine_adapter.py.md`; the `deactivate_workflow` patch retarget in Method step 5 depends on that document's collapse landing first.

## Assumptions
- Line numbers refer to HEAD `ad48bfa28`; no already-generated procedure of this batch edits this file, so citations stay valid at execution time.
- `adapter.execute_turn` calls its own private methods internally (`scripts/agent/workflow_engine_adapter.py` L168-171 init/activate, L239/L243 halt), while the orchestrator calls only the public `deactivate_workflow` (L200) — so public-alias patches on a mocked adapter intercept nothing in the turn flow.
- The Phase 1 experiment (Plan `UNK-02`) assumes no interception currently happens for the public-name patches; each test is verified individually, not assumed.

## Design decisions
- Per-test verification over bulk rename: each of the 10 public-name patch groups is retargeted only after the HEAD experiment shows which private target the exercised flow really calls (`REQ-003` acceptance: the retargeted mock's call asserts pass).
- The private `deactivate_workflow` twin patch at L2873 flips to the public name instead of staying private, because after the sibling collapse the orchestrator flow only reaches the real body through the public name.

## Alternatives considered
- Delete the inert patches wholesale: rejected — the tests pin observable timeout/halt behavior of the real flow; the plan mandates retargeting, and `REQ-004` forbids removing coverage.
- Keep public-name patches and re-add the aliases as real delegating methods: rejected — contradicts the plan's whole premise (alias deletion, `REQ-001`/`REQ-005`).

## Implementation
### Target file
`tests/agent/test_orchestrator.py`

### Procedure
Run the HEAD interception experiment first and record a per-test map, then retarget each patch group to the private name the flow really calls, keep the intercepting `deactivate_workflow` patches, and fix the two misleading comments.

### Method
1. Phase 1 (HEAD experiment, records `UNK-02`): for each affected test, temporarily switch its public-name patches to the private names on HEAD and run it; record in the Execution Log which tests pass with the private patches (interception proven), which newly fail, and which asserts fail. Newly visible failures are flow dependencies the inert patches were hiding — fix them before proceeding, never by deleting or weakening the test (`REQ-004`).
2. Retarget the turn-flow groups (init and activate patches to `_init_workflow_task` / `_activate_workflow`; mock `return_value` and `side_effect` values stay identical, e.g. the `("wf-1", MagicMock(task_id="task-1"))` tuple and the `_fake_activate` side effects): L312/L315 (`test_handle_turn_returns_normally_on_genuine_workflow_timeout`), L341/L344 (`test_handle_turn_does_not_raise_on_workflow_timeout`), L435 (`test_handle_turn_returns_normally_on_genuine_asyncio_wait_for_timeout`), L532 (`test_handle_turn_does_not_raise_on_real_asyncio_wait_for_timeout`), L632 (`test_retry_runs_turn_entry_once`), L862 (lambda side effect, `test_entry_failure_not_retried`), L980 (`test_entry_longer_than_stage_timeout_still_completes`), L1074 (`test_llm_stage_still_bounded_by_timeout`).
3. Retarget the direct-`execute_turn` halt groups (both init and activate to private names; the tests keep calling `orch._workflow_adapter.execute_turn` with the patched `StateStore` and `WorkflowEngine` wiring): L2755/L2758 (`test_preserves_halted_status_via_halt_error`), L2798/L2801 (`test_preserves_halted_status_via_timeout_error`).
4. Keep the intercepting private group untouched: L1558 `_activate_workflow` in `test_failure_before_activate_emits_single_turn_end` already patches the real call target.
5. After sibling document 01's collapse lands: flip the twin patch at L2873 from `_deactivate_workflow` to `deactivate_workflow` in `test_execute_failure_returns_typed_tuple_without_adapter_status_write`; the private init/activate patches at L2869-2870 stay (`scripts/agent/orchestrator.py` reaches the deactivate body only through the public name).
6. Comments at L420 and L518 already name the private methods while the code patches public aliases; the retargeting above makes them accurate without a separate edit — confirm this in the diff review.

### Details
- The `deactivate_workflow` patch sites at L316/L345/L439/L536/L636/L867/L984/L1078/L2759/L2802 are already intercepting (the orchestrator finally block calls the public name) — unchanged (`REQ-004`).
- No assert_called-family assertion exists on the lifecycle mocks at HEAD; after retargeting, add call asserts where Phase 1 proved the flow guarantees the call, per the plan's `REQ-003` acceptance mechanism.

## Compatibility considerations
- Pure test-side change until step 5, which is gated on sibling document 01 landing; both ship in the same release unit `wfaudit008-full`, so no intermediate state has a test patch pointing at a deleted name.

## Security considerations
- None: test wiring only, no production code or I/O change.

## Rollback considerations
- Revert the commit: patches return to HEAD names; behavior of the suite is HEAD behavior. No persisted state.

## Validation plan
- Per-test: `uv run pytest tests/agent/test_orchestrator.py -v -k {test_name}` for each affected test after retargeting — green, with the new call asserts passing (`REQ-003`).
- Phase 1 evidence: the interception map recorded in the Execution Log lists each test with its proven call target (`UNK-02` closure).
- `REQ-004` review: diff review confirms no test deleted, no assertion weakened, mock return/side-effect values unchanged.
- Full `uv run pytest tests/ -q` after both procedures of the unit land; lint gates per `rules/toolchain.md` (tests are linted by `ruff`).

## Completion criteria
- Every `patch.object` target in the affected tests names a method the exercised flow actually invokes; the plan's REQ-005 grep shows no public-alias patch strings left (`init_workflow_task(`, `activate_workflow(` appear only as private-underscore usages).
- All affected tests pass with unchanged observable assertions, and the Phase 1 interception map is recorded in the Execution Log.

## Out of Scope
- The adapter alias deletion and the `tests/agent/workflow/test_adapter_alias_surface.py` (new) pinning tests (sibling document 01, same release unit).
- `tests/agent/test_orchestrator.py` fixtures and helpers unrelated to the lifecycle patches (untouched).
- Docs (plan Documentation Impact verified no-change).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: HEAD interception experiment per test; record map (`UNK-02`) | Completed | 20261109-022546 | 20261109-022546 | implementation complete; validation gates green; suite 4216 passed; REQ-005 grep clean |
| 2 | Retarget the 10 public-name patch groups per Method 2-3 (`REQ-003`) | Completed | 20261109-022546 | 20261109-022546 | implementation complete; validation gates green; suite 4216 passed; REQ-005 grep clean |
| 3 | Flip L2873 twin patch after sibling document 01 lands (Method 5) | Completed | 20261109-022546 | 20261109-022546 | implementation complete; validation gates green; suite 4216 passed; REQ-005 grep clean |
| 4 | Add guaranteed-call asserts; confirm L420/L518 comments accurate after retargeting (Method 6, Details) | Completed | 20261109-022546 | 20261109-022546 | implementation complete; validation gates green; suite 4216 passed; REQ-005 grep clean |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-022546 | 20261109-022546 | implementation complete; validation gates green; suite 4216 passed; REQ-005 grep clean |

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
- **Requirement ID**: `REQ-003` (patches intercept real calls), `REQ-004` (behavior-preserving retargeting)
- **Source issue**: `issues/20261107-203221_wfaudit008_dead-alias-test-patches.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084009_wfaudit008_dead-alias-test-patches.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-162804
- **Related target files**: `tests/agent/test_orchestrator.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-162804 -->
