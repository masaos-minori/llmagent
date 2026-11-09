## Goal
Rename the `RetryPolicy` kwarg `backoff_sec` to `retry_wait_sec` in `tests/agent/workflow/test_session_diagnostics_wiring.py` so the wiring fixture constructs `RetryPolicy` under the renamed field (`REQ-003`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 10 only: `tests/agent/workflow/test_session_diagnostics_wiring.py`.

## Assumptions
- Landing order: after procedure 03 (`scripts/agent/workflow/models.py` renames the `RetryPolicy` dataclass field); running this file before row 3 lands fails with `TypeError` on the unknown kwarg.
- HEAD census: exactly one `backoff_sec` occurrence in the file, the fixture construction at L38 `retry_policy=RetryPolicy(max_attempts=1, backoff_sec=0)`.

## Design decisions
- Mechanical kwarg rename `backoff_sec=0` -> `retry_wait_sec=0`; values and the rest of the fixture unchanged.

## Alternatives considered
- N/A: single-site rename dictated by the models field rename (procedure 03).

## Implementation
### Target file
`tests/agent/workflow/test_session_diagnostics_wiring.py`

### Procedure
Rename one keyword argument.

### Method
At L38, `retry_policy=RetryPolicy(max_attempts=1, backoff_sec=0)` -> `retry_policy=RetryPolicy(max_attempts=1, retry_wait_sec=0)`.

### Details
- After the edit, `grep -n backoff_sec tests/agent/workflow/test_session_diagnostics_wiring.py` returns nothing.

## Compatibility considerations
- The file imports `RetryPolicy` directly from `agent.workflow.models` (L17); no import edit is needed because only the kwarg name changes.

## Security considerations
- No change.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_session_diagnostics_wiring.py -q` green after row 3 lands.
- Full `uv run pytest tests/ -q` and lint/type gates per `rules/toolchain.md` at unit completion.

## Completion criteria
- `REQ-003` for this file: no `backoff_sec` token remains; wiring tests green.

## Out of Scope
- Any change to the diagnostics wiring under test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-092921 | 20261109-092921 | — |
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
- **Related target files**: tests/agent/workflow/test_session_diagnostics_wiring.py
