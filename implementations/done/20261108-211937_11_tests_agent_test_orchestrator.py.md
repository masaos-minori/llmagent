## Goal
Rename every `backoff_sec` fixture and helper reference in `tests/agent/test_orchestrator.py` to `retry_wait_sec`, and pin the reduced `_record_exit_status` signature after the adapter strips its `error_kind` parameter (`REQ-001`, `REQ-003`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 11 only: `tests/agent/test_orchestrator.py`.

## Assumptions
- Landing order: after procedure 01 (adapter signature reduction), procedure 02 (engine), and procedure 03 (models field rename); the new signature test fails before row 1 lands.
- HEAD census: 12 `backoff_sec` occurrences at L204, L414, L512, L613, L853, L961, L1055, L3171, L3819, L3929, L3934, L3982; rename every occurrence remaining at execution time.
- Sibling pending procedures on this file (`implementations/20261108-162804_02_tests_agent_test_orchestrator.py.md` and `implementations/20261108-175155_08_tests_agent_test_orchestrator.py.md`) are text-anchored and disjoint from these sites (plan Related Documents row).

## Design decisions
- The two behavioral sites keep their roles after the rename: L3819 `await asyncio.sleep(policy.backoff_sec)` inside `class _RetryThenHaltEngine` becomes `policy.retry_wait_sec` (the fake engine mirrors the real engine's constant wait), and L3929's comment "force backoff_sec=0 so the retries are instant" renames with it.
- New test `test_record_exit_status_reduced_signature` (new) is signature-level pinning, not behavior pinning: `inspect.signature(WorkflowEngineAdapter._record_exit_status)` must name exactly `exit_reason` and `task` (no `error_kind` parameter). A second new test `test_status_for_exit_single_parameter_mapping` (new) pins `_status_for_exit` as one-parameter with the `cancelled` -> `halted` and `completed` -> `None` mappings (the plan's `REQ-001` acceptance and the Validation plan of procedure 01). Neither `inspect` nor `agent.workflow_engine_adapter` is imported by the file at HEAD `e4b47f11e` (it only patches `agent.workflow_engine_adapter.*` by string), so both imports are added to the top-level import block.
- New test placement: end of `class TestTaskStatusPerTurnOutcome` (HEAD L3192), the class that already exercises the real adapter/engine status paths.

## Alternatives considered
- Call `_record_exit_status` with the old 3-argument shape and expect `TypeError`: rejected — a signature introspection assert states the contract directly and survives future refactors of the call path.
- Deleting the fake-engine sleep line instead of renaming: rejected — the fake mirrors the engine loop the plan keeps (REQ-004).

## Implementation
### Target file
`tests/agent/test_orchestrator.py`

### Procedure
File-wide key rename per the census, then add one signature test.

### Method
1. Rename all 12 occurrences: the `RetryPolicy(max_attempts=..., backoff_sec=...)` fixtures (L204, L414, L512, L613, L853, L961, L1055, L3171, L3934, L3982), the fake-engine attribute read at L3819, and the comment at L3929 — each `backoff_sec` -> `retry_wait_sec`.
2. Add `import inspect` to the top-level stdlib imports (alphabetical position) and `from agent.workflow_engine_adapter import WorkflowEngineAdapter, _status_for_exit` to the first-party block (ruff isort places it after the `agent.workflow...` imports).
3. Append to `class TestTaskStatusPerTurnOutcome`:
   - `test_record_exit_status_reduced_signature` (new): `params = inspect.signature(WorkflowEngineAdapter._record_exit_status).parameters; assert "error_kind" not in params; assert list(params) == ["self", "exit_reason", "task"]`.
   - `test_status_for_exit_single_parameter_mapping` (new): `assert list(inspect.signature(_status_for_exit).parameters) == ["exit_reason"]; assert _status_for_exit("cancelled") == "halted"; assert _status_for_exit("completed") is None`.

### Details
- After the edit, `grep -n backoff_sec tests/agent/test_orchestrator.py` returns nothing.
- New imports: `inspect` and `WorkflowEngineAdapter`/`_status_for_exit` from `agent.workflow_engine_adapter` (no import cycle: the module is already loaded by `agent.orchestrator`).

## Compatibility considerations
- Running this file before rows 1 and 3 land fails (old signature, old kwarg); the plan's Phase 1/3 chains land them together.

## Security considerations
- No change.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run pytest tests/agent/test_orchestrator.py -q` green after rows 1-3 land; the new test fails on HEAD (signature still carries `error_kind`).
- Full `uv run pytest tests/ -q` and lint/type gates per `rules/toolchain.md` at unit completion.

## Completion criteria
- `REQ-001`: the signature test proves `_record_exit_status` takes `(self, exit_reason, task)`. `REQ-003`: no `backoff_sec` token remains in the file.

## Out of Scope
- Deactivation-twin and alias-block test edits (owned by `162804_02`/`175155_08`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-092921 | 20261109-092921 | Changed: test_orchestrator.py; imports corrected, _status_for_exit pin test added |
| 2 | Add or update tests per Validation plan | Completed | 20261109-092921 | 20261109-092921 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-092921 | 20261109-092921 | Full suite 11904 passed; 3 pre-existing env errors in test_workflow_status_vocabulary.py (/tmp/opencode missing); diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-092921 | 20261109-092921 | N/A: docs covered by procedures 13-14 |

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
- **Requirement ID**: `REQ-001`, `REQ-003`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: tests/agent/test_orchestrator.py
