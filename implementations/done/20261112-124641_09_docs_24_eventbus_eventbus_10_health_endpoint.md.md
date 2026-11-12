## Goal
Clarify the EventBus `liveness` field against the MCP `liveness` flag with a cross-reference (`REQ-003` / `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan; locate each passage by its quoted text, and skip and report it if it is already correct (Phase 1 rule).
- EventBus: `liveness` means `The DLQ sweep task is running`; MCP (`mcp_02_02`): `liveness` defaults to `true` and subclasses may override it for critical internal states (checked).
- Overlap: adrrev014 edits health fields elsewhere in this file; compatible.

## Design decisions
- Extend the table cell; add one sentence with a link to `mcp_02_02_startup-modes-and-health.md`.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/24_eventbus/eventbus_10_health_endpoint.md`

### Procedure
1. Edit the `liveness` row: `The DLQ sweep task is running (EventBus-specific; not the MCP server process-state flag described in mcp_02_02)`.

### Method
- Use the existing link style of the file; add the document to front matter `related` only if the checker requires it.

### Details
- Do not change the readiness row or the gate sentence.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_needs_confirmation_inventory.py` — pass.

## Completion criteria
- The two meanings are distinguished with a cross-reference.

## Out of Scope
- MCP health text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-204830 | 20261112-204830 |  |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-204830 | 20261112-204830 |  |

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
- **Requirement ID**: `REQ-003` — EventBus `liveness` versus MCP `liveness`
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `docs/24_eventbus/eventbus_10_health_endpoint.md`