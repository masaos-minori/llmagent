## Goal

Test Agent recovery after response loss: state mapping, no re-execution, replay-unavailable handling, and degradation when control is unavailable.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the new test module, using a fake control server (httpx `MockTransport` (new) or `respx`) and a temporary workflow store.

## Assumptions

- Verified: `respx` and `pytest-httpx`-style mocking are available in the dev environment (`respx` plugin is loaded in the suite).
- Verified: the resolver is exercised through `tool_call_state_ops.classify_stale_pending` with seeded `dispatched` rows.

## Design decisions

- One fake control server answers GET `/v1/call_state/{key}` from a dict of payloads; handler-execution counters prove nothing is re-run.

## Alternatives considered

N/A: integration style per the Plan Tests section.

## Implementation
### Target file
`tests/agent/test_mcp_call_recovery.py` (new)

### Procedure
1. Mapping: completed, failed, reconciliation_required (expired lease and interrupted), and in_progress payloads produce the expected Agent row states; in_progress leaves the row `dispatched`.
2. No re-execution: a completed call and a `replay_unavailable` result class never invoke a handler or `HttpTransport.call`; assert counters stay zero.
3. Degradation: empty control token, unknown server, control timeout, 401, malformed payload, and `unknown_key` leave the row `outcome_unknown`; the lookup bound limits control calls per pass.
4. Scenario cases from the Plan: workflow dispatch accepted but response lost, git remote-update evidence reuse, deletion already completed, and ambiguous external result leading to operator review (`reconciliation_required`).
5. Config: `McpServerConfig.control_auth_token` resolves an env reference, tolerates an unset one, and is excluded from repr.

### Method
Seed rows with `record_tool_call` and `finalize_tool_call`; build `McpCallRecoveryService` (new) with a fake `server_for_tool`.

### Details
- Assert log output contains no token value (caplog).

## Compatibility considerations

N/A: new tests.

## Security considerations

N/A: tests only; dummy tokens.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_mcp_call_recovery.py tests/agent/workflow/`

## Completion criteria

- All mapping, no-re-execution, degradation, and scenario cases pass.

## Out of Scope

Real network access and per-tool reconcilers.

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
- **Requirement ID**: `REQ-005` (ledger-state to Agent-state mapping and Agent recovery)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `tests/agent/test_mcp_call_recovery.py`
