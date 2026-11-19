## Goal

- Emit the registered path template in the requeue audit record instead of the unregistered `/dlq/requeue` (`REQ-007`; `AC-005`).

## Scope
**Release unit**: audit-route-vocabulary

## Assumptions

- `ASM-02`: the audit `route` field has no code consumer, so its value is an operator-facing log contract.
- Row 12 updates the assertion that currently pins `/dlq/requeue` (`tests/eventbus/test_eventbus_dlq.py:1301`).

## Design decisions

- `D-04`, `D-05`: an HTTP-driven audit record names the registered path template it came from, which for this handler is `/dlq/{event_id}/requeue` (line 50).

## Alternatives considered

- Emit a non-route identifier for the requeue: rejected - the action is triggered by a registered HTTP route.

## Implementation
### Target file
`scripts/eventbus/dlq_route.py`
### Procedure
1. Change `route="/dlq/requeue"` (line 80) to `route="/dlq/{event_id}/requeue"`.

### Method
- One keyword argument; the record shape, the audit event type, and the target field are unchanged.

### Details
- The registered decorator is `@router.post("/dlq/{event_id}/requeue")` at line 50; `/dlq/requeue` is one of the four phantom keys the old route map carried.
- The manifest entry for this route (row 19) carries the same path template with method `POST` and role `OPERATOR`, so log and manifest now use one vocabulary.

## Compatibility considerations

- Row 12 updates the pinned assertion in the same commit; the EventBus docs already use the registered path (`ASM-07`).

## Security considerations

- N/A: the record already carries only a target id and a token fingerprint.

## Rollback considerations

- N/A: revert the commit together with row 12's assertion.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py -v` — the record names the registered path (unit (T-012): requeue audit record)
- `rg "/dlq/requeue" scripts/eventbus/ tests/eventbus/ docs/24_eventbus/` — no match outside archived work items (static: no phantom path left)

## Completion criteria

- The requeue audit record carries `/dlq/{event_id}/requeue` and `tests/eventbus/test_eventbus_dlq.py` asserts it.

## Out of Scope

- Any change to the requeue handler behavior or its role gate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the emitted route value | Completed | 20261119-232759 | 20261119-232759 | one keyword argument emitted route is now /dlq/{event_id}/requeue; uv run pytest tests/eventbus/test_eventbus_dlq.py -q 33 passed |
| 2 | Run `uv run pytest tests/eventbus/test_eventbus_dlq.py -v` | Completed | 20261119-232759 | 20261119-232759 | with row 12 emitted route is now /dlq/{event_id}/requeue; uv run pytest tests/eventbus/test_eventbus_dlq.py -q 33 passed |

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
- **Requirement ID**: `REQ-007` (audit records, docstrings, and the operator-facing documentation name either a registered route path or an identifier explicitly documented as a non-route internal loop)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `scripts/eventbus/dlq_route.py`