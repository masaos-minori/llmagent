## Goal
Rename the `retry_policy` key inside the three inline workflow-JSON fixture strings in `tests/agent/test_repl_health.py` from `backoff_sec` to `retry_wait_sec` so the fixtures load under the renamed loader contract (`REQ-003`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 12 only: `tests/agent/test_repl_health.py`.

## Assumptions
- Landing order: after procedure 04 (loader); running this file before row 4 lands fails with the loader's missing-keys error on the old fixture key.
- HEAD census: exactly three `backoff_sec` occurrences, all inside JSON fixture strings — L473 `'"retry_policy": {"max_attempts": 3, "backoff_sec": 1}'`, L500 and L514 (same content, closing brace variant).

## Design decisions
- In-fixture key rename only: `"backoff_sec": 1` -> `"retry_wait_sec": 1`; `max_attempts` values and surrounding fixture JSON unchanged.

## Alternatives considered
- N/A: fixture renames are mechanical consequences of the loader contract (procedure 04).

## Implementation
### Target file
`tests/agent/test_repl_health.py`

### Procedure
Rename the key in each fixture string.

### Method
At L473, L500, and L514, replace `"backoff_sec": 1` with `"retry_wait_sec": 1` inside the quoted JSON. No other fixture text changes.

### Details
- After the edit, `grep -n backoff_sec tests/agent/test_repl_health.py` returns nothing.

## Compatibility considerations
- The fixtures are parsed by the real loader (health-check tests that write a workflow definition), so this row must land in the same commit as row 4.

## Security considerations
- No change.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run pytest tests/agent/test_repl_health.py -q` green after row 4 lands.
- Full `uv run pytest tests/ -q` and lint/type gates per `rules/toolchain.md` at unit completion.

## Completion criteria
- `REQ-003` for this file: no `backoff_sec` token remains; health tests green.

## Out of Scope
- REPL health behavior itself.

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
- **Related target files**: tests/agent/test_repl_health.py
