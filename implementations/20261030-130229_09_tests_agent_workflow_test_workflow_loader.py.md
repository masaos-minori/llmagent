## Goal

Cover the `retry_on` policy field in `tests/agent/workflow/test_workflow_loader.py` and pin the shipped configuration (`REQ-001`, loader validation of the policy; `REQ-009`, tests; `REQ-011`, deployment compatibility).

## Scope

- Modify only `tests/agent/workflow/test_workflow_loader.py`.

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 1 tests, written with rows 02-04; independent of the wfrecovery001 Plan. Execution order follows the Plan's phases, not `seq`.
- Existing structure: `TestWorkflowLoaderLoad` (`:32`) writes JSON files into `tmp_path` and covers `test_load_retry_policy` (`:50`) and missing-key cases (`:75-112`).
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `retry_on` (row 02 document).

## Design decisions

- Follow the existing pattern: write a definition dict to `tmp_path`, load it, assert on the returned `WorkflowDef` or the raised `WorkflowLoadError`.

## Alternatives considered

- N/A: test row.

## Implementation

### Target file

`tests/agent/workflow/test_workflow_loader.py`

### Procedure

1. Add: a definition without `retry_on` loads with the default `("exception",)`.
2. Add: a valid list (`["exception", "timeout"]`) loads as a tuple in order.
3. Add: an unknown kind and a non-list value each raise `WorkflowLoadError` naming the value.
4. Add: the shipped `config/workflows/default.json` loads and carries `retry_on` equal to `("exception",)`, and a copy of it without the key still loads.

### Method

- For the shipped file test, load by path through `WorkflowLoader(workflows_dir=...)` pointed at the repository `config/workflows` directory (resolved from the test file location).

### Details

- Write the new tests first and confirm they fail before rows 02-04 are implemented.

## Compatibility considerations

- N/A: tests only.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_loader.py -v`
- `uv run ruff format tests/agent/workflow/test_workflow_loader.py`, `uv run ruff check tests/agent/workflow/test_workflow_loader.py`

## Completion criteria

- The four cases above are covered and pass after rows 02-04.

## Out of Scope

- Engine and orchestrator tests (rows 08 and 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the loader tests | Pending | — | — | Plan Phase 1 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-009, REQ-011 (loader tests)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: tests/agent/workflow/test_workflow_loader.py
