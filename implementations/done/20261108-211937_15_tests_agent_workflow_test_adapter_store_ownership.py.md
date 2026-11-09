## Goal
Rename the `RetryPolicy` kwarg `backoff_sec` to `retry_wait_sec` in `tests/agent/workflow/test_adapter_store_ownership.py` so the `_definition()` fixture constructs `RetryPolicy` under the renamed field (`REQ-003`, fallout row added to the Plan 2026-11-09).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 15 only: `tests/agent/workflow/test_adapter_store_ownership.py`.

## Assumptions
- Landing order: after procedure `implementations/20261108-211937_03_scripts_agent_workflow_models.py.md` (row 3, renames the dataclass field); before row 3 lands the new kwarg raises `TypeError`.
- The file was added by wfaudit008 commit `634724f3d` after the Plan froze; at HEAD `e4b47f11e` it carries exactly one `backoff_sec` occurrence, `retry_policy=RetryPolicy(max_attempts=1, backoff_sec=0)` in `_definition()` (L36).

## Design decisions
- Mechanical kwarg rename `backoff_sec=0` -> `retry_wait_sec=0`; the value and the rest of the fixture stay unchanged.

## Alternatives considered
- N/A: single-site rename dictated by the models field rename (procedure 03).

## Implementation
### Target file
`tests/agent/workflow/test_adapter_store_ownership.py`

### Procedure
Rename one keyword argument.

### Method
In `_definition()`, `retry_policy=RetryPolicy(max_attempts=1, backoff_sec=0),` -> `retry_policy=RetryPolicy(max_attempts=1, retry_wait_sec=0),`.

### Details
- After the edit, `grep -n backoff_sec tests/agent/workflow/test_adapter_store_ownership.py` returns nothing.
- `RetryPolicy` is already imported from `agent.workflow.models`; no import edit.

## Compatibility considerations
- Must land with the release unit; the file does not load under the old kwarg once procedure 03 lands.

## Security considerations
- No change.

## Rollback considerations
- N/A: revert with the release unit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_adapter_store_ownership.py -q` green after row 3 lands.
- `grep -rn backoff_sec tests/` returns nothing after all rows land.

## Completion criteria
- No `backoff_sec` token in the file; the file's tests pass against the renamed field.

## Out of Scope
- Any change to the store-ownership assertions the file pins (wfaudit006/wfaudit008).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-092921 | 20261109-092921 | Changed: test_adapter_store_ownership.py (Plan row 15, fallout amendment) |
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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: tests/agent/workflow/test_adapter_store_ownership.py
