## Goal

- State the two `route` vocabularies in the audit-record docstrings, so a reader can tell a registered path from an internal-phase identifier (`REQ-007`; `AC-005`).

## Scope
**Release unit**: audit-route-vocabulary

## Assumptions

- `ASM-02`: no code consumer reads the field, so this is a documentation contract for operators and for the doc gate in row 14.

## Design decisions

- `D-05`: one place states the vocabulary - the `log_privileged_action` argument description (and the sibling `log_authorization_change` description) - and every call site conforms to it.

## Alternatives considered

- Encode the vocabulary in a typed field or enum: rejected - the field is a log label with no consumer, and `REQ-013` forbids inventing a compatibility-shaped model for it.

## Implementation
### Target file
`scripts/eventbus/audit.py`
### Procedure
1. Rewrite the `route` argument description in `log_privileged_action` (lines 138-155) as: a registered FastAPI route path template, or one of the documented non-route internal identifiers `ttl_sweep` and `startup`.
2. Apply the same wording to the `route` description in `log_authorization_change` so the two audit helpers agree.

### Method
- Docstring-only change; signature, record fields, and emission format are unchanged.

### Details
- Current text: `route: Route being accessed.` (line 151), which cannot describe `ttl_sweep` or `startup`.
- Call sites after rows 6-8: `/dlq/{event_id}/requeue`, `/events/{event_id}/ack`, `/nack`, `/health`, `/publish`, `/subscribe`, `/replay`, `/dlq`, `/admin/topics/authorization`, `ttl_sweep`, `startup`.

## Compatibility considerations

- Row 14 mirrors the vocabulary in the operator-facing doc; rows 6-8 make the emitted values match it.

## Security considerations

- N/A: documentation of an existing log field.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_authz_generation_ttl.py -v` — both forms asserted (unit (T-012, T-013): vocabulary asserted by tests)
- `uv run python tools/check_docs_consistency.py --domain eventbus` — no drift (docs: documentation gate)

## Completion criteria

- Both audit helpers document the two vocabularies, and no call site emits a value outside them.

## Out of Scope

- Adding or renaming audit record fields, or changing the audit action vocabulary.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the two `route` argument descriptions | Completed | 20261119-232759 | 20261119-232759 | docstring only two privileged-helper route argument descriptions rewritten; EventBus audit assertions and check_docs_consistency --domain eventbus clean |
| 2 | Run the EventBus audit assertions and docs gate | Completed | 20261119-232759 | 20261119-232759 | with rows 6-8, 12-14 two privileged-helper route argument descriptions rewritten; EventBus audit assertions and check_docs_consistency --domain eventbus clean |

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
- **Related target files**: `scripts/eventbus/audit.py`