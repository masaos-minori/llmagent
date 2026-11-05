## Goal

Remove the dead duplicate handler module so partial-completion handling has one
implementation, the live runner path.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The module has no production importer under `scripts/` (verified by `rg`).
- `scripts/shared/llm_transport_errors.py` is a different module and must not be
  touched.
- Its behavior is covered by the rewritten runner-path tests in the companion
  `tests/agent/test_llm_partial_completion.py` document.

## Design decisions

- Delete the whole module rather than stub it; three functions have no caller.

## Alternatives considered

- Keeping the module behind a feature flag: rejected; dead code with no importer.

## Implementation
### Target file
`scripts/agent/llm_transport_errors.py`

### Procedure

- Delete `scripts/agent/llm_transport_errors.py` (`handle_llm_transport_error`,
  `handle_partial_completion`, `handle_non_partial_error`).
- Remove the nine `from agent.llm_transport_errors import ...` statements from
  `tests/agent/test_llm_partial_completion.py` (handled in the companion test
  rewrite document).

### Method

- Single-file removal; no import graph references the module outside tests.

### Details

- Do not touch `scripts/shared/llm_transport_errors.py`.

## Compatibility considerations

- No production caller; only the test file referenced it, and that file is rewritten.

## Security considerations

- N/A: no auth, secret, or input-handling change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `rg agent.llm_transport_errors scripts/` returns no importer.
- Full test suite passes after the test rewrite.

## Completion criteria

- `scripts/agent/llm_transport_errors.py` no longer exists; no import references it.

## Out of Scope

- Any change to how partial text is stored, shown, or retried.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-084444_02_scripts_agent_llm_transport_errors.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002 — remove the dead duplicate handler module
- **Source issue**: issues/20261031-180511_partialcount001_partial-completion-counter-dead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115736_partialcount001_partial-completion-counter-dead.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-084444
- **Related target files**: scripts/agent/llm_transport_errors.py
