## Goal

Reconcile `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` to the new lease + identity contract (REQ-012; AC-11).

## Scope
**Release unit**: docs-sync

## Assumptions
- Rows 01/02/03 have landed (Phases 2-3): the doc describes the contract as implemented, not as planned.
- The doc currently claims a `derive_idempotency_key(method, tool_name, args, uid)` derivation at :69 (no such function exists in `scripts/`) and a dangling follow-up-issue reference at :108 (verified 2026-11-21).

## Design decisions
- Replace the key-derivation paragraph with the caller-supplied logical-call-id contract (`X-Idempotency-Key` from `context.call_id`; `scripts/agent/tool_runner.py::_logical_call_id`), consistent with the Plan Design verification findings.
- The `PRAGMA user_version = 1` claim becomes true once row 01 stamps it; the doc states the stamp as part of the creation sequence.

## Alternatives considered
- N/A: documentation reconciliation of frozen contract text.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
### Procedure
Rewrite the store sections to the new contract and fix the two stale claims.
### Method
- Schema/config sections: `dedup_call_state` columns (`owner_id`, `lease_expires_epoch`, `attempt_number`), `store_meta`, `call_attempt_history`, `lease_seconds`/`max_attempts`.
- Decision sections: acquisition vocabulary (D-5), lease rules (D-2), terminal immutability (D-3), identity start states (D-4), operator resolution (REQ-007); add the lost/replaced/legacy/mismatch branches to the Replay Decision Table.
- Remove the `derive_idempotency_key` derivation text (:69) and the stale follow-up-issue citation (:108); describe the execution-snapshot `dedup` component (row 03).
### Details
- Keep the doc's existing section skeleton (Retention sweep, classification, snapshot sections) and update in place.

## Compatibility considerations
- This file is the canonical store doc other docs link to; cross-references from mcp_03_03/agent docs must still resolve (docs structure checker validates).

## Security considerations
- N/A: prose.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` (routing.md docs gate).

## Completion criteria
- AC-11: the doc describes acquisition vocabulary, start states, lease columns, identity, operator resolution; no stale `derive_idempotency_key`/unstamped-`user_version`/dangling-reference claims remain.

## Out of Scope
- Other docs rows (18-23), code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the doc per Implementation > Method | Completed | — | 20261121-125716 | Doc rewritten in place to the lease+identity contract: identity stamp/start states, lease+terminal immutability, acquisition vocabulary, attempt history, lease_seconds/max_attempts config keys, caller-supplied logical-call-id key (derive_idempotency_key text removed), dangling follow-up-issue citation removed, execution_snapshot 5-component dedup component added, Replay Decision Table rebuilt with identity-refusal branches. |
| 2 | Run the docs checkers (routing.md Tools) | Completed | — | 20261121-125716 | check_docs_quality.py and check_docs_structure.py both pass (two REQ-xxx markers removed to satisfy the Current-Specification-Only Policy). |

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
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`