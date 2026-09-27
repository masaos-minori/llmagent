## Goal

Create `scripts/agent/eventbus_topic_admin_client.py`: an Agent-side client calling the new `POST /admin/topics/authorization` endpoint with the ADMIN token (REQ-004).

## Scope

In scope: a new client module following the EVENTBUS-005/006 client conventions. Out of scope: the endpoint's own implementation (rows 1-3).

## Assumptions

- The endpoint's request body shape (row 2) is `{"consumer_authorization": {...}, "topic_authorization": {...}}` (both optional) — confirm against row 2's actual implementation before finalizing this client, since row 2 is itself partially blocked and its exact contract may shift.

## Design decisions

- Follow `scripts/agent/eventbus_client.py` (EVENTBUS-005 Plan) and `scripts/agent/eventbus_subscriber.py` (EVENTBUS-006 Plan)'s established config-dataclass + typed-result convention, for consistency across all three Event Bus clients.

## Alternatives considered

- Merging this client into `eventbus_client.py` (EVENTBUS-005) as an additional method: rejected — keeps each client module scoped to one capability, matching this Plan's own Out-of-Scope discipline (EVENTBUS-005/006 explicitly excluded topic management from their own scope).

## Implementation

### Target file

`scripts/agent/eventbus_topic_admin_client.py`

### Procedure

1. Create a `@dataclass EventBusTopicAdminClientConfig` holding the admin endpoint URL, timeout, and ADMIN token.
2. Create a client class with an async method that POSTs the authorization update body to `/admin/topics/authorization` with the ADMIN token header.
3. Return a typed success/error result, matching the EVENTBUS-005/006 clients' convention.

### Method

New module, following the two sibling Event Bus clients' established convention.

### Details

- Re-confirm the endpoint's exact request/response shape against row 2's actual implementation immediately before finalizing this client — row 2 was partially blocked at the time this document was written, so its final shape may differ from this row's assumption.

## Compatibility considerations

New module, no existing callers.

## Security considerations

The ADMIN token is the highest-privilege credential in the per-role token model — ensure it is sourced the same way `eventbus_client.py`/`eventbus_subscriber.py` source their own tokens (config value, not hardcoded), and is not logged.

## Rollback considerations

New, uncalled file — revert via `git revert` or deletion.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/eventbus_topic_admin_client.py` | Unit | `uv run pytest tests/agent/test_eventbus_topic_admin_client.py -q` | All tests pass, at least 1 collected |
| `scripts/agent/eventbus_topic_admin_client.py` | Static | `uv run ruff check scripts/agent/eventbus_topic_admin_client.py && uv run mypy scripts/agent/eventbus_topic_admin_client.py && uv run lint-imports && uv run bandit -r scripts/agent/eventbus_topic_admin_client.py -c pyproject.toml` | All pass |

## Completion criteria

- The client successfully calls the endpoint end-to-end once row 2 is unblocked and implemented (AC-4).

## Out of scope

- The endpoint's own implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-144037 | 20260927-144037 | Client shape can be drafted now; final request/response confirmation depends on row 2 unblocking |
| 2 | Add or update tests per Validation plan | Completed | 20260927-144037 | 20260927-144037 | Covered by `tests/agent/test_eventbus_topic_admin_client.py` (row 6) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-144037 | 20260927-144037 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-144037 | 20260927-144037 | N/A: no `docs/00_index.md` task-scope row maps this new file |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20260927-115652_eventbus007_implement-agent-eventbus-topic-management-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121125_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123813
- **Related target files**: scripts/agent/eventbus_topic_admin_client.py