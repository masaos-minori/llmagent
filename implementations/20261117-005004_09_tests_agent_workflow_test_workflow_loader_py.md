## Goal

Update `tests/agent/workflow/test_workflow_loader.py` to the strict `retry_on` contract: add `retry_on` to the `_VALID` fixture, convert the two absent-key acceptance tests into rejection tests naming `retry_policy.retry_on`, and add an empty-`retry_on` semantics test (`REQ-001`, `REQ-002`, `REQ-005`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-001` (seq 02) makes `retry_on` a required loader key; the loader rejects an absent key with `WorkflowLoadError` naming it.
- `_VALID` (line 21) is the shared fixture spread into most tests via `dict(_VALID)`; adding `retry_on` there keeps every such test valid under the new required-key rule.

## Design decisions
- **Fixture-level change**: put `retry_on` in `_VALID.retry_policy` rather than patching each test, so all `dict(_VALID)`-based tests carry a valid value.
- **Empty-list semantics test** encodes Decision 2 (Plan `Design`): an explicit `retry_on: []` loads successfully and yields `()`.

## Alternatives considered
N/A: test-only.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_loader.py`
### Procedure
1. Add `retry_on` to the `_VALID` fixture.
2. Convert `test_absent_retry_on_key_loads_default` into a rejection test.
3. Convert `test_older_format_definition_without_retry_on_loads` into a rejection test.
4. Add an empty-`retry_on` semantics test.
### Method
One fixture edit; two test-body rewrites; one new test method.
### Details
- Lines 29 (`_VALID`): change
  `    "retry_policy": {"max_attempts": 3, "retry_wait_sec": 1},`
  to
  `    "retry_policy": {"max_attempts": 3, "retry_wait_sec": 1, "retry_on": ["exception"]},`
  so every `dict(_VALID)`-based test carries a valid `retry_on` under the required-key rule.
- Lines 285-288 (`test_absent_retry_on_key_loads_default`): rewrite to a rejection test. Build a definition that omits `retry_on` (e.g. `data = {k: v for k, v in _VALID.items() if k != "retry_policy"}` then re-add `retry_policy` without `retry_on`, or pop `retry_on` from a copy), then assert `pytest.raises(WorkflowLoadError)` with a message matching `retry_policy.retry_on`. Remove the old `assert loader.load().retry_policy.retry_on == ("exception",)`.
- Lines 290-298 (`test_older_format_definition_without_retry_on_loads`): rewrite to a rejection test with the same shape — a definition lacking `retry_on` must raise `WorkflowLoadError` naming `retry_policy.retry_on`.
- Add a new test (empty-`retry_on` semantics / Decision 2): build `_VALID` with `retry_policy` set to `{"max_attempts": 3, "retry_wait_sec": 1, "retry_on": []}`, load it, and assert `loader.load().retry_policy.retry_on == ()` (success, "retry nothing").

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_loader.py`:
  - absent `retry_on` → `WorkflowLoadError` naming `retry_policy.retry_on`;
  - explicit `retry_on: []` → loads, `retry_on == ()`;
  - unknown kind still rejected;
  - `config/workflows/default.json` still loads with exception-only retry.

## Completion criteria
- `_VALID` carries `retry_on`; the two absent-key tests are rejection tests naming `retry_policy.retry_on`; an empty-`retry_on` semantics test asserts `()`.

## Out of Scope
Other call sites (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (required loader key), `REQ-002` (empty-`retry_on` semantics), `REQ-005` (call-site surface)
- **Source issue**: `issues/20261116-114753_compat001_workflow-definition-strict-contract.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261116-214100_compat001_workflow-definition-strict-contract.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-005004
- **Related target files**: `tests/agent/workflow/test_workflow_loader.py`
