## Goal

Delete `test_turn_state_concurrency` and the imports it alone uses, since the `TurnState` members
it exercises (`tool_calls`, `add_tool_call`, `get_tool_calls`, `turn_count`) are deleted by the
`scripts/agent/context.py` sibling document (`REQ-010`, tied to `REQ-009`).

## Scope

- **In-Scope**: deleting `test_turn_state_concurrency` (`:23-36`), the `import asyncio` (`:1`),
  and the `TurnState` import (`:4`) that it alone uses.
- **Out-of-Scope**: the remaining `AgentContext` / `AppServices` tests (unchanged).

## Assumptions

- `test_turn_state_concurrency` is the ONLY consumer of `asyncio` and `TurnState` in this file
  (per the Plan's evidence: `test_context.py:23-36` is the only consumer of the deleted members).
- Deleting the test is safe because the members it covered no longer exist after the context
  sibling lands.

## Design decisions

- Delete the test and the two imports together in one change so the file neither references a
  removed symbol nor carries an unused import (which `ruff`/isort would flag).

## Alternatives considered

`N/A: keeping the test would fail to compile against the deleted members; converting it to test a
different member was rejected (the user chose deletion over population, `REQ-009`).`

## Implementation

### Target file

`tests/agent/test_context.py`

### Procedure

1. Read `tests/agent/test_context.py` in full.
2. Delete `test_turn_state_concurrency` (`:23-36`) in full.
3. Remove the `import asyncio` line (`:1`) — confirm it is not used elsewhere in the file.
4. Remove the `TurnState` import (`:4`) — confirm `TurnState` is not referenced anywhere else in
   the file.
5. If either import is still used elsewhere, keep it and instead only delete the test body.
6. Confirm `ruff`/isort report no unused import and the remaining tests still reference only
   surviving symbols.

### Method

Inline deletions; no new symbols.

### Details

- The concurrency test exercised `add_tool_call` / `get_tool_calls` / `turn_count` via
  `asyncio.gather`; those members live in `context.py` and are removed there, so this test has no
  valid subject anymore.
- Do not touch the `AgentContext` / `AppServices` tests; they do not import `asyncio` or
  `TurnState`.

## Compatibility considerations

Test-only change; no production contract affected. The `context.py` sibling must land so the
deleted members are actually gone before this compiles clean.

## Security considerations

`N/A: test-only change; no auth, secret, or input-handling change.`

## Rollback considerations

`N/A: revert the single commit.`

## Validation plan

- `ruff` + isort pass (no unused imports after deletion).
- The remaining `tests/agent/test_context.py` tests pass.
- Full agent test suite passes (`rules/toolchain.md`).

## Completion criteria

`test_turn_state_concurrency` is removed, the now-unused `import asyncio` and `TurnState` import
are gone, no remaining reference to them exists in the file, and the surviving tests pass under
`ruff`.

## Out of Scope

The `TurnState` deletions in `scripts/agent/context.py` and the other tests, production code, and
doc passages are handled by sibling documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `test_turn_state_concurrency` + unused imports (`Implementation > Procedure`) | Pending | — | — | run after `context.py` deletes its members |
| 2 | Add or update tests per Validation plan | N/A: deletion only | | | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `ruff`, full suite |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: no doc edit in this file | | | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-010` (delete the only consumer test of the dead members), tied to
  `REQ-009`
- **Source issue**: `issues/20261021-093421_turn004_turn-end-events-duplicated-or-missing.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-140855_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-092307
- **Related target files**: `tests/agent/test_context.py`
