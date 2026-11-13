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
- Remove the `topic_authorization` parameter from `update_topics_authorization` (55-60).
- Update the docstring (60-62) to describe `consumer_authorization` only.
- Delete the `body["topic_authorization"]` assignment (66-67).

### Companion test files
- `tests/agent/test_eventbus_topic_admin_client.py`
  - Procedure: remove the `topic_authorization` cases (57, 65, 84); assert the posted body contains no `topic_authorization` key.
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
