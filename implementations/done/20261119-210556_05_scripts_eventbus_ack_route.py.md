## Goal

- Correct the `_do_ack` docstring so it names only the registered route `POST /events/{event_id}/ack` instead of the unregistered `/ack` (`REQ-007`; `AC-005`).

## Scope
**Release unit**: audit-route-vocabulary

## Assumptions

- Behavior is unchanged: the docstring is the only edit, and `tests/eventbus/test_eventbus_ack_nack.py` must pass untouched.

## Design decisions

- `D-05`: a docstring names either a registered route path or an identifier documented as non-route; `/ack` is neither.

## Alternatives considered

- Document `/ack` as an internal alias: rejected - no such path is registered (`ack_route.py:122`).

## Implementation
### Target file
`scripts/eventbus/ack_route.py`
### Procedure
1. Rewrite the `_do_ack` docstring line (line 63) so it says the ack logic backs the registered `POST /events/{event_id}/ack` route.

### Method
- Docstring-only edit; no signature, control flow, or audit call changes.

### Details
- Current text at line 63: "Common ack logic shared by /ack and /events/{event_id}/ack."
- The registered routes are `POST /events/{event_id}/ack` (line 122) and `POST /nack` (line 137).

## Compatibility considerations

- No generated artifact reads this docstring.

## Security considerations

- N/A: wording only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v` — all pass unchanged (characterization: ack/nack behavior)
- `rg "/ack\b" scripts/eventbus/ack_route.py` — only the registered path remains (static: no unregistered path in the file)

## Completion criteria

- `scripts/eventbus/ack_route.py` names no route that is not registered.

## Out of Scope

- Any behavior change in `_do_ack` or the ack/nack routes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the docstring line | Completed | 20261119-232759 | 20261119-232759 | docstring only docstring route line rewritten to the registered template; uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q green |
| 2 | Run `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v` | Completed | 20261119-232759 | 20261119-232759 | unchanged behavior docstring route line rewritten to the registered template; uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q green |

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
- **Related target files**: `scripts/eventbus/ack_route.py`