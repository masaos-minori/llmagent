## Goal

Update `docs/22_mcp/mcp_03_03_transport-and-health.md` to the new dedup acquisition vocabulary and start states, and fix the deterministic-key claim to the logical-call-id contract (REQ-006, REQ-012; AC-11).

## Scope
**Release unit**: docs-sync

## Assumptions
- Rows 01/02/17 have landed.
- Current text (verified 2026-11-21): :38 claims the key is derived by `derive_idempotency_key(method, tool_name, args, uid)` — no such function exists in `scripts/` — and the durable-store paragraph lists the four ledger states (`pending`/`completed`/`failed`/`interrupted`) with the dispatcher-boundary rejection semantics.

## Design decisions
- The key paragraph adopts the caller-supplied contract: `X-Idempotency-Key` / logical call id (`scripts/agent/tool_runner.py::_logical_call_id`), byte-identical between transport and dedup row for one call.
- Ledger states stay `pending`/`completed`/`failed`/`interrupted`; the doc adds the acquisition results (D-5) as the caller-facing vocabulary and the start states as the store-availability layer.

## Alternatives considered
- N/A: documentation reconciliation of frozen contract text.

## Implementation
### Target file
`docs/22_mcp/mcp_03_03_transport-and-health.md`
### Procedure
Rewrite the key-derivation sentence (:38) and the durable-dedup state/failure-semantics block (:51-59 region).
### Method
- Replace the derivation claim with the logical-call-id contract; keep the `idempotency_key_reused` rejection semantics (overlay and durable row) — they are unchanged in row 02.
- State the new acquisition outcomes and the non-retryable refusal / retryable overlay-only degradation per start state (ADR-004 MCP-001 wording preserved).
### Details
- The cross-link to db_03_07 stays; its content is updated by row 17.

## Compatibility considerations
- Transport health semantics (MCP-001/002 governance) are unchanged; only vocabulary text updates.

## Security considerations
- N/A: prose.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` (routing.md docs gate).

## Completion criteria
- AC-11: no `derive_idempotency_key` claim remains; the doc states the acquisition vocabulary and start-state refusal rules.

## Out of Scope
- Other mcp docs, dispatcher implementation (row 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the doc per Implementation > Method | Pending | — | — | |
| 2 | Run the docs checkers (routing.md Tools) | Pending | — | — | |

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
- **Requirement ID**: REQ-006, REQ-012
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `docs/22_mcp/mcp_03_03_transport-and-health.md`
