## Goal

Remove the `topic_authorization` parameter and body key from `EventBusTopicAdminClient.update_topics_authorization` (REQ-002).

## Scope
**Release unit**: single-authorization-format (with rows 01, 02, 04, 05, 06, 14, 17)

## Assumptions
- The client has no caller outside `tests/agent/test_eventbus_topic_admin_client.py` (verified by `rg`).
- The client already fails against the endpoint today because it sends no `expected_generation` (UNK-06); this row removes `topic_authorization` only and does not repair that contract.

## Design decisions
- N/A: parameter removal is fixed by the Plan.

## Alternatives considered
- Adding `expected_generation` to the client in the same change: rejected; it is a separate scope decision recorded as UNK-06.

## Implementation
### Target file
`scripts/agent/eventbus_topic_admin_client.py`
### Procedure
Delete the parameter and its body entry.
### Method
Signature and body edit; the request/response plumbing is otherwise unchanged.
### Details
- Remove the `topic_authorization` parameter from `update_topics_authorization` (signature 55-59; the parameter line is 58, verified 2026-11-13).
- Update the docstring (60-63) to describe `consumer_authorization` only; the "Both parameters are optional" sentence at 62 must be reworded to a single parameter.
- Delete the `body["topic_authorization"]` assignment (67-68; the procedure's original 66-67 was re-verified 2026-11-13 — the consumer assignment is at 65-66 and stays).

### Companion test files
- `tests/agent/test_eventbus_topic_admin_client.py`
  - Procedure (claims verified 2026-11-13): remove the `topic_authorization` cases (argument at 57, expected body entry at 65, and the `assert "topic_authorization" not in kwargs["json"]` at 84 — keep that final assertion pattern since it directly locks AC-2 for the client); the remaining tests (28, 39, 69, 89, 111, 126) already pass `consumer_authorization` only.
  - Validation: `uv run pytest tests/agent/test_eventbus_topic_admin_client.py`

## Compatibility considerations
- The endpoint ignores unknown body keys, so an older caller sending the key still lands on the no-op/422 path (UNK-04); no other repository caller exists.

## Security considerations
- N/A: no credential or authorization semantics change.

## Rollback considerations
- Restore the parameter and body key; no persisted state.

## Validation plan
- `uv run pytest tests/agent/test_eventbus_topic_admin_client.py`
- AC-2: `rg -n "topic_authorization" scripts/agent/eventbus_topic_admin_client.py` returns nothing.

## Completion criteria
- The client's public method takes only `consumer_authorization`; companion tests pass.

## Out of Scope
- Sending `expected_generation` from the client (UNK-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-13 | 2026-11-13 | client consumer-only; companion tests 6 passed |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-13 | 2026-11-13 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-13 | 2026-11-13 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-13 | 2026-11-13 | — |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `scripts/agent/eventbus_topic_admin_client.py`, `tests/agent/test_eventbus_topic_admin_client.py`
