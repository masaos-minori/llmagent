## Goal

Let `audit_approval` accept and write the provenance fields (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `scripts/agent/tool_audit.py`; assertions live in the approval test row.

## Assumptions

- Verified: `audit_approval` builds a `ToolApprovalEvent` from masked args and writes it as JSON (`scripts/agent/tool_audit.py:111-148`); `decision` already carries the outcome.

## Design decisions

- Add keyword-only `request_id`, `preview_source`, and `fallback_reason` parameters defaulting to empty and pass them to the event.

## Alternatives considered

N/A: pass-through parameters.

## Implementation
### Target file
`scripts/agent/tool_audit.py`

### Procedure
1. Extend the `audit_approval` signature and the event construction; update the docstring to say no answer text is accepted.

### Method
Signature and constructor change only.

### Details
- Keep `args_preview` bounded and masked as today.

## Compatibility considerations

Existing positional and keyword calls stay valid because the new parameters are keyword-only with defaults.

## Security considerations

The answer text has no parameter, so it cannot be logged.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent -k "audit or approval" -q`
- `uv run ruff check scripts/agent/tool_audit.py && uv run mypy scripts/agent/tool_audit.py`

## Completion criteria

- Provenance fields are written when given and empty otherwise; no answer text path exists.

## Out of Scope

Deciding the field values (approval row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`); assertions are in the approval test row | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (audit writes request id, preview source, fallback reason, outcome; never the answer)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/tool_audit.py`
