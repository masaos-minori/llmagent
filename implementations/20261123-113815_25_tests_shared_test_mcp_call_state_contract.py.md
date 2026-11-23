## Goal

Pin the closed vocabularies, the totality of the ledger-state mapping, the reconciler Protocol shape, and tolerant control-token resolution.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the new test module only.

## Assumptions

- Verified: `TOOL_CALL_STATES` (agent) is importable from tests, so the mapping test can assert every non-`in_progress` target is a member.

## Design decisions

- Parametrize over every ledger status and lease flag; assert `agent_state_for` returns a member of `AGENT_RECOVERY_STATES` and raises `ValueError` for an unknown status.

## Alternatives considered

N/A: plain pytest.

## Implementation
### Target file
`tests/shared/test_mcp_call_state_contract.py` (new)

### Procedure
1. Assert the exact members of `RESULT_CLASSES`, `RECONCILE_OUTCOMES`, `CONTROL_ERROR_CODES`, and `AGENT_RECOVERY_STATES`.
2. Assert the mapping table totality and that every target except `in_progress` is in `TOOL_CALL_STATES`.
3. Assert `ReconcileEvidence` rejects an unknown outcome and a stub class satisfies `Reconciler` structurally.
4. Assert `resolve_control_token` returns the value for a set variable (monkeypatch env), `""` for unset, empty, and non-string input.

### Method
Use `monkeypatch.setenv`/`delenv`; no network, no files.

### Details
- Keep tests independent of dedup store code.

## Compatibility considerations

N/A: new tests.

## Security considerations

N/A: tests only; no real tokens (use dummy values).

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_call_state_contract.py`

## Completion criteria

- The module passes and fails if a vocabulary member or a mapping entry is removed.

## Out of Scope

Ledger and API behavior (other test rows).

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
- **Requirement ID**: `REQ-004` (reconciler contract), `REQ-005` (ledger-state to Agent-state mapping and Agent recovery)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `tests/shared/test_mcp_call_state_contract.py`
