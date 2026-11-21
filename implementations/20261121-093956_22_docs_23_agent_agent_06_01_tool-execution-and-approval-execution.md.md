## Goal

Fix the two stale key-derivation claims in `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` to the logical-call-id contract (REQ-012; AC-11).

## Scope
**Release unit**: docs-sync

## Assumptions
- Row 01/02 have landed.
- Current text (verified 2026-11-21): :81 and :99 cite `shared/http_transport.py::derive_idempotency_key(...)`; `rg derive_idempotency_key scripts/` finds no definition — the actual contract is the caller-supplied logical call id (`scripts/agent/tool_runner.py::_logical_call_id`, `context.call_id`).

## Design decisions
- State the byte-identical property as an outcome of the shared logical call id (same id flows to the `X-Idempotency-Key` header and the dedup row key), not a derivation function.

## Alternatives considered
- N/A: documentation reconciliation of frozen contract text.

## Implementation
### Target file
`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
### Procedure
Rewrite the two cited sentences.
### Method
- :81 region: the row key is the logical call id generated once per prepared call and passed as `X-Idempotency-Key`; :99 region: the `tool_call_state` row key written during execution (workflow database ledger, `scripts/agent/tool_runner.py::_record_pending_state`) equals the transport idempotency key because both read the same logical call id (`context.call_id`).
- Keep the surrounding approval-execution narrative untouched.
### Details
- Reference only: `scripts/agent/tool_runner.py::_logical_call_id` exists today (:153 region) and is not modified by this Plan.

## Compatibility considerations
- Consistent with row 21 (mcp_03_03) wording; cross-links resolve via the docs structure checker.

## Security considerations
- N/A: prose.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` (routing.md docs gate).

## Completion criteria
- AC-11: no `derive_idempotency_key` citation remains in this file.

## Out of Scope
- `scripts/agent/tool_runner.py` (Reference File only, unchanged).

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
- **Requirement ID**: REQ-012
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
