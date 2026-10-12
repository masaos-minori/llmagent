## Goal
- Add one test that pins the documented contract: recovery refreshes the display-cache approval id from the recovered record while an existing task id is preserved (`REQ-002`).

## Scope
- Only `tests/agent/test_startup_approval_recovery.py`: one new test at the end of the class that tests the orchestrator's pending-approval recovery.

## Assumptions
- The neighbouring tests build a mock context inline and patch the lookup of pending approvals and the store at their definition modules; the new test does the same and does not patch the logger (the first recovery test does not either).
- This is a characterization test: it passes on the unchanged code and is meant to fail only if someone changes the contract.

## Design decisions
- Preset a stale approval id and a different task id so one run shows both outcomes: the id is refreshed, the task id is kept.
- State in the docstring that it pins the documented contract so a future change is deliberate.

## Alternatives considered
N/A: the Plan Design section already rejected adding a guard to the id assignment.

## Implementation
### Target file
`tests/agent/test_startup_approval_recovery.py`

### Procedure
1. At the end of the class (after the last recovery test) add test_startup_recovery_refreshes_pending_approval_id_but_keeps_task_id as an async test with the same asyncio marker as its neighbours.
2. Build the mock context as in the first recovery test, but preset the approval id to approval-stale and the task id to task-old, and the approval-pending flag to false.
3. Make the lookup return one pending approval for task-456 whose approval id is approval-123, patch the lookup and the store like the neighbours do, and run the orchestrator's pending-approval recovery.
4. Assert the approval-pending flag is true, the approval id is approval-123 (refreshed), and the task id is still task-old (guard preserved).
5. Run the new test on the unchanged production code and confirm it passes.
6. Mutation check: temporarily make the production id assignment conditional on the id being unset (wrap that one line in a check that the current value is None), run the new test and confirm it fails, then revert with the inverse edit and confirm that git diff for the production file is empty (do not use a checkout).

### Method
- Copy the structure of the first recovery test and the task-id preservation test; add only the preset values and the assertions described above.

### Details
- No new helper or import is needed; the module already imports what the neighbouring tests use.
- Do not edit existing tests.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_approval_recovery.py -v`: 27 existing plus the new test pass.
- Mutation check as in the procedure: the new test fails under the temporary guard and the production file is clean after the revert.
- `uv run ruff format --check tests/agent/test_startup_approval_recovery.py`, `uv run ruff check tests/agent/test_startup_approval_recovery.py`.
- Execution order for the whole plan: procedure 02 (test) first, then 01 (comment), then 03 (docs).

## Completion criteria
- The new test exists and passes on the unchanged code; it fails under the temporary guard; the production file is clean after the revert; existing tests are unchanged and pass.

## Out of scope
- Production code, other tests, and any change to the existing task-id preservation test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the characterization test and run the mutation check | Completed | 20261012-165514 | 20261012-165602 | stale_detector clean; applied first changed: tests/agent/test_startup_approval_recovery.py (+1 characterization test); passes on unchanged code; mutation check: id guard makes it fail (27 others pass), reverted by inverse edit, production file diff empty |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-165631 | 20261012-165631 | ruff format/check pass; check_mock_patch_targets no findings; 28 tests pass |

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
- **Requirement ID**: `REQ-002` (characterization test of the contract)
- **Source issue**: issues/20261012-124847_start005_startup-approval-recovery-overwrites-pending_approval_id-without-checking-current-turn-state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-164808_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-165021
- **Related target files**: tests/agent/test_startup_approval_recovery.py