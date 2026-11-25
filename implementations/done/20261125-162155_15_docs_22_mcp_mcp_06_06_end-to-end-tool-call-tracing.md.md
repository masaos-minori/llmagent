## Goal

Correct the stale `dedup_state` and `idempotency_key` statements and add the audit field definitions and the compatibility note (REQ-006, REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Step 3a (20261125): line 51 lists `snapshot_mismatch`, `result_truncated`, `unreplayable`, which do not exist as `dedup_state` values; the shipped set is `duplicate_hit`, `in_progress`, `outcome_unknown`, `replay_unavailable`, `replayed`, `store_error`, `lease_conflict`, `reconciliation_required`, `interrupted` (Step 3a re-check: `reconciliation_required` and `interrupted` are emitted via `dedup_gate.py` line 164 `dedup_state=state`; the earlier 7-value list missed them). Line 53 calls `idempotency_key` a derived `workflow:task:turn:call` string; it is the logical call id (`tool_runner._logical_call_id`).

## Design decisions

- Document the definitions of `dedup_state`, `turn_id`, `task_linkage`, `task_id`, `idempotency_key` plus the compatibility note (additive fields, older records readable).

## Alternatives considered

N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`
### Procedure
Replace the value list at line 51 with the shipped set; rewrite line 53 to describe `idempotency_key` as the logical call id generated at preparation; add the field definitions and the compatibility note.
### Method
Keep the join-on-`mcp_request_id` guidance; state the audit line can also be joined on `idempotency_key`.
### Details
N/A.

## Compatibility considerations

N/A: documentation-only; the note itself is the deliverable.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_consistency.py` (per `rules/tool-gates.md`)

## Completion criteria

- The value list matches the shipped state set and the `idempotency_key` description matches the code (AC-4).

## Out of Scope

- The final design-docs sweep owned by the mcpai012 Issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261125 | shipped 9-value set applied; idempotency_key rewritten as preparation-time logical call id; field definitions + compatibility note added |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | — | 20261125 | check_docs_quality + check_docs_structure passed |

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
- **Requirement ID**: REQ-006, REQ-008 (field definitions and compatibility note)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`