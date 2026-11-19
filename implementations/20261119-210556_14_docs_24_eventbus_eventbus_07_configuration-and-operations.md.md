## Goal

- State the audit `route` vocabulary an operator will actually see in the EventBus log: registered path templates for HTTP-driven actions, and `startup` and `ttl_sweep` for internal phases (`REQ-007`; `AC-005`).

## Scope
**Release unit**: audit-route-vocabulary

## Assumptions

- Only this line and the sweep paragraph need the change; the rest of the doc already names registered paths (`ASM-07`).

## Design decisions

- `D-05`: one doc statement mirrors the vocabulary `scripts/eventbus/audit.py` documents (row 09).

## Alternatives considered

- Leave the doc describing `route="/startup"` and keep the code value: rejected - the code value changes, and a stale operator-facing contract is what the issue reports.

## Implementation
### Target file
`docs/24_eventbus/eventbus_07_configuration-and-operations.md`
### Procedure
1. Update the startup-baseline bullet at line 97 so the record it describes carries `route="startup"`.
2. Update the sweep bullet (line 90) so it names `route="ttl_sweep"` as the internal-loop identifier.
3. Add one sentence naming both identifiers as non-route internal phases, distinct from the registered path templates used by HTTP-driven records.

### Method
- Documentation edit only; the tail sections and front matter stay as they are.

### Details
- Current text at line 97 records `route="/startup"` as part of the operator-facing audit contract.
- Registered path templates the doc already uses: `/health`, `/publish`, `/subscribe`, `/replay`, `/dlq`, `/dlq/{event_id}/requeue`, `/events/{event_id}/ack`, `/nack`, `/admin/topics/authorization`.

## Compatibility considerations

- Read by `tools/check_docs_consistency.py --domain eventbus`; no generated block lives in this file.

## Security considerations

- N/A: no credential or token value is documented.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_consistency.py --domain eventbus && uv run python tools/check_docs_quality.py` — no drift, no stale reference (docs: documentation freshness)

## Completion criteria

- `AC-005`: the operator doc names only registered paths or the two documented non-route identifiers.

## Out of Scope

- Prose rewrites elsewhere in `docs/24_eventbus/`, which already use the registered paths.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two bullets and add the vocabulary sentence | Pending | — | — | docs only |
| 2 | Run the eventbus documentation checkers | Pending | — | — | `check_docs_consistency.py --domain eventbus`, `check_docs_quality.py` |

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
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`
