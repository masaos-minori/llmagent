## Goal
Rename every `backoff_sec` fixture, payload, assertion, test method name, and match string in `tests/agent/workflow/test_workflow_loader.py` to `retry_wait_sec`, keeping the loader validation tests green under the new key (`REQ-003`/`REQ-005`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 7 only: `tests/agent/workflow/test_workflow_loader.py`.

## Assumptions
- Landing order: after procedure 04 (loader emits the new key/validation labels) and after `implementations/20261108-151141_02_tests_agent_workflow_test_workflow_loader.py.md` (wfaudit004 appends new test classes at file end, including retry-policy payload fixtures naming `backoff_sec`); this procedure then renames every `backoff_sec` occurrence remaining in the file at execution time — HEAD count 11 plus whatever wfaudit004 added (plan Related Documents row freezes wfaudit004 first).
- Test method rename: `test_negative_backoff_sec_rejected` (HEAD L181) -> `test_negative_retry_wait_sec_rejected` (new) so the file carries no `backoff_sec` token.

## Design decisions
- Rename rule is textual ("every remaining `backoff_sec` occurrence in the file at execution time"), anchored by the HEAD quoted sites rather than line numbers: the JSON fixture string at L29, the `wdef.retry_policy.backoff_sec == 1` assertion at L56, the payload mutation at L175, the method name and payload at L181-185, the `pytest.raises(..., match="backoff_sec must be >= 0")` string at L189, the parametrized field list `["max_attempts", "backoff_sec"]` at L254, and the payload fixtures at L274, L304, L316, L328.
- The match string follows the loader label produced by procedure 04 (`retry_policy.retry_wait_sec must be >= 0`); the parametrized test asserts each required key is reported when absent — the field list names the new key.

## Alternatives considered
- Keep the old match string and expect the loader to dual-report: rejected — procedure 04 renames the `_require_int` label, so the test string must match the new message exactly.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_loader.py`

### Procedure
File-wide textual rename of the key and dependent names.

### Method
Rename each occurrence per the Assumptions list: fixture JSON strings `"backoff_sec": N` -> `"retry_wait_sec": N`, attribute accesses `.backoff_sec` -> `.retry_wait_sec`, the method name `test_negative_backoff_sec_rejected` -> `test_negative_retry_wait_sec_rejected` (new), and the match string to `"retry_wait_sec must be >= 0"`. No assertion logic, parameter sets, or fixture structure change beyond the name.

### Details
- After the edit, `grep -n backoff_sec tests/agent/workflow/test_workflow_loader.py` returns nothing.
- REQ-005's "existing loader validation tests (L236, L254 parametrization) pass with the renamed field" is satisfied by the rename alone — no new test needed in this file.

## Compatibility considerations
- None beyond the landing order: running this file before procedures 04/06 land fails (loader rejects the new key); the plan's Phase 3 chain lands them together.

## Security considerations
- No change.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_loader.py -q` green after rows 4 and 6 land.
- Full `uv run pytest tests/ -q` and lint/type gates per `rules/toolchain.md` at unit completion.

## Completion criteria
- No `backoff_sec` token in the file; all loader validation tests pass against the renamed key and message.

## Out of Scope
- New loader validation tests (wfaudit004's `151141_02` adds those; this row renames only).

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
- **Requirement ID**: `REQ-003`, `REQ-005`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: tests/agent/workflow/test_workflow_loader.py
