## Goal

Assert the default and override of the new approval field (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: this test file only.

## Assumptions

- Verified precedent: default and override assertions for `gitops_push_blocked` at lines 278 and 322 (`tests/agent/test_config_builders.py`).

## Design decisions

- Add assertions beside the precedent: default True when absent, False when set false, and a non-boolean value rejected.

## Alternatives considered

N/A: follows the existing tests.

## Implementation
### Target file
`tests/agent/test_config_builders.py`

### Procedure
1. Extend the approval default test and the override test; add a rejection case if the module tests invalid booleans for sibling fields.

### Method
Add assertions to existing tests; no new fixtures.

### Details
- Also run the registry consistency tests to confirm the field is registered.

## Compatibility considerations

N/A: test-only.

## Security considerations

N/A: test-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py -q`
- `uv run ruff check tests/agent/test_config_builders.py`

## Completion criteria

- The default and override are asserted and pass.

## Out of Scope

Reload tests and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213744 | 20261122-213744 | Changed: tests/agent/test_config_builders.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-213744 | 20261122-213744 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-005` (default and override of the new approval field)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `tests/agent/test_config_builders.py`
