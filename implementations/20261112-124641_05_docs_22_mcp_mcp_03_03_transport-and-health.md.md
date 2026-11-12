## Goal
Add `DEGRADED` to the `mcp_03_03` state-transition diagram, and `UNKNOWN` to the state table if the code uses it (`REQ-002` / `AC-2`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan; locate each passage by its quoted text, and skip and report it if it is already correct (Phase 1 rule).
- Code (`scripts/shared/mcp_health.py`): `McpServerHealthState` has `HEALTHY`, `DEGRADED` (failing but not yet unavailable), `UNAVAILABLE`, `HALF_OPEN`, `UNKNOWN`; the diagram goes `HEALTHY -> UNAVAILABLE` only; the table lists four states (checked). Verify whether `UNKNOWN` is ever returned (`get_state` returns `HEALTHY` for unknown keys per the doc) before adding it.
- Overlap: adrrev017 row 12 edits another passage; adrrev014/016 do not touch this diagram.

## Design decisions
- Extend the ASCII diagram with a `DEGRADED` node between `HEALTHY` and `UNAVAILABLE`; keep every existing edge.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/22_mcp/mcp_03_03_transport-and-health.md`

### Procedure
1. Add `HEALTHY ──(failure < threshold)──→ DEGRADED`, `DEGRADED ──(failure × threshold)──→ UNAVAILABLE`, and `DEGRADED ──(record_success)──→ HEALTHY`.
2. If `UNKNOWN` is a reachable state, add its row; otherwise leave the table and state the reason in the progress report.

### Method
- Redraw the diagram in the existing `text` code fence; confirm against `record_failure` and `record_success` semantics in the paragraph below the table.

### Details
- Do not change the semantics paragraph.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain mcp` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_needs_confirmation_inventory.py` — pass.

## Completion criteria
- The diagram shows `DEGRADED` with its transitions and agrees with the state table.

## Out of Scope
- Registry behavior; other diagrams.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` — state diagram includes `DEGRADED`
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `docs/22_mcp/mcp_03_03_transport-and-health.md`
