## Goal

Add the startup-side cases for the newly rejected inputs and for the candidate-build entry the reload
path calls, so startup is shown to reject what reload rejects (REQ-001, shared strict type rules;
REQ-002, reload candidate through the startup parser).

## Scope
**Release unit**: R1-strict-primitives

## Assumptions
- This file pins startup assembly today; the parity comparison itself lives in row 27, so this file covers
  only the startup side.
- The tests reuse `tests/agent/_config_test_defaults.py` so production validation does not fail for
  unrelated reasons (Plan `Reference Files`).

## Design decisions
- Cases are added for each newly rejected input on the startup path, mirroring the parity table rows.
- A case asserts the candidate-build entry returns a typed `AgentConfig` without mutating live state.

## Alternatives considered
- Relying on the parity test alone — rejected: AC-6 requires the removed-key rejection to be shown on the
  startup path as well (row 39).

## Implementation
### Target file
`tests/agent/test_config_builders.py`

### Procedure

### Method
- Startup-side rejection cases for every input in the Plan's `Newly rejected inputs` list.
- A case for the candidate-build entry exposed by row 13.

### Details
- Existing passing cases are unchanged; only the coercion-tolerant cases are retargeted to rejection.

## Compatibility considerations
- Blast radius: this file is the startup-assembly pin; changing it does not change production behavior.

## Security considerations
- N/A: the tests assert accept and reject results, not output.

## Rollback considerations
- Revert the Phase 1 commit.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -q`
- `uv run pytest tests/integration/test_standard_config_integration.py -m integration -q`

## Completion criteria
- Every newly rejected input has a startup-side rejection case, and the candidate-build entry has a case
  showing it performs no live mutation.

## Out of Scope
- The parity table (row 27).
- The removed-key cases (row 39).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-002 (reload candidate through the startup parser); AC-1
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `tests/agent/test_config_builders.py`
